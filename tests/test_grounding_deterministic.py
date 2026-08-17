from llm.grounding import grounding_checker


def test_hormonal_cause_claim_is_caught_and_stripped():
    result = grounding_checker.deterministic_check(
        "This dryness is caused by a hormonal imbalance, so drink more water."
    )
    assert result is not None
    assert result.grounding_score == 0.0
    assert any("hormonal" in claim for claim in result.unsupported_claims)


def test_absolute_language_is_caught():
    result = grounding_checker.deterministic_check("This will guaranteed cure your acne overnight.")
    assert result is not None
    assert result.unsupported_claims


def test_clean_advice_passes_deterministic_pass():
    result = grounding_checker.deterministic_check("Your skin looks a bit dry, try a fragrance-free moisturiser.")
    assert result is None
