import html
import pandas as pd
import numpy as np

# Train 데이터 분석 후 선정한 최종 feature 20개
FEATURE_LIST = [
    "essay_count", "profile_completeness", "religion_type", "edu_level",
    "wants_kids", "has_kids", "diet_type", "drugs_level", "job",
    "height", "status", "income",
    "essay_total_words", "smokes_level", "diet_strict", "edu_status", "age",
    "has_kids_na", "essay_avg_len", "essay_len_std"
]

# 범주형 결측은 'not_disclosed' 범주로 구분; 수치형 NaN은 CatBoost에 그대로 전달
CAT_FEATURES = [
    "religion_type", "edu_level", "wants_kids", "has_kids", "diet_type",
    "job", "status", "diet_strict", "edu_status"
]

# profile_completeness 계산 항목 (17개, 팀원 노트북과 동일한 값)
# 결측 패턴이 같은 항목은 원본 컬럼 그대로 사용: drinks, drugs, ethnicity, religion, smokes, sign
PROFILE = [
    "body_type", "diet_type", "diet_strict", "drinks", "drugs", "edu_level",
    "edu_status", "ethnicity", "job", "has_kids", "wants_kids", "pets_dog",
    "pets_cat", "religion_type", "religion", "smokes", "sign"
]

ESSAY = [f"essay{i}" for i in range(10)]
MISSING_ESSAY = r"(?i)^\s*(?:[.\-?_/]*|na|n/a)\s*$"   # 빈 문자열, '.', '-', 'na' 등

DRUGS = {"never": 0, "sometimes": 1, "often": 2}
SMOKES = {"no": 0, "trying to quit": 1, "when drinking": 2, "sometimes": 3, "yes": 4}



def feature_extraction(df:pd.DataFrame) -> tuple:
    result = df.copy()

    # cleaning: HTML entity는 essay에만 있고, 빈 문자열도 essay0의 1건뿐
    result[ESSAY] = (
        result[ESSAY]
        .apply(lambda col: col.map(html.unescape, na_action="ignore"))
        .replace(MISSING_ESSAY, np.nan, regex=True)
    )

    # ---- 범주형 파생 (헬퍼 함수 대신 vectorized 문자열 연산) ----
    diet, kids = result["diet"], result["offspring"]
    result["diet_type"] = diet.str.replace(r"^(?:mostly|strictly) ", "", regex=True)
    result["diet_strict"] = (
        diet.str.extract(r"^(mostly|strictly)", expand=False)
            .fillna("plain").where(diet.notna())
    )
    result["has_kids"] = (
        kids.str.extract(r"^(has|doesn't have kids)", expand=False)
            .map({"has": "yes", "doesn't have kids": "no"})
    )
    result["wants_kids"] = (
        kids.str.extract(r"(might want|doesn't want|wants)", expand=False)
            .map({"might want": "maybe", "doesn't want": "no", "wants": "yes"})
    )
    result["edu_level"] = result["education"].str.extract(
        r"(high school|two-year college|college/university|masters program"
        r"|law school|med school|ph\.d program|space camp)", expand=False)
    result["edu_status"] = result["education"].str.extract(
        r"^(graduated from|working on|dropped out of)", expand=False)
    result["religion_type"] = result["religion"].str.extract(
        r"^(agnosticism|atheism|christianity|judaism|catholicism"
        r"|islam|hinduism|buddhism|other)", expand=False)
    result["pets_dog"] = result["pets"].where(result["pets"].str.contains("dogs"))
    result["pets_cat"] = result["pets"].where(result["pets"].str.contains("cats"))

    # ---- 수치형 파생 ----
    result["drugs_level"] = result["drugs"].map(DRUGS)
    result["smokes_level"] = result["smokes"].map(SMOKES)

    # ---- 결측을 채우기 전에 먼저 계산해야 하는 값 ----
    result["profile_completeness"] = result[PROFILE].notna().mean(axis=1)
    result["essay_count"] = result[ESSAY].notna().sum(axis=1)
    result["has_kids_na"] = kids.isna().astype("int8")
    # 응답은 했지만 자녀 유무가 불명확한 경우 (미응답과 구분)
    result["has_kids"] = result["has_kids"].fillna("unspecified").where(kids.notna())

    # ---- essay: HTML 태그와 공백을 제거한 길이 / 단어 수 ----
    clean = result[ESSAY].apply(
        lambda col: col.str.replace(r"(?:<[^>]+>|\s)+", " ", regex=True).str.strip()
    )
    result["essay_total_words"] = clean.apply(lambda col: col.str.count(r"\b\w+\b")).sum(axis=1)
    # 실제 응답한 essay끼리만 비교 (mean/std가 NaN을 자동으로 건너뜀)
    lengths = clean.apply(lambda col: col.str.len()).where(result[ESSAY].notna())
    result["essay_avg_len"] = lengths.mean(axis=1)
    result["essay_len_std"] = lengths.std(axis=1)

    # ---- 이상치 / 비공개 처리 ----
    result["age"] = result["age"].where(result["age"].between(18, 90))
    result["income"] = result["income"].replace(-1, np.nan)

    result[CAT_FEATURES] = result[CAT_FEATURES].fillna("not_disclosed").astype("category")

    return result[FEATURE_LIST]