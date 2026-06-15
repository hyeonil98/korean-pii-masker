"""
여러 JSONL 소스를 지정 비율로 혼합하고 train / valid / test 로 분리한다.

사용:
  python scripts/mix_dataset.py \\
    --source data/generated/synthetic_written.jsonl:0.40 \\
    --source data/generated/synthetic_stt.jsonl:0.40 \\
    --source data/generated/klue_ner.jsonl:0.10 \\
    --source data/generated/negative.jsonl:0.10 \\
    --total 10000 \\
    --output-dir data/processed/

각 --source 값은 "파일경로:비율" 형식. 비율 합계는 1.0이어야 한다.
--total 미지정 시 소스 파일 총 건수에 비율을 적용한다.
"""

from pathlib import Path
import argparse
import json
import math
import random
import sys


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "data" / "processed"


def _load_jsonl(path: Path) -> list[dict]:
    samples = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def _save_jsonl(samples: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def _deduplicate(samples: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for s in samples:
        key = s["text"]
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def mix(
    sources: list[tuple[Path, float]],
    total: int | None,
    split_ratio: tuple[float, float, float],
    seed: int,
    output_dir: Path,
) -> None:
    rng = random.Random(seed)

    # 각 소스 로딩
    loaded: list[tuple[list[dict], float]] = []
    for path, ratio in sources:
        samples = _load_jsonl(path)
        rng.shuffle(samples)
        loaded.append((samples, ratio))
        print(f"  로딩: {path.name}  {len(samples):,}건  (비율 {ratio:.0%})")

    # 전체 목표 수 계산
    if total is None:
        total = sum(len(s) for s, _ in loaded)
        print(f"총 목표: {total:,}건 (소스 합계)")
    else:
        print(f"총 목표: {total:,}건")

    # 각 소스에서 샘플링
    mixed: list[dict] = []
    for samples, ratio in loaded:
        n = math.ceil(total * ratio)
        if n > len(samples):
            # 부족하면 반복 샘플링
            picked = (samples * math.ceil(n / len(samples)))[:n]
        else:
            picked = samples[:n]
        mixed.extend(picked)

    # 중복 제거 + 셔플
    mixed = _deduplicate(mixed)
    rng.shuffle(mixed)

    print(f"혼합 후 (중복 제거): {len(mixed):,}건")

    # Train / Valid / Test 분리
    tr, vl, te = split_ratio
    n_train = math.floor(len(mixed) * tr)
    n_valid = math.floor(len(mixed) * vl)

    train_data = mixed[:n_train]
    valid_data = mixed[n_train:n_train + n_valid]
    test_data  = mixed[n_train + n_valid:]

    # ID 재부여
    for i, s in enumerate(train_data): s["id"] = f"train-{i:06d}"
    for i, s in enumerate(valid_data): s["id"] = f"valid-{i:06d}"
    for i, s in enumerate(test_data):  s["id"] = f"test-{i:06d}"

    # 저장
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_jsonl(train_data, output_dir / "train.jsonl")
    _save_jsonl(valid_data, output_dir / "valid.jsonl")
    _save_jsonl(test_data,  output_dir / "test.jsonl")

    print(f"\n저장 완료: {output_dir}")
    print(f"  train : {len(train_data):,}건")
    print(f"  valid : {len(valid_data):,}건")
    print(f"  test  : {len(test_data):,}건")

    # 레이블 분포 출력
    _print_label_stats("train", train_data)


def _print_label_stats(split: str, samples: list[dict]) -> None:
    counts: dict[str, int] = {}
    for s in samples:
        for ent in s.get("entities", []):
            t = ent["type"]
            counts[t] = counts.get(t, 0) + 1

    print(f"\n[{split} entity 분포]")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<20} {v:,}")


def _parse_source(value: str) -> tuple[Path, float]:
    if ":" not in value:
        raise argparse.ArgumentTypeError(f"'path:ratio' 형식이어야 합니다: {value}")
    path_str, ratio_str = value.rsplit(":", 1)
    return Path(path_str), float(ratio_str)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="여러 JSONL 소스를 혼합하고 train/valid/test 로 분리합니다."
    )
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        metavar="PATH:RATIO",
        help="소스 파일과 비율 (예: data/generated/synthetic.jsonl:0.4). 여러 번 지정 가능.",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=None,
        help="목표 샘플 수 (미지정 시 소스 합계 사용)",
    )
    parser.add_argument(
        "--split",
        default="0.8:0.1:0.1",
        help="train:valid:test 비율 (기본값: 0.8:0.1:0.1)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(_DEFAULT_OUTPUT_DIR),
        help=f"출력 디렉토리 (기본값: {_DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    sources = [_parse_source(s) for s in args.source]
    total_ratio = sum(r for _, r in sources)
    if abs(total_ratio - 1.0) > 0.01:
        print(f"경고: 비율 합계 = {total_ratio:.3f} (1.0 권장)")

    tr, vl, te = map(float, args.split.split(":"))

    print(f"\n[데이터 혼합 시작]")
    mix(
        sources=sources,
        total=args.total,
        split_ratio=(tr, vl, te),
        seed=args.seed,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
