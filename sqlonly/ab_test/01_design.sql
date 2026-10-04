-- ════════════════════════════════════════════════════════════
-- A/B 테스트 — 대상 선정과 무작위 배정
--
-- ⚠️ 이 파일의 INSERT는 주석 처리돼 있다.
--    실제 서비스 데이터가 들어온 뒤에 푸는 것이 전제다.
--    지금은 "이렇게 설계했다"를 보여주는 문서 겸 쿼리다.
-- ════════════════════════════════════════════════════════════


-- ════════════════════════════════════════════════════════════
-- 1단계 · 실험 대상 정하기
--
-- 전원에게 개입하면 효과를 알 수 없다. 개입이 의미 있는 집단만 고른다.
-- 예) 실험명 '온보딩_최소요건' → 자기소개를 덜 쓴 High 위험군
-- ════════════════════════════════════════════════════════════
SELECT
    COUNT(*)                                        AS 실험대상,
    ROUND(AVG(churn_prob)::numeric * 100, 1)        AS 평균위험도,
    ROUND(AVG(churn_actual)::numeric * 100, 1)      AS 현재이탈률
FROM v_test
WHERE risk_tier = 'High'
  AND essay_count <= 7;


-- ════════════════════════════════════════════════════════════
-- 2단계 · 무작위로 반씩 나누기
--
-- treatment = 개입한다 · control = 아무것도 안 한다
-- random() 으로 나누는 게 핵심이다. 조건으로 나누면 두 집단이 애초에 달라져서
-- 나중에 차이가 나도 개입 덕분인지 원래 다른 사람들이었는지 구분할 수 없다.
-- ════════════════════════════════════════════════════════════
-- INSERT INTO ab_assignment (user_id, experiment, arm)
-- SELECT user_id,
--        '온보딩_최소요건',
--        CASE WHEN random() < 0.5 THEN 'treatment' ELSE 'control' END
-- FROM predictions
-- WHERE risk_tier = 'High' AND essay_count <= 7;


-- ════════════════════════════════════════════════════════════
-- 3단계 · 배정이 공정했는지 확인  ← 빼먹으면 안 되는 단계
--
-- 두 집단의 평균 위험도가 비슷해야 한다.
-- 한쪽이 눈에 띄게 높으면 재배정한다. (random()을 다시 돌린다)
-- ════════════════════════════════════════════════════════════
SELECT
    a.arm                                        AS 집단,
    COUNT(*)                                     AS 인원,
    ROUND(AVG(p.churn_prob)::numeric * 100, 1)   AS 평균위험도,
    ROUND(AVG(p.essay_count)::numeric, 2)        AS 평균자기소개칸,
    ROUND(AVG(p.profile_completeness)::numeric, 3) AS 평균완성도
FROM ab_assignment a
JOIN predictions p USING (user_id)
WHERE a.experiment = '온보딩_최소요건'
GROUP BY a.arm
ORDER BY a.arm;


-- ════════════════════════════════════════════════════════════
-- 4단계 · 개입 발송 대상 뽑기 (treatment 집단만)
--
-- control 집단에는 절대 보내면 안 된다. 보내는 순간 실험이 무효가 된다.
-- ════════════════════════════════════════════════════════════
SELECT
    p.user_id,
    ROUND(p.churn_prob::numeric * 100, 1) AS 위험도,
    p.essay_count                          AS 현재칸수,
    '자기소개 ' || LEAST(3, 10 - p.essay_count) || '칸만 더 쓰면 노출이 늘어납니다'
                                           AS 푸시문구
FROM ab_assignment a
JOIN predictions p USING (user_id)
LEFT JOIN campaigns c
       ON c.user_id = p.user_id AND c.action = '넛지푸시_3칸'
WHERE a.experiment = '온보딩_최소요건'
  AND a.arm        = 'treatment'      -- ★ 이 조건이 핵심
  AND c.id IS NULL                    -- 중복 발송 방지
ORDER BY p.churn_prob DESC;


-- 발송 후 이력 남기기
-- INSERT INTO campaigns (user_id, action, note)
-- SELECT p.user_id, '넛지푸시_3칸', '실험: 온보딩_최소요건 / treatment'
-- FROM ab_assignment a
-- JOIN predictions p USING (user_id)
-- LEFT JOIN campaigns c ON c.user_id = p.user_id AND c.action = '넛지푸시_3칸'
-- WHERE a.experiment = '온보딩_최소요건' AND a.arm = 'treatment' AND c.id IS NULL;


-- ════════════════════════════════════════════════════════════
-- 5단계 · 30일 뒤 결과 기록 (실제 서비스에서 배치로 수행)
-- ════════════════════════════════════════════════════════════
-- INSERT INTO outcomes (user_id, measured_at, retained_30d, profile_edited)
-- SELECT user_id, now(), <30일 내 접속 여부>, <프로필 수정 여부>
-- FROM ab_assignment WHERE experiment = '온보딩_최소요건';

-- → 결과 비교는 03_measure.sql 에서
