"""Confirms POST /llm/chat still works — the scan rewrite must not break it."""

from fastapi.testclient import TestClient


def _fake_llm_response(text: str):
    class _Resp:
        pass

    r = _Resp()
    r.text = text
    return r


def test_chat_endpoint_still_works(monkeypatch):
    import main
    from llm import wabi_sabi_llm

    chat_json = '{"type":"chat","data":{"response":"Hi! What is your skin type?"}}'
    monkeypatch.setattr(
        wabi_sabi_llm.chat_model, "generate_content", lambda _payload: _fake_llm_response(chat_json)
    )

    client = TestClient(main.app)
    response = client.post("/llm/chat", json={"messages": [{"role": "human", "content": "hi"}]})

    assert response.status_code == 200
    assert response.json()["result"] == "Hi! What is your skin type?"
