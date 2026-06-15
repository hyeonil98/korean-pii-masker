import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Optional


PLACEHOLDER_PATTERN = re.compile(r"\{([A-Z0-9_]+)\}")


# =========================
# Dictionaries
# =========================

SURNAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"
]

GIVEN_NAMES = [
    "민수", "서연", "지훈", "하준", "지우", "도윤", "예준", "수빈",
    "유진", "민재", "지민", "서준", "도현", "예은", "현우", "시우",
    "지아", "하윤", "은우", "준호"
]

BANKS = [
    "국민은행", "신한은행", "우리은행", "하나은행",
    "카카오뱅크", "토스뱅크", "농협", "기업은행"
]

CITIES = [
    "서울시", "부산시", "대구시", "인천시", "광주시",
    "대전시", "울산시", "경기도", "충남", "충북", "전남", "전북", "경남", "경북"
]

DISTRICTS = [
    "강남구", "마포구", "서초구", "송파구", "분당구", "해운대구",
    "유성구", "연수구", "보령시", "천안시", "청주시", "전주시"
]

ROADS = [
    "테헤란로", "월드컵북로", "판교역로", "센텀중앙로",
    "대학로", "중앙로", "충무로", "해안로", "서해로"
]

REGIONS = [
    "서울 강남", "서울 마포", "경기 성남", "충남 보령", "충북 청주",
    "부산 해운대", "대전 유성", "인천 연수", "전북 전주", "경남 창원"
]

JOBS = [
    "사무직", "유통쪽", "배달", "영업직", "자영업",
    "운전직", "현장직", "프리랜서", "주부", "교사", "간호사"
]

ORGS = [
    # 보험사
    "메리츠화재", "삼성화재", "현대해상", "DB손해보험",
    "한화생명", "교보생명", "롯데손해보험", "흥국화재",
    # 은행
    "우리은행", "국민은행", "카카오뱅크", "토스뱅크",
    "신한은행", "하나은행", "SC제일은행", "대구은행", "부산은행",
    # 병원
    "서울대학교병원", "삼성서울병원", "서울아산병원",
    "고려대학교병원", "가톨릭대학교서울성모병원",
    # 대학교
    "연세대학교", "고려대학교", "한양대학교", "성균관대학교", "이화여자대학교",
    # 기업
    "삼성전자", "LG전자", "현대자동차", "SK텔레콤", "KT",
    "카카오", "네이버", "쿠팡", "롯데그룹", "CJ그룹",
]

EMAIL_NAMES = [
    "minsu", "gildong", "user", "hello", "test", "seoyeon",
    "jihoon", "customer", "sample", "kim"
]

EMAIL_DOMAINS = [
    "example.com", "test.co.kr", "sample.net", "mail.com", "demo.co.kr"
]

FILLERS = [
    "", "", "", "아 ", "어 ", "음 ", "네 ", "4네 ", "그 ", "저 "
]


# =========================
# Korean number utilities
# =========================

DIGIT_TO_KOREAN = {
    "0": "공",
    "1": "일",
    "2": "이",
    "3": "삼",
    "4": "사",
    "5": "오",
    "6": "육",
    "7": "칠",
    "8": "팔",
    "9": "구",
}

MONTH_SPOKEN = {
    1: "일월",
    2: "이월",
    3: "삼월",
    4: "사월",
    5: "오월",
    6: "유월",
    7: "칠월",
    8: "팔월",
    9: "구월",
    10: "시월",
    11: "십일월",
    12: "십이월",
}

DAY_SPOKEN = {
    1: "일일",
    2: "이일",
    3: "삼일",
    4: "사일",
    5: "오일",
    6: "육일",
    7: "칠일",
    8: "팔일",
    9: "구일",
    10: "십일",
    11: "십일일",
    12: "십이일",
    13: "십삼일",
    14: "십사일",
    15: "십오일",
    16: "십육일",
    17: "십칠일",
    18: "십팔일",
    19: "십구일",
    20: "이십일",
    21: "이십일일",
    22: "이십이일",
    23: "이십삼일",
    24: "이십사일",
    25: "이십오일",
    26: "이십육일",
    27: "이십칠일",
    28: "이십팔일",
}


def digits_to_korean_digits(value: str, group: Optional[List[int]] = None) -> str:
    """
    "01012345678" -> "공일공 일이삼사 오육칠팔"
    """
    converted = "".join(DIGIT_TO_KOREAN[ch] for ch in value if ch.isdigit())

    if not group:
        return converted

    parts = []
    idx = 0
    for size in group:
        parts.append(converted[idx: idx + size])
        idx += size

    if idx < len(converted):
        parts.append(converted[idx:])

    return " ".join(parts)


# =========================
# Fake value generators
# =========================

def gen_name() -> str:
    style = random.random()
    name = random.choice(SURNAMES) + random.choice(GIVEN_NAMES)

    if style < 0.85:
        return name
    elif style < 0.93:
        # 김 민수
        return name[0] + " " + name[1:]
    else:
        # 김 민 수
        return " ".join(list(name))


def gen_phone() -> str:
    mid = random.randint(1000, 9999)
    last = random.randint(1000, 9999)

    formats = [
        f"010-{mid}-{last}",
        f"010{mid}{last}",
        f"010 {mid} {last}",
        f"010.{mid}.{last}",
        f"010/{mid}/{last}",
        f"010){mid}-{last}",
    ]

    return random.choice(formats)


def gen_phone_spoken() -> str:
    mid = random.randint(1000, 9999)
    last = random.randint(1000, 9999)
    raw = f"010{mid}{last}"

    formats = [
        digits_to_korean_digits(raw, [3, 4, 4]),
        f"공일공 {digits_to_korean_digits(str(mid))} {digits_to_korean_digits(str(last))}",
        f"공일공에 {digits_to_korean_digits(str(mid))}에 {digits_to_korean_digits(str(last))}",
        f"영일공 {digits_to_korean_digits(str(mid))} {digits_to_korean_digits(str(last))}",
    ]

    return random.choice(formats)


def gen_email() -> str:
    name = random.choice(EMAIL_NAMES)
    suffix = random.randint(1, 9999)
    domain = random.choice(EMAIL_DOMAINS)

    formats = [
        f"{name}{suffix}@{domain}",
        f"{name}.{suffix}@{domain}",
        f"{name}_{suffix}@{domain}",
        f"{name}+test{suffix}@{domain}",
    ]

    return random.choice(formats)


def gen_email_spoken() -> str:
    name = random.choice(EMAIL_NAMES)
    domain = random.choice(["example", "test", "sample", "mail"])
    tld = random.choice(["com", "net", "co kr"])

    formats = [
        f"{name} 골뱅이 {domain} 점 {tld}",
        f"{name} at {domain} dot {tld}",
        f"{name} 골뱅이 {domain} 닷 {tld}",
    ]

    return random.choice(formats)


def gen_address() -> str:
    city = random.choice(CITIES)
    district = random.choice(DISTRICTS)
    road = random.choice(ROADS)
    number = random.randint(1, 300)

    detail = random.choice([
        "",
        f" {random.randint(1, 120)}동 {random.randint(101, 2403)}호",
        f" {random.randint(1, 20)}층",
        f" {random.randint(101, 1500)}호",
    ])

    return f"{city} {district} {road} {number}{detail}"


def gen_address_short() -> str:
    return random.choice([
        random.choice(REGIONS),
        random.choice(DISTRICTS),
        f"{random.choice(DISTRICTS)} {random.choice(ROADS)}",
        f"{random.choice(REGIONS)} 쪽",
        f"{random.choice(REGIONS)} 근처",
    ])


def gen_region() -> str:
    region = random.choice(REGIONS)

    formats = [
        region,
        f"{region}이요",
        f"그냥 {region}",
        f"{region} 쪽이에요",
    ]

    return random.choice(formats)


def gen_dob_parts() -> Tuple[int, int, int]:
    year = random.randint(1960, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return year, month, day


def gen_dob() -> str:
    year, month, day = gen_dob_parts()

    formats = [
        f"{year}{month:02d}{day:02d}",
        f"{str(year)[2:]}{month:02d}{day:02d}",
        f"{year}-{month:02d}-{day:02d}",
        f"{year}년 {month}월 {day}일",
        f"{str(year)[2:]}년 {month}월 {day}일",
    ]

    return random.choice(formats)


def gen_dob_spoken() -> str:
    year, month, day = gen_dob_parts()
    yy = str(year)[2:]

    formats = [
        f"{digits_to_korean_digits(yy)}년 {MONTH_SPOKEN[month]} {DAY_SPOKEN[day]}",
        f"{digits_to_korean_digits(yy)} {MONTH_SPOKEN[month]} {DAY_SPOKEN[day]}",
        f"{yy}년 {month}월 {day}일",
        f"{digits_to_korean_digits(yy + str(month).zfill(2) + str(day).zfill(2))}",
    ]

    return random.choice(formats)


def gen_dob_yy() -> str:
    year = random.randint(1960, 2005)
    yy = str(year)[2:]

    formats = [
        yy,
        f"{yy}년",
        digits_to_korean_digits(yy),
        f"{digits_to_korean_digits(yy)}년",
    ]

    return random.choice(formats)


def gen_dob_yymm() -> str:
    year = random.randint(1960, 2005)
    month = random.randint(1, 12)
    yy = str(year)[2:]
    yymm = f"{yy}{month:02d}"

    formats = [
        yymm,
        digits_to_korean_digits(yymm),
        f"{digits_to_korean_digits(yy)}년 {MONTH_SPOKEN[month]}",
        f"{yy}년 {month}월",
    ]

    return random.choice(formats)


def gen_dob_mm() -> str:
    month = random.randint(1, 12)

    formats = [
        f"{month}",
        f"{month}월",
        MONTH_SPOKEN[month],
    ]

    return random.choice(formats)


def gen_dob_dd() -> str:
    day = random.randint(1, 28)

    formats = [
        f"{day}",
        f"{day}일",
        DAY_SPOKEN[day],
    ]

    return random.choice(formats)


def gen_rrn() -> str:
    year = random.randint(60, 99)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    front = f"{year:02d}{month:02d}{day:02d}"

    # 실제 주민등록번호가 아니라 합성/무작위 값
    back_first = random.choice(["1", "2", "3", "4"])
    back_rest = random.randint(100000, 999999)
    back = f"{back_first}{back_rest}"

    formats = [
        f"{front}-{back}",
        f"{front}{back}",
        f"{front} - {back}",
    ]

    return random.choice(formats)


def gen_card() -> str:
    parts = [
        random.randint(1000, 9999),
        random.randint(1000, 9999),
        random.randint(1000, 9999),
        random.randint(1000, 9999),
    ]

    formats = [
        f"{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}",
        f"{parts[0]} {parts[1]} {parts[2]} {parts[3]}",
        f"{parts[0]}{parts[1]}{parts[2]}{parts[3]}",
        f"****-****-****-{parts[3]}",
    ]

    return random.choice(formats)


def gen_account() -> str:
    formats = [
        f"{random.randint(100000, 999999)}-{random.randint(10, 99)}-{random.randint(100000, 999999)}",
        f"{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(10, 99)}",
        f"{random.randint(100000000000, 999999999999)}",
        f"{random.randint(1000, 9999)}-{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
    ]

    return random.choice(formats)


def gen_id() -> str:
    bases = ["user", "kim", "lee", "minsu", "guest", "customer", "alpha", "test"]
    formats = [
        f"{random.choice(bases)}{random.randint(100, 9999)}",
        f"{random.choice(bases)}_{random.randint(100, 9999)}",
        f"{random.choice(bases)}.{random.randint(100, 9999)}",
    ]
    return random.choice(formats)


def gen_car_number() -> str:
    korean_char = random.choice(["가", "나", "다", "라", "마", "거", "너", "더", "러", "버", "서", "어", "저", "하"])
    formats = [
        f"{random.randint(10, 99)}{korean_char} {random.randint(1000, 9999)}",
        f"{random.randint(100, 999)}{korean_char}{random.randint(1000, 9999)}",
    ]

    return random.choice(formats)


def gen_ip() -> str:
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def gen_job() -> str:
    job = random.choice(JOBS)

    formats = [
        job,
        f"{job}이에요",
        f"{job} 쪽이에요",
        f"{job}입니다",
    ]

    return random.choice(formats)


def gen_org() -> str:
    return random.choice(ORGS)


def gen_bank() -> str:
    return random.choice(BANKS)


GENERATORS: Dict[str, Callable[[], str]] = {
    "NAME": gen_name,
    "PHONE": gen_phone,
    "PHONE_SPOKEN": gen_phone_spoken,
    "EMAIL": gen_email,
    "EMAIL_SPOKEN": gen_email_spoken,
    "ADDRESS": gen_address,
    "ADDRESS_SHORT": gen_address_short,
    "REGION": gen_region,
    "DOB": gen_dob,
    "DOB_SPOKEN": gen_dob_spoken,
    "DOB_YY": gen_dob_yy,
    "DOB_YYMM": gen_dob_yymm,
    "DOB_MM": gen_dob_mm,
    "DOB_DD": gen_dob_dd,
    "DATE_OF_BIRTH": gen_dob,
    "RRN": gen_rrn,
    "CARD": gen_card,
    "BANK": gen_bank,
    "ACCOUNT": gen_account,
    "ID": gen_id,
    "CAR_NUMBER": gen_car_number,
    "IP": gen_ip,
    "JOB": gen_job,
    "ORG": gen_org,
}


# placeholder -> label type
# BANK는 단독으로 개인정보성이 낮다고 보고 기본 라벨 제외.
LABEL_MAP: Dict[str, Optional[str]] = {
    "NAME": "NAME",
    "PHONE": "PHONE",
    "PHONE_SPOKEN": "PHONE",
    "EMAIL": "EMAIL",
    "EMAIL_SPOKEN": "EMAIL",
    "ADDRESS": "ADDRESS",
    "ADDRESS_SHORT": "ADDRESS",
    "REGION": "REGION",
    "DOB": "DATE_OF_BIRTH",
    "DOB_SPOKEN": "DATE_OF_BIRTH",
    "DOB_YY": "DATE_OF_BIRTH",
    "DOB_YYMM": "DATE_OF_BIRTH",
    "DOB_MM": "DATE_OF_BIRTH",
    "DOB_DD": "DATE_OF_BIRTH",
    "DATE_OF_BIRTH": "DATE_OF_BIRTH",
    "RRN": "RRN",
    "CARD": "CARD",
    "ACCOUNT": "ACCOUNT",
    "ID": "ID",
    "CAR_NUMBER": "CAR_NUMBER",
    "IP": "IP",
    "JOB": "JOB",
    "ORG": "ORG",
    "BANK": None,
}


# =========================
# Built-in templates
# =========================

BUILTIN_WRITTEN_TEMPLATES = [
    "{NAME} 고객님, 문의는 {PHONE}로 연락 주세요.",
    "제 이름은 {NAME}이고 연락처는 {PHONE}입니다.",
    "성함은 {NAME}, 전화번호는 {PHONE}입니다.",
    "답변은 {EMAIL}로 보내주세요.",
    "{NAME}입니다. 이메일은 {EMAIL}입니다.",
    "배송지는 {ADDRESS}입니다.",
    "배송 주소를 {ADDRESS}로 변경해주세요.",
    "수령인은 {NAME}, 연락처는 {PHONE}, 주소는 {ADDRESS}입니다.",
    "회원명은 {NAME}, 아이디는 {ID}입니다.",
    "{NAME}님의 생년월일은 {DATE_OF_BIRTH}입니다.",
    "환불 계좌는 {BANK} {ACCOUNT}입니다.",
    "예금주는 {NAME}입니다.",
    "{NAME} 명의의 {BANK} 계좌 {ACCOUNT}로 환불해주세요.",
    "카드 번호는 {CARD}입니다.",
    "차량번호는 {CAR_NUMBER}입니다.",
    "접속 IP는 {IP}입니다.",
    "사용자 {ID}가 {IP}에서 로그인했습니다.",
    "{NAME} / {PHONE} / {EMAIL} / {ADDRESS}",
    # ORG 포함 템플릿
    "{ORG} 고객센터입니다. {NAME} 고객님 맞으시죠?",
    "{ORG}에서 안내드립니다. 연락처는 {PHONE}입니다.",
    "가입하신 {ORG} 상품 관련하여 {EMAIL}로 안내드렸습니다.",
    "{NAME}님은 현재 {ORG} 고객이십니다.",
    "담당자: {NAME} / 소속: {ORG} / 연락처: {PHONE}",
    "{ORG} {NAME} 고객님, 계약 관련 문의는 {PHONE}로 주세요.",
    "소속 기관은 {ORG}이며, 담당자 연락처는 {PHONE}입니다.",
    "{NAME}님의 직장은 {ORG}으로 등록되어 있습니다.",
    "{ORG} 재직 증명 관련 문의를 {EMAIL}로 보내주세요.",
    "{ORG}에 재직 중인 {NAME}입니다. 연락처는 {PHONE}입니다.",
]

BUILTIN_STT_TEMPLATES = [
    "[상담원] 성함이 어떻게 되세요\n[고객] {NAME}이요\n[상담원] 네 {NAME}님 맞으시죠",
    "[상담원] 연락 가능한 번호가 어떻게 되세요\n[고객] {PHONE_SPOKEN}\n[상담원] 네 {PHONE_SPOKEN} 맞으세요",
    "[고객] 제 번호는 {PHONE}이에요\n[상담원] {PHONE}로 연락드리면 될까요",
    "[고객] 전번은 {PHONE_SPOKEN}입니다",
    "[상담원] 생년월일 몇 년 몇 월이세요\n[고객] {DOB_YYMM}\n[상담원] 일자는요\n[고객] {DOB_DD}",
    "[상담원] 주민번호 앞자리만 말씀해주세요\n[고객] {DOB}\n[상담원] 네 {DOB} 확인했습니다",
    "[상담원] 배우자님 생년월일 알려주세요\n[고객] {DOB_SPOKEN}\n[상담원] 네 {DOB_SPOKEN} 맞으시고요",
    "[상담원] 지역은 혹시 어디세요 주소는 안 나와 있거든요\n[고객] {REGION}\n[상담원] 네 {REGION} 확인했습니다",
    "[상담원] 주소는 어떻게 되세요\n[고객] {ADDRESS}\n[상담원] 네 {ADDRESS}로 등록되어 있습니다",
    "[상담원] 하시는 일은 뭘까요\n[고객] {JOB}\n[상담원] 네 {JOB}으로 확인하겠습니다",
    "[상담원] 아이디가 어떻게 되세요\n[고객] {ID}입니다\n[상담원] 네 {ID} 계정 확인했습니다",
    "[상담원] 메일 주소 알려주세요\n[고객] {EMAIL_SPOKEN}\n[상담원] 네 {EMAIL_SPOKEN} 맞으세요",
    "[상담원] 환불 계좌 알려주세요\n[고객] {BANK} {ACCOUNT}요\n[상담원] 예금주는 누구세요\n[고객] {NAME}입니다",
    # ORG 포함 STT 템플릿
    "[상담원] 현재 재직 중이신 회사가 어디세요\n[고객] {ORG}이요\n[상담원] 네 {ORG} 맞으시죠",
    "[상담원] 어느 기관 상품이세요\n[고객] {ORG}이요\n[상담원] 네 {ORG} 고객님 맞으시고요",
    "[상담원] 가입하신 보험사가 어디세요\n[고객] {ORG}입니다\n[상담원] {ORG} 확인했습니다",
    "[고객] 저 {ORG} 다니는데요 단체보험 문의드리려고요\n[상담원] 네 {ORG} 재직자 상품 안내드릴게요",
    "[상담원] 직장은 어디세요\n[고객] {ORG} 다녀요\n[상담원] 네 {ORG} 재직 확인하겠습니다",
    "[상담원] 계약자 성함이랑 회사명 말씀해주세요\n[고객] {NAME}이고요 {ORG}입니다\n[상담원] 네 {NAME}님 {ORG} 확인했습니다",
]

BUILTIN_NEGATIVE_TEMPLATES = [
    "서울시는 오늘 새로운 교통 정책을 발표했습니다.",
    "삼성전자는 신제품 출시 계획을 공개했습니다.",
    "홍길동전은 허균의 대표적인 고전 소설입니다.",
    "세종대왕은 한글을 창제했습니다.",
    "상품 코드 123456은 현재 품절 상태입니다.",
    "가격은 12,000원입니다.",
    "수량은 3개입니다.",
    "테스트 계정으로 로그인했습니다.",
    "국민은행은 새로운 서비스를 출시했습니다.",
    "신한은행 앱 업데이트가 완료되었습니다.",
    "강남역 근처 카페를 추천해주세요.",
    "보험료가 얼마 정도 나오는지 궁금합니다.",
    "암 진단자금은 보장 내용에 따라 달라질 수 있습니다.",
    "치료비는 연간 한도 내에서 보장됩니다.",
    "[상담원] 통화 괜찮으세요\n[고객] 네 괜찮아요",
    "[상담원] 문의하신 내용 확인했습니다\n[고객] 네 감사합니다",
]


# =========================
# Template loading
# =========================

def parse_template_file(path: Path) -> List[str]:
    """
    템플릿 파일 파싱.

    - 빈 줄로 구분된 블록은 하나의 템플릿으로 처리
    - 빈 줄이 없으면 각 줄을 하나의 템플릿으로 처리
    """
    content = path.read_text(encoding="utf-8").strip()

    if not content:
        return []

    blocks = re.split(r"\n\s*\n", content)

    templates = []

    if len(blocks) > 1:
        for block in blocks:
            block = block.strip()
            if block:
                templates.append(block)
    else:
        for line in content.splitlines():
            line = line.strip()
            if line:
                templates.append(line)

    return templates


def load_templates_from_dir(templates_dir: Path) -> Dict[str, List[str]]:
    """
    권장 구조:

    data/templates/
    ├── written/*.txt
    ├── stt/*.txt
    └── negative/*.txt
    """
    result = {
        "written": [],
        "stt": [],
        "negative": [],
    }

    for category in result.keys():
        category_dir = templates_dir / category

        if not category_dir.exists():
            continue

        for file_path in category_dir.glob("*.txt"):
            result[category].extend(parse_template_file(file_path))

    return result


def get_templates(templates_dir: Optional[str]) -> Dict[str, List[str]]:
    templates = {
        "written": BUILTIN_WRITTEN_TEMPLATES.copy(),
        "stt": BUILTIN_STT_TEMPLATES.copy(),
        "negative": BUILTIN_NEGATIVE_TEMPLATES.copy(),
    }

    if templates_dir:
        loaded = load_templates_from_dir(Path(templates_dir))

        for key in templates.keys():
            if loaded[key]:
                templates[key] = loaded[key]

    return templates


# =========================
# Rendering
# =========================

def maybe_add_stt_filler(template: str) -> str:
    """
    STT 데이터스럽게 앞에 짧은 추임새를 붙인다.
    span은 render_template에서 계산하므로 안전하다.
    """
    filler = random.choice(FILLERS)

    if not filler:
        return template

    lines = template.splitlines()

    if not lines:
        return template

    # 첫 번째 발화 내용에만 filler 추가
    # 예: [고객] {NAME}이요 -> [고객] 아 {NAME}이요
    first = lines[0]

    if "] " in first:
        speaker, utterance = first.split("] ", 1)
        lines[0] = f"{speaker}] {filler}{utterance}"
    else:
        lines[0] = filler + first

    return "\n".join(lines)


def render_template(template: str, sample_id: str, category: str) -> Dict:
    """
    placeholder를 치환하면서 entity span을 생성한다.
    """
    text = ""
    entities = []
    pos = 0

    for match in PLACEHOLDER_PATTERN.finditer(template):
        prefix = template[pos:match.start()]
        text += prefix

        key = match.group(1)

        if key not in GENERATORS:
            raise ValueError(f"Unknown placeholder: {key}")

        value = GENERATORS[key]()

        start = len(text)
        text += value
        end = len(text)

        label_type = LABEL_MAP.get(key)

        if label_type is not None:
            entities.append({
                "type": label_type,
                "start": start,
                "end": end,
                "text": value,
                "source": "synthetic",
                "placeholder": key,
            })

        pos = match.end()

    text += template[pos:]

    sample = {
        "id": sample_id,
        "category": category,
        "text": text,
        "entities": entities,
    }

    validate_sample(sample)

    return sample


def render_negative(template: str, sample_id: str) -> Dict:
    sample = {
        "id": sample_id,
        "category": "negative",
        "text": template,
        "entities": [],
    }

    validate_sample(sample)

    return sample


def validate_sample(sample: Dict) -> None:
    text = sample["text"]

    for ent in sample["entities"]:
        start = ent["start"]
        end = ent["end"]
        ent_text = ent["text"]

        if text[start:end] != ent_text:
            raise ValueError(
                f"Offset mismatch in {sample['id']}: "
                f"expected={ent_text!r}, actual={text[start:end]!r}, "
                f"start={start}, end={end}"
            )


# =========================
# Dataset generation
# =========================

def choose_category(mode: str, negative_ratio: float) -> str:
    if random.random() < negative_ratio:
        return "negative"

    if mode == "written":
        return "written"

    if mode == "stt":
        return "stt"

    if mode == "all":
        return random.choice(["written", "stt"])

    raise ValueError(f"Invalid mode: {mode}")


def generate_dataset(
    num_samples: int,
    mode: str,
    negative_ratio: float,
    templates: Dict[str, List[str]],
) -> List[Dict]:
    samples = []

    for i in range(num_samples):
        category = choose_category(mode, negative_ratio)
        sample_id = f"synthetic-{category}-{i:06d}"

        if category == "negative":
            template = random.choice(templates["negative"])
            sample = render_negative(template, sample_id)
        else:
            template = random.choice(templates[category])

            if category == "stt":
                template = maybe_add_stt_filler(template)

            sample = render_template(template, sample_id, category)

        samples.append(sample)

    return samples


def write_jsonl(samples: List[Dict], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")


def print_stats(samples: List[Dict]) -> None:
    category_count = {}
    entity_count = {}

    for sample in samples:
        category = sample["category"]
        category_count[category] = category_count.get(category, 0) + 1

        for ent in sample["entities"]:
            ent_type = ent["type"]
            entity_count[ent_type] = entity_count.get(ent_type, 0) + 1

    print("\n[Dataset Stats]")
    print("categories:")
    for key, value in sorted(category_count.items()):
        print(f"  - {key}: {value}")

    print("entities:")
    for key, value in sorted(entity_count.items()):
        print(f"  - {key}: {value}")


# =========================
# CLI
# =========================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic Korean PII datasets for written text and STT-style conversations."
    )

    parser.add_argument(
        "--num-samples",
        type=int,
        default=1000,
        help="Number of samples to generate.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/generated/synthetic.jsonl",
        help="Output JSONL file path.",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["all", "written", "stt"],
        default="all",
        help="Dataset mode.",
    )

    parser.add_argument(
        "--negative-ratio",
        type=float,
        default=0.2,
        help="Ratio of negative samples.",
    )

    parser.add_argument(
        "--templates-dir",
        type=str,
        default=None,
        help="Optional templates directory. Expected subdirs: written, stt, negative.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if not 0 <= args.negative_ratio <= 1:
        raise ValueError("--negative-ratio must be between 0 and 1.")

    random.seed(args.seed)

    templates = get_templates(args.templates_dir)

    for key in ["written", "stt", "negative"]:
        if not templates[key]:
            raise ValueError(f"No templates found for category: {key}")

    samples = generate_dataset(
        num_samples=args.num_samples,
        mode=args.mode,
        negative_ratio=args.negative_ratio,
        templates=templates,
    )

    write_jsonl(samples, args.output)

    print(f"\nSaved: {args.output}")
    print_stats(samples)


if __name__ == "__main__":
    main()
