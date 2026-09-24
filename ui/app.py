"""Catch 화면 (app.py) — 실행할 때 가장 먼저 읽히는 메인 파일

[이 서비스는 뭔가요?]
데이팅 앱 운영사 담당자가 사용자 프로필(나이, 직업 등)을 입력하면
"이 사용자가 곧 앱을 떠날 위험이 얼마나 되는지" 보여주는 웹 화면입니다.
여기서 '이탈'이란 마지막 접속 후 30일 이상 앱에 들어오지 않는 것을 말해요.
(아직 예측 모델이 연결 전이라, 결과 자리에는 '--' 가 표시됩니다.)

[Streamlit 은 어떻게 동작하나요? — 처음 보는 분을 위한 설명]
- 파이썬 코드를 위에서 아래로 읽으면서 웹 화면을 그립니다. (HTML/자바스크립트를 몰라도 됨)
- 사용자가 버튼을 누르거나 값을 바꿀 때마다 이 파일이 '처음부터 다시' 실행됩니다.
  그래서 st.selectbox 같은 입력칸은 실행될 때마다 '지금 선택된 값'을 돌려줘요.
- st.markdown(..., unsafe_allow_html=True) 는 HTML 로 글자 모양을 꾸며 넣을 때 씁니다.

[파일 구성 — 모두 ui 폴더 안]
- app.py            : (이 파일) SERVICE 화면 + 메뉴 이동
- page_home.py      : HOME 화면 (서비스 소개)
- page_insight.py   : INSIGHT 화면 (이탈 위험 사용자 분석 대시보드)
- page_retention.py : RETENTION 화면 (위험 수준별 리텐션 전략)
- page_about.py     : ABOUT 화면 (프로젝트·모델 정보)
- project_facts.py  : 위 세 화면에 나오는 숫자·설명 문구 모음 (최종 모델 확정 후 여기를 갱신)
- insight_data.py   : INSIGHT 의 그룹별 이탈률 계산 (data 폴더의 데이터 파일 사용)
- ui_parts.py       : 세 화면이 함께 쓰는 카드·그래프·표 조각
- styles.py         : 색, 글자 크기 같은 디자인(CSS)
- avatars.py        : 프로필 예시 얼굴 그리기
- predict.py        : 예측(모델) 담당. 화면 입력값 -> 20개 feature 표 변환, 모델 예측, SHAP 계산
- service_view.py   : SERVICE 화면 오른쪽 '결과 칸'. 모델 연결 전/후로 카드 내용이 자동으로 바뀌어요
- db.py             : DB 연결 담당. 예측 결과를 predictions_live 테이블에 기록해요

[실행 방법]  프로젝트 맨 바깥 폴더에서:  uv run streamlit run ui/app.py
"""
import streamlit as st    # 웹 화면을 파이썬으로 만들어 주는 라이브러리 (관례로 st 라고 줄여 씁니다)

import os     # model_file 컬럼에 넣을 파일 이름만 뽑을 때 씀 (os.path.basename)

# =========================================================
# 기본 설정
# =========================================================
# 웹 페이지의 '기본값'을 정합니다.
# 주의: 화면을 그리는 Streamlit 명령 중 가장 먼저 실행돼야 해서 맨 위에 둡니다.
st.set_page_config(
    page_title="Catch",          # 브라우저 탭에 보이는 이름
    page_icon="💘",                   # 브라우저 탭에 보이는 아이콘
    layout="wide",                   # 화면을 좌우로 넓게 사용
    initial_sidebar_state="collapsed"   # 왼쪽 사이드바는 처음부터 접어 둠 (안 쓰므로)
)

# 같은 폴더(ui)의 다른 파일에서 필요한 기능만 '가져옵니다(import)'.
# 파일을 나눠 두면 "디자인은 styles.py, 얼굴은 avatars.py" 처럼 고칠 곳을 바로 찾을 수 있어요.
from styles import apply_styles        # styles.py  : CSS(디자인)
from avatars import input_card_html    # avatars.py : 프로필 예시 얼굴이 들어간 입력 카드
import db                                                   # DB 연결 (predictions_live 에 기록)
import project_facts as facts                               # feature 이름 -> 한글 이름 짝꿍표
# 메뉴별 화면은 파일을 따로 두었어요. (as 뒤는 이 파일에서 부를 이름표)
from service_view import render_result_panel               # SERVICE 오른쪽 결과 칸
from predict import find_model_path, load_model, predict_churn   # 예측 모델 연결
from page_home import render as render_home                # HOME      메뉴 화면
from page_insight import render as render_insight        # INSIGHT   메뉴 화면
from page_retention import render as render_retention    # RETENTION 메뉴 화면
from page_about import render as render_about            # ABOUT     메뉴 화면

# 디자인 규칙(CSS)을 화면에 적용합니다.
# 이 줄이 없으면 핑크 테마가 모두 사라지고 스트림릿 기본 모양으로 나와요.
apply_styles()


# models 폴더에서 .cbm 파일을 한 번만 찾아 불러옵니다. (없으면 None -> EDA 참고 신호로 대신함)
# 경로(churn_model_path)도 따로 기억해 둬요. predictions_live 의 model_file 컬럼에 파일 이름을
# 남길 때 필요해서예요.
# @st.cache_resource 가 없으면 화면을 조작할 때마다 매번 다시 찾고 불러와서 느려져요.
@st.cache_resource
def _find_churn_model_path():
    return find_model_path()


@st.cache_resource
def _load_churn_model():
    path = _find_churn_model_path()
    if path is None:
        return None
    try:
        return load_model(path)
    except Exception:
        return None


churn_model_path = _find_churn_model_path()
churn_model = _load_churn_model()

# 예측 결과에서 위험 신호 상위 3개를 한글 이름으로 바꿀 때 쓰는 짝꿍표.
# project_facts.py 에서 한 번만 만들어 둔 걸 가져다 써요 (service_view.py 도 같은 걸 씁니다).
# predict.py 의 'low'/'mid'/'high' -> predictions_live 테이블이 쓰는 'Low'/'Medium'/'High'
_RISK_TIER_LABELS = {"low": "Low", "mid": "Medium", "high": "High"}

# =========================================================
# 페이지 이동 (HOME 버튼 -> SERVICE)
# =========================================================
# HOME 화면의 "이탈 위험 분석하기" 버튼을 누르면 실행되는 함수입니다.
# st.session_state 는 Streamlit 이 '코드가 다시 실행되는 사이에도 기억해 두는 메모장'이에요.
# 아래 메뉴(라디오 버튼)의 이름표(key)가 "page" 라서, 여기 값을 SERVICE 로 바꾸면
# 메뉴 선택도 SERVICE 로 바뀌고 화면이 서비스 페이지로 넘어갑니다.
def go_to_service():
    st.session_state["page"] = "SERVICE"


# =========================================================
# 상단 NAV
# =========================================================
# st.columns([1.2, 3]) : 화면을 가로로 나눕니다. 왼쪽(로고) : 오른쪽(메뉴) = 1.2 : 3 비율
logo_col, nav_col = st.columns([1.2, 3])

# "with 칸:" 아래 들여쓴 코드는 그 칸 안에 그려집니다.
with logo_col:
    if st.button("♥ Catch", key="logo_home", type="tertiary"):
        st.session_state.page = "HOME"

with nav_col:
    # 메뉴를 '라디오 버튼(여러 개 중 하나만 고르는 버튼)'으로 만들었어요.
    # 지금 고른 메뉴 이름이 page 변수에 들어가고, 아래 if 문이 그 값을 보고 화면을 바꿉니다.
    page = st.radio(
        "menu",                                              # 이 입력칸의 이름 (화면에는 안 보임)
        ["HOME", "SERVICE", "INSIGHT", "RETENTION", "ABOUT"],  # 메뉴 5개
        horizontal=True,                                     # 가로로 나열
        label_visibility="collapsed",                        # 위의 이름 글자를 숨김
        key="page"                                           # 이 선택값의 '이름표' (go_to_service 가 이 이름표로 값을 바꿈)
    )


# =========================================================
# HOME
# =========================================================
# 메뉴에서 고른 값(page)에 따라 서로 다른 화면을 그립니다.
# HOME -> SERVICE -> INSIGHT ... 순서로 if / elif 가 이어져요.
if page == "HOME":
    # HOME 화면은 page_home.py 에 있어요. 시작 버튼을 눌렀을 때 실행할 함수(go_to_service)를 넘겨줍니다.
    render_home(on_start=go_to_service)


# =========================================================
# SERVICE
# =========================================================
# 서비스 화면: 왼쪽에 사용자 정보를 입력하고, 오른쪽에 예측 결과가 나오는 구조입니다.
elif page == "SERVICE":

    # 화면 맨 위 제목 문구
    st.markdown("""
<div style="padding-top: 50px; padding-bottom: 25px;">
<div style="font-size: 14px; font-weight: 800; color: #d1245e;">
CHURN RISK PREDICTION
</div>

<div style="font-size: 38px; font-weight: 850; color: #222; margin-top: 8px;">
사용자 이탈 위험 분석
</div>

<div style="font-size: 16px; color: #5a5a5a; margin-top: 10px;">
사용자 프로필 정보를 입력하면 장기 미접속 위험을 분석합니다.
</div>
</div>
""", unsafe_allow_html=True)

    # 왼쪽(입력) : 오른쪽(결과) = 1.25 : 1 로 나눔. gap="large" 는 두 칸 사이를 넓게 띄움
    input_col, result_col = st.columns([1.25, 1], gap="large")

    # =====================================================
    # 왼쪽 : 사용자 정보 입력
    # =====================================================
    with input_col:

        # st.empty() 는 '빈 자리표'입니다. 얼굴 카드를 지금 바로 그리지 않고 자리만 잡아 둬요.
        # 이유: 얼굴이 성별/나이에 따라 바뀌어야 하는데, 그 값은 아래 입력칸에서 받기 때문입니다.
        #       입력값을 받은 뒤(아래 "성별 / 나이에 맞는 얼굴로..." 줄)에 이 자리에 카드를 채웁니다.
        avatar_slot = st.empty()

        st.write("")    # 빈 줄 하나 (위아래 간격 띄우기)

        # -------------------------------------------------
        # 기본 정보
        # -------------------------------------------------
        # expander = 접었다 펼 수 있는 상자. expanded=True 는 처음부터 열어 두라는 뜻입니다.
        # (입력 항목이 많아서 종류별로 상자를 나눠 화면이 길어 보이지 않게 했어요.)
        with st.expander("👤 기본 정보", expanded=True):

            # 성별 / 나이 / 키를 한 줄에 나란히 (칸 3개)
            col_gender, col1, col2 = st.columns(3)

            with col_gender:
                # 성별은 위쪽 '예시 얼굴'을 성별에 맞게 바꾸는 데만 쓰고, 예측 모델에는 넣지 않습니다.
                # st.selectbox = 목록에서 하나를 고르는 드롭다운. 고른 값이 변수에 담겨요.
                gender_kr = st.selectbox(
                    "성별",
                    ["선택해주세요", "여성", "남성"],
                    help="프로필 예시 얼굴에만 쓰이고 예측에는 사용되지 않아요."
                )
                # 화면의 한글 -> avatars.py 가 알아듣는 글자(f=여성, m=남성, None=선택 안 함)로 바꿈
                gender_face = {"선택해주세요": None, "여성": "f", "남성": "m"}[gender_kr]

            with col1:
                age = st.selectbox(
                    "나이",
                    list(range(18, 91)),   # 18, 19, ... 90 까지의 목록
                    index=10               # 처음에 보일 값: 목록의 11번째 = 28세
                )

            with col2:
                height_kr = st.selectbox(
                    "키",
                    [f"{cm} cm" for cm in range(140, 201)],   # "140 cm" ~ "200 cm"
                    index=28                                   # 처음에 보일 값: 168 cm
                )

                # "168 cm" 에서 " cm" 를 떼고 숫자만 뽑은 뒤, 인치로 환산합니다.
                # 이유: 학습 데이터(OkCupid)의 키가 cm 가 아니라 인치 단위라서,
                #       모델에는 학습 때와 같은 단위로 넘겨야 합니다. (1인치 = 2.54cm)
                height_cm = int(height_kr.replace(" cm", ""))
                height = height_cm / 2.54

            # 방금 고른 성별 / 나이에 맞는 얼굴로, 위에서 잡아 둔 자리(avatar_slot)에 카드를 그립니다.
            # 성별이나 나이를 바꿀 때마다 코드가 다시 실행되어 얼굴도 함께 바뀌어요.
            avatar_slot.markdown(input_card_html(gender_face, age), unsafe_allow_html=True)

            # ─ 선택지(드롭다운)를 만드는 방식 ────────────────────────────
            # 화면에는 '한글'을 보여주고, 모델에는 학습할 때 쓴 '영어 값'을 넘겨야 합니다.
            # 그래서 {"화면에 보이는 한글": "모델이 아는 값"} 짝꿍표(dict)를 만들어 둡니다.
            # 아무것도 고르지 않았거나 모르는 경우는 None(= 빈칸)으로 처리해요.
            #
            # 아래 선택지 값들은 common/feature_extraction.py (최종 확정판)이 실제로 배운
            # 카테고리와 글자까지 똑같이 맞춰 뒀어요. (다르면 모델이 '모르는 값' 취급을 해요)
            # 등급 숫자로 바뀌는 흡연/약물, 자녀 무응답 플래그(has_kids_na), 소득 비공개(NaN),
            # 프로필 완성도 계산 같은 나머지 변환은 predict.py 의 build_feature_row() 가 맡아요.
            # ────────────────────────────────────────────────────────────

            # 직업
            # 원본 데이터 파일(okcupid_profiles.csv)의 job 컬럼을 직접 확인해서
            # value_counts() 로 나온 21개 값을 전부 그대로 옮겨 적었어요. (2026-09-22 확인)
            job_map = {
                "선택해주세요": None,
                "기타": "other",
                "학생": "student",
                "과학 · 기술 · 공학": "science / tech / engineering",
                "컴퓨터 · 하드웨어 · 소프트웨어": "computer / hardware / software",
                "예술 · 음악 · 글쓰기": "artistic / musical / writer",
                "영업 · 마케팅 · 사업 개발": "sales / marketing / biz dev",
                "의료 · 건강": "medicine / health",
                "교육 · 학계": "education / academia",
                "경영 · 임원": "executive / management",
                "금융 · 은행 · 부동산": "banking / financial / real estate",
                "엔터테인먼트 · 미디어": "entertainment / media",
                "법률": "law / legal services",
                "숙박 · 여행": "hospitality / travel",
                "건설 · 기술직": "construction / craftsmanship",
                "사무 · 행정": "clerical / administrative",
                "정치 · 공공행정": "political / government",
                "운수업": "transportation",
                "무직": "unemployed",
                "은퇴": "retired",
                "군인": "military",
                "미응답": "rather not say",
            }

            job_kr = st.selectbox(
                "직업",
                list(job_map.keys())
            )

            # 사용자가 고른 한글(job_kr)로 짝꿍표를 찾아, 모델용 값(job)을 꺼냅니다.
            # 아래 다른 선택지들도 모두 같은 방식이에요.
            job = job_map[job_kr]

            # 관계 상태 (싱글 / 만남 가능 등). 이탈률 차이가 큰 항목이라 모델에서 중요하게 봅니다.
            status_map = {
                "선택해주세요": None,
                "싱글": "single",
                "만남 가능": "available",
                "만나는 사람 있음": "seeing someone",
                "기혼": "married",
                "미응답": "unknown"
            }

            status_kr = st.selectbox(
                "현재 관계 상태",
                list(status_map.keys())
            )

            status = status_map[status_kr]

            # 소득: 공개한 사람만 금액을 입력받습니다.
            # (원본 데이터에서 비공개가 80%라서 '공개했는지 여부' 자체도 하나의 정보가 돼요.)
            income_disclosed = st.selectbox(
                "소득 정보를 공개했나요?",
                ["선택해주세요", "공개", "미공개"]
            )

            if income_disclosed == "공개":
                income = st.number_input(     # 숫자만 입력할 수 있는 칸
                    "연 소득 (USD)",
                    min_value=0,              # 0 보다 작은 값은 입력 불가
                    value=50000,              # 처음에 들어 있는 값
                    step=1000                 # + - 버튼을 누르면 1000 씩 변함
                )
            else:
                income = None    # 비공개 -> 값 없음(결측). 학습 때도 비공개 코드(-1)를 결측으로 바꿔서 썼어요

        # -------------------------------------------------
        # 학력 및 종교 (학습할 때는 '학력 단계 + 재학/졸업 상태', '종교 종류' 로 나눠서 사용)
        # -------------------------------------------------
        with st.expander("🎓 학력 및 종교"):

            # 학력
            # ⚠️ 수정: 예전 값("college","university","masters","ph.d")은 모델이 학습한
            #    카테고리와 글자가 달라서 전부 '모르는 값' 취급을 받고 있었어요. 최종
            #    feature_extraction.py 가 실제로 쓰는 문자열로 맞췄어요. ("기타"는 모델이
            #    학습한 카테고리에 없어서 '선택 안 함(미응답)'과 동일하게 처리돼요)
            education_map = {
                "선택해주세요": None,
                "고등학교": "high school",
                "전문대학": "two-year college",
                "대학교": "college/university",
                "석사": "masters program",
                "박사": "ph.d program",
            }

            education_kr = st.selectbox(
                "최종 학력",
                list(education_map.keys())
            )

            education = education_map[education_kr]

            # 교육 상태
            # ⚠️ 수정: "graduated"/"dropped out"은 모델 카테고리와 한 글자씩 달라서(뒤에 " from"/" of"가
            #    빠짐) 모르는 값 취급을 받고 있었어요. "미응답": "unknown"도 edu_status 에는 없는
            #    카테고리라 지우고 선택 안 함(None)과 같게 뒀어요.
            education_status_map = {
                "선택해주세요": None,
                "졸업": "graduated from",
                "재학 중": "working on",
                "중퇴": "dropped out of",
            }

            education_status_kr = st.selectbox(
                "교육 상태",
                list(education_status_map.keys())
            )

            education_status = education_status_map[education_status_kr]

            # 종교
            religion_map = {
                "선택해주세요": None,
                "불가지론": "agnosticism",
                "무신론": "atheism",
                "기독교": "christianity",
                "가톨릭": "catholicism",
                "유대교": "judaism",
                "불교": "buddhism",
                "힌두교": "hinduism",
                "이슬람교": "islam",
                "기타": "other",
                "미응답": "not_disclosed"
            }

            religion_kr = st.selectbox(
                "종교",
                list(religion_map.keys())
            )

            religion = religion_map[religion_kr]

        # -------------------------------------------------
        # 라이프스타일 (식단, 흡연, 약물)
        # -------------------------------------------------
        with st.expander("🍽️ 라이프스타일"):

            # 식단 유형
            diet_type_map = {
                "선택해주세요": None,
                "특별한 제한 없음": "anything",
                "채식": "vegetarian",
                "비건": "vegan",
                "코셔 식단": "kosher",
                "할랄 식단": "halal",
                "기타": "other",
                "미응답": "not_disclosed"
            }

            diet_type_kr = st.selectbox(
                "식단 유형",
                list(diet_type_map.keys())
            )

            diet_type = diet_type_map[diet_type_kr]

            # 식단 준수 정도
            # ⚠️ 수정: "특별히 신경 쓰지 않음"이 diet_type 의 값("anything")으로 잘못 들어가 있었어요.
            #    diet_strict 의 '신경 안 씀'에 해당하는 실제 카테고리는 "plain"이에요.
            diet_strict_map = {
                "선택해주세요": None,
                "대체로 지킴": "mostly",
                "엄격하게 지킴": "strictly",
                "특별히 신경 쓰지 않음": "plain",
                "미응답": "not_disclosed"
            }

            diet_strict_kr = st.selectbox(
                "식단 준수 정도",
                list(diet_strict_map.keys())
            )

            diet_strict = diet_strict_map[diet_strict_kr]

            # 흡연
            # ⚠️ 수정: "피우지 않음"/"자주 피움"이 "never"/"often"으로 되어 있었는데, 모델이
            #    실제로 배운 값은 "no"/"yes"예요. (predict.py 의 SMOKES 짝꿍표와 글자가
            #    같아야 등급 숫자로 바뀔 수 있어요)
            smoking_map = {
                "선택해주세요": None,
                "피우지 않음": "no",
                "가끔 피움": "sometimes",
                "술 마실 때만 피움": "when drinking",
                "금연 중": "trying to quit",
                "자주 피움": "yes",
                "미응답": "not_disclosed"
            }

            smoking_kr = st.selectbox(
                "흡연 여부",
                list(smoking_map.keys())
            )

            smoking = smoking_map[smoking_kr]

            # 약물
            drugs_map = {
                "선택해주세요": None,
                "사용하지 않음": "never",
                "가끔 사용": "sometimes",
                "자주 사용": "often",
                "미응답": "not_disclosed"
            }

            drugs_kr = st.selectbox(
                "약물 사용 여부",
                list(drugs_map.keys())
            )

            drugs = drugs_map[drugs_kr]

        # -------------------------------------------------
        # 가족 정보 (자녀가 있는지, 앞으로 원하는지)
        # -------------------------------------------------
        with st.expander("👨‍👩‍👧 가족 정보"):

            # 자녀 여부
            has_kids_map = {
                "선택해주세요": None,
                "자녀 없음": "no",
                "자녀 있음": "yes",
                "미응답": "not_disclosed"
            }

            has_kids_kr = st.selectbox(
                "현재 자녀가 있나요?",
                list(has_kids_map.keys())
            )

            has_kids = has_kids_map[has_kids_kr]

            # 자녀 계획
            wants_kids_map = {
                "선택해주세요": None,
                "원함": "yes",
                "원하지 않음": "no",
                "아직 모르겠음": "maybe",
                "미응답": "not_disclosed"
            }

            wants_kids_kr = st.selectbox(
                "향후 자녀를 원하나요?",
                list(wants_kids_map.keys())
            )

            wants_kids = wants_kids_map[wants_kids_kr]

        # -------------------------------------------------
        # 프로필 / 자기소개
        # 자기소개 글은 모델이 내용을 '읽는' 게 아니라, 작성한 개수와 글자 수 같은
        # '숫자'로 바뀌어 쓰입니다. (성실하게 채운 사람일수록 앱을 오래 쓰는 경향이 있어요)
        # 참고: Streamlit 은 expander 안에 expander를 넣을 수 없어서,
        #       '추가 항목'은 체크박스로 펼치도록 만들었습니다.
        # -------------------------------------------------
        with st.expander("📝 프로필 / 자기소개"):

            st.caption(
                "자기소개 작성 내용을 바탕으로 프로필 작성량과 길이 등의 정보를 자동으로 계산합니다."
            )

            essay0 = st.text_area(     # 여러 줄을 쓸 수 있는 큰 입력칸
                "자기소개",
                height=120,
                placeholder="사용자의 기본 자기소개 내용을 입력해주세요."
            )

            show_more_essays = st.checkbox("추가 자기소개 항목도 입력하기")

            # 체크하지 않으면 추가 항목은 "빈 글자"로 둡니다. (변수가 항상 존재해야 나중에 모델에 넘길 때 에러가 안 나요)
            essay1 = essay2 = essay3 = essay4 = ""
            essay5 = essay6 = essay7 = essay8 = essay9 = ""

            # 체크박스를 눌렀을 때만 추가 입력칸 9개를 보여줍니다.
            if show_more_essays:

                essay1 = st.text_area(
                    "나에 대한 설명",
                    height=90,
                    placeholder="자신에 대해 추가로 작성한 내용을 입력해주세요."
                )

                essay2 = st.text_area(
                    "현재 하고 있는 일",
                    height=90,
                    placeholder="직업, 학업, 현재 하고 있는 일에 대한 내용을 입력해주세요."
                )

                essay3 = st.text_area(
                    "잘하는 것",
                    height=90,
                    placeholder="자신이 잘한다고 생각하는 것에 대한 내용을 입력해주세요."
                )

                essay4 = st.text_area(
                    "사람들이 처음 알아보는 특징",
                    height=90,
                    placeholder="다른 사람들이 나에게서 가장 먼저 알아보는 특징을 입력해주세요."
                )

                essay5 = st.text_area(
                    "좋아하는 것",
                    height=90,
                    placeholder="좋아하는 책, 영화, 음악, 음식 등에 대한 내용을 입력해주세요."
                )

                essay6 = st.text_area(
                    "없이는 살 수 없는 것",
                    height=90,
                    placeholder="중요하게 생각하는 것들을 입력해주세요."
                )

                essay7 = st.text_area(
                    "자주 생각하는 것",
                    height=90,
                    placeholder="평소 자주 생각하는 주제나 관심사를 입력해주세요."
                )

                essay8 = st.text_area(
                    "평소 여가 시간",
                    height=90,
                    placeholder="주말이나 여가 시간에 주로 무엇을 하는지 입력해주세요."
                )

                essay9 = st.text_area(
                    "연락해도 좋은 경우",
                    height=90,
                    placeholder="어떤 사람과 연결되고 싶은지 입력해주세요."
                )

        # 분석 버튼. 눌린 순간에만 predict_button 이 True 가 됩니다.
        # 모델은 이 파일 위쪽에서 한 번만 불러놨어요(churn_model). 버튼을 누르면 predict_churn() 으로
        # 실제 예측을 하고, models 폴더에 .cbm 파일이 없으면 churn_model 이 None 이라 EDA 참고 신호로 대신해요.
        predict_button = st.button(
            "💘 이탈 위험 분석하기",
            use_container_width=True     # 버튼을 칸 너비에 꽉 채움
        )

    # =====================================================
    # 오른쪽 : 예측 결과
    # =====================================================
    with result_col:
        # 결과 칸은 service_view.py 가 채워요. models 폴더에 모델(.cbm)이 있으면 진짜 예측을,
        # 없으면 예전처럼 분석 결과(EDA) 기반 참고 신호를 보여줍니다. (앱은 어느 쪽이든 안 멈춰요)
        essays = [essay0, essay1, essay2, essay3, essay4, essay5, essay6, essay7, essay8, essay9]

        current_inputs = {
            "age": age, "height": height, "job": job, "status": status, "income": income,
            "education": education, "education_status": education_status, "religion": religion,
            "diet_type": diet_type, "diet_strict": diet_strict, "smoking": smoking, "drugs": drugs,
            "has_kids": has_kids, "wants_kids": wants_kids, "essays": essays,
        }

        # What-if 입력을 바꾸면 Streamlit이 화면을 다시 실행하므로, 직전에 계산한 원본 결과와
        # 입력을 session_state에 보관해 결과 화면이 사라지지 않게 합니다.
        prediction = st.session_state.get("service_prediction")
        prediction_inputs = st.session_state.get("service_prediction_inputs")
        if predict_button and churn_model is not None:
            prediction = predict_churn(current_inputs, churn_model)
            prediction_inputs = current_inputs
            st.session_state["service_prediction"] = prediction
            st.session_state["service_prediction_inputs"] = current_inputs
            st.session_state.pop("service_whatif", None)
            st.session_state.pop("service_show_whatif_editor", None)

            # 방금 예측한 결과를 predictions_live 테이블에 한 줄 남겨요.
            # (INSIGHT 의 v_live_recent · v_live_today 뷰가 이 표를 보고 만들어져요)
            # 신호 상위 3개를 "이름 (위험↑)" / "이름 (안정↓)" 모양으로 바꿔서 reason_1~3 에 넣어요.
            row = prediction["row"]     # predict.py 가 만든 1행짜리 표 (essay_count 등을 여기서 꺼내요)
            reasons = []
            for code, value in prediction["top_signals"][:3]:
                name = facts.FEATURE_LABELS.get(code, code)
                arrow = "위험↑" if value > 0 else "안정↓"
                reasons.append(f"{name} ({arrow})")
            reasons += [None] * (3 - len(reasons))     # 3개가 안 되면 나머지는 빈칸으로

            # DB 기록은 '되면 좋고 안 돼도 화면은 그대로 보여준다'는 원칙이라, 실패해도 조용히 넘어가요.
            db.log_prediction({
                "churn_prob": prediction["risk"],
                "risk_tier": _RISK_TIER_LABELS[prediction["level"]],
                "age": age,
                "sex": gender_face,          # 'f' / 'm' / None (예측에는 안 쓰지만 기록용으로 남김)
                "status": status,
                "job": job,
                "essay_count": int(row["essay_count"].iloc[0]),
                "profile_completeness": float(row["profile_completeness"].iloc[0]),
                "reason_1": reasons[0], "reason_2": reasons[1], "reason_3": reasons[2],
                "model_file": os.path.basename(churn_model_path) if churn_model_path else None,
                "note": None,
            })
        elif predict_button:
            # 모델이 없는 상태에서 버튼을 누르면 과거 결과를 새 결과처럼 보여주지 않습니다.
            prediction = None
            prediction_inputs = None
            st.session_state.pop("service_prediction", None)
            st.session_state.pop("service_prediction_inputs", None)
            st.session_state.pop("service_whatif", None)
            st.session_state.pop("service_show_whatif_editor", None)

        render_result_panel(
            essays=(prediction_inputs or current_inputs)["essays"],
            has_kids=(prediction_inputs or current_inputs)["has_kids"],
            status=(prediction_inputs or current_inputs)["status"],
            clicked=predict_button,
            prediction=prediction,
            current_inputs=prediction_inputs,
            model=churn_model,
        )


# =========================================================
# INSIGHT / RETENTION / ABOUT
# 화면 내용이 길어서 각각 다른 파일에 있어요. 여기서는 '호출'만 합니다.
#   INSIGHT   : 이탈 위험 사용자 분석 대시보드 (page_insight.py)
#   RETENTION : 위험 수준별 리텐션 전략        (page_retention.py)
#   ABOUT     : 프로젝트 및 모델 정보           (page_about.py)
# =========================================================
elif page == "INSIGHT":
    render_insight()

elif page == "RETENTION":
    render_retention()

elif page == "ABOUT":
    render_about()
