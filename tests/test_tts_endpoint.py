from fastapi.testclient import TestClient


def test_tts_rejects_empty_text():
    import main

    client = TestClient(main.app)
    response = client.post("/tts", json={"text": "   "})
    assert response.status_code == 400


def test_tts_returns_502_when_synthesis_fails(monkeypatch):
    import main
    from routers import tts

    async def _raise(*_args, **_kwargs):
        raise RuntimeError("upstream boom")

    monkeypatch.setattr(tts, "synthesize_speech", _raise)
    client = TestClient(main.app)

    response = client.post("/tts", json={"text": "hello"})

    assert response.status_code == 502


def test_tts_returns_wav_audio_on_success(monkeypatch):
    import main
    from routers import tts

    async def _fake_synthesize(_text, _style=None):
        return b"RIFF....WAVEfmt "

    monkeypatch.setattr(tts, "synthesize_speech", _fake_synthesize)
    client = TestClient(main.app)

    response = client.post("/tts", json={"text": "hello there"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content.startswith(b"RIFF")
