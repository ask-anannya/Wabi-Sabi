from services import scan_store


def test_delete_scan_removes_it_and_returns_true():
    saved = scan_store.save_scan(
        user_id="delete-test-user",
        metrics=[{"name": "moisture", "normalised": 0.5}],
        trust_score=0.7,
        advice=[{"metric": "moisture", "text": "stay hydrated"}],
    )
    assert scan_store.delete_scan(saved.id, "delete-test-user") is True
    remaining = scan_store.get_scan_history("delete-test-user")
    assert all(r.id != saved.id for r in remaining)


def test_delete_scan_scoped_to_owner():
    saved = scan_store.save_scan(
        user_id="owner-user",
        metrics=[{"name": "moisture", "normalised": 0.5}],
        trust_score=0.7,
        advice=[],
    )
    # Wrong user_id must not be able to delete someone else's scan.
    assert scan_store.delete_scan(saved.id, "different-user") is False
    assert scan_store.delete_scan(saved.id, "owner-user") is True


def test_delete_nonexistent_scan_returns_false():
    assert scan_store.delete_scan(999999, "anyone") is False
