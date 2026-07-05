# core/features.py

from itertools import combinations


def odd_even_count(nums):
    odd = sum(1 for n in nums if n % 2 == 1)
    even = len(nums) - odd
    return odd, even


def low_high_count(nums):
    low = sum(1 for n in nums if n <= 19)
    high = len(nums) - low
    return low, high


def sum_value(nums):
    return sum(nums)


def span_value(nums):
    return max(nums) - min(nums)


def consecutive_count(nums):
    nums = sorted(nums)
    count = 0

    for a, b in zip(nums, nums[1:]):
        if b - a == 1:
            count += 1

    return count


def same_tail_count(nums):
    tails = [n % 10 for n in nums]
    return len(tails) - len(set(tails))


def ac_value(nums):
    diffs = set()

    for a, b in combinations(sorted(nums), 2):
        diffs.add(abs(b - a))

    return len(diffs) - (len(nums) - 1)


def analyze_set(nums):
    nums = sorted(nums)

    odd, even = odd_even_count(nums)
    low, high = low_high_count(nums)

    return {
        "numbers": nums,
        "sum": sum_value(nums),
        "span": span_value(nums),
        "odd": odd,
        "even": even,
        "low": low,
        "high": high,
        "consecutive": consecutive_count(nums),
        "same_tail": same_tail_count(nums),
        "ac": ac_value(nums),
    }


def print_features(nums):
    result = analyze_set(nums)

    print("===================================")
    print("Feature Engine V2.0")
    print("===================================")
    print("號碼：", " ".join(f"{n:02d}" for n in result["numbers"]))
    print(f"和值：{result['sum']}")
    print(f"跨度：{result['span']}")
    print(f"奇偶：{result['odd']}:{result['even']}")
    print(f"大小：{result['low']}:{result['high']}")
    print(f"連號數：{result['consecutive']}")
    print(f"同尾數：{result['same_tail']}")
    print(f"AC值：{result['ac']}")
    print("===================================")


if __name__ == "__main__":
    print_features([2, 10, 15, 31, 37])