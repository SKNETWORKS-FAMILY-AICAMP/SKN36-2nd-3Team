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
import streamlit as st

import project_facts as facts
from ui_parts import action_card, note_box, page_header, section_title, show, signal_card, tag

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
        show(section_title("이런 사용자가 특히 위험해요",
                           "문서에 정리된 분석에서 이탈률 차이가 컸던 특징이에요. 위 전략을 어디에 집중할지 정할 때 참고하세요."))
        left, right = st.columns(2, gap="large")
        for i, s in enumerate(facts.KEY_SIGNALS):
            with (left if i % 2 == 0 else right):
                show(signal_card(s["title"], s["high_label"], s["high_rate"], s["low_label"], s["low_rate"]))


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
