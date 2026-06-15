# Data Card

## Dataset Name

Korean PII NER Dataset (Synthetic + KLUE-NER)

## Dataset Description

한국어 개인정보 탐지 NER 모델 학습을 위한 합성 데이터셋입니다. 문어체 CS 메시지, STT 구어체 상담 대화, 실주소 기반 주소 변형, KLUE-NER 공개 데이터를 혼합하여 구성하였습니다.

## Data Sources

| 소스 | 파일 | 건수 | 설명 |
|------|------|------|------|
| 문어체 합성 | `synthetic_written.jsonl` | 4,000 | 템플릿 기반 CS/배송 메시지 패턴 |
| STT 합성 | `synthetic_stt.jsonl` | 4,000 | 상담원-고객 구어체 대화 패턴 |
| Negative | `negative.jsonl` | 2,000 | PII 없는 일반 문장 |
| 주소 | `addresses.jsonl` | 1,000 | 행안부 도로명주소 기반 주소 변형 7종 |
| KLUE-NER | `klue_ner.jsonl` | 21,008 | KLUE train split (PS→NAME, LC→ADDRESS, OG→ORG) |

## Processed Split

`mix_dataset.py`로 4:4:1:1 비율 혼합 후 8:1:1 분리 (총 10,000 목표, 중복 제거 후 8,177건)

| Split | 파일 | 건수 |
|-------|------|------|
| Train | `data/processed/train.jsonl` | 6,541 |
| Valid | `data/processed/valid.jsonl` | 817 |
| Test | `data/processed/test.jsonl` | 819 |

## Train Entity Distribution

| Entity Type | Count |
|-------------|-------|
| NAME | 2,714 |
| PHONE | 1,967 |
| DATE_OF_BIRTH | 1,586 |
| ADDRESS | 1,272 |
| EMAIL | 932 |
| ID | 765 |
| ACCOUNT | 559 |
| REGION | 486 |
| JOB | 486 |
| ORG | 314 |
| IP | 279 |
| CARD | 150 |
| CAR_NUMBER | 130 |

## Included PII Types

| Type | Description | 예시 |
|------|-------------|------|
| NAME | 이름 | 김민수, 김 민수 |
| PHONE | 전화번호 (문어체/구어체) | 010-1234-5678, 공일공 일이삼사 오육칠팔 |
| EMAIL | 이메일 (문어체/구어체) | user@example.com, 유저 골뱅이 example 닷 com |
| ADDRESS | 주소 | 서울특별시 강남구 테헤란로 123 |
| REGION | 지역 언급 (구어체) | 서울 강남 쪽이요 |
| DATE_OF_BIRTH | 생년월일 | 900101, 90년 일월 일일 |
| RRN | 주민등록번호 | 900101-1234567 |
| CARD | 카드번호 | 1234-5678-9012-3456 |
| ACCOUNT | 계좌번호 | 110-123-456789 |
| ID | 사용자 ID | user1234 |
| CAR_NUMBER | 차량번호 | 12가 3456 |
| IP | IP 주소 | 192.168.0.1 |
| JOB | 직업 | 사무직이에요 |
| ORG | 기관/회사명 | 메리츠화재, 서울대학교병원 |

## STT Characteristics

- `[상담원]` / `[고객]` 화자 구분 구조
- 구어체 숫자 읽기: `공일공 일이삼사 오육칠팔`, `백이십삼`
- 이메일 구어체: `골뱅이`, `닷컴`, `at`
- 발화 추임새: `아`, `어`, `네`, `그`
- 날짜 구어체: `팔십오년 시월 이십팔일`
- 상담원 반복 확인 발화 패턴

## Address Data Source

행정안전부 도로명주소 한글 데이터 (2025년 5월 기준, `data/202605_RoadAddress_KR_Full/`)  
17개 시도, 시군구 232개, 도로명 39,070개 기반으로 7종 주소 변형 생성:
- 문어체 전체 (`서울특별시 강남구 테헤란로 123`)
- 시도 축약 (`서울 강남구 테헤란로 123`)
- 시도 생략 (`강남구 테헤란로 123`)
- 구어체 한자식 숫자 (`테헤란로 백이십삼`)
- 구어체 낱자 숫자 (`테헤란로 일이삼`)
- STT 방향 표현 (`강남구 테헤란로 근처예요`)
- STT 지역 표현 (`서울 강남 쪽이요`) → REGION 레이블

## Privacy

본 데이터셋은 실제 개인을 식별할 수 있는 정보를 포함하지 않습니다.  
모든 PII 값은 가짜 생성기(`scripts/generate_synthetic.py`)로 생성된 합성 데이터입니다.  
주소는 실제 도로명 구성요소를 사용하나 건물번호 등은 무작위로 생성됩니다.
