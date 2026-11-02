"""
Active-ingredient tolerance ladders. Each family is an ordered list of rungs
from gentlest (0) to strongest; a product's rung is the first rung whose
ceiling covers its strongest active. The tolerance model
(services/tolerance.py) only ever lets a user climb ONE rung above what
they've proven they tolerate — the "I jumped straight to 1% retinol and
burned my face off" failure mode is exactly what this exists to prevent.

Concentrations a brand doesn't disclose are treated as UNDISCLOSED_RUNG
(conservatively strong) rather than guessed low: if a brand won't say how
strong it is, we don't assume it's gentle.
"""

# family -> list of (rung_label, {form: max_pct}). A form missing from a
# rung's dict means that form can't sit on that rung (it's stronger).
LADDERS: dict[str, list[tuple[str, dict[str, float]]]] = {
    "retinoid": [
        ("Gentle retinoid (HPR / ≤0.1% retinol)", {"hpr": 100.0, "retinyl_ester": 100.0, "retinol": 0.1}),
        ("Low retinol (≤0.3%) / starter retinal", {"retinol": 0.3, "retinal": 0.02}),
        ("Mid retinol (≤0.5%) / retinal ≤0.05%", {"retinol": 0.5, "retinal": 0.05}),
        ("High retinol (≤1%) / retinal ≤0.1%", {"retinol": 1.0, "retinal": 0.1}),
        ("Strong retinal (≤0.2%) / adapalene", {"retinal": 0.2, "adapalene": 0.1}),
    ],
    # AHA rungs are in glycolic-equivalent %: lactic and mandelic are larger
    # molecules that penetrate more slowly, so they're counted at half strength.
    "aha": [
        ("Gentle AHA (≤5%)", {"glycolic": 5.0}),
        ("Light AHA (≤8%)", {"glycolic": 8.0}),
        ("Moderate AHA (≤10%)", {"glycolic": 10.0}),
        ("Strong AHA (≤15%)", {"glycolic": 15.0}),
        ("Peel-strength AHA (>15%)", {"glycolic": 100.0}),
    ],
    "bha": [
        ("Gentle BHA (≤0.5%)", {"salicylic": 0.5}),
        ("Light BHA (≤1%)", {"salicylic": 1.0}),
        ("Full-strength BHA (≤2%)", {"salicylic": 2.0}),
    ],
    "vitamin_c": [
        ("Vitamin C derivative", {"derivative": 100.0}),
        ("L-ascorbic acid ≤10%", {"l_ascorbic": 10.0}),
        ("L-ascorbic acid ≤15%", {"l_ascorbic": 15.0}),
        ("L-ascorbic acid >15%", {"l_ascorbic": 100.0}),
    ],
    "benzoyl_peroxide": [
        ("Benzoyl peroxide ≤2.5%", {"benzoyl_peroxide": 2.5}),
        ("Benzoyl peroxide ≤5%", {"benzoyl_peroxide": 5.0}),
        ("Benzoyl peroxide ≤10%", {"benzoyl_peroxide": 10.0}),
    ],
    "niacinamide": [
        ("Niacinamide ≤5%", {"niacinamide": 5.0}),
        ("Niacinamide ≤10%", {"niacinamide": 10.0}),
        ("Niacinamide >10%", {"niacinamide": 100.0}),
    ],
    "azelaic": [
        ("Azelaic acid ≤10%", {"azelaic": 10.0}),
        ("Azelaic acid >10%", {"azelaic": 100.0}),
    ],
}

# Where someone with no history starts. Retinoids, acids and benzoyl peroxide
# start at the bottom; low-irritation families can start one step up.
STARTER_RUNG = {
    "retinoid": 0, "aha": 0, "bha": 1, "vitamin_c": 1,
    "benzoyl_peroxide": 0, "niacinamide": 1, "azelaic": 0,
}

# Forms whose % is converted before ladder lookup (see AHA note above).
FORM_EQUIVALENCE = {
    "lactic": ("glycolic", 0.5),
    "mandelic": ("glycolic", 0.5),
    "betaine_salicylate": ("salicylic", 0.25),
}

# Undisclosed % → assume the second-strongest rung of the family.
def undisclosed_rung(family: str) -> int:
    return max(0, len(LADDERS[family]) - 2)


def rung_for(family: str, form: str, pct: float | None, rinse_off: bool = False) -> int:
    """Ladder rung for one active. Rinse-off products (cleansers) sit one rung
    lower — contact time is seconds, not hours."""
    if family not in LADDERS:
        return 0
    if pct is None:
        rung = undisclosed_rung(family)
    else:
        if form in FORM_EQUIVALENCE:
            form, factor = FORM_EQUIVALENCE[form]
            pct = pct * factor
        rung = len(LADDERS[family]) - 1
        for i, (_label, ceilings) in enumerate(LADDERS[family]):
            if form in ceilings and pct <= ceilings[form]:
                rung = i
                break
    if rinse_off:
        rung = max(0, rung - 1)
    return rung


def rung_label(family: str, rung: int) -> str:
    ladder = LADDERS.get(family)
    if not ladder:
        return family
    return ladder[max(0, min(rung, len(ladder) - 1))][0]


FAMILY_LABELS = {
    "retinoid": "retinoid",
    "aha": "AHA exfoliant",
    "bha": "BHA exfoliant",
    "vitamin_c": "vitamin C",
    "benzoyl_peroxide": "benzoyl peroxide",
    "niacinamide": "niacinamide",
    "azelaic": "azelaic acid",
}

SENSITIZERS = {
    "fragrance": "Added fragrance / parfum",
    "essential_oils": "Essential oils",
    "alcohol_denat": "Drying alcohol (alcohol denat.)",
    "lanolin": "Lanolin",
    "coconut_derivatives": "Coconut-derived oils",
}

# advice_bands categories (domain/advice_bands.py) -> what the product must
# carry in its own `categories` list to count as addressing that need.
# Constraint-style categories (fragrance_free, retinoid_escalation, ...) are
# handled in services/trust_engine.py as filters, not as needs.
NEED_CATEGORIES = {
    "hydrating", "barrier_repair", "antioxidant", "sunscreen_strict", "retinoid_gradual",
    "vitamin_c", "brightening", "oil_control", "exfoliant_mild", "pore_minimizing",
    "gentle_cleanser", "non_comedogenic",
}

EVIDENCE_WEIGHT = {"strong": 1.0, "moderate": 0.6, "weak": 0.25}
