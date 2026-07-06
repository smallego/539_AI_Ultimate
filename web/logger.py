import json
import logging
from datetime import datetime

from web.config import LOG_DIR

LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_path():
    return LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"


def get_logger():
    logger = logging.getLogger("539_ai_web")
    logger.setLevel(logging.INFO)

    path = str(log_path())
    if not any(getattr(handler, "baseFilename", None) == path for handler in logger.handlers):
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger


def log_event(action, status="INFO", **details):
    payload = {
        "action": action,
        "status": status,
        "details": details,
    }
    get_logger().info(json.dumps(payload, ensure_ascii=False, default=str))
