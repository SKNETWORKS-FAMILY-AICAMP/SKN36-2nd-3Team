"""SERVICE 화면의 '결과 칸' 채우기 (service_view.py)

[이 파일이 하는 일]
SERVICE 화면 오른쪽 '결과 칸'을 카드 3장으로 채워 줍니다.
  1) 예측 결과       : 위험 단계 막대(Low / Medium / High) + '비슷하게 쓴 사용자의 실제 이탈률'
  2) 주요 신호       : 입력한 내용에서 이탈과 관련이 컸던 신호를 골라 보여줌
  3) 추천 리텐션 전략 : 위험 신호에 맞는 조치를 제안

[중요: 아직 '모델 예측'이 아니에요]
최종 모델이 연결되기 전이라 '위험 단계'는 비워 두고,
대신 팀 분석(EDA)에서 나온 실제 숫자로 '참고 신호'를 보여줍니다.
  예) 자기소개가 총 100자 이하 -> 이런 사용자의 실제 이탈률은 55.0%
모델이 연결되면 아래 render_result_panel() 안의 risk_level 만 채우면 위험 단계가 켜져요.

[숫자는 어디서 오나요?]
project_facts.py (팀 노트북 02_essay_deep_experiment 의 Train 데이터 EDA 결과)
"""
import re

import project_facts as facts
from page_retention import LEVELS
from ui_parts import esc, note_box, show

# ---------------------------------------------------------
# 1) 입력값 분석 (계산만 하는 부분. 화면 그리기와 분리해 두었어요)
# ---------------------------------------------------------
# 자기소개에서 '진짜 글이 아닌 것'(점 하나, 물음표 등)은 안 쓴 것으로 봅니다. (전처리 노트북과 같은 규칙)
_PLACEHOLDER = re.compile(r"(?i)[.\-?_/]+|na|n/a")
_LINK = re.compile(r"(?i)https?://|www\.")


def clean_essay(text):
    """HTML 태그를 지우고 공백을 정리한 자기소개 글. 진짜 글이 없으면 빈 글자를 돌려줌."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return "" if _PLACEHOLDER.fullmatch(text) or not text else text


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


def _rate_color(rate):
    """이탈률이 높을수록 빨강, 낮을수록 초록 (숫자 색)"""
    if rate >= 40:
        return "#c81e55"
    if rate >= 28:
        return "#9a5a08"
    if rate <= 20:
        return "#237a3f"
    return "#5a5a5a"


def _card_prediction(info, risk_level=None):
    """카드 1: 예측 결과. risk_level 은 나중에 모델이 채워 줄 값('low' / 'mid' / 'high')이에요."""
    segments = ""
    for key, label in (("low", "Low"), ("mid", "Medium"), ("high", "High")):
        # 위험 단계를 아직 모르면(모델 연결 전) 세 칸 모두 흐리게, 알면 해당 칸만 또렷하게
        dim = " dim" if risk_level != key else ""
        segments += f'<span class="risk-seg {key}{dim}">{label}</span>'
    note = ("모델이 연결되면 위험 단계가 여기에 표시돼요." if risk_level is None
            else "모델이 예측한 위험 단계예요.")

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

    return ('<div class="result-card"><span class="preview-ribbon">모델 연결 전</span>'
            '<div class="result-title">📊 예측 결과</div>'
            f'<div class="risk-scale">{segments}</div><div class="result-note">{note}</div>{ref}</div>')


def _card_signals(info):
    """카드 2: 주요 신호"""
    if info["signals"]:
        rows = ""
        for kind, title, stat in info["signals"]:
            icon = "⚠️" if kind == "warn" else "✅"
            rows += (f'<div class="sig-row {kind}"><div class="sig-icon">{icon}</div><div>'
                     f'<div class="sig-title">{esc(title)}</div><div class="sig-stat">{esc(stat)}</div></div></div>')
        body = rows
    else:
        checks = "".join(f'<span class="chip">{c}</span>' for c in
                         ("자기소개 분량", "자기소개 링크", "자녀 항목 응답", "관계 상태"))
        body = ('<div class="placeholder" style="margin-top:0">정보를 입력하면 이탈률 차이가 컸던 신호를 '
                f'여기에 골라서 보여줘요.</div><div style="margin-top:12px">{checks}</div>')
    return ('<div class="result-card"><div class="result-title">🔍 주요 신호</div>'
            '<div class="dash-sub" style="margin-top:-8px">지금은 분석 결과(EDA) 기준이에요. '
            '모델이 연결되면 SHAP 값으로 바뀌어요.</div>'
            f'{body}</div>')


def _card_strategies(info):
    """카드 3: 추천 리텐션 전략"""
    if info["strategies"]:
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
    return ('<div class="result-card"><div class="result-title">🎯 추천 리텐션 전략</div>'
            f'{body}</div>')


def render_result_panel(essays, has_kids, status, clicked=False, risk_level=None):
    """결과 칸 전체를 그린다. app.py 의 SERVICE 화면 오른쪽 칸에서 호출해요.

    clicked    : '이탈 위험 분석하기' 버튼을 눌렀는지
    risk_level : 모델이 연결되면 'low' / 'mid' / 'high' 를 넘겨 주세요. (지금은 None)
    """
    info = analyze_inputs(essays, has_kids, status)
    if clicked:
        # 버튼을 눌러도 아직 모델이 없어서, 무엇이 표시되는지 알려 줍니다.
        show(note_box("아직 예측 모델이 연결되지 않았어요. 아래는 분석 결과(EDA)에서 나온 실제 이탈률로 만든 참고 신호예요."))
    show(_card_prediction(info, risk_level))
    show(_card_signals(info))
    show(_card_strategies(info))
