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
    """우선 관리 대상 명단. (전략 카드 아래, 맨 마지막에 놓아요)"""
    if result["n"] == 0:
        return
    table_rows = [(f"#{uid}", tier, f"{prob * 100:.1f}%", _reason_base_name(reason) or "-", _strategy_for_reason(reason))
                 for uid, tier, prob, reason in result["rows"]]
    show(table_card(f"우선 관리 대상 (이탈 확률 높은 순 {len(table_rows)}명)",
                    f"현재 조건의 {risk_label} 사용자 {result['n']:,}명 중 이탈 확률이 가장 높은 사용자예요. 정렬: 이탈 확률 ↓",
                    ["익명 프로필 ID", "위험 등급", "이탈 확률", "주요 위험 신호", "추천 전략"], table_rows))
    show(note_box(facts.SEGMENT_LIST_DISCLAIMER))


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

    # ③ 추천 전략
    show(section_title("추천 전략"))
    for icon, title, text in level["actions"]:
        show(action_card(icon, title, text))

    # ④ 우선 관리 대상 명단
    if result:
        _render_segment_list(result, risk_label)


def render():
    # 화면 제목
    show(page_header("RETENTION STRATEGY", "위험 수준별 리텐션 전략",
                     "예측된 이탈 위험에 따라 운영자가 취할 수 있는 조치를 제안합니다."))

    st.caption(db.cache_status_caption())

    show(note_box("위험 수준(Low / Medium / High)을 나누는 확률 기준은 최종 모델의 결과를 확인한 뒤에 정해요. "
                  "SERVICE 화면에서 예측한 위험 수준을 아래에서 골라서 보세요."))

    # ⚠️ st.tabs 대신 하나만 고르는 선택 컨트롤을 써요. st.tabs 는 '보이는 탭만' 계산하는 게
    # 아니라, with tab: 안의 코드를 탭마다 전부 실행해요. High 탭만 보고 있어도 실제로는
    # High·Medium·Low 세 번 다 db.query_segment() 가 실행되는 걸 직접 확인했어요. 이러면
    # 필터 하나만 바꿔도 DB에 세 번 쏘는 셈이라, 지금 고른 등급 하나만 그리게 바꿨어요.
    _segmented = getattr(st, "segmented_control", None)
    if _segmented is not None:
        selected_tab = _segmented("위험 수준", [level["tab"] for level in facts.LEVELS],
                                  default=facts.LEVELS[0]["tab"], label_visibility="collapsed",
                                  key="retention_level_select")
    else:      # 옛 Streamlit 버전엔 segmented_control 이 없어서, 라디오로 대신해요
        selected_tab = st.radio("위험 수준", [level["tab"] for level in facts.LEVELS],
                                horizontal=True, label_visibility="collapsed",
                                key="retention_level_select")
    level = next((lv for lv in facts.LEVELS if lv["tab"] == selected_tab), facts.LEVELS[0])
    _render_level(level)

    # 운영할 때 주의할 점
    show(note_box("예측 신호는 이탈의 '원인'이 아니라 함께 나타나는 '경향'이에요. "
                  "그래서 전략은 일부 사용자에게 먼저 시험(A/B 테스트)해서 효과를 확인한 뒤 넓혀 가는 것을 권장해요."))

    # 실제 서비스 도입 후 A/B 테스트 검증 계획
    _ab_test_section()