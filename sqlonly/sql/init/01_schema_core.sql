-- ════════════════════════════════════════════════════════════
-- 핵심 스키마 — 지금 실제로 데이터가 들어가는 테이블
-- predictions / lift_summary / meta + 안전장치 뷰 2개
-- 컨테이너가 "처음 만들어질 때 한 번" 자동 실행된다.
-- 수정 후 반영:  docker compose down -v && docker compose up -d
-- ════════════════════════════════════════════════════════════


-- ── 1. 예측 결과 (메인) ───────────────────────────────────────
-- 학습 피처 20개 + 예측 결과 + 화면용 원본 2개
CREATE TABLE predictions (
    user_id              INTEGER      PRIMARY KEY,   -- 원본 CSV 행 번호
    split                VARCHAR(10)  NOT NULL,      -- 'train' | 'test'
    churn_actual         SMALLINT     NOT NULL,      -- 실제 이탈 여부 0/1
    churn_prob           REAL         NOT NULL,      -- 모델이 계산한 이탈 확률
    rank_pct             REAL,                       -- 위험도 백분위 (작을수록 위험)
    risk_tier            VARCHAR(10),                -- 'High' | 'Medium' | 'Low'

    -- ── 학습 피처 20개 ──
    -- 자기소개 관련 (H1 가설)
    essay_count          SMALLINT,    -- 작성 칸 수 0~10
    essay_total_words    INTEGER,     -- 총 단어 수
    essay_avg_len        REAL,        -- 칸당 평균 글자 수
    essay_len_std        REAL,        -- 칸별 길이 편차
    profile_completeness REAL,        -- 프로필 17개 항목 응답 비율 0~1

    -- 상태 (H2 가설)
    status               VARCHAR(20), -- single / available / seeing someone / married / unknown

    -- 소득 (H3 가설) — NULL이면 미공개
    income               REAL,

    -- 인적 속성
    age                  REAL,
    height               REAL,
    job                  VARCHAR(50),
    edu_level            VARCHAR(30),
    edu_status           VARCHAR(20),
    religion_type        VARCHAR(20),
    diet_type            VARCHAR(20),
    diet_strict          VARCHAR(30),
    drugs_level          REAL,
    smokes_level         REAL,
    has_kids             VARCHAR(15),
    has_kids_na          SMALLINT,
    wants_kids           VARCHAR(30),

    -- ── 학습에 안 쓴 원본 (화면 표시용) ──
    sex                  VARCHAR(5),
    location             TEXT,

    -- ── 예측 근거 (SHAP 상위 3개) ──
    reason_1             TEXT,
    reason_2             TEXT,
    reason_3             TEXT
);

COMMENT ON TABLE  predictions            IS '사용자별 이탈 확률 예측 결과';
COMMENT ON COLUMN predictions.split      IS 'train은 모델이 정답을 본 데이터. 성능 계산은 반드시 test로만';
COMMENT ON COLUMN predictions.churn_prob IS '0~1. 1에 가까울수록 이탈 위험 높음';
COMMENT ON COLUMN predictions.income     IS 'NULL이면 소득 미공개 (원본의 -1)';

CREATE INDEX idx_pred_prob  ON predictions (churn_prob DESC);
CREATE INDEX idx_pred_split ON predictions (split);
CREATE INDEX idx_pred_tier  ON predictions (risk_tier);
CREATE INDEX idx_pred_essay ON predictions (essay_count);
CREATE INDEX idx_pred_seg   ON predictions (sex, status);


-- ── 2. Lift 요약 (발표용) ─────────────────────────────────────
CREATE TABLE lift_summary (
    bucket      VARCHAR(20) PRIMARY KEY,
    n           INTEGER,
    churn_rate  REAL,
    lift        REAL
);


-- ── 3. 메타 정보 (재현성 기록) ────────────────────────────────
CREATE TABLE meta (
    built_at    TIMESTAMP,
    model_file  TEXT,
    churn_days  INTEGER,
    n_rows      INTEGER,
    n_features  INTEGER
);


-- ════════════════════════════════════════════════════════════
-- 파생 뷰 — 쿼리를 짧게 만들고 실수를 막는다
-- ════════════════════════════════════════════════════════════

-- split 필터를 깜빡하지 않도록. 성능·Lift는 항상 이 뷰로.
CREATE VIEW v_test AS
SELECT * FROM predictions WHERE split = 'test';

COMMENT ON VIEW v_test IS '평가용 데이터만. 성능 지표는 항상 이 뷰로 계산할 것';


-- 가설 검증용 파생 컬럼을 미리 붙여둔 뷰
CREATE VIEW v_user AS
SELECT
    p.*,
    -- H2: 적극적으로 상대를 찾는 중인가
    CASE WHEN status IN ('single', 'available') THEN 1 ELSE 0 END AS actively_looking,
    -- H3: 소득을 공개했는가
    CASE WHEN income IS NOT NULL THEN 1 ELSE 0 END                AS income_disclosed,
    -- H1-1: 자기소개를 한 칸도 안 썼는가
    CASE WHEN essay_count = 0 THEN 1 ELSE 0 END                   AS essay_empty,
    -- 프로필 완성도 구간
    CASE
        WHEN profile_completeness < 0.50 THEN '1_매우낮음'
        WHEN profile_completeness < 0.65 THEN '2_낮음'
        WHEN profile_completeness < 0.80 THEN '3_보통'
        WHEN profile_completeness < 0.95 THEN '4_높음'
        ELSE                                   '5_매우높음'
    END AS completeness_band
FROM predictions p;

COMMENT ON VIEW v_user IS '가설 검증용 파생 컬럼(actively_looking, income_disclosed 등)을 붙인 뷰';


