"""예측 담당 (predict.py)

[이 파일이 하는 일]
화면(app.py)에서 사용자가 입력한 값을 받아서, 팀이 학습한 CatBoost 모델이 이해하는
20개 항목짜리 표(1행)로 바꾸고, 그 표로 "이탈 위험이 몇 %인지"를 계산해 돌려줍니다.

[왜 화면 파일과 따로 두나요?]
화면 코드와 모델 코드가 한 파일에 섞이면, 모델을 바꿀 때마다 화면 코드까지 뒤져야 해요.
따로 두면 이 파일만 고치면 되고, 화면 담당과 모델 담당이 서로 안 부딪힙니다.
(비유: app.py 는 '주문 받는 카운터', predict.py 는 '주방'입니다.)

[출처 — 반드시 common/feature_extraction.py 와 같아야 하는 부분]
아래 FEATURE_LIST · CAT_FEATURES · DRUGS · SMOKES 값은 team 의
common/feature_extraction.py (okcupid_model_final 노트북, 최종 확정판)에서 그대로 옮겨 왔어요.
그 파일이 바뀌면 여기도 같이 바꿔야 해요. (두 곳이 어긋나면 예측이 틀어집니다)

[모델 파일 연결 방법]
프로젝트 맨 바깥(ui 폴더와 같은 위치)에 models 폴더를 만들고, 팀이 저장한 .cbm 파일을
그 안에 넣으면 app.py 가 find_model_path() 로 자동으로 찾아서 씁니다. 파일이 없으면
SERVICE 화면은 예전처럼 분석 결과(EDA) 기반 참고 신호만 보여주고, 앱이 멈추지는 않아요.

[정확도에 대한 중요한 한계]
프로필 완성도(profile_completeness)는 원래 17개 항목으로 계산하는데, 지금 SERVICE 화면에는
그중 10개만 입력칸이 있어요(체형·음주·인종·반려견·반려묘·종교 진지함·별자리 없음).
그래서 화면에서 다 채워도 완성도가 10/17(약 0.59)을 넘지 못하고, 그만큼 모델이 실제보다
이탈 위험을 더 높게 볼 수 있어요. project_facts.PROFILE_COMPLETENESS_ITEMS 에 자세히 적어 뒀어요.
"""
import html
import re

import numpy as np
import pandas as pd

import project_facts as facts

# =========================================================
# 1) 팀의 최종 feature_extraction.py 와 반드시 같아야 하는 상수
# =========================================================
# 모델이 실제로 보는 20개 항목, 이 순서 그대로 표(DataFrame)를 만들어야 합니다.
FEATURE_LIST = [
    "essay_count", "profile_completeness", "religion_type", "edu_level",
    "wants_kids", "has_kids", "diet_type", "drugs_level", "job",
    "height", "status", "income",
    "essay_total_words", "smokes_level", "diet_strict", "edu_status", "age",
    "has_kids_na", "essay_avg_len", "essay_len_std",
]

# 이 9개는 '범주형'이라고 CatBoost 에 알려줘야 해요. (나머지 11개는 숫자)
CAT_FEATURES = [
    "religion_type", "edu_level", "wants_kids", "has_kids", "diet_type",
    "job", "status", "diet_strict", "edu_status",
]

# 화면의 흡연/약물 선택값(원본 글자) -> 학습 때 쓴 등급 숫자
DRUGS = {"never": 0, "sometimes": 1, "often": 2}
SMOKES = {"no": 0, "trying to quit": 1, "when drinking": 2, "sometimes": 3, "yes": 4}

# 자기소개 정리 규칙 (team 코드와 동일). '진짜 글이 아닌 것'(점 하나, 물음표, 'na' 등)을 판단하는
# 정규식이에요. service_view.py 의 EDA 참고 신호도 같은 판단 기준을 쓰기 위해 이름 앞에 밑줄(_)을
# 빼서 다른 파일에서도 가져다 쓸 수 있게 공개해 뒀어요. (전에는 service_view.py 가 이 판단을
# 살짝 다른 정규식으로 따로 만들어 놨어서, 둘 중 하나만 고치면 SERVICE 예측과 화면 참고 신호가
# '같은 자기소개'를 다르게 판단할 위험이 있었어요)
MISSING_ESSAY = re.compile(r"(?i)^\s*(?:[.\-?_/]*|na|n/a)\s*$")   # 빈 글자, '.', '-', 'na' 등
_TAG_OR_SPACE = re.compile(r"(?:<[^>]+>|\s)+")                      # HTML 태그 + 공백
_WORD = re.compile(r"\b\w+\b")


# =========================================================
# 2) 자기소개 10칸 -> 숫자 4개 (essay_count, total_words, avg_len, len_std)
# =========================================================
def _clean_essay(text):
    """HTML 특수문자를 풀고, '진짜 글이 아닌 것'(점 하나, 'na' 등)이면 None 을 돌려준다."""
    if not text:
        return None
    text = html.unescape(text)
    return None if MISSING_ESSAY.fullmatch(text.strip()) else text


def essay_features(essays):
    """자기소개 10칸(리스트) -> (작성 칸 수, 총 단어 수, 칸당 평균 글자 수, 칸별 길이 편차)

    평균/편차는 '실제로 쓴 칸'끼리만 비교해요. (팀 코드의 essay_avg_len / essay_len_std 와 동일한 방식)
    표준편차는 칸이 2개 이상 있어야 계산돼요(1개면 편차라는 개념이 없어서 NaN).
    """
    lengths, total_words = [], 0
    for raw in essays:
        cleaned = _clean_essay(raw)
        if cleaned is None:
            continue
        stripped = _TAG_OR_SPACE.sub(" ", cleaned).strip()
        lengths.append(len(stripped))
        total_words += len(_WORD.findall(stripped))

    count = len(lengths)
    avg_len = float(np.mean(lengths)) if lengths else np.nan
    len_std = float(np.std(lengths, ddof=1)) if len(lengths) >= 2 else np.nan
    return count, total_words, avg_len, len_std


# =========================================================
# 3) 프로필 완성도 (17개 항목 중 몇 개에 응답했는지)
# =========================================================
def profile_completeness(answered: dict) -> float:
    """answered : {컬럼명: 응답했으면 True} — project_facts.PROFILE_COMPLETENESS_ITEMS 의 17개 기준.
    화면에 입력칸이 없는 7개는 호출하는 쪽에서 항상 False 로 넘겨요."""
    keys = [col for col, _, _ in facts.PROFILE_COMPLETENESS_ITEMS]
    return sum(1 for k in keys if answered.get(k)) / len(keys)


# =========================================================
# 4) 화면 입력값(dict) -> 모델에 넣을 1행짜리 표
# =========================================================
def build_feature_row(inputs: dict) -> pd.DataFrame:
    """SERVICE 화면에서 모은 입력값을 모델이 이해하는 20개 항목짜리 표(1행)로 바꾼다.

    inputs 의 키는 app.py 의 변수 이름과 맞춰 주세요:
        age, height, job, status, income, education, education_status, religion,
        diet_type, diet_strict, smoking, drugs, has_kids, wants_kids, essays(10개 리스트)
    값이 없는 항목(선택 안 함)은 None 이면 됩니다.
    """
    essay_count, essay_total_words, essay_avg_len, essay_len_std = essay_features(inputs.get("essays", []))

    has_kids = inputs.get("has_kids")
    smoking = inputs.get("smoking")
    drugs = inputs.get("drugs")

    # 화면 선택값 -> 학습 때 쓴 등급 숫자. 안 고르면 NaN (CatBoost 가 빈칸으로 처리)
    smokes_level = SMOKES.get(smoking, np.nan)
    drugs_level = DRUGS.get(drugs, np.nan)

    # 프로필 완성도: 화면에서 받는 10개 항목의 응답 여부 + 화면에 없는 7개는 항상 미응답
    answered = {
        "diet_type": inputs.get("diet_type") is not None,
        "diet_strict": inputs.get("diet_strict") is not None,
        "drugs": drugs is not None,
        "edu_level": inputs.get("education") is not None,
        "edu_status": inputs.get("education_status") is not None,
        "job": inputs.get("job") is not None,
        "has_kids": has_kids is not None,
        "wants_kids": inputs.get("wants_kids") is not None,
        "religion_type": inputs.get("religion") is not None,
        "smokes": smoking is not None,
        # 화면에 입력칸이 없는 7개 (project_facts.PROFILE_COMPLETENESS_ITEMS 참고)
        "body_type": False, "drinks": False, "ethnicity": False,
        "pets_dog": False, "pets_cat": False, "religion": False, "sign": False,
    }

    def cat(value):
        """범주형 값: 안 고르면 학습 때와 같은 'not_disclosed' 로"""
        return value if value is not None else "not_disclosed"

    row = {
        "essay_count": essay_count,
        "profile_completeness": profile_completeness(answered),
        "religion_type": cat(inputs.get("religion")),
        "edu_level": cat(inputs.get("education")),
        "wants_kids": cat(inputs.get("wants_kids")),
        "has_kids": cat(has_kids),
        "diet_type": cat(inputs.get("diet_type")),
        "drugs_level": drugs_level,
        "job": cat(inputs.get("job")),
        "height": inputs.get("height"),
        "status": cat(inputs.get("status")),
        "income": inputs.get("income"),
        "essay_total_words": essay_total_words,
        "smokes_level": smokes_level,
        "diet_strict": cat(inputs.get("diet_strict")),
        "edu_status": cat(inputs.get("education_status")),
        "age": inputs.get("age"),
        "has_kids_na": 1 if has_kids is None else 0,
        "essay_avg_len": essay_avg_len,
        "essay_len_std": essay_len_std,
    }

    df = pd.DataFrame([row], columns=FEATURE_LIST)
    numeric_cols = [c for c in FEATURE_LIST if c not in CAT_FEATURES]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    for col in CAT_FEATURES:
        df[col] = df[col].astype(str).astype("category")
    return df


# =========================================================
# 5) 모델 불러오기 / 예측하기
# =========================================================
def load_model(path):
    """저장해 둔 .cbm 모델 파일을 읽어 온다. (예: models/okcupid_model_09_19_18_56.cbm)"""
    from catboost import CatBoostClassifier
    model = CatBoostClassifier()
    model.load_model(str(path))
    return model


def find_model_path():
    """models 폴더에서 .cbm 파일을 찾는다. (insight_data.py 의 data 폴더 찾기와 같은 방식)

    프로젝트 맨 바깥의 models 폴더를 먼저 보고, 없으면 지금 실행 위치와 ui 폴더 안도 봐요.
    파일이 여러 개면 최근에 수정된 것을 고릅니다. 하나도 없으면 None.
    """
    from pathlib import Path
    here = Path(__file__).resolve().parent      # ui 폴더
    candidates = []
    for folder in (here.parent / "models", Path.cwd() / "models", here / "models"):
        if folder.is_dir():
            candidates += list(folder.glob("*.cbm"))
    if not candidates:
        return None
    return str(max(candidates, key=lambda p: p.stat().st_mtime))


def risk_level_of(probability: float) -> str:
    """확률(0~1) -> 'low' / 'mid' / 'high'. 기준은 project_facts.RISK_THRESHOLDS (지금은 임시값)."""
    t = facts.RISK_THRESHOLDS
    if probability >= t["high"]:
        return "high"
    if probability >= t["mid"]:
        return "mid"
    return "low"


def top_signals(model, row: pd.DataFrame, top_n: int = 5):
    """이 한 명의 예측에 각 항목이 얼마나 영향을 줬는지 (CatBoost 내장 SHAP).

    별도 shap 패키지 없이, CatBoost 가 가지고 있는 기능만으로 계산해요.
    반환: [(항목 이름, 영향값), ...] — 영향값이 양수면 위험을 높이는 쪽, 음수면 낮추는 쪽.
    """
    from catboost import Pool
    cat_idx = [row.columns.get_loc(c) for c in CAT_FEATURES]
    pool = Pool(row, cat_features=cat_idx)
    shap_values = model.get_feature_importance(pool, type="ShapValues")
    values = shap_values[0, :-1]     # 마지막 칸은 '기준값(base value)'이라 뺌
    order = np.argsort(-np.abs(values))[:top_n]
    return [(row.columns[i], float(values[i])) for i in order]


def predict_churn(inputs: dict, model) -> dict:
    """화면 입력값(dict) + 불러온 모델 -> 이탈 위험 결과

    model : load_model() 로 불러온 CatBoostClassifier
    반환  : {"risk": 0.62, "level": "high", "top_signals": [...], "row": 1행짜리 표}
    """
    row = build_feature_row(inputs)
    probability = float(model.predict_proba(row)[0, 1])
    return {
        "risk": probability,
        "level": risk_level_of(probability),
        "top_signals": top_signals(model, row),
        "row": row,
    }
