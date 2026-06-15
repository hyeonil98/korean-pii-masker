"""
NER 모델 학습 스크립트.

사용:
  python scripts/train.py
  python scripts/train.py --config configs/train.yaml
  python scripts/train.py --train data/processed/train.jsonl --valid data/processed/valid.jsonl
"""

from pathlib import Path
import argparse
import json
import sys
from typing import Any

try:
    import yaml
    from labels import LABEL_NAMES, LABEL2ID, ID2LABEL
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    import yaml
    from labels import LABEL_NAMES, LABEL2ID, ID2LABEL

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = _PROJECT_ROOT / "configs" / "train.yaml"


# =========================
# 데이터 로딩 및 전처리
# =========================

def _load_jsonl(path: Path) -> list[dict]:
    samples = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def _build_char_labels(text: str, entities: list[dict]) -> list[str]:
    """각 문자 위치에 BIO 레이블을 할당한다."""
    labels = ["O"] * len(text)
    for ent in entities:
        t = ent["type"]
        s, e = ent["start"], ent["end"]
        if s >= len(text) or e > len(text):
            continue
        labels[s] = f"B-{t}"
        for i in range(s + 1, e):
            labels[i] = f"I-{t}"
    return labels


def _tokenize_and_align(batch: dict, tokenizer: Any, max_length: int) -> dict:
    """배치 단위 토크나이징 + 레이블 정렬."""
    texts = batch["text"]
    all_entities = batch["entities"]

    encodings = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding=False,
        return_offsets_mapping=True,
    )

    all_labels = []
    for text, entities, offset_mapping in zip(
        texts, all_entities, encodings["offset_mapping"]
    ):
        char_labels = _build_char_labels(text, entities)
        token_labels = []
        prev_end = -1

        for start, end in offset_mapping:
            if start == 0 and end == 0:
                # [CLS] / [SEP] 등 special token
                token_labels.append(-100)
                continue

            # 첫 번째 서브워드인지 판별: 직전 토큰의 end와 현재 start가 연속이면 비첫번째 서브워드
            is_first_subword = (start != prev_end) or (prev_end == -1)

            if is_first_subword:
                label_str = char_labels[start] if start < len(char_labels) else "O"
                token_labels.append(LABEL2ID.get(label_str, LABEL2ID["O"]))
            else:
                token_labels.append(-100)

            prev_end = end

        all_labels.append(token_labels)

    encodings.pop("offset_mapping")
    encodings["labels"] = all_labels
    return encodings


# =========================
# 평가 지표 (학습 중)
# =========================

def _compute_metrics(eval_pred: Any) -> dict[str, float]:
    try:
        from seqeval.metrics import f1_score, precision_score, recall_score
    except ImportError:
        return {}

    import numpy as np

    logits, label_ids = eval_pred
    predictions = np.argmax(logits, axis=-1)

    true_seqs, pred_seqs = [], []
    for pred_row, label_row in zip(predictions, label_ids):
        true_seq, pred_seq = [], []
        for p, l in zip(pred_row, label_row):
            if l == -100:
                continue
            true_seq.append(ID2LABEL[l])
            pred_seq.append(ID2LABEL[p])
        true_seqs.append(true_seq)
        pred_seqs.append(pred_seq)

    return {
        "precision": precision_score(true_seqs, pred_seqs, zero_division=0),
        "recall":    recall_score(true_seqs, pred_seqs, zero_division=0),
        "f1":        f1_score(true_seqs, pred_seqs, zero_division=0),
    }


# =========================
# 학습 메인
# =========================

def train(cfg: dict) -> None:
    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForTokenClassification,
            TrainingArguments,
            Trainer,
            DataCollatorForTokenClassification,
        )
        from datasets import Dataset
    except ImportError as e:
        print(f"필수 패키지 없음: {e}\n  pip install transformers datasets torch")
        sys.exit(1)

    model_name: str = cfg["model"]["name"]
    max_length: int = cfg["model"]["max_length"]
    t_cfg: dict = cfg["training"]
    data_cfg: dict = cfg["data"]

    # 경로는 프로젝트 루트 기준
    train_path = _PROJECT_ROOT / data_cfg["train"]
    valid_path = _PROJECT_ROOT / data_cfg["valid"]

    print(f"모델: {model_name}")
    print(f"학습: {train_path}")
    print(f"검증: {valid_path}")

    # 데이터 로딩
    train_samples = _load_jsonl(train_path)
    valid_samples = _load_jsonl(valid_path)
    print(f"학습 {len(train_samples):,}건 / 검증 {len(valid_samples):,}건")

    # HuggingFace Dataset
    train_ds = Dataset.from_list(train_samples)
    valid_ds = Dataset.from_list(valid_samples)

    # 토크나이저
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def _map_fn(batch: dict) -> dict:
        return _tokenize_and_align(batch, tokenizer, max_length)

    train_ds = train_ds.map(_map_fn, batched=True, remove_columns=train_ds.column_names)
    valid_ds = valid_ds.map(_map_fn, batched=True, remove_columns=valid_ds.column_names)

    # 모델
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL_NAMES),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    output_dir = _PROJECT_ROOT / t_cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=t_cfg["num_train_epochs"],
        per_device_train_batch_size=t_cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=t_cfg["per_device_eval_batch_size"],
        learning_rate=t_cfg["learning_rate"],
        weight_decay=t_cfg["weight_decay"],
        warmup_steps=t_cfg.get("warmup_steps", 0),
        lr_scheduler_type=t_cfg["lr_scheduler_type"],
        eval_strategy=t_cfg["eval_strategy"],
        save_strategy=t_cfg["save_strategy"],
        load_best_model_at_end=t_cfg["load_best_model_at_end"],
        metric_for_best_model=t_cfg["metric_for_best_model"],
        greater_is_better=t_cfg["greater_is_better"],
        fp16=t_cfg.get("fp16", False),
        dataloader_num_workers=t_cfg.get("dataloader_num_workers", 0),
        seed=t_cfg.get("seed", 42),
        logging_steps=t_cfg.get("logging_steps", 50),
        report_to=t_cfg.get("report_to", "none"),
    )

    collator = DataCollatorForTokenClassification(tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        data_collator=collator,
        compute_metrics=_compute_metrics,
        processing_class=tokenizer,
    )

    trainer.train()

    best_dir = output_dir / "best"
    trainer.save_model(str(best_dir))
    tokenizer.save_pretrained(str(best_dir))
    print(f"\n최적 모델 저장: {best_dir}")


# =========================
# CLI
# =========================

def _load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="한국어 PII NER 모델 학습")
    parser.add_argument(
        "--config",
        default=str(_DEFAULT_CONFIG),
        help=f"학습 설정 YAML (기본값: {_DEFAULT_CONFIG})",
    )
    parser.add_argument("--train", default=None, help="학습 JSONL 경로 (config 오버라이드)")
    parser.add_argument("--valid", default=None, help="검증 JSONL 경로 (config 오버라이드)")
    parser.add_argument("--model", default=None, help="베이스 모델 이름 (config 오버라이드)")
    parser.add_argument("--epochs", type=int, default=None, help="학습 epoch 수")
    parser.add_argument("--output-dir", default=None, help="체크포인트 저장 경로")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    cfg = _load_config(Path(args.config))

    # CLI 인자로 config 오버라이드
    if args.train:   cfg["data"]["train"] = args.train
    if args.valid:   cfg["data"]["valid"] = args.valid
    if args.model:   cfg["model"]["name"] = args.model
    if args.epochs:  cfg["training"]["num_train_epochs"] = args.epochs
    if args.output_dir: cfg["training"]["output_dir"] = args.output_dir

    train(cfg)


if __name__ == "__main__":
    main()
