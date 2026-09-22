-- ⚠️ 이 파일은 public 스키마를 명시합니다.
-- DBeaver 편집기가 다른 스키마를 보고 있어도 그대로 실행됩니다.
SET search_path TO public;

-- ════════════════════════════════════════════════════════════
-- 실시간 진단 확인용 — DBeaver에서 Ctrl + Enter
-- 테이블·뷰 정의는 sql/init/04_schema_live.sql 에 있다.
-- ════════════════════════════════════════════════════════════


-- ① 진단이 쌓이고 있나
SELECT COUNT(*) AS 총진단수,
       MIN(created_at) AS 처음,
       MAX(created_at) AS 마지막
FROM public.predictions_live;


-- ② 최근 진단 20건  ← SERVICE 화면 하단
SELECT * FROM public.v_live_recent;


-- ③ 오늘 요약  ← 관리자 화면 상단 카드
SELECT * FROM public.v_live_today;


-- ④ 가장 흔한 위험 근거
SELECT * FROM public.v_live_reason;


-- ⑤ 학습 데이터와 분포가 비슷한가  ← 모델 재학습 판단용
-- 두 줄의 평균자기소개칸·평균완성도가 많이 벌어지면
-- 실제 사용자가 학습 데이터와 달라졌다는 뜻이다.
SELECT * FROM public.v_live_vs_train;


-- ⑥ 날짜별 추이
SELECT to_char(created_at, 'YYYY-MM-DD')                     AS 날짜,
       COUNT(*)                                              AS 진단수,
       COUNT(*) FILTER (WHERE risk_tier = 'High')            AS 고위험,
       ROUND(AVG(churn_prob)::numeric * 100, 1)              AS 평균위험도
FROM public.predictions_live
GROUP BY 1
ORDER BY 1 DESC;


-- ⑦ 어떤 모델로 뽑은 결과인가 (모델 교체 후 확인용)
SELECT model_file AS 모델파일,
       COUNT(*)   AS 건수,
       MAX(created_at) AS 마지막사용
FROM public.predictions_live
GROUP BY model_file
ORDER BY 마지막사용 DESC;


-- ⑧ 샘플 데이터 지우기 (실제 진단이 쌓이기 시작하면)
-- DELETE FROM public.predictions_live WHERE note = 'sample';
