"""INSIGHT 화면 — 이탈 위험 사용자 분석 대시보드 (page_insight.py)

[이 화면은 뭘 보여주나요?]
플랫폼 운영자(관리자)가 "어떤 사용자가 이탈 위험이 높은지" 한눈에 보는 분석 화면입니다.
내용이 많아서 '맨 위 요약'과 '탭 4개'로 나눠 놓았어요.

  맨 위  : 핵심 발견 3가지 요약 + 핵심 숫자 4개
  탭 1   : 핵심 신호      — 이탈이 많은 그룹과 적은 그룹의 이탈률 비교
  탭 2   : 자기소개 · 프로필 — 자기소개 '개수 x 길이' 표, 프로필 완성도, 자주 비워두는 항목
  탭 3   : 가상 사용자 유형 — 분석 결과를 조합해 만든 '가상 사용자' 카드 4장 (얼굴 포함)
  탭 4   : 모델 · 그룹별   — 위험군 분포, 모델이 중요하게 본 항목(SHAP), 연령대 등 그룹별 이탈률

[숫자는 어디서 오나요?]
- 요약, 탭 1~3, 탭 4의 SHAP: project_facts.py 에 적어 둔 값.
  팀 노트북(02_essay_deep_experiment)의 Train 데이터(44,959명) EDA 결과와 노션 결과서 기준이에요.
- 탭 4의 그룹별 이탈률: data 폴더의 데이터 파일을 읽어서 직접 계산 (insight_data.py).
  파일이 없으면 앱이 멈추는 대신 '준비 중' 카드가 나옵니다.

app.py 에서 render() 를 호출하면 이 화면이 그려져요.
"""
import streamlit as st

import project_facts as facts
from avatars import single_face
from insight_data import (LIFESTYLE_OPTIONS, by_age, by_essay_count, by_lifestyle, by_status,
                          load_dataset, overall_rate)
from ui_parts import (check_list_card, heatmap_card, kpi_card, note_box, page_header, persona_card,
                      placeholder_card, rank_list_card, rate_bars_card, section_title, show, signal_card,
                      takeaway_band)


def _chart(title, subtitle, rows, baseline):
    """계산 결과(rows)가 있으면 막대그래프 카드, 없으면 '준비 중' 카드를 만든다."""
    if not rows:
        return placeholder_card(title, "이 항목을 계산할 데이터가 없어요.")
    return rate_bars_card(title, subtitle, rows, baseline=baseline)


def _summary_items():
    """맨 위 '핵심 발견 3가지'. 숫자는 모두 project_facts.py 에서 가져와요."""
    comp, essay, kids = facts.KEY_SIGNALS[0], facts.KEY_SIGNALS[1], facts.KEY_SIGNALS[2]
    grid_low, grid_high = facts.ESSAY_GRID_RATES[3][0], facts.ESSAY_GRID_RATES[3][4]
    return [
        (f"{comp['high_rate'] / comp['low_rate']:.1f}배",
         "프로필을 덜 채울수록 떠나요",
         f"가장 덜 채운 구간 {comp['high_rate']:.1f}% vs 가장 많이 채운 구간 {comp['low_rate']:.1f}%"),
        (f"{grid_low:.0f}% → {grid_high:.0f}%",
         "자기소개는 '길이'가 더 말해줘요",
         f"같은 10칸이라도 칸당 50자 이하 {grid_low:.1f}%, 700자 초과 {grid_high:.1f}%"),
        (f"{kids['high_rate'] / kids['low_rate']:.1f}배",
         "빈칸도 하나의 신호예요",
         f"자녀 항목을 비워 두면 {kids['high_rate']:.1f}%, 답하면 {kids['low_rate']:.1f}%"),
    ]


# ---------------------------------------------------------
# 탭 1: 핵심 신호
# ---------------------------------------------------------
def _tab_signals():
    show(section_title("핵심 신호 한눈에",
                       "이탈이 많은 쪽과 적은 쪽의 이탈률을 비교했어요. 오른쪽 위 숫자는 몇 배 차이인지를 뜻해요."))
    left, right = st.columns(2, gap="large")
    for i, s in enumerate(facts.KEY_SIGNALS):
        with (left if i % 2 == 0 else right):        # 왼쪽/오른쪽 칸에 번갈아 놓기
            show(signal_card(s["title"], s["high_label"], s["high_rate"], s["low_label"], s["low_rate"]))


# ---------------------------------------------------------
# 탭 2: 자기소개 · 프로필
# ---------------------------------------------------------
def _tab_essay():
    show(section_title("자기소개는 '개수'보다 '길이'가 더 말해줘요",
                       f"팀 분석(학습용 데이터 {facts.TRAIN_USERS:,}명)에서 나온 결과예요."))
    a, b = st.columns(2, gap="large")
    with a:
        # 색이 진할수록 이탈률이 높은 칸이에요.
        show(heatmap_card("자기소개 작성 칸 수 × 칸당 평균 글자 수",
                          "세로는 몇 칸을 썼는지, 가로는 한 칸당 평균 글자 수예요. 진한 핑크일수록 이탈률이 높아요.",
                          facts.ESSAY_GRID_ROWS, facts.ESSAY_GRID_COLS,
                          facts.ESSAY_GRID_RATES, facts.ESSAY_GRID_COUNTS,
                          footer="사람 수가 100명대인 칸은 우연일 수 있으니 참고만 하세요."))
    with b:
        rows = [{"label": name, "rate": rate, "n": n} for name, rate, n in facts.COMPLETENESS_GROUPS]
        show(rate_bars_card("프로필 완성도 구간별 이탈률",
                            "프로필 17개 항목 중 채운 비율을 5구간으로 나눴어요. 구간마다 사람 수는 달라요.",
                            rows, baseline=facts.CHURN_RATE))
    e10_low = facts.ESSAY_GRID_RATES[3][0]     # 10칸을 다 써도 칸당 50자 이하일 때
    e10_high = facts.ESSAY_GRID_RATES[3][4]    # 10칸을 다 쓰고 칸당 700자 초과일 때
    show(note_box(f"같은 10칸을 채워도 칸당 평균이 50자 이하면 이탈률이 {e10_low:.1f}%, 700자를 넘으면 {e10_high:.1f}%예요. "
                  "그래서 '몇 칸을 썼는지'뿐 아니라 '얼마나 성의 있게 썼는지'도 함께 봤어요."))

    show(section_title("비어 있는 칸도 하나의 정보예요",
                       "사용자들이 자주 비워두는 항목과, 빈칸을 어떻게 다뤘는지 정리했어요."))
    c1, c2 = st.columns(2, gap="large")
    with c1:
        rows = [{"label": name, "rate": rate} for name, rate in facts.MISSING_RATES]
        show(rate_bars_card("항목별로 비워둔 사용자 비율", "막대가 길수록 응답하지 않은 사용자가 많은 항목이에요.",
                            rows, hot_labels=["소득", "자녀 희망", "자녀 유무"]))
    with c2:
        kids = facts.KEY_SIGNALS[2]
        show(check_list_card("빈칸은 이렇게 다뤘어요", "지우거나 평균값으로 채우지 않고 그대로 살렸어요.", [
            ("글자로 된 항목", "'응답하지 않음(not_disclosed)'이라는 별도의 값으로 남겨요."),
            ("숫자로 된 항목", "빈칸 그대로 두고, CatBoost 가 빈칸을 직접 다루게 해요."),
            ("자녀 항목", "무응답 여부를 따로 표시(has_kids_na)해요. 무응답이면 이탈률이 "
                      f"{kids['high_rate']:.1f}%, 응답하면 {kids['low_rate']:.1f}%예요."),
            ("소득", "비공개(-1)를 실제 소득처럼 계산하지 않도록 빈칸으로 바꿔요."),
        ]))


# ---------------------------------------------------------
# 탭 3: 가상 사용자 유형 (페르소나)
# ---------------------------------------------------------
def _tab_personas():
    # 분석에서 이탈률 차이가 컸던 특징들을 조합해서 '이런 유형의 사용자'를 그려 봤어요.
    # 실제 사람이 아니라 이해를 돕기 위한 예시이고, 얼굴은 avatars.py 가 그려요.
    show(section_title("이런 사용자가 위험해요",
                       "분석에서 이탈률 차이가 컸던 특징을 조합해 만든 '가상 사용자' 유형이에요. "
                       "큰 숫자는 그 유형의 실제 이탈률이고, 아래 신호의 숫자는 각 특징 하나만의 이탈률이에요."))
    pl, pr = st.columns(2, gap="large")
    for i, persona in enumerate(facts.PERSONAS):
        gender, age, idx = persona["face"]
        card = persona_card(single_face(gender, age, size=72, idx=idx, bg=persona["bg"]),
                            persona["name"], persona["level"], persona["level_text"], persona["story"],
                            persona["headline_text"], persona["headline_rate"], persona["headline_n"],
                            persona["traits"], persona["actions"])
        with (pl if i % 2 == 0 else pr):
            show(card)
    show(note_box("얼굴과 나이는 카드를 구분하기 위한 꾸밈이에요. 이탈과 관련 있는 것은 프로필을 얼마나 성의 있게 채웠는지예요. "
                  "'이렇게 도와주세요'는 RETENTION 화면의 전략 중에서 어울리는 것을 고른 제안이에요."))


# ---------------------------------------------------------
# 탭 4: 모델 · 그룹별
# ---------------------------------------------------------
def _tab_model_groups(df, has_data, churn_rate):
    # 위험군 분포는 '모델이 사용자마다 계산한 확률'이 있어야 만들 수 있어서, 모델 연결 후 채웁니다.
    show(section_title("위험군 분포와 주요 예측 신호"))
    p, q = st.columns(2, gap="large")
    with p:
        show(placeholder_card("전체 위험군 분포 (Low / Medium / High)",
                              "모델이 연결되면 전체 사용자를 위험 수준별로 나눈 비율이 여기에 표시돼요."))
    with q:
        show(rank_list_card("모델이 중요하게 본 항목 TOP 5",
                            f"{facts.MODEL_NAME} 모델의 SHAP 분석 결과 (영향이 큰 순서)",
                            facts.SHAP_RANKING,
                            footer="예측에 기여한 정도이며, 이탈의 원인을 뜻하지는 않아요. 최종 모델이 정해지면 바뀔 수 있어요."))

    show(section_title("그룹별 이탈률",
                       "막대가 길수록 이탈률이 높아요. 점선은 전체 평균이고, 평균보다 높은 그룹은 진한 핑크로 칠했어요."))
    if not has_data:
        show(placeholder_card("그룹별 이탈률 차트",
                              "data 폴더에서 데이터 파일을 찾지 못했어요. okcupid_cleaned.csv.gz "
                              "(또는 okcupid_profiles.csv)를 data 폴더에 넣으면 연령대, 관계 상태, 자기소개 작성량, "
                              "라이프스타일별 그래프가 자동으로 나타나요."))
        return

    g1, g2 = st.columns(2, gap="large")
    with g1:
        show(_chart("연령대별", "나이 구간별 이탈률", by_age(df), churn_rate))
    with g2:
        show(_chart("관계 상태별", "프로필에 적은 현재 관계 상태별 이탈률", by_status(df), churn_rate))

    g3, g4 = st.columns(2, gap="large")
    with g3:
        show(_chart("자기소개 작성량별", "자기소개 10칸 중 몇 칸을 채웠는지", by_essay_count(df), churn_rate))
    with g4:
        # 라이프스타일은 항목(음주/흡연/약물/식단)을 골라서 볼 수 있게 했어요.
        # st.selectbox 로 고른 값이 option 에 담기고, 바꿀 때마다 아래 그래프가 다시 그려져요.
        option = st.selectbox("라이프스타일 항목 선택", list(LIFESTYLE_OPTIONS), key="insight_lifestyle")
        show(_chart(f"{option}별", f"'{option}' 항목 응답별 이탈률 (응답하지 않은 사용자는 '미응답')",
                    by_lifestyle(df, option), churn_rate))


def render():
    # ── 1) 화면 제목 ─────────────────────────────────────
    show(page_header("USER INSIGHT", "이탈 위험 사용자 분석",
                     "프로필 정보와 장기 미접속(이탈)의 관계를 한눈에 확인하는 관리자용 대시보드입니다."))

    # ── 2) 핵심 발견 3가지 (맨 위 요약) ──────────────────
    show(takeaway_band("핵심 발견 3가지", _summary_items()))

    # data 폴더의 파일을 읽습니다. (없으면 None)
    df = load_dataset()
    has_data = df is not None

    # 파일이 있으면 실제 값을, 없으면 문서에 적힌 값을 보여줍니다.
    users = len(df) if has_data else facts.TOTAL_USERS
    churn_rate = overall_rate(df) if has_data else facts.CHURN_RATE

    # ── 3) 핵심 숫자 4개 ────────────────────────────────
    # st.columns(4) : 화면을 같은 너비 4칸으로 나눔
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        show(kpi_card("분석 사용자", f"{users:,}명", f"{facts.DATASET_NAME} 프로필"))
    with k2:
        show(kpi_card("이탈률", f"{churn_rate:.1f}%", f"마지막 접속 후 {facts.CHURN_DAYS}일 이상 미접속"))
    with k3:
        show(kpi_card("이탈 기준", f"{facts.CHURN_DAYS}일", "데이터 안에서 가장 최근 접속 시각이 기준"))
    with k4:
        show(kpi_card("사용 항목", f"{facts.FEATURE_COUNT}개", "프로필 + 자기소개에서 만든 feature"))

    # ── 4) 탭 4개 ───────────────────────────────────────
    # st.tabs : 탭(상단 메뉴)으로 내용을 나눠서 보여줍니다. 한 화면에 다 쌓으면 너무 길어서 나눴어요.
    t1, t2, t3, t4 = st.tabs(["핵심 신호", "자기소개 · 프로필", "가상 사용자 유형", "모델 · 그룹별 분석"])
    with t1:
        _tab_signals()
    with t2:
        _tab_essay()
    with t3:
        _tab_personas()
    with t4:
        _tab_model_groups(df, has_data, churn_rate)

    # ── 5) 읽을 때 주의할 점 (탭 밖, 항상 보임) ──────────────
    note = ("지역별 분석은 뺐어요. 사용자의 99.8%가 캘리포니아라서 지역 간 비교가 의미 없기 때문이에요. "
            "또 이 화면의 차이는 '함께 나타나는 경향'이지 이탈의 원인이 아니에요.")
    if has_data:
        note += f" '그룹별 이탈률'은 data 폴더의 파일({users:,}명)로 직접 계산한 값이에요."
    show(note_box(note))
