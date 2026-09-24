-- ════════════════════════════════════════════════════════════
-- A/B 테스트 시뮬레이션 — '젤리보상' 실험을 가상으로 채워본다
--
-- ⚠️ 이건 진짜 실험 결과가 아니다. OkCupid 데이터는 2012년에 한 번 찍힌 사진이라
--    "지금 배정하고 30일 기다린다"는 게 원래 불가능하다 (ab_test/README.md 참고).
--    그래서 "실제로 이렇게 운영했다면 결과 화면이 어떤 모양일지"를 보여주는
--    시뮬레이션이다. 발표에서는 반드시 '시뮬레이션'이라고 표시해야 한다.
--
-- 절반은 진짜, 절반은 가정
--   · 배정(누가 treatment/control 인지)   → 진짜 무작위 (가정 없음)
--   · control 결과                        → 진짜 (원래 역사대로 아무 개입도 안 받은 사람들이라,
--                                            실제 churn_actual 을 뒤집은 값이 곧 '개입 없었을 때' 결과다)
--   · treatment 결과                      → 가정 (실제로 넛지를 보낸 적이 없어서, "보냈다면" 을
--                                            우리가 가진 진짜 상관관계로 추정한다)
--
-- ⚠️ churn_prob(모델 예측 확률)을 그대로 베이스로 쓰지 않은 이유
--   PROBABILITY_CALIBRATION_NOTE 에 적어 둔 것처럼, 이 모델의 예측 확률은 실제보다
--   부풀려져 있다(auto_class_weights=Balanced). 그래서 여기서는 churn_prob 이 아니라
--   실제 역사(churn_actual, 부풀림 없는 진짜 0/1 값)를 기준으로 삼았다.
-- ════════════════════════════════════════════════════════════

-- 0) 다시 실행할 수 있게, 이전 시뮬레이션 결과는 지운다
DELETE FROM outcomes WHERE user_id IN (
    SELECT user_id FROM ab_assignment WHERE experiment = '젤리보상'
);
DELETE FROM ab_assignment WHERE experiment = '젤리보상';


-- 1) 배정 — High 위험군을 무작위로 반씩 (진짜, 가정 없음)
INSERT INTO ab_assignment (user_id, experiment, arm)
SELECT user_id,
       '젤리보상',
       CASE WHEN random() < 0.5 THEN 'treatment' ELSE 'control' END
FROM predictions
WHERE risk_tier = 'High';


-- 2) 결과 채우기
--
-- 가정한 값(uplift)의 출처: project_facts.KEY_SIGNALS 의 '자기소개 분량' 신호.
--   자기소개 100자 이하 이탈률 55.04%  vs  100자 초과 이탈률 24.01%   (격차 31.03pp)
-- 이 31.03pp 전부를 '넛지 하나의 효과'로 우기면 과장이다 (상관관계에는 다른 요인도 섞여 있다).
-- 그래서 절반만 — 약 15.5pp만 — 젤리보상 넛지의 가정 효과로 잡았다. (이 절반 비율 자체도
-- 우리가 고른 보수적인 가정값이라, 발표에서 "왜 절반이냐"고 물으면 "상관관계를 그대로 인과로
-- 우기지 않으려는 보수적 처리"라고 답하면 된다.)
--
-- '전체 15.5pp 개선'을 어느 사람들에게 적용할지: 원래도 안 떠날 사람을 더 안 떠나게 만들 수는
-- 없으니(이미 100%), '원래 떠났을 사람'(churn_actual=1) 중 일부만 넛지로 구제되는 걸로 계산한다.
-- 그래서 구제 확률 = 목표 전체 개선폭(0.1551) ÷ control 집단의 실제 이탈률.
WITH control_base AS (
    SELECT AVG(p.churn_actual) AS churn_rate      -- control 집단의 실제 이탈률 (부풀림 없는 진짜 값)
    FROM ab_assignment a JOIN predictions p USING (user_id)
    WHERE a.experiment = '젤리보상' AND a.arm = 'control'
),
assumed AS (
    SELECT 0.1551 / (SELECT churn_rate FROM control_base) AS rescue_rate,  -- 이탈할 사람 중 구제 확률
           0.05  AS control_edit_rate,     -- control 도 자연히 프로필을 고치는 사람이 있다고 가정한 기준선
           0.30  AS treatment_edit_rate    -- 넛지를 받은 사람 중 30%가 실제로 반응해 프로필을 고친다고 가정
)
INSERT INTO outcomes (user_id, measured_at, retained_30d, profile_edited)
SELECT
    a.user_id,
    now(),
    CASE
        WHEN a.arm = 'control' THEN (1 - p.churn_actual)         -- 진짜: 개입 없었던 실제 역사
        WHEN p.churn_actual = 0 THEN 1                            -- treatment 인데 원래도 안 떠날 사람은 그대로 유지
        ELSE (random() < LEAST(1.0, assumed.rescue_rate))::int    -- 원래 떠났을 사람 중 일부를 구제
    END AS retained_30d,
    CASE
        WHEN a.arm = 'control' THEN (random() < assumed.control_edit_rate)::int
        ELSE (random() < assumed.treatment_edit_rate)::int
    END AS profile_edited
FROM ab_assignment a
JOIN predictions p USING (user_id)
CROSS JOIN assumed
WHERE a.experiment = '젤리보상';


-- 3) 확인 — 배정이 공정했는지, 결과가 그럴듯하게 나왔는지
SELECT arm AS 집단, COUNT(*) AS 인원,
       ROUND(AVG(p.churn_prob)::numeric * 100, 1) AS 평균위험도
FROM ab_assignment a JOIN predictions p USING (user_id)
WHERE a.experiment = '젤리보상' GROUP BY arm;

SELECT a.arm AS 집단, COUNT(*) AS 인원,
       ROUND(AVG(o.retained_30d)::numeric * 100, 1) AS 잔존율,
       ROUND(AVG(o.profile_edited)::numeric * 100, 1) AS 프로필수정률
FROM ab_assignment a JOIN outcomes o USING (user_id)
WHERE a.experiment = '젤리보상' GROUP BY a.arm ORDER BY a.arm;
