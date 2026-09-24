"""SERVICE 화면의 '결과 칸' 채우기 (service_view.py)

[이 파일이 하는 일]
SERVICE 화면 오른쪽 '결과 칸'을 카드 3장으로 채워 줍니다.
  1) 예측 결과       : 위험 단계 막대(Low / Medium / High) + 예측 확률(모델 연결 시) 또는
                       '비슷하게 쓴 사용자의 실제 이탈률'(모델 연결 전)
  2) 주요 신호       : 모델이 연결됐으면 진짜 SHAP 값, 아니면 EDA 에서 나온 참고 신호
  3) 추천 리텐션 전략 : 위험 단계(또는 위험 신호)에 맞는 조치를 제안

[모델 연결 전 / 후로 카드 내용이 달라져요]
app.py 가 models 폴더에서 .cbm 파일을 찾으면 predict.predict_churn() 을 호출해서
prediction 인자로 결과를 넘겨줘요. 그러면 이 파일은 진짜 예측값을 보여주고,
prediction 이 없으면(모델 파일이 없을 때) 예전처럼 분석 결과(EDA) 기반 참고 신호를 보여줘요.
어느 쪽이든 화면이 멈추지 않도록 만들어 뒀어요.

[숫자는 어디서 오나요?]
- EDA 참고 신호: project_facts.py (팀 노트북 02_essay_deep_experiment 의 Train 데이터 결과)
- 진짜 예측값 : predict.py 가 불러온 CatBoost 모델
"""
import copy
import re

import streamlit as st
import streamlit.components.v1 as components
import project_facts as facts
from page_retention import LEVELS
from predict import MISSING_ESSAY, predict_churn   # 결측 판단 규칙 + What-if 재예측
from ui_parts import esc, note_box, show

# ---------------------------------------------------------
# 1) 입력값 분석 (계산만 하는 부분. 화면 그리기와 분리해 두었어요)
# ---------------------------------------------------------
# 자기소개에서 '진짜 글이 아닌 것'(점 하나, 물음표 등)은 안 쓴 것으로 봅니다.
# 이 판단 자체는 predict.py 의 MISSING_ESSAY 를 그대로 가져다 써요. (전에는 여기서 살짝 다른
# 정규식을 따로 만들어 놨어서, SERVICE 예측과 이 화면의 참고 신호가 같은 자기소개를 서로 다르게
# '비어 있다/아니다'로 판단할 수 있는 위험이 있었어요. 하나로 합쳐서 그 위험을 없앴어요.)
_LINK = re.compile(r"(?i)https?://|www\.")


def clean_essay(text):
    """HTML 태그를 지우고 공백을 정리한 자기소개 글. 진짜 글이 없으면 빈 글자를 돌려줌."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if MISSING_ESSAY.fullmatch(text) or not text else text


def _group_index(value, upper_bounds):
    """value 가 upper_bounds 의 몇 번째 구간(이하)에 속하는지. 마지막은 '초과' 구간."""
    for i, bound in enumerate(upper_bounds):
        if value <= bound:
            return i
    return len(upper_bounds)


def analyze_inputs(essays, has_kids, status):
    """화면에서 입력한 값을 분석해서 '참고 신호'를 만든다.

    essays   : 자기소개 10칸의 글 목록 (비어 있으면 "")
    has_kids : 'no' / 'yes' / 'not_disclosed' / None(선택 안 함)
    status   : 'single' / 'available' / 'seeing someone' / 'married' / 'unknown' / None
    반환     : dict (count, total_len, avg_len, group, signals, strategies, touched)
    """
    cleaned = [clean_essay(e) for e in essays]
    written = [e for e in cleaned if e]
    count = len(written)
    total_len = sum(len(e) for e in written)
    avg_len = total_len / count if count else None
    has_link = any(_LINK.search(e) for e in written)

    # 아직 아무것도 입력하지 않았다면 신호를 만들지 않아요. (빈 화면에 경고가 뜨는 걸 방지)
    touched = bool(written) or has_kids is not None or status is not None

    # '작성 칸 수 x 칸당 평균 글자 수' 표에서 내 입력과 같은 칸 찾기
    group = None
    if count >= 1:
        row = _group_index(count, [3, 6, 9])            # 1~3칸 / 4~6칸 / 7~9칸 / 10칸
        col = _group_index(avg_len, [50, 150, 350, 700])  # 50자 이하 ... 700자 초과
        group = {"rate": facts.ESSAY_GRID_RATES[row][col], "n": facts.ESSAY_GRID_COUNTS[row][col],
                 "row": facts.ESSAY_GRID_ROWS[row], "col": facts.ESSAY_GRID_COLS[col]}

    signals = []           # 각 항목: (종류 warn/ok, 제목, 근거 숫자)
    strategies = []        # 추천 전략 이름
    if touched:
        essay_sig, kids_sig, status_sig = facts.KEY_SIGNALS[1], facts.KEY_SIGNALS[2], facts.KEY_SIGNALS[4]
        link_sig = facts.KEY_SIGNALS[3]

        # ① 자기소개 분량 (총 100자 이하인가)
        if total_len <= 100:
            signals.append(("warn", f"자기소개가 거의 비어 있어요 (총 {total_len}자)",
                            f"총 100자 이하면 이탈률 {essay_sig['high_rate']:.1f}% (초과하면 {essay_sig['low_rate']:.1f}%)"))
            strategies += ["프로필 작성 유도", "프로필 개선 가이드"]
        else:
            signals.append(("ok", f"자기소개를 충분히 썼어요 (총 {total_len:,}자)",
                            f"100자 초과면 이탈률 {essay_sig['low_rate']:.1f}% (이하면 {essay_sig['high_rate']:.1f}%)"))

        # ② 자기소개에 링크가 있는가 (있으면 이탈률이 낮은 경향)
        if has_link:
            signals.append(("ok", "자기소개에 링크가 들어 있어요",
                            f"링크 있음 {link_sig['low_rate']:.1f}% (없음 {link_sig['high_rate']:.1f}%)"))

        # ③ 자녀 항목에 응답했는가
        if has_kids is None or has_kids == "not_disclosed":
            signals.append(("warn", "자녀 항목이 비어 있어요",
                            f"무응답이면 이탈률 {kids_sig['high_rate']:.1f}% (응답하면 {kids_sig['low_rate']:.1f}%)"))
            strategies.append("프로필 완성 리워드")
        else:
            signals.append(("ok", "자녀 항목에 응답했어요",
                            f"응답하면 이탈률 {kids_sig['low_rate']:.1f}% (무응답이면 {kids_sig['high_rate']:.1f}%)"))

        # ④ 관계 상태
        if status == "seeing someone":
            signals.append(("warn", "만나는 사람이 있다고 적었어요",
                            f"이 경우 이탈률 {status_sig['high_rate']:.1f}% (싱글 {status_sig['low_rate']:.1f}%)"))
            strategies.append("재접속 알림")
        elif status in ("single", "available"):
            signals.append(("ok", "새로운 만남을 찾는 상태예요",
                            f"싱글 {status_sig['low_rate']:.1f}% vs 만나는 사람 있음 {status_sig['high_rate']:.1f}%"))

    strategies = list(dict.fromkeys(strategies))       # 중복 제거 (순서는 유지)
    return {"count": count, "total_len": total_len, "avg_len": avg_len, "group": group,
            "signals": signals, "strategies": strategies, "touched": touched}


# ---------------------------------------------------------
# 2) 화면 그리기
# ---------------------------------------------------------
# 전략 이름 -> (아이콘, 설명). RETENTION 화면(page_retention.py)의 내용을 그대로 가져와요.
STRATEGY_INFO = {title: (icon, text) for level in LEVELS for icon, title, text in level["actions"]}

# 위험 단계('low'/'mid'/'high') -> RETENTION 화면의 전략 카드 전체
LEVEL_BY_KIND = {level["kind"]: level for level in LEVELS}

# feature 영문 이름 -> 화면에 보여줄 한글 이름. project_facts.py 에서 한 번만 만들어 둔 걸 가져다 써요.
FEATURE_LABELS = facts.FEATURE_LABELS

# SERVICE 결과에서 SHAP 신호와 운영 액션을 직접 연결해 보여주기 위한 설명표.
# RETENTION의 큰 전략 범주는 유지하되, 이 화면에서는 왜 추천됐는지가 바로 보이도록 구체화합니다.
SIGNAL_ACTIONS = {
    "작성한 칸 수": ("자기소개 작성 유도", "비어 있는 자기소개 항목을 단계별로 채우도록 안내"),
    "총 단어 수": ("자기소개 보완 가이드", "작성 예시와 질문형 가이드로 소개 분량 보완"),
    "칸당 평균 글자 수": ("자기소개 품질 가이드", "짧거나 과도하게 긴 항목을 읽기 좋은 분량으로 안내"),
    "칸별 길이 편차": ("프로필 균형 개선", "일부 항목에 치우친 자기소개를 고르게 보완하도록 안내"),
    "프로필 완성도": ("프로필 완성 리워드", "미작성 항목을 완료하면 젤리 등 보상 제공"),
    "학력 단계": ("학력 정보 확인", "오래되거나 누락된 학력 정보를 다시 확인하도록 요청"),
    "졸업/재학/중퇴": ("학업 상태 업데이트", "졸업·재학·중퇴 상태를 현재 정보로 갱신하도록 안내"),
    "식단 종류": ("취향 기반 추천", "식단 취향이 비슷한 상대와 관심사를 우선 추천"),
    "식단 엄격도": ("식단 정보 재확인", "현재 식단 기준을 다시 선택하고 취향 추천에 반영"),
    "관계 상태": ("관계 상태 재확인", "현재 만남 목적을 확인한 뒤 맞춤 추천·재접속 알림 제공"),
    "직업": ("직업·관심사 기반 추천", "직업과 연관된 관심사 그룹이나 상대를 추천"),
    "자녀 유무": ("가족 정보 선택 안내", "민감정보임을 명시하고 선택적으로 정보를 보완하도록 안내"),
    "자녀 항목 무응답": ("가족 정보 선택 안내", "응답 또는 비공개를 명확히 선택하도록 안내"),
    "자녀 희망": ("관계 가치관 추천", "자녀 계획이 비슷한 상대를 우선 추천"),
    "종교": ("가치관 기반 추천", "종교·가치관 선호가 비슷한 상대를 추천"),
    "흡연 정도": ("라이프스타일 추천", "흡연 성향이 비슷한 상대를 우선 추천"),
    "약물 사용 정도": ("라이프스타일 정보 확인", "라이프스타일 정보를 다시 확인하도록 안내"),
    "연소득": ("소득 공개 설정 확인", "공개 여부와 입력값을 다시 확인하도록 안내"),
    "키": ("프로필 정보 확인", "현재 프로필 정보가 정확한지 확인하도록 안내"),
    "나이": ("기본 정보 확인", "가입 정보와 현재 프로필 정보가 일치하는지 확인"),
}

# What-if에서 바꿀 수 있는 실제 모델 입력값. 화면(app.py)의 카테고리와 정확히 맞춥니다.
WHAT_IF_FIELDS = {
    "자기소개": ("essays", None),
    "최종 학력": ("education", {
        "미응답": None, "고등학교": "high school", "전문대학": "two-year college",
        "대학교": "college/university", "석사": "masters program", "박사": "ph.d program",
    }),
    "교육 상태": ("education_status", {
        "미응답": None, "졸업": "graduated from", "재학 중": "working on", "중퇴": "dropped out of",
    }),
    "식단 유형": ("diet_type", {
        "미응답": None, "특별한 제한 없음": "anything", "채식": "vegetarian", "비건": "vegan",
        "코셔 식단": "kosher", "할랄 식단": "halal", "기타": "other",
    }),
    "식단 준수 정도": ("diet_strict", {
        "미응답": None, "특별히 신경 쓰지 않음": "plain", "대체로 지킴": "mostly", "엄격하게 지킴": "strictly",
    }),
    "관계 상태": ("status", {
        "미응답": None, "싱글": "single", "만남 가능": "available",
        "만나는 사람 있음": "seeing someone", "기혼": "married",
    }),
    "직업": ("job", {
        "미응답": None, "기타": "other", "학생": "student",
        "과학·기술·공학": "science / tech / engineering",
        "컴퓨터·소프트웨어": "computer / hardware / software",
        "예술·음악·글쓰기": "artistic / musical / writer",
        "영업·마케팅": "sales / marketing / biz dev", "의료·건강": "medicine / health",
        "교육·학계": "education / academia", "경영·임원": "executive / management",
        "금융·부동산": "banking / financial / real estate", "법률": "law / legal services",
        "숙박·여행": "hospitality / travel", "건설·기술직": "construction / craftsmanship",
        "사무·행정": "clerical / administrative", "정치·공공행정": "political / government",
        "운수업": "transportation", "무직": "unemployed", "은퇴": "retired", "군인": "military",
    }),
    "자녀 유무": ("has_kids", {"미응답": None, "자녀 없음": "no", "자녀 있음": "yes"}),
    "향후 자녀 계획": ("wants_kids", {
        "미응답": None, "원함": "yes", "원하지 않음": "no", "아직 모르겠음": "maybe",
    }),
    "흡연 여부": ("smoking", {
        "미응답": None, "피우지 않음": "no", "가끔 피움": "sometimes",
        "술 마실 때만": "when drinking", "금연 중": "trying to quit", "자주 피움": "yes",
    }),
    "약물 사용 여부": ("drugs", {
        "미응답": None, "사용하지 않음": "never", "가끔 사용": "sometimes", "자주 사용": "often",
    }),
    "종교": ("religion", {
        "미응답": None, "불가지론": "agnosticism", "무신론": "atheism", "기독교": "christianity",
        "가톨릭": "catholicism", "유대교": "judaism", "불교": "buddhism",
        "힌두교": "hinduism", "이슬람교": "islam", "기타": "other",
    }),
}


def _rate_color(rate):
    """이탈률(%, 0~100)이 높을수록 빨강, 낮을수록 초록 (숫자 색)"""
    if rate >= 40:
        return "#c81e55"
    if rate >= 28:
        return "#9a5a08"
    if rate <= 20:
        return "#237a3f"
    return "#5a5a5a"


def _prob_color(p):
    """예측 확률(0~1)이 높을수록 빨강, 낮을수록 초록 (숫자 색). 기준은 RISK_THRESHOLDS 와 맞춤."""
    t = facts.RISK_THRESHOLDS
    if p >= t["high"]:
        return "#c81e55"
    if p >= t["mid"]:
        return "#9a5a08"
    return "#237a3f"


def _card_prediction(info, prediction=None, baseline_prediction=None, change_label=None):
    """카드 1: 예측 결과.

    prediction 이 있으면(모델 연결됨) 진짜 예측 확률과 위험 단계를 보여주고,
    없으면(모델 연결 전) 위험 단계 자리를 비워 둔 채 '비슷한 사용자의 실제 이탈률'을 참고로 보여줘요.
    """
    risk_level = prediction["level"] if prediction else None
    segments = ""
    for key, label in (("low", "Low"), ("mid", "Medium"), ("high", "High")):
        # 위험 단계를 아직 모르면(모델 연결 전) 세 칸 모두 흐리게, 알면 해당 칸만 또렷하게
        dim = " dim" if risk_level != key else ""
        segments += f'<span class="risk-seg {key}{dim}">{label}</span>'

    if prediction and baseline_prediction:
        ribbon, note = "프로필 변경 재예측", "동일한 CatBoost 모델로 변경 전·후 입력을 비교한 결과예요."
        before = float(baseline_prediction["risk"])
        after = float(prediction["risk"])
        delta_pp = (after - before) * 100
        direction = "하락" if delta_pp < 0 else "상승" if delta_pp > 0 else "변화 없음"
        arrow_class = "down" if delta_pp < 0 else "up" if delta_pp > 0 else "same"
        tier_label = lambda level: {"low":"LOW RISK", "mid":"MEDIUM RISK", "high":"HIGH RISK"}[level]
        chips = "".join(
            f'<span class="change-chip">{esc(part.strip())}</span>'
            for part in (change_label or "").split(" · ") if part.strip()
        )
        warning = (
            '<div class="hero-model-note">변화 폭이 큰 경우 실제 개선 효과가 아니라, '
            '모델이 변경된 입력 조합에 민감하게 반응한 결과일 수 있어요.</div>'
            if abs(delta_pp) >= 20 else ""
        )
        ref = (
            f'<div class="hero-compare">'
            f'<div class="compare-value before"><small>변경 전</small><strong>{before*100:.1f}%</strong>'
            f'<span>{tier_label(baseline_prediction["level"])}</span></div>'
            f'<div class="compare-arrow {arrow_class}"><b>→</b><span>{abs(delta_pp):.1f}%p {direction}</span></div>'
            f'<div class="compare-value after"><small>변경 후</small><strong>{after*100:.1f}%</strong>'
            f'<span>{tier_label(prediction["level"])}</span></div></div>'
            f'<div class="change-chips">{chips}</div>{warning}'
        )
    elif prediction:
        ribbon, note = "모델 연결됨", "CatBoost 모델이 실제로 계산한 위험 단계예요."
        p = prediction["risk"]
        color = _prob_color(p)
        actual = facts.TIER_ACTUAL_RATES[risk_level]
        level_label = {"low": "LOW RISK", "mid": "MEDIUM RISK", "high": "HIGH RISK"}[risk_level]
        ref = (f'<div class="result-hero-grid">'
               f'<div class="hero-score" style="color:{color}"><strong>{p * 100:.1f}</strong><span>%</span>'
               f'<small>예측 이탈 확률</small></div>'
               f'<div class="hero-summary"><span class="level-pill {risk_level}">{level_label}</span>'
               f'<p>평가 데이터에서 같은 등급 사용자의 실제 이탈률은 <b>{actual:.1f}%</b>였습니다.</p>'
               f'<small>확률의 절대값보다 Low·Medium·High 등급을 중심으로 해석해 주세요.</small>'
               f'</div></div>')
    else:
        ribbon, note = "모델 연결 전", "모델이 연결되면 위험 단계가 여기에 표시돼요."
        group = info["group"]
        if group:
            color = _rate_color(group["rate"])
            ref = (f'<div class="ref-box"><div class="ref-rate" style="color:{color}">{group["rate"]:.1f}%</div>'
                   f'<div class="ref-text"><b>비슷하게 쓴 사용자의 실제 이탈률</b><br>'
                   f'자기소개 {esc(group["row"])} · 칸당 {esc(group["col"])} · {group["n"]:,}명 기준</div></div>')
        elif info["touched"]:
            ref = ('<div class="ref-box"><div class="ref-text">자기소개를 입력하면, 비슷하게 쓴 사용자의 '
                   '<b>실제 이탈률</b>을 여기에 보여줘요.</div></div>')
        else:
            ref = ('<div class="ref-box"><div class="ref-text">정보를 입력하면, 비슷한 사용자의 '
                   '<b>실제 이탈률</b>을 여기에 보여줘요.</div></div>')

    return (f'<div class="result-card result-hero"><span class="preview-ribbon">{ribbon}</span>'
            '<div class="result-kicker">RISK OVERVIEW</div><div class="result-title">예측 결과</div>'
            f'{ref}<div class="risk-scale">{segments}</div><div class="result-note">{note}</div></div>')


def _card_signals(info, prediction=None):
    """카드 2: 주요 신호.

    prediction 이 있으면 진짜 SHAP 값 상위 5개를, 없으면 EDA 기반 참고 신호를 보여줘요.
    """
    if prediction:
        rows = ""
        for rank, (code, value) in enumerate(prediction["top_signals"][:3], start=1):
            name = FEATURE_LABELS.get(code, code)
            up = value > 0                                  # 양수 = 위험을 높이는 쪽
            icon, kind = ("↑", "warn") if up else ("↓", "ok")
            stat = f"위험을 {'높이는' if up else '낮추는'} 방향 · SHAP {abs(value):.2f}"
            rows += (f'<div class="sig-row {kind}"><div class="signal-rank">0{rank}</div>'
                     f'<div class="sig-icon">{icon}</div><div class="signal-copy">'
                     f'<div class="sig-title">{esc(name)}</div><div class="sig-stat">{esc(stat)}</div></div></div>')
        sub = "개인 예측에 가장 크게 작용한 SHAP 신호 TOP 3"
        body = rows
    elif info["signals"]:
        rows = ""
        for kind, title, stat in info["signals"]:
            icon = "⚠️" if kind == "warn" else "✅"
            rows += (f'<div class="sig-row {kind}"><div class="sig-icon">{icon}</div><div>'
                     f'<div class="sig-title">{esc(title)}</div><div class="sig-stat">{esc(stat)}</div></div></div>')
        sub = "지금은 분석 결과(EDA) 기준이에요. 모델이 연결되면 SHAP 값으로 바뀌어요."
        body = rows
    else:
        checks = "".join(f'<span class="chip">{c}</span>' for c in
                         ("자기소개 분량", "자기소개 링크", "자녀 항목 응답", "관계 상태"))
        sub = "지금은 분석 결과(EDA) 기준이에요. 모델이 연결되면 SHAP 값으로 바뀌어요."
        body = ('<div class="placeholder" style="margin-top:0">정보를 입력하면 이탈률 차이가 컸던 신호를 '
                f'여기에 골라서 보여줘요.</div><div style="margin-top:12px">{checks}</div>')
    return ('<div class="result-card compact-card"><div class="result-kicker">WHY THIS SCORE</div>'
            '<div class="result-title">주요 예측 신호</div>'
            f'<div class="dash-sub">{esc(sub)}</div>'
            f'{body}</div>')


def _card_strategies(info, prediction=None):
    """카드 3: 추천 리텐션 전략.

    prediction 이 있으면 이 사람의 SHAP 신호 중 '위험을 실제로 높이는 쪽'(양수)만 골라서
    RETENTION.REASON_TO_STRATEGY 로 전략을 찾아 보여줘요. (전에는 등급 전체 전략 5개를
    무조건 다 보여줬는데, 그러면 프로필을 열심히 쓴 사람도 자기소개랑 상관없는 이유로 High
    등급이 됐을 때 "프로필 작성 유도"를 받는 식으로 안 맞는 전략이 나갔어요. 이제는 이 사람의
    진짜 위험 원인에 맞는 전략만 추려서 보여줘요.)
    없으면 지금까지처럼 입력값에서 찾은 신호에 맞는 전략만 골라서 보여줘요.
    """
    if prediction:
        level = LEVEL_BY_KIND[prediction["level"]]
        # 위험을 '낮추는'(음수) 신호는 전략이 필요 없어서 빼고, '높이는'(양수) 신호만 남겨요.
        risk_signals = [(code, value) for code, value in prediction["top_signals"][:3] if value > 0]

        action_groups = {}       # 같은 액션으로 이어지는 신호는 한 행으로 묶어요.
        for code, _ in risk_signals:
            signal_name = FEATURE_LABELS.get(code, code)
            action_name, action_text = SIGNAL_ACTIONS.get(
                signal_name,
                (facts.REASON_TO_STRATEGY.get(signal_name, facts.REASON_TO_STRATEGY_DEFAULT),
                 "해당 프로필 정보를 확인하고 사용자에게 맞는 운영 전략을 적용"),
            )
            if action_name not in action_groups:
                action_groups[action_name] = {"signals": [], "text": action_text}
            action_groups[action_name]["signals"].append(signal_name)

        if action_groups:
            header = (f'<div class="dash-sub" style="margin-top:-8px">'
                      f'각 예측 신호가 어떤 운영 액션으로 이어지는지 연결했습니다.</div>')
        else:
            # 상위 신호가 전부 '보호 요인'이면(위험을 높이는 뚜렷한 신호가 없으면), 등급 전체 전략으로 대신해요.
            action_groups = {
                name: {"signals": [f'{level["name"]} 등급'], "text": text}
                for _, name, text in level["actions"][:3]
            }
            header = (f'<div class="dash-sub" style="margin-top:-8px">'
                      f'뚜렷하게 위험을 높인 신호가 없어서, {esc(level["name"])} 등급의 기본 전략을 보여줘요.</div>')

        rows = ""
        for rank, (action_name, action) in enumerate(list(action_groups.items())[:3], start=1):
            sources = " · ".join(dict.fromkeys(action["signals"]))
            rows += (f'<div class="action-row"><div class="action-index">0{rank}</div><div class="action-main">'
                     f'<div class="action-source">{esc(sources)} <span>→</span></div>'
                     f'<div class="action-name">{esc(action_name)}</div>'
                     f'<div class="action-desc">{esc(action["text"])}</div></div></div>')
        body = header + rows
    elif info["strategies"]:
        rows = ""
        for name in info["strategies"]:
            icon, text = STRATEGY_INFO.get(name, ("✨", ""))
            rows += (f'<div class="strat-row"><div class="strat-icon">{icon}</div><div>'
                     f'<div class="sig-title">{esc(name)}</div><div class="sig-stat">{esc(text)}</div></div></div>')
        body = rows
    elif info["touched"]:
        body = ('<div class="placeholder" style="margin-top:0">지금 입력한 정보에서는 눈에 띄는 위험 신호가 없어요. '
                '모델 결과가 나오면 위험 단계에 맞는 전략을 보여줘요.</div>')
    else:
        body = ('<div class="placeholder" style="margin-top:0">위험 신호가 확인되면, 그에 맞는 '
                '리텐션 전략을 여기에 제안해요.</div>')
    return ('<div class="result-card compact-card"><div class="result-kicker">NEXT BEST ACTION</div>'
            '<div class="result-title">추천 리텐션 전략</div>'
            f'{body}</div>')


def _inject_dialog_styles():
    """결과 팝업만 홈 화면과 어울리는 간결한 카드 디자인으로 다듬는다."""
    st.markdown("""
    <style>
    div[data-testid="stDialog"] div[role="dialog"] {
        border-radius: 28px;
        border: 1px solid rgba(228, 37, 96, .12);
        box-shadow: 0 28px 80px rgba(83, 27, 48, .20);
        background: linear-gradient(180deg, #fff 0%, #fffafb 100%);
    }
    div[data-testid="stDialog"] .result-card {
        margin: 0 0 14px 0; padding: 24px;
        border: 1px solid #f0e4e8; border-radius: 22px;
        box-shadow: 0 8px 24px rgba(76, 38, 51, .055);
        background: rgba(255,255,255,.96);
    }
    div[data-testid="stDialog"] .result-hero {
        position: relative; overflow: hidden;
        background: radial-gradient(circle at 94% 0%, #ffe3ec 0, transparent 34%), #fff;
    }
    div[data-testid="stDialog"] .result-kicker {
        color: #e42560; font-size: 11px; font-weight: 800; letter-spacing: .13em;
        margin-bottom: 4px;
    }
    div[data-testid="stDialog"] .result-title {
        font-size: 21px; font-weight: 800; color: #241b1e; margin-bottom: 16px;
    }
    div[data-testid="stDialog"] .preview-ribbon {
        top: 20px; right: 22px; border: 0; background: #fff0f5; color: #d61f57;
    }
    div[data-testid="stDialog"] .result-hero-grid {
        display: grid; grid-template-columns: 190px 1fr; gap: 24px; align-items: center;
        padding: 4px 0 20px;
    }
    div[data-testid="stDialog"] .hero-score strong { font-size: 52px; line-height: 1; letter-spacing: -.05em; }
    div[data-testid="stDialog"] .hero-score > span { font-size: 25px; font-weight: 800; }
    div[data-testid="stDialog"] .hero-score small { display: block; margin-top: 8px; color: #786970; font-weight: 700; }
    div[data-testid="stDialog"] .hero-summary { border-left: 1px solid #f0dfe5; padding-left: 24px; }
    div[data-testid="stDialog"] .hero-summary p { margin: 12px 0 5px; color: #41363a; line-height: 1.55; }
    div[data-testid="stDialog"] .hero-summary small { color: #8d7c83; }
    div[data-testid="stDialog"] .level-pill {
        display: inline-flex; padding: 6px 11px; border-radius: 999px; font-size: 11px; font-weight: 900;
        letter-spacing: .08em;
    }
    div[data-testid="stDialog"] .level-pill.high { color:#c91852; background:#ffe4ed; }
    div[data-testid="stDialog"] .level-pill.mid { color:#976316; background:#fff2dc; }
    div[data-testid="stDialog"] .level-pill.low { color:#247146; background:#e8f7ee; }
    div[data-testid="stDialog"] .risk-scale { margin: 0; gap: 7px; }
    div[data-testid="stDialog"] .risk-seg { height: 9px; font-size: 0; border-radius: 999px; }
    div[data-testid="stDialog"] .result-note { margin-top: 9px; text-align: right; font-size: 11px; color:#9a8b91; }
    div[data-testid="stDialog"] .compact-card { min-height: 100%; padding: 22px; }
    div[data-testid="stDialog"] .dash-sub { margin: -8px 0 14px !important; color:#8d7c83; font-size:12px; }
    div[data-testid="stDialog"] .sig-row {
        display:grid; grid-template-columns: 28px 28px 1fr; gap:8px; align-items:center;
        padding: 12px 0; margin:0; border-radius:0; background:transparent !important;
        border-bottom:1px solid #f3e8eb;
    }
    div[data-testid="stDialog"] .sig-row:last-child { border-bottom:0; }
    div[data-testid="stDialog"] .signal-rank { color:#c8b7bd; font-size:11px; font-weight:800; }
    div[data-testid="stDialog"] .sig-icon {
        width:24px; height:24px; display:grid; place-items:center; border-radius:8px;
        font-size:14px; font-weight:900;
    }
    div[data-testid="stDialog"] .sig-row.warn .sig-icon { color:#d81f58; background:#ffe7ef; }
    div[data-testid="stDialog"] .sig-row.ok .sig-icon { color:#26784a; background:#e8f7ee; }
    div[data-testid="stDialog"] .sig-title { font-size:14px; color:#2e2528; }
    div[data-testid="stDialog"] .sig-stat { margin-top:2px; font-size:11px; color:#8b7b81; }
    div[data-testid="stDialog"] .action-row {
        display:grid; grid-template-columns:28px 1fr; gap:10px; padding:12px 0;
        border-bottom:1px solid #f3e8eb;
    }
    div[data-testid="stDialog"] .action-row:last-child { border-bottom:0; }
    div[data-testid="stDialog"] .action-index {
        color:#c8b7bd; font-size:11px; font-weight:800; padding-top:3px;
    }
    div[data-testid="stDialog"] .action-source {
        color:#d9255e; font-size:10px; font-weight:800; letter-spacing:.02em; margin-bottom:3px;
    }
    div[data-testid="stDialog"] .action-source span { color:#c5aeb6; padding-left:3px; }
    div[data-testid="stDialog"] .action-name {
        color:#2b2225; font-size:14px; font-weight:800; margin-bottom:3px;
    }
    div[data-testid="stDialog"] .action-desc {
        color:#8b7b81; font-size:11px; line-height:1.5;
    }
    div[data-testid="stDialog"] .scenario-result {
        margin-top:18px; padding:22px; border:1px solid #efdfe5; border-radius:22px;
        background:linear-gradient(135deg,#fff 0%,#fff8fa 100%);
        box-shadow:0 10px 28px rgba(80,36,52,.06);
    }
    div[data-testid="stDialog"] .scenario-eyebrow {
        color:#df225b; font-size:10px; font-weight:900; letter-spacing:.14em; margin-bottom:13px;
    }
    div[data-testid="stDialog"] .scenario-grid {
        display:grid; grid-template-columns:1fr 54px 1fr; gap:14px; align-items:stretch;
    }
    div[data-testid="stDialog"] .scenario-side {
        padding:18px; border-radius:17px; background:#faf7f8; border:1px solid #f2e9ec;
    }
    div[data-testid="stDialog"] .scenario-side.after {
        background:#f1faf4; border-color:#dcefe2;
    }
    div[data-testid="stDialog"] .scenario-label { color:#8a7980; font-size:12px; font-weight:700; }
    div[data-testid="stDialog"] .scenario-number {
        margin:7px 0 8px; color:#33292d; font-size:38px; line-height:1; font-weight:900; letter-spacing:-.04em;
    }
    div[data-testid="stDialog"] .scenario-side.after .scenario-number { color:#247449; }
    div[data-testid="stDialog"] .scenario-tier {
        display:inline-flex; padding:5px 9px; border-radius:999px; background:#fff;
        color:#6f6066; font-size:10px; font-weight:900; letter-spacing:.06em;
    }
    div[data-testid="stDialog"] .scenario-arrow {
        display:flex; flex-direction:column; align-items:center; justify-content:center; color:#d8235b;
        font-size:24px; font-weight:900;
    }
    div[data-testid="stDialog"] .scenario-arrow small {
        margin-top:6px; padding:5px 8px; border-radius:999px; background:#e8f7ed;
        color:#28774a; font-size:10px; white-space:nowrap;
    }
    div[data-testid="stDialog"] .change-chips { display:flex; flex-wrap:wrap; gap:7px; margin-top:16px; }
    div[data-testid="stDialog"] .change-chip {
        padding:7px 10px; border-radius:10px; background:#fff0f5; color:#b91d4d;
        font-size:11px; font-weight:750;
    }
    div[data-testid="stDialog"] .scenario-summary {
        margin-top:14px; color:#392f33; font-size:14px; font-weight:750; line-height:1.55;
    }
    div[data-testid="stDialog"] .scenario-caution {
        margin-top:12px; padding:11px 13px; border-radius:12px; background:#fff8e8;
        color:#80601e; font-size:11px; line-height:1.55;
    }
    div[data-testid="stDialog"] .hero-compare {
        display:grid; grid-template-columns:1fr 150px 1fr; gap:18px; align-items:center;
        padding:6px 0 16px;
    }
    div[data-testid="stDialog"] .compare-value {
        padding:18px 20px; border:1px solid #f0e5e8; border-radius:18px; background:#faf8f9;
    }
    div[data-testid="stDialog"] .compare-value.after { background:#f1faf4; border-color:#dcefe2; }
    div[data-testid="stDialog"] .compare-value small { display:block; color:#8d7d83; font-weight:750; }
    div[data-testid="stDialog"] .compare-value strong {
        display:block; margin:5px 0 8px; color:#382d31; font-size:42px; line-height:1; letter-spacing:-.05em;
    }
    div[data-testid="stDialog"] .compare-value.after strong { color:#257548; }
    div[data-testid="stDialog"] .compare-value span {
        display:inline-flex; padding:5px 8px; border-radius:999px; background:#fff;
        color:#74646b; font-size:10px; font-weight:900; letter-spacing:.05em;
    }
    div[data-testid="stDialog"] .compare-arrow { text-align:center; }
    div[data-testid="stDialog"] .compare-arrow b { display:block; color:#dd255c; font-size:30px; line-height:1; }
    div[data-testid="stDialog"] .compare-arrow span {
        display:inline-flex; margin-top:9px; padding:6px 10px; border-radius:999px;
        font-size:11px; font-weight:850; white-space:nowrap;
    }
    div[data-testid="stDialog"] .compare-arrow.down span { color:#24764a; background:#e7f7ed; }
    div[data-testid="stDialog"] .compare-arrow.up span { color:#c81e55; background:#ffe8ef; }
    div[data-testid="stDialog"] .compare-arrow.same span { color:#75656b; background:#f2edef; }
    div[data-testid="stDialog"] .hero-model-note {
        margin-top:11px; padding:10px 12px; border-radius:11px; background:#fff8e8;
        color:#80601e; font-size:11px; line-height:1.5;
    }
    div[data-testid="stDialog"] hr { border-color:#f2e2e7; margin: 16px 0 20px; }
    @media (max-width: 760px) {
        div[data-testid="stDialog"] .result-hero-grid { grid-template-columns: 1fr; gap:14px; }
        div[data-testid="stDialog"] .hero-summary { border-left:0; border-top:1px solid #f0dfe5; padding:14px 0 0; }
        div[data-testid="stDialog"] .scenario-grid { grid-template-columns:1fr; }
        div[data-testid="stDialog"] .scenario-arrow { transform:rotate(90deg); min-height:28px; }
        div[data-testid="stDialog"] .scenario-arrow small { display:none; }
        div[data-testid="stDialog"] .hero-compare { grid-template-columns:1fr; }
        div[data-testid="stDialog"] .compare-arrow b { transform:rotate(90deg); }
    }
    </style>
    """, unsafe_allow_html=True)


@st.dialog("이탈 위험 분석 결과", width="large", dismissible=False)
def _render_result_dialog(info, current_inputs, current_prediction, model):
    """기본 분석 결과를 먼저 보여주고, 원할 때만 프로필 변경 재예측을 연다."""
    current_risk = float(current_prediction["risk"])
    _inject_dialog_styles()

    # 재계산 결과가 있으면 화면 전체(확률·SHAP 신호·추천 전략)를 변경 후 결과로 전환합니다.
    saved_whatif = st.session_state.get("service_whatif")
    has_active_whatif = bool(
        saved_whatif
        and abs(float(saved_whatif["base_risk"]) - current_risk) < 1e-12
    )
    displayed_prediction = saved_whatif["prediction"] if has_active_whatif else current_prediction

    # 재계산 직후 스크롤이 돌아올 정확한 위치입니다.
    st.markdown('<div id="service-result-top"></div>', unsafe_allow_html=True)

    intro_col, close_col = st.columns([8, 1])
    with intro_col:
        st.markdown("<div style='color:#8d7c83;font-size:13px;margin:2px 0 16px'>"
                    "입력한 프로필을 바탕으로 이탈 위험과 우선 대응 전략을 정리했습니다.</div>",
                    unsafe_allow_html=True)
    with close_col:
        if st.button("닫기", key="close_result_dialog", type="secondary", use_container_width=True):
            # 전체 화면을 다시 실행하면 분석 버튼의 클릭 상태가 False가 되어 팝업만 닫힙니다.
            st.rerun()

    # 기존에 SERVICE 오른쪽 칸에 있던 결과를 모두 팝업 안으로 옮깁니다.
    show(_card_prediction(
        info,
        displayed_prediction,
        baseline_prediction=current_prediction if has_active_whatif else None,
        change_label=saved_whatif.get("label") if has_active_whatif else None,
    ))
    signal_col, strategy_col = st.columns([1.08, .92], gap="medium")
    with signal_col:
        show(_card_signals(info, displayed_prediction))
    with strategy_col:
        show(_card_strategies(info, displayed_prediction))

    # What-if 계산을 마친 직후라면 팝업 안의 최상단 결과 카드로 자동 이동합니다.
    # st.markdown 안의 script는 실행되지 않아서, 높이 0인 component에서 부모 화면을 제어합니다.
    if st.session_state.pop("service_scroll_result_top", False):
        components.html(
            """
            <script>
            setTimeout(() => {
                const doc = window.parent.document;
                const target = doc.getElementById('service-result-top');
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 120);
            </script>
            """,
            height=0,
            width=0,
        )

    if has_active_whatif:
        reset_col, _ = st.columns([1.35, 3])
        with reset_col:
            if st.button("↩ 원래 결과로 돌아가기", key="reset_whatif_result", use_container_width=True):
                st.session_state.pop("service_whatif", None)
                st.rerun(scope="fragment")

    st.divider()
    st.markdown("#### 프로필을 바꾸면 예측도 달라질까요?")
    st.caption("현재 결과를 확인한 뒤, 자기소개·학력·식단·관계 상태 등 프로필 항목을 바꿔 같은 모델로 다시 계산할 수 있어요.")

    if st.button(
        "✨ 프로필을 바꿔 다시 계산해보기",
        use_container_width=True,
        key="open_whatif_editor",
    ):
        st.session_state["service_show_whatif_editor"] = True

    if not st.session_state.get("service_show_whatif_editor", False):
        return

    # 최초 입력에서 아예 선택하지 않은 항목과, 이미 입력했지만 바꿔 볼 항목을 분리해서 보여줍니다.
    missing_fields = []
    existing_fields = []
    for label, (input_key, _) in WHAT_IF_FIELDS.items():
        if input_key == "essays":
            is_missing = not any(clean_essay(text) for text in current_inputs.get("essays", []))
        else:
            # '미응답'을 명시적으로 고른 값(not_disclosed 등)은 선택한 것으로 보고,
            # 정말 '선택해주세요'로 남긴 None만 미선택 항목으로 분류합니다.
            is_missing = current_inputs.get(input_key) is None
        (missing_fields if is_missing else existing_fields).append(label)

    # 각 목록에서 선택한 항목의 입력창을 바로 그 목록 아래에 그리기 위한 공통 함수입니다.
    changes = {}

    def render_change_inputs(field_labels, key_prefix):
        for field_label in field_labels:
            input_key, option_map = WHAT_IF_FIELDS[field_label]
            st.markdown(f"**{field_label} 입력**" if key_prefix == "missing" else f"**{field_label} 변경**")

            if input_key == "essays":
                scenario = st.radio(
                    "자기소개 변경 방식",
                    ["첫 자기소개 작성 또는 보완", "자기소개 항목 한 칸 추가"],
                    key=f"whatif_scenario_{key_prefix}",
                    horizontal=True,
                )
                changed_value = st.text_area(
                    "변경 후 자기소개 내용",
                    height=110,
                    placeholder="변경하거나 새로 작성할 자기소개를 입력해주세요.",
                    key=f"whatif_essay_text_{key_prefix}",
                )
                changes[field_label] = {
                    "input_key": input_key, "value": changed_value, "scenario": scenario,
                }
            else:
                current_value = current_inputs.get(input_key)
                option_labels = list(option_map)
                current_label = next(
                    (label for label, value in option_map.items() if value == current_value),
                    option_labels[0],
                )
                changed_label = st.selectbox(
                    f"변경 후 {field_label}" if key_prefix == "existing" else f"새로 입력할 {field_label}",
                    option_labels,
                    index=option_labels.index(current_label),
                    key=f"whatif_value_{key_prefix}_{input_key}",
                )
                changes[field_label] = {
                    "input_key": input_key,
                    "value": option_map[changed_label],
                    "display_value": changed_label,
                }

    if missing_fields:
        st.markdown("##### 선택하지 않은 항목 채우기")
        st.caption("처음 분석할 때 선택하지 않은 항목이에요. 새로 입력할 항목을 골라주세요.")
        selected_missing = st.multiselect(
            "미선택 항목 (복수 선택 가능)",
            missing_fields,
            key="whatif_missing_fields",
            label_visibility="collapsed",
        )
        # 미선택 목록에서 고른 항목의 입력창은 이 영역 바로 아래에 표시합니다.
        render_change_inputs(selected_missing, "missing")
    else:
        st.caption("✓ 처음 분석할 때 선택하지 않은 프로필 항목이 없습니다.")
        selected_missing = []

    st.markdown("##### 기존 입력 항목 바꿔보기")
    st.caption("이미 입력한 정보 중 다른 값으로 시험해 볼 항목을 골라주세요.")
    selected_existing = st.multiselect(
        "기존 입력 항목 (복수 선택 가능)",
        existing_fields,
        key="whatif_existing_fields",
        label_visibility="collapsed",
    )
    # 기존 입력 목록에서 고른 항목의 입력창도 이 영역 바로 아래에 표시합니다.
    render_change_inputs(selected_existing, "existing")

    # 화면 배치는 분리하되, 계산할 때는 두 영역의 선택값을 합쳐 한 번에 재예측합니다.
    selected_fields = selected_missing + selected_existing

    if st.button("변경 후 위험도 계산", use_container_width=True, key="whatif_predict"):
        unfilled_missing = [
            field for field in selected_missing
            if changes[field]["input_key"] != "essays" and changes[field]["value"] is None
        ]
        if not selected_fields:
            st.warning("변경할 프로필 항목을 하나 이상 선택해주세요.")
        elif "자기소개" in changes and not changes["자기소개"]["value"].strip():
            st.warning("변경 후 자기소개 내용을 먼저 입력해주세요.")
        elif unfilled_missing:
            st.warning(f"새로 채울 항목의 값을 선택해주세요: {', '.join(unfilled_missing)}")
        else:
            scenario_inputs = copy.deepcopy(current_inputs)
            result_labels = []

            for field_label, change in changes.items():
                input_key = change["input_key"]
                if input_key == "essays":
                    scenario_essays = list(scenario_inputs.get("essays", []))
                    scenario_essays += [""] * (10 - len(scenario_essays))

                    if change["scenario"] == "첫 자기소개 작성 또는 보완":
                        scenario_essays[0] = change["value"]
                        result_labels.append("첫 자기소개 작성/보완")
                    else:
                        empty_index = next(
                            (i for i in range(1, 10) if not str(scenario_essays[i]).strip()),
                            None,
                        )
                        if empty_index is None:
                            st.warning("이미 자기소개 10칸을 모두 작성해 추가할 빈칸이 없어요.")
                            return
                        scenario_essays[empty_index] = change["value"]
                        result_labels.append(f"자기소개 {empty_index + 1}번째 칸 추가")
                    scenario_inputs["essays"] = scenario_essays
                else:
                    scenario_inputs[input_key] = change["value"]
                    result_labels.append(f"{field_label}: {change['display_value']}")

            scenario_prediction = predict_churn(scenario_inputs, model)
            st.session_state["service_whatif"] = {
                "base_risk": current_risk,
                "prediction": scenario_prediction,
                "label": " · ".join(result_labels),
            }
            st.session_state["service_scroll_result_top"] = True
            # dialog는 fragment이므로 이 팝업만 다시 그려 위쪽 결과 카드까지 즉시 교체합니다.
            st.rerun(scope="fragment")


def render_result_panel(
    essays,
    has_kids,
    status,
    clicked=False,
    prediction=None,
    current_inputs=None,
    model=None,
):
    """결과 칸 전체를 그린다. app.py 의 SERVICE 화면 오른쪽 칸에서 호출해요.

    clicked    : '이탈 위험 분석하기' 버튼을 눌렀는지
    prediction : 모델이 연결됐으면 predict.predict_churn() 의 반환값을, 아니면 None 을 넘겨 주세요.
    """
    info = analyze_inputs(essays, has_kids, status)
    if clicked and prediction is None:
        # 버튼을 눌렀는데 모델 파일을 못 찾은 경우, 무엇이 표시되는지 알려 줍니다.
        show(note_box("models 폴더에서 예측 모델(.cbm)을 찾지 못했어요. 아래는 분석 결과(EDA)에서 "
                      "나온 실제 이탈률로 만든 참고 신호예요."))
        show(_card_prediction(info, prediction))
        show(_card_signals(info, prediction))
        show(_card_strategies(info, prediction))

    # 모델 예측에 성공하면 오른쪽 칸에는 따로 결과를 그리지 않고,
    # 분석 결과와 재계산 기능을 모두 가운데 모달 하나에서 보여줍니다.
    if clicked and prediction is not None and current_inputs is not None and model is not None:
        _render_result_dialog(info, current_inputs, prediction, model)
