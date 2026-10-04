-- ⚠️ 이 파일은 public 스키마를 명시합니다.
-- DBeaver 편집기가 다른 스키마를 보고 있어도 그대로 실행됩니다.
SET search_path TO public;

-- ════════════════════════════════════════════════════════════
-- 개입(캠페인) 대상 추출 + 품질 보상 설계
--
-- SQL로 "줄 세우기"가 되니까, 그 줄 앞쪽만 뽑아서 푸시를 보낼 수 있다.
-- 이 파일은 그 발송 대상을 뽑는 쿼리들이다.
-- ════════════════════════════════════════════════════════════


-- ════════════════════════════════════════════════════════════
-- 개입 ①  넛지 푸시 — "3칸 더 쓰면 노출이 늘어납니다"
--
-- 대상 조건
--   · High 위험군 (상위 10%)
--   · 자기소개를 7칸 이하로 썼음 → "3칸 더"가 말이 되는 사람
--   · 이미 같은 푸시를 받은 적 없음
-- ════════════════════════════════════════════════════════════
SELECT
    p.user_id,
    ROUND(p.churn_prob::numeric * 100, 1)              AS 위험도,
    p.essay_count                                      AS 현재칸수,
    10 - p.essay_count                                 AS 남은칸수,
    '자기소개 ' || LEAST(3, 10 - p.essay_count) || '칸만 더 쓰면 노출이 늘어납니다'
                                                       AS 푸시문구,
    p.reason_1                                         AS 선정근거
FROM public.predictions p
LEFT JOIN public.campaigns c
       ON c.user_id = p.user_id
      AND c.action  = '넛지푸시_3칸'
WHERE p.risk_tier  = 'High'
  AND p.essay_count BETWEEN 0 AND 7
  AND c.id IS NULL                      -- 아직 안 보낸 사람만
ORDER BY p.churn_prob DESC
LIMIT 1000;

-- 실제로 발송했다면 이력을 남긴다 (중복 발송 방지)
-- INSERT INTO campaigns (user_id, action, note)
-- SELECT p.user_id, '넛지푸시_3칸', 'High + essay_count<=7'
-- FROM public.predictions p
-- LEFT JOIN public.campaigns c ON c.user_id = p.user_id AND c.action = '넛지푸시_3칸'
-- WHERE p.risk_tier = 'High' AND p.essay_count BETWEEN 0 AND 7 AND c.id IS NULL;


-- ════════════════════════════════════════════════════════════
-- 개입 ②  완성 보상 — 프로필 100% 달성 시 24시간 노출 부스트
--
-- 원가 0원. "완성했다"의 기준을 SQL로 정의한다.
-- ════════════════════════════════════════════════════════════
SELECT
    user_id,
    ROUND(profile_completeness::numeric * 100, 1) AS 완성도,
    essay_count                                   AS 자기소개칸,
    '부스트 24시간'                                AS 보상
FROM public.predictions
WHERE profile_completeness >= 0.95      -- 17개 중 17개 (반올림 여유)
  AND essay_count          >= 8         -- 자기소개도 충분히
ORDER BY profile_completeness DESC, essay_count DESC;

-- 완성 직전인 사람 = 넛지 효율이 가장 높은 구간
SELECT
    user_id,
    ROUND(profile_completeness::numeric * 100, 1) AS 완성도,
    ROUND((0.95 - profile_completeness)::numeric * 17, 0) AS 남은항목수,
    ROUND(churn_prob::numeric * 100, 1)           AS 위험도
FROM public.predictions
WHERE profile_completeness BETWEEN 0.80 AND 0.94
ORDER BY churn_prob DESC
LIMIT 500;
-- "2개만 더 채우면 부스트!" → 가장 싸게 완성률을 올리는 지점


-- ※ 젤리 품질 보상과 A/B 테스트 쿼리는 ab_test/ 폴더로 옮겼습니다.
--   (현재 데이터가 없어 실행되지 않는 것들)
