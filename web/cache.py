import time
from collections import deque
from threading import RLock

TTL_SECONDS = 60


class TTLCache:
    def __init__(self, ttl=TTL_SECONDS):
        self.ttl = ttl
        self._items = {}
        self._hits = 0
        self._misses = 0
        self._lock = RLock()

    def get(self, key):
        now = time.time()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                self._misses += 1
                return None

            expires_at, value = item
            if expires_at < now:
                self._items.pop(key, None)
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key, value):
        with self._lock:
            self._items[key] = (time.time() + self.ttl, value)
        return value

    def get_or_set(self, key, factory):
        value = self.get(key)
        if value is not None:
            return value
        return self.set(key, factory())

    def clear(self):
        with self._lock:
            self._items.clear()

    def stats(self):
        with self._lock:
            total = self._hits + self._misses
            return {
                "ttl": self.ttl,
                "size": len(self._items),
                "hits": self._hits,
                "misses": self._misses,
                "hitRate": round((self._hits / total) * 100, 2) if total else 0,
            }


api_cache = TTLCache()
api_metrics = deque(maxlen=100)


def cached(key, factory):
    return api_cache.get_or_set(key, factory)


def clear_cache():
    api_cache.clear()


def cache_stats():
    return api_cache.stats()


def record_api_metric(path, method, duration_ms, success, request_id):
    api_metrics.append(
        {
            "path": path,
            "method": method,
            "durationMs": round(duration_ms, 2),
            "success": bool(success),
            "requestId": request_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def performance_stats():
    rows = list(api_metrics)
    average = sum(row["durationMs"] for row in rows) / len(rows) if rows else 0
    stats = cache_stats()
    return {
        "averageApiTime": round(average, 2),
        "cacheHit": stats["hits"],
        "cacheMiss": stats["misses"],
        "cacheHitRate": stats["hitRate"],
        "recentApiCount": len(rows),
        "recentApi": rows,
        "memory": memory_usage(),
        "cpu": cpu_usage(),
    }


def memory_usage():
    try:
        import psutil

        process = psutil.Process()
        return {
            "rssMb": round(process.memory_info().rss / 1024 / 1024, 2),
            "available": True,
        }
    except Exception:
        return {"rssMb": None, "available": False}


def cpu_usage():
    try:
        import psutil

        return {
            "percent": psutil.cpu_percent(interval=None),
            "available": True,
        }
    except Exception:
        return {"percent": None, "available": False}
