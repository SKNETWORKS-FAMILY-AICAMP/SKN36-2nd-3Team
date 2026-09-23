"""Catch 화면 스타일 (styles.py)

[이 파일이 하는 일]
화면의 '겉모습'(색, 글자 크기, 여백, 모서리 둥글기, 그림자 등)을 정하는 CSS 규칙 모음입니다.
글의 내용은 app.py 가, 겉모습은 이 파일이 맡아요.
(비유: app.py 는 '입을 옷', styles.py 는 '코디')

[CSS 읽는 법]
    .hero-title {          <- 'hero-title' 이라는 이름표(class)가 붙은 것에 적용
        font-size: 66px;   <- 글자 크기
        color: #1f1f1f;    <- 글자 색 (#숫자 = 색 코드, #ff4f81 이 이 서비스의 메인 핑크)
    }
app.py 의 HTML 에서 <div class="hero-title"> 처럼 이름표를 붙이면 이 규칙이 적용됩니다.

  - px  = 화면 점 단위 크기,  rem = 기본 글자 크기를 기준으로 한 크기
  - border-radius = 모서리 둥글기 (숫자가 클수록 둥글게)
  - !important    = 스트림릿이 기본으로 주는 디자인보다 '내 규칙을 우선해 줘' 라는 뜻
  - /* 이런 글 */  = CSS 의 주석 (화면에는 안 보이고 설명용)
  - data-testid   = 스트림릿이 각 부품(선택창, 버튼 등)에 붙여 둔 이름표.
                    이걸로 '선택창만', '입력칸만' 골라서 꾸밉니다.

[검정색이 다시 보이면]
스트림릿이 컴퓨터의 다크 모드를 따라 어두운 테마로 뜨면 검정 부분이 생깁니다.
프로젝트 맨 바깥의 .streamlit/config.toml 에서 라이트 테마로 고정해 두었으니
그 파일이 제자리에 있는지 먼저 확인하세요.

[자주 하는 수정]
  - 메인 핑크를 바꾸고 싶다   -> #ff4f81 을 원하는 색 코드로 (Ctrl+H 로 한꺼번에 바꾸기)
  - 카드 모서리를 덜 둥글게   -> .feature-card 의 border-radius 숫자를 줄이기
"""
import streamlit as st

# 아래 큰 따옴표 3개(""") 사이의 글이 통째로 CSS 입니다.
# <style> 태그로 감싸야 브라우저가 "이건 디자인 규칙이구나" 하고 읽어요.
CSS = """
<style>

/* ---------- 전체 배경 / 여백 ---------- */
/* .stApp = 스트림릿 화면 전체. 연한 핑크빛이 번지는(radial-gradient) 배경을 깔아요. */
.stApp {
    background:
        radial-gradient(circle at 85% 15%, #ffe8f0 0%, transparent 25%),
        radial-gradient(circle at 10% 80%, #fff1f5 0%, transparent 30%),
        #fffafb;
}

/* 가운데 내용 영역: 위 여백 1.5rem, 아래 여백 4rem, 가로는 최대 1250px 까지만
   (모니터가 넓어도 내용이 너무 퍼지지 않게) */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 4rem;
    max-width: 1250px;
}

/* 스트림릿이 기본으로 붙이는 오른쪽 위 메뉴, 아래 문구, 상단 바를 숨겨서
   우리 서비스 화면처럼 보이게 함 */
#MainMenu, footer, header {
    visibility: hidden;
}

/* ---------- 로고 ---------- */
/* 왼쪽 위 ♥ Catch 글자 */
.logo {
    font-size: 28px;
    font-weight: 800;
    color: #222222;
    letter-spacing: -1px;
}

.logo-heart {
    color: #ff4f81;
}

/* ---------- Hero ---------- */
/* Hero = 홈 화면 맨 위의 큰 소개 영역 (큰 제목 + 설명 문구) */
.hero-wrap {
    padding: 100px 20px 70px 20px;
    text-align: center;
}

.hero-badge {
    display: inline-block;
    padding: 9px 18px;
    border-radius: 30px;
    background: #fff0f5;
    color: #d1245e;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 24px;
}

.hero-title {
    font-size: 66px;
    line-height: 1.13;
    font-weight: 850;
    color: #1f1f1f;
    letter-spacing: -3px;
}

.hero-highlight {
    color: #ff4f81;
}

.hero-description {
    margin-top: 24px;
    font-size: 20px;
    line-height: 1.75;
    color: #666666;
}

.hero-sub {
    margin-top: 8px;
    font-size: 16px;
    color: #6b6b6b;
}

/* ---------- 카드 ---------- */
/* 흰 배경에 둥근 모서리와 옅은 그림자가 있는 상자.
   홈의 기능 소개 3개, 서비스 화면의 입력 카드에 씀 */
.feature-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #f4e6eb;
    border-radius: 24px;
    padding: 30px 28px;
    min-height: 240px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
}

.feature-icon {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: #fff0f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 25px;
    margin-bottom: 22px;
}

.feature-title {
    font-size: 20px;
    font-weight: 800;
    color: #252525;
    margin-bottom: 12px;
}

.feature-text {
    font-size: 15.5px;
    color: #5a5a5a;
    line-height: 1.7;
}

/* ---------- 섹션 제목 ---------- */
/* "WHAT WE DO" 같은 작은 글자(label)와 그 아래 큰 제목(title) */
.section-label {
    text-align: center;
    color: #d1245e;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1px;
    margin-top: 60px;
}

.section-title {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    color: #252525;
    margin-top: 8px;
    margin-bottom: 36px;
}

/* ---------- 버튼 ---------- */
/* 분홍색 둥근 버튼. :hover 는 마우스를 올렸을 때 색을 살짝 진하게 */
div.stButton > button {
    border: none;
    border-radius: 14px;
    background: #e0295f;
    color: white;
    font-weight: 750;
    font-size: 16px;
    padding: 0.8rem 2rem;
    min-height: 52px;
    box-shadow: 0 7px 18px rgba(255, 79, 129, 0.22);
}

div.stButton > button:hover {
    background: #c81e55;
    color: white;
    border: none;
}

/* ---------- 상단 nav radio ---------- */
/* 상단 메뉴(HOME / SERVICE ...)는 라디오 버튼을 가로로 늘어놓은 것. 간격과 글자 굵기만 조정 */
div[data-testid="stRadio"] > div {
    gap: 20px;
}

div[data-testid="stRadio"] label {
    font-size: 14px;
    font-weight: 650;
}

/* ---------- 입력 항목 라벨 ---------- */
/* 입력칸 위의 이름표 글자("나이", "직업" 등)를 진하고 또렷하게 */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stCheckbox"] label,
div[data-testid="stRadio"] > label,
div[data-testid="stCaptionContainer"] {
    color: #222222 !important;
    font-weight: 700 !important;
}

.stMarkdown,
.stCaption {
    color: #555555 !important;
}

/* ---------- expander ---------- */
/* expander = 접었다 펼 수 있는 상자("기본 정보", "라이프스타일" 등).
   summary 는 그 상자의 제목 줄이라서 연한 핑크 바탕으로 */
div[data-testid="stExpander"] {
    color: #222222 !important;
}

div[data-testid="stExpander"] summary {
    background: #ffe4ec !important;
    color: #c81e55 !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}

/* ---------- 일반 input / textarea ---------- */
/* 글자 입력칸(input)과 긴 글 입력칸(textarea)의 배경, 테두리, 모서리 */
input,
textarea {
    background-color: #fff7fa !important;
    color: #333333 !important;
    border-radius: 12px !important;
}

textarea {
    border: 1px solid #f5b8ca !important;
}

div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
    background-color: #fff7fa !important;
    border-radius: 12px !important;
}

div[data-baseweb="textarea"] {
    border: 1px solid #f3b8ca !important;
}

div[data-baseweb="textarea"]:focus-within {
    border-color: #ff4f81 !important;
    box-shadow: 0 0 0 1px #ff4f81 !important;
}

/* 숫자 입력(연 소득)의 + - 버튼 */
div[data-testid="stNumberInput"] button {
    background-color: #ffe4ec !important;
    color: #ff4f81 !important;
    border: none !important;
}

/* ============================= */
/* Selectbox (닫혀 있을 때)       */
/* ============================= */

/* 선택창 본체 (드롭다운을 닫아 둔 평소 모습): 연한 핑크 배경 + 핑크 테두리 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #fff7fa !important;
    border: 1px solid #f3b8ca !important;
    border-radius: 12px !important;
    color: #333333 !important;
}

/* 선택창 안쪽 (글씨 영역 + 화살표 영역) 은 배경 없이 -> 본체의 핑크색이 비쳐 보임.
   이 규칙이 없으면 오른쪽 화살표 칸이 어두운 색으로 남아요 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div > div * {
    background-color: transparent !important;
    color: #333333 !important;
}

/* 화살표 */
div[data-testid="stSelectbox"] svg {
    fill: #ff4f81 !important;
    color: #ff4f81 !important;
}

/* 포커스 = 선택창을 클릭해서 활성화된 상태: 테두리를 진한 핑크로 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    border-color: #ff4f81 !important;
    box-shadow: 0 0 0 1px #ff4f81 !important;
}

/* ============================= */
/* Selectbox (펼쳐진 목록)        */
/* 선택창을 클릭하면 펼쳐지는 목록은 화면 맨 위 별도 레이어(popover)에 그려집니다.
   그래서 위의 선택창 규칙이 적용되지 않고, 아래처럼 따로 색을 지정해야 해요.
   (검정 목록이 나오던 원인이 바로 이 부분이었습니다) */
/* ============================= */

div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] div[data-baseweb="menu"],
div[data-baseweb="popover"] ul,
ul[role="listbox"] {
    background-color: #fffafb !important;
    color: #333333 !important;
}

div[data-baseweb="popover"] > div {
    border: 1px solid #f3b8ca !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 30px rgba(58, 26, 37, 0.10) !important;
}

li[role="option"] {
    background-color: #fffafb !important;
    color: #333333 !important;
}

li[role="option"] * {
    background-color: transparent !important;
    color: #333333 !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background-color: #ffe4ec !important;
}

li[role="option"][aria-selected="true"] * {
    color: #ff4f81 !important;
}


/* ================================================================ */
/* INSIGHT / RETENTION / ABOUT 화면에서 쓰는 카드·그래프·표 디자인       */
/* (ui_parts.py 가 만드는 HTML 의 class 이름과 짝이에요)                */
/* ================================================================ */

/* ---------- 구역 제목 ---------- */
.section-head {
    font-size: 22px;
    font-weight: 800;
    color: #252525;
    margin: 34px 0 4px 0;
}

.section-sub {
    font-size: 15px;
    color: #6b6b6b;
    margin-bottom: 14px;
    line-height: 1.6;
}

/* ---------- 기본 카드 (흰 상자) ---------- */
.dash-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #f4e6eb;
    border-radius: 24px;
    padding: 24px 26px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
    margin-bottom: 20px;
}

.dash-title {
    font-size: 18px;
    font-weight: 800;
    color: #252525;
}

.dash-sub {
    font-size: 14px;
    color: #6b6b6b;
    margin: 4px 0 14px 0;
    line-height: 1.6;
}

.dash-foot {
    font-size: 13px;
    color: #6b6b6b;
    margin-top: 14px;
}

/* ---------- 숫자 카드 ---------- */
.kpi-card {
    min-height: 118px;
}

.kpi-label {
    font-size: 14px;
    font-weight: 700;
    color: #5a5a5a;
}

.kpi-value {
    font-size: 32px;
    font-weight: 850;
    color: #ff4f81;
    margin-top: 6px;
    letter-spacing: -1px;
}

.kpi-sub {
    font-size: 13.5px;
    color: #6b6b6b;
    margin-top: 4px;
    line-height: 1.5;
}

/* ---------- 막대그래프 ---------- */
/* 한 줄 = [이름] [막대] [숫자] 가 가로로 나란히 */
.bar-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0;
}

.bar-label {
    width: 150px;
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 650;
    color: #444444;
    line-height: 1.35;
}

.bar-n {
    font-size: 12.5px;
    font-weight: 500;
    color: #6b6b6b;
}

/* 막대가 들어가는 옅은 트랙 */
.bar-track {
    position: relative;
    flex: 1;
    height: 14px;
    background: #fdeef3;
    border-radius: 8px;
}

/* 색이 칠해진 막대. hot 이 붙으면 진한 핑크 */
.bar-fill {
    height: 100%;
    border-radius: 8px;
    background: #f5b8ca;
}

.bar-fill.hot {
    background: #ff4f81;
}

/* 전체 평균을 나타내는 세로 점선 */
.bar-base {
    position: absolute;
    top: -4px;
    bottom: -4px;
    border-left: 2px dashed #b08a97;
}

.bar-value {
    width: 58px;
    flex-shrink: 0;
    text-align: right;
    font-size: 14px;
    font-weight: 800;
    color: #252525;
}

/* 두 그룹 비교 카드의 제목 줄 (제목 + 배수 알약) */
.signal-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

/* ---------- 알약(작은 표시) ---------- */
.tag {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12.5px;
    font-weight: 800;
    white-space: nowrap;
}

.tag-high { background: #ffe0e8; color: #c81e55; }
.tag-mid  { background: #fff0d9; color: #9a5a08; }
.tag-low  { background: #e8f7ec; color: #237a3f; }

/* ---------- 표 ---------- */
.fact-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.fact-table th {
    text-align: left;
    color: #5a5a5a;
    font-weight: 700;
    padding: 10px 12px;
    border-bottom: 1px solid #f4e6eb;
}

.fact-table td {
    padding: 12px;
    color: #333333;
    border-bottom: 1px solid #f9eef2;
    font-size: 14.5px;
}

/* 강조할 줄 (채택한 모델) */
.fact-table tr.hl td {
    background: #fff0f5;
    color: #e0245e;
    font-weight: 800;
}

/* ---------- 체크 목록 / 순위 목록 ---------- */
.check-item,
.rank-item {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    padding: 10px 0;
}

.rank-item {
    border-bottom: 1px solid #f9eef2;
}

.check-mark,
.rank-no {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #ffe4ec;
    color: #c81e55;
    font-size: 13px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
}

.check-title {
    font-size: 15px;
    font-weight: 750;
    color: #2a2a2a;
}

.check-text {
    font-size: 14px;
    color: #5a5a5a;
    line-height: 1.6;
    margin-top: 2px;
}

/* 설명이 비어 있으면 자리를 차지하지 않게 */
.check-text:empty {
    display: none;
}

.code {
    font-size: 13px;
    font-weight: 600;
    color: #6b6b6b;
    margin-left: 6px;
}

/* ---------- 문단 / 안내 상자 / 준비 중 ---------- */
.para {
    font-size: 15px;
    color: #555555;
    line-height: 1.8;
    margin-bottom: 10px;
}

.note-box {
    background: #fff3f7;
    border-radius: 16px;
    padding: 14px 18px;
    font-size: 14.5px;
    color: #5a5a5a;
    line-height: 1.75;
    margin: 6px 0 20px 0;
}

.placeholder {
    margin-top: 12px;
    padding: 30px 22px;
    border: 1.5px dashed #f3b8ca;
    border-radius: 16px;
    text-align: center;
    color: #8a5a6e;
    font-size: 15px;
    line-height: 1.7;
}

/* ---------- 전략 카드 (RETENTION) ---------- */
.action-card {
    display: flex;
    gap: 16px;
    align-items: center;
    padding: 18px 20px;
    border: 1px solid #f4e6eb;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.92);
    margin-bottom: 12px;
    box-shadow: 0 8px 24px rgba(58, 26, 37, 0.04);
}

.action-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: #fff0f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
}

.action-title {
    font-size: 16px;
    font-weight: 800;
    color: #252525;
}

.action-text {
    font-size: 14.5px;
    color: #5a5a5a;
    line-height: 1.6;
    margin-top: 3px;
}

.level-head {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 18px;
}

.level-headline {
    font-size: 20px;
    font-weight: 800;
    color: #252525;
}

.level-goal {
    font-size: 14.5px;
    color: #5a5a5a;
    line-height: 1.7;
    margin: 8px 0 4px 0;
}

/* ---------- 단계 흐름 (ABOUT: 앞으로의 확장 방향) ---------- */
.step-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.step-item {
    flex: 1;
    min-width: 150px;
    background: #fff7fa;
    border-radius: 16px;
    padding: 16px;
}

.step-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    background: #ffe4ec;
    color: #c81e55;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 8px;
}

/* ================================================================ */
/* HOME / ABOUT 에서 쓰는 숫자 줄, 단계 흐름, 칩, 예시 화면, 마무리 문구  */
/* ================================================================ */

/* ---------- 숫자 줄 (HOME) ---------- */
/* 큰 숫자 4개를 하얀 띠 안에 나란히. 칸 사이는 옅은 세로줄로 나눔 */
.stat-band {
    display: flex;
    flex-wrap: wrap;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #f4e6eb;
    border-radius: 28px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
    padding: 26px 10px;
    margin: 30px 0 10px 0;
}

.stat-item {
    flex: 1;
    min-width: 180px;
    text-align: center;
    padding: 6px 12px;
    border-right: 1px solid #f7e8ee;
}

.stat-item:last-child {
    border-right: none;
}

.stat-num {
    font-size: 36px;
    font-weight: 850;
    color: #ff4f81;
    letter-spacing: -1px;
}

.stat-label {
    font-size: 14px;
    color: #5a5a5a;
    margin-top: 4px;
}

/* ---------- 단계 흐름 (HOME 이용 방법, ABOUT 만든 과정) ---------- */
/* [단계] → [단계] → [단계] 가 가로로 이어짐. 화면이 좁으면 아래로 줄바꿈 */
.flow-row {
    display: flex;
    align-items: stretch;
    gap: 10px;
    flex-wrap: wrap;
}

.flow-step {
    flex: 1;
    min-width: 170px;
    background: #ffffff;
    border: 1px solid #f4e6eb;
    border-radius: 22px;
    padding: 24px 22px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
}

/* 다른 카드 안에 넣을 때는 옅은 핑크 배경, 그림자 없이 */
.flow-step.tint {
    background: #fff7fa;
    box-shadow: none;
}

/* 번호(1,2,3) 또는 아이콘이 들어가는 동그란/둥근 표시 */
.flow-badge {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #ffe4ec;
    color: #c81e55;
    font-size: 17px;
    font-weight: 850;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 14px;
}

.flow-badge.icon {
    border-radius: 14px;
    font-size: 22px;
}

.flow-title {
    font-size: 17px;
    font-weight: 800;
    color: #252525;
}

.flow-desc {
    font-size: 14.5px;
    color: #5a5a5a;
    line-height: 1.65;
    margin-top: 6px;
}

/* 단계 아래의 핵심 숫자/문구 (예: 59,946명 · 31개 컬럼) */
.flow-meta {
    margin-top: 12px;
    font-size: 13px;
    font-weight: 700;
    color: #c81e55;
}

.flow-arrow {
    align-self: center;
    color: #f3b8ca;
    font-size: 22px;
    font-weight: 800;
}

/* ---------- 칩(작은 알약 모양 표시) ---------- */
.chip {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 14px;
    background: #f6f1f3;
    color: #5a4d52;
    font-size: 13.5px;
    font-weight: 600;
    margin: 0 6px 8px 0;
}

.chip b {
    color: #c81e55;
    font-weight: 800;
}

.chip-pink {
    background: #ffe4ec;
    color: #c81e55;
    font-weight: 750;
}

/* ---------- 예시 화면 카드 (HOME 미리보기) ---------- */
/* 점선 테두리 + '예시 화면' 딱지로, 진짜 결과가 아니라 모양 예시임을 분명히 함 */
.preview-card {
    position: relative;
    background: #ffffff;
    border: 1.5px dashed #f3b8ca;
    border-radius: 24px;
    padding: 26px 26px 20px 26px;
    margin-bottom: 20px;
}

.preview-ribbon {
    position: absolute;
    top: 18px;
    right: 20px;
    background: #fff0f5;
    color: #8a5a6e;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 12px;
}

.preview-title {
    font-size: 18px;
    font-weight: 800;
    color: #252525;
    margin-bottom: 16px;
}

.preview-risk {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fff3f7;
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 18px;
}

.preview-risk-text {
    font-size: 15px;
    font-weight: 700;
    color: #444444;
}

.preview-label {
    font-size: 13.5px;
    font-weight: 750;
    color: #5a5a5a;
    margin-bottom: 8px;
}

/* ---------- 마무리 문구 (HOME 맨 아래) ---------- */
.cta-band {
    text-align: center;
    margin-top: 56px;
    padding: 30px 20px 8px 20px;
}

.cta-title {
    font-size: 30px;
    font-weight: 850;
    color: #252525;
    letter-spacing: -1px;
}

.cta-text {
    font-size: 16px;
    color: #5a5a5a;
    margin: 10px 0 22px 0;
}

/* ---------- 히트맵 표 (INSIGHT: 자기소개 개수 x 길이) ---------- */
/* 칸의 배경 색 진하기는 코드(ui_parts.heatmap_card)가 값에 맞춰 정해 줘요 */
.heat-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 6px;
}

.heat-table th {
    font-size: 13px;
    font-weight: 700;
    color: #5a5a5a;
    text-align: center;
    padding: 4px 2px;
}

.heat-table th.heat-row {
    text-align: right;
    padding-right: 8px;
    white-space: nowrap;
    color: #444444;
}

.heat-table td {
    padding: 0;
}

/* 스트림릿의 기본 표 테두리와 배경을 지워서 칸 사이에 선이 보이지 않게 */
.heat-table th,
.heat-table td {
    border: none !important;
    background: transparent !important;
}

.heat-cell {
    border-radius: 12px;
    padding: 12px 6px;
    text-align: center;
    font-size: 15px;
    font-weight: 800;
}

.heat-n {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.95;
    margin-top: 2px;
}

/* ---------- 가상 사용자 카드 (INSIGHT 페르소나) ---------- */
.persona-card {
    position: relative;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #f4e6eb;
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
    margin-bottom: 20px;
}

/* 오른쪽 위 '가상 사용자' 딱지: 실제 사람이 아님을 분명히 */
.persona-ribbon {
    position: absolute;
    top: 18px;
    right: 20px;
    background: #fff0f5;
    color: #8a5a6e;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 12px;
}

.persona-top {
    display: flex;
    align-items: center;
    gap: 16px;
}

.persona-name {
    font-size: 20px;
    font-weight: 850;
    color: #252525;
    margin-top: 8px;
}

.persona-story {
    font-size: 14.5px;
    color: #5a5a5a;
    line-height: 1.7;
    margin: 16px 0 4px 0;
}

/* 대표 그룹의 실제 이탈률을 크게 보여주는 상자 */
.persona-stat {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #fff7fa;
    border-radius: 16px;
    padding: 14px 18px;
    margin: 14px 0 16px 0;
}

.persona-rate {
    font-size: 32px;
    font-weight: 850;
    letter-spacing: -1px;
}

.persona-rate.high { color: #c81e55; }
.persona-rate.mid  { color: #9a5a08; }
.persona-rate.low  { color: #237a3f; }

.persona-stat-text {
    font-size: 13.5px;
    color: #5a5a5a;
    line-height: 1.6;
}

/* ---------- 핵심 발견 요약 띠 (INSIGHT 맨 위) ---------- */
/* 페이지를 열자마자 '결론 3가지'를 읽을 수 있게, 은은한 핑크 바탕에 큰 숫자로 보여줘요 */
.take-band {
    background: linear-gradient(135deg, #fff0f5 0%, #ffffff 70%);
    border: 1px solid #f4dce4;
    border-radius: 28px;
    padding: 26px 30px 22px 30px;
    margin: 4px 0 22px 0;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
}

.take-eyebrow {
    font-size: 14px;
    font-weight: 800;
    color: #d1245e;
    margin-bottom: 14px;
}

.take-row {
    display: flex;
    flex-wrap: wrap;
    gap: 22px;
}

.take-item {
    flex: 1;
    min-width: 220px;
    border-left: 3px solid #ffc2d4;
    padding-left: 16px;
}

.take-big {
    font-size: 34px;
    font-weight: 850;
    color: #ff4f81;
    letter-spacing: -1px;
    line-height: 1.15;
}

.take-title {
    font-size: 16.5px;
    font-weight: 800;
    color: #252525;
    margin-top: 6px;
}

.take-text {
    font-size: 14px;
    color: #5a5a5a;
    line-height: 1.6;
    margin-top: 4px;
}

/* 히트맵 표의 줄(tr)에도 스트림릿이 넣는 가로줄 제거 */
.heat-table,
.heat-table tr {
    border: none !important;
    background: transparent !important;
}

/* ================================================================ */
/* SERVICE 화면 오른쪽 '결과 칸' 카드 (service_view.py 가 만드는 HTML)   */
/* ================================================================ */
.result-card {
    position: relative;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #f4e6eb;
    border-radius: 24px;
    padding: 26px 28px;
    box-shadow: 0 12px 35px rgba(58, 26, 37, 0.05);
    margin-bottom: 20px;
}

.result-title {
    font-size: 20px;
    font-weight: 800;
    color: #222222;
    margin-bottom: 16px;
}

/* 위험 단계 막대: Low / Medium / High 세 칸. dim 이 붙은 칸은 흐리게(아직 모름) */
.risk-scale {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
}

.risk-seg {
    flex: 1;
    text-align: center;
    padding: 12px 0;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 800;
}

.risk-seg.low  { background: #e8f7ec; color: #237a3f; }
.risk-seg.mid  { background: #fff0d9; color: #9a5a08; }
.risk-seg.high { background: #ffe0e8; color: #c81e55; }
.risk-seg.dim  { opacity: 0.45; }

.result-note {
    font-size: 14px;
    color: #5a5a5a;
    text-align: center;
    margin-bottom: 16px;
}

/* '비슷하게 쓴 사용자의 실제 이탈률' 상자 */
.ref-box {
    display: flex;
    align-items: center;
    gap: 18px;
    background: #fff7fa;
    border-radius: 18px;
    padding: 18px 20px;
}

.ref-rate {
    font-size: 40px;
    font-weight: 850;
    letter-spacing: -1px;
    white-space: nowrap;
}

.ref-text {
    font-size: 14px;
    color: #5a5a5a;
    line-height: 1.65;
}

/* 신호 한 줄: warn(주의) 은 연한 핑크, ok(양호) 는 연한 초록 배경 */
.sig-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 12px 14px;
    border-radius: 14px;
    margin-bottom: 8px;
}

.sig-row.warn { background: #fff3f7; }
.sig-row.ok   { background: #f2faf4; }

.sig-icon {
    font-size: 18px;
    line-height: 1.4;
}

.sig-title {
    font-size: 15px;
    font-weight: 750;
    color: #2a2a2a;
}

.sig-stat {
    font-size: 13.5px;
    color: #5a5a5a;
    line-height: 1.55;
    margin-top: 2px;
}

/* 추천 전략 한 줄 */
.strat-row {
    display: flex;
    gap: 14px;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f9eef2;
}

.strat-row:last-child {
    border-bottom: none;
}

.strat-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #fff0f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    flex-shrink: 0;
}

/* ================================================================ */
/* 상단 메뉴 고정 (스크롤해도 화면 맨 위에 붙어 있게)                     */
/* ================================================================ */
/* app.py 의 로고에 붙인 nav-anchor 표시를 보고, 그 표시가 들어 있는 '맨 위 한 줄'만 고정해요.
   (:has() 는 '안에 ~가 있는 것'을 고르는 CSS 문법이에요. 최신 크롬/엣지/사파리/파이어폭스에서 동작)
   스트림릿 버전에 따라 줄을 감싸는 상자가 있을 수도, 없을 수도 있어서 두 경우를 모두 적어 뒀어요. */
.block-container > div[data-testid="stVerticalBlock"] > *:has(.nav-anchor),
div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > *:has(.nav-anchor) {
    position: sticky;
    top: 0;
    z-index: 999;
    padding: 12px 0 8px 0;
    isolation: isolate;
}

/* 메뉴 바의 흰 배경을 브라우저 전체 폭으로 확장 */
.block-container > div[data-testid="stVerticalBlock"] > *:has(.nav-anchor),
div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > *:has(.nav-anchor) {
    position: sticky;
    top: 0;
    z-index: 999;

    /* 메뉴 바를 브라우저 전체 폭으로 확장 */
    width: 100vw !important;
    max-width: 100vw !important;
    margin-left: calc(50% - 50vw) !important;

    box-sizing: border-box;
    padding: 12px max(40px, calc((100vw - 1250px) / 2)) 8px;

    background: rgba(255, 250, 251, 0.97);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(244, 230, 235, 0.9);
}

/* ================================================================ */
/* 한글 줄바꿈: 단어 중간(예: "프|로필")에서 끊기지 않고 띄어쓰기에서 줄바꿈 */
/* ================================================================ */
.stApp {
    word-break: keep-all;
    overflow-wrap: break-word;
}

/* ---------- 모델 비교 표: 스트림릿 기본 격자(세로줄·바깥 테두리)를 지우고 가로줄만 남김 ---------- */
.fact-table,
.fact-table th,
.fact-table td,
.fact-table tr {
    border-left: none !important;
    border-right: none !important;
    border-top: none !important;
    background: transparent !important;
}

.fact-table th {
    border-bottom: 1px solid #f4e6eb !important;
}

.fact-table td {
    border-bottom: 1px solid #f9eef2 !important;
}

/* 강조할 줄(채택한 모델)의 배경은 위에서 지운 배경보다 우선해야 해서 다시 한 번 지정 */
.fact-table tr.hl td {
    background: #fff0f5 !important;
}
</style>
"""


def apply_styles():
    """위 CSS 를 화면에 적용한다. app.py 맨 위에서 한 번 호출하면 됩니다.
    (unsafe_allow_html=True 는 'HTML/CSS 를 글자가 아니라 코드로 읽어 줘' 라는 뜻)"""
    st.markdown(CSS, unsafe_allow_html=True)
