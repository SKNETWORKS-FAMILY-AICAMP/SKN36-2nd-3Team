# Day Zero — SQL 전용 패키지

## 파이썬도, 모델도 필요 없습니다

59,946명의 **이탈 확률·등급·근거가 이미 계산돼 있습니다.**
`predictions.csv` 안에 들어 있고, 컨테이너가 만들어질 때 자동으로 적재됩니다.

| | 필요 |
| --- | :---: |
| Docker Desktop | ✅ |
| DBeaver | ✅ |
| Python · catboost | ❌ |
| `common/` 모듈 | ❌ |
| 모델 파일 `.cbm` | ❌ |
| 원본 CSV (131MB) | ❌ |

---

## 실행 — 명령어 한 줄

```bash
docker compose up -d
```

끝입니다. 1~2분 기다리면 테이블·뷰·데이터가 전부 들어가 있습니다.

### 확인

```bash
docker compose logs db | findstr 적재
```

```
NOTICE:  적재 완료: predictions 59946행
```

이 줄이 보이면 성공입니다.

---

## DBeaver 연결

새 데이터베이스 연결 → PostgreSQL

| 항목 | 값 |
| --- | --- |
| Host | `localhost` |
| Port | `5432` |
| Database | `okcupid` |
| Username | `dayzero` |
| Password | `dayzero123` |

드라이버를 내려받겠냐고 물으면 **Download** → **Test Connection** → **Finish**

### 첫 쿼리

```sql
SELECT split, COUNT(*) AS 인원,
       ROUND(AVG(churn_actual)::numeric * 100, 2) AS 이탈률
FROM predictions
GROUP BY split;
```

| split | 인원 | 이탈률 |
| --- | ---: | ---: |
| train | 44,959 | 25.72 |
| test | 14,987 | 25.72 |

이렇게 나오면 전부 제대로 들어온 것입니다.

---

## 폴더 구조

```
├─ docker-compose.yml
├─ sql/
│   ├─ init/                      ← 컨테이너 첫 생성 시 자동 실행
│   │   ├─ 01_schema_core.sql       predictions · lift_summary · meta
│   │   ├─ 02_schema_ab.sql         A/B 확장 테이블 6개 (비어 있음)
│   │   ├─ 03_views.sql             화면용 뷰 9개
│   │   ├─ 04_schema_live.sql       predictions_live + 실시간 뷰 4개
│   │   ├─ 05_load_data.sql         ★ CSV 적재
│   │   ├─ predictions.csv          ★ 59,946행 (21MB)
│   │   ├─ lift_summary.csv
│   │   └─ meta.csv
│   └─ query/                     ← DBeaver에서 손으로 실행
│       ├─ 01_check.sql             기본 확인 11개
│       ├─ 02_hypothesis.sql        가설 H1-1 ~ H3 검증
│       ├─ 03_campaign.sql          푸시·부스트 대상 추출
│       └─ 04_live.sql              실시간 진단 확인
└─ ab_test/                       ← 아직 안 돌아가는 설계 (0행)
```

`.csv` 는 PostgreSQL이 자동 실행하지 않습니다. `.sql` 만 실행하고,
`05_load_data.sql` 이 옆에 있는 csv를 읽어 들이는 구조입니다.

---

## 다시 하고 싶을 때

```bash
docker compose down -v     # -v 가 있어야 데이터까지 지워짐
docker compose up -d
```

몇 번을 다시 해도 됩니다. 원본을 건드리지 않습니다.

### 뷰만 고칠 때는 컨테이너를 다시 만들 필요가 없습니다

`03_views.sql` · `04_schema_live.sql` 은 맨 위에 `DROP VIEW IF EXISTS` 가 있습니다.
DBeaver에서 파일을 열고 **Alt + X**(전체 실행)로 다시 돌리면 갱신됩니다.

---

## 화면용 뷰

| 뷰 | 화면 | 보여주는 것 |
| --- | --- | --- |
| `v_insight_risk` | INSIGHT | 등급별 인원·실제 이탈률 |
| `v_insight_completeness` | INSIGHT | 프로필 완성도 구간별 이탈률 |
| `v_insight_essay` | INSIGHT | 자기소개 칸수별 이탈률 |
| `v_insight_reason` | INSIGHT | 가장 흔한 위험 근거 |
| `v_insight_calibration` | INSIGHT | 예측과 실제가 얼마나 맞는가 |
| `v_insight_segment` | INSIGHT | 성별·연령대 교차 |
| `v_retention_action` | RETENTION | 무엇을 하면 되는가 (A~D) |
| `v_retention_list` | RETENTION | 개입 대상 명단 |
| `v_about_hypothesis` | ABOUT | 가설 검증 요약 |
| `v_live_recent` | SERVICE | 최근 진단 20건 |
| `v_live_today` | SERVICE | 오늘 진단 수·등급 분포 |
| `v_live_reason` | SERVICE | 실시간 근거 순위 |
| `v_live_vs_train` | — | 학습 데이터와 분포 비교 |

UI 담당자에게는 **뷰 이름과 `SELECT * FROM ...` 한 줄**만 주면 됩니다.
계산은 DB가 끝내 뒀습니다.

---

## 이 숫자는 어디서 왔나

```
데이터        Kaggle OkCupid Profiles 59,946명
이탈 정의     2012-07-01 기준 30일 이상 미접속 → 25.72%
모델          CatBoost (depth 5 · lr 0.06 · iterations 300 · Balanced)
분할          train 44,959 / test 14,987 (stratify, seed 42)
성능          ROC-AUC 0.740
근거          CatBoost 내장 SHAP 상위 3개
등급          High ≥ 0.60 · Medium 0.40~0.60 · Low < 0.40
```

팀의 학습 파이프라인(`common/feature_extraction.py`)을 그대로 써서 계산했습니다.

### 화면에 숫자를 쓸 때 주의

확률의 **절대값은 실제보다 높게 나옵니다** (`auto_class_weights="Balanced"` 때문).
예측 77.9% 구간의 실제 이탈률은 55.9%입니다. **순위는 맞습니다.**

`v_insight_calibration` 을 실행하면 이 차이가 그대로 보입니다.
발표에서 먼저 짚고 넘어가면 오히려 점수가 되는 부분입니다.

---

## predictions_live 는 비어 있나?

샘플 3건이 들어 있습니다. SERVICE 화면을 먼저 그려 볼 수 있게 넣어 둔 것입니다.

```sql
DELETE FROM predictions_live WHERE note = 'sample';
```

실제 진단이 쌓이기 시작하면 지우면 됩니다.

---

비밀번호 `dayzero123` 은 개발용입니다. 실서비스라면 환경변수로 빼야 합니다.
