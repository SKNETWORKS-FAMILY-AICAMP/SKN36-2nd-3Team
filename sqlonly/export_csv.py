"""
export_csv.py — build_db.py가 만든 SQLite를 sql/init 의 CSV로 내보낸다.

모델이 바뀌었을 때만 쓰는 스크립트다.
평소에는 실행할 필요가 없다 (CSV가 이미 들어 있다).

사전:  python build_db.py      → data/okcupid.db 생성
실행:  python export_csv.py
이후:  docker compose down -v && docker compose up -d
"""

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

BASE   = Path(__file__).resolve().parent
DB     = BASE / "data" / "okcupid.db"
INIT   = BASE / "sql" / "init"
SCHEMA = INIT / "01_schema_core.sql"

if not DB.exists():
    sys.exit(f"[중단] {DB} 가 없습니다. 먼저 python build_db.py 를 실행하세요.")

# ── 스키마에서 컬럼 순서와 정수형 컬럼을 읽는다 ────────────────
# CSV 컬럼 순서를 손으로 맞추면 언젠가 반드시 어긋난다. 스키마를 진실로 삼는다.
block = re.search(r"CREATE TABLE predictions \((.*?)\n\);", SCHEMA.read_text(encoding="utf-8"), re.S).group(1)
pairs = re.findall(r"^\s{4}(\w+)\s+(\w+)", block, re.M)
cols  = [c for c, _ in pairs]
ints  = [c for c, t in pairs if t.upper() in ("INTEGER", "SMALLINT", "BIGINT")]

con = sqlite3.connect(DB)

pred = pd.read_sql("SELECT * FROM predictions", con)
missing = set(cols) - set(pred.columns)
if missing:
    sys.exit(f"[중단] 스키마에 있는 컬럼이 예측 결과에 없습니다: {missing}")

pred = pred[cols]
for c in ints:
    # 0.0 같은 실수 표기가 남으면 COPY가 정수 컬럼에서 거부한다
    pred[c] = pd.to_numeric(pred[c], errors="coerce").round().astype("Int64")
pred.to_csv(INIT / "predictions.csv", index=False, encoding="utf-8")

pd.read_sql("SELECT * FROM lift_summary", con).to_csv(INIT / "lift_summary.csv", index=False, encoding="utf-8")
pd.read_sql("SELECT * FROM meta", con).to_csv(INIT / "meta.csv", index=False, encoding="utf-8")

size = (INIT / "predictions.csv").stat().st_size / 1024 / 1024
print(f"완료: predictions.csv {len(pred):,}행 · {size:.1f}MB")
print("다음:  docker compose down -v  &&  docker compose up -d")
