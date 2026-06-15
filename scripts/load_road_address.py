"""
data/road_address/*.txt (도로명주소 한글) 데이터 로더.

rnaddrkor_*.txt 컬럼 (pipe-separated, EUC-KR):
  2: 시도명  3: 시군구명  10: 도로명
 12: 건물본번  13: 건물부번  16: 우편번호
"""

from pathlib import Path
from typing import Iterator, NamedTuple
import argparse
import json
import random


ENCODING = "euc-kr"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data" / "202605_RoadAddress_KR_Full"
_DEFAULT_OUTPUT = _PROJECT_ROOT / "data" / "generated" / "road_address_components.json"

COL_SIDO = 2
COL_SIGUNGU = 3
COL_ROAD = 10
COL_BLD_MAIN = 12
COL_BLD_SUB = 13
COL_POSTAL = 16

MIN_FIELDS = 17


class RoadAddress(NamedTuple):
    sido: str
    sigungu: str
    road: str
    bld_main: int
    bld_sub: int
    postal_code: str


def _iter_file(path: Path) -> Iterator[RoadAddress]:
    with path.open(encoding=ENCODING, errors="replace") as f:
        for line in f:
            fields = line.rstrip("\n").split("|")
            if len(fields) < MIN_FIELDS:
                continue
            bld_main_raw = fields[COL_BLD_MAIN]
            if not bld_main_raw.isdigit():
                continue
            bld_sub_raw = fields[COL_BLD_SUB]
            yield RoadAddress(
                sido=fields[COL_SIDO],
                sigungu=fields[COL_SIGUNGU],
                road=fields[COL_ROAD],
                bld_main=int(bld_main_raw),
                bld_sub=int(bld_sub_raw) if bld_sub_raw.isdigit() else 0,
                postal_code=fields[COL_POSTAL],
            )


def load_road_addresses(
    data_dir: str | Path,
    *,
    sample_rate: float = 1.0,
    seed: int = 42,
) -> list[RoadAddress]:
    """
    data_dir 아래 rnaddrkor_*.txt 파일을 모두 로딩한다.

    sample_rate: 0 < x <= 1.0 — 메모리 절약을 위해 무작위 샘플링
    """
    data_dir = Path(data_dir)
    files = sorted(data_dir.glob("rnaddrkor_*.txt"))

    if not files:
        raise FileNotFoundError(f"rnaddrkor_*.txt 파일을 찾을 수 없습니다: {data_dir}")

    rng = random.Random(seed)
    addresses: list[RoadAddress] = []

    for path in files:
        for addr in _iter_file(path):
            if sample_rate < 1.0 and rng.random() > sample_rate:
                continue
            addresses.append(addr)

    return addresses


def extract_components(addresses: list[RoadAddress]) -> dict[str, list[str]]:
    """주소 목록에서 고유한 구성 요소를 추출한다."""
    sidos: set[str] = set()
    sigungus: set[str] = set()
    roads: set[str] = set()

    for addr in addresses:
        if addr.sido:
            sidos.add(addr.sido)
        if addr.sigungu:
            sigungus.add(addr.sigungu)
        if addr.road:
            roads.add(addr.road)

    return {
        "sido": sorted(sidos),
        "sigungu": sorted(sigungus),
        "road": sorted(roads),
    }


def _print_stats(addresses: list[RoadAddress], components: dict[str, list[str]]) -> None:
    print(f"\n[Road Address Stats]")
    print(f"  총 주소 수    : {len(addresses):,}")
    print(f"  고유 시도     : {len(components['sido'])}")
    print(f"  고유 시군구   : {len(components['sigungu'])}")
    print(f"  고유 도로명   : {len(components['road']):,}")
    print(f"\n  시도 목록:")
    for sido in components["sido"]:
        print(f"    - {sido}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="도로명주소 한글 데이터(rnaddrkor_*.txt)를 로딩합니다."
    )
    parser.add_argument(
        "--data-dir",
        default=str(_DEFAULT_DATA_DIR),
        help=f"rnaddrkor_*.txt 파일이 있는 디렉토리 (기본값: {_DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.01,
        help="로딩 비율 0~1 (기본값: 0.01 = 1%%)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="샘플링 랜덤 시드 (기본값: 42)",
    )
    parser.add_argument(
        "--output",
        default=str(_DEFAULT_OUTPUT),
        help=f"구성 요소 JSON 저장 경로 (기본값: {_DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print(f"로딩 중: {args.data_dir}  (sample_rate={args.sample_rate})")
    addresses = load_road_addresses(
        args.data_dir,
        sample_rate=args.sample_rate,
        seed=args.seed,
    )

    components = extract_components(addresses)
    _print_stats(addresses, components)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(components, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {output_path}")


if __name__ == "__main__":
    main()
