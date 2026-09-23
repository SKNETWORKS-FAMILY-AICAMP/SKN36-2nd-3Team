"""HOME 화면 — 서비스 소개 첫 화면 (page_home.py)

[이 화면은 뭘 보여주나요?]
서비스를 처음 보는 사람이 "이게 뭐고, 어떻게 쓰고, 어떤 결과가 나오는지" 이해하도록 안내하는 화면입니다.
  1) 큰 제목(Hero)과 시작 버튼
  2) 숫자로 보는 Catch (사용자 수, 이탈률, 사용 항목, 이탈자 탐지 비율)
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
from avatars import single_face


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

def _signal_phone():
    """아바타를 이용한 Catch의 '이탈 신호 감지' 예시 화면"""
    center = single_face("f", 27, size=118, idx=0, bg="#ffe4ec")
    face_1 = single_face("m", 29, size=66, idx=1, bg="#e6f0ff")
    face_2 = single_face("f", 25, size=62, idx=2, bg="#fff0d9")
    face_3 = single_face("m", 32, size=60, idx=3, bg="#e8f7ec")

    return (
        '<div class="catch-phone">'
        '<div class="phone-notch"></div>'
        '<div class="phone-label">CATCH SIGNAL</div>'
        '<div class="phone-copy">떠나기 전,<br>이탈 신호를 감지합니다.</div>'
        '<div class="orbit-area">'
        '<div class="orbit-motion">'
        '<div class="orbit orbit-1"></div>'
        '<div class="orbit orbit-2"></div>'
        '<div class="orbit orbit-3"></div>'
        f'<div class="orbit-center">{center}</div>'
        f'<div class="orbit-face face-1">{face_1}</div>'
        f'<div class="orbit-face face-2">{face_2}</div>'
        f'<div class="orbit-face face-3">{face_3}</div>'
        '<span class="signal-dot dot-1"></span>'
        '<span class="signal-dot dot-2"></span>'
        '<span class="signal-dot dot-3"></span>'
        '</div>'
        f'<div class="orbit-center">{center}</div>'
        '</div>'
        '<div class="phone-footer">Risk signals detected</div>'
        '</div>'
    )


def _hero_image_base64():
    """Hero 이미지를 base64 문자열로 바꿉니다."""
    image_path = Path(__file__).parent / "assets" / "catch_hero.png"

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

    # ── 이탈 신호 소개 + Catch 아바타 화면 ─────────────────────
    recall_pct = round(facts.MODEL_METRICS["Recall"] * 100)

    st.markdown(
        """
<style>
.catch-story {
    min-height: 100vh;
    padding: 105px 7vw 90px;
    box-sizing: border-box;
    text-align: center;
}

.catch-story-title {
    color: #171217;
    font-size: clamp(48px, 5.8vw, 94px);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.075em;
}

.catch-story-sub {
    margin-top: 24px;
    color: #655860;
    font-size: clamp(17px, 1.35vw, 22px);
    font-weight: 600;
    line-height: 1.6;
}

.catch-story-layout {
    max-width: 1220px;
    margin: 70px auto 0;
    display: grid;
    grid-template-columns: 1fr 360px 1fr;
    align-items: center;
    gap: 72px;
    text-align: left;
}

.catch-stat {
    padding: 28px 0;
    border-top: 1px solid #eadde2;
}

.catch-number {
    color: #171217;
    font-size: clamp(35px, 3vw, 54px);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.06em;
}

.catch-number em {
    color: #ff4f87;
    font-style: normal;
}

.catch-label {
    margin-top: 10px;
    color: #655860;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.5;
}

.catch-phone {
    position: relative;
    width: 330px;
    height: 570px;
    margin: 0 auto;
    padding: 48px 24px 20px;
    box-sizing: border-box;
    overflow: hidden;
    border: 8px solid #1d1b1d;
    border-radius: 43px;
    background: #fffafb;
    box-shadow: 0 24px 50px rgba(52, 22, 34, 0.20);
}

.phone-notch {
    position: absolute;
    top: 13px;
    left: 50%;
    width: 108px;
    height: 22px;
    transform: translateX(-50%);
    border-radius: 99px;
    background: #1d1b1d;
}

.phone-label {
    color: #ff4f87;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.12em;
}

.phone-copy {
    margin-top: 10px;
    color: #171217;
    font-size: 22px;
    font-weight: 800;
    line-height: 1.28;
    letter-spacing: -0.05em;
}

.orbit-area {
    position: relative;
    width: 275px;
    height: 275px;
    margin: 35px auto 0;
}

.orbit-motion {
    position: absolute;
    inset: 0;
    animation: orbit-spin 14s linear infinite;
    transform-origin: center;
}

.orbit-motion .orbit-face img {
    display: block;
    animation: face-keep-upright 14s linear infinite reverse;
}

@keyframes orbit-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes face-keep-upright {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* 캐릭터와 점을 처음에 숨김 */
.orbit-face,
.signal-dot {
    opacity: 0;
}

/* 1번 캐릭터 + 점 */
.face-1,
.dot-1 {
    animation: signal-rise 0.95s cubic-bezier(0.22, 1, 0.36, 1) 0.10s both;
}

/* 2번 캐릭터 + 점 */
.face-2,
.dot-2 {
    animation: signal-rise 0.95s cubic-bezier(0.22, 1, 0.36, 1) 0.55s both;
}

/* 3번 캐릭터 + 점 */
.face-3,
.dot-3 {
    animation: signal-rise 0.95s cubic-bezier(0.22, 1, 0.36, 1) 1.00s both;
}

@keyframes signal-rise {
    from {
        opacity: 0;
        transform: translateY(34px) scale(0.82);
    }

    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.orbit {
    position: absolute;
    top: 50%;
    left: 50%;
    border: 1px dashed #e4cfd8;
    border-radius: 50%;
    transform: translate(-50%, -50%);
}

.orbit-1 { width: 104px; height: 104px; }
.orbit-2 { width: 178px; height: 178px; }
.orbit-3 { width: 250px; height: 250px; }

.orbit-center,
.orbit-face {
    position: absolute;
    z-index: 2;
}

.orbit-center {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.face-1 { top: 17px; left: 5px; }
.face-2 { top: 89px; right: -2px; }
.face-3 { bottom: 1px; left: 20px; }

.signal-dot {
    position: absolute;
    z-index: 3;
    width: 12px;
    height: 12px;
    border: 3px solid #fff;
    border-radius: 50%;
    background: #ff4f87;
    box-shadow: 0 2px 7px rgba(255, 79, 135, 0.45);
}

.dot-1 { top: 70px; left: 98px; }
.dot-2 { top: 133px; right: 18px; }
.dot-3 { bottom: 78px; left: 93px; }

.phone-footer {
    position: absolute;
    right: 0;
    bottom: 25px;
    left: 0;
    color: #9b8790;
    font-size: 11px;
    font-weight: 700;
    text-align: center;
    letter-spacing: 0.03em;
}

@media (max-width: 850px) {
    .catch-story {
        padding: 75px 24px 60px;
    }

    .catch-story-layout {
        grid-template-columns: 1fr;
        gap: 28px;
    }

    .catch-phone {
        order: -1;
    }

    .catch-story-layout > div:first-child,
    .catch-story-layout > div:last-child {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    show(
        '<section class="catch-story">'
        '<div class="catch-story-title">BEFORE THEY GO,<br>THERE&apos;S A SIGN.</div>'
        '<div class="catch-story-sub">떠나기 전에는,<br>늘 놓치기 쉬운 신호가 있습니다.</div>'
        '<div class="catch-story-layout">'
        '<div>'
        f'<div class="catch-stat"><div class="catch-number"><em>{facts.TOTAL_USERS:,}</em>명</div><div class="catch-label">분석한 사용자</div></div>'
        f'<div class="catch-stat"><div class="catch-number"><em>{facts.CHURN_RATE:.1f}%</em></div><div class="catch-label">{facts.CHURN_DAYS}일 이상 미접속한<br>사용자 비율</div></div>'
        '</div>'
        f'<div>{_signal_phone()}</div>'
        '<div>'
        f'<div class="catch-stat"><div class="catch-number"><em>{facts.FEATURE_COUNT}개</em></div><div class="catch-label">예측에 쓴 프로필 항목</div></div>'
        f'<div class="catch-stat"><div class="catch-number">약 <em>{recall_pct}%</em></div><div class="catch-label">실제 이탈자를<br>찾아낸 비율</div></div>'
        '</div>'
        '</div>'
        '</section>'
    )

    # ── Catch가 하는 일 ─────────────────────────────
    st.markdown(
        """
<style>
.catch-flow-section {
    padding: 110px 7vw 70px;
    box-sizing: border-box;
}

.catch-flow-label {
    color: #ff4f87;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.12em;
}

.catch-flow-heading {
    margin-top: 12px;
    color: #171217;
    font-size: clamp(40px, 4.6vw, 76px);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.075em;
}

.catch-flow-sub {
    margin-top: 22px;
    color: #655860;
    font-size: 18px;
    font-weight: 600;
    line-height: 1.6;
}

.catch-flow-list {
    margin-top: 78px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    border-top: 1px solid #e7dce1;
}

.catch-flow-item {
    min-height: 285px;
    padding: 34px 34px 20px;
    box-sizing: border-box;
    border-right: 1px solid #e7dce1;
}

.catch-flow-item:first-child {
    padding-left: 0;
}

.catch-flow-item:last-child {
    border-right: 0;
}

.catch-flow-number {
    color: #ff4f87;
    font-size: clamp(58px, 5vw, 88px);
    font-weight: 800;
    line-height: 0.9;
    letter-spacing: -0.09em;
}

.catch-flow-en {
    margin-top: 42px;
    color: #9a858d;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.12em;
}

.catch-flow-title {
    margin-top: 10px;
    color: #171217;
    font-size: clamp(23px, 2vw, 32px);
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.05em;
}

.catch-flow-copy {
    margin-top: 15px;
    color: #655860;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.65;
}

@media (max-width: 768px) {
    .catch-flow-section {
        padding: 80px 24px 45px;
    }

    .catch-flow-list {
        margin-top: 50px;
        grid-template-columns: 1fr;
    }

    .catch-flow-item,
    .catch-flow-item:first-child {
        min-height: auto;
        padding: 30px 0;
        border-right: 0;
        border-bottom: 1px solid #e7dce1;
    }

    .catch-flow-en {
        margin-top: 20px;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    show(
        '<section class="catch-flow-section">'
        '<div class="catch-flow-label">CATCH, THEN ACT.</div>'
        '<div class="catch-flow-heading">신호를 포착하고, 이유를 읽고,<br>다시 연결할 순간을 만듭니다.</div>'
        '<div class="catch-flow-sub">Catch는 이탈 가능성을 예측하는 데서 멈추지 않고,<br>운영팀이 바로 움직일 수 있는 다음 액션까지 연결합니다.</div>'
        '<div class="catch-flow-list">'
        '<div class="catch-flow-item">'
        '<div class="catch-flow-number">01</div>'
        '<div class="catch-flow-en">SPOT THE SIGNAL</div>'
        '<div class="catch-flow-title">떠나기 전,<br>먼저 포착합니다.</div>'
        '<div class="catch-flow-copy">행동 로그가 충분하지 않아도<br>프로필에서 이탈 위험 신호를 찾습니다.</div>'
        '</div>'
        '<div class="catch-flow-item">'
        '<div class="catch-flow-number">02</div>'
        '<div class="catch-flow-en">READ THE REASON</div>'
        '<div class="catch-flow-title">왜 떠나는지,<br>읽어냅니다.</div>'
        '<div class="catch-flow-copy">어떤 프로필 특징이 위험도에 영향을 줬는지<br>운영팀이 이해하기 쉽게 보여줍니다.</div>'
        '</div>'
        '<div class="catch-flow-item">'
        '<div class="catch-flow-number">03</div>'
        '<div class="catch-flow-en">MAKE THE MOVE</div>'
        '<div class="catch-flow-title">다시 올 이유를,<br>만듭니다.</div>'
        '<div class="catch-flow-copy">위험 수준에 맞춰 프로필 완성 유도,<br>재접속 알림 같은 액션을 제안합니다.</div>'
        '</div>'
        '</div>'
        '</section>'
    )


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