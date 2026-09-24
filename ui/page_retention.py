"""RETENTION 화면 — 위험 수준별 리텐션 전략 (page_retention.py)

[리텐션(Retention)이란?]
사용자가 앱을 떠나지 않고 계속 쓰도록 '붙잡아 두는' 활동입니다.
(예: 한동안 안 들어온 사용자에게 재접속 알림 보내기)

[이 화면은 뭘 보여주나요?]
예측된 이탈 위험(High / Medium / Low)에 따라 운영자가 어떤 조치를 하면 좋을지 제안합니다.
  - High   : 곧 떠날 가능성이 커서 가장 먼저 붙잡아야 하는 사용자
  - Medium : 조금만 도와주면 계속 쓸 수 있는 사용자
  - Low    : 안정적으로 쓰는 사용자 -> 유료 전환·프로모션 대상

전략의 뼈대는 노션 '프로젝트 기획서'의 활용 예시이고, 각 카드의 설명 문장은
읽기 쉽게 풀어 쓴 '제안'입니다. (실제로 효과가 있는지는 운영 데이터로 확인이 필요해요.)

app.py 에서 render() 를 호출하면 이 화면이 그려져요.
"""
import re

import streamlit as st

import db
import project_facts as facts
from insight_data import STATUS_LABELS
from ui_parts import (action_card, check_list_card, kpi_card, note_box, page_header, placeholder_card,
                      rate_bars_card, section_title, show, signal_card, table_card, tag)

def _reason_base_name(reason_text):
    """'자기소개 작성 칸 수 (위험↑)' -> '자기소개 작성 칸 수' (괄호 뒤 화살표 표시를 뗀다)"""
    if not reason_text:
        return None
    return re.sub(r"\s*\([^)]*\)\s*$", "", reason_text).strip()


def _strategy_for_reason(reason_text):
    """위험 신호(reason_1) -> 어울리는 리텐션 전략 이름. 매칭이 없으면 기본 전략을 돌려준다."""
    base = _reason_base_name(reason_text)
    return facts.REASON_TO_STRATEGY.get(base, facts.REASON_TO_STRATEGY_DEFAULT)


# 화면 선택창에 쓸 옵션들. "전체"를 고르면 그 조건은 걸지 않아요(db.query_segment 에 None 으로 전달).
_RISK_OPTIONS = {"전체": None, "High": "High", "Medium": "Medium", "Low": "Low"}
# 완성도 구간: {"전체": None, "하위 33%": 1, "중간 33%": 2, "상위 33%": 3}
_COMPLETENESS_OPTIONS = {"전체": None, **{label: i + 1 for i, label in enumerate(facts.SEGMENT_COMPLETENESS_LABELS)}}
# 자기소개 구간: {"전체": (None, None), "0개": (0, 0), "1~3개": (1, 3), ...}
_ESSAY_OPTIONS = {"전체": (None, None)}
for _label, _lo, _hi in zip(facts.SEGMENT_ESSAY_LABELS, facts.SEGMENT_ESSAY_BINS[:-1], facts.SEGMENT_ESSAY_BINS[1:]):
    _ESSAY_OPTIONS[_label] = (_lo + 1, _hi)
# 나이대: {"전체": (None, None), "18~24세": (18, 24), ...}
_AGE_OPTIONS = {"전체": (None, None)}
for _label, _lo, _hi in zip(facts.SEGMENT_AGE_LABELS, facts.SEGMENT_AGE_BINS[:-1], facts.SEGMENT_AGE_BINS[1:]):
    _AGE_OPTIONS[_label] = (_lo + 1, _hi)
# 관계 상태: insight_data.STATUS_LABELS(원본값 -> 한글)을 뒤집어서 재사용 (화면 기준을 하나로 맞춤)
_STATUS_OPTIONS = {"전체": None, **{kr: raw for raw, kr in STATUS_LABELS.items()}}


def _sql_targeting_section(risk_tier, risk_label, key_suffix):
    """현재 위험 탭(High / Medium / Low)에 해당하는 사용자만 predictions 테이블에서 조회한다.

    탭 자체가 위험 등급 필터 역할을 하므로, 사용자가 별도의 위험 등급 선택창을 다시 고를 필요가 없어요.
    나머지 조건(완성도/자기소개/관계 상태/연령대)만 추가로 좁힐 수 있습니다.
    """
    show(section_title(
        f"{risk_label} 대상자 찾기",
        f"현재 탭의 {risk_label} 사용자만 조회해요. 아래 조건을 추가하면 같은 위험 등급 안에서 더 세분화할 수 있습니다."
    ))

    if not db.is_connected():
        show(placeholder_card("대상자 조회", db.NOT_CONNECTED_HINT))
        return

    # 위험 등급은 현재 탭으로 고정. 나머지 4개 조건만 선택합니다.
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        comp_kr = st.selectbox(
            "프로필 완성도", list(_COMPLETENESS_OPTIONS),
            key=f"seg_comp_{key_suffix}"
        )
    with c2:
        essay_kr = st.selectbox(
            "자기소개 작성 수준", list(_ESSAY_OPTIONS),
            key=f"seg_essay_{key_suffix}"
        )
    with c3:
        status_kr = st.selectbox(
            "관계 상태", list(_STATUS_OPTIONS),
            key=f"seg_status_{key_suffix}"
        )
    with c4:
        age_kr = st.selectbox(
            "연령대", list(_AGE_OPTIONS),
            key=f"seg_age_{key_suffix}"
        )

    essay_min, essay_max = _ESSAY_OPTIONS[essay_kr]
    age_min, age_max = _AGE_OPTIONS[age_kr]

    result = db.query_segment(
        risk_tier=risk_tier,
        completeness_tier=_COMPLETENESS_OPTIONS[comp_kr],
        essay_min=essay_min,
        essay_max=essay_max,
        status=_STATUS_OPTIONS[status_kr],
        age_min=age_min,
        age_max=age_max,
        limit=facts.SEGMENT_LIST_LIMIT,
    )

    if result is None:
        show(placeholder_card(
            "대상자 조회",
            "DB에는 연결됐지만 조회에 실패했어요. predictions 테이블이 있는지, 컨테이너를 최신으로 띄웠는지 확인해 주세요."
        ))
        return

    if result["n"] == 0:
        show(placeholder_card(
            "대상자 조회",
            f"현재 조건에 맞는 {risk_label} 사용자가 없어요. 조건을 조금 넓혀서 다시 찾아보세요."
        ))
        return

    # 결과 요약 카드 3개 — 모두 '현재 탭의 위험 등급' 기준
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        show(kpi_card(
            f"{risk_label} 대상자 수",
            f"{result['n']:,}명",
            "현재 탭 + 아래 필터 조건을 모두 만족한 사용자"
        ))
    with k2:
        show(kpi_card(
            f"{risk_label} 평균 이탈 확률",
            f"{result['avg_prob'] * 100:.1f}%",
            "현재 조회된 사용자들의 모델 예측 확률 평균"
        ))
    with k3:
        tier_share = result.get("tier_share")
        tier_share_text = f"{tier_share * 100:.1f}%" if tier_share is not None else "-"
        show(kpi_card(
            f"{risk_label} 등급 비율",
            tier_share_text,
            "같은 추가 조건 사용자 중 현재 위험 등급이 차지하는 비율"
        ))

    # 주요 위험 신호: '현재 위험 등급 집단 안에서' reason_1 비율
    if result["reasons"]:
        rows = [
            {
                "label": _reason_base_name(name) or "(기록 없음)",
                "rate": n / result["n"] * 100,
                "n": n,
            }
            for name, n in result["reasons"]
        ]
        show(rate_bars_card(
            f"{risk_label} 집단의 주요 이탈 신호",
            "막대 길이 = 이 집단에서 해당 신호가 1순위 위험 요인이었던 사용자 비율입니다.",
            rows,
            footer="여기서는 막대 길이와 사람 수가 같은 기준입니다: 비율 = 해당 신호 인원 ÷ 현재 조회 인원."
        ))

    # 우선 관리 대상 명단 — 현재 위험 등급 안에서 확률 높은 순
    table_rows = [
        (
            f"#{uid}",
            tier,
            f"{prob * 100:.1f}%",
            _reason_base_name(reason) or "-",
            _strategy_for_reason(reason),
        )
        for uid, tier, prob, reason in result["rows"]
    ]
    show(table_card(
        f"{risk_label} 우선 관리 대상 (이탈 확률 높은 순 {len(table_rows)}명)",
        f"현재 조건의 {risk_label} 사용자 {result['n']:,}명 중 이탈 확률이 가장 높은 사용자예요.",
        ["익명 프로필 ID", "위험 등급", "이탈 확률", "주요 위험 신호", "추천 전략"],
        table_rows,
    ))
    show(note_box(facts.SEGMENT_LIST_DISCLAIMER))


def _ab_test_section():
    """맨 아래: 실제 서비스 도입 후 전략 효과를 검증할 A/B 테스트 계획."""
    show(section_title(
        "전략 효과 A/B 테스트 계획",
        "SERVICE의 What-if는 모델 예측의 변화를 보여주고, 실제 전략 효과는 운영 데이터로 별도 검증합니다.",
    ))
    show(check_list_card(
        "실제 서비스 도입 후 검증 절차",
        "임의의 효과 수치를 만들지 않고 실제 행동 로그가 쌓인 뒤 아래 순서로 비교합니다.",
        [
            ("1. 대상 선정", "SQL로 동일한 조건의 위험군을 선정합니다. 예: High 위험군 중 자기소개 미작성 사용자"),
            ("2. 무작위 배정", "대상자를 처리군과 대조군에 무작위로 나누고 두 집단의 시작 위험도가 비슷한지 확인합니다."),
            ("3. 전략 적용", "처리군에만 프로필 작성 가이드·젤리 보상 등의 전략을 적용하고 대조군은 기존 서비스를 유지합니다."),
            ("4. 실제 결과 비교", "프로필 수정률, 7일 재방문율, 30일 이탈률을 실제 로그로 비교합니다."),
        ],
    ))
    show(note_box(
        "현재 OkCupid 데이터에는 캠페인 노출과 개입 이후 행동 로그가 없어 실제 A/B 효과값을 계산할 수 없습니다. "
        "따라서 이 화면은 결과를 만들어 내는 시뮬레이션이 아니라, 실제 서비스에서 사용할 검증 구조를 설명합니다."
    ))

# ---------------------------------------------------------
# 위험 수준별 내용. 전략을 바꾸고 싶으면 아래 글만 고치면 됩니다.
#   actions = [(아이콘, 전략 이름, 설명), ...]
# ---------------------------------------------------------
LEVELS = [
    {
        "tab": "🔴 High Risk",
        "kind": "high",
        "name": "High Risk",
        "headline": "가장 먼저 붙잡아야 할 사용자",
        "goal": "이탈 가능성이 높은 사용자예요. 프로필을 채우게 하고 다시 접속할 이유를 만들어 주는 것이 목표입니다.",
        "actions": [
            ("✍️", "프로필 작성 유도",
             "자기소개와 비어 있는 항목을 채우도록 가입 직후부터 안내해요."),
            ("🎁", "프로필 완성 리워드",
             "프로필을 끝까지 채우면 혜택을 줘서 완성까지 이어지게 해요."),
            ("🔔", "재접속 알림",
             "한동안 접속이 없으면 알림으로 다시 불러와요."),
            ("💞", "관심사 기반 추천 강화",
             "프로필의 관심사가 비슷한 상대를 먼저 보여줘요. (도입 여부는 검토가 필요해요)"),
            ("❤️", "무료 Like · 리텐션 혜택",
             "다시 돌아오면 무료 Like 같은 혜택을 줘서 복귀를 도와요."),
        ],
        "show_signals": True,      # High 탭에서는 '이런 사용자가 High 로 잘 나와요' 근거를 함께 보여줌
    },
    {
        "tab": "🟠 Medium Risk",
        "kind": "mid",
        "name": "Medium Risk",
        "headline": "조금만 도와주면 계속 쓸 사용자",
        "goal": "당장 떠날 정도는 아니지만 흥미를 잃기 쉬운 사용자예요. 앱을 열어 볼 이유를 만들어 주는 것이 목표입니다.",
        "actions": [
            ("🆕", "신규 상대 추천",
             "새로 가입한 사용자를 추천해서 앱을 열 이유를 만들어요."),
            ("➕", "관심사 추가 입력 유도",
             "관심사를 더 적게 하면 추천이 정확해진다고 안내해요."),
            ("📝", "프로필 개선 가이드",
             "비어 있거나 짧은 항목을 알려 주고 작성 예시를 보여줘요."),
        ],
        "show_signals": False,
    },
    {
        "tab": "🟢 Low Risk",
        "kind": "low",
        "name": "Low Risk",
        "headline": "안정적으로 이용 중인 사용자",
        "goal": "이탈 위험이 낮은 사용자예요. 이 사용자들에게는 붙잡기보다 서비스 가치를 높이는 방향으로 접근합니다.",
        "actions": [
            ("⭐", "프리미엄 기능 안내",
             "유료 기능의 장점을 알려 줘요."),
            ("👑", "VIP 구독 전환 후보",
             "충성도가 높아 구독 전환 가능성이 큰 사용자로 분류해요."),
            ("📣", "광고 · 프로모션 노출 정책 활용",
             "이탈 위험이 낮은 사용자를 기준으로 프로모션 노출 빈도를 조절해요."),
        ],
        "show_signals": False,
    },
]


def _render_level(level):
    """위험 수준 하나(탭 하나)의 내용을 그린다."""
    # 위쪽: 위험 수준 표시(알약) + 한 줄 요약 + 목표
    show(f'<div class="level-head">{tag(level["name"], level["kind"])}'
         f'<span class="level-headline">{level["headline"]}</span></div>'
         f'<div class="level-goal">{level["goal"]}</div>')

    # 추천 전략 카드들
    show(section_title("추천 전략"))
    for icon, title, text in level["actions"]:
        show(action_card(icon, title, text))

    # High 탭에서만: 어떤 사용자가 위험한지 데이터 근거
    if level["show_signals"]:
        show(section_title(
            "이런 사용자가 특히 위험해요",
            "막대 길이와 색은 '사람 수'가 아니라 각 그룹의 이탈률을 뜻해요. 사람 수가 적어도 이탈률이 높으면 진하고 길게 보일 수 있습니다."
        ))
        left, right = st.columns(2, gap="large")
        for i, s in enumerate(facts.KEY_SIGNALS):
            with (left if i % 2 == 0 else right):
                show(signal_card(s["title"], s["high_label"], s["high_rate"], s["low_label"], s["low_rate"]))

    # 현재 탭의 위험 등급으로 SQL 대상자 조회를 고정합니다.
    _sql_targeting_section(
        risk_tier=level["name"].split()[0],
        risk_label=level["name"],
        key_suffix=level["kind"],
    )


def render():
    # 화면 제목
    show(page_header("RETENTION STRATEGY", "위험 수준별 리텐션 전략",
                     "예측된 이탈 위험에 따라 운영자가 취할 수 있는 조치를 제안합니다."))

    show(note_box("위험 수준(Low / Medium / High)을 나누는 확률 기준은 최종 모델의 결과를 확인한 뒤에 정해요. "
                  "SERVICE 화면에서 예측한 위험 수준에 맞는 탭을 골라서 보세요."))

    # st.tabs : 탭(상단 메뉴)으로 내용을 나눠서 보여줍니다. 탭마다 with 블록 안의 내용이 들어가요.
    tabs = st.tabs([level["tab"] for level in LEVELS])
    for tab, level in zip(tabs, LEVELS):
        with tab:
            _render_level(level)

    # 운영할 때 주의할 점
    show(note_box("예측 신호는 이탈의 '원인'이 아니라 함께 나타나는 '경향'이에요. "
                  "그래서 전략은 일부 사용자에게 먼저 시험(A/B 테스트)해서 효과를 확인한 뒤 넓혀 가는 것을 권장해요."))

    # 실제 서비스 도입 후 A/B 테스트 검증 계획
    _ab_test_section()
