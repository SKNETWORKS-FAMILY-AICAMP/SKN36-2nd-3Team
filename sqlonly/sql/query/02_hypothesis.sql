-- ⚠️ 이 파일은 public 스키마를 명시합니다.
-- DBeaver 편집기가 다른 스키마를 보고 있어도 그대로 실행됩니다.
SET search_path TO public;

-- ════════════════════════════════════════════════════════════
-- 가설 검증 쿼리 — H1-1 ~ H3
--
-- 사용법: 쿼리 위에 커서를 두고 Ctrl + Enter
-- 주의:   전부 v_user + split='test' 기준. train은 모델이 정답을 본 데이터라 제외.
-- ════════════════════════════════════════════════════════════


-- ════════════════════════════════════════════════════════════
-- H1-1  자기소개를 한 칸도 작성하지 않은 사용자는
--       작성한 사용자보다 이탈률이 높을 것이다.
--
-- 검증법: 0칸 집단과 1칸 이상 집단의 이탈률을 비교한다.
--         두 집단의 차이가 크고, train/test에서 비슷하면 채택.
-- ════════════════════════════════════════════════════════════
SELECT
    CASE WHEN essay_count = 0 THEN '0칸 (미작성)' ELSE '1칸 이상' END AS 집단,
    COUNT(*)                                          AS 인원,
    SUM(churn_actual)                                 AS 이탈자,
    ROUND(AVG(churn_actual)::numeric * 100, 1)        AS 이탈률
FROM public.v_user
WHERE split = 'test'
GROUP BY 1
ORDER BY 1;

-- 같은 비교를 train/test 양쪽에서 → 재현되는지 확인 (흔들림 검사)
SELECT
    split,
    CASE WHEN essay_count = 0 THEN '0칸' ELSE '1칸+' END AS 집단,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_user
GROUP BY split, 2
ORDER BY 2, split;


-- ════════════════════════════════════════════════════════════
-- H1-2  자기소개 작성 개수가 증가할수록 이탈률은 감소할 것이다.
--
-- 검증법: 0~10칸별 이탈률이 "계단처럼 단조 감소"하는지 본다.
--         중간에 튀는 구간이 있으면 단조성 기각.
-- ════════════════════════════════════════════════════════════
SELECT
    essay_count                                AS 작성칸수,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률,
    -- 바로 앞 구간 대비 변화량. 전부 음수여야 단조 감소.
    ROUND(AVG(churn_actual)::numeric * 100
          - LAG(AVG(churn_actual)::numeric * 100)
            OVER (ORDER BY essay_count), 1)    AS 직전대비
FROM public.v_user
WHERE split = 'test'
GROUP BY essay_count
ORDER BY essay_count;


-- ════════════════════════════════════════════════════════════
-- H1-3  자기소개 총길이가 증가할수록 이탈률은 감소하지만,
--       일정 길이 이후 감소 효과는 작아질 것이다  (체감 효과)
--
-- 검증법: 길이를 10등분(십분위)해서 구간별 이탈률을 본다.
--         앞쪽 구간의 낙차가 크고 뒤쪽이 평평해지면 채택.
-- ════════════════════════════════════════════════════════════
WITH binned AS (
    SELECT NTILE(10) OVER (ORDER BY essay_total_words) AS 십분위,
           essay_total_words,
           churn_actual
    FROM public.v_user
    WHERE split = 'test' AND essay_total_words IS NOT NULL
)
SELECT
    십분위,
    MIN(essay_total_words)                     AS 최소단어,
    MAX(essay_total_words)                     AS 최대단어,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률,
    ROUND(AVG(churn_actual)::numeric * 100
          - LAG(AVG(churn_actual)::numeric * 100) OVER (ORDER BY 십분위), 1) AS 직전대비
FROM binned
GROUP BY 십분위
ORDER BY 십분위;

-- 체감 효과를 한눈에: 앞쪽 절반 vs 뒤쪽 절반의 평균 낙차 비교
WITH binned AS (
    SELECT NTILE(10) OVER (ORDER BY essay_total_words) AS q, churn_actual
    FROM public.v_user WHERE split = 'test' AND essay_total_words IS NOT NULL
), rates AS (
    SELECT q, AVG(churn_actual) * 100 AS rate FROM binned GROUP BY q
)
SELECT
    ROUND((MAX(rate) FILTER (WHERE q = 1) - MAX(rate) FILTER (WHERE q = 5))::numeric, 1) AS 앞쪽_1에서5_낙차,
    ROUND((MAX(rate) FILTER (WHERE q = 6) - MAX(rate) FILTER (WHERE q = 10))::numeric, 1) AS 뒤쪽_6에서10_낙차
FROM rates;
-- 앞쪽 낙차 >> 뒤쪽 낙차 이면 H1-3 채택


-- ════════════════════════════════════════════════════════════
-- H1-4  전체 프로필 완성도가 높을수록 이탈률은 낮을 것이다.
--
-- 검증법: 완성도 구간(v_user.completeness_band)별 이탈률.
-- ════════════════════════════════════════════════════════════
SELECT
    completeness_band                          AS 완성도구간,
    COUNT(*)                                   AS 인원,
    ROUND(MIN(profile_completeness)::numeric, 2) AS 최소,
    ROUND(MAX(profile_completeness)::numeric, 2) AS 최대,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_user
WHERE split = 'test'
GROUP BY completeness_band
ORDER BY completeness_band;


-- ════════════════════════════════════════════════════════════
-- H2   적극적으로 상대를 찾는 사용자는
--      그렇지 않은 사용자보다 이탈률이 낮을 것이다.
--
-- actively_looking = status IN ('single','available')
-- ════════════════════════════════════════════════════════════
SELECT
    CASE actively_looking WHEN 1 THEN '적극적 (single/available)'
                          ELSE '비적극 (연애중·기혼·미기재)' END AS 집단,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_user
WHERE split = 'test'
GROUP BY actively_looking
ORDER BY actively_looking DESC;

-- status 원본값별로 더 자세히
SELECT
    status,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_user
WHERE split = 'test'
GROUP BY status
ORDER BY 이탈률 DESC;


-- ════════════════════════════════════════════════════════════
-- H3   소득 공개 여부는 프로필 참여도의 단순한 지표가 아니며,
--      다른 사용자 특성에 따라 효과가 달라질 것이다.  (조절효과)
--
-- 검증법 3단계:
--   ① 단독 효과 — 공개 vs 미공개
--   ② 완성도를 고정하고 봐도 같은 방향인가
--   ③ 완성도 구간마다 효과의 크기·방향이 달라지는가  ← 이게 핵심
-- ════════════════════════════════════════════════════════════

-- ① 단독 효과
SELECT
    CASE income_disclosed WHEN 1 THEN '소득 공개' ELSE '미공개' END AS 집단,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM public.v_user
WHERE split = 'test'
GROUP BY income_disclosed
ORDER BY income_disclosed DESC;

-- ②③ 완성도 구간 × 소득공개 교차표 (조절효과 확인)
SELECT
    completeness_band AS 완성도구간,
    ROUND(AVG(churn_actual) FILTER (WHERE income_disclosed = 1)::numeric * 100, 1) AS 공개_이탈률,
    ROUND(AVG(churn_actual) FILTER (WHERE income_disclosed = 0)::numeric * 100, 1) AS 미공개_이탈률,
    ROUND((AVG(churn_actual) FILTER (WHERE income_disclosed = 1)
         - AVG(churn_actual) FILTER (WHERE income_disclosed = 0))::numeric * 100, 1) AS 차이,
    COUNT(*) FILTER (WHERE income_disclosed = 1) AS 공개_인원,
    COUNT(*) FILTER (WHERE income_disclosed = 0) AS 미공개_인원
FROM public.v_user
WHERE split = 'test'
GROUP BY completeness_band
ORDER BY completeness_band;
-- 구간마다 '차이'의 부호나 크기가 달라지면 → 조절효과 있음 → H3 채택

-- 성별로도 갈리는지
SELECT
    sex AS 성별,
    ROUND(AVG(churn_actual) FILTER (WHERE income_disclosed = 1)::numeric * 100, 1) AS 공개_이탈률,
    ROUND(AVG(churn_actual) FILTER (WHERE income_disclosed = 0)::numeric * 100, 1) AS 미공개_이탈률,
    ROUND((AVG(churn_actual) FILTER (WHERE income_disclosed = 1)
         - AVG(churn_actual) FILTER (WHERE income_disclosed = 0))::numeric * 100, 1) AS 차이
FROM public.v_user
WHERE split = 'test'
GROUP BY sex;


-- ════════════════════════════════════════════════════════════
-- 보너스 — 가설 검증 결과를 한 표로 정리
-- 발표 자료에 그대로 붙일 수 있는 형태
-- ════════════════════════════════════════════════════════════
WITH h AS (
    SELECT 'H1-1  자기소개 0칸'          AS 가설,
           AVG(churn_actual) FILTER (WHERE essay_count = 0)  AS 해당,
           AVG(churn_actual) FILTER (WHERE essay_count > 0)  AS 반대,
           COUNT(*) FILTER (WHERE essay_count = 0)           AS 해당인원
    FROM public.v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H1-4  완성도 하위 (<0.5)',
           AVG(churn_actual) FILTER (WHERE profile_completeness < 0.5),
           AVG(churn_actual) FILTER (WHERE profile_completeness >= 0.5),
           COUNT(*) FILTER (WHERE profile_completeness < 0.5)
    FROM public.v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H2    비적극 (연애중·기혼)',
           AVG(churn_actual) FILTER (WHERE actively_looking = 0),
           AVG(churn_actual) FILTER (WHERE actively_looking = 1),
           COUNT(*) FILTER (WHERE actively_looking = 0)
    FROM public.v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H3    소득 공개',
           AVG(churn_actual) FILTER (WHERE income_disclosed = 1),
           AVG(churn_actual) FILTER (WHERE income_disclosed = 0),
           COUNT(*) FILTER (WHERE income_disclosed = 1)
    FROM public.v_user WHERE split = 'test'
)
SELECT 가설,
       해당인원,
       ROUND(해당::numeric * 100, 1) AS 해당집단_이탈률,
       ROUND(반대::numeric * 100, 1) AS 반대집단_이탈률,
       ROUND((해당 / NULLIF(반대, 0))::numeric, 2) AS 배수
FROM h
ORDER BY 배수 DESC;
