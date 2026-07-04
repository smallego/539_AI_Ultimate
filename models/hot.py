# models/hot.py

from collections import Counter


def get_numbers(row):
    return [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]


def hot_model(draws, recent_n=20):
    recent = draws[-recent_n:]
    counter = Counter()

    for row in recent:
        counter.update(get_numbers(row))

    return {num: counter.get(num, 0) for num in range(1, 40)}