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
                      rate_bars_card, section_title, show, table_card, tag)

def _reason_base_name(reason_text):
    """'자기소개 작성 칸 수 (위험↑)' -> '자기소개 작성 칸 수' (괄호 뒤 화살표 표시를 뗀다)"""
    if not reason_text:
        return None
    return re.sub(r"\s*\([^)]*\)\s*$", "", reason_text).strip()


_TIER_KEY = {"High": "high", "Medium": "mid", "Low": "low"}


def _strategy_for_reason(reason_text, risk_tier):
    """위험 신호(reason_1) -> 이 사람이 받는 전략 문구 (표에 한 칸으로 보여줄 문자열).

    ⚠️ SERVICE 화면과 같은 원칙: 등급 공통 혜택(facts.RISK_BASELINE_BENEFIT)은 신호가 뭐든
    예외 없이 받고, 신호가 실제로 개입 가능한(프로필을 고쳐서 개선할 수 있는) 것이면 그 위에
    개인화 안내를 '+' 로 덧붙여서 같이 보여줘요. (전에는 개입 가능한 사람은 개인화 안내만
    한 칸에 보여서, "이 사람들은 공통 혜택을 안 받나?"처럼 보이는 문제가 있었어요 — 실제로는
    둘 다 받는데, 표에 하나만 보여서 그렇게 보인 거예요. 이제 표에도 둘 다 보이게 했어요.)
    """
    base = _reason_base_name(reason_text)
    baseline_name, _ = facts.RISK_BASELINE_BENEFIT.get(_TIER_KEY.get(risk_tier, "mid"),
                                                        facts.RISK_BASELINE_BENEFIT["mid"])
    if base in facts.ACTIONABLE_SIGNALS:
        action_name, _ = facts.SIGNAL_ACTIONS.get(base, facts.SIGNAL_ACTIONS_DEFAULT)
        return f"{baseline_name} + {action_name}"
    return baseline_name


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


# A/B 시뮬레이션에서 쓰는 가정값. 자기소개 분량별 관측 이탈률 격차(100자 이하 55.04% vs 초과 24.01%
# = 31.03%p)의 절반을 '전략 효과'로 가정해요. 상관관계를 그대로 인과 효과로 쓰면 과장이라서요.
# (이 절반 비율은 데이터로 증명한 값이 아니라 팀이 정한 보수적 가정이에요)
_AB_OBSERVED_GAP_PP = 31.03

# A/B 시뮬레이션의 '전략 쓴 그룹' 효과 가정. 두 가지를 버튼으로 바꿔 볼 수 있어요. (둘 다 실제 효과가 아니라 가정값)
#  · 낙관: 자기소개 분량별 관측 이탈률 격차(31.03%p)의 절반. 상관관계를 그대로 인과 효과로 쓰면 과장이라 절반만 반영
#  · 보수: 팀 검정력 분석(약 1,839명 표본)에서 80% 넘는 확률로 발견 가능한 최소 효과 크기. '예상 효과'가 아니라 '검증 가능한 최소 크기'
_AB_SCENARIOS = {
    "낙관 시나리오 · 15.5%p": {
        "effect": 0.1551, "label": "15.5%p",
        "basis": (f"관측 이탈률 격차 {_AB_OBSERVED_GAP_PP:.2f}%p의 절반(약 15.5%p)을 전략 효과로 가정한 값이에요. "
                  "관찰된 차이는 상관관계라서 전부 효과로 보면 과장이 되기 때문에 절반만 반영했어요."),
    },
    "보수 시나리오 · 7%p": {
        "effect": 0.07, "label": "7%p",
        "basis": ("팀의 검정력 분석에서 '현재 표본(약 1,839명)으로 80% 넘는 확률로 발견할 수 있는 최소 효과 크기'인 "
                  "7%p를 가정한 값이에요. 7%p는 예상되는 효과가 아니라, 실험으로 확인할 수 있는 최소 크기예요."),
    },
}

# 배정과 구제 여부를 random() 대신 user_id 해시로 정해요. 그래야 화면을 새로고침해도 결과가 안 바뀌어요.
# (abs(hashtext(...)) 는 아주 드물게 정수 범위를 넘을 수 있어서 bigint 로 바꿔 계산해요)
def _ab_sim_sql(effect):
    return f"""
WITH high AS (
    SELECT user_id, churn_actual, churn_prob,
           CASE WHEN mod(abs(hashtext(user_id::text || 'arm')::bigint), 2) = 0
                THEN 'treatment' ELSE 'control' END AS arm,
           mod(abs(hashtext(user_id::text || 'rescue')::bigint), 10000) / 10000.0 AS u
    FROM predictions
    WHERE risk_tier = 'High'
),
base AS (SELECT AVG(churn_actual) AS churn_rate FROM high WHERE arm = 'control'),
sim AS (
    SELECT h.arm, h.churn_prob,
           CASE WHEN h.arm = 'control' THEN 1 - h.churn_actual
                WHEN h.churn_actual = 0 THEN 1
                WHEN h.u < LEAST(1.0, {effect} / b.churn_rate) THEN 1
                ELSE 0 END AS retained
    FROM high h CROSS JOIN base b
)
SELECT arm, COUNT(*) AS n,
       AVG(churn_prob) AS avg_prob,
       AVG(retained) AS retained_rate
FROM sim GROUP BY arm ORDER BY arm
"""


def _dot_grid(stay_rate_pct):
    """사용자 100명을 점 100개로 그려요. 30일 뒤에도 남은 사람은 진한 분홍, 떠난 사람은 연한 회색.
    (마크다운이 들여쓰기를 코드 블록으로 읽지 않게 HTML 을 한 줄로 이어 붙여요)"""
    stay = max(0, min(100, round(stay_rate_pct)))
    dots = "".join(
        f'<span style="aspect-ratio:1;border-radius:50%;background:{"#e42560" if i < stay else "#ecdde3"}"></span>'
        for i in range(100))
    return (f'<div style="display:grid;grid-template-columns:repeat(10,1fr);gap:6px;'
            f'max-width:280px">{dots}</div>')


def _people_chart(c_ret, t_ret):
    """'High 위험 사용자 100명이 있다면' 그림: 전략 안 쓴 그룹 vs 쓴 그룹을 나란히 보여줘요."""
    def side(title, tag_text, ret, tag_color):
        stay = round(ret)
        return (f'<div><div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<b style="font-size:17px;color:#2b2225">{title}</b>'
                f'<span style="font-size:12px;font-weight:800;color:#fff;background:{tag_color};'
                f'padding:3px 10px;border-radius:999px">{tag_text}</span></div>'
                f'<div style="font-size:15px;color:#8b7b81;margin-bottom:12px">'
                f'남은 사람 <b style="color:#e42560;font-size:22px">{stay}명</b> · 떠난 사람 <b>{100 - stay}명</b></div>'
                f'{_dot_grid(ret)}</div>')
    body = (f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:36px">'
            f'{side("전략 안 쓴 그룹", "실제 과거 기록", c_ret, "#8b7b81")}'
            f'{side("전략 쓴 그룹", "가정", t_ret, "#e42560")}</div>')
    legend = ('<div style="margin-top:14px;font-size:14px;color:#8b7b81">'
              '<span style="color:#e42560">●</span> 30일 뒤에도 앱에 남은 사람 &nbsp;&nbsp;'
              '<span style="color:#d9c3cb">●</span> 떠난 사람</div>')
    show('<div class="dash-card"><div class="dash-title">High 위험 사용자 100명이 있다면</div>'
         '<div class="dash-sub">30일 뒤에 몇 명이 남을까요? 점 하나 = 사용자 1명이에요.</div>'
         f'{body}{legend}</div>')


def _ab_test_section():
    """A/B 테스트 운영 시뮬레이션 화면.

    ⚠️ 이 결과는 실제 실험이 아니라 가정 기반 시뮬레이션이에요.
      - 배정(누가 전략 쓴/안 쓴 그룹인지): 무작위 (가정 없음)
      - 전략 안 쓴 그룹(대조군): 실제 과거 기록 (개입이 없었으니 진짜 값)
      - 전략 쓴 그룹(처리군): 가정 (전략을 적용했다면 이탈이 이만큼 줄었을 것이라는 시나리오)
    카드 3개에 인원·시작 위험도까지 담아서 표는 뺐어요. (같은 숫자가 카드와 표에 두 번 나오던 걸 정리)
    """
    show(section_title(
        "A/B 테스트 운영 시뮬레이션",
        "High 위험군을 무작위로 반으로 나눠, 한쪽에만 전략을 썼다고 가정하고 30일 뒤 얼마나 남는지 비교해요.",
    ))

    scenario_name = _pick("시나리오", list(_AB_SCENARIOS), key="ab_scenario")
    scenario = _AB_SCENARIOS[scenario_name]
    st.caption("전략 쓴 그룹의 효과를 어떻게 가정하느냐에 따라 결과가 달라져요. 두 가지를 바꿔 가며 비교해 보세요.")

    df = db.run_query(_ab_sim_sql(scenario["effect"])) if db.is_connected() else None
    if df is None or len(df) < 2:
        show(placeholder_card("시뮬레이션 결과", db.NOT_CONNECTED_HINT if not db.is_connected()
                              else "DB에는 연결됐지만 시뮬레이션을 계산하지 못했어요. predictions 테이블을 확인해 주세요."))
    else:
        rows = {r["arm"]: r for _, r in df.iterrows()}
        ctrl, treat = rows["control"], rows["treatment"]
        c_ret, t_ret = float(ctrl["retained_rate"]) * 100, float(treat["retained_rate"]) * 100

        k1, k2, k3 = st.columns(3, gap="medium")
        with k1:
            show(kpi_card("전략 안 쓴 그룹 · 30일 뒤 남은 비율", f"{c_ret:.1f}%",
                          f"대조군 {int(ctrl['n']):,}명 · 실제 과거 기록"))
        with k2:
            show(kpi_card("전략 쓴 그룹 · 30일 뒤 남은 비율", f"{t_ret:.1f}%",
                          f"처리군 {int(treat['n']):,}명 · 가정 시나리오"))
        with k3:
            show(kpi_card("차이", f"+{t_ret - c_ret:.1f}%p",
                          f"가정한 효과 약 {scenario['label']} 근처 · 시작 위험도 {float(ctrl['avg_prob']) * 100:.1f}% vs "
                          f"{float(treat['avg_prob']) * 100:.1f}%로 비슷"))
        _people_chart(c_ret, t_ret)
        show(note_box(
            f"전략 안 쓴 그룹은 실제 과거 결과이고, 전략 쓴 그룹은 {scenario['basis']} "
            f"두 시나리오 모두 전략 효과를 증명하는 결과가 아니라, 실제 도입 시 이런 결과 화면이 나온다는 시뮬레이션이에요."))

    with st.expander("실제 서비스 도입 후 검증 절차 보기"):
        show(check_list_card(
            "실제 서비스 도입 후 검증 절차",
            "가정값이 아니라 실제 행동 로그가 쌓인 뒤에는 아래 순서로 같은 결과를 채워서 비교합니다.",
            [
                ("1. 대상 선정", "SQL로 동일한 조건의 위험군을 선정합니다. 예: High 위험군 중 자기소개 미작성 사용자"),
                ("2. 무작위 배정", "대상자를 처리군과 대조군에 무작위로 나누고 두 집단의 시작 위험도가 비슷한지 확인합니다."),
                ("3. 전략 적용", "처리군에만 프로필 작성 가이드·젤리 보상 등의 전략을 적용하고 대조군은 기존 서비스를 유지합니다."),
                ("4. 실제 결과 비교", "30일 잔존율·30일 이탈률·프로필 수정률·7일 재방문율을 실제 로그로 비교합니다."),
            ],
        ))

# 위험 수준별 전략 데이터(LEVELS)는 project_facts.py 로 옮겼어요. (service_view.py 도 같은 걸 써요)


def _segment_filters(key_suffix):
    """조건 선택창 4개(완성도/자기소개/관계 상태/연령대)를 그리고, 고른 값을 돌려준다."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        comp_kr = st.selectbox("프로필 완성도", list(_COMPLETENESS_OPTIONS), key=f"seg_comp_{key_suffix}")
    with c2:
        essay_kr = st.selectbox("자기소개 작성 수준", list(_ESSAY_OPTIONS), key=f"seg_essay_{key_suffix}")
    with c3:
        status_kr = st.selectbox("관계 상태", list(_STATUS_OPTIONS), key=f"seg_status_{key_suffix}")
    with c4:
        age_kr = st.selectbox("연령대", list(_AGE_OPTIONS), key=f"seg_age_{key_suffix}")
    essay_min, essay_max = _ESSAY_OPTIONS[essay_kr]
    age_min, age_max = _AGE_OPTIONS[age_kr]
    return {
        "completeness_tier": _COMPLETENESS_OPTIONS[comp_kr],
        "essay_min": essay_min, "essay_max": essay_max,
        "status": _STATUS_OPTIONS[status_kr],
        "age_min": age_min, "age_max": age_max,
    }


def _render_segment_summary(result, risk_label):
    """대상자 수 · 평균 이탈 확률 · 등급 비율 카드 3개 + 주요 위험 신호 막대. (데이터부터 먼저 보여줘요)"""
    if result["n"] == 0:
        show(placeholder_card("대상자 조회", f"현재 조건에 맞는 {risk_label} 사용자가 없어요. 조건을 조금 넓혀서 다시 찾아보세요."))
        return

    if result["n"] < 30:
        # 표본이 적으면 평균 확률·비율 같은 숫자가 우연히 크게 튈 수 있어요. (히트맵에 있는
        # "사람 수가 적으면 우연일 수 있다"는 안내와 같은 취지예요)
        show(note_box(f"⚠️ 표본이 {result['n']}명으로 적어요. 아래 숫자(평균 확률 등)는 우연에 의해 크게 흔들릴 수 있으니 참고만 하세요."))

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        show(kpi_card("대상자 수", f"{result['n']:,}명", "현재 탭 + 아래 필터 조건을 모두 만족한 사용자"))
    with k2:
        show(kpi_card("평균 이탈 확률", f"{result['avg_prob'] * 100:.1f}%", "현재 조회된 사용자들의 모델 예측 확률 평균"))
    with k3:
        tier_share = result.get("tier_share")
        tier_share_text = f"{tier_share * 100:.1f}%" if tier_share is not None else "-"
        show(kpi_card("위험군 비중", tier_share_text, f"같은 필터 조건 사용자 중 {risk_label} 비율"))

    if result["reasons"]:
        rows = [{"label": _reason_base_name(name) or "(기록 없음)", "rate": n / result["n"] * 100, "n": n}
                for name, n in result["reasons"]]
        show(rate_bars_card(f"{risk_label} 집단의 주요 이탈 신호",
                            "막대 길이 = 이 집단에서 해당 신호가 1순위 위험 요인이었던 사용자 비율입니다.",
                            rows, footer="막대 길이와 사람 수가 같은 기준이에요: 비율 = 해당 신호 인원 ÷ 현재 조회 인원."))


def _render_segment_list(result, risk_label):
    """우선 관리 대상 명단. (위험 순으로 상위 10명만 보여줘요 — 20줄은 화면이 너무 길어져서 줄였어요)"""
    if result["n"] == 0:
        return
    table_rows = [(f"#{uid}", tier, f"{prob * 100:.1f}%", _reason_base_name(reason) or "-",
                  _strategy_for_reason(reason, tier))
                 for uid, tier, prob, reason in result["rows"][:10]]
    show(table_card(f"우선 관리 대상 (이탈 확률 높은 순 {len(table_rows)}명)",
                    f"현재 조건의 {risk_label} 사용자 {result['n']:,}명 중 이탈 확률이 가장 높은 사용자예요.",
                    ["익명 프로필 ID", "위험 등급", "이탈 확률", "주요 위험 신호", "추천 전략"], table_rows))
    show(note_box(f"{facts.SEGMENT_LIST_DISCLAIMER} 예측 신호는 이탈의 '원인'이 아니라 함께 나타나는 '경향'이에요."))


def _render_level(level):
    """위험 수준 하나의 내용을 그린다.

    순서: ① 등급 요약 → ② 조건 필터 + 데이터(대상자 수·신호) → ③ 추천 전략 → ④ 우선 관리 대상 명단.
    전에는 '추천 전략'이 제일 먼저 나와서, 실제 숫자(대상자 수 등)를 보려면 한참 스크롤해야 했어요.
    데이터를 먼저 보여주고 그다음 "그래서 뭘 하면 되나"로 이어지게 순서를 바꿨어요. (이런 사용자가
    특히 위험해요' 같은 고정 EDA 카드는 이제 RETENTION 에서 빼고 INSIGHT 에만 남겼어요 — 여기서는
    이미 이 조건 그룹 실제 주요 신호를 보여주니, 같은 내용이 두 번 나오는 걸 피했어요)
    """
    risk_tier = level["name"].split()[0]
    risk_label = level["name"]
    key_suffix = level["kind"]

    # ① 위쪽: 위험 수준 표시(알약) + 한 줄 요약 + 목표
    show(f'<div class="level-head">{tag(level["name"], level["kind"])}'
         f'<span class="level-headline">{level["headline"]}</span></div>'
         f'<div class="level-goal">{level["goal"]}</div>')

    # ② 조건 필터 + 데이터
    show(section_title(f"{risk_label} 대상자 찾기",
                       f"현재 탭의 {risk_label} 사용자만 조회해요. 아래 조건을 추가하면 더 세분화할 수 있습니다."))
    if not db.is_connected():
        show(placeholder_card("대상자 조회", db.NOT_CONNECTED_HINT))
        result = None
    else:
        filters = _segment_filters(key_suffix)
        result = db.query_segment(risk_tier=risk_tier, limit=facts.SEGMENT_LIST_LIMIT, **filters)
        if result is None:
            show(placeholder_card("대상자 조회",
                                  "DB에는 연결됐지만 조회에 실패했어요. predictions 테이블이 있는지, "
                                  "컨테이너를 최신으로 띄웠는지 확인해 주세요."))
        else:
            _render_segment_summary(result, risk_label)

    # ③ 우선 관리 대상 명단
    if result:
        _render_segment_list(result, risk_label)

    # ④ 이 등급의 추천 전략 전체 (평소엔 접어 두고, 궁금할 때만 펼쳐요)
    with st.expander(f"{risk_label} 등급 추천 전략 전체 보기"):
        for icon, title, text in level["actions"]:
            show(action_card(icon, title, text))


def _pick(label, options, key, default_index=0):
    """하나만 고르는 선택 컨트롤. (옛 Streamlit 버전엔 segmented_control 이 없어서 라디오로 대신해요)
    st.tabs 는 탭 안의 코드를 전부 실행해서 DB를 여러 번 부르기 때문에, 지금 고른 화면 하나만 그리게 했어요."""
    seg = getattr(st, "segmented_control", None)
    if seg is not None:
        picked = seg(label, options, default=options[default_index], label_visibility="collapsed", key=key)
    else:
        picked = st.radio(label, options, index=default_index, horizontal=True,
                          label_visibility="collapsed", key=key)
    return picked if picked in options else options[default_index]     # 선택을 풀어서 None 이 돼도 첫 항목으로


def render():
    # 화면 제목
    show(page_header("RETENTION STRATEGY", "위험 수준별 리텐션 전략",
                     "예측된 이탈 위험에 따라 운영자가 취할 수 있는 조치를 제안합니다."))

    t = facts.RISK_THRESHOLDS
    st.caption(f"{db.cache_status_caption()}  ·  위험 등급 기준: High {t['high'] * 100:.0f}% 이상 · "
               f"Medium {t['mid'] * 100:.0f}~{t['high'] * 100:.0f}% · Low {t['mid'] * 100:.0f}% 미만")

    # 한 화면에 다 보여주면 너무 길어서, 두 화면으로 나눴어요.
    view = _pick("화면", ["대상자 · 전략", "A/B 시뮬레이션"], key="retention_view")
    if view == "A/B 시뮬레이션":
        _ab_test_section()
        return

    tabs = [level["tab"] for level in facts.LEVELS]
    selected_tab = _pick("위험 수준", tabs, key="retention_level_select")
    level = next((lv for lv in facts.LEVELS if lv["tab"] == selected_tab), facts.LEVELS[0])
    _render_level(level)