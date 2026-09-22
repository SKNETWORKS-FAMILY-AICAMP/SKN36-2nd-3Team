-- ════════════════════════════════════════════════════════════
-- A/B 테스트 — 배정과 효과 측정
-- ⚠️ ab_assignment / outcomes 에 데이터가 쌓여야 실행된다.
-- ════════════════════════════════════════════════════════════
-- A/B 테스트 — 개입 효과를 숫자로 증명한다
-- ════════════════════════════════════════════════════════════

-- ① High 위험군을 무작위로 처치군/대조군에 배정
-- INSERT INTO ab_assignment (user_id, experiment, arm)
-- SELECT user_id,
--        '젤리보상',
--        CASE WHEN random() < 0.5 THEN 'treatment' ELSE 'control' END
-- FROM predictions
-- WHERE risk_tier = 'High';

-- ② 배정이 한쪽으로 쏠리지 않았는지 확인 (반반이어야 정상)
SELECT arm AS 집단, COUNT(*) AS 인원,
       ROUND(AVG(p.churn_prob)::numeric * 100, 1) AS 평균위험도
FROM ab_assignment a
JOIN predictions p USING (user_id)
WHERE a.experiment = '젤리보상'
GROUP BY arm;
-- 평균위험도가 두 집단에서 비슷해야 공정한 비교가 된다

-- ③ 30일 후 결과 비교  ← 재계약을 만드는 표
SELECT
    a.arm                                          AS 집단,
    COUNT(*)                                       AS 인원,
    ROUND(AVG(o.retained_30d)::numeric * 100, 1)   AS 잔존율,
    ROUND(AVG(o.profile_edited)::numeric * 100, 1) AS 프로필수정률
FROM ab_assignment a
JOIN outcomes o USING (user_id)
WHERE a.experiment = '젤리보상'
GROUP BY a.arm
ORDER BY a.arm;
