# korean-pii-masker

한국어 텍스트에서 개인정보 및 민감정보를 탐지하고 마스킹하기 위한 프로젝트입니다.

이 프로젝트는 정규식 기반 탐지기와 한국어 NER(Named Entity Recognition) 모델을 함께 사용하여 이름, 전화번호, 이메일, 주소, 주민등록번호, 카드번호, 계좌번호 등 다양한 개인정보를 탐지하고 비식별화하는 것을 목표로 합니다.

---

## Overview

개인정보 마스킹은 단순히 특정 패턴을 치환하는 작업만으로는 충분하지 않습니다.

예를 들어 전화번호, 이메일, 주민등록번호처럼 형식이 명확한 정보는 정규식 기반 탐지가 효과적이지만, 이름, 주소, 기관명처럼 문맥에 따라 달라지는 정보는 NER 모델이 필요합니다.

본 프로젝트는 다음과 같은 하이브리드 구조를 지향합니다.

```text
Input Text
   ↓
Preprocessing
   ↓
PII Detection
  ├─ Regex-based Recognizer
  ├─ Korean NER Recognizer
  ├─ Dictionary-based Recognizer
  └─ Context-aware Postprocessor
   ↓
Span Merge & Conflict Resolution
   ↓
Masking Policy Engine
   ↓
Masked Text
```

## Features

- 한국어 개인정보 탐지
- 정규식 기반 개인정보 탐지
- NER 기반 개인정보 탐지
- 개인정보 유형별 마스킹 정책 적용
- 탐지 결과 span 병합
- 부분 마스킹 / 전체 마스킹 지원
- 학습 데이터셋 구축 및 평가 파이프라인 제공 예정

## Supported PII Types

현재 또는 향후 지원 예정인 개인정보 유형은 다음과 같습니다.

| Type | Description | Example |
|------|-------------|---------|
| NAME | 이름 | 홍길동 |
| PHONE | 전화번호 | 010-1234-5678 |
| EMAIL | 이메일 | user@example.com |
| RRN | 주민등록번호 | 900101-1234567 |
| ADDRESS | 주소 | 서울시 강남구 테헤란로 |
| CARD | 카드번호 | 1234-5678-9012-3456 |
| ACCOUNT | 계좌번호 | 110-123-456789 |
| DATE_OF_BIRTH | 생년월일 | 1990년 1월 1일 |
| CAR_NUMBER | 차량번호 | 12가 3456 |
| IP | IP 주소 | 192.168.0.1 |
| ID | 사용자 ID | user123 |
| ORG | 기관명/회사명 | 오픈AI코리아 |

## Example

**Input**

```
홍길동 고객님, 주문하신 상품은 서울시 강남구 테헤란로 123으로 배송됩니다.
문의는 010-1234-5678 또는 gildong@example.com으로 연락 주세요.
```

**Output**

```
홍** 고객님, 주문하신 상품은 서울시 강남구 ***로 배송됩니다.
문의는 010-****-5678 또는 g******@example.com으로 연락 주세요.
```

또는 정책에 따라 다음과 같이 치환할 수도 있습니다.

```
[NAME] 고객님, 주문하신 상품은 [ADDRESS]로 배송됩니다.
문의는 [PHONE] 또는 [EMAIL]으로 연락 주세요.
```

## Project Structure

```
korean-pii-masker/
├── README.md
├── requirements.txt
├── configs/
│   └── default.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
├── notebooks/
├── src/
│   └── pii_masker/
│       ├── __init__.py
│       ├── recognizers/
│       │   ├── regex_recognizer.py
│       │   ├── ner_recognizer.py
│       │   └── dictionary_recognizer.py
│       ├── masking/
│       │   ├── policy.py
│       │   └── masker.py
│       ├── postprocessing/
│       │   ├── span_merger.py
│       │   └── context_filter.py
│       ├── training/
│       │   ├── dataset.py
│       │   └── trainer.py
│       └── evaluation/
│           └── metrics.py
├── tests/
└── examples/
    └── quickstart.py
```

## Installation

```bash
git clone https://github.com/your-username/korean-pii-masker.git
cd korean-pii-masker

pip install -r requirements.txt
```

## Quick Start

아래 코드는 예시이며, 실제 구현에 따라 변경될 수 있습니다.

```python
from pii_masker import PIIMasker

masker = PIIMasker()

text = """
홍길동 고객님, 문의는 010-1234-5678 또는 gildong@example.com으로 연락 주세요.
"""

masked_text = masker.mask(text)

print(masked_text)
```

**Result**

```
홍** 고객님, 문의는 010-****-5678 또는 g******@example.com으로 연락 주세요.
```

## Detection Result Example

탐지기는 다음과 같은 형태의 결과를 반환하는 것을 목표로 합니다.

```json
[
  {
    "type": "NAME",
    "text": "홍길동",
    "start": 0,
    "end": 3,
    "score": 0.98,
    "source": "ner"
  },
  {
    "type": "PHONE",
    "text": "010-1234-5678",
    "start": 12,
    "end": 25,
    "score": 1.0,
    "source": "regex"
  }
]
```

## Masking Policies

개인정보 유형별로 다른 마스킹 정책을 적용할 수 있습니다.

| Type | Original | Masked |
|------|----------|--------|
| NAME | 홍길동 | 홍** |
| PHONE | 010-1234-5678 | 010-\*\*\*\*-5678 |
| EMAIL | gildong@example.com | g\*\*\*\*\*\*@example.com |
| RRN | 900101-1234567 | 900101-1\*\*\*\*\*\* |
| CARD | 1234-5678-9012-3456 | \*\*\*\*-\*\*\*\*-\*\*\*\*-3456 |
| ADDRESS | 서울시 강남구 테헤란로 123 | 서울시 강남구 *** |
| ACCOUNT | 110-123-456789 | [ACCOUNT] |

## NER Label Schema

NER 모델 학습에는 BIO tagging 방식을 사용합니다.

**Example Sentence**

```
홍길동은 서울시 강남구에 거주합니다.
```

**BIO Labels**

```
홍길동    B-NAME
은       O
서울시    B-ADDRESS
강남구    I-ADDRESS
에       O
거주합니다 O
.        O
```

**Supported Labels**

```
B-NAME, I-NAME
B-PHONE, I-PHONE
B-EMAIL, I-EMAIL
B-RRN, I-RRN
B-ADDRESS, I-ADDRESS
B-CARD, I-CARD
B-ACCOUNT, I-ACCOUNT
B-DATE_OF_BIRTH, I-DATE_OF_BIRTH
B-CAR_NUMBER, I-CAR_NUMBER
B-IP, I-IP
B-ID, I-ID
B-ORG, I-ORG
O
```

## Dataset

본 프로젝트에서는 다음과 같은 방식으로 데이터셋을 구축하는 것을 권장합니다.

### 1. Synthetic Data

템플릿 기반으로 가상의 개인정보 데이터를 생성합니다.

```
{NAME} 고객님, 배송지는 {ADDRESS}입니다.
문의는 {PHONE} 또는 {EMAIL}로 연락 주세요.
```

예시:

```
김민수 고객님, 배송지는 서울시 강남구 테헤란로 123입니다.
문의는 010-1234-5678 또는 minsu@example.com으로 연락 주세요.
```

### 2. Public NER Dataset

한국어 NER 데이터셋을 활용하여 이름, 주소, 기관명 등 일반 개체명 인식 능력을 학습할 수 있습니다.

### 3. Domain-specific Data

실제 서비스 환경의 문장 패턴을 반영한 도메인별 데이터를 추가로 구축합니다.

단, 실제 개인정보가 포함된 데이터를 사용할 경우 반드시 개인정보 보호 정책과 관련 법령을 준수해야 합니다.

## Training

학습 스크립트는 추후 추가 예정입니다.

예상 학습 방식:

```bash
python -m pii_masker.training.trainer \
  --config configs/default.yaml \
  --train data/processed/train.jsonl \
  --valid data/processed/valid.jsonl
```

추천 모델 후보:

- `klue/roberta-base`
- `monologg/koelectra-base-v3-discriminator`
- `kykim/bert-kor-base`
- `xlm-roberta-base`

## Evaluation

개인정보 마스킹 모델은 일반적인 accuracy보다 개인정보 누락 여부가 중요합니다.

주요 평가 지표:

| Metric | Description |
|--------|-------------|
| Precision | 탐지한 개인정보 중 실제 개인정보 비율 |
| Recall | 실제 개인정보 중 탐지한 비율 |
| F1-score | Precision과 Recall의 조화 평균 |
| Entity-level F1 | 개체 단위 F1 |
| Character-level Recall | 문자 단위 누락률 |
| Leakage Rate | 마스킹 후 남은 개인정보 비율 |

개인정보 보호 목적에서는 특히 Recall과 Leakage Rate를 중요하게 봅니다.

## Roadmap

- [x] 정규식 기반 탐지기 구현
  - [x] 전화번호 탐지
  - [x] 이메일 탐지
  - [x] 주민등록번호 탐지
  - [x] 카드번호 탐지
  - [x] IP 주소 탐지
  - [x] 차량번호 탐지
- [ ] NER 학습 데이터 포맷 정의
- [ ] 한국어 NER 모델 학습 파이프라인 구현
- [ ] span merge 로직 구현
- [ ] 마스킹 정책 엔진 구현
- [ ] 평가 스크립트 구현
- [ ] CLI 지원
- [ ] REST API 지원
- [ ] Docker 지원

## CLI Usage

추후 지원 예정입니다.

```bash
pii-masker mask --text "홍길동님, 010-1234-5678로 연락 주세요."
```

결과:

```
홍**님, 010-****-5678로 연락 주세요.
```

파일 단위 처리:

```bash
pii-masker mask-file --input input.txt --output output.txt
```

## API Usage

추후 지원 예정입니다.

```
POST /mask
Content-Type: application/json
```

```json
{
  "text": "홍길동님, 010-1234-5678로 연락 주세요."
}
```

Response:

```json
{
  "masked_text": "홍**님, 010-****-5678로 연락 주세요.",
  "entities": [
    {
      "type": "NAME",
      "text": "홍길동",
      "start": 0,
      "end": 3,
      "score": 0.98
    },
    {
      "type": "PHONE",
      "text": "010-1234-5678",
      "start": 6,
      "end": 19,
      "score": 1.0
    }
  ]
}
```

## Privacy Notice

이 프로젝트는 개인정보 보호와 비식별화를 돕기 위한 도구입니다.

하지만 자동화된 개인정보 탐지 모델은 모든 개인정보를 완벽하게 탐지하지 못할 수 있습니다. 따라서 실제 서비스나 운영 환경에 적용할 경우 다음 사항을 권장합니다.

- 마스킹 결과에 대한 주기적 검수
- 도메인별 테스트셋 구축
- 미탐/오탐 사례 수집
- 중요 데이터에 대한 사람 검수 절차
- 원문 로그 저장 최소화
- 접근 권한 통제
- 암호화 저장
- 관련 법령 및 내부 보안 정책 준수

## Limitations

- NER 모델은 문맥에 따라 이름, 주소, 기관명을 잘못 탐지할 수 있습니다.
- 정규식 기반 탐지는 비정형 표현에 약할 수 있습니다.
- 마스킹된 데이터도 다른 정보와 결합될 경우 재식별 위험이 있을 수 있습니다.
- 실제 개인정보가 포함된 데이터셋을 사용할 경우 별도의 보안 및 법적 검토가 필요합니다.

## Contributing

기여는 언제든 환영합니다.

기여 가능한 영역:

- 정규식 패턴 개선
- 한국어 NER 데이터셋 추가
- 마스킹 정책 추가
- 평가 지표 개선
- 문서 개선
- 테스트 케이스 추가

## License

This project is licensed under the MIT License.

## Disclaimer

본 프로젝트는 연구 및 개발 목적으로 제공됩니다.
프로젝트 사용으로 인해 발생하는 개인정보 보호, 법적 책임, 보안 사고 등에 대해서는 사용자가 직접 검토하고 책임져야 합니다.
