"""
KLUE-NER 데이터셋을 프로젝트 JSONL 포맷으로 변환한다.

레이블 매핑:
  PS (인물)    → NAME
  LC (지역)    → ADDRESS
  OG (기관)    → ORG
  DT / TI / QT → 무시 (O)

사용:
  python scripts/convert_klue_ner.py --output data/generated/klue_ner.jsonl
  python scripts/convert_klue_ner.py --split train --output data/generated/klue_ner_train.jsonl
"""

from pathlib import Path
import argparse
import json
import sys

try:
    from labels import KLUE_NER_MAP
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    from labels import KLUE_NER_MAP

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT = _PROJECT_ROOT / "data" / "generated" / "klue_ner.jsonl"


def _tokens_to_text_and_entities(
    tokens: list[str],
    ner_tags: list[int],
    tag_names: list[str],
) -> tuple[str, list[dict]]:
    """토큰 목록과 BIO 태그에서 텍스트와 entity span 목록을 생성한다."""
    # 토큰 → 텍스트 + 각 토큰의 char offset 계산
    text = ""
    offsets: list[tuple[int, int]] = []
    for token in tokens:
        start = len(text)
        text += token
        offsets.append((start, len(text)))
        text += " "
    text = text.rstrip()

    tags = [tag_names[t] for t in ner_tags]

    entities: list[dict] = []
    i = 0
    while i < len(tags):
        tag = tags[i]
        if not tag.startswith("B-"):
            i += 1
            continue

        klue_type = tag[2:]
        pii_type = KLUE_NER_MAP.get(klue_type)

        # 매핑 없는 타입은 건너뜀
        j = i + 1
        while j < len(tags) and tags[j] == f"I-{klue_type}":
            j += 1

        if pii_type is not None:
            start_char = offsets[i][0]
            end_char = offsets[j - 1][1]
            span_text = text[start_char:end_char]
            entities.append({
                "type": pii_type,
                "start": start_char,
                "end": end_char,
                "text": span_text,
                "source": "klue_ner",
            })

        i = j

    return text, entities


def convert(split: str, output_path: Path) -> int:
    try:
        from datasets import load_dataset
    except ImportError:
        print("datasets 패키지가 필요합니다: pip install datasets")
        sys.exit(1)

    print(f"KLUE-NER 로딩 중 (split={split})...")
    ds = load_dataset("klue", "ner", split=split, trust_remote_code=True)
    tag_names: list[str] = ds.features["ner_tags"].feature.names

    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with output_path.open("w", encoding="utf-8") as f:
        for idx, example in enumerate(ds):
            tokens: list[str] = example["tokens"]
            ner_tags: list[int] = example["ner_tags"]

            text, entities = _tokens_to_text_and_entities(tokens, ner_tags, tag_names)

            sample = {
                "id": f"klue-ner-{split}-{idx:06d}",
                "category": "klue_ner",
                "text": text,
                "entities": entities,
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            count += 1

    return count


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="KLUE-NER 데이터셋을 프로젝트 JSONL 포맷으로 변환합니다."
    )
    parser.add_argument(
        "--split",
        default="train",
        choices=["train", "validation"],
        help="KLUE-NER 분할 (기본값: train)",
    )
    parser.add_argument(
        "--output",
        default=str(_DEFAULT_OUTPUT),
        help=f"출력 JSONL 경로 (기본값: {_DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_path = Path(args.output)
    count = convert(args.split, output_path)
    print(f"변환 완료: {output_path}  ({count:,}건)")


if __name__ == "__main__":
    main()
