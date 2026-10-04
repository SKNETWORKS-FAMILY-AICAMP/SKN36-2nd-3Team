-- ════════════════════════════════════════════════════════════
-- 화면용 뷰 — UI 담당자는 이 뷰만 SELECT 하면 된다.
--
-- 규칙
--   · UI 코드에 긴 SQL을 넣지 않는다. 여기서 뷰로 만들어 넘긴다.
--   · 집계 값은 전부 test 기준(v_test). train은 모델이 정답을 본 데이터.
--   · 컬럼명은 한글로 내보낸다 → 차트 라벨을 그대로 쓸 수 있다.
--
-- 실행:  DBeaver에서 이 파일을 열고 Alt + X (전체 실행)
-- ════════════════════════════════════════════════════════════

DROP VIEW IF EXISTS v_insight_risk;
DROP VIEW IF EXISTS v_insight_completeness;
DROP VIEW IF EXISTS v_insight_essay;
DROP VIEW IF EXISTS v_insight_reason;
DROP VIEW IF EXISTS v_insight_calibration;
DROP VIEW IF EXISTS v_insight_segment;
DROP VIEW IF EXISTS v_retention_action;
DROP VIEW IF EXISTS v_retention_list;
DROP VIEW IF EXISTS v_about_hypothesis;


-- ════════════════════════════════════════════════════════════
-- 1. v_insight_risk — 위험군 분포
--    화면: INSIGHT 최상단 / 차트: 도넛 또는 가로 막대 3개
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_risk AS
SELECT
    risk_tier                                                       AS 등급,
    COUNT(*)                                                        AS 인원,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)              AS 비율,
    ROUND(AVG(churn_actual)::numeric * 100, 1)                      AS 실제이탈률,
    CASE risk_tier WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END AS 정렬
FROM v_test
GROUP BY risk_tier;

COMMENT ON VIEW v_insight_risk IS '위험 등급(High/Medium/Low)별 인원·비율·실제 이탈률. INSIGHT 최상단 도넛/막대용';


-- ════════════════════════════════════════════════════════════
-- 2. v_insight_completeness — 프로필 완성도별 이탈률
--    화면: INSIGHT / 차트: 세로 막대 (왼→오 감소해야 정상)
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_completeness AS
SELECT
    completeness_band                          AS 완성도구간,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM v_user
WHERE split = 'test'
GROUP BY completeness_band;

COMMENT ON VIEW v_insight_completeness IS '프로필 완성도 5구간(v_user.completeness_band 기준)별 실제 이탈률. INSIGHT용';


-- ════════════════════════════════════════════════════════════
-- 3. v_insight_essay — 자기소개 작성 칸 수별 이탈률
--    화면: INSIGHT / 차트: 세로 막대 11개 (0~10칸)
--    ★ 0칸 → 1칸 낙차가 가장 크다. 그 지점을 강조 색으로.
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_essay AS
SELECT
    essay_count                                AS 작성칸수,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률,
    ROUND(AVG(churn_actual)::numeric * 100
          - LAG(AVG(churn_actual)::numeric * 100) OVER (ORDER BY essay_count), 1)
                                               AS 직전대비
FROM v_test
GROUP BY essay_count;

COMMENT ON VIEW v_insight_essay IS '자기소개 작성 칸 수(0~10)별 실제 이탈률과 직전 칸 대비 변화량. INSIGHT용';


-- ════════════════════════════════════════════════════════════
-- 4. v_insight_reason — 고위험 판정 사유 TOP
--    화면: INSIGHT / 차트: 가로 막대 또는 그냥 표
--    ★ SHAP을 한글 문장으로 미리 바꿔둔 것. 막대그래프보다 잘 읽힌다.
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_reason AS
SELECT
    reason_1                                   AS 주요근거,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_prob)::numeric * 100, 1)   AS 평균위험도
FROM v_test
WHERE risk_tier = 'High'
GROUP BY reason_1;

COMMENT ON VIEW v_insight_reason IS 'High 등급 사용자의 1순위 위험 근거(reason_1)별 인원·평균 위험도. INSIGHT용';


-- ════════════════════════════════════════════════════════════
-- 5. v_insight_calibration — 모델 신뢰도 (예측 vs 실제)
--    화면: ABOUT / 차트: 선 2개 겹치기 (예측선 · 실제선)
--    ★ "이 등급 믿어도 되나요?"에 대한 답. 두 선이 붙어 있으면 신뢰 가능.
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_calibration AS
SELECT
    CASE WHEN churn_prob >= 0.7 THEN '0.7 ~ 1.0'
         WHEN churn_prob >= 0.6 THEN '0.6 ~ 0.7'
         WHEN churn_prob >= 0.5 THEN '0.5 ~ 0.6'
         WHEN churn_prob >= 0.4 THEN '0.4 ~ 0.5'
         WHEN churn_prob >= 0.3 THEN '0.3 ~ 0.4'
         ELSE                        '0.0 ~ 0.3' END AS 예측확률구간,
    COUNT(*)                                        AS 인원,
    ROUND(AVG(churn_prob)::numeric * 100, 1)        AS 평균예측확률,
    ROUND(AVG(churn_actual)::numeric * 100, 1)      AS 실제이탈률
FROM v_test
GROUP BY 1;

COMMENT ON VIEW v_insight_calibration IS '예측 확률 구간별 평균 예측 확률 vs 실제 이탈률 비교 (모델 신뢰도 확인용). ABOUT용';


-- ════════════════════════════════════════════════════════════
-- 6. v_insight_segment — 세그먼트 교차 (성별 × 연령대 × 등급)
--    화면: INSIGHT 필터 영역 / UI에서 WHERE로 걸러 쓴다
--    예)  WHERE 성별 = 'f' AND 연령대 = '25-29'
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_insight_segment AS
SELECT
    sex AS 성별,
    CASE WHEN age <  25 THEN '18-24'
         WHEN age <  30 THEN '25-29'
         WHEN age <  35 THEN '30-34'
         WHEN age <  45 THEN '35-44'
         ELSE                '45+'  END        AS 연령대,
    risk_tier                                  AS 등급,
    COUNT(*)                                   AS 인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 이탈률
FROM v_test
WHERE age IS NOT NULL
GROUP BY 1, 2, 3;

COMMENT ON VIEW v_insight_segment IS '성별×연령대×위험등급 교차표. INSIGHT 필터 영역에서 WHERE로 걸러 씀';


-- ════════════════════════════════════════════════════════════
-- 7. v_retention_action — 개입 그룹별 대상 규모
--    화면: RETENTION 메인 / 차트: 표 + 인원 막대
--    ★ 담당자가 가장 궁금해하는 것 = "그래서 몇 명한테 뭘 하면 되나"
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_retention_action AS
SELECT
    CASE
        WHEN essay_count = 0
             THEN 'A. 자기소개 0칸 → 첫 한 칸 유도'
        WHEN profile_completeness BETWEEN 0.80 AND 0.94
             THEN 'B. 완성 직전 → 마무리 유도'
        WHEN essay_total_words < 255
             THEN 'C. 자기소개 250단어까지 유도'
        ELSE 'D. 개선 여지 낮음 (유지·수익화 대상)'
    END                                        AS 개입그룹,
    COUNT(*)                                   AS 대상인원,
    ROUND(AVG(churn_actual)::numeric * 100, 1) AS 현재이탈률,
    ROUND(AVG(churn_prob)::numeric * 100, 1)   AS 평균위험도
FROM v_test
GROUP BY 1;

COMMENT ON VIEW v_retention_action IS '규칙 기반 개입 그룹(A~D)별 대상 인원·현재 이탈률·평균 위험도. RETENTION 메인용';


-- ════════════════════════════════════════════════════════════
-- 8. v_retention_list — 고위험군 명단 (CSV 다운로드용)
--    화면: RETENTION 하단 / UI: 표 + st.download_button
--    ★ 담당자가 "가져가서 CRM에 넣는" 결과물. 이게 진짜 제품이다.
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_retention_list AS
SELECT
    user_id                                          AS 사용자ID,
    ROUND(churn_prob::numeric * 100, 1)              AS 위험도,
    risk_tier                                        AS 등급,
    sex                                              AS 성별,
    age                                              AS 나이,
    essay_count                                      AS 자기소개칸,
    ROUND(profile_completeness::numeric * 100, 0)    AS 완성도,
    reason_1                                         AS 주요근거,
    CASE
        WHEN essay_count = 0 THEN '첫 자기소개 작성 유도'
        WHEN essay_count <= 7
             THEN '자기소개 ' || LEAST(3, 10 - essay_count) || '칸 추가 유도'
        WHEN profile_completeness < 0.95 THEN '프로필 마무리 유도'
        ELSE '재접속 알림'
    END                                              AS 추천액션
FROM v_test
WHERE risk_tier = 'High';

COMMENT ON VIEW v_retention_list IS 'High 등급 사용자 명단 + 추천 액션. RETENTION 하단 CSV 다운로드용';


-- ════════════════════════════════════════════════════════════
-- 9. v_about_hypothesis — 가설 검증 결과 한 표
--    화면: ABOUT / 차트: 표 그대로
-- ════════════════════════════════════════════════════════════
CREATE VIEW v_about_hypothesis AS
WITH h AS (
    SELECT 'H1  자기소개 미작성'  AS 가설,
           AVG(churn_actual) FILTER (WHERE essay_count = 0) AS 해당,
           AVG(churn_actual) FILTER (WHERE essay_count > 0) AS 반대,
           COUNT(*) FILTER (WHERE essay_count = 0)          AS 해당인원
    FROM v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H2  프로필 완성도 낮음',
           AVG(churn_actual) FILTER (WHERE profile_completeness < 0.5),
           AVG(churn_actual) FILTER (WHERE profile_completeness >= 0.5),
           COUNT(*) FILTER (WHERE profile_completeness < 0.5)
    FROM v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H3  비적극 (연애중·기혼)',
           AVG(churn_actual) FILTER (WHERE actively_looking = 0),
           AVG(churn_actual) FILTER (WHERE actively_looking = 1),
           COUNT(*) FILTER (WHERE actively_looking = 0)
    FROM v_user WHERE split = 'test'
  UNION ALL
    SELECT 'H4  소득 공개',
           AVG(churn_actual) FILTER (WHERE income_disclosed = 1),
           AVG(churn_actual) FILTER (WHERE income_disclosed = 0),
           COUNT(*) FILTER (WHERE income_disclosed = 1)
    FROM v_user WHERE split = 'test'
)
SELECT 가설,
       해당인원,
       ROUND(해당::numeric * 100, 1)              AS 해당집단_이탈률,
       ROUND(반대::numeric * 100, 1)              AS 반대집단_이탈률,
       ROUND((해당 / NULLIF(반대, 0))::numeric, 2) AS 배수
FROM h;

COMMENT ON VIEW v_about_hypothesis IS 'H1~H4 가설 검증 결과를 한 표로 정리. ABOUT용';


-- ── 만들어진 뷰 확인 ─────────────────────────────────────────
SELECT table_name AS 뷰이름
FROM information_schema.views
WHERE table_schema = 'public' AND table_name LIKE 'v_%'
ORDER BY table_name;