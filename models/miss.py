# models/miss.py

def get_numbers(row):
    return [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]


def miss_model(draws):
    result = {}

    for num in range(1, 40):
        miss = 0

        for row in reversed(draws):
            if num in get_numbers(row):
                break
            miss += 1

        result[num] = miss

    return result