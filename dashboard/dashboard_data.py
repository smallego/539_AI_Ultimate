# dashboard/dashboard_data.py

from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
BACKTEST_PATH = BASE_DIR / "reports" / "backtest_result.csv"
TUNING_PATH = BASE_DIR / "reports" / "tuning_result.csv"


def read_latest_draw():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT draw_no, draw_date, n1, n2, n3, n4, n5
        FROM draw_history
        ORDER BY draw_date DESC, draw_no DESC
        LIMIT 1
    """, conn)
    conn.close()
    return df


def read_weights_top10():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT number, final_weight
        FROM model_weights
        ORDER BY final_weight DESC
        LIMIT 10
    """, conn)
    conn.close()
    return df


def read_latest_predictions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT set_no, n1, n2, n3, n4, n5
        FROM prediction_history
        ORDER BY id DESC
        LIMIT 5
    """, conn)
    conn.close()
    return df.sort_values("set_no")


def read_backtest():
    if BACKTEST_PATH.exists():
        return pd.read_csv(BACKTEST_PATH)
    return pd.DataFrame()


def read_tuning():
    if TUNING_PATH.exists():
        return pd.read_csv(TUNING_PATH)
    return pd.DataFrame()