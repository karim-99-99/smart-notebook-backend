"""
Launch-safe usage monitoring: scans per day, active users, OCR time, failures.
In-memory; gives real numbers for capacity and reliability.
"""
import time
from collections import deque
from datetime import date, datetime

# Current day
_today: date = date.today()
_scans_today: int = 0
_failures_today: int = 0
_active_user_ids_today: set[int] = set()
# Last N OCR durations in seconds
_ocr_times: deque[float] = deque(maxlen=100)


def _ensure_today() -> None:
    global _today, _scans_today, _failures_today, _active_user_ids_today
    if date.today() != _today:
        _today = date.today()
        _scans_today = 0
        _failures_today = 0
        _active_user_ids_today = set()


def record_ocr_success(user_id: int, duration_sec: float) -> None:
    global _today, _scans_today, _active_user_ids_today, _ocr_times
    _ensure_today()
    _scans_today += 1
    _active_user_ids_today.add(user_id)
    _ocr_times.append(duration_sec)


def record_ocr_failure(user_id: int | None = None) -> None:
    global _today, _failures_today, _active_user_ids_today
    _ensure_today()
    _failures_today += 1
    if user_id is not None:
        _active_user_ids_today.add(user_id)


def get_stats() -> dict:
    global _today, _scans_today, _failures_today, _active_user_ids_today, _ocr_times
    _ensure_today()
    times = list(_ocr_times)
    return {
        "date": _today.isoformat(),
        "scans_today": _scans_today,
        "active_users_today": len(_active_user_ids_today),
        "failures_today": _failures_today,
        "ocr_times": {
            "count": len(times),
            "avg_sec": round(sum(times) / len(times), 2) if times else None,
            "last_10": [round(t, 2) for t in times[-10:]][::-1],
        },
    }
