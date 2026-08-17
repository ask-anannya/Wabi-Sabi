"""
End-to-end smoke test: the FastAPI app boots (confirms the identifier-bug
fix actually fixed booting) and POST /scan works in YOUCAM_MOCK_MODE without
any real GCP/YouCam credentials, exercising the full analyse_and_advise
pipeline including the grounding checker's LLM call — so the scan LLM and
grounding LLM calls are stubbed here rather than hitting Vertex AI.
"""

import io

from fastapi.testclient import TestClient


def _fake_llm_response(text: str):
    class _Resp:
        pass

    r = _Resp()
    r.text = text
    return r


def test_post_scan_end_to_end_in_mock_mode(monkeypatch):
    import main
    from llm import wabi_sabi_scan_llm
    from llm.grounding import grounding_checker

    scan_json = (
        '{"type":"scan","data":{"reading_summary":"Your skin looks a bit dry with some acne.",'
        '"advice":[{"metric":"moisture","recommend":["hydrating"],"avoid":[],'
        '"text":"Try a fragrance-free moisturiser for the dryness."}],'
        '"progress_note":"","derm_referral":false}}'
    )
    grounding_json = (
        '{"claims":[{"text":"Try a fragrance-free moisturiser for the dryness.","grounded":true,'
        '"supporting_metric":"moisture","note":""}],"grounding_score":0.9,"unsupported_claims":[]}'
    )

    monkeypatch.setattr(
        wabi_sabi_scan_llm.chat_model, "generate_content", lambda _payload: _fake_llm_response(scan_json)
    )
    monkeypatch.setattr(
        grounding_checker.llm.chat_model, "generate_content", lambda _prompt: _fake_llm_response(grounding_json)
    )

    client = TestClient(main.app)
    files = {"image": ("skin.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
    data = {"user_id": "smoke-test-user", "age": "24", "skin_type": "oily", "concerns": "acne"}

    response = client.post("/scan", files=files, data=data)

    assert response.status_code == 200
    body = response.json()
    assert body["spoken_script"]
    assert body["trust"]["band"] in ("confident", "fairly_confident", "uncertain", "see_a_dermatologist")
    assert any(m["name"] == "moisture" for m in body["metrics"])
