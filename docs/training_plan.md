# NER 모델 학습 플랜

## 목표

한국어 PII(개인정보) 탐지를 위한 NER 모델 학습.  
STT(음성 인식) 텍스트와 문어체 텍스트 모두를 처리할 수 있는 단일 모델을 목표로 한다.

---

## 데이터 구성 전략

총 학습 데이터를 4개 구간으로 구성한다.

| 구분 | 비율 | 역할 |
|------|------|------|
| 문어체 합성 데이터 | 40% | 정형 PII 패턴 학습 |
| STT 구어체 합성 데이터 | 40% | 구어체·음성 인식 오류 패턴 학습 |
| 실제 STT 라벨링 데이터 | 10~20% | 실제 분포 앵커링 |
| Negative / Noise 데이터 | 10~20% | 오탐(FP) 억제 |

---

## 각 구간 상세

### 1. 문어체 합성 데이터 (40%)

**생성 방법**: `scripts/generate_synthetic.py` (mode=`written`)

포함 패턴:
- 고객 문의 / CS 메시지 형식
- 배송지 주소 포함 문장
- 이름 + 전화번호 + 이메일 복합 문장
- 카드번호 / 계좌번호 / 주민등록번호 포함 문장

주소 강화:
- `scripts/generate_addresses.py` 로 실제 도로명주소 기반 문어체 주소 생성
- 형식 예: `서울특별시 강남구 테헤란로 123`, `강남구 테헤란로 123`

### 2. STT 구어체 합성 데이터 (40%)

**생성 방법**: `scripts/generate_synthetic.py` (mode=`stt`)

포함 패턴:
- `[상담원] / [고객]` 화자 구분 구조
- 구어체 숫자 읽기: `공일공 일이삼사 오육칠팔`, `백이십삼`
- 이메일 구어체: `골뱅이`, `닷컴`, `at`
- 발화 추임새: `아`, `어`, `네`, `그`
- 날짜 구어체: `팔십오년 시월`, `이십팔일`
- 상담원 반복 확인 발화

주소 강화:
- `scripts/generate_addresses.py` STT 변형 포함
- 형식 예: `강남구 테헤란로 쪽이에요`, `서울 강남 쪽이요`, `테헤란로 백이십삼`

### 3. 실제 STT 라벨링 데이터 (10~20%)

**목적**: 합성 데이터의 분포 편향을 실제 발화 패턴으로 보정하는 앵커 역할

수집 방법:
- 실제 상담 STT 텍스트 일부를 수동 라벨링
- 공개 한국어 NER 데이터셋(KLUE-NER 등) 중 적합한 라벨 매핑 후 혼합
- 비식별화된 실제 발화 데이터 사용 (법령 준수 필수)

요구 사항:
- 동일 JSONL 포맷 (`id`, `category`, `text`, `entities`)
- `"source": "human"` 필드로 구분
- 최소 500~1,000건 확보 권장

### 4. Negative / Noise 데이터 (10~20%)

**생성 방법**: `scripts/generate_synthetic.py` (mode=`all`, `--negative-ratio` 조정)

포함 패턴:
- 개인정보 없는 일반 문장 (기업명, 정책, 상품명 등)
- 숫자가 포함되지만 PII가 아닌 경우: 상품코드, 가격, 날짜(사건일)
- 고유명사가 포함되지만 인명이 아닌 경우: 지명, 브랜드명
- 개인정보처럼 보이는 노이즈: 불완전한 전화번호, 비정형 숫자열

목적:
- 오탐(False Positive) 억제
- 문맥 기반 판단 능력 강화

---

## 학습 포맷

### BIO Tagging

```
홍길동    B-NAME
은       O
010     B-PHONE
-       I-PHONE
1234    I-PHONE
-       I-PHONE
5678    I-PHONE
로       O
연락     O
주세요   O
```

### 토크나이저 전략

- 형태소 단위 또는 wordpiece 중 선택
- 추천: **wordpiece** (klue/roberta-base 기준) — 구어체 띄어쓰기 오류에 강함

---

## 추천 베이스 모델

| 모델 | 특징 | 우선순위 |
|------|------|---------|
| `klue/roberta-base` | KLUE 벤치마크 최고 성능, 한국어 전용 | ★ 1순위 |
| `monologg/koelectra-base-v3-discriminator` | 경량, 속도 우선 시 | ★ 2순위 |
| `xlm-roberta-base` | 다국어, 영문 혼용 텍스트 포함 시 | 필요 시 |

---

## 구현 단계 (Phase)

### Phase 0 — 데이터 파이프라인 완성 `[완료]`

- [x] `generate_synthetic.py` — 문어체 / STT 합성 데이터 생성
- [x] `load_road_address.py` — 실제 도로명주소 로딩
- [x] `generate_addresses.py` — 주소 변형 7종 생성
- [x] `convert_klue_ner.py` — KLUE-NER → 프로젝트 JSONL 변환 (PS→NAME, LC→ADDRESS, OG→ORG)
- [x] `mix_dataset.py` — 소스별 비율 혼합 + 중복 제거 + train/valid/test 분리

### Phase 1 — 데이터 품질 검증 `[mix_dataset.py에 내장]`

- [x] 레이블 분포 출력 (`mix_dataset.py` 실행 시 자동 출력)
- [x] 중복 문장 제거 (text hash 기준, `mix_dataset.py` 내 `_deduplicate`)
- [x] train / valid / test 분리 (기본 8:1:1, `--split` 인자로 조정)
- [ ] 오프셋(span) 정합성 검증 — `generate_synthetic.py`의 `validate_sample()` 활용

### Phase 2 — 베이스라인 모델 학습 `[완료]`

- [x] `scripts/train.py` — HuggingFace `Trainer` 기반, `klue/roberta-base` + TokenClassification head
- [x] `configs/train.yaml` — 학습 하이퍼파라미터 설정
- [x] 체크포인트 저장: `models/checkpoints/v1/best/`

```bash
python scripts/train.py
python scripts/train.py --config configs/train.yaml
python scripts/train.py --train data/processed/train.jsonl --valid data/processed/valid.jsonl
```

### Phase 3 — 평가 `[완료]`

- [x] `scripts/evaluate.py` — Entity-level F1(seqeval), Character-level Recall, Leakage Rate
- [x] PII 유형별 세분화 리포트
- [x] 결과 저장: `data/generated/eval_result.json`

```bash
python scripts/evaluate.py --model models/checkpoints/v1/best --test data/processed/test.jsonl
```

### Phase 4 — 반복 개선

- [ ] 오탐 / 미탐 사례 수집 → negative 데이터 보강
- [ ] 실제 STT 라벨링 데이터 추가
- [ ] 주소 생성 다양성 확대 (지번주소, 아파트 동호수 등)

---

## 디렉토리 구조 (목표)

```
data/
├── 202605_RoadAddress_KR_Full/   # 원본 (git 제외)
├── generated/
│   ├── road_address_components.json
│   ├── addresses.jsonl           # generate_addresses.py 출력 (1,000건)
│   ├── synthetic_written.jsonl   # generate_synthetic.py --mode written (4,000건)
│   ├── synthetic_stt.jsonl       # generate_synthetic.py --mode stt (4,000건)
│   ├── negative.jsonl            # generate_synthetic.py --negative-ratio 1.0 (2,000건)
│   └── klue_ner.jsonl            # convert_klue_ner.py 출력 (21,008건)
└── processed/
    ├── train.jsonl               # mix_dataset.py 출력 (6,541건)
    ├── valid.jsonl               # (817건)
    └── test.jsonl                # (819건)

models/
└── checkpoints/
    └── v1/

scripts/
├── labels.py                     # ✅ 레이블 정의
├── generate_synthetic.py         # ✅ 문어체/STT 합성 PII 데이터 생성
├── load_road_address.py          # ✅ 공개 도로명주소 로딩
├── generate_addresses.py         # ✅ 주소 변형 7종 생성
├── convert_klue_ner.py           # ✅ KLUE-NER → JSONL 변환
├── mix_dataset.py                # ✅ 소스 혼합 + train/valid/test 분리
├── train.py                      # ✅ 모델 학습 (klue/roberta-base)
└── evaluate.py                   # ✅ 평가 (F1, Char Recall, Leakage Rate)

configs/
└── train.yaml                    # ✅ 학습 하이퍼파라미터
```

---

## 우선순위 요약

| 순서 | 작업 | 파일 | 상태 |
|------|------|------|------|
| 1 | 외부 NER 데이터 변환 | `scripts/convert_klue_ner.py` | ✅ 완료 |
| 2 | 데이터 혼합 + 분리 | `scripts/mix_dataset.py` | ✅ 완료 |
| 3 | 베이스라인 학습 | `scripts/train.py` | 대기 |
| 4 | 평가 | `scripts/evaluate.py` | 대기 |
