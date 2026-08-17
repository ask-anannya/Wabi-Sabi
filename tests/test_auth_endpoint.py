from fastapi.testclient import TestClient


def test_google_sign_in_without_client_id_returns_503(monkeypatch):
    import main
    from routers import auth

    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", None)
    client = TestClient(main.app)

    response = client.post("/auth/google", json={"credential": "fake-token"})

    assert response.status_code == 503


def test_google_sign_in_rejects_invalid_token(monkeypatch):
    import main
    from routers import auth

    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "test-client-id")

    def _raise(*_args, **_kwargs):
        raise ValueError("bad token")

    monkeypatch.setattr(auth.id_token, "verify_oauth2_token", _raise)
    client = TestClient(main.app)

    response = client.post("/auth/google", json={"credential": "not-a-real-token"})

    assert response.status_code == 401


def test_google_sign_in_upserts_user_on_valid_token(monkeypatch):
    import main
    from routers import auth

    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(
        auth.id_token,
        "verify_oauth2_token",
        lambda *_a, **_k: {"sub": "google-user-1", "email": "a@b.com", "name": "A B", "picture": "http://pic"},
    )
    client = TestClient(main.app)

    response = client.post("/auth/google", json={"credential": "real-looking-token"})

    assert response.status_code == 200
    body = response.json()["result"]
    assert body["user_id"] == "google-user-1"
    assert body["email"] == "a@b.com"
