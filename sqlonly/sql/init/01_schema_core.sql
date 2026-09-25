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
COMMENT ON COLUMN predictions.user_id              IS '원본 OkCupid CSV 의 행 번호 (사용자 고유 식별자, 실제 계정 아님)';
COMMENT ON COLUMN predictions.split                IS 'train은 모델이 정답을 본 데이터. 성능 계산은 반드시 test로만';
COMMENT ON COLUMN predictions.churn_actual         IS '실제 이탈 여부(정답). 1=이탈(마지막 접속 후 30일 이상 미접속), 0=유지';
COMMENT ON COLUMN predictions.churn_prob           IS '0~1. 1에 가까울수록 이탈 위험 높음. auto_class_weights=Balanced 로 학습해서 절대값은 실제 이탈률보다 부풀려져 있음 (순위는 정확)';
COMMENT ON COLUMN predictions.rank_pct             IS '전체 사용자 중 이탈 확률 기준 백분위. 값이 작을수록 위험도가 높은 쪽(상위)';
COMMENT ON COLUMN predictions.risk_tier            IS 'churn_prob 을 3단계로 나눈 등급. High >= 0.60, Medium 0.40~0.60, Low < 0.40';
COMMENT ON COLUMN predictions.essay_count          IS '자기소개 10칸 중 실제로 글을 쓴 칸 수 (빈 글자·점 하나 등은 미작성으로 처리)';
COMMENT ON COLUMN predictions.essay_total_words    IS '작성한 자기소개 전체의 총 단어 수';
COMMENT ON COLUMN predictions.essay_avg_len        IS '실제로 쓴 칸끼리만 비교한 칸당 평균 글자 수';
COMMENT ON COLUMN predictions.essay_len_std        IS '칸별 글자 수의 표준편차 (칸이 2개 미만이면 NULL). 값이 크면 칸마다 분량이 들쭉날쭉하다는 뜻';
COMMENT ON COLUMN predictions.profile_completeness IS '프로필 17개 항목 중 응답한 비율(0~1). 화면(SERVICE)에서는 그중 10개만 입력받을 수 있어 최대 약 0.59에 그침';
COMMENT ON COLUMN predictions.status               IS '관계 상태 원본값: single / available / seeing someone / married / unknown';
COMMENT ON COLUMN predictions.income               IS 'NULL이면 소득 미공개 (원본의 -1)';
COMMENT ON COLUMN predictions.age                  IS '나이 (18~90 범위 밖은 결측 처리됨)';
COMMENT ON COLUMN predictions.height               IS '키 (인치 단위, 원본 데이터 기준)';
COMMENT ON COLUMN predictions.job                  IS '직업 카테고리 (원본 데이터의 21개 값 중 하나, 미응답은 not_disclosed)';
COMMENT ON COLUMN predictions.edu_level            IS '학력 단계 (high school / two-year college / college/university / masters program / ph.d program 등)';
COMMENT ON COLUMN predictions.edu_status           IS '교육 상태: graduated from / working on / dropped out of';
COMMENT ON COLUMN predictions.religion_type        IS '종교 카테고리, 미응답은 not_disclosed';
COMMENT ON COLUMN predictions.diet_type            IS '식단 종류: anything / vegetarian / vegan / kosher / halal / other, 미응답은 not_disclosed';
COMMENT ON COLUMN predictions.diet_strict          IS '식단 엄격도: mostly / strictly / plain(신경 안 씀), 미응답은 not_disclosed';
COMMENT ON COLUMN predictions.drugs_level          IS '약물 사용 등급 숫자: 0=사용 안 함, 1=가끔, 2=자주. 미응답은 NULL';
COMMENT ON COLUMN predictions.smokes_level         IS '흡연 등급 숫자: 0=안 피움 ~ 4=자주. 미응답은 NULL';
COMMENT ON COLUMN predictions.has_kids             IS '자녀 유무: yes / no, 미응답은 not_disclosed';
COMMENT ON COLUMN predictions.has_kids_na          IS 'has_kids 가 무응답이면 1, 응답했으면 0 (무응답 자체를 신호로 쓰기 위한 플래그)';
COMMENT ON COLUMN predictions.wants_kids           IS '자녀 희망 여부: yes / no / maybe, 미응답은 not_disclosed';
COMMENT ON COLUMN predictions.sex                  IS '성별(m/f). 모델 학습에는 안 쓰고 화면 표시용으로만 저장';
COMMENT ON COLUMN predictions.location             IS '거주 지역 원본 텍스트 (예: "san francisco, california"). 99.8%가 캘리포니아라 지역별 분석에는 안 씀';
COMMENT ON COLUMN predictions.reason_1             IS '이 사용자 예측에 가장 크게 기여한 항목 (CatBoost SHAP 1위). "이름 (위험↑)" 또는 "이름 (안정↓)" 형식';
COMMENT ON COLUMN predictions.reason_2             IS 'SHAP 기여도 2위 항목';
COMMENT ON COLUMN predictions.reason_3             IS 'SHAP 기여도 3위 항목';

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

COMMENT ON TABLE  lift_summary            IS '위험도 상위 구간별로 실제 이탈률이 얼마나 높은지 미리 계산해 둔 발표용 요약표';
COMMENT ON COLUMN lift_summary.bucket     IS '위험도 구간 이름 (예: "상위 10%", "상위 20%")';
COMMENT ON COLUMN lift_summary.n          IS '해당 구간에 속한 사용자 수';
COMMENT ON COLUMN lift_summary.churn_rate IS '해당 구간의 실제 이탈률 (0~1)';
COMMENT ON COLUMN lift_summary.lift       IS '전체 평균 이탈률 대비 이 구간이 몇 배 더 위험한지 (Lift 값)';


-- ── 3. 메타 정보 (재현성 기록) ────────────────────────────────
CREATE TABLE meta (
    built_at    TIMESTAMP,
    model_file  TEXT,
    churn_days  INTEGER,
    n_rows      INTEGER,
    n_features  INTEGER
);

COMMENT ON TABLE  meta            IS '이 DB 를 어떤 모델·설정으로 만들었는지 기록 (재현성용, 1행)';
COMMENT ON COLUMN meta.built_at   IS 'predictions 를 계산한 시각';
COMMENT ON COLUMN meta.model_file IS '예측에 사용한 .cbm 모델 파일 이름';
COMMENT ON COLUMN meta.churn_days IS '이탈 기준 일수 (30일 이상 미접속 = 이탈)';
COMMENT ON COLUMN meta.n_rows     IS '전체 사용자 수 (59,946명)';
COMMENT ON COLUMN meta.n_features IS '모델이 학습한 feature 개수 (20개)';


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
    -- ⚠️ 여기 5단계 절대 기준(0.50/0.65/0.80/0.95)은 이 뷰의 가설 검증(H1-4, H3) 전용이에요.
    --    Streamlit RETENTION 화면의 "완성도 필터"는 이거랑 다르게, 전체를 NTILE(3)으로
    --    하위/중간/상위 33%씩 상대적으로 나눠요(db.py 참고). 두 기준이 서로 다른 목적으로
    --    일부러 다르게 설계된 거라, 발표에서 "완성도 구간"을 언급할 땐 어느 쪽 기준인지
    --    구분해서 말해야 숫자가 안 맞아 보이는 걸 피할 수 있어요.
    CASE
        WHEN profile_completeness < 0.50 THEN '1_매우낮음'
        WHEN profile_completeness < 0.65 THEN '2_낮음'
        WHEN profile_completeness < 0.80 THEN '3_보통'
        WHEN profile_completeness < 0.95 THEN '4_높음'
        ELSE                                   '5_매우높음'
    END AS completeness_band
FROM predictions p;

COMMENT ON VIEW   v_user                      IS '가설 검증용 파생 컬럼(actively_looking, income_disclosed 등)을 붙인 뷰';
COMMENT ON COLUMN v_user.actively_looking     IS 'H2 가설용: status 가 single/available 이면 1(적극적), 그 외(연애중·기혼·미기재)는 0';
COMMENT ON COLUMN v_user.income_disclosed     IS 'H3 가설용: income 이 NULL 이 아니면(공개했으면) 1, 미공개면 0';
COMMENT ON COLUMN v_user.essay_empty          IS 'H1-1 가설용: essay_count = 0 이면 1(자기소개 미작성)';
COMMENT ON COLUMN v_user.completeness_band    IS 'H1-4·H3 가설용 프로필 완성도 5단계(절대 기준). RETENTION 화면의 3등분(상대 기준)과는 다른 별도 정의 — 위 CASE 문 주석 참고';