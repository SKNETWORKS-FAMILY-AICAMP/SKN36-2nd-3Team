"""DB 연결 담당 (db.py)

[이 파일이 하는 일]
sqlonly 폴더의 PostgreSQL 컨테이너에 접속해서, SQL 쿼리 결과를 표(DataFrame)로 돌려줍니다.
INSIGHT · RETENTION 화면이 이 파일을 통해 "지금 이 순간 DB에 실제로 있는 값"을 가져다 써요.
(비유: predict.py 가 '예측 담당'이라면, 이 파일은 'DB 담당'입니다)

[먼저 해야 할 것]
1. sqlonly 폴더에서 DB 컨테이너를 켜 두세요:  docker compose up -d
   (sqlonly/README.md 참고 — predictions.csv 등이 자동으로 들어가요)
2. 이 프로젝트에 접속 정보를 알려주는 .env 파일이 필요해요. 프로젝트 맨 바깥에
   .env.example 을 복사해서 .env 로 이름 바꾸고, 필요하면 비밀번호를 수정하세요.
       cp .env.example .env
3. 패키지를 추가하세요:  uv add "psycopg[binary]" python-dotenv

[DB 가 꺼져 있거나 .env 가 없으면?]
앱이 멈추지 않아요. run_query() 가 None 을 돌려주고, 화면은 "DB 연결 안 됨" 안내 카드를 보여줘요.
(data 폴더 CSV, models 폴더 .cbm 이 없을 때와 똑같은 방식이에요)

[테이블 데이터가 0행이면?]
연결은 됐지만 결과가 비어 있는 경우예요 (예: ab_assignment, outcomes — 아직 실험을 안 돌려서 그래요).
이건 연결 실패와는 다르게 취급해야 해서, run_query() 는 '연결 실패(None)'와 '연결 성공 + 0행(빈 표)'을
구분해서 돌려줍니다. 화면 쪽에서 이 둘을 다른 안내 문구로 보여주면 돼요.

[비밀번호에 대해]
sqlonly/README.md 에 적힌 dayzero123 은 개발용 기본값이에요. .env 파일에 실제 값을 넣고,
그 .env 파일은 절대 깃에 커밋하지 마세요 (.gitignore 에 이미 들어 있어야 해요).
"""
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# 1) 접속 정보 읽기
# ---------------------------------------------------------
def _load_env():
    """.env 파일이 있으면 읽어서 os.environ 에 넣어준다. (python-dotenv 가 없어도 앱은 안 멈춤)"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve().parent
    for folder in (here.parent, here):     # 프로젝트 맨 바깥 -> ui 폴더 순서로 찾음
        env_path = folder / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return


_load_env()

# 환경변수에 없으면 sqlonly/README.md 의 개발용 기본값을 씁니다.
# (실제 서비스에서는 .env 로 진짜 값을 넣고, 이 기본값은 로컬 개발용으로만 쓰세요)
import os  # noqa: E402  (dotenv 로딩 뒤에 읽어야 해서 여기 위치)

DB_CONFIG = {
    "host": os.getenv("DAYZERO_DB_HOST", "localhost"),
    "port": os.getenv("DAYZERO_DB_PORT", "5432"),
    "dbname": os.getenv("DAYZERO_DB_NAME", "okcupid"),
    "user": os.getenv("DAYZERO_DB_USER", "dayzero"),
    "password": os.getenv("DAYZERO_DB_PASSWORD", "dayzero123"),
}


# ---------------------------------------------------------
# 2) 연결
# ---------------------------------------------------------
@st.cache_resource
def _get_engine():
    """DB 연결 엔진을 한 번만 만들어서 재사용한다. 연결에 실패하면 None.

    SQLAlchemy 의 '엔진'은 필요할 때 알아서 연결을 열고 닫아 주는 관리자예요. (직접 연결 하나만
    들고 있는 것보다 안전해서 pandas 가 공식적으로 이 방식을 권장해요)
    @st.cache_resource : Streamlit 이 이 함수의 결과를 기억해 뒀다가, 화면을 조작할 때마다
    새로 만들지 않고 같은 엔진을 계속 씁니다.
    """
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        return None
    url = (f"postgresql+psycopg://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
          f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:            # 진짜로 연결이 되는지 한 번 확인
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None


def is_connected() -> bool:
    """DB에 지금 연결할 수 있는지. 화면 맨 위에 상태를 보여줄 때 씁니다."""
    return _get_engine() is not None


# ---------------------------------------------------------
# 3) 쿼리 실행
# ---------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame | None:
    """SQL 쿼리를 실행해서 결과를 표(DataFrame)로 돌려준다.

    반환값 읽는 법 (이 셋을 구분해서 화면을 그려 주세요):
      - None          : DB에 연결하지 못했어요 (컨테이너가 꺼져 있거나, .env 가 없거나, 접속 정보가 틀림)
      - 빈 표(0행)     : 연결은 됐지만 조건에 맞는 데이터가 없어요 (예: 아직 실험을 안 돌림)
      - 값이 있는 표    : 정상적으로 결과가 나왔어요

    @st.cache_data(ttl=60) : 같은 쿼리를 60초 동안은 다시 DB에 묻지 않고 기억해 둔 결과를 씁니다.
    DB 부담을 줄여 주지만, 데이터가 막 바뀐 직후라면 최대 60초 정도 옛날 값이 보일 수 있어요.
    """
    conn = _get_engine()
    if conn is None:
        return None
    try:
        return pd.read_sql(sql, conn, params=params)
    except Exception:
        # 연결은 됐는데 쿼리 자체가 잘못된 경우도 (컨테이너를 최신으로 안 띄웠다든가) 화면이
        # 안 멈추게 None 으로 처리해요. 원인을 보고 싶으면 이 except 를 잠깐 지우고 실행해 보세요.
        return None


def run_view(view_name: str) -> pd.DataFrame | None:
    """뷰(view) 하나를 통째로 읽어 온다. run_query(f"SELECT * FROM {view_name}") 과 같아요.

    view_name 은 코드에 미리 정해 둔 이름만 쓰세요 (사용자 입력을 그대로 넣지 않기 위해).
    """
    return run_query(f"SELECT * FROM {view_name}")


# ---------------------------------------------------------
# 4) 쓰기 (SERVICE 예측 결과를 predictions_live 에 한 줄 남기기)
# ---------------------------------------------------------
# predictions_live 테이블의 컬럼 (DBeaver 에서 SELECT * FROM predictions_live 로 직접 확인함).
# id 와 created_at 은 DB 가 자동으로 채워 줘서 우리가 넣을 필요 없어요.
_LIVE_COLUMNS = ["churn_prob", "risk_tier", "age", "sex", "status", "job",
                "essay_count", "profile_completeness",
                "reason_1", "reason_2", "reason_3", "model_file", "note"]


def log_prediction(values: dict) -> bool:
    """SERVICE 에서 예측한 결과를 predictions_live 테이블에 한 줄 저장한다.

    values : 위 _LIVE_COLUMNS 중 아는 것만 넣으면 됩니다. (없는 키는 NULL 로 들어가요)
    반환   : 저장에 성공하면 True, 실패해도(연결 안 됨, 테이블 없음 등) 예외 없이 False.
             이 함수는 '기록에 실패했다고 SERVICE 화면 예측 자체를 막으면 안 된다'는
             원칙으로 만들었어요. 그래서 실패해도 화면은 평소처럼 결과를 보여줘요.

    run_query() 와 달리 @st.cache_data 를 안 붙였어요. 쓰기 작업은 캐시하면 안 되고
    (캐시된 '가짜 성공'을 돌려주게 돼요), 매번 새로 DB에 물어봐야 해요.
    """
    engine = _get_engine()
    if engine is None:
        return False
    from sqlalchemy import text
    payload = {c: values.get(c) for c in _LIVE_COLUMNS}
    col_sql = ", ".join(_LIVE_COLUMNS)
    val_sql = ", ".join(f":{c}" for c in _LIVE_COLUMNS)
    sql = f"INSERT INTO predictions_live ({col_sql}) VALUES ({val_sql})"
    try:
        with engine.begin() as conn:      # begin() : 성공하면 자동 저장(commit), 실패하면 자동 취소(rollback)
            conn.execute(text(sql), payload)
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# 5) RETENTION 'SQL 타겟팅' — 조건에 맞는 사용자 집단 조회
# ---------------------------------------------------------
# 세 쿼리(요약/신호 집계/명단)가 똑같은 조건을 써야 해서, 조건 부분(filtered)을 CTE 하나로
# 만들어 두고 세 쿼리가 나눠 씁니다. (:이름) 은 SQL 이 아니라 파이썬에서 채워 넣는 자리예요.
#
# ":risk_tier IS NULL OR risk_tier = :risk_tier" 처럼 써 둔 이유: 필터를 안 걸었을 때(None)는
# 앞쪽 조건이 참이 돼서 전체가 통과하고, 걸었을 때는 뒤쪽 조건으로 걸러져요. 이렇게 하면 SQL
# 글자 자체는 항상 똑같고, 채워 넣는 값만 바뀌어서 안전해요 (사용자가 고른 값을 SQL 문자열에
# 직접 끼워 넣지 않아요). CAST(... AS text) 는 '이 값의 종류'를 미리 알려 주는 표시예요. 값이
# 전부 None(NULL)일 수도 있어서, 이게 없으면 PostgreSQL 이 "이 값이 글자인지 숫자인지" 정하지
# 못해서 에러가 나요. (PostgreSQL 의 :: 축약 표기 대신 CAST() 를 쓴 이유: SQLAlchemy 의 text() 가
# ':이름::타입' 을 '이름 뒤에 콜론이 이스케이프된 것'으로 오해해서 값이 안 채워지는 문제가 있어요)
_SEGMENT_BASE = """
WITH base AS (
    SELECT user_id, age, status, risk_tier, churn_prob, essay_count,
           profile_completeness, reason_1,
           NTILE(3) OVER (ORDER BY profile_completeness) AS completeness_tier
    FROM predictions
),
filtered AS (
    SELECT * FROM base
    WHERE (CAST(:risk_tier AS text) IS NULL OR risk_tier = :risk_tier)
      AND (CAST(:age_min AS int) IS NULL OR age >= :age_min)
      AND (CAST(:age_max AS int) IS NULL OR age <= :age_max)
      AND (CAST(:essay_min AS int) IS NULL OR essay_count >= :essay_min)
      AND (CAST(:essay_max AS int) IS NULL OR essay_count <= :essay_max)
      AND (CAST(:status AS text) IS NULL OR status = :status)
      AND (CAST(:completeness_tier AS int) IS NULL OR completeness_tier = :completeness_tier)
)
"""

_SEGMENT_SUMMARY_SQL = _SEGMENT_BASE + """
SELECT COUNT(*) AS n,
       AVG(churn_prob) AS avg_prob,
       AVG((risk_tier = 'High')::int) AS high_share
FROM filtered
"""

_SEGMENT_REASONS_SQL = _SEGMENT_BASE + """
SELECT reason_1, COUNT(*) AS n
FROM filtered
WHERE reason_1 IS NOT NULL
GROUP BY reason_1
ORDER BY n DESC
LIMIT 5
"""

_SEGMENT_LIST_SQL = _SEGMENT_BASE + """
SELECT user_id, risk_tier, churn_prob, reason_1
FROM filtered
ORDER BY churn_prob DESC
LIMIT :limit
"""


@st.cache_data(ttl=60, show_spinner=False)
def query_segment(risk_tier=None, age_min=None, age_max=None, essay_min=None, essay_max=None,
                  status=None, completeness_tier=None, limit=20):
    """조건에 맞는 사용자 집단을 predictions 테이블에서 찾는다.

    각 인자는 필터 하나씩이에요. None 이면 '전체'(그 조건은 안 건다는 뜻)입니다.
        risk_tier         : 'High' / 'Medium' / 'Low'
        age_min, age_max  : 나이 범위 (둘 다 포함)
        essay_min/max     : 자기소개 작성 칸 수 범위
        status            : 관계 상태 (예: 'single')
        completeness_tier : 프로필 완성도 3등분 중 몇 번째인지 (1=하위, 2=중간, 3=상위)
        limit             : 명단에 몇 명까지 보여줄지

    반환 (연결 실패나 쿼리 오류 시 None):
        {"n": 인원 수,
         "avg_prob": 평균 이탈 확률(0~1) 또는 None(인원이 0명일 때),
         "high_share": High 등급 비율(0~1) 또는 None,
         "reasons": [(위험 신호, 사람 수), ...]  # 흔한 순
         "rows": [(user_id, risk_tier, churn_prob, reason_1), ...]}  # 이탈 확률 높은 순
    """
    engine = _get_engine()
    if engine is None:
        return None
    from sqlalchemy import text
    params = {"risk_tier": risk_tier, "age_min": age_min, "age_max": age_max,
             "essay_min": essay_min, "essay_max": essay_max, "status": status,
             "completeness_tier": completeness_tier}
    try:
        with engine.connect() as conn:
            summary = conn.execute(text(_SEGMENT_SUMMARY_SQL), params).mappings().one()
            reasons = conn.execute(text(_SEGMENT_REASONS_SQL), params).mappings().all()
            rows = conn.execute(text(_SEGMENT_LIST_SQL), {**params, "limit": limit}).mappings().all()
    except Exception:
        return None

    return {
        "n": int(summary["n"] or 0),
        "avg_prob": float(summary["avg_prob"]) if summary["avg_prob"] is not None else None,
        "high_share": float(summary["high_share"]) if summary["high_share"] is not None else None,
        "reasons": [(r["reason_1"], int(r["n"])) for r in reasons],
        "rows": [(r["user_id"], r["risk_tier"], float(r["churn_prob"]), r["reason_1"]) for r in rows],
    }


# ---------------------------------------------------------
# 6) INSIGHT 탭 4 — 전체 위험군 분포 · 그룹별 이탈률
# ---------------------------------------------------------
def get_risk_tier_distribution():
    """predictions 테이블(59,946명 전체) 위험 등급 분포.

    반환: risk_tier · n(인원) · share(비율, 0~100 %) 컬럼을 가진 표(DataFrame).
          DB 연결 실패면 None, 연결은 됐지만 데이터가 없으면 빈 표.
    share 는 0~100 사이 '퍼센트 숫자'예요. (0~1 사이 비율이 아니라 rate_bars_card 가
    바로 "24.7%" 로 찍을 수 있는 값으로 db.py 에서 미리 계산해 둡니다)
    """
    df = run_query("SELECT risk_tier, COUNT(*) AS n FROM predictions GROUP BY risk_tier")
    if df is None or df.empty:
        return df
    df["share"] = df["n"] / df["n"].sum() * 100
    return df


# 그룹별 이탈률 계산에 쓰는 구간·이름표. insight_data.py 가 data 폴더 CSV로 계산할 때 쓰는
# 것과 똑같이 맞춰서, DB로 계산해도 INSIGHT 화면의 다른 그래프와 기준이 어긋나지 않게 해요.
_AGE_BANDS = [(17, 24, "18~24세"), (24, 29, "25~29세"), (29, 34, "30~34세"),
             (34, 44, "35~44세"), (44, 120, "45세 이상")]
_ESSAY_BANDS = [(-1, 0, "0개"), (0, 3, "1~3개"), (3, 6, "4~6개"), (6, 10, "7~10개")]
_STATUS_LABELS_SQL = {"single": "싱글", "available": "만남 가능", "seeing someone": "만나는 사람 있음",
                      "married": "기혼", "unknown": "미응답"}
_SMOKE_LABELS_SQL = {0: "안 피움", 1: "금연 중", 2: "술 마실 때만", 3: "가끔", 4: "자주"}
_DRUG_LABELS_SQL = {0: "안 함", 1: "가끔", 2: "자주"}
_DIET_LABELS_SQL = {"anything": "제한 없음", "vegetarian": "채식", "vegan": "비건",
                    "other": "기타", "kosher": "코셔", "halal": "할랄"}


def _band_case_sql(column, bands):
    """숫자 구간(bands)을 SQL의 CASE WHEN 문자열로 바꾼다. 예) age 구간 -> "CASE WHEN age > 17 ..."
    이렇게 SQL 글자로 만들어서 GROUP BY 를 DB 안에서 하게 해요. (파이썬으로 6만 행을 안 가져와도 됨)
    column 과 bands 는 항상 이 파일 안의 고정된 값만 들어와서(사용자 입력 아님) 안전해요."""
    whens = " ".join(f"WHEN {column} > {lo} AND {column} <= {hi} THEN '{label}'" for lo, hi, label in bands)
    return f"CASE {whens} END"


def _map_case_sql(column, label_map):
    """글자/숫자 값(label_map)을 SQL의 CASE WHEN 문자열로 바꾼다. 예) status 값 -> 한글 이름."""
    whens = " ".join(
        f"WHEN {column} = {raw if isinstance(raw, (int, float)) else repr(raw)} THEN '{label}'"
        for raw, label in label_map.items()
    )
    return f"CASE {whens} END"


@st.cache_data(ttl=60, show_spinner=False)
def get_group_churn_rates(dimension: str):
    """predictions 테이블에서 dimension(구분 기준)별 실제 이탈률을 SQL 의 GROUP BY 로 계산한다.

    dimension : "age" / "status" / "essay" / "흡연" / "약물" / "식단"
    반환      : [{"label": 그룹 이름, "rate": 이탈률(0~100), "n": 인원}, ...]
                insight_data.AGE_LABELS 등과 같은 순서로 정렬됨.
                DB 연결 안 되거나 dimension 을 모르면 None. (빈 리스트가 아니라 None 이라서
                page_insight.py 의 'not any([...])' 검사와 합쳐서 '준비 중' 카드로 이어져요)

    구간 나누기·평균 계산을 SQL 안에서 끝내고 결과 몇 줄만 받아와요. (예전 버전은 6만 행을
    통째로 가져와 파이썬에서 나눴는데, 이 계산은 DB 가 훨씬 잘하는 일이라 SQL 쪽으로 옮겼어요)
    """
    plan = {
        "age": ("age", _AGE_BANDS, None, [b[2] for b in _AGE_BANDS]),
        "essay": ("essay_count", _ESSAY_BANDS, None, [b[2] for b in _ESSAY_BANDS]),
        "status": ("status", None, _STATUS_LABELS_SQL, list(_STATUS_LABELS_SQL.values())),
        "흡연": ("smokes_level", None, _SMOKE_LABELS_SQL, list(_SMOKE_LABELS_SQL.values())),
        "약물": ("drugs_level", None, _DRUG_LABELS_SQL, list(_DRUG_LABELS_SQL.values())),
        "식단": ("diet_type", None, _DIET_LABELS_SQL, list(_DIET_LABELS_SQL.values())),
    }
    if dimension not in plan:
        return None
    column, bands, label_map, order = plan[dimension]
    case_expr = _band_case_sql(column, bands) if bands else _map_case_sql(column, label_map)

    df = run_query(f"""
        SELECT {case_expr} AS g, COUNT(*) AS n, AVG(churn_actual) AS rate
        FROM predictions
        WHERE {column} IS NOT NULL
        GROUP BY g
    """)
    if df is None:
        return None

    rows = [{"label": row["g"], "rate": float(row["rate"]) * 100, "n": int(row["n"])}
            for _, row in df.iterrows() if row["g"] is not None]
    rows = sorted((r for r in rows if r["label"] in order), key=lambda r: order.index(r["label"]))
    return rows or None
