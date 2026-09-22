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
"""HOME 화면 — 서비스 소개 첫 화면 (page_home.py)"""

import base64
from pathlib import Path

import streamlit as st

import project_facts as facts
from ui_parts import check_list_card, flow_row, show, stat_band


def _preview_card():
    """예시 결과 카드"""
    signals = ["프로필 완성도 낮음", "자기소개 100자 이하", "자녀 항목 무응답"]
    strategies = ["프로필 작성 유도", "재접속 알림"]

    chips = "".join(f'<span class="chip">{signal}</span>' for signal in signals)
    plans = "".join(f'<span class="chip chip-pink">{strategy}</span>' for strategy in strategies)

    return (
        '<div class="preview-card"><span class="preview-ribbon">예시 화면</span>'
        '<div class="preview-title">📊 예측 결과</div>'
        '<div class="preview-risk"><span class="tag tag-high">High Risk</span>'
        '<span class="preview-risk-text">이탈 위험이 높은 사용자예요</span></div>'
        f'<div class="preview-label">주요 예측 신호</div><div>{chips}</div>'
        f'<div class="preview-label">추천 리텐션 전략</div><div>{plans}</div>'
        '<div class="dash-foot">모양을 보여주기 위한 예시이며, 실제 예측값이 아니에요.</div></div>'
    )


def _hero_image_base64():
    """Hero 이미지를 base64 문자열로 바꿉니다."""
    image_path = Path(__file__).parent / "assets" / "staymatch_hero.png"

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def render(on_start):
    hero_image = _hero_image_base64()

    st.markdown(
        f"""
<style>
.hero-wrap {{
    width: 100vw !important;
    max-width: 100vw !important;
    height: calc(100vh - 56px);
    min-height: 680px;
    margin-left: calc(50% - 50vw) !important;
    box-sizing: border-box;

    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;

    background-image:
        linear-gradient(
            90deg,
            rgba(20, 10, 16, 0.68) 0%,
            rgba(20, 10, 16, 0.32) 48%,
            rgba(20, 10, 16, 0.06) 78%
        ),
        url("data:image/png;base64,{hero_image}");

    background-size: cover;
    background-position: 68% center;
    background-attachment: fixed;
}}

.hero-content {{
    width: 100%;
    text-align: center;
}}

.hero-title {{
    color: #ffffff;
    font-size: clamp(72px, 8vw, 140px);
    font-weight: 800;
    line-height: 1.02;
    letter-spacing: -0.075em;
    text-shadow: 0 5px 24px rgba(0, 0, 0, 0.22);

    opacity: 0;
    transform: translateY(70px);
    animation: title-rise 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.2s forwards;
}}

@keyframes title-rise {{
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.hero-highlight {{
    color: #ffb6d2;
}}

@media (max-width: 768px) {{
    .hero-wrap {{
        min-height: 620px;
        background-position: 64% center;
        background-attachment: scroll;
    }}

    .hero-title {{
        font-size: 58px;
    }}
}}
</style>
<div class="hero-wrap"><div class="hero-content"><div class="hero-title">Come back<br><span class="hero-highlight">to me.</span></div></div></div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<style>
.catch-story {
    min-height: 72vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 24px;
    text-align: center;
    box-sizing: border-box;
}

.catch-story-title {
    color: #171217;
    font-size: clamp(52px, 6.5vw, 104px);
    font-weight: 800;
    line-height: 1.03;
    letter-spacing: -0.075em;
}

.catch-story-desc {
    margin-top: 28px;
    color: #5f535a;
    font-size: clamp(17px, 1.45vw, 24px);
    font-weight: 600;
    line-height: 1.6;
}

@media (max-width: 768px) {
    .catch-story {
        min-height: 55vh;
        padding: 60px 20px;
    }

    .catch-story-title {
        font-size: 52px;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    show(
        '<div class="catch-story">'
        '<div class="catch-story-title">BEFORE THEY GO,<br>THERE&apos;S A SIGN.</div>'
        '<div class="catch-story-desc">떠나기 전에는,<br>늘 놓치기 쉬운 신호가 있습니다.</div>'
        '</div>'
    )

    # 숫자로 보는 Catch
    recall_pct = round(facts.MODEL_METRICS["Recall"] * 100)

    show(
        stat_band(
            [
                (f"{facts.TOTAL_USERS:,}명", "분석한 사용자"),
                (f"{facts.CHURN_RATE:.1f}%", f"{facts.CHURN_DAYS}일 이상 미접속(이탈)한 비율"),
                (f"{facts.FEATURE_COUNT}개", "예측에 쓴 프로필 항목"),
                (f"약 {recall_pct}%", "실제 이탈자를 찾아낸 비율"),
            ]
        )
    )

    # 기능 소개
    st.markdown(
        """
<div class="section-label">WHAT WE DO</div>
<div class="section-title">Catch가 제공하는 기능</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
<div class="feature-card">
    <div class="feature-icon">🔍</div>
    <div class="feature-title">이탈 위험 조기 탐지</div>
    <div class="feature-text">
        행동 로그가 충분히 쌓이지 않은 사용자도
        프로필 정보를 기반으로 장기 미접속
        가능성을 예측합니다.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
<div class="feature-card">
    <div class="feature-icon">📊</div>
    <div class="feature-title">사용자 특성 분석</div>
    <div class="feature-text">
        프로필 완성도와 자기소개 작성량 등
        장기 미접속과 관련된 주요 예측 신호를
        확인할 수 있습니다.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
<div class="feature-card">
    <div class="feature-icon">🎯</div>
    <div class="feature-title">리텐션 전략 지원</div>
    <div class="feature-text">
        사용자 위험도를 기반으로
        프로필 완성 유도, 재접속 알림 등
        운영 전략 수립을 지원합니다.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # 이용 흐름
    show(
        '<div class="section-label">HOW IT WORKS</div>'
        '<div class="section-title">이렇게 사용해요</div>'
    )

    show(
        flow_row(
            [
                ("", "프로필 입력", "나이, 직업, 자기소개 같은 사용자 프로필 정보를 입력해요.", ""),
                ("", "이탈 위험 예측", "장기 미접속 확률을 계산해서 Low / Medium / High 로 알려줘요.", ""),
                ("", "리텐션 전략 확인", "위험 수준에 맞는 유지 전략을 바로 확인해요.", ""),
            ],
            numbered=True,
        )
    )

    # 결과 미리보기
    show(
        '<div class="section-label">PREVIEW</div>'
        '<div class="section-title">이런 결과를 받아볼 수 있어요</div>'
    )

    left, right = st.columns(2, gap="large")

    with left:
        show(
            check_list_card(
                "결과 화면에는 이런 내용이 담겨요",
                "예측 한 번으로 세 가지를 알 수 있어요.",
                [
                    ("위험 등급", "Low / Medium / High 로 한눈에 확인해요."),
                    ("주요 예측 신호", "어떤 프로필 특징이 위험도에 영향을 줬는지 알려줘요."),
                    ("추천 리텐션 전략", "위험 수준에 맞는 조치를 바로 제안해요."),
                ],
            )
        )

    with right:
        show(_preview_card())

    # 마지막 CTA
    show(
        '<div class="cta-band">'
        '<div class="cta-title">지금 바로 이탈 위험을 분석해 보세요</div>'
        '<div class="cta-text">프로필 정보만 입력하면 위험 수준과 추천 전략을 확인할 수 있어요.</div>'
        '</div>'
    )

    _, mid, _ = st.columns([2, 1, 2])

    with mid:
        st.button(
            "분석 시작하기  →",
            key="home_cta_bottom",
            use_container_width=True,
            on_click=on_start,
        )