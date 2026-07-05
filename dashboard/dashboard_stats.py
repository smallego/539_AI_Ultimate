from analytics.statistics import basic_statistics


def analytics_tables(last_n=100):
    stats = basic_statistics(last_n=last_n)

    analytics = [
        ["期數", stats["draws"]],
        ["平均和值", stats["avg_sum"]],
        ["平均跨度", stats["avg_span"]],
        ["奇數", stats["odd"]],
        ["偶數", stats["even"]],
        ["小號(1~20)", stats["low"]],
        ["大號(21~39)", stats["high"]],
    ]

    hot = [[n, c] for n, c in stats["hot"]]
    cold = [[n, c] for n, c in stats["cold"]]

    return analytics, hot, cold


def period_comparison(periods=(10, 30, 100)):
    rows = []
    for n in periods:
        stats = basic_statistics(last_n=n)
        hot_top = stats["hot"][0][0] if stats["hot"] else ""
        cold_top = stats["cold"][0][0] if stats["cold"] else ""
        rows.append([
            f"最近{n}期",
            stats["draws"],
            stats["avg_sum"],
            stats["avg_span"],
            hot_top,
            cold_top,
        ])
    return rows
