from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_FILE = MODEL_DIR / "weights.json"

DEFAULT = {
    "SCORER_WEIGHT": 0.40,
    "COOCCURRENCE_WEIGHT": 0.20,
    "BALANCE_WEIGHT": 0.15,
    "AI_WEIGHT": 0.25,
}


def load_weights():
    if not MODEL_FILE.exists():
        save_weights(DEFAULT)
        return DEFAULT.copy()

    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights(w):
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, indent=4)


def learn(roi):

    w = load_weights()

    if roi < -70:
        w["AI_WEIGHT"] += 0.02
        w["SCORER_WEIGHT"] -= 0.01
        w["COOCCURRENCE_WEIGHT"] -= 0.01

    elif roi > -40:
        w["AI_WEIGHT"] -= 0.01
        w["SCORER_WEIGHT"] += 0.01

    total = sum(w.values())

    for k in w:
        w[k] /= total

    save_weights(w)

    return w