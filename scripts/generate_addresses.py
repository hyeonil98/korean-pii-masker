"""
공개 도로명주소 데이터에서 다양한 형태의 주소 합성 샘플을 생성한다.

생성 단계:
  1. load_road_address.py로 공개 데이터에서 행정구역/도로명 추출
  2. 중복 제거
  3. 랜덤 샘플링
  4. 건물번호 랜덤 생성
  5. 상세주소 랜덤 생성
  6. STT 구어체 변형 생성

출력 예시:
  서울특별시 강남구 테헤란로 123
  서울 강남구 테헤란로 123
  강남구 테헤란로 123
  테헤란로 백이십삼
  테헤란로 일이삼
  강남구 테헤란로 쪽이에요
  서울 강남 쪽이요
"""

from pathlib import Path
from typing import NamedTuple
import argparse
import json
import random
import sys

try:
    from load_road_address import RoadAddress, load_road_addresses
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    from load_road_address import RoadAddress, load_road_addresses

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "data" / "202605_RoadAddress_KR_Full"
_DEFAULT_OUTPUT = _PROJECT_ROOT / "data" / "generated" / "addresses.jsonl"


# =========================
# 한국어 숫자 변환
# =========================

_DIGIT_KO = {"0": "공", "1": "일", "2": "이", "3": "삼", "4": "사",
              "5": "오", "6": "육", "7": "칠", "8": "팔", "9": "구"}

_UNITS = ["", "십", "백", "천"]
_MYRIADS = ["", "만", "억"]
_ONES = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]


def _to_sino_korean(n: int) -> str:
    """아라비아 숫자를 한자 계열 수 읽기로 변환한다 (백이십삼)."""
    if n == 0:
        return "영"

    result = ""
    myriad_idx = 0

    while n > 0:
        chunk = n % 10000
        if chunk:
            chunk_str = ""
            for unit_idx, digit in enumerate(reversed(str(chunk))):
                d = int(digit)
                if d == 0:
                    continue
                one = "" if (d == 1 and unit_idx > 0) else _ONES[d]
                chunk_str = one + _UNITS[unit_idx] + chunk_str
            result = chunk_str + _MYRIADS[myriad_idx] + result
        n //= 10000
        myriad_idx += 1

    return result


def _to_digit_korean(n: int) -> str:
    """아라비아 숫자를 숫자 낱개 읽기로 변환한다 (일이삼)."""
    return "".join(_DIGIT_KO[ch] for ch in str(n))


# =========================
# 주소 풀
# =========================

class AddressPool(NamedTuple):
    sidos: list[str]
    sigungus: list[str]
    roads: list[str]
    sido_to_short: dict[str, str]


_SIDO_SHORT: dict[str, str] = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}


def build_pool(addresses: list[RoadAddress]) -> AddressPool:
    sidos = sorted({a.sido for a in addresses if a.sido})
    sigungus = sorted({a.sigungu for a in addresses if a.sigungu})
    roads = sorted({a.road for a in addresses if a.road})
    sido_to_short = {s: _SIDO_SHORT.get(s, s) for s in sidos}
    return AddressPool(sidos=sidos, sigungus=sigungus, roads=roads, sido_to_short=sido_to_short)


# =========================
# 주소 생성기
# =========================

def _rand_bld_num(rng: random.Random) -> int:
    return rng.randint(1, 999)


def _rand_detail(rng: random.Random) -> str:
    style = rng.random()
    if style < 0.5:
        return ""
    elif style < 0.7:
        return f" {rng.randint(1, 30)}층"
    elif style < 0.85:
        return f" {rng.randint(101, 2403)}호"
    else:
        return f" {rng.randint(1, 30)}동 {rng.randint(101, 2403)}호"


def gen_full_formal(pool: AddressPool, rng: random.Random) -> str:
    """서울특별시 강남구 테헤란로 123"""
    sido = rng.choice(pool.sidos)
    sigungu = rng.choice(pool.sigungus)
    road = rng.choice(pool.roads)
    num = _rand_bld_num(rng)
    detail = _rand_detail(rng)
    return f"{sido} {sigungu} {road} {num}{detail}"


def gen_short_sido(pool: AddressPool, rng: random.Random) -> str:
    """서울 강남구 테헤란로 123"""
    sido = rng.choice(pool.sidos)
    sigungu = rng.choice(pool.sigungus)
    road = rng.choice(pool.roads)
    num = _rand_bld_num(rng)
    detail = _rand_detail(rng)
    short = pool.sido_to_short[sido]
    return f"{short} {sigungu} {road} {num}{detail}"


def gen_no_sido(pool: AddressPool, rng: random.Random) -> str:
    """강남구 테헤란로 123"""
    sigungu = rng.choice(pool.sigungus)
    road = rng.choice(pool.roads)
    num = _rand_bld_num(rng)
    detail = _rand_detail(rng)
    return f"{sigungu} {road} {num}{detail}"


def gen_spoken_sino(pool: AddressPool, rng: random.Random) -> str:
    """테헤란로 백이십삼"""
    road = rng.choice(pool.roads)
    num = _rand_bld_num(rng)
    return f"{road} {_to_sino_korean(num)}"


def gen_spoken_digit(pool: AddressPool, rng: random.Random) -> str:
    """테헤란로 일이삼"""
    road = rng.choice(pool.roads)
    num = _rand_bld_num(rng)
    return f"{road} {_to_digit_korean(num)}"


def gen_stt_direction(pool: AddressPool, rng: random.Random) -> str:
    """강남구 테헤란로 쪽이에요"""
    sigungu = rng.choice(pool.sigungus)
    road = rng.choice(pool.roads)
    suffix = rng.choice(["쪽이에요", "방향이에요", "근처예요", "근방이에요"])
    return f"{sigungu} {road} {suffix}"


def gen_stt_region(pool: AddressPool, rng: random.Random) -> str:
    """서울 강남 쪽이요"""
    sido = rng.choice(pool.sidos)
    sigungu = rng.choice(pool.sigungus)
    suffix = rng.choice(["쪽이요", "쪽이에요", "근처요", "방향이요", "살아요", "거주해요"])
    short = pool.sido_to_short[sido]
    sigungu_short = sigungu.replace("구", "").replace("시", "").replace("군", "")
    return f"{short} {sigungu_short} {suffix}"


_GENERATORS = [
    ("formal", gen_full_formal, "ADDRESS"),
    ("short_sido", gen_short_sido, "ADDRESS"),
    ("no_sido", gen_no_sido, "ADDRESS"),
    ("spoken_sino", gen_spoken_sino, "ADDRESS"),
    ("spoken_digit", gen_spoken_digit, "ADDRESS"),
    ("stt_direction", gen_stt_direction, "ADDRESS"),
    ("stt_region", gen_stt_region, "REGION"),
]


# =========================
# 샘플 생성
# =========================

def generate_samples(
    pool: AddressPool,
    num_samples: int,
    rng: random.Random,
) -> list[dict]:
    samples = []

    for i in range(num_samples):
        _, gen_fn, label = rng.choice(_GENERATORS)
        text = gen_fn(pool, rng)

        sample = {
            "id": f"addr-{i:06d}",
            "category": "address",
            "text": text,
            "entities": [
                {
                    "type": label,
                    "start": 0,
                    "end": len(text),
                    "text": text,
                    "source": "real_data",
                }
            ],
        }
        samples.append(sample)

    return samples


# =========================
# CLI
# =========================

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="공개 도로명주소 데이터에서 합성 주소 샘플을 생성합니다."
    )
    parser.add_argument(
        "--data-dir",
        default=str(_DEFAULT_DATA_DIR),
        help=f"rnaddrkor_*.txt 파일 디렉토리 (기본값: {_DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.01,
        help="데이터 로딩 비율 (기본값: 0.01 = 1%%)",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=1000,
        help="생성할 샘플 수 (기본값: 1000)",
    )
    parser.add_argument(
        "--output",
        default=str(_DEFAULT_OUTPUT),
        help=f"출력 JSONL 경로 (기본값: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed)

    print(f"주소 데이터 로딩 중: {args.data_dir}  (sample_rate={args.sample_rate})")
    addresses = load_road_addresses(
        args.data_dir,
        sample_rate=args.sample_rate,
        seed=args.seed,
    )
    print(f"로딩 완료: {len(addresses):,}건")

    pool = build_pool(addresses)
    print(f"풀 구성 - 시도 {len(pool.sidos)}, 시군구 {len(pool.sigungus)}, 도로명 {len(pool.roads):,}")

    samples = generate_samples(pool, args.num_samples, rng)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"\n저장 완료: {output_path}  ({len(samples):,}건)")

    print("\n[샘플 미리보기]")
    for sample in samples[:7]:
        print(f"  {sample['text']}")


if __name__ == "__main__":
    main()
