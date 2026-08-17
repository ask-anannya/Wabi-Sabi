from llm.grounding import compute_ambiguity
from services.youcam_client import SkinMetric


def _metric(band_distance: float) -> SkinMetric:
    return SkinMetric(name="moisture", raw_score=50, normalised=0.5, band="moderate", band_distance=band_distance)


def test_boundary_reading_is_highly_ambiguous():
    near_boundary = compute_ambiguity([_metric(0.01)])
    band_centre = compute_ambiguity([_metric(0.125)])
    assert near_boundary.ambiguity > band_centre.ambiguity
    assert near_boundary.ambiguity > 0.8
    assert band_centre.ambiguity == 0.0


def test_no_metrics_is_not_ambiguous():
    assert compute_ambiguity([]).ambiguity == 0.0
