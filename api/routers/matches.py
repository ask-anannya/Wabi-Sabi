from fastapi import APIRouter

from services import catalog, profile_store, scan_store, trust_engine
from utils.exception_handler import ExceptionBase

router = APIRouter()


def _latest_metrics(user_id: str) -> list[dict] | None:
    try:
        last = scan_store.get_last_scan(user_id)
    except Exception as e:
        print(f"[matches] get_last_scan failed, falling back to profile concerns: {e}")
        return None
    return last.metrics_json if last is not None else None


def _profile(user_id: str):
    try:
        return profile_store.get_profile(user_id)
    except Exception as e:
        raise ExceptionBase(status_code=503, message="Your profile is unavailable right now.") from e


@router.get("/matches")
async def matches(user_id: str, limit: int = 6):
    profile = _profile(user_id)
    return await trust_engine.honest_matches(profile, _latest_metrics(user_id), limit=max(1, min(limit, 12)))


@router.get("/products/{product_id}/honest")
async def honest_check(product_id: str, user_id: str):
    product = catalog.get(product_id)
    if product is None:
        raise ExceptionBase(status_code=404, message="Product not found.")
    return await trust_engine.honest_check(product, _profile(user_id), _latest_metrics(user_id))
