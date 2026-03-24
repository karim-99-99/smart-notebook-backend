"""
Simple in-memory rate limiter: max N requests per user per minute.
Launch-safe protection; no queue. Keyed by user id.
"""
import time
from collections import defaultdict
from fastapi import HTTPException

# max 10 OCR requests per user per minute
MAX_REQUESTS_PER_MINUTE = int(__import__("os").getenv("OCR_RATE_LIMIT_PER_MIN", "10"))
WINDOW_SECONDS = 60

# user_id -> list of request timestamps (within window)
_request_times: dict[int, list[float]] = defaultdict(list)


def _clean_old(user_id: int) -> None:
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS
    _request_times[user_id] = [t for t in _request_times[user_id] if t > cutoff]


def check_ocr_rate_limit(user_id: int) -> None:
    """Raises HTTPException 429 if user exceeded limit. Call before processing OCR."""
    _clean_old(user_id)
    timestamps = _request_times[user_id]
    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Too many scan requests. Limit is {MAX_REQUESTS_PER_MINUTE} per minute. Please try again later.",
        )
    timestamps.append(time.monotonic())
