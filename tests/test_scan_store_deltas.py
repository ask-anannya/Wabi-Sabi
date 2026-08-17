from services import scan_store


def test_sub_threshold_delta_reads_as_about_the_same():
    previous = [{"name": "dryness", "normalised": 0.50}]
    current = [{"name": "dryness", "normalised": 0.53}]  # 0.03 change, below SIGNIFICANCE_THRESHOLD
    deltas = scan_store.compute_deltas(previous, current)
    assert deltas["dryness"]["direction"] == "about_the_same"


def test_above_threshold_improvement_is_reported():
    previous = [{"name": "dryness", "normalised": 0.70}]
    current = [{"name": "dryness", "normalised": 0.40}]
    deltas = scan_store.compute_deltas(previous, current)
    assert deltas["dryness"]["direction"] == "improved"


def test_above_threshold_worsening_is_reported():
    previous = [{"name": "dryness", "normalised": 0.20}]
    current = [{"name": "dryness", "normalised": 0.50}]
    deltas = scan_store.compute_deltas(previous, current)
    assert deltas["dryness"]["direction"] == "worsened"


def test_save_and_get_last_scan_round_trips():
    scan_store.save_scan(
        user_id="test-user-1",
        metrics=[{"name": "dryness", "normalised": 0.5}],
        trust_score=0.8,
        advice=[{"metric": "dryness", "text": "stay hydrated"}],
    )
    last = scan_store.get_last_scan("test-user-1")
    assert last is not None
    assert last.trust_score == 0.8
