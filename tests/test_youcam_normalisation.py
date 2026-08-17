import asyncio

from services import youcam_client as yc


def test_normalise_higher_is_worse(monkeypatch):
    # Every real METRIC_CONFIG entry is higher_is_better (confirmed live) —
    # test the other polarity branch with a synthetic severity-style metric.
    monkeypatch.setitem(yc.METRIC_CONFIG, "severity_score", {"raw_range": (0, 100), "polarity": "higher_is_worse"})
    assert yc._normalise("severity_score", 0) == 0.0
    assert yc._normalise("severity_score", 100) == 1.0
    assert yc._normalise("severity_score", 50) == 0.5


def test_normalise_higher_is_better_polarity_is_inverted():
    # All real metrics (moisture, wrinkle, redness, age_spot, acne, pore)
    # are higher_is_better 0-100 health scores, confirmed against a real
    # completed YouCam task — a high raw score should map to LOW severity.
    assert yc._normalise("moisture", 90) < 0.2
    assert yc._normalise("moisture", 10) > 0.8
    assert yc._normalise("acne", 92) < 0.1


def test_band_for_boundaries():
    assert yc._band_for(0.0)[0] == "clear"
    assert yc._band_for(0.24)[0] == "clear"
    assert yc._band_for(0.26)[0] == "mild"
    assert yc._band_for(0.5)[0] in ("mild", "moderate")
    assert yc._band_for(0.9)[0] == "significant"


def test_analyse_skin_mock_mode_returns_bands_from_fixture():
    result = asyncio.run(yc.analyse_skin(b"fake-bytes", concerns=list(yc.METRIC_CONFIG.keys())))
    by_name = {m.name: m for m in result.metrics}

    # Fixture uses real captured ui_scores: acne=92, wrinkle=83, redness=84,
    # age_spot=92 -> inverted to low severity (clear); moisture=71, pore=66
    # -> inverted to moderate severity (mild).
    assert by_name["acne"].band == "clear"
    assert by_name["wrinkle"].band == "clear"
    assert by_name["moisture"].band == "mild"
    assert result.file_id == "mock-file-id"
