# 팀 합치기

## 원칙 하나

> **DB는 공유하지 않습니다. 파일만 공유하고, DB는 각자 만듭니다.**

`docker compose up -d` 한 줄이면 누구 컴퓨터에서든 **똑같은 DB**가 만들어집니다.
그래서 "내 DB를 어떻게 넘기지?"를 고민할 필요가 없습니다.
GitHub에 올려야 할 것은 SQL 파일과 `predictions.csv` 뿐입니다.

---

## 폴더 주인 정하기 — 충돌의 90%가 여기서 납니다

같은 파일을 두 명이 고치면 merge conflict가 납니다. 미리 나눠 두면 안 납니다.

| 폴더 | 주인 | 나머지는 |
| --- | --- | --- |
| `notebooks/eda/` | EDA 담당 | 읽기만 |
| `notebooks/model/` · `models/` | 모델링 담당 | 읽기만 |
| `sql/` · `ab_test/` | **데이터(나)** | 읽기만 |
| `app/` · `frontend/` | UI 담당 | 읽기만 |
| `README.md` | 팀장 | 고칠 게 있으면 말하기 |
| `common/` | **아무도 안 건드림** | 고치면 전원이 깨집니다 |

`common/` 을 고쳐야 할 일이 생기면 **반드시 단톡방에 먼저 말하세요.**
`feature_extraction.py` 가 바뀌면 모델도, 예측값도, SQL도 전부 다시 만들어야 합니다.

---

## GitHub에 올릴 것 / 안 올릴 것

| | 파일 | 용량 |
| :---: | --- | --- |
| ✅ | `sql/` 전체 (`predictions.csv` 포함) | 21MB |
| ✅ | `ab_test/` · `docker-compose.yml` | 작음 |
| ✅ | 노트북 (`.ipynb`) | 작음 |
| ✅ | `common/` | 작음 |
| ❌ | `data/okcupid_profiles.csv` | **131MB — 올리면 push가 막힙니다** |
| ❌ | `models/*.cbm` | 각자 필요 없음 |
| ❌ | `data/*.db` | 자동 생성물 |

`.gitignore` 를 같이 넣어 뒀습니다. 그대로 최상단에 두면 됩니다.

> `predictions.csv` 21MB는 GitHub에서 문제없습니다. (경고 50MB / 차단 100MB)
> 이게 없으면 팀원이 `up -d` 해도 테이블이 비어 있으니 **반드시 올려야 합니다.**

---

## 팀원이 받아서 하는 것

```bash
git clone <저장소 주소>
cd <폴더>
docker compose up -d
```

1~2분 뒤 DBeaver로 접속하면 59,946행이 들어와 있습니다.
**파이썬도, 모델도, 원본 CSV도 필요 없습니다.**

---

## 누구에게 무엇을 주나

| 받는 사람 | 주는 것 | 한 줄 설명 |
| --- | --- | --- |
| **UI 담당** | 뷰 목록 + `sql/query/01_check.sql` | "`SELECT * FROM v_insight_risk` 한 줄이면 됩니다. 계산은 DB가 끝내 뒀어요." |
| **EDA 담당** | `sql/query/02_hypothesis.sql` | "가설 H1~H3을 SQL로 검증한 결과입니다. 발표 자료 숫자로 쓰세요." |
| **모델링 담당** | `05_load_data.sql` 의 존재 | "모델이 바뀌면 `predictions.csv` 만 갈아 끼우면 됩니다." |
| **팀장** | `ab_test/README.md` | "인과 검증은 A/B로 한다는 설계입니다. 질문 방어용." |

---

## 모델이 바뀌면 (모델링 담당이 최종본을 내면)

지금 들어 있는 `predictions.csv` 는 팀의 파이프라인(`common/feature_extraction.py`)과
같은 설정으로 계산한 것입니다. 최종 모델이 나오면 이렇게 갈아 끼웁니다.

```bash
python build_db.py            # 새 .cbm 으로 예측 다시 계산
python export_csv.py          # SQLite → predictions.csv
docker compose down -v
docker compose up -d
```

`sql/` 안의 SQL은 **한 줄도 안 고쳐도 됩니다.** CSV만 바뀝니다.

> 시간이 없으면 지금 CSV로 발표해도 됩니다.
> 성능(ROC-AUC 0.740)과 등급 분포가 노트북 결과와 일치하는 것을 확인했습니다.

---

## 합치는 날 순서

```
1. 각자 자기 폴더만 push          (충돌 없음)
2. 한 명이 pull 받아 전체 실행     docker compose down -v && up -d
3. 뷰 13개가 전부 도는지 확인      sql/query/01_check.sql
4. UI가 그 DB에 붙는지 확인
5. 숫자 맞춰 보기                 노트북 결과 == SQL 결과
```

**5번을 빼먹지 마세요.** 발표 자료의 숫자와 화면의 숫자가 다르면
그 자리에서 바로 질문이 들어옵니다.

---

## 자주 나는 문제

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `up -d` 했는데 테이블이 비어 있음 | `predictions.csv` 가 안 올라감 | `.gitignore` 확인 후 다시 push |
| `port is already allocated` | 5432를 다른 것이 쓰는 중 | `docker-compose.yml` 을 `"5433:5432"` 로 |
| SQL을 고쳤는데 반영이 안 됨 | 컨테이너가 이미 만들어짐 | `down -v` → `up -d` |
| 뷰만 고치고 싶음 | — | DBeaver에서 **Alt + X** (컨테이너 그대로) |
| `git push` 가 거부됨 | 131MB CSV를 올림 | `.gitignore` 넣고 커밋 다시 |
