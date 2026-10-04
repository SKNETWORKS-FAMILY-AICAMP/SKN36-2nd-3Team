-- ════════════════════════════════════════════════════════════
-- 데이터 적재 — 미리 계산해 둔 예측 결과를 넣는다
--
-- 모델을 돌릴 필요가 없다. 59,946명의 이탈 확률·등급·근거가
-- 이미 predictions.csv 에 계산돼 있고, 여기서 통째로 읽어 들인다.
--
-- 컨테이너가 처음 만들어질 때 01~04 다음으로 자동 실행된다.
-- ════════════════════════════════════════════════════════════

COPY predictions (
    user_id, split, churn_actual, churn_prob, rank_pct, risk_tier,
    essay_count, essay_total_words, essay_avg_len, essay_len_std,
    profile_completeness, status, income, age, height, job,
    edu_level, edu_status, religion_type, diet_type, diet_strict,
    drugs_level, smokes_level, has_kids, has_kids_na, wants_kids,
    sex, location, reason_1, reason_2, reason_3
)
FROM '/docker-entrypoint-initdb.d/predictions.csv'
WITH (FORMAT csv, HEADER true);

COPY lift_summary (bucket, n, churn_rate, lift)
FROM '/docker-entrypoint-initdb.d/lift_summary.csv'
WITH (FORMAT csv, HEADER true);

COPY meta (built_at, model_file, churn_days, n_rows, n_features)
FROM '/docker-entrypoint-initdb.d/meta.csv'
WITH (FORMAT csv, HEADER true);

-- 통계 갱신 — 쿼리 속도가 빨라진다
ANALYZE predictions;

-- 적재 확인 (컨테이너 로그에 찍힌다)
DO $$
DECLARE n INTEGER;
BEGIN
    SELECT COUNT(*) INTO n FROM predictions;
    RAISE NOTICE '적재 완료: predictions %행', n;
END $$;
