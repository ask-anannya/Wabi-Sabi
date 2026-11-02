"""
Onboarding quiz -> matches -> hype check -> usage -> redness check-in, through
the HTTP layer in mock mode.
"""

import uuid

from fastapi.testclient import TestClient


def test_honest_flow_end_to_end():
    import main

    client = TestClient(main.app)
    user = f"honest-flow-{uuid.uuid4()}"

    catalog = client.get("/catalog").json()
    assert len(catalog["products"]) >= 50

    quiz = client.post("/profile/quiz", json={
        "user_id": user, "skin_type": "combination",
        "concerns": ["wrinkle", "acne"], "sensitizers": ["fragrance"],
        "style_prefs": ["budget", "derm"], "burned_product_ids": ["to-retinol-1"], "worked_product_ids": [],
    })
    assert quiz.status_code == 200
    retinoid = next(l for l in quiz.json()["ladders"] if l["family"] == "retinoid")
    assert retinoid["cap"] == 3

    matches = client.get("/matches", params={"user_id": user}).json()
    assert matches["matches"] and all(m["fits_tolerance"] for m in matches["matches"])

    check = client.get("/products/de-a-passioni/honest", params={"user_id": user}).json()["match"]
    assert check["verdict"] == "not_for_you"

    assert client.post("/usage", json={"user_id": user, "product_id": "to-granactive-2"}).status_code == 200
    res = client.post("/checkin", json={"user_id": user, "product_id": "to-granactive-2", "severity": "redness"}).json()
    retinoid = next(l for l in res["ladders"] if l["family"] == "retinoid")
    assert retinoid["cap"] == 0 and retinoid["allowed"] == -1
    assert client.get("/usage", params={"user_id": user}).json()["result"] == []
