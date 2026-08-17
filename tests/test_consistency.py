from llm.grounding import check_consistency


def test_exfoliant_at_significant_dryness_is_a_violation():
    result = check_consistency(["high_pct_exfoliant"], {"moisture": "significant"})
    assert not result.consistent
    assert "high_pct_exfoliant" in result.violating_categories


def test_hydrating_at_significant_dryness_is_consistent():
    result = check_consistency(["hydrating", "barrier_repair"], {"moisture": "significant"})
    assert result.consistent
    assert result.violations == []


def test_clear_band_has_no_avoid_list_so_nothing_violates():
    result = check_consistency(["high_pct_exfoliant"], {"moisture": "clear"})
    assert result.consistent
