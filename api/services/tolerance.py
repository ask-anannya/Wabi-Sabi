"""
Personal tolerance model. Pure functions over UserProfile — no I/O — so the
safety rules are easy to test in isolation.

The rules:
  - You may go at most ONE rung above the strongest rung you've proven.
  - A rung that caused redness/peeling becomes a hard cap: nothing at or
    above it is ever recommended again (until the user resets it).
  - Four weeks of "fine" check-ins on a product proves its rung.
  - A known sensitizer in a product is a hard fail, no matter how good it is.
"""

import datetime

from domain.actives import FAMILY_LABELS, SENSITIZERS, STARTER_RUNG, rung_label
from models.profile import Product, ReactionAlert, ToleranceLevel, UserProfile
from services import catalog

PROVE_AFTER_DAYS = 28
SCAN_REACTION_WINDOW_DAYS = 28
BAD_REACTIONS = {"redness", "peeling"}


def _level(profile: UserProfile, family: str) -> ToleranceLevel:
    return profile.tolerance.get(family) or ToleranceLevel()


def allowed_rung(profile: UserProfile, family: str, no_escalation: bool = False) -> int:
    """Highest rung of `family` this user should be offered. -1 = none.
    no_escalation (from the scan's avoid list) holds the user at what they've
    already proven — no first steps either."""
    level = _level(profile, family)
    if no_escalation:
        allowed = level.proven
    elif level.proven < 0:
        allowed = STARTER_RUNG.get(family, 0)
    else:
        allowed = level.proven + 1
    if level.cap is not None:
        allowed = min(allowed, level.cap - 1)
    return allowed


def fits(
    product: Product,
    profile: UserProfile,
    extra_sensitizers: set[str] | None = None,
    no_escalation_families: set[str] | None = None,
) -> tuple[bool, str, int]:
    """Returns (ok, plain-language reason, margin). Margin is how many rungs
    of headroom remain (2 for products with no gated actives)."""
    avoid = set(profile.sensitizers) | (extra_sensitizers or set())
    hit = [s for s in product.sensitizers if s in avoid]
    if hit:
        names = ", ".join(SENSITIZERS.get(s, s).lower() for s in hit)
        if set(hit) & set(profile.sensitizers):
            return False, f"Contains {names}, which you've told us your skin reacts to.", -1
        return False, f"Contains {names}. Your current redness reading says to skip it for now.", -1

    margin = 2
    notes = []
    for family, rung in catalog.rungs(product).items():
        no_esc = family in (no_escalation_families or set())
        allowed = allowed_rung(profile, family, no_escalation=no_esc)
        level = _level(profile, family)
        label = rung_label(family, rung)
        fam = FAMILY_LABELS.get(family, family)
        if rung > allowed:
            if level.cap is not None and rung == level.cap:
                why = f"You've reacted to this strength before (\"{label}\"), so it's off your list."
            elif level.cap is not None and rung > level.cap:
                why = (f"This is \"{label}\", stronger than \"{rung_label(family, level.cap)}\", "
                       "which already irritated your skin.")
            elif no_esc:
                why = f"This is \"{label}\". Your scan says not to step up your {fam} right now."
            elif level.proven < 0:
                why = f"This is \"{label}\". You haven't used a {fam} yet, so start at \"{rung_label(family, STARTER_RUNG.get(family, 0))}\"."
            else:
                why = (f"This is \"{label}\", more than one step above what you've proven you "
                       f"tolerate (\"{rung_label(family, level.proven)}\").")
            return False, why, allowed - rung
        margin = min(margin, allowed - rung)
        if level.proven >= rung:
            notes.append(f"you've already handled \"{rung_label(family, level.proven)}\"")
        elif level.proven < 0:
            notes.append(f"\"{label}\" is the right first step for a {fam}")
        else:
            notes.append(f"\"{label}\" is one careful step up from what you've proven")

    if not notes:
        return True, "No strong actives. Nothing here to build tolerance to.", margin
    return True, "Within your tolerance: " + "; ".join(notes) + ".", margin


def apply_quiz(profile: UserProfile, burned: list[Product], worked: list[Product]) -> UserProfile:
    tol = {k: v.model_copy() for k, v in profile.tolerance.items()}
    for product in burned:
        for family, rung in catalog.rungs(product).items():
            level = tol.setdefault(family, ToleranceLevel())
            level.cap = rung if level.cap is None else min(level.cap, rung)
    for product in worked:
        for family, rung in catalog.rungs(product).items():
            level = tol.setdefault(family, ToleranceLevel())
            level.proven = max(level.proven, rung)
    for level in tol.values():
        if level.cap is not None:
            level.proven = min(level.proven, level.cap - 1)
    return profile.model_copy(update={"tolerance": tol})


def apply_checkin(
    profile: UserProfile,
    product: Product,
    severity: str,
    started_at: datetime.datetime | None,
    had_bad_reaction: bool,
    now: datetime.datetime | None = None,
) -> tuple[UserProfile, str]:
    now = now or datetime.datetime.utcnow()
    tol = {k: v.model_copy() for k, v in profile.tolerance.items()}
    rungs = catalog.rungs(product)

    if severity in BAD_REACTIONS:
        for family, rung in rungs.items():
            level = tol.setdefault(family, ToleranceLevel())
            level.cap = rung if level.cap is None else min(level.cap, rung)
            level.proven = min(level.proven, rung - 1)
        if rungs:
            capped = ", ".join(f"\"{rung_label(f, r)}\"" for f, r in rungs.items())
            msg = (f"Logged. Nothing at {capped} or stronger will be suggested again. "
                   "Pause this product and stick to gentle cleansing and barrier repair until your skin settles.")
        else:
            msg = "Logged. We'll steer you away from this product. Pause it and let your skin settle."
        return profile.model_copy(update={"tolerance": tol}), msg

    if severity == "tingling":
        return profile, ("Mild tingling is common in the first couple of weeks. Keep to 2-3 nights a week, "
                         "and if it turns into redness or peeling, log it.")

    # "fine"
    if not rungs:
        return profile, "Noted. Glad it's working."
    days = (now - started_at).days if started_at else 0
    if days >= PROVE_AFTER_DAYS and not had_bad_reaction:
        unlocked = []
        for family, rung in rungs.items():
            level = tol.setdefault(family, ToleranceLevel())
            if level.cap is None or rung < level.cap:
                level.proven = max(level.proven, rung)
                unlocked.append(rung_label(family, allowed_rung(
                    profile.model_copy(update={"tolerance": tol}), family)))
        msg = f"{days} days with no reaction, so this strength is proven."
        if unlocked:
            msg += " You can now try: " + ", ".join(f"\"{u}\"" for u in unlocked) + "."
        return profile.model_copy(update={"tolerance": tol}), msg
    remaining = max(0, PROVE_AFTER_DAYS - days)
    return profile, f"Noted. {remaining} more days without a reaction and we'll unlock the next step."


def scan_reaction_suspects(
    deltas: dict,
    usage: list[tuple[Product, datetime.datetime]],
    now: datetime.datetime | None = None,
) -> list[Product]:
    """Products with actives started recently, if an irritation reading
    (redness, texture, dryness) got measurably worse."""
    if not irritation_readings(deltas):
        return []
    now = now or datetime.datetime.utcnow()
    window = datetime.timedelta(days=SCAN_REACTION_WINDOW_DAYS)
    return [p for p, started in usage if p.actives and now - started <= window]


# YouCam metrics whose worsening after a new active signals irritation, and
# the reaction severity it maps to (rough texture / dryness = peeling).
IRRITATION_METRICS = {"redness": ("redness", "redness"), "texture": ("texture", "peeling"),
                      "moisture": ("dryness", "peeling")}


def irritation_readings(deltas: dict) -> list[str]:
    return [m for m in IRRITATION_METRICS if deltas.get(m, {}).get("direction") == "worsened"]


def scan_severity(readings: list[str]) -> str:
    return "redness" if "redness" in readings else "peeling"


def reaction_alert(reaction_id: int, product: Product, severity: str = "redness") -> ReactionAlert:
    name = f"{product.brand} {product.name}"
    strength = ", ".join(catalog.strength_labels(product))
    reading = "redness" if severity == "redness" else "texture or dryness"
    return ReactionAlert(
        reaction_id=reaction_id,
        product_id=product.id,
        product_name=name,
        text=(f"Your {reading} reading got worse since you started {name}"
              f"{f' ({strength})' if strength else ''}. Was it irritating your skin?"),
    )
