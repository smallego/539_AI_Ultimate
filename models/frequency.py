# models/frequency.py

from collections import Counter


def get_numbers(row):
    return [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]


def frequency_model(draws):
    counter = Counter()

    for row in draws:
        counter.update(get_numbers(row))

    return {num: counter.get(num, 0) for num in range(1, 40)}


def frequency_model_window(draws):
    windows = [
        (30, 0.40),
        (60, 0.30),
        (120, 0.20),
        (len(draws), 0.10),
    ]

    scores = {n: 0.0 for n in range(1, 40)}

    for size, weight in windows:
        subset = draws[-size:]
        counter = Counter()

        for row in subset:
            counter.update(get_numbers(row))

        max_count = max(counter.values()) if counter else 1

        for n in range(1, 40):
            scores[n] += (counter.get(n, 0) / max_count) * weight

    return scores