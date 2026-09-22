-- ⚠️ 이 파일은 public 스키마를 명시합니다.
-- DBeaver 편집기가 다른 스키마를 보고 있어도 그대로 실행됩니다.
SET search_path TO public;

-- ════════════════════════════════════════════════════════════
-- DBeaver에서 하나씩 실행해 보는 확인용 쿼리 모음
-- 실행: 쿼리 위에 커서를 두고  Ctrl + Enter
-- ════════════════════════════════════════════════════════════


-- ① 테이블이 잘 만들어졌나
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;


-- ② 몇 행 들어왔나
SELECT split, COUNT(*) AS 인원,
       ROUND(AVG(churn_actual)::numeric * 100, 2) AS 이탈률
FROM public.predictions
GROUP BY split;


-- ③ 가장 위험한 20명  ← 제품의 핵심 화면
SELECT user_id,
       ROUND(churn_prob::numeric * 100, 1) AS 위험도,
       risk_tier AS 등급,
       age AS 나이, sex AS 성별, job AS 직업,
       essay_count AS 자기소개칸,
       reason_1 AS 주요근거
FROM public.v_test
ORDER BY churn_prob DESC
LIMIT 20;


-- ④ Lift 표 (미리 계산해 둔 것)
SELECT * FROM public.lift_summary;


-- ⑤ Lift를 직접 계산해 보기 (윈도우 함수)
SELECT NTILE(10) OVER (ORDER BY churn_prob DESC) AS 위험도_십분위,
       COUNT(*) AS 인원,
       ROUND(AVG(churn_actual)::numeric * 100, 1) AS 실제이탈률
FROM public.v_test
GROUP BY 위험도_십분위
ORDER BY 위험도_십분위;


-- ⑥ 세그먼트 교차표 — 성별 × 등급
SELECT sex AS 성별, risk_tier AS 등급,
       COUNT(*) AS 인원,
       ROUND(AVG(churn_actual)::numeric * 100, 1) AS 실제이탈률
FROM public.v_test
GROUP BY sex, risk_tier
ORDER BY sex, 실제이탈률 DESC;


-- ⑦ 규칙 세그먼트 (CASE WHEN)
SELECT CASE
         WHEN essay_count = 0                             THEN '① 자기소개 0칸'
         WHEN essay_avg_len < 150                         THEN '② 짧게 씀'
         WHEN essay_count = 10 AND essay_avg_len >= 300    THEN '④ 충실히 작성'
         ELSE '③ 보통'
       END AS 세그먼트,
       COUNT(*) AS 인원,
       ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_test
GROUP BY 1
ORDER BY 1;


-- ⑧ 예산 시뮬레이터 — 상위 N명에 개입하면 이탈자 몇 %를 커버하나
WITH ranked AS (
    SELECT churn_actual,
           ROW_NUMBER() OVER (ORDER BY churn_prob DESC) AS 순위,
           SUM(churn_actual) OVER (ORDER BY churn_prob DESC) AS 누적이탈자
    FROM public.v_test
)
SELECT 순위 AS 개입대상수,
       누적이탈자,
       ROUND(누적이탈자::numeric * 100 /
             (SELECT SUM(churn_actual) FROM public.v_test), 1) AS 커버율
FROM ranked
WHERE 순위 % 500 = 0
ORDER BY 순위;


-- ⑨ 가장 흔한 이탈 근거 TOP 5
SELECT reason_1 AS 주요근거,
       COUNT(*) AS 인원,
       ROUND(AVG(churn_prob)::numeric * 100, 1) AS 평균위험도
FROM public.v_test
WHERE risk_tier = 'High'
GROUP BY reason_1
ORDER BY 인원 DESC
LIMIT 5;


-- ⑩ 모델 vs 직관 불일치 — 열심히 썼는데도 위험한 사람
SELECT user_id,
       ROUND(churn_prob::numeric * 100, 1) AS 위험도,
       essay_count, ROUND(essay_avg_len::numeric) AS 칸당길이,
       ROUND(profile_completeness::numeric, 2) AS 완성도,
       reason_1
FROM public.v_test
WHERE churn_prob > 0.7
  AND essay_count >= 8
  AND profile_completeness > 0.8
ORDER BY churn_prob DESC
LIMIT 10;


-- ⑪ 메타 정보 — 어떤 모델로 만든 DB인가
SELECT * FROM public.meta;
