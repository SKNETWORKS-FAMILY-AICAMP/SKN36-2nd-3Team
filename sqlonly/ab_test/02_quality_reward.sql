-- ════════════════════════════════════════════════════════════
-- 젤리 품질 보상 — "길이보다 질"
--
-- ⚠️ profile_feedback / profile_impressions 에 데이터가 있어야 실행된다.
--    현재는 비어 있으므로 결과가 0행이다. 설계를 보여주는 용도.
-- ════════════════════════════════════════════════════════════
-- 개입 ③  젤리 보상 — "길이보다 질"
--
-- 문제: 글자 수로 젤리를 주면 의미 없는 장문이 늘어난다.
-- 해법: 다른 사용자가 남긴 프로필 품질 평가를 기준으로 지급한다.
--       단, 칭찬 수가 아니라 "칭찬 수 ÷ 노출 수"를 쓴다.
-- ════════════════════════════════════════════════════════════

-- 왜 칭찬 수를 그대로 쓰면 안 되나 — 노출이 많으면 칭찬도 많다
SELECT
    NTILE(5) OVER (ORDER BY 노출수) AS 노출_5분위,
    ROUND(AVG(노출수))               AS 평균노출,
    ROUND(AVG(칭찬수), 1)            AS 평균칭찬수,
    ROUND(AVG(칭찬률), 4)            AS 평균칭찬률
FROM v_profile_quality
GROUP BY 노출_5분위
ORDER BY 노출_5분위;
-- 평균칭찬수는 노출과 함께 오르지만, 칭찬률은 평평해야 정상.
-- 칭찬률이 공정한 지표라는 근거가 된다.


-- 젤리 지급 대상 — 칭찬률 상위 + 최소 노출 확보
SELECT
    q.user_id,
    q.노출수,
    q.칭찬수,
    q.칭찬률,
    q.알차요, q.대화쉬움, q.가치관,
    -- 배지 종류가 다양할수록 가산 (한 가지만 몰린 건 신뢰도 낮음)
    (CASE WHEN q.알차요   > 0 THEN 1 ELSE 0 END
   + CASE WHEN q.대화쉬움 > 0 THEN 1 ELSE 0 END
   + CASE WHEN q.가치관   > 0 THEN 1 ELSE 0 END)          AS 배지종류,
    CASE
        WHEN q.칭찬률 >= 0.15 THEN 50
        WHEN q.칭찬률 >= 0.10 THEN 30
        WHEN q.칭찬률 >= 0.05 THEN 10
        ELSE 0
    END                                                    AS 지급젤리
FROM v_profile_quality q
WHERE q.노출수 >= 30          -- 표본이 너무 적으면 칭찬률이 튄다
  AND q.칭찬률 >= 0.05
ORDER BY q.칭찬률 DESC
LIMIT 200;


-- 어뷰징 방지 ① 서로 칭찬 품앗이 탐지
SELECT
    a.from_user_id AS 사용자A,
    a.to_user_id   AS 사용자B,
    COUNT(*)       AS 상호칭찬수
FROM profile_feedback a
JOIN profile_feedback b
  ON a.from_user_id = b.to_user_id
 AND a.to_user_id   = b.from_user_id
GROUP BY a.from_user_id, a.to_user_id
HAVING COUNT(*) >= 2
ORDER BY 상호칭찬수 DESC;

-- 어뷰징 방지 ② 한 사람이 뿌린 칭찬이 비정상적으로 많은 경우
SELECT from_user_id AS 평가자,
       COUNT(*)     AS 뿌린칭찬수,
       COUNT(DISTINCT to_user_id) AS 대상자수
FROM profile_feedback
WHERE created_at >= now() - INTERVAL '7 days'
GROUP BY from_user_id
HAVING COUNT(*) > 50
ORDER BY 뿌린칭찬수 DESC;


-- 젤리 지급 실행 (원장에 기록)
-- INSERT INTO jelly_ledger (user_id, amount, reason)
-- SELECT user_id,
--        CASE WHEN 칭찬률 >= 0.15 THEN 50
--             WHEN 칭찬률 >= 0.10 THEN 30
--             ELSE 10 END,
--        '품질칭찬'
-- FROM v_profile_quality
-- WHERE 노출수 >= 30 AND 칭찬률 >= 0.05;


-- 사용자별 젤리 잔액
SELECT user_id, SUM(amount) AS 잔액
FROM jelly_ledger
GROUP BY user_id
ORDER BY 잔액 DESC
LIMIT 20;
