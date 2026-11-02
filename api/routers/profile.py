import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from domain.actives import FAMILY_LABELS, LADDERS, SENSITIZERS
from models.profile import UserProfile
from services import catalog, profile_store, tolerance
from utils.exception_handler import ExceptionBase

router = APIRouter()

SEVERITIES = {"fine", "tingling", "redness", "peeling"}


class ProfileUpdate(BaseModel):
    user_id: str
    skin_type: str | None = None
    concerns: list[str] = Field(default_factory=list)
    sensitizers: list[str] = Field(default_factory=list)
    style_prefs: list[str] = Field(default_factory=list)


class QuizSubmission(ProfileUpdate):
    burned_product_ids: list[str] = Field(default_factory=list)
    worked_product_ids: list[str] = Field(default_factory=list)


class UsageStart(BaseModel):
    user_id: str
    product_id: str


class Checkin(BaseModel):
    user_id: str
    product_id: str
    severity: str


class ReactionResolution(BaseModel):
    user_id: str
    confirmed: bool


def _store_unavailable(e: Exception) -> ExceptionBase:
    print(f"[profile] store error: {e}")
    return ExceptionBase(status_code=503, message="Your profile is unavailable right now.")


def _product_or_404(product_id: str):
    product = catalog.get(product_id)
    if product is None:
        raise ExceptionBase(status_code=404, message="Product not found.")
    return product


def _ladders(profile: UserProfile) -> list[dict]:
    """Per-family view of where the user stands, for the tolerance ladder UI."""
    out = []
    for family, rungs in LADDERS.items():
        level = profile.tolerance.get(family)
        out.append({
            "family": family,
            "label": FAMILY_LABELS[family],
            "rungs": [label for label, _ in rungs],
            "proven": level.proven if level else -1,
            "cap": level.cap if level else None,
            "allowed": tolerance.allowed_rung(profile, family),
        })
    return out


def _profile_view(profile: UserProfile) -> dict:
    return {"profile": profile, "ladders": _ladders(profile)}


@router.get("/profile")
async def get_profile(user_id: str):
    try:
        return _profile_view(profile_store.get_profile(user_id))
    except Exception as e:
        raise _store_unavailable(e) from e


@router.put("/profile")
async def put_profile(body: ProfileUpdate):
    try:
        current = profile_store.get_profile(body.user_id)
        updated = current.model_copy(update=body.model_dump(exclude={"user_id"}) | {
            "skin_type_source": "you" if body.skin_type else current.skin_type_source, "onboarded": True})
        return _profile_view(profile_store.save_profile(updated))
    except Exception as e:
        raise _store_unavailable(e) from e


@router.post("/profile/quiz")
async def submit_quiz(body: QuizSubmission):
    burned = [_product_or_404(pid) for pid in body.burned_product_ids]
    worked = [_product_or_404(pid) for pid in body.worked_product_ids]
    try:
        current = profile_store.get_profile(body.user_id)
        base = current.model_copy(update=body.model_dump(
            exclude={"user_id", "burned_product_ids", "worked_product_ids"}) | {
            "skin_type_source": "you" if body.skin_type else current.skin_type_source, "onboarded": True})
        updated = tolerance.apply_quiz(base, burned, worked)
        for p in burned:
            profile_store.log_reaction(body.user_id, p.id, "redness", source="quiz")
        return _profile_view(profile_store.save_profile(updated))
    except Exception as e:
        raise _store_unavailable(e) from e


@router.get("/catalog")
async def get_catalog():
    return {
        "products": [catalog.summary(p) for p in catalog.all_products().values()],
        "sensitizers": [{"id": k, "label": v} for k, v in SENSITIZERS.items()],
        "styles": catalog.STYLES,
    }


@router.get("/usage")
async def get_usage(user_id: str):
    try:
        records = profile_store.active_usage(user_id)
    except Exception as e:
        raise _store_unavailable(e) from e
    out = []
    for r in records:
        product = catalog.get(r.product_id)
        if product is None:
            continue
        out.append({"product": catalog.summary(product), "started_at": r.started_at.isoformat(),
                    "days": (datetime.datetime.utcnow() - r.started_at).days})
    return {"result": out}


@router.post("/usage")
async def start_usage(body: UsageStart):
    _product_or_404(body.product_id)
    try:
        record = profile_store.start_usage(body.user_id, body.product_id)
    except Exception as e:
        raise _store_unavailable(e) from e
    return {"result": {"product_id": record.product_id, "started_at": record.started_at.isoformat()}}


@router.delete("/usage/{product_id}")
async def stop_usage(product_id: str, user_id: str):
    try:
        stopped = profile_store.stop_usage(user_id, product_id)
    except Exception as e:
        raise _store_unavailable(e) from e
    return {"result": "stopped" if stopped else "not_in_use"}


@router.post("/checkin")
async def checkin(body: Checkin):
    if body.severity not in SEVERITIES:
        raise ExceptionBase(status_code=400, message=f"severity must be one of {sorted(SEVERITIES)}")
    product = _product_or_404(body.product_id)
    try:
        profile = profile_store.get_profile(body.user_id)
        usage = next((u for u in profile_store.active_usage(body.user_id) if u.product_id == product.id), None)
        started_at = usage.started_at if usage else None
        had_bad = any(
            r.severity in tolerance.BAD_REACTIONS and r.confirmed and (started_at is None or r.created_at >= started_at)
            for r in profile_store.reactions(body.user_id, product.id)
        )
        updated, message = tolerance.apply_checkin(profile, product, body.severity, started_at, had_bad)
        profile_store.log_reaction(body.user_id, product.id, body.severity, source="checkin")
        if body.severity in tolerance.BAD_REACTIONS:
            profile_store.stop_usage(body.user_id, product.id)
        profile_store.save_profile(updated)
    except Exception as e:
        raise _store_unavailable(e) from e
    return {"message": message, **_profile_view(updated)}


@router.get("/reactions/pending")
async def pending_reactions(user_id: str):
    try:
        records = profile_store.pending_scan_reactions(user_id)
    except Exception as e:
        raise _store_unavailable(e) from e
    alerts = []
    for r in records:
        product = catalog.get(r.product_id)
        if product is not None:
            alerts.append(tolerance.reaction_alert(r.id, product, r.severity))
    return {"result": alerts}


@router.post("/reactions/{reaction_id}/resolve")
async def resolve_reaction(reaction_id: int, body: ReactionResolution):
    """User confirms or dismisses a scan-detected reaction. Confirming applies
    it to their tolerance exactly like a manual redness check-in."""
    try:
        record = profile_store.resolve_scan_reaction(body.user_id, reaction_id, body.confirmed)
        if record is None:
            raise ExceptionBase(status_code=404, message="Reaction not found.")
        profile = profile_store.get_profile(body.user_id)
        message = "Dismissed. We won't count it against that product."
        product = catalog.get(record.product_id)
        if body.confirmed and product is not None:
            profile, message = tolerance.apply_checkin(profile, product, record.severity, None, True)
            profile_store.stop_usage(body.user_id, product.id)
            profile_store.save_profile(profile)
    except ExceptionBase:
        raise
    except Exception as e:
        raise _store_unavailable(e) from e
    return {"message": message, **_profile_view(profile)}
