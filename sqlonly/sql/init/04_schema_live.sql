-- ════════════════════════════════════════════════════════════
-- 실시간 진단 스키마 — SERVICE 화면이 쓰는 테이블
--
-- predictions        : 학습 데이터 59,946명 (과거, 고정)
-- predictions_live   : 화면에서 방금 진단한 프로필 (현재, 계속 쌓임)
--
-- service/predict.py 의 ChurnPredictor.save() 가 여기에 INSERT 한다.
-- 컨테이너가 "처음 만들어질 때 한 번" 자동 실행된다.
-- 수정 후 반영:  docker compose down -v && docker compose up -d
-- ════════════════════════════════════════════════════════════


-- ── 1. 진단 이력 ─────────────────────────────────────────────
-- 화면에서 [진단하기]를 누를 때마다 한 행씩 쌓인다.
CREATE TABLE predictions_live (
    id                   SERIAL       PRIMARY KEY,
    created_at           TIMESTAMP    NOT NULL DEFAULT now(),

    -- 예측 결과
    churn_prob           REAL         NOT NULL,      -- 0 ~ 1
    risk_tier            VARCHAR(10)  NOT NULL,      -- 'High' | 'Medium' | 'Low'

    -- 입력값 중 화면에 다시 보여줄 것들
    age                  REAL,
    sex                  VARCHAR(5),
    status               VARCHAR(30),
    job                  VARCHAR(50),
    essay_count          SMALLINT,
    profile_completeness REAL,

    -- 왜 그렇게 나왔는가 (SHAP 상위 3개)
    reason_1             VARCHAR(60),
    reason_2             VARCHAR(60),
    reason_3             VARCHAR(60),

    -- 추적용
    model_file           VARCHAR(100),               -- 어떤 .cbm 으로 뽑았나
    note                 TEXT                        -- 데모 메모 등 자유 입력
);

CREATE INDEX idx_live_created ON predictions_live (created_at DESC);
CREATE INDEX idx_live_tier    ON predictions_live (risk_tier);


-- ════════════════════════════════════════════════════════════
-- 2. 화면용 뷰
-- ════════════════════════════════════════════════════════════

-- ── 최근 진단 20건 — SERVICE 화면 하단 "최근 진단 내역" ──────
DROP VIEW IF EXISTS v_live_recent;
CREATE VIEW v_live_recent AS
SELECT
    id                                          AS 번호,
    to_char(created_at, 'MM-DD HH24:MI')        AS 진단시각,
    ROUND(churn_prob::numeric * 100, 1)         AS 위험도,
    risk_tier                                   AS 등급,
    age                                         AS 나이,
    sex                                         AS 성별,
    status                                      AS 연애상태,
    essay_count                                 AS 자기소개칸,
    ROUND(profile_completeness::numeric, 2)     AS 완성도,
    reason_1                                    AS 주요근거
FROM predictions_live
ORDER BY created_at DESC
LIMIT 20;


-- ── 오늘 요약 — 관리자 화면 상단 카드 ────────────────────────
DROP VIEW IF EXISTS v_live_today;
CREATE VIEW v_live_today AS
SELECT
    COUNT(*)                                                    AS 오늘진단수,
    COUNT(*) FILTER (WHERE risk_tier = 'High')                  AS 고위험,
    COUNT(*) FILTER (WHERE risk_tier = 'Medium')                AS 중간,
    COUNT(*) FILTER (WHERE risk_tier = 'Low')                   AS 안정,
    ROUND(AVG(churn_prob)::numeric * 100, 1)                    AS 평균위험도
FROM predictions_live
WHERE created_at >= date_trunc('day', now());


-- ── 근거 순위 — "우리 앱 사용자는 주로 무엇 때문에 위험한가" ──
DROP VIEW IF EXISTS v_live_reason;
CREATE VIEW v_live_reason AS
SELECT
    reason_1                                    AS 주요근거,
    COUNT(*)                                    AS 건수,
    ROUND(AVG(churn_prob)::numeric * 100, 1)    AS 평균위험도
FROM predictions_live
WHERE reason_1 IS NOT NULL
GROUP BY reason_1
ORDER BY 건수 DESC;


-- ── 학습 데이터 vs 실제 진단 비교 ────────────────────────────
-- 화면에서 들어오는 프로필이 학습 데이터와 비슷한 분포인지 본다.
-- 많이 다르면 모델을 다시 학습해야 한다는 신호다.
DROP VIEW IF EXISTS v_live_vs_train;
CREATE VIEW v_live_vs_train AS
SELECT '학습데이터(test)' AS 구분,
       COUNT(*)                                       AS 인원,
       ROUND(AVG(churn_prob)::numeric * 100, 1)       AS 평균위험도,
       ROUND(AVG(essay_count)::numeric, 2)            AS 평균자기소개칸,
       ROUND(AVG(profile_completeness)::numeric, 3)   AS 평균완성도
FROM predictions WHERE split = 'test'
UNION ALL
SELECT '실시간 진단',
       COUNT(*),
       ROUND(AVG(churn_prob)::numeric * 100, 1),
       ROUND(AVG(essay_count)::numeric, 2),
       ROUND(AVG(profile_completeness)::numeric, 3)
FROM predictions_live;


-- ════════════════════════════════════════════════════════════
-- 3. 동작 확인용 샘플 (DB만 먼저 보고 싶을 때)
--    실제 진단이 쌓이기 시작하면 지워도 된다.
--    DELETE FROM predictions_live WHERE note = 'sample';
-- ════════════════════════════════════════════════════════════
INSERT INTO predictions_live
    (churn_prob, risk_tier, age, sex, status, job,
     essay_count, profile_completeness,
     reason_1, reason_2, reason_3, model_file, note)
VALUES
    (0.79, 'High',   27, 'm', 'single', NULL, 1, 0.12,
     '자기소개 작성 칸 수 (위험 ↑)', '자기소개 길이 편차 (위험 ↑)', '자녀 유무 (위험 ↑)',
     'sample.cbm', 'sample'),
    (0.54, 'Medium', 27, 'm', 'single', NULL, 0, 0.06,
     '키 (위험 ↑)', '자기소개 작성 칸 수 (위험 ↑)', '프로필 완성도 (위험 ↑)',
     'sample.cbm', 'sample'),
    (0.32, 'Low',    31, 'f', 'single', 'science / tech / engineering', 10, 1.00,
     '자녀 희망 (안정 ↓)', '자기소개 칸당 분량 (안정 ↓)', '프로필 완성도 (안정 ↓)',
     'sample.cbm', 'sample');
