-- ════════════════════════════════════════════════════════════
-- 확장 스키마 — A/B 테스트 · 품질 보상
--
-- ⚠️ 지금은 데이터가 없다. 제안서의 "향후 구조"를 보여주는 용도.
--    테이블 정의는 여기(Docker 자동 실행)에 두고,
--    실제 쿼리와 설계 문서는 ab_test/ 폴더에 있다.
-- ════════════════════════════════════════════════════════════
-- 확장 스키마 — 지금은 비어 있다. 제안서의 "향후 구조" 용도.
-- ════════════════════════════════════════════════════════════

-- ── A/B 테스트 ────────────────────────────────────────────────
CREATE TABLE ab_assignment (
    user_id     INTEGER,
    experiment  VARCHAR(50),               -- '온보딩_최소요건' | '젤리보상'
    arm         VARCHAR(10),               -- 'treatment' | 'control'
    assigned_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (user_id, experiment)
);

-- ── 개입 이력 (푸시·부스트 발송 기록) ─────────────────────────
CREATE TABLE campaigns (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER,
    action      VARCHAR(50),               -- '넛지푸시_3칸' | '부스트24h' | '젤리지급'
    sent_at     TIMESTAMP DEFAULT now(),
    note        TEXT
);
CREATE INDEX idx_camp_user ON campaigns (user_id, action);

-- ── 결과 측정 ─────────────────────────────────────────────────
CREATE TABLE outcomes (
    user_id        INTEGER,
    measured_at    TIMESTAMP,
    retained_30d   SMALLINT,               -- 1: 남음, 0: 떠남
    profile_edited SMALLINT,               -- 개입 후 프로필을 수정했는가
    PRIMARY KEY (user_id, measured_at)
);


-- ════════════════════════════════════════════════════════════
-- 프로필 품질 평가 — "길이보다 질" 보상 설계
-- ════════════════════════════════════════════════════════════

-- ── 다른 사용자가 남긴 프로필 칭찬 ────────────────────────────
-- '관심 있어요'(=좋아요)와 분리해서 기록한다.
CREATE TABLE profile_feedback (
    id           SERIAL PRIMARY KEY,
    to_user_id   INTEGER      NOT NULL,    -- 평가받은 사람
    from_user_id INTEGER      NOT NULL,    -- 평가한 사람
    badge        VARCHAR(20)  NOT NULL,    -- 'rich' | 'easy_talk' | 'values_clear'
    created_at   TIMESTAMP    DEFAULT now(),
    -- 같은 사람이 같은 배지를 중복으로 못 주게
    UNIQUE (to_user_id, from_user_id, badge)
);
CREATE INDEX idx_fb_to ON profile_feedback (to_user_id);

COMMENT ON COLUMN profile_feedback.badge IS
  'rich=프로필이 알차요 / easy_talk=대화를 시작하기 쉬워요 / values_clear=가치관이 잘 드러나요';


-- ── 프로필 노출 수 ────────────────────────────────────────────
-- 칭찬 수를 그냥 쓰면 "노출이 많은 사람"이 유리해진다. 분모로 쓴다.
CREATE TABLE profile_impressions (
    user_id     INTEGER PRIMARY KEY,
    impressions INTEGER NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP DEFAULT now()
);


-- ── 젤리 지급 원장 ────────────────────────────────────────────
CREATE TABLE jelly_ledger (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER     NOT NULL,
    amount     INTEGER     NOT NULL,       -- 지급 +, 사용 −
    reason     VARCHAR(50) NOT NULL,       -- '품질칭찬' | '프로필완성' | '사용'
    ref_id     INTEGER,                    -- profile_feedback.id 등
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_jelly_user ON jelly_ledger (user_id);


-- ── 프로필 품질 점수 뷰 ───────────────────────────────────────
-- ★ 핵심: 칭찬 수가 아니라 "칭찬 수 ÷ 노출 수"로 본다.
CREATE VIEW v_profile_quality AS
SELECT
    i.user_id,
    i.impressions                                               AS 노출수,
    COUNT(f.id)                                                 AS 칭찬수,
    COUNT(*) FILTER (WHERE f.badge = 'rich')                    AS 알차요,
    COUNT(*) FILTER (WHERE f.badge = 'easy_talk')               AS 대화쉬움,
    COUNT(*) FILTER (WHERE f.badge = 'values_clear')            AS 가치관,
    ROUND(COUNT(f.id)::numeric / NULLIF(i.impressions, 0), 4)   AS 칭찬률
FROM profile_impressions i
LEFT JOIN profile_feedback f ON f.to_user_id = i.user_id
GROUP BY i.user_id, i.impressions;

COMMENT ON VIEW v_profile_quality IS
  '프로필 품질 = 칭찬수 ÷ 노출수. 노출이 많아 칭찬이 쌓이는 효과를 보정한다';
