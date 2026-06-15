# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

한국어 텍스트에서 개인정보를 탐지하고 마스킹하는 프로젝트. 현재는 NER 모델 학습을 위한 **합성 데이터 생성 파이프라인** 구축 단계이며, 탐지기/마스킹 엔진은 미구현 상태.

## Commands

```bash
# 합성 PII 데이터 생성 (문어체/STT)
python scripts/generate_synthetic.py --mode written --num-samples 4000 --output data/generated/synthetic_written.jsonl
python scripts/generate_synthetic.py --mode stt --num-samples 4000 --output data/generated/synthetic_stt.jsonl --negative-ratio 0.0

# 합성 negative 데이터 생성
python scripts/generate_synthetic.py --mode all --num-samples 2000 --negative-ratio 1.0 --output data/generated/negative.jsonl

# 실제 주소 기반 합성 주소 샘플 생성 → data/generated/addresses.jsonl
python scripts/generate_addresses.py --sample-rate 0.01 --num-samples 1000

# 도로명주소 원본 데이터 로딩 → data/generated/road_address_components.json
python scripts/load_road_address.py --sample-rate 0.01

# KLUE-NER 데이터 변환 → data/generated/klue_ner.jsonl  (datasets 패키지 필요)
python scripts/convert_klue_ner.py --split train

# 데이터 혼합 + train/valid/test 분리 → data/processed/
python scripts/mix_dataset.py \
  --source data/generated/synthetic_written.jsonl:0.40 \
  --source data/generated/synthetic_stt.jsonl:0.40 \
  --source data/generated/klue_ner.jsonl:0.10 \
  --source data/generated/negative.jsonl:0.10 \
  --total 10000

# 모델 학습 → models/checkpoints/v1/best/
python scripts/train.py
python scripts/train.py --config configs/train.yaml

# 평가 → data/generated/eval_result.json
python scripts/evaluate.py --model models/checkpoints/v1/best --test data/processed/test.jsonl
```

모든 스크립트는 `--help` 로 인자 확인 가능. 경로 기본값은 `__file__` 기준 절대경로로 설정되어 있어 어느 디렉토리에서 실행해도 동작.

## Architecture

### 데이터 생성 파이프라인

```
data/202605_RoadAddress_KR_Full/*.txt  (원본, EUC-KR, pipe-delimited)
         ↓ load_road_address.py
data/generated/road_address_components.json  (시도/시군구/도로명 목록)
         ↓ generate_addresses.py
data/generated/addresses.jsonl  (7가지 구어체·문어체 변형 주소 샘플)

templates (내장 또는 data/templates/{written,stt,negative}/*.txt)
         ↓ generate_synthetic.py
data/generated/synthetic.jsonl  (PII entity span 포함 NER 학습 데이터)
```

### JSONL 출력 포맷 (모든 스크립트 공통)

```json
{
  "id": "synthetic-written-000001",
  "category": "written|stt|negative|address",
  "text": "김민수 고객님, 문의는 010-1234-5678로 연락 주세요.",
  "entities": [
    {"type": "NAME", "start": 0, "end": 3, "text": "김민수", "source": "synthetic"},
    {"type": "PHONE", "start": 12, "end": 25, "text": "010-1234-5678", "source": "synthetic"}
  ]
}
```

### generate_synthetic.py 핵심 구조

- `GENERATORS` dict: placeholder 키(`NAME`, `PHONE`, ...) → 생성 함수 매핑
- `LABEL_MAP`: placeholder → NER label 타입 매핑. `BANK`는 `None`(entity 미생성) — 의도적 설계
- `render_template()`: 템플릿 치환과 동시에 character-level span을 계산하여 `entities` 생성
- `REGION`과 `ADDRESS`는 별도 레이블 — REGION은 방향/지역 언급(`강남 쪽이요`), ADDRESS는 실주소
- STT 카테고리: 구어체 숫자(`PHONE_SPOKEN`, `DOB_SPOKEN`), 발화 추임새 랜덤 삽입

### load_road_address.py / generate_addresses.py

- 원본 파일: EUC-KR 인코딩, `|` 구분자 24컬럼 (`rnaddrkor_*.txt`)
- `load_road_addresses(data_dir, sample_rate=0.01)` — 모듈로 import 가능
- `generate_addresses.py`는 `load_road_address`를 import하며 7가지 주소 변형 생성:
  - 문어체 3종 (전체/시도축약/시도생략) + 구어체 숫자 2종 + STT 방향표현 2종

## Raw Data

`data/202605_RoadAddress_KR_Full/` — 행정안전부 도로명주소 한글 데이터 (2025년 5월 기준)
- `rnaddrkor_*.txt`: 도로명주소 (17개 시도, EUC-KR, ~1GB 총합)
- `jibun_rnaddrkor_*.txt`: 지번주소 (14컬럼, 같은 인코딩)
- 직접 git commit 금지 (용량)

## PII 타입 정의

`NAME` · `PHONE` · `EMAIL` · `ADDRESS` · `REGION` · `RRN` · `CARD` · `ACCOUNT` · `DATE_OF_BIRTH` · `CAR_NUMBER` · `IP` · `ID` · `JOB` · `ORG`

NER 학습 시 BIO tagging 사용 (`B-NAME`, `I-NAME`, ..., `O`).
