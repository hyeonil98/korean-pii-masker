"""
학습된 NER 모델을 평가한다.

지표:
  - Entity-level Precision / Recall / F1 (seqeval, 토큰 단위)
  - Character-level Recall  : 실제 PII 문자 중 탐지된 비율
  - Leakage Rate            : 탐지되지 않은 PII 문자 비율 (1 - char recall)

사용:
  python scripts/evaluate.py --model models/checkpoints/v1/best --test data/processed/test.jsonl
"""

from pathlib import Path
import argparse
import json
import sys
from typing import Any

try:
    from labels import LABEL_NAMES, LABEL2ID, ID2LABEL
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    from labels import LABEL_NAMES, LABEL2ID, ID2LABEL

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


# =========================
# 데이터 유틸
# =========================

def _load_jsonl(path: Path) -> list[dict]:
    samples = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def _entities_to_char_mask(text: str, entities: list[dict]) -> list[bool]:
    mask = [False] * len(text)
    for ent in entities:
        s, e = ent["start"], ent["end"]
        for i in range(s, min(e, len(text))):
            mask[i] = True
    return mask


def _entities_to_char_labels(text: str, entities: list[dict]) -> list[str]:
    """entity span 목록 → 문자 단위 BIO 레이블."""
    labels = ["O"] * len(text)
    for ent in entities:
        t = ent["type"]
        s, e = ent["start"], min(ent["end"], len(text))
        if s < len(labels):
            labels[s] = f"B-{t}"
        for i in range(s + 1, e):
            if i < len(labels):
                labels[i] = f"I-{t}"
    return labels


def _char_labels_to_token_bio(char_labels: list[str], offsets: list[tuple]) -> list[str]:
    """문자 단위 BIO → 토큰 단위 BIO (첫 번째 서브워드만 유지, train.py와 동일 로직)."""
    token_labels = []
    prev_end = -1
    for start, end in offsets:
        if start == 0 and end == 0:
            continue  # special token 제외
        is_first_subword = (start != prev_end) or (prev_end == -1)
        if is_first_subword:
            label = char_labels[start] if start < len(char_labels) else "O"
            token_labels.append(label)
        prev_end = end
    return token_labels


# =========================
# 추론
# =========================

def _predict_batch(
    texts: list[str],
    tokenizer: Any,
    model: Any,
    max_length: int,
    device: Any,
) -> tuple[list[list[dict]], list[list[str]], list[list[tuple]]]:
    """
    텍스트 배치에 대해 예측을 수행한다.

    Returns:
        all_entities  : 샘플별 예측 entity span 목록 (char-level 지표용)
        all_pred_bios : 샘플별 토큰 단위 BIO 시퀀스 (seqeval용)
        all_offsets   : 샘플별 offset_mapping
    """
    import torch

    encodings = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding=True,
        return_tensors="pt",
        return_offsets_mapping=True,
    )
    offset_mappings = encodings.pop("offset_mapping").tolist()
    encodings = {k: v.to(device) for k, v in encodings.items()}

    with torch.no_grad():
        outputs = model(**encodings)

    pred_ids = outputs.logits.argmax(dim=-1).cpu().tolist()

    all_entities: list[list[dict]] = []
    all_pred_bios: list[list[str]] = []

    for text, preds, offsets in zip(texts, pred_ids, offset_mappings):
        entities: list[dict] = []
        pred_bio_seq: list[str] = []
        cur_type: str | None = None
        cur_start: int = 0
        prev_end: int = -1

        for pred_id, (start, end) in zip(preds, offsets):
            if start == 0 and end == 0:
                # special token — 열린 entity 닫기
                if cur_type is not None:
                    entities.append({"type": cur_type, "start": cur_start, "end": prev_end})
                    cur_type = None
                continue

            is_first_subword = (start != prev_end) or (prev_end == -1)

            if is_first_subword:
                label = ID2LABEL[pred_id]
                pred_bio_seq.append(label)

                if label.startswith("B-"):
                    if cur_type is not None:
                        entities.append({"type": cur_type, "start": cur_start, "end": start})
                    cur_type = label[2:]
                    cur_start = start
                elif label.startswith("I-"):
                    ptype = label[2:]
                    if cur_type != ptype:
                        if cur_type is not None:
                            entities.append({"type": cur_type, "start": cur_start, "end": start})
                        cur_type = ptype
                        cur_start = start
                else:
                    if cur_type is not None:
                        entities.append({"type": cur_type, "start": cur_start, "end": start})
                        cur_type = None

            prev_end = end

        if cur_type is not None:
            entities.append({"type": cur_type, "start": cur_start, "end": prev_end})

        all_entities.append(entities)
        all_pred_bios.append(pred_bio_seq)

    return all_entities, all_pred_bios, offset_mappings


# =========================
# 지표 계산
# =========================

def _entity_level_metrics(
    true_bio_seqs: list[list[str]],
    pred_bio_seqs: list[list[str]],
) -> dict:
    """토큰 단위 BIO 시퀀스로 seqeval entity-level F1 계산."""
    try:
        from seqeval.metrics import classification_report
    except ImportError:
        print("seqeval 없음: pip install seqeval")
        return {}

    report = classification_report(true_bio_seqs, pred_bio_seqs, output_dict=True, zero_division=0)
    macro = report.get("macro avg", {})
    return {
        "precision": macro.get("precision", 0.0),
        "recall":    macro.get("recall", 0.0),
        "f1":        macro.get("f1-score", 0.0),
        "_report":   report,
    }


def _char_level_metrics(
    true_all: list[list[dict]],
    pred_all: list[list[dict]],
    text_all: list[str],
) -> dict:
    """문자 단위 recall과 leakage rate 계산."""
    total_pii_chars = 0
    detected_chars = 0

    for text, true_ents, pred_ents in zip(text_all, true_all, pred_all):
        true_mask = _entities_to_char_mask(text, true_ents)
        pred_mask = _entities_to_char_mask(text, pred_ents)

        for t, p in zip(true_mask, pred_mask):
            if t:
                total_pii_chars += 1
                if p:
                    detected_chars += 1

    recall = detected_chars / total_pii_chars if total_pii_chars > 0 else 1.0
    return {
        "char_recall":     recall,
        "leakage_rate":    1.0 - recall,
        "total_pii_chars": total_pii_chars,
        "detected_chars":  detected_chars,
    }


# =========================
# 메인 평가 루프
# =========================

def evaluate(model_dir: Path, test_path: Path, batch_size: int, max_length: int) -> None:
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForTokenClassification
    except ImportError as e:
        print(f"필수 패키지 없음: {e}")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"디바이스: {device}")
    print(f"모델: {model_dir}")
    print(f"테스트: {test_path}")

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForTokenClassification.from_pretrained(str(model_dir))
    model.to(device)
    model.eval()

    samples = _load_jsonl(test_path)
    print(f"테스트 샘플: {len(samples):,}건\n")

    texts = [s["text"] for s in samples]
    true_all = [s.get("entities", []) for s in samples]

    pred_all: list[list[dict]] = []
    pred_bio_seqs: list[list[str]] = []
    true_bio_seqs: list[list[str]] = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_true = true_all[i:i + batch_size]

        batch_pred_ents, batch_pred_bios, batch_offsets = _predict_batch(
            batch_texts, tokenizer, model, max_length, device
        )

        # 정답 entity span → 토큰 단위 BIO (train.py와 동일 로직)
        for text, entities, offsets in zip(batch_texts, batch_true, batch_offsets):
            char_labels = _entities_to_char_labels(text, entities)
            token_bio = _char_labels_to_token_bio(char_labels, offsets)
            true_bio_seqs.append(token_bio)

        pred_all.extend(batch_pred_ents)
        pred_bio_seqs.extend(batch_pred_bios)

        if (i // batch_size) % 10 == 0:
            print(f"  추론 중... {i + len(batch_texts)}/{len(texts)}")

    # 지표 계산
    entity_metrics = _entity_level_metrics(true_bio_seqs, pred_bio_seqs)
    char_metrics = _char_level_metrics(true_all, pred_all, texts)

    # 결과 출력
    print("\n[Entity-level Metrics]")
    print(f"  Precision : {entity_metrics.get('precision', 0):.4f}")
    print(f"  Recall    : {entity_metrics.get('recall', 0):.4f}")
    print(f"  F1        : {entity_metrics.get('f1', 0):.4f}")

    print("\n[Character-level Metrics]")
    print(f"  PII 문자 수      : {char_metrics['total_pii_chars']:,}")
    print(f"  탐지된 PII 문자  : {char_metrics['detected_chars']:,}")
    print(f"  Char Recall      : {char_metrics['char_recall']:.4f}")
    print(f"  Leakage Rate     : {char_metrics['leakage_rate']:.4f}  ← 낮을수록 좋음")

    if "_report" in entity_metrics:
        print("\n[타입별 F1]")
        report = entity_metrics["_report"]
        for label, scores in sorted(report.items()):
            if label in ("micro avg", "macro avg", "weighted avg"):
                continue
            if isinstance(scores, dict):
                f1 = scores.get("f1-score", 0)
                support = scores.get("support", 0)
                if support > 0:
                    print(f"  {label:<20} f1={f1:.3f}  (support={support})")

    # 결과 저장
    output = _PROJECT_ROOT / "data" / "generated" / "eval_result.json"
    result = {**entity_metrics, **char_metrics}
    result.pop("_report", None)
    with output.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NER 모델 평가")
    parser.add_argument(
        "--model",
        default=str(_PROJECT_ROOT / "models" / "checkpoints" / "v1" / "best"),
        help="모델 디렉토리",
    )
    parser.add_argument(
        "--test",
        default=str(_PROJECT_ROOT / "data" / "processed" / "test.jsonl"),
        help="테스트 JSONL 경로",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    evaluate(
        model_dir=Path(args.model),
        test_path=Path(args.test),
        batch_size=args.batch_size,
        max_length=args.max_length,
    )


if __name__ == "__main__":
    main()
