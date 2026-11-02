"""
Deeper YouCam usage: the five extra concerns from the same skin-analysis
task, skin_age / all.score, skin-type inference, and texture/dryness-based
reaction detection.
"""

import asyncio
import datetime

from services import catalog, tolerance
from services import youcam_client as yc


def _metric(name, normalised):
    band, dist = yc._band_for(normalised)
    return yc.SkinMetric(name=name, raw_score=100 * (1 - normalised), normalised=normalised, band=band, band_distance=dist)


def test_mock_scan_returns_all_eleven_concerns_and_summary():
    result = asyncio.run(yc.analyse_skin(b"fake", concerns=list(yc.METRIC_CONFIG)))
    names = {m.name for m in result.metrics}
    assert {"oiliness", "radiance", "texture", "firmness", "eye_bag"} <= names
    assert len(names) == 11
    assert result.skin_age == 43
    assert result.overall_score == 81.3


def test_extract_summary_reads_real_score_info_shape():
    score_info = {"pore": {"ui_score": 66}, "all": {"score": 81.33333}, "skin_age": 43, "resize_image": {}}
    assert yc._extract_summary(score_info) == (43, 81.3)
    assert yc._extract_summary({}) == (None, None)


def test_infer_skin_type():
    assert yc.infer_skin_type([_metric("oiliness", 0.7), _metric("moisture", 0.1)]) == "oily"
    assert yc.infer_skin_type([_metric("oiliness", 0.1), _metric("moisture", 0.6)]) == "dry"
    assert yc.infer_skin_type([_metric("oiliness", 0.6), _metric("moisture", 0.6)]) == "combination"
    assert yc.infer_skin_type([_metric("oiliness", 0.1), _metric("moisture", 0.1)]) == "normal"
    assert yc.infer_skin_type([_metric("oiliness", 0.7), _metric("moisture", 0.1), _metric("redness", 0.6)]) == "sensitive"
    assert yc.infer_skin_type([_metric("acne", 0.3)]) is None


def test_worse_texture_after_an_exfoliant_is_flagged_as_peeling():
    now = datetime.datetime(2026, 11, 2)
    usage = [(catalog.get("to-glycolic-7"), now - datetime.timedelta(days=7))]
    deltas = {"texture": {"direction": "worsened", "change": -0.1}}
    assert [p.id for p in tolerance.scan_reaction_suspects(deltas, usage, now)] == ["to-glycolic-7"]
    assert tolerance.scan_severity(tolerance.irritation_readings(deltas)) == "peeling"
    alert = tolerance.reaction_alert(1, catalog.get("to-glycolic-7"), "peeling")
    assert "texture or dryness" in alert.text
