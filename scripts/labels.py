"""
NER 레이블 정의. 모든 스크립트에서 공통으로 사용한다.
"""

LABEL_NAMES: list[str] = [
    "O",
    "B-NAME",        "I-NAME",
    "B-PHONE",       "I-PHONE",
    "B-EMAIL",       "I-EMAIL",
    "B-ADDRESS",     "I-ADDRESS",
    "B-REGION",      "I-REGION",
    "B-RRN",         "I-RRN",
    "B-CARD",        "I-CARD",
    "B-ACCOUNT",     "I-ACCOUNT",
    "B-DATE_OF_BIRTH", "I-DATE_OF_BIRTH",
    "B-CAR_NUMBER",  "I-CAR_NUMBER",
    "B-IP",          "I-IP",
    "B-ID",          "I-ID",
    "B-JOB",         "I-JOB",
    "B-ORG",         "I-ORG",
]

LABEL2ID: dict[str, int] = {label: idx for idx, label in enumerate(LABEL_NAMES)}
ID2LABEL: dict[int, str] = {idx: label for idx, label in enumerate(LABEL_NAMES)}

# KLUE-NER 레이블 → 우리 PII 타입 매핑 (매핑 없는 타입은 None → O로 처리)
KLUE_NER_MAP: dict[str, str | None] = {
    "PS": "NAME",
    "LC": "ADDRESS",
    "OG": "ORG",
    "DT": None,
    "TI": None,
    "QT": None,
}
