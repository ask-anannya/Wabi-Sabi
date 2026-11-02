"""
Tolerance model: the safety rules that keep the app from recommending the
1% retinol that burned someone, or a jump of more than one rung.
"""

import datetime

from models.profile import ToleranceLevel, UserProfile
from services import catalog, tolerance


def _p(pid):
    return catalog.get(pid)


def test_rung_lookup_orders_retinoids_by_strength():
    assert catalog.rungs(_p("to-granactive-2"))["retinoid"] == 0
    assert catalog.rungs(_p("to-retinol-02"))["retinoid"] == 1
    assert catalog.rungs(_p("to-retinol-1"))["retinoid"] == 3
    assert catalog.rungs(_p("gg-a-game-10"))["retinoid"] == 3
    assert catalog.rungs(_p("differin-gel"))["retinoid"] == 4


def test_undisclosed_strength_is_treated_as_strong():
    assert catalog.rungs(_p("sunday-riley-a-plus"))["retinoid"] >= 3


def test_rinse_off_sits_one_rung_lower():
    assert catalog.rungs(_p("panoxyl-10-wash"))["benzoyl_peroxide"] == 1


def test_new_user_only_gets_the_gentlest_rung():
    profile = UserProfile(user_id="u")
    assert tolerance.fits(_p("to-granactive-2"), profile)[0]
    ok, why, _ = tolerance.fits(_p("to-retinol-1"), profile)
    assert not ok and "haven't used a retinoid" in why


def test_quiz_burn_caps_the_ladder_below_the_burning_rung():
    profile = tolerance.apply_quiz(UserProfile(user_id="u"), burned=[_p("to-retinol-1")], worked=[_p("to-retinol-05")])
    level = profile.tolerance["retinoid"]
    assert level.cap == 3 and level.proven == 2
    # 0.5% proven, 1% burned -> nothing at rung 3+, even though proven+1 == 3.
    assert tolerance.allowed_rung(profile, "retinoid") == 2
    assert not tolerance.fits(_p("de-a-passioni"), profile)[0]  # 1% retinol, the hyped one
    assert tolerance.fits(_p("gg-a-game-5"), profile)[0]  # 0.05% retinal, rung 2


def test_known_sensitizer_is_a_hard_fail():
    profile = UserProfile(user_id="u", sensitizers=["fragrance"])
    ok, why, _ = tolerance.fits(_p("la-mer-creme"), profile)
    assert not ok and "fragrance" in why


def test_redness_checkin_steps_down_and_caps():
    profile = UserProfile(user_id="u", tolerance={"retinoid": ToleranceLevel(proven=1)})
    updated, msg = tolerance.apply_checkin(profile, _p("to-retinol-05"), "redness", None, False)
    assert updated.tolerance["retinoid"].cap == 2
    assert updated.tolerance["retinoid"].proven == 1
    assert "Nothing at" in msg


def test_four_weeks_fine_proves_the_rung():
    now = datetime.datetime(2026, 10, 31)
    profile = UserProfile(user_id="u")
    started = now - datetime.timedelta(days=30)
    updated, msg = tolerance.apply_checkin(profile, _p("to-granactive-2"), "fine", started, False, now=now)
    assert updated.tolerance["retinoid"].proven == 0
    assert tolerance.allowed_rung(updated, "retinoid") == 1


def test_fine_too_early_does_not_unlock():
    now = datetime.datetime(2026, 10, 31)
    profile = UserProfile(user_id="u")
    updated, msg = tolerance.apply_checkin(profile, _p("to-granactive-2"), "fine", now - datetime.timedelta(days=5), False, now=now)
    assert "retinoid" not in updated.tolerance
    assert "23 more days" in msg


def test_scan_flags_recent_active_when_redness_worsens():
    now = datetime.datetime(2026, 10, 31)
    usage = [
        (_p("to-retinol-02"), now - datetime.timedelta(days=10)),
        (_p("cerave-moisturizing-cream"), now - datetime.timedelta(days=10)),  # no actives
        (_p("to-niacinamide-10"), now - datetime.timedelta(days=90)),  # too long ago
    ]
    worse = {"redness": {"direction": "worsened", "change": -0.12}}
    assert [p.id for p in tolerance.scan_reaction_suspects(worse, usage, now)] == ["to-retinol-02"]
    same = {"redness": {"direction": "about_the_same", "change": -0.02}}
    assert tolerance.scan_reaction_suspects(same, usage, now) == []
