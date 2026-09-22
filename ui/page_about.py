"""ABOUT 화면 — 프로젝트 및 모델 정보 (page_about.py)

[이 화면은 뭘 보여주나요?]
이 서비스를 처음 보는 사람도 "무슨 프로젝트이고, 어떤 데이터로, 어떤 모델을 썼고, 한계는 뭔지"
이해할 수 있게 정리한 소개 화면입니다. 탭 4개로 나눴어요.
  1) 프로젝트      : 무엇을 하는 서비스인지, 누구를 위한 건지
  2) 데이터·Target : 어떤 데이터인지, '이탈'을 어떻게 정의했는지
  3) 모델          : 어떤 모델들을 비교했고 어떤 성적이 나왔는지
  4) 한계·확장     : 지금 데이터의 한계와 앞으로의 발전 방향

숫자와 긴 설명 문구는 project_facts.py 에서 가져옵니다. (최종 모델이 정해지면 그 파일만 고치면 돼요)
app.py 에서 render() 를 호출하면 이 화면이 그려져요.
"""
import streamlit as st

import project_facts as facts
from ui_parts import (check_list_card, chip_card, flow_card, kpi_card, note_box, page_header, rate_bars_card,
                      section_title, show, steps_card, table_card, text_card)


def _tab_project():
    """탭 1: 프로젝트 소개"""
    show(text_card("무엇을 하는 서비스인가요?", [
        "StayMatch 는 데이팅 플랫폼 운영사를 위한 '사용자 이탈 예측 · 리텐션 지원' 서비스입니다.",
        "Like, Match, Message 같은 행동 기록이 쌓이기 전인 신규 가입자도, 프로필 정보만으로 "
        "장기 미접속(이탈) 위험을 미리 알아볼 수 있는지 확인하는 프로젝트예요.",
    ]))

    # 만든 과정 흐름도: 데이터 -> 전처리 -> 모델링 -> 서비스
    # 내용은 project_facts.py 의 PIPELINE 에 있어서, 숫자가 바뀌면 그쪽만 고치면 돼요.
    show(flow_card("이 서비스는 이렇게 만들어졌어요", "데이터에서 화면까지 네 단계로 진행했어요.", facts.PIPELINE))

    # 사용한 기술 목록 (TECH_STACK 도 project_facts.py 에 있어요)
    show(chip_card("사용한 기술", "어떤 도구를 어디에 썼는지 정리했어요.", facts.TECH_STACK))

    c1, c2 = st.columns(2, gap="large")
    with c1:
        show(check_list_card("누구를 위한 서비스인가요?", "데이팅 플랫폼을 운영하는 사람들이에요.", [
            ("데이팅 플랫폼 운영사", "OkCupid, Tinder, 위피, 글램 같은 서비스"),
            ("서비스 기획자", "가입 초기 온보딩과 프로필 작성 정책을 개선"),
            ("CRM · 마케팅 담당자", "위험 수준에 맞는 알림과 혜택을 설계"),
            ("플랫폼 운영자", "위험 사용자 비율과 특징을 한눈에 확인"),
        ]))
    with c2:
        show(check_list_card("이렇게 활용해요", "프로필 입력부터 전략 선택까지 세 단계예요.", [
            ("1. 프로필 입력", "사용자의 나이, 직업, 자기소개 등을 입력해요."),
            ("2. 이탈 위험 예측", "이탈 확률을 계산해 Low / Medium / High 로 나눠요."),
            ("3. 리텐션 전략 선택", "위험 수준에 맞는 조치를 RETENTION 화면에서 확인해요."),
        ]))

    show(note_box("차별점: 행동 기록이 없다는 점을 약점으로만 보지 않고, 가입 직후 온보딩 단계에서도 "
                  "프로필만으로 이탈 위험을 판단할 수 있는지에 집중했어요."))


def _tab_data():
    """탭 2: 데이터와 Target(정답) 정의"""
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        show(kpi_card("사용자 수", f"{facts.TOTAL_USERS:,}명", f"{facts.DATASET_NAME} ({facts.DATASET_SOURCE})"))
    with k2:
        show(kpi_card("원본 컬럼", f"{facts.RAW_COLUMNS}개", "프로필 · 라이프스타일 · 자기소개 등"))
    with k3:
        show(kpi_card("수집 시기", facts.DATASET_COLLECTED, "샌프란시스코 베이에어리어"))
    with k4:
        show(kpi_card("이탈률", f"{facts.CHURN_RATE:.1f}%",
                      f"이탈 {facts.CHURN_USERS:,}명 / 유지 {facts.KEEP_USERS:,}명"))

    show(section_title("'이탈'은 이렇게 정의했어요",
                       "데이터에는 탈퇴 기록이 없어서, 마지막 접속 시각(last_online)으로 이탈을 만들었어요."))
    left, right = st.columns(2, gap="large")
    with left:
        show(text_card("Target 정의", [
            f"기준 시각: {facts.REFERENCE_TIME} (데이터 안에서 가장 최근 접속 시각)",
            f"이탈(1): 기준 시각보다 {facts.CHURN_DAYS}일 이상 이전에 마지막으로 접속한 사용자",
            f"유지(0): 최근 {facts.CHURN_DAYS}일 안에 접속한 사용자",
            "왜 30일일까요? 7일·14일은 잠깐 쉬는 사용자까지 이탈로 보게 되고, "
            "90일·180일은 이탈자가 너무 적어 모델이 배우기 어려워요. 30일은 데이팅 앱의 일반적인 "
            "재방문 주기를 넘기면서 이탈 비율(약 1 : 2.9)도 학습하기 좋은 수준이에요.",
        ]))
    with right:
        # 기준 일수별 이탈률. 30일만 진하게 칠해서 '우리가 고른 기준'을 보여줘요.
        rows = [{"label": name, "rate": rate} for name, rate in facts.THRESHOLD_TABLE]
        show(rate_bars_card("기준 일수에 따른 이탈률", "일수를 바꾸면 이탈률이 이렇게 달라져요.",
                            rows, hot_labels=[f"{facts.CHURN_DAYS}일"],
                            footer="진한 막대 = 우리가 고른 기준"))

    show(note_box("자기소개 원문은 모델에 그대로 넣지 않고, 작성한 칸 수 · 총 단어 수 · 평균 길이 같은 "
                  "숫자로 바꿔서 사용했어요. 비워 둔 항목도 '응답하지 않음'이라는 정보로 남겼어요."))

    show(note_box(f"전체 {facts.TOTAL_USERS:,}명을 학습용 {facts.TRAIN_USERS:,}명(75%)과 평가용 {facts.TEST_USERS:,}명(25%)으로 "
                  f"나눴어요. 두 그룹의 이탈 비율이 똑같이 {facts.CHURN_RATE:.1f}%가 되도록 맞춰서 나눴고, "
                  "모델은 학습용 데이터로만 배웠어요."))

    # 모델이 보는 25개 항목: project_facts.FEATURE_GROUPS 를 그룹별 칩 카드로 보여줍니다.
    show(section_title(f"모델이 보는 {facts.FEATURE_COUNT}개 항목",
                       "프로필 정보와, 프로필·자기소개를 얼마나 성실히 채웠는지에서 만든 항목이에요. "
                       "영문은 코드에서 쓰는 이름이에요."))
    subtitles = ["사용자 자신에 대한 기본 정보예요.",
                 "학력, 종교, 생활 습관에 대한 응답이에요.",
                 "자녀에 대한 응답이에요. 무응답인지 여부도 하나의 항목이에요.",
                 "얼마나 성실히 채웠는지를 나타내요. 20개 중 5개가 여기에 속해요."]
    g1, g2 = st.columns(2, gap="large")
    for i, ((name, items), sub) in enumerate(zip(facts.FEATURE_GROUPS, subtitles)):
        with (g1 if i % 2 == 0 else g2):
            # chip_card 는 (이름, 설명) 쌍을 받아서 '설명 이름' 모양의 칩으로 그려요.
            show(chip_card(f"{name} ({len(items)}개)", sub, [(desc, f"· {code}") for code, desc in items]))


def _tab_model():
    """탭 3: 모델 비교와 성적"""
    show(text_card(f"현재 채택 후보: {facts.MODEL_NAME}", [
        f"같은 {facts.FEATURE_COUNT}개 항목으로 6개 모델을 비교했고, 그중 {facts.MODEL_NAME} 의 성능이 가장 좋았어요. "
        "글자로 된 항목과 빈칸을 그대로 다룰 수 있고, SHAP 으로 예측 이유를 설명할 수 있다는 점도 선택 이유예요.",
    ]))

    # 모델 비교 표 (CatBoost 줄 강조)
    rows = [(name, f"{auc:.3f}", f"{rec:.3f}", f"{pre:.3f}", f"{f1:.3f}")
            for name, auc, rec, pre, f1 in facts.MODEL_COMPARISON]
    show(table_card("모델 비교", "분류 기준 확률은 모두 0.5예요. 숫자가 클수록 좋아요.",
                    ["모델", "ROC-AUC", "Recall", "Precision", "F1"], rows,
                    highlight_row=facts.SELECTED_MODEL_ROW))

    # 채택 후보의 상세 성적 (숫자 카드 3개 + 3개)
    m = facts.MODEL_METRICS
    show(section_title(f"{facts.MODEL_NAME} 상세 성적"))
    r1 = st.columns(3, gap="medium")
    for col, (label, sub) in zip(r1, [("ROC-AUC", "이탈/유지를 구분하는 전반적인 능력"),
                                      ("Recall", "실제 이탈자 중 찾아낸 비율"),
                                      ("Precision", "이탈로 예측한 사람 중 실제 이탈 비율")]):
        with col:
            show(kpi_card(label, f"{m[label]:.3f}", sub))
    r2 = st.columns(3, gap="medium")
    for col, (label, sub) in zip(r2, [("F1", "Recall 과 Precision 의 균형"),
                                      ("PR-AUC", "이탈자를 찾는 능력 (불균형 데이터에 적합)"),
                                      ("Accuracy", "전체 중 맞힌 비율")]):
        with col:
            show(kpi_card(label, f"{m[label]:.3f}", sub))

    show(note_box("이렇게 읽어요: Recall 이 약 70% 라서 실제 이탈자 10명 중 7명을 찾아내요. 대신 Precision 이 약 41% 라서 "
                  "이탈로 예측한 사람 중 절반 이상은 사실 이탈하지 않아요(오탐). 이탈자가 전체의 25.7% 로 적은 데이터라 "
                  "Accuracy 보다 Recall · PR-AUC 를 중심으로 봤어요."))
    show(note_box(f"5-Fold 교차검증 평균 ROC-AUC 는 {facts.CV_ROC_AUC:.3f} 예요. {facts.MODEL_CAVEAT}"))


def _tab_limits():
    """탭 4: 한계와 앞으로의 방향"""
    left, right = st.columns(2, gap="large")
    with left:
        show(check_list_card("지금 데이터의 한계", "결과를 해석할 때 꼭 알아 두세요.", facts.LIMITS))
    with right:
        show(steps_card("앞으로의 확장 방향", "실제 플랫폼의 행동 기록을 받으면 이렇게 발전시킬 수 있어요.",
                        facts.FUTURE_STEPS))
        show(check_list_card("확보하면 좋은 데이터", "행동 기록이 생기면 예측이 훨씬 정확해져요.",
                             [(item, "") for item in facts.FUTURE_DATA]))


def render():
    show(page_header("ABOUT STAYMATCH", "프로젝트 및 모델 정보",
                     "어떤 데이터로 무엇을 예측하는지, 그리고 지금의 한계까지 투명하게 정리했어요."))

    # 탭 4개. 탭마다 위에서 만든 함수가 내용을 그려요.
    t1, t2, t3, t4 = st.tabs(["프로젝트", "데이터 · Target", "모델", "한계 · 확장"])
    with t1:
        _tab_project()
    with t2:
        _tab_data()
    with t3:
        _tab_model()
    with t4:
        _tab_limits()
