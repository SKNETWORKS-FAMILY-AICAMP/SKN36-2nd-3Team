"""StayMatch 화면 (app.py) — 실행할 때 가장 먼저 읽히는 메인 파일

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
- predict.py        : 예측(모델) 담당. 최종 모델이 정해지면 채울 예정

[실행 방법]  프로젝트 맨 바깥 폴더에서:  uv run streamlit run ui/app.py
"""
import streamlit as st    # 웹 화면을 파이썬으로 만들어 주는 라이브러리 (관례로 st 라고 줄여 씁니다)

# =========================================================
# 기본 설정
# =========================================================
# 웹 페이지의 '기본값'을 정합니다.
# 주의: 화면을 그리는 Streamlit 명령 중 가장 먼저 실행돼야 해서 맨 위에 둡니다.
st.set_page_config(
    page_title="StayMatch",          # 브라우저 탭에 보이는 이름
    page_icon="💘",                   # 브라우저 탭에 보이는 아이콘
    layout="wide",                   # 화면을 좌우로 넓게 사용
    initial_sidebar_state="collapsed"   # 왼쪽 사이드바는 처음부터 접어 둠 (안 쓰므로)
)

# 같은 폴더(ui)의 다른 파일에서 필요한 기능만 '가져옵니다(import)'.
# 파일을 나눠 두면 "디자인은 styles.py, 얼굴은 avatars.py" 처럼 고칠 곳을 바로 찾을 수 있어요.
from styles import apply_styles        # styles.py  : CSS(디자인)
from avatars import input_card_html    # avatars.py : 프로필 예시 얼굴이 들어간 입력 카드
# 메뉴별 화면은 파일을 따로 두었어요. (as 뒤는 이 파일에서 부를 이름표)
from page_home import render as render_home                # HOME      메뉴 화면
from page_insight import render as render_insight        # INSIGHT   메뉴 화면
from page_retention import render as render_retention    # RETENTION 메뉴 화면
from page_about import render as render_about            # ABOUT     메뉴 화면

# 디자인 규칙(CSS)을 화면에 적용합니다.
# 이 줄이 없으면 핑크 테마가 모두 사라지고 스트림릿 기본 모양으로 나와요.
apply_styles()

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
    st.markdown(
        """
        <div class="logo">
            <span class="logo-heart">♥</span> StayMatch
        </div>
        """,
        unsafe_allow_html=True
    )

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
<div style="font-size: 14px; font-weight: 800; color: #ff4f81;">
CHURN RISK PREDICTION
</div>

<div style="font-size: 38px; font-weight: 850; color: #222; margin-top: 8px;">
사용자 이탈 위험 분석
</div>

<div style="font-size: 16px; color: #777; margin-top: 10px;">
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
            # ⚠️ TODO (모델 연결 때 손볼 곳)
            #   지금 영어 값 중 일부는 임시라서 학습 데이터의 값과 글자가 다릅니다.
            #   최종 feature 가 확정되면 predict.py 에서 아래처럼 맞출 예정이에요.
            #   (기준: 노션 '데이터 전처리 결과서'의 최종 25개 feature)
            #   - 직업       : 원본 21종('science / tech / engineering' 등)이라 지금 값과 다름
            #   - 학력/상태  : 'college/university', 'graduated from' 같은 형태
            #   - 식단 엄격도: '신경 안 씀' 은 'plain'
            #   - 흡연/약물  : 글자가 아니라 등급 숫자 (흡연 0~4, 약물 0~2)
            #   - 자녀 유무  : 'no' / 'yes' / 'unspecified' / 'not_disclosed' 4가지 (+ 무응답 여부 플래그 has_kids_na)
            #   - 소득 비공개: 숫자가 아닌 '결측(NaN)'으로 (-1 이 아님)
            #   - 빈칸 처리  : 글자(범주형) 항목의 빈칸은 'not_disclosed' 라는 별도 값으로 남기고,
            #                  숫자 항목의 빈칸은 NaN 그대로 둡니다. (CatBoost 가 알아서 처리)
            #                  그래서 아래 '미응답 -> not_disclosed' 는 학습 방식과 맞는 값이에요.
            # ────────────────────────────────────────────────────────────

            # 직업
            job_map = {
                "선택해주세요": None,
                "학생": "student",
                "IT · 기술": "technology",
                "교육": "education",
                "의료": "medicine",
                "비즈니스 · 경영": "business",
                "금융": "finance",
                "예술": "arts",
                "영업 · 판매": "sales",
                "기타": "other"
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
            education_map = {
                "선택해주세요": None,
                "고등학교": "high school",
                "전문대학": "college",
                "대학교": "university",
                "석사": "masters",
                "박사": "ph.d",
                "기타": "other"
            }

            education_kr = st.selectbox(
                "최종 학력",
                list(education_map.keys())
            )

            education = education_map[education_kr]

            # 교육 상태
            education_status_map = {
                "선택해주세요": None,
                "졸업": "graduated",
                "재학 중": "working on",
                "중퇴": "dropped out",
                "미응답": "unknown"
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
            diet_strict_map = {
                "선택해주세요": None,
                "대체로 지킴": "mostly",
                "엄격하게 지킴": "strictly",
                "특별히 신경 쓰지 않음": "anything",
                "미응답": "not_disclosed"
            }

            diet_strict_kr = st.selectbox(
                "식단 준수 정도",
                list(diet_strict_map.keys())
            )

            diet_strict = diet_strict_map[diet_strict_kr]

            # 흡연
            smoking_map = {
                "선택해주세요": None,
                "피우지 않음": "never",
                "가끔 피움": "sometimes",
                "술 마실 때만 피움": "when drinking",
                "금연 중": "trying to quit",
                "자주 피움": "often",
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
        # 참고: Streamlit 은 expander 안에 expander 를 넣을 수 없어서,
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
        # TODO (모델 연결 때): 아래처럼 predict.py 의 함수를 불러 결과를 오른쪽 카드에 표시할 예정
        #   from predict import predict_churn
        #   if predict_button:
        #       result = predict_churn({"age": age, "height": height, "job": job, ...})
        predict_button = st.button(
            "💘 이탈 위험 분석하기",
            use_container_width=True     # 버튼을 칸 너비에 꽉 채움
        )

    # =====================================================
    # 오른쪽 : 예측 결과
    # =====================================================
    # 아래 카드 3개(예측 결과 / 주요 예측 신호 / 추천 리텐션 전략)는 지금은 '자리'만 만들어 둔 상태입니다.
    # 모델이 연결되면 여기에 실제 결과가 표시돼요.
    with result_col:

        # 카드 1: 이탈 위험도. 지금은 '--' 로 비워 둠 (나중에 예: 62% 처럼 표시)
        st.markdown("""
<div style="
background: white;
border: 1px solid #f4e6eb;
border-radius: 24px;
padding: 30px;
box-shadow: 0 12px 35px rgba(58,26,37,0.05);
margin-bottom: 20px;
">

<div style="
font-size: 20px;
font-weight: 800;
color: #222;
margin-bottom: 20px;
">
📊 예측 결과
</div>

<div style="
background: #fff3f7;
border-radius: 20px;
padding: 35px;
text-align: center;
">

<div style="
font-size: 14px;
color: #888;
">
CHURN RISK
</div>

<div style="
font-size: 52px;
font-weight: 850;
color: #ff4f81;
margin-top: 10px;
">
--
</div>

<div style="
font-size: 15px;
color: #777;
">
모델 연결 후 예측 결과가 표시됩니다.
</div>

</div>

</div>
""", unsafe_allow_html=True)

        # 카드 2: 주요 예측 신호. SHAP(각 항목이 위험도에 얼마나 영향을 줬는지 알려 주는 방법)으로 채울 예정
        st.markdown("""
<div style="
background: white;
border: 1px solid #f4e6eb;
border-radius: 24px;
padding: 28px;
margin-bottom: 20px;
">

<div style="
font-size: 19px;
font-weight: 800;
margin-bottom: 18px;
">
🔍 주요 예측 신호
</div>

<div style="
color: #888;
line-height: 1.9;
font-size: 15px;
">
모델 예측 후 SHAP 값을 기반으로<br>
사용자별 주요 예측 신호를 표시합니다.
</div>

</div>
""", unsafe_allow_html=True)

        # 카드 3: 추천 리텐션 전략 (리텐션 = 사용자가 앱을 계속 쓰도록 붙잡아 두는 활동)
        #         위험 수준에 맞는 운영 방법(재접속 알림 등)을 보여줄 예정
        st.markdown("""
<div style="
background: white;
border: 1px solid #f4e6eb;
border-radius: 24px;
padding: 28px;
">

<div style="
font-size: 19px;
font-weight: 800;
margin-bottom: 18px;
">
🎯 추천 리텐션 전략
</div>

<div style="
color: #888;
line-height: 1.9;
font-size: 15px;
">
예측된 위험 수준과 주요 특성을 기반으로<br>
플랫폼 운영자가 검토할 수 있는 리텐션 전략을 제공합니다.
</div>

</div>
""", unsafe_allow_html=True)


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
