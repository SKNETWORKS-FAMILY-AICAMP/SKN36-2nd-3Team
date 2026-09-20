"""화면 조립 부품 모음 (ui_parts.py)

[이 파일이 하는 일]
INSIGHT / RETENTION / ABOUT 페이지가 공통으로 쓰는 '화면 조각'을 만들어 줍니다.
  - 페이지 맨 위 제목            page_header()
  - 숫자 카드                    kpi_card()
  - 막대그래프 카드               rate_bars_card()
  - 두 그룹 비교 카드             signal_card()
  - 표 / 체크 목록 / 안내 상자 등  table_card(), check_list_card(), note_box() ...
  - 숫자 줄 / 단계 흐름 / 칩 목록   stat_band(), flow_row(), flow_card(), chip_card()
  - 색으로 보는 표(히트맵)          heatmap_card()
  - 가상 사용자 카드(페르소나)      persona_card()

[왜 따로 뺐나요?]
카드를 만드는 HTML 코드는 길고 반복돼요. 한곳에 모아 두면 세 페이지가 같은 모양을 쓰고,
모양을 바꿀 때도 여기(와 styles.py)만 고치면 됩니다.

[동작 방식]
아래 함수들은 모두 'HTML 글자'를 돌려주기만 합니다. 실제로 화면에 그리는 건 show() 예요.
    show(kpi_card("분석 사용자", "59,946명"))
※ HTML 안에 빈 줄이나 4칸 이상 들여쓰기가 있으면 Streamlit 이 코드 블록으로 오해해서
   글자 그대로 보여 주기 때문에, 아래 함수들은 HTML 을 '한 줄로 이어 붙여서' 만듭니다.
"""
import html

import streamlit as st


def show(markup):
    """HTML 글자를 화면에 그린다. (unsafe_allow_html=True : 글자가 아니라 HTML 코드로 읽어 줘)"""
    st.markdown(markup, unsafe_allow_html=True)


def esc(text):
    """글자 안의 <, >, & 같은 특수문자를 안전하게 바꿔 준다. (HTML 이 깨지는 것을 방지)"""
    return html.escape(str(text))


# ---------------------------------------------------------
# 페이지 제목
# ---------------------------------------------------------
def page_header(label, title, subtitle):
    """SERVICE 화면 제목과 같은 모양: 작은 핑크 글씨 + 큰 제목 + 회색 설명"""
    return (
        '<div style="padding-top: 50px; padding-bottom: 25px;">'
        f'<div style="font-size: 14px; font-weight: 800; color: #ff4f81;">{esc(label)}</div>'
        f'<div style="font-size: 38px; font-weight: 850; color: #222; margin-top: 8px;">{esc(title)}</div>'
        f'<div style="font-size: 16px; color: #777; margin-top: 10px;">{esc(subtitle)}</div>'
        '</div>'
    )


def section_title(text, sub=""):
    """페이지 안의 큰 구역 제목 (예: '주요 예측 신호')"""
    sub_html = f'<div class="section-sub">{esc(sub)}</div>' if sub else ""
    return f'<div class="section-head">{esc(text)}</div>{sub_html}'


# ---------------------------------------------------------
# 숫자 카드
# ---------------------------------------------------------
def kpi_card(label, value, sub=""):
    """큰 숫자 하나를 보여 주는 카드. 예) 이탈률 / 25.7% / 30일 이상 미접속"""
    sub_html = f'<div class="kpi-sub">{esc(sub)}</div>' if sub else ""
    return (f'<div class="dash-card kpi-card"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value">{esc(value)}</div>{sub_html}</div>')


# ---------------------------------------------------------
# 막대그래프
# ---------------------------------------------------------
def _bar_row(label, rate, scale, hot, n=None, base_pct=None):
    """막대 한 줄. scale = 막대가 100% 길이가 되는 이탈률 값"""
    width = max(min(rate / scale * 100, 100), 1.5)      # 막대 길이(%) — 너무 짧아 안 보이는 것 방지
    n_html = f'<div class="bar-n">{n:,}명</div>' if n else ""
    base_html = f'<div class="bar-base" style="left:{base_pct:.1f}%"></div>' if base_pct is not None else ""
    fill_class = "bar-fill hot" if hot else "bar-fill"
    return (f'<div class="bar-row"><div class="bar-label">{esc(label)}{n_html}</div>'
            f'<div class="bar-track"><div class="{fill_class}" style="width:{width:.1f}%"></div>{base_html}</div>'
            f'<div class="bar-value">{rate:.1f}%</div></div>')


def rate_bars_card(title, subtitle, rows, baseline=None, hot_labels=None, footer=""):
    """이탈률 막대그래프 카드.

    rows       : [{"label": ..., "rate": 이탈률(%), "n": 사람 수(없어도 됨)}, ...]
    baseline   : 전체 평균 이탈률. 있으면 점선으로 표시하고, 평균보다 높은 막대를 진한 핑크로 칠함
    hot_labels : 진하게 칠할 막대 이름 목록 (baseline 대신 직접 지정하고 싶을 때)
    footer     : 카드 아래 작은 설명
    """
    top = max([r["rate"] for r in rows] + ([baseline] if baseline else []))
    scale = top * 1.12                                   # 가장 긴 막대가 꽉 차지 않게 여유를 둠
    base_pct = (baseline / scale * 100) if baseline else None

    bars = ""
    for r in rows:
        if hot_labels is not None:
            hot = r["label"] in hot_labels
        else:
            hot = baseline is not None and r["rate"] > baseline
        bars += _bar_row(r["label"], r["rate"], scale, hot, r.get("n"), base_pct)

    legend = f"점선 = 전체 평균 {baseline:.1f}%" if baseline else ""
    foot_text = " · ".join(t for t in (legend, footer) if t)
    foot_html = f'<div class="dash-foot">{esc(foot_text)}</div>' if foot_text else ""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>{bars}{foot_html}</div>')


def signal_card(title, high_label, high_rate, low_label, low_rate):
    """두 그룹의 이탈률을 나란히 비교하는 카드. 오른쪽 위에 '몇 배 차이인지'를 붙여 준다."""
    ratio = high_rate / low_rate
    scale = high_rate * 1.08
    return (f'<div class="dash-card"><div class="signal-head"><div class="dash-title">{esc(title)}</div>'
            f'<span class="tag tag-high">{ratio:.1f}배</span></div>'
            f'{_bar_row(high_label, high_rate, scale, True)}'
            f'{_bar_row(low_label, low_rate, scale, False)}</div>')


# ---------------------------------------------------------
# 표 / 목록 / 안내 상자
# ---------------------------------------------------------
def table_card(title, subtitle, headers, rows, highlight_row=None, footer=""):
    """표 카드. highlight_row = 강조할 줄 번호(0부터)"""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = ""
    for i, row in enumerate(rows):
        cls = ' class="hl"' if i == highlight_row else ""
        body += f"<tr{cls}>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
    foot_html = f'<div class="dash-foot">{esc(footer)}</div>' if footer else ""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>'
            f'<table class="fact-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{foot_html}</div>')


def check_list_card(title, subtitle, items):
    """제목 + 설명이 붙은 항목 목록 카드. items = [(굵은 제목, 설명), ...]"""
    li = "".join(f'<div class="check-item"><div class="check-mark">✓</div>'
                 f'<div><div class="check-title">{esc(t)}</div><div class="check-text">{esc(d)}</div></div></div>'
                 for t, d in items)
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>{li}</div>')


def text_card(title, paragraphs):
    """제목 + 문단 몇 개로 된 설명 카드"""
    body = "".join(f'<div class="para">{esc(p)}</div>' for p in paragraphs)
    return f'<div class="dash-card"><div class="dash-title">{esc(title)}</div><div style="margin-top:12px">{body}</div></div>'


def action_card(icon, title, text):
    """전략 카드 한 장: 왼쪽 아이콘 + 오른쪽 제목/설명"""
    return (f'<div class="action-card"><div class="action-icon">{icon}</div>'
            f'<div><div class="action-title">{esc(title)}</div><div class="action-text">{esc(text)}</div></div></div>')


def rank_list_card(title, subtitle, items, footer=""):
    """순위 목록 카드. items = [(영문 이름, 쉬운 이름, 설명), ...]  (1위부터 차례로)"""
    li = ""
    for i, (code, name, desc) in enumerate(items, start=1):
        li += (f'<div class="rank-item"><div class="rank-no">{i}</div><div>'
               f'<div class="check-title">{esc(name)} <span class="code">{esc(code)}</span></div>'
               f'<div class="check-text">{esc(desc)}</div></div></div>')
    foot_html = f'<div class="dash-foot">{esc(footer)}</div>' if footer else ""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>{li}{foot_html}</div>')


def steps_card(title, subtitle, steps):
    """단계 흐름 카드. steps = [(꼬리표, 제목, 설명), ...]"""
    li = ""
    for tag, name, desc in steps:
        li += (f'<div class="step-item"><div class="step-tag">{esc(tag)}</div>'
               f'<div class="check-title">{esc(name)}</div><div class="check-text">{esc(desc)}</div></div>')
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div><div class="step-row">{li}</div></div>')


def placeholder_card(title, message):
    """아직 데이터가 없을 때 '준비 중'을 보여 주는 카드"""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="placeholder">{esc(message)}</div></div>')


def note_box(text):
    """회색-핑크 안내 상자 (주의사항, 해석 방법 등)"""
    return f'<div class="note-box">{esc(text)}</div>'


def tag(text, kind="high"):
    """작은 알약 모양 표시. kind = high(빨강) / mid(주황) / low(초록)"""
    return f'<span class="tag tag-{kind}">{esc(text)}</span>'


# ---------------------------------------------------------
# 숫자 줄 / 단계 흐름 / 칩 (HOME, ABOUT 에서 사용)
# ---------------------------------------------------------
def stat_band(items):
    """큰 숫자 여러 개를 한 줄로 늘어놓은 띠. items = [("59,946명", "분석한 사용자"), ...]"""
    cells = "".join(f'<div class="stat-item"><div class="stat-num">{esc(num)}</div>'
                    f'<div class="stat-label">{esc(label)}</div></div>' for num, label in items)
    return f'<div class="stat-band">{cells}</div>'


def flow_row(steps, numbered=False, tint=False):
    """단계를 화살표(→)로 이어서 가로로 보여준다.

    steps    : [(아이콘, 제목, 설명, 작은 핵심 문구), ...]   (핵심 문구는 없으면 "")
    numbered : True 면 아이콘 대신 1, 2, 3 번호를 붙임 (순서가 중요한 흐름일 때)
    tint     : True 면 옅은 핑크 배경 (다른 카드 안에 넣을 때)
    """
    step_class = "flow-step tint" if tint else "flow-step"
    html_parts = []
    for i, (icon, title, desc, meta) in enumerate(steps, start=1):
        badge = (f'<div class="flow-badge">{i}</div>' if numbered
                 else f'<div class="flow-badge icon">{icon}</div>')
        meta_html = f'<div class="flow-meta">{esc(meta)}</div>' if meta else ""
        html_parts.append(f'<div class="{step_class}">{badge}<div class="flow-title">{esc(title)}</div>'
                          f'<div class="flow-desc">{esc(desc)}</div>{meta_html}</div>')
        if i < len(steps):
            html_parts.append('<div class="flow-arrow">→</div>')
    return f'<div class="flow-row">{"".join(html_parts)}</div>'


def flow_card(title, subtitle, steps, numbered=False):
    """제목이 붙은 카드 안에 단계 흐름을 넣은 것"""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>{flow_row(steps, numbered, tint=True)}</div>')


def chip_card(title, subtitle, chips):
    """작은 알약(칩) 여러 개를 나열한 카드. chips = [(이름, 한 줄 설명), ...]"""
    body = "".join(f'<span class="chip"><b>{esc(name)}</b> {esc(role)}</span>' for name, role in chips)
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div><div>{body}</div></div>')


def heatmap_card(title, subtitle, row_labels, col_labels, rates, counts=None, footer=""):
    """칸마다 값의 크기에 따라 핑크색 진하기가 달라지는 표(히트맵).

    rates  : rates[행][열] = 이탈률(%)  — 값이 클수록 진한 핑크
    counts : counts[행][열] = 그 칸의 사람 수 (없어도 됨)
    """
    flat = [v for row in rates for v in row]
    low, high = min(flat), max(flat)
    head = "".join(f"<th>{esc(c)}</th>" for c in col_labels)
    body = ""
    for r, label in enumerate(row_labels):
        cells = ""
        for c, rate in enumerate(rates[r]):
            # 값이 클수록 진하게. (가장 작은 값은 아주 옅게, 가장 큰 값은 가장 진하게)
            alpha = 0.10 + 0.85 * (rate - low) / (high - low) if high > low else 0.5
            text_color = "#ffffff" if alpha > 0.55 else "#5a2d3c"      # 진한 칸은 흰 글씨
            n_html = f'<div class="heat-n">{counts[r][c]:,}명</div>' if counts else ""
            cells += (f'<td><div class="heat-cell" style="background:rgba(255,79,129,{alpha:.2f});'
                      f'color:{text_color}">{rate:.1f}%{n_html}</div></td>')
        body += f'<tr><th class="heat-row">{esc(label)}</th>{cells}</tr>'
    foot_html = f'<div class="dash-foot">{esc(footer)}</div>' if footer else ""
    return (f'<div class="dash-card"><div class="dash-title">{esc(title)}</div>'
            f'<div class="dash-sub">{esc(subtitle)}</div>'
            f'<table class="heat-table"><thead><tr><th></th>{head}</tr></thead><tbody>{body}</tbody></table>'
            f'{foot_html}</div>')


def persona_card(face_html, name, level, level_text, story, headline_text, headline_rate, headline_n,
                 traits, actions):
    """가상 사용자(페르소나) 카드 한 장.

    face_html     : 얼굴 <img> HTML (avatars.single_face 가 만들어 줌)
    level         : high / mid / low  (알약과 숫자 색을 정해요)
    headline_*    : 이 유형의 대표 그룹 설명과 그 그룹의 실제 이탈률, 사람 수
    traits        : [(특징 이름, 이탈률 %), ...]  각 특징 하나만의 이탈률
    actions       : ["추천 전략 이름", ...]
    """
    trait_html = "".join(f'<span class="chip">{esc(label)} <b>{rate:.1f}%</b></span>' for label, rate in traits)
    action_html = "".join(f'<span class="chip chip-pink">{esc(a)}</span>' for a in actions)
    return (
        '<div class="persona-card"><span class="persona-ribbon">가상 사용자</span>'
        f'<div class="persona-top"><div>{face_html}</div><div>'
        f'<span class="tag tag-{level}">{esc(level_text)}</span>'
        f'<div class="persona-name">{esc(name)}</div></div></div>'
        f'<div class="persona-story">{esc(story)}</div>'
        f'<div class="persona-stat"><span class="persona-rate {level}">{headline_rate:.1f}%</span>'
        f'<span class="persona-stat-text">{esc(headline_text)}<br>실제 이탈률 · {headline_n:,}명 기준</span></div>'
        f'<div class="preview-label">함께 보면 좋은 신호 (각각의 이탈률)</div><div>{trait_html}</div>'
        f'<div class="preview-label" style="margin-top:8px">이렇게 도와주세요</div><div>{action_html}</div></div>'
    )
