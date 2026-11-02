"""
The Honest Match trust engine. Four sources, one score:

  YouCam  -> what your skin needs right now (metric bands -> advice categories)
  You     -> what your skin tolerates (services/tolerance.py, a hard gate)
  Catalog -> what's actually in the bottle and what it costs per ml
  Signals -> the layer marketing hides behind:
               * Hype gap: editorial buzz tier vs. the product's real substance
               * People like you: what this app's users with your skin type and
                 experience level actually logged after using it
               * Your style: brand style tags vs. your shopping style (tiebreaker)
               * Honest dupe: same active & strength, cheaper, similar brand style

Every reason shown to the user is built here from structured facts — no LLM
writes claims about a product, so nothing can be hallucinated into a
recommendation.
"""

from domain.actives import EVIDENCE_WEIGHT, FAMILY_LABELS, SENSITIZERS
from domain.advice_bands import ADVICE_BANDS
from models.profile import (
    Dupe, HonestMatch, HypeInfo, PeopleLikeYou, Product, Reason, UserProfile, ValueInfo,
)
from services import catalog, profile_store, tolerance

METRIC_LABELS = {
    "moisture": "dryness", "wrinkle": "fine lines", "redness": "redness",
    "age_spot": "dark spots", "acne": "breakouts", "pore": "visible pores",
    "oiliness": "oiliness", "radiance": "dullness", "texture": "uneven texture",
    "firmness": "loss of firmness", "eye_bag": "under-eye puffiness",
}
CATEGORY_LABELS = {
    "hydrating": "hydration", "barrier_repair": "barrier repair", "antioxidant": "antioxidant protection",
    "sunscreen_strict": "daily sun protection", "retinoid_gradual": "a gradual retinoid",
    "vitamin_c": "vitamin C", "brightening": "brightening", "oil_control": "oil control",
    "exfoliant_mild": "gentle exfoliation", "pore_minimizing": "pore care",
    "gentle_cleanser": "gentle cleansing", "non_comedogenic": "non-clogging",
}
# Baseline needs everyone has, so a first-time user with no scan still gets
# sensible basics. Kept low so real scan readings dominate.
BASELINE_NEEDS = {"sunscreen_strict": 0.35, "gentle_cleanser": 0.2, "hydrating": 0.2}
SEVERITY_FALLBACK = 0.6  # weight for a self-reported concern with no scan

OVERPRICED_RATIO = 2.0
HYPE_GAP_THRESHOLD = 0.25


# ---------- needs from YouCam ----------

class Needs:
    def __init__(self):
        self.weights: dict[str, float] = dict(BASELINE_NEEDS)
        self.sources: dict[str, list[str]] = {}  # category -> human metric readings that drove it
        self.extra_sensitizers: set[str] = set()
        self.no_escalation: set[str] = set()
        self.avoid_occlusive = False
        self.from_scan = False

    def add(self, category: str, weight: float, source: str):
        self.weights[category] = max(self.weights.get(category, 0.0), weight)
        self.sources.setdefault(category, []).append(source)


def needs_from(metrics: list[dict] | None, profile: UserProfile) -> Needs:
    needs = Needs()
    readings: list[tuple[str, str, float]] = []
    if metrics:
        needs.from_scan = True
        readings = [(m["name"], m["band"], float(m["normalised"])) for m in metrics]
    else:
        readings = [(c, "moderate", SEVERITY_FALLBACK) for c in profile.concerns if c in ADVICE_BANDS]

    for name, band, severity in readings:
        config = ADVICE_BANDS.get(name)
        if not config or band == "clear":
            continue
        label = f"{METRIC_LABELS.get(name, name)} ({band})"
        for cat in config.get("recommend", {}).get(band, []):
            if cat == "fragrance_free":
                needs.extra_sensitizers.add("fragrance")
            elif cat != "derm_referral":
                needs.add(cat, severity, label)
        for cat in config.get("avoid", {}).get(band, []):
            if cat == "alcohol_denat":
                needs.extra_sensitizers.add("alcohol_denat")
            elif cat == "retinoid_escalation":
                needs.no_escalation.add("retinoid")
            elif cat == "high_pct_exfoliant":
                needs.no_escalation.update({"aha", "bha"})
            elif cat == "occlusive_heavy":
                needs.avoid_occlusive = True
    return needs


def _need_fit(product: Product, needs: Needs) -> tuple[float, list[str]]:
    hits = [c for c in product.categories if c in needs.weights]
    if not hits:
        return 0.0, []
    # Best single need + a little credit for covering more than one.
    weights = sorted((needs.weights[c] for c in hits), reverse=True)
    score = min(1.0, weights[0] + 0.15 * sum(weights[1:]))
    return score, hits


# ---------- value & substance (catalog) ----------

def _equivalents(product: Product, profile: UserProfile | None = None, needs: Needs | None = None) -> list[Product]:
    """Same job, same strength: same value group, same rung on every active
    family, at least as well evidenced. Optionally only ones that fit the user."""
    group = catalog.value_group(product)
    rungs = catalog.rungs(product)
    out = []
    for other in catalog.all_products().values():
        if other.id == product.id or catalog.value_group(other) != group:
            continue
        if rungs and catalog.rungs(other).get(product.primary_family) != rungs.get(product.primary_family):
            continue
        if not rungs and not (set(other.categories) & set(product.categories)):
            continue
        if EVIDENCE_WEIGHT.get(other.evidence, 0) < EVIDENCE_WEIGHT.get(product.evidence, 0):
            continue
        if profile is not None:
            ok, _, _ = tolerance.fits(other, profile, needs.extra_sensitizers if needs else None,
                                      needs.no_escalation if needs else None)
            if not ok:
                continue
        out.append(other)
    return out


def value_info(product: Product) -> tuple[ValueInfo, Product | None]:
    median = catalog.group_medians()[catalog.value_group(product)]
    ratio = product.price_per_ml / median if median else 1.0
    cheaper = [p for p in _equivalents(product) if p.price_per_ml <= product.price_per_ml / OVERPRICED_RATIO]
    best = min(cheaper, key=lambda p: p.price_per_ml) if cheaper else None
    overpriced = ratio >= OVERPRICED_RATIO and best is not None
    return ValueInfo(
        price_per_ml=round(product.price_per_ml, 3),
        group_median_per_ml=round(median, 3),
        ratio=round(ratio, 2),
        overpriced=overpriced,
    ), (best if overpriced else None)


def substance(product: Product, value: ValueInfo) -> float:
    evidence = EVIDENCE_WEIGHT.get(product.evidence, 0.5) * (0.8 if product.undisclosed else 1.0)
    value_score = min(1.0, 1.0 / value.ratio) if value.ratio > 0 else 1.0
    return round(0.6 * evidence + 0.4 * value_score, 3)


def hype_info(popularity: float | None, subst: float) -> HypeInfo:
    if popularity is None:
        return HypeInfo(popularity=None, substance=subst, gap=None, label="unknown")
    gap = round(popularity - subst, 3)
    if gap > HYPE_GAP_THRESHOLD:
        label = "hyped"
    elif gap < -HYPE_GAP_THRESHOLD:
        label = "under_the_radar"
    else:
        label = "earned"
    return HypeInfo(popularity=round(popularity, 3), substance=subst, gap=gap, label=label)


# ---------- signals: editorial buzz, community reactions, your style ----------

COHORT_MIN_REPORTS = 3


class SignalsContext:
    """Everything beyond the scan, the tolerance gate and the catalog. All
    local: editorial brand data (api/data/brands.json) and this app's own
    community reaction log."""

    def __init__(self, profile: UserProfile):
        self.profile = profile

    def buzz(self, brand: str) -> float | None:
        return catalog.buzz_score(brand)

    def styles(self, brand: str) -> set[str]:
        return catalog.brand_styles(brand)

    def style_affinity(self, brand: str) -> float | None:
        prefs = set(self.profile.style_prefs)
        if not prefs:
            return None
        return _jaccard(prefs, self.styles(brand))


def _jaccard(a: set[str], b: set[str]) -> float:
    return round(len(a & b) / len(a | b), 3) if a and b else 0.0


def _experience(profile: UserProfile, family: str | None) -> str:
    if family is None:
        return "any"
    level = profile.tolerance.get(family)
    return "new" if level is None or level.proven < 0 else "experienced"


def people_like_you(product: Product, profile: UserProfile) -> PeopleLikeYou:
    """What happened to OTHER users of this app with the same skin type and
    the same experience level with this product's active: the honest version
    of "it worked for her"."""
    family = product.primary_family
    try:
        reports = profile_store.cohort_reports(product.id, exclude_user=profile.user_id)
    except Exception as e:
        print(f"[trust_engine] cohort lookup failed: {e}")
        reports = []
    mine = _experience(profile, family)
    cohort = [
        severity for other, severity in reports
        if (not profile.skin_type or other.skin_type == profile.skin_type)
        and _experience(other, family) == mine
    ]
    who = f"{profile.skin_type} skin" if profile.skin_type else "skin like yours"
    if mine != "any":
        who += f" who are {'new to' if mine == 'new' else 'experienced with'} {FAMILY_LABELS.get(family, family)}"
    if len(cohort) < COHORT_MIN_REPORTS:
        return PeopleLikeYou(affinity=None, label="unknown", text=(
            f"Not enough reports yet from people with {who}. Whatever worked for an influencer, "
            "your tolerance decides."))
    bad = sum(1 for s in cohort if s in tolerance.BAD_REACTIONS)
    ok_share = round(1 - bad / len(cohort), 2)
    if bad / len(cohort) >= 0.4:
        return PeopleLikeYou(affinity=ok_share, label="reacted", text=(
            f"{bad} of {len(cohort)} people with {who} reported redness or peeling on this."))
    if bad == 0:
        return PeopleLikeYou(affinity=ok_share, label="tolerated", text=(
            f"All {len(cohort)} people with {who} who logged this tolerated it."))
    return PeopleLikeYou(affinity=ok_share, label="mixed", text=(
        f"{len(cohort) - bad} of {len(cohort)} people with {who} tolerated this; {bad} reacted."))


def _possessive(name: str) -> str:
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def safer_alternative(product: Product, profile: UserProfile, needs: Needs) -> Dupe | None:
    """For a product that fails the user's tolerance: the strongest version of
    the same job they CAN handle, cheapest first among equals."""
    group = catalog.value_group(product)
    family = product.primary_family
    options = []
    for other in catalog.all_products().values():
        if other.id == product.id or catalog.value_group(other) != group:
            continue
        if not family and not (set(other.categories) & set(product.categories)):
            continue
        if not tolerance.fits(other, profile, needs.extra_sensitizers, needs.no_escalation)[0]:
            continue
        if needs.avoid_occlusive and other.occlusive:
            continue
        options.append(other)
    if not options:
        return None
    best = max(options, key=lambda p: (catalog.rungs(p).get(family, 0) if family else 0,
                                       EVIDENCE_WEIGHT.get(p.evidence, 0), -p.price_per_ml))
    strengths = catalog.strength_labels(best)
    strength = f" ({strengths[0]})" if strengths else ""
    return Dupe(
        kind="safer",
        product=catalog.summary(best),
        savings_pct=max(0, round(100 * (1 - best.price_per_ml / product.price_per_ml))),
        style_overlap=None,
        text=f"A version your skin can handle: {best.brand} {best.name}{strength}, ${best.price_per_ml:.2f}/ml.",
    )


def find_dupe(ctx: SignalsContext, product: Product, profile: UserProfile, needs: Needs) -> Dupe | None:
    candidates = [p for p in _equivalents(product, profile, needs) if p.price_per_ml <= product.price_per_ml * 0.6]
    if not candidates:
        return None
    src_styles = ctx.styles(product.brand)
    # Evidence first, then similar brand style, then price: style never beats substance.
    best = max(candidates, key=lambda p: (EVIDENCE_WEIGHT.get(p.evidence, 0),
                                          _jaccard(src_styles, ctx.styles(p.brand)), -p.price_per_ml))
    savings = min(99, round(100 * (1 - best.price_per_ml / product.price_per_ml)))
    strengths = catalog.strength_labels(best)
    same = (f"Same job, same strength ({strengths[0]})" if strengths
            else f"Same job ({CATEGORY_LABELS.get(best.categories[0], best.category)})")
    return Dupe(
        product=catalog.summary(best),
        savings_pct=savings,
        style_overlap=_jaccard(src_styles, ctx.styles(best.brand)),
        text=f"{same}, {savings}% less per ml: {best.brand} {best.name}.",
    )


# ---------- scoring ----------

def _score(need: float, subst: float, taste: float | None, margin: int, hype: HypeInfo, fits: bool) -> int:
    tol = 1.0 if margin >= 1 else 0.85
    taste_component = taste if taste is not None else 0.5
    # Style is a tiebreaker between honest options, never a reason to
    # outrank a product with more substance.
    raw = 0.40 * need + 0.30 * subst + 0.10 * taste_component + 0.20 * tol
    if hype.gap is not None and hype.gap > HYPE_GAP_THRESHOLD:
        raw -= 0.5 * (hype.gap - HYPE_GAP_THRESHOLD)
    score = round(100 * max(0.0, min(1.0, raw)))
    return min(score, 30) if not fits else score


def _evaluate(product: Product, profile: UserProfile, needs: Needs, ctx: SignalsContext) -> HonestMatch:
    reasons: list[Reason] = []
    need, hits = _need_fit(product, needs)
    if hits:
        drivers = sorted({s for c in hits for s in needs.sources.get(c, [])})
        what = ", ".join(CATEGORY_LABELS.get(c, c) for c in hits[:3])
        if drivers:
            reasons.append(Reason(kind="need", label="Your skin needs this", tone="good", source="youcam",
                                  text=f"Provides {what}, which your {', '.join(drivers)} reading calls for."))
        else:
            reasons.append(Reason(kind="need", label="Everyday basic", tone="neutral", source="you",
                                  text=f"Provides {what}, a basic every routine needs."))
    else:
        reasons.append(Reason(kind="need", label="Not what you need now", tone="warn", source="youcam",
                              text="Doesn't target anything your latest reading flagged."))

    fits, tol_text, margin = tolerance.fits(product, profile, needs.extra_sensitizers, needs.no_escalation)
    if fits and needs.avoid_occlusive and product.occlusive:
        fits, tol_text = False, "A heavy, occlusive texture. Your breakout reading says to skip these for now."
    reasons.append(Reason(kind="tolerance", label="Fits your tolerance" if fits else "Not for your skin",
                          tone="good" if fits else "bad", source="you", text=tol_text))

    value, cheaper = value_info(product)
    # Only ever NAME a cheaper equivalent this user can actually use — never
    # point someone at the exact product that burned them.
    named = cheaper
    if cheaper is not None and not tolerance.fits(cheaper, profile, needs.extra_sensitizers, needs.no_escalation)[0]:
        usable = [p for p in _equivalents(product, profile, needs)
                  if p.price_per_ml <= product.price_per_ml / OVERPRICED_RATIO]
        named = min(usable, key=lambda p: p.price_per_ml) if usable else None
    if value.overpriced and cheaper is not None:
        alternative = (f"{named.brand} {named.name} does the same at ${named.price_per_ml:.2f}/ml." if named
                       else f"The same strength sells for as little as ${cheaper.price_per_ml:.2f}/ml elsewhere.")
        reasons.append(Reason(kind="value", label="Overpriced", tone="bad", source="catalog", text=(
            f"${value.price_per_ml:.2f}/ml, {value.ratio:.1f}x the typical price for this job. {alternative}")))
    elif value.ratio <= 0.75:
        reasons.append(Reason(kind="value", label="Great value", tone="good", source="catalog",
                              text=f"${value.price_per_ml:.2f}/ml, below the typical ${value.group_median_per_ml:.2f}/ml for this job."))
    else:
        reasons.append(Reason(kind="value", label="Fair price", tone="neutral", source="catalog",
                              text=f"${value.price_per_ml:.2f}/ml, close to the typical ${value.group_median_per_ml:.2f}/ml for this job."))
    if product.undisclosed:
        reasons.append(Reason(kind="value", label="Strength undisclosed", tone="warn", source="catalog",
                              text="The brand doesn't publish the active's concentration, so we treat it as potentially strong."))

    subst = substance(product, value)
    hype = hype_info(ctx.buzz(product.brand), subst)
    buzz_word = catalog.buzz_level(product.brand) or "unrated"
    if hype.label == "hyped":
        reasons.append(Reason(kind="hype", label="More hype than substance", tone="bad", source="editorial", text=(
            f"{product.brand} is a {buzz_word}-buzz brand, but this product's evidence and value score "
            f"only {round(100 * subst)}/100.")))
    elif hype.label == "earned" and value.overpriced:
        reasons.append(Reason(kind="hype", label="Formula earns it, price doesn't", tone="warn", source="editorial", text=(
            f"{_possessive(product.brand)} buzz is backed by a proven formula, but you're paying a "
            f"brand premium of {value.ratio:.1f}x for it.")))
    elif hype.label == "earned":
        reasons.append(Reason(kind="hype", label="Buzz is earned", tone="good", source="editorial",
                              text=f"The buzz matches what's in the bottle (substance {round(100 * subst)}/100)."))
    elif hype.label == "under_the_radar":
        reasons.append(Reason(kind="hype", label="Under the radar", tone="good", source="editorial",
                              text=f"Less buzz than it deserves: substance {round(100 * subst)}/100."))

    taste = ctx.style_affinity(product.brand)
    if taste is not None:
        shared = sorted(set(profile.style_prefs) & ctx.styles(product.brand))
        if shared:
            reasons.append(Reason(kind="taste", label="Your style", tone="good", source="you",
                                  text=f"Fits your shopping style: {', '.join(shared)}."))
        else:
            reasons.append(Reason(kind="taste", label="Not your usual style", tone="neutral", source="you",
                                  text=f"{product.brand} isn't your usual kind of brand. Judged on substance, not style."))

    score = _score(need, subst, taste, margin, hype, fits)
    verdict = "not_for_you" if not fits else ("great_fit" if score >= 70 else "good_fit")
    if not fits:
        headline = tol_text
    elif value.overpriced and cheaper is not None:
        headline = (f"Works for you, but overpriced. {named.brand} does the same for less." if named
                    else "Works for you, but overpriced for what's in the bottle.")
    elif hype.label == "hyped":
        headline = "Fits you, but you're paying for the hype."
    elif verdict == "great_fit":
        headline = "Honest pick: does what your skin needs, within your tolerance, fairly priced."
    else:
        headline = "A reasonable option for you."

    return HonestMatch(
        product=catalog.summary(product), honest_score=score, fits_tolerance=fits, verdict=verdict,
        headline=headline, reasons=reasons, value=value, hype=hype, taste_affinity=taste,
    )


async def honest_matches(profile: UserProfile, metrics: list[dict] | None, limit: int = 6) -> dict:
    needs = needs_from(metrics, profile)
    ctx = SignalsContext(profile)

    evaluated = []
    for product in catalog.all_products().values():
        need, _ = _need_fit(product, needs)
        if need <= 0:
            continue
        match = _evaluate(product, profile, needs, ctx)
        if match.fits_tolerance:
            evaluated.append(match)

    # One pick per need category first (a routine, not six retinols), then fill by score.
    evaluated.sort(key=lambda m: m.honest_score, reverse=True)
    picked, seen_groups = [], set()
    for m in evaluated:
        group = catalog.value_group(catalog.get(m.product.id))
        if group not in seen_groups:
            picked.append(m)
            seen_groups.add(group)
        if len(picked) >= limit:
            break

    _enrich(picked, profile, needs, ctx)
    return {
        "matches": picked,
        "needs": [{"category": c, "label": CATEGORY_LABELS.get(c, c), "weight": round(w, 2),
                   "from": needs.sources.get(c, [])} for c, w in sorted(needs.weights.items(), key=lambda x: -x[1])],
        "avoiding": sorted(SENSITIZERS.get(s, s) for s in set(profile.sensitizers) | needs.extra_sensitizers),
        "from_scan": needs.from_scan,
    }


async def honest_check(product: Product, profile: UserProfile, metrics: list[dict] | None) -> dict:
    """Full honest breakdown for ANY product, e.g. the one an influencer just pushed."""
    needs = needs_from(metrics, profile)
    ctx = SignalsContext(profile)
    match = _evaluate(product, profile, needs, ctx)
    _enrich([match], profile, needs, ctx, always_dupe=True)
    return {"match": match}


def _enrich(matches: list[HonestMatch], profile: UserProfile, needs: Needs, ctx: SignalsContext,
            always_dupe: bool = False) -> None:
    for m in matches:
        product = catalog.get(m.product.id)
        plu = people_like_you(product, profile)
        m.people_like_you = plu
        m.reasons.append(Reason(kind="people_like_you", label="People like you?", source="community",
                                tone={"tolerated": "good", "reacted": "bad", "mixed": "warn"}.get(plu.label, "neutral"),
                                text=plu.text))
        dupe = None
        if always_dupe or m.value.overpriced or m.hype.label == "hyped":
            dupe = find_dupe(ctx, product, profile, needs)
        if dupe is None and not m.fits_tolerance and always_dupe:
            dupe = safer_alternative(product, profile, needs)
        if dupe is not None:
            m.dupe = dupe
            m.reasons.append(Reason(
                kind="dupe", label="Honest dupe" if dupe.kind == "dupe" else "Try this instead", tone="good",
                source="catalog" if dupe.kind == "dupe" else "you", text=dupe.text))
