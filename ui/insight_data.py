"""INSIGHT 페이지용 데이터 계산 (insight_data.py)

[이 파일이 하는 일]
프로젝트 폴더의 data 폴더에서 OkCupid 데이터 파일을 찾아 읽고,
"연령대별 / 관계 상태별 / 자기소개 작성량별 ... 이탈률"을 계산해 줍니다.
(화면에 그리는 일은 page_insight.py 가 해요. 이 파일은 '계산'만 담당합니다.)

[어떤 파일을 찾나요? — 아래 순서대로 data 폴더에서 찾아요]
1) okcupid_cleaned.csv.gz  (전처리 노트북이 저장하는 정리된 파일)
2) okcupid_profiles.csv    (Kaggle 원본 파일)
파일이 없어도 앱은 멈추지 않아요. INSIGHT 는 project_facts.py 에 적힌 요약 수치만 보여줍니다.

[이탈률이란?]
어떤 그룹의 사용자 중 '이탈(30일 이상 미접속)'한 사람의 비율입니다.
예) 20대 사용자 1,000명 중 250명이 이탈 -> 20대 이탈률 25%
"""
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 파일 이름 / 컬럼 이름
# ---------------------------------------------------------
CLEANED_NAMES = ["okcupid_cleaned.csv.gz", "okcupid_cleaned.csv"]
RAW_NAMES = ["okcupid_profiles.csv", "okcupid_profiles.csv.gz"]

ESSAY_COLS = [f"essay{i}" for i in range(10)]        # 자기소개 10칸

# 값 -> 화면에 보여줄 한글 이름
STATUS_LABELS = {"single": "싱글", "available": "만남 가능", "seeing someone": "만나는 사람 있음",
                 "married": "기혼", "unknown": "미응답"}
DRINK_LABELS = {0: "안 마심", 1: "거의 안 마심", 2: "사회적으로", 3: "자주", 4: "매우 자주"}
SMOKE_LABELS = {0: "안 피움", 1: "금연 중", 2: "술 마실 때만", 3: "가끔", 4: "자주"}
DRUG_LABELS = {0: "안 함", 1: "가끔", 2: "자주"}
DIET_LABELS = {"anything": "제한 없음", "vegetarian": "채식", "vegan": "비건",
               "other": "기타", "kosher": "코셔", "halal": "할랄"}

# 원본 파일의 글자 값 -> 등급 숫자 (전처리 노트북과 같은 규칙)
RAW_DRINKS = {"not at all": 0, "rarely": 1, "socially": 2, "often": 3, "very often": 4, "desperately": 4}
RAW_SMOKES = {"no": 0, "trying to quit": 1, "when drinking": 2, "sometimes": 3, "yes": 4}
RAW_DRUGS = {"never": 0, "sometimes": 1, "often": 2}

# 라이프스타일 항목 선택지: 화면 이름 -> (표준 컬럼 이름, 보여줄 순서)
LIFESTYLE_OPTIONS = {
    "음주": ("drinks", list(DRINK_LABELS.values())),
    "흡연": ("smokes", list(SMOKE_LABELS.values())),
    "약물": ("drugs", list(DRUG_LABELS.values())),
    "식단": ("diet", list(DIET_LABELS.values())),
}
AGE_LABELS = ["18~24세", "25~29세", "30~34세", "35~44세", "45세 이상"]
NO_ANSWER = "미응답"      # 빈칸(NaN)도 하나의 그룹으로 보여줍니다 (미응답 자체가 신호라서)


# ---------------------------------------------------------
# 1) 데이터 파일 찾기
# ---------------------------------------------------------
def _data_dirs():
    """data 폴더가 있을 만한 위치들. (이 파일의 상위 폴더 / 현재 위치 / ui 폴더 안)"""
    here = Path(__file__).resolve().parent          # ui 폴더
    return [here.parent / "data", Path.cwd() / "data", here / "data"]


def _find(names):
    for folder in _data_dirs():
        for name in names:
            path = folder / name
            if path.exists():
                return path
    return None


# ---------------------------------------------------------
# 2) 두 종류의 파일을 '같은 모양'으로 맞추기
#    나중에 계산할 때 파일 종류를 신경 쓰지 않도록,
#    아래 컬럼을 가진 표(DataFrame)로 통일합니다.
#      churn(0/1), age, status, essay_count, drinks, smokes, drugs, diet
# ---------------------------------------------------------
def _has_text(series):
    """자기소개 칸에 '진짜 글'이 있는지 (빈칸이나 '.' 같은 것은 안 쓴 것으로 봄)"""
    text = series.astype("string").str.strip().str.lower()
    return series.notna() & ~text.isin(["", ".", "-", "?", "_", "/", "na", "n/a"])


def _count_essays(df):
    cols = [c for c in ESSAY_COLS if c in df.columns]
    if cols:
        return sum(_has_text(df[c]).astype(int) for c in cols)
    if "essay_count" in df.columns:
        return pd.to_numeric(df["essay_count"], errors="coerce")
    return pd.Series(float("nan"), index=df.index)


def _to_labels(series, mapping):
    """등급 숫자(0,1,2..)나 글자 값을 한글 이름으로 바꾼다. 없는 값은 빈칸(NaN)."""
    if series is None:
        return None
    if series.dtype == object or str(series.dtype) in ("string", "str"):
        return series.map(mapping)
    return pd.to_numeric(series, errors="coerce").round().map(mapping)


def _from_cleaned(path):
    """전처리가 끝난 파일(okcupid_cleaned)을 표준 모양으로"""
    wanted = {"churn", "churn_suspect", "age", "status", "drinks_level", "smokes_level",
              "drugs_level", "diet_type", "essay_count", *ESSAY_COLS}
    df = pd.read_csv(path, usecols=lambda c: c in wanted)
    target = next((c for c in ("churn", "churn_suspect") if c in df.columns), None)
    if target is None or "age" not in df.columns:
        return None

    out = pd.DataFrame({"churn": pd.to_numeric(df[target], errors="coerce").astype(float),
                        "age": pd.to_numeric(df["age"], errors="coerce")})
    out["status"] = df["status"].map(STATUS_LABELS) if "status" in df.columns else None
    out["essay_count"] = _count_essays(df)

    out["drinks"] = _to_labels(df.get("drinks_level"), DRINK_LABELS)
    out["smokes"] = _to_labels(df.get("smokes_level"), SMOKE_LABELS)
    out["drugs"] = _to_labels(df.get("drugs_level"), DRUG_LABELS)
    out["diet"] = _to_labels(df.get("diet_type"), DIET_LABELS)
    return out


def _from_raw(path):
    """Kaggle 원본 파일(okcupid_profiles)을 표준 모양으로. 이탈(churn)도 여기서 직접 만든다."""
    wanted = {"age", "status", "last_online", "drinks", "smokes", "drugs", "diet", *ESSAY_COLS}
    df = pd.read_csv(path, usecols=lambda c: c in wanted)
    if "last_online" not in df.columns or "age" not in df.columns:
        return None

    # 가장 최근 접속 시각을 '수집 시점'으로 보고, 30일 이상 지났으면 이탈(1)
    last = pd.to_datetime(df["last_online"], format="%Y-%m-%d-%H-%M", errors="coerce")
    days_inactive = (last.max() - last).dt.days
    churn = (days_inactive >= 30).astype(float).where(last.notna())

    age = pd.to_numeric(df["age"], errors="coerce")
    out = pd.DataFrame({"churn": churn, "age": age.where(age.between(18, 90))})   # 18~90세 밖은 오류값
    out["status"] = df["status"].map(STATUS_LABELS) if "status" in df.columns else None
    out["essay_count"] = _count_essays(df)

    out["drinks"] = _to_labels(df.get("drinks"), {k: DRINK_LABELS[v] for k, v in RAW_DRINKS.items()})
    out["smokes"] = _to_labels(df.get("smokes"), {k: SMOKE_LABELS[v] for k, v in RAW_SMOKES.items()})
    out["drugs"] = _to_labels(df.get("drugs"), {k: DRUG_LABELS[v] for k, v in RAW_DRUGS.items()})
    # diet 는 'mostly vegetarian' 처럼 앞에 수식어가 붙어 있어서 떼어 냄
    if "diet" in df.columns:
        diet_type = df["diet"].astype("string").str.replace(r"^(mostly|strictly)\s+", "", regex=True)
        out["diet"] = diet_type.map(DIET_LABELS)
    else:
        out["diet"] = None
    return out


@st.cache_data(show_spinner="데이터를 불러오는 중...")
def load_dataset():
    """data 폴더의 파일을 읽어 표준 모양의 표(DataFrame)를 돌려준다. 못 찾으면 None.

    @st.cache_data : 한 번 읽은 결과를 기억해 둡니다. (파일이 커서 매번 읽으면 느려요)
    """
    for finder, reader in ((CLEANED_NAMES, _from_cleaned), (RAW_NAMES, _from_raw)):
        path = _find(finder)
        if path is None:
            continue
        try:
            df = reader(path)
        except Exception:        # 파일 모양이 예상과 달라도 앱이 멈추지 않게, 다음 후보로 넘어감
            continue
        if df is not None and df["churn"].notna().sum() > 0:
            return df.dropna(subset=["churn"]).reset_index(drop=True)
    return None


# ---------------------------------------------------------
# 3) 그룹별 이탈률 계산
#    결과 모양: [{"label": "20~29세", "rate": 27.3, "n": 12345}, ...]
# ---------------------------------------------------------
def _rate_rows(groups, churn, order=None):
    """groups(그룹 이름)별로 churn(0/1)의 평균 = 이탈률(%)과 사람 수를 계산"""
    table = pd.DataFrame({"g": groups, "churn": churn}).dropna(subset=["g"])
    stats = table.groupby("g", observed=True)["churn"].agg(["mean", "size"])
    rows = [{"label": str(name), "rate": float(row["mean"] * 100), "n": int(row["size"])}
            for name, row in stats.iterrows() if row["size"] > 0]
    if order:
        rows = sorted((r for r in rows if r["label"] in order), key=lambda r: order.index(r["label"]))
    return rows or None


def overall_rate(df):
    return float(df["churn"].mean() * 100)


def by_essay_count(df):
    """자기소개를 몇 칸 채웠는지에 따른 이탈률"""
    groups = pd.cut(df["essay_count"], bins=[-1, 0, 3, 6, 10],
                    labels=["0개", "1~3개", "4~6개", "7~10개"])
    return _rate_rows(groups, df["churn"])


def by_age(df):
    groups = pd.cut(df["age"], bins=[17, 24, 29, 34, 44, 120], labels=AGE_LABELS)
    return _rate_rows(groups, df["churn"])


def by_status(df):
    if df["status"].notna().sum() == 0:
        return None
    order = list(STATUS_LABELS.values())
    return _rate_rows(df["status"], df["churn"], order)


def by_lifestyle(df, option):
    """라이프스타일(음주/흡연/약물/식단) 항목별 이탈률. 빈칸은 '미응답' 그룹으로 따로 보여준다."""
    column, order = LIFESTYLE_OPTIONS[option]
    series = df[column]
    if series is None or series.notna().sum() == 0:
        return None
    groups = series.fillna(NO_ANSWER)
    return _rate_rows(groups, df["churn"], order + [NO_ANSWER])
