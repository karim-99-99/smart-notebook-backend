"""
Launch usage stats: scans per day, active users, OCR time, failures.
GET /api/stats — no auth for simplicity; protect with reverse proxy or env later if needed.
"""
from fastapi import APIRouter
from app.utils.usage_stats import get_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=dict)
def read_usage_stats():
    """Return usage metrics: scans_today, active_users_today, failures_today, ocr_times."""
    return get_stats()
