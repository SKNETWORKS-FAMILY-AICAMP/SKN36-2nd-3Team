"""HOME 화면 — 서비스 소개 첫 화면 (page_home.py)

[이 화면은 뭘 보여주나요?]
서비스를 처음 보는 사람이 "이게 뭐고, 어떻게 쓰고, 어떤 결과가 나오는지" 이해하도록 안내하는 화면입니다.
  1) 큰 제목(Hero)과 시작 버튼
  2) 숫자로 보는 StayMatch (사용자 수, 이탈률, 사용 항목, 이탈자 탐지 비율)
  3) 제공하는 기능 3가지
  4) 이용 흐름 3단계
  5) 결과 화면 미리보기 (예시)
  6) 마무리 시작 버튼

[on_start 는 뭔가요?]
"시작하기" 버튼을 눌렀을 때 실행할 함수입니다. 메뉴를 SERVICE 로 바꾸는 일은 app.py 가 하기 때문에,
app.py 가 그 함수를 여기로 넘겨줘요.   render_home(on_start=go_to_service)

app.py 에서 render() 를 호출하면 이 화면이 그려져요.
"""
import streamlit as st

import project_facts as facts
from ui_parts import check_list_card, flow_row, show, stat_band


def _preview_card():
    """'예시 결과 화면' 카드. 실제 예측값이 아니라 어떤 모양으로 나오는지 보여주는 그림이에요."""
    # 예측 신호는 project_facts.KEY_SIGNALS 에서 이탈률 차이가 컸던 항목들입니다.
    signals = ["프로필 완성도 낮음", "자기소개 100자 이하", "자녀 항목 무응답"]
    strategies = ["프로필 작성 유도", "재접속 알림"]
    chips = "".join(f'<span class="chip">{s}</span>' for s in signals)
    plans = "".join(f'<span class="chip chip-pink">{s}</span>' for s in strategies)
    return (
        '<div class="preview-card"><span class="preview-ribbon">예시 화면</span>'
        '<div class="preview-title">📊 예측 결과</div>'
        '<div class="preview-risk"><span class="tag tag-high">High Risk</span>'
        '<span class="preview-risk-text">이탈 위험이 높은 사용자예요</span></div>'
        f'<div class="preview-label">주요 예측 신호</div><div>{chips}</div>'
        f'<div class="preview-label">추천 리텐션 전략</div><div>{plans}</div>'
        '<div class="dash-foot">모양을 보여주기 위한 예시이며, 실제 예측값이 아니에요.</div></div>'
    )


def render(on_start):

    # 맨 위 큰 소개 문구(Hero). HTML 로 꾸민 글이고,
    # class="..." 이름표에 해당하는 디자인은 styles.py 에 있어요.
    st.markdown(
        """
<div class="hero-wrap">

<div class="hero-badge">
DATING RETENTION INTELLIGENCE
</div>

<div class="hero-title">
    Predict Churn.<br>
    <span class="hero-highlight">Keep Connections.</span>
</div>

<div class="hero-description">
데이팅 플랫폼 운영사를 위한<br>
사용자 이탈 예측 및 리텐션 지원 서비스
</div>

<div class="hero-sub">
프로필 정보를 기반으로 장기 미접속 위험을 조기에 탐지합니다.
</div>

</div>
""",
        unsafe_allow_html=True
    )

    # CTA 버튼 (CTA = Call To Action, 사용자가 다음 행동을 하도록 유도하는 버튼)
    # 화면을 2 : 1 : 2 로 나눠 '가운데 칸'에만 버튼을 넣으면 버튼이 화면 가운데에 옵니다.
    btn_left, btn_center, btn_right = st.columns([2, 1, 2])

    with btn_center:
        st.button(
            "이탈 위험 분석하기  →",
            use_container_width=True,
            on_click=on_start   # 버튼이 눌리면 위에서 만든 go_to_service 함수를 실행
        )

    # 숫자로 보는 StayMatch: 서비스의 규모와 성능을 한 줄로 보여줍니다.
    # 숫자는 project_facts.py 에서 가져와요. (직접 쓰면 나중에 숫자가 어긋날 수 있어서)
    recall_pct = round(facts.MODEL_METRICS["Recall"] * 100)
    show(stat_band([
        (f"{facts.TOTAL_USERS:,}명", "분석한 사용자"),
        (f"{facts.CHURN_RATE:.1f}%", f"{facts.CHURN_DAYS}일 이상 미접속(이탈)한 비율"),
        (f"{facts.FEATURE_COUNT}개", "예측에 쓴 프로필 항목"),
        (f"약 {recall_pct}%", "실제 이탈자를 찾아낸 비율"),
    ]))

    # 기능 소개 제목 ("WHAT WE DO" + "StayMatch가 제공하는 기능")
    st.markdown(
        """
        <div class="section-label">
            WHAT WE DO
        </div>

        <div class="section-title">
            StayMatch가 제공하는 기능
        </div>
        """,
        unsafe_allow_html=True
    )

    # 같은 너비의 칸 3개. 아래 카드 3개(이탈 조기 탐지 / 사용자 특성 분석 / 리텐션 전략)를 나란히 놓습니다.
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
<div class="feature-card">

<div class="feature-icon">
🔍
</div>

<div class="feature-title">
이탈 위험 조기 탐지
</div>

<div class="feature-text">
행동 로그가 충분히 쌓이지 않은 사용자도
프로필 정보를 기반으로 장기 미접속
가능성을 예측합니다.
</div>

</div>
""",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
<div class="feature-card">

<div class="feature-icon">
📊
</div>

<div class="feature-title">
사용자 특성 분석
</div>

<div class="feature-text">
프로필 완성도와 자기소개 작성량 등
장기 미접속과 관련된 주요 예측 신호를
확인할 수 있습니다.
</div>

</div>
""",
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
<div class="feature-card">

<div class="feature-icon">
🎯
</div>

<div class="feature-title">
리텐션 전략 지원
</div>

<div class="feature-text">
사용자 위험도를 기반으로
프로필 완성 유도, 재접속 알림 등
운영 전략 수립을 지원합니다.
</div>

</div>
""",
            unsafe_allow_html=True
        )

    # ── 이용 흐름: 서비스를 어떻게 쓰는지 3단계로 ────────────────
    # 순서가 있는 내용이라 번호(1, 2, 3)와 화살표로 이어서 보여줍니다.
    show('<div class="section-label">HOW IT WORKS</div>'
         '<div class="section-title">이렇게 사용해요</div>')
    show(flow_row([
        ("", "프로필 입력", "나이, 직업, 자기소개 같은 사용자 프로필 정보를 입력해요.", ""),
        ("", "이탈 위험 예측", "장기 미접속 확률을 계산해서 Low / Medium / High 로 알려줘요.", ""),
        ("", "리텐션 전략 확인", "위험 수준에 맞는 유지 전략을 바로 확인해요.", ""),
    ], numbered=True))

    # ── 결과 미리보기: 서비스를 쓰면 어떤 화면을 받는지 ───────────
    show('<div class="section-label">PREVIEW</div>'
         '<div class="section-title">이런 결과를 받아볼 수 있어요</div>')
    left, right = st.columns(2, gap="large")
    with left:
        show(check_list_card("결과 화면에는 이런 내용이 담겨요", "예측 한 번으로 세 가지를 알 수 있어요.", [
            ("위험 등급", "Low / Medium / High 로 한눈에 확인해요."),
            ("주요 예측 신호", "어떤 프로필 특징이 위험도에 영향을 줬는지 알려줘요."),
            ("추천 리텐션 전략", "위험 수준에 맞는 조치를 바로 제안해요."),
        ]))
    with right:
        show(_preview_card())

    # ── 마무리: 한 번 더 시작 버튼 ─────────────────────────────
    show('<div class="cta-band"><div class="cta-title">지금 바로 이탈 위험을 분석해 보세요</div>'
         '<div class="cta-text">프로필 정보만 입력하면 위험 수준과 추천 전략을 확인할 수 있어요.</div></div>')
    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        # key 는 위쪽 버튼과 이름이 겹치지 않게 구분하는 이름표예요. (같은 위젯이 두 개면 에러가 나요)
        st.button("분석 시작하기  →", key="home_cta_bottom", use_container_width=True, on_click=on_start)
