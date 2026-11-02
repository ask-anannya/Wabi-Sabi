"""
Trust engine: the hard tolerance gate, overpriced flag, hype gap (editorial
buzz), community "people like you", style tiebreaker, and honest dupes.
"""

import asyncio

import uuid

from models.profile import UserProfile
from services import catalog, profile_store, tolerance, trust_engine

WRINKLES = [{"name": "wrinkle", "band": "moderate", "normalised": 0.6}]


def _run(coro):
    return asyncio.run(coro)


def test_matches_never_include_products_over_tolerance():
    profile = tolerance.apply_quiz(UserProfile(user_id="u"), burned=[catalog.get("to-retinol-1")], worked=[])
    result = _run(trust_engine.honest_matches(profile, WRINKLES, limit=12))
    assert result["matches"]
    for m in result["matches"]:
        assert m.fits_tolerance
        assert tolerance.fits(catalog.get(m.product.id), profile)[0]


def test_wrinkle_reading_surfaces_a_retinoid():
    profile = UserProfile(user_id="u")
    result = _run(trust_engine.honest_matches(profile, WRINKLES, limit=6))
    retinoids = [m for m in result["matches"] if "retinoid" in catalog.rungs(catalog.get(m.product.id))]
    assert retinoids, "moderate wrinkles should get a gentle retinoid"
    assert all(catalog.rungs(catalog.get(m.product.id))["retinoid"] == 0 for m in retinoids)


def test_ce_ferulic_is_overpriced_with_a_named_equivalent():
    value, cheaper = trust_engine.value_info(catalog.get("skinceuticals-ce-ferulic"))
    assert value.overpriced
    assert cheaper is not None and cheaper.price_per_ml < value.price_per_ml / 2


def test_cheap_product_is_not_flagged_overpriced():
    value, _ = trust_engine.value_info(catalog.get("to-retinol-02"))
    assert not value.overpriced


def test_hype_gap_labels():
    assert trust_engine.hype_info(0.95, 0.3).label == "hyped"
    assert trust_engine.hype_info(0.9, 0.85).label == "earned"
    assert trust_engine.hype_info(0.35, 0.9).label == "under_the_radar"
    assert trust_engine.hype_info(None, 0.5).label == "unknown"


def test_honest_check_on_hyped_luxury_cream():
    profile = UserProfile(user_id="u")
    result = _run(trust_engine.honest_check(catalog.get("la-mer-creme"), profile, None))
    match = result["match"]
    assert match.hype.label == "hyped"
    assert match.value.overpriced
    assert match.dupe is not None
    assert match.people_like_you is not None
    assert any(r.source == "editorial" and r.kind == "hype" for r in match.reasons)


def test_dupe_keeps_the_same_strength_and_fits_the_user():
    profile = tolerance.apply_quiz(UserProfile(user_id="u"), burned=[], worked=[catalog.get("to-retinol-05")])
    result = _run(trust_engine.honest_check(catalog.get("de-a-passioni"), profile, WRINKLES))
    dupe = result["match"].dupe
    assert dupe is not None
    dupe_product = catalog.get(dupe.product.id)
    assert catalog.rungs(dupe_product)["retinoid"] == catalog.rungs(catalog.get("de-a-passioni"))["retinoid"]
    assert dupe.savings_pct >= 40


def test_style_prefs_drive_the_taste_tiebreaker():
    profile = UserProfile(user_id="u", style_prefs=["budget", "derm"])
    result = _run(trust_engine.honest_matches(profile, WRINKLES, limit=6))
    assert all(m.taste_affinity is not None for m in result["matches"])
    assert any(r.kind == "taste" and r.label == "Your style" for m in result["matches"] for r in m.reasons)


def test_people_like_you_needs_enough_reports():
    me = UserProfile(user_id=f"me-{uuid.uuid4()}", skin_type="dry")
    plu = trust_engine.people_like_you(catalog.get("gg-a-game-5"), me)
    assert plu.label == "unknown" and "Not enough reports" in plu.text


def test_people_like_you_counts_matching_cohort_only():
    product = catalog.get("pc-c15")
    tag = uuid.uuid4().hex[:8]
    # The test DB persists between runs: start this product's cohort from empty.
    with profile_store.SessionLocal() as session:
        session.query(profile_store.ReactionRecord).filter(
            profile_store.ReactionRecord.product_id == product.id).delete()
        session.commit()
    # Three oily-skin vitamin C newcomers: two reacted, one fine.
    for i, severity in enumerate(["redness", "peeling", "fine"]):
        uid = f"cohort-{tag}-{i}"
        profile_store.save_profile(UserProfile(user_id=uid, skin_type="oily"))
        profile_store.log_reaction(uid, product.id, severity, source="checkin")
    # Different skin type: must not count.
    other = f"cohort-{tag}-dry"
    profile_store.save_profile(UserProfile(user_id=other, skin_type="dry"))
    profile_store.log_reaction(other, product.id, "fine", source="checkin")

    me = UserProfile(user_id=f"me-{tag}", skin_type="oily")
    plu = trust_engine.people_like_you(product, me)
    assert plu.label == "reacted"
    assert plu.text.startswith("2 of 3 people with oily skin who are new to vitamin C reported")


def test_product_over_tolerance_offers_a_safer_version():
    profile = tolerance.apply_quiz(UserProfile(user_id="u"), burned=[catalog.get("to-retinol-1")], worked=[catalog.get("to-retinol-02")])
    match = _run(trust_engine.honest_check(catalog.get("de-a-passioni"), profile, WRINKLES))["match"]
    assert not match.fits_tolerance
    assert match.dupe is not None and match.dupe.kind == "safer"
    safer = catalog.get(match.dupe.product.id)
    assert tolerance.fits(safer, profile)[0]
    assert catalog.rungs(safer)["retinoid"] == tolerance.allowed_rung(profile, "retinoid")


def test_overpriced_never_names_a_product_that_burned_the_user():
    profile = tolerance.apply_quiz(UserProfile(user_id="u"), burned=[catalog.get("to-retinol-1")], worked=[catalog.get("to-retinol-02")])
    match = _run(trust_engine.honest_check(catalog.get("de-a-passioni"), profile, WRINKLES))["match"]
    overpriced = next(r for r in match.reasons if r.label == "Overpriced")
    assert "Retinol 1% in Squalane" not in overpriced.text


def test_honest_picks_exclude_overpriced_and_hyped_products():
    result = _run(trust_engine.honest_matches(UserProfile(user_id="u"), None, limit=12))
    assert result["matches"]
    for m in result["matches"]:
        assert not m.value.overpriced
        assert m.hype.label != "hyped"
