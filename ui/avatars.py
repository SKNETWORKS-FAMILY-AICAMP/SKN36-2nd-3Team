"""프로필 예시 얼굴 그리기 (avatars.py)

[이 파일이 하는 일]
"사용자 정보 입력" 카드 위쪽에 보이는 동그란 얼굴 그림을 만듭니다.
사용자가 고른 성별과 나이에 맞춰서 얼굴이 바뀝니다.
  예) 여성 + 28세 -> 머리를 묶은 젊은 얼굴
      남성 + 63세 -> 흰머리에 안경 쓴 얼굴

[왜 만들었나요?]
입력 화면이 텅 비어 보이지 않게 하고, 데이팅 서비스다운 분위기를 내기 위해서입니다.
※ 예측 모델은 얼굴이나 사진을 전혀 쓰지 않습니다. 화면 장식일 뿐이에요.

[얼굴은 어디서 가져오나요?]
DiceBear 라는 무료 아바타 도구의 'Lorelei' 스타일을 씁니다 (CC0 = 출처 표기 없이 자유롭게 사용 가능).
인터넷에서 그림을 받아오는 게 아니라, 설치한 패키지가 내 컴퓨터에서 직접 그려요.
그래서 발표장 인터넷이 불안해도 문제없습니다.

[필요한 패키지]  uv add dicebear-core dicebear-styles
(설치가 안 돼 있어도 앱이 멈추지 않고 이모지 얼굴로 대신 보여줍니다.)
"""
import streamlit as st

import base64                            # 그림을 '글자'로 바꿔 HTML 안에 넣기 위해 사용
from importlib.resources import files    # 설치된 패키지 안의 파일을 읽기 위해 사용

# ---------------------------------------------------------
# 패키지가 설치돼 있는지 확인
# ---------------------------------------------------------
# try / except 는 "일단 해보고, 안 되면 이렇게 하자" 라는 뜻이에요.
# 패키지가 없을 때 앱 전체가 에러로 멈추는 것을 막아 줍니다.
try:
    from dicebear import Avatar, Style
    HAS_DICEBEAR = True     # 설치돼 있음 -> 진짜 얼굴을 그린다
except ImportError:
    HAS_DICEBEAR = False    # 설치 안 됨 -> 이모지 얼굴로 대신한다

# ---------------------------------------------------------
# 얼굴 꾸미기 재료 (성별 / 나이대에 따라 다르게 고름)
# ---------------------------------------------------------
# Lorelei 스타일에는 머리 모양이 1~48번까지 있습니다.
# 직접 그려서 눈으로 확인한 뒤, 긴 머리·묶은 머리는 여성 쪽에,
# 짧은 머리·머리숱이 적은 모양은 남성 쪽에 나눠 담았어요.
# 구조:  성별("f"=여성, "m"=남성) -> 나이대(20~80) -> 사용할 머리 모양 번호 목록
HAIR_VARIANTS = {
    "f": {
        20: [26, 14, 15, 16, 21, 23, 41, 46],
        30: [13, 17, 19, 35, 40, 24, 18],
        40: [13, 17, 19, 35, 40, 24],
        50: [13, 17, 19, 35, 40, 32],
        60: [13, 17, 35, 40, 32, 10],
        70: [13, 17, 35, 32, 10, 19],
        80: [13, 17, 35, 32, 10, 19],
    },
    "m": {
        20: [4, 5, 7, 8, 12, 39, 6, 27],
        30: [1, 3, 9, 22, 43, 47, 6],
        40: [1, 3, 9, 22, 43, 47],
        50: [1, 2, 3, 43, 47, 28],
        60: [2, 43, 28, 44, 25, 47],       # 머리숱이 줄어드는 모양 포함
        70: [25, 28, 44, 2, 43, 34],
        80: [25, 28, 44, 34, 2, 43],
    },
}

# 나이가 들수록 머리색이 검정 -> 회색 -> 흰색으로 바뀝니다. (#숫자 = 색 코드)
# 목록에 색이 여러 개면 그중 하나가 자동으로 골라져요.
HAIR_COLORS = {
    20: ["#2b211d", "#4a3122", "#6b4630"],
    30: ["#2b211d", "#3b2a20", "#4a3122"],
    40: ["#2b211d", "#3b2a20", "#4a3122", "#5b5652"],
    50: ["#4a4340", "#6f6a66", "#8a8480"],
    60: ["#a5a5a5", "#b3b3b3", "#9a9a9a"],
    70: ["#c2c2c2", "#cfcfcf", "#d9d9d9"],
    80: ["#e3e3e3", "#ececec", "#d9d9d9"],
}
SKIN_COLORS = ["#f5d7b1", "#ecad80", "#f0c9a0"]    # 피부색 후보

# '확률(%)'은 그 특징이 나올 가능성입니다. 0 = 절대 안 나옴, 100 = 항상 나옴.
GLASSES_CHANCE = {20: 0, 30: 10, 40: 25, 50: 40, 60: 60, 70: 75, 80: 90}   # 안경: 나이 들수록 자주
BEARD_CHANCE = {                                                            # 수염
    "f": {d: 0 for d in range(20, 90, 10)},                                 # 여성은 항상 0
    "m": {20: 0, 30: 15, 40: 30, 50: 40, 60: 50, 70: 55, 80: 60},
}
EARRINGS_CHANCE = {"f": 45, "m": 0}                                         # 귀걸이

# 표정은 무난한 것만 골랐어요 (윙크 / 혀 내밀기 / 선글라스는 제외)
MOUTHS = [f"happy{i:02d}" for i in (1, 2, 3, 4, 5, 6, 13)]
EYES = [f"variant{i:02d}" for i in (2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17, 20, 23, 24)]
GLASSES_VARIANTS = ["variant01", "variant03", "variant04", "variant05"]

# 얼굴 뒤 동그라미 배경색 (파스텔 핑크 / 살구 / 하늘 / 연두)
FACE_BACKGROUNDS = ["#ffe4ec", "#fff0d9", "#e6f0ff", "#e8f7ec"]


def age_group_of(age):
    """나이 -> 연령대. 28세 -> 20, 47세 -> 40 처럼 10단위로 내림합니다.

    - age // 10 * 10 : 일의 자리를 버림 (28 -> 20)
    - max(..., 20)   : 18~19세도 '20대'로 취급
    - min(..., 80)   : 80세 이상은 모두 '80대'로 취급 (입력 가능한 나이가 18~90세라서)
    """
    return min(max(age // 10 * 10, 20), 80)


# @st.cache_resource / @st.cache_data 는 "한 번 만든 결과를 기억해 두는" 기능입니다.
# Streamlit 은 화면을 조작할 때마다 코드를 처음부터 다시 실행하기 때문에,
# 기억해 두지 않으면 매번 같은 얼굴을 다시 그려서 느려져요.
@st.cache_resource
def lorelei_style():
    """Lorelei 스타일 '설계도'(json 파일)를 읽어 온다. 한 번만 읽으면 충분해서 기억해 둠."""
    text = files("dicebear_styles").joinpath("lorelei.json").read_text("utf-8")
    return Style.from_json(text)


@st.cache_data(show_spinner=False)
def face_data_uri(gender, decade, idx, bg):
    """얼굴 하나를 그려서, HTML 의 <img> 태그에 바로 넣을 수 있는 '주소 글자'로 돌려준다.

    gender : "f" 또는 "m"
    decade : 나이대 (20, 30, ... 80)
    idx    : 같은 성별·나이대 안에서 몇 번째 얼굴인지 (0, 1, 2, 3 ...)
    bg     : 배경색
    """
    # 이 성별·나이대에서 쓸 수 있는 머리 모양 목록
    pool = HAIR_VARIANTS[gender][decade]

    # 얼굴을 그릴 때 넘겨주는 '주문서'입니다.
    options = {
        # seed(씨앗)가 같으면 항상 같은 얼굴이 나옵니다 (그래서 새로고침해도 얼굴이 안 바뀜)
        "seed": f"{gender}-{decade}-{idx}",
        # 머리 모양: 목록 중 idx 번째 (목록보다 idx 가 크면 처음부터 다시 돌아 씀)
        "hairVariant": [f"variant{pool[idx % len(pool)]:02d}"],
        "hairColor": HAIR_COLORS[decade],          # 나이대에 맞는 머리색 후보
        "skinColor": SKIN_COLORS,
        "eyesVariant": EYES,
        "mouthVariant": MOUTHS,
        "glassesVariant": GLASSES_VARIANTS,
        "glassesProbability": GLASSES_CHANCE[decade],        # 안경 쓸 확률
        "beardProbability": BEARD_CHANCE[gender][decade],    # 수염 날 확률
        "earringsProbability": EARRINGS_CHANCE[gender],      # 귀걸이 할 확률
        "frecklesProbability": 15 if decade == 20 else 0,    # 주근깨는 20대에만 가끔
        "hairAccessoriesProbability": 0,
        "backgroundColor": [bg],
    }

    # 주문서대로 그림(SVG 형식)을 그립니다.
    svg = Avatar(lorelei_style(), options).to_string()

    # 그림을 파일로 저장하지 않고, 글자(base64)로 바꿔서 HTML 안에 바로 끼워 넣습니다.
    # 이렇게 하면 이미지 파일을 따로 관리할 필요가 없어요.
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def face_stack(gender, age, n=4, size=48):
    """겹쳐진 동그란 얼굴 n개를 HTML 한 줄로 만든다.

    gender: 'f' / 'm' / None  (None = 성별을 아직 안 골랐음 -> 여성·남성을 번갈아 보여줌)
    age   : 화면에서 고른 나이
    n     : 보여줄 얼굴 개수 (기본 4개)
    size  : 얼굴 크기(px)
    """
    decade = age_group_of(age)
    imgs = ""    # 얼굴 <img> 태그를 여기에 계속 이어 붙입니다.
    for i in range(n):
        # 성별을 골랐으면 그 성별, 아니면 여성/남성을 번갈아
        g = gender or ("f" if i % 2 == 0 else "m")
        # 몇 번째 얼굴인지 (성별 미선택이면 여성·남성이 각자 0,1번째 얼굴을 쓰도록)
        idx = i if gender else i // 2
        bg = FACE_BACKGROUNDS[i % len(FACE_BACKGROUNDS)]
        # 두 번째 얼굴부터는 왼쪽으로 살짝 겹쳐서 프로필 사진 모음처럼 보이게 함
        overlap = "" if i == 0 else "margin-left:-12px;"
        # 동그랗게(50%) + 흰 테두리 + 배경색을 입히는 CSS
        style = (f"width:{size}px;height:{size}px;border-radius:50%;"
                 f"border:3px solid white;background:{bg};{overlap}")
        if HAS_DICEBEAR:
            src = face_data_uri(g, decade, idx, bg)
            imgs += f'<img src="{src}" alt="avatar" style="{style}">'
        else:
            # dicebear 패키지가 없으면 이모지로 대체
            emoji = ["🙂", "😊", "😎", "🤗"][i % 4]
            imgs += (f'<div style="{style}display:flex;align-items:center;'
                     f'justify-content:center;font-size:24px;">{emoji}</div>')
    return f'<div style="display:flex;margin-top:22px;">{imgs}</div>'


def single_face(gender, age, size=72, idx=0, bg="#ffe4ec"):
    """동그란 얼굴 하나를 <img> HTML 로 만든다. (페르소나 카드처럼 얼굴 한 개가 필요할 때 사용)

    gender : 'f' / 'm'
    age    : 얼굴에 반영할 나이 (머리색, 안경 등이 나이대에 맞춰짐)
    size   : 얼굴 크기(px)
    idx    : 같은 성별·나이대 안에서 몇 번째 얼굴인지 (다른 얼굴을 보고 싶으면 숫자를 바꾸세요)
    bg     : 얼굴 뒤 배경색
    """
    style = (f"width:{size}px;height:{size}px;border-radius:50%;border:3px solid white;"
             f"background:{bg};box-shadow:0 6px 16px rgba(58,26,37,0.12);")
    if HAS_DICEBEAR:
        src = face_data_uri(gender, age_group_of(age), idx, bg)
        return f'<img src="{src}" alt="avatar" style="{style}">'
    # dicebear 패키지가 없으면 이모지로 대체
    return (f'<div style="{style}display:flex;align-items:center;justify-content:center;'
            f'font-size:{size // 2}px;">🙂</div>')


def input_card_html(gender, age):
    """'사용자 정보 입력' 카드 전체(제목 + 설명 + 얼굴들 + 안내 문구)를 HTML 로 만든다.
    app.py 에서 이 결과를 화면에 그려요."""
    return f"""
<div class="feature-card" style="min-height: auto;">
<div class="feature-title">👤 사용자 정보 입력</div>
<div class="feature-text">프로필에 등록된 사용자 정보를 입력해주세요.</div>
{face_stack(gender, age)}
<div style="margin-top:12px;font-size:12px;color:#aaa;">프로필 예시 이미지 · 예측에는 사용되지 않아요</div>
</div>
"""
