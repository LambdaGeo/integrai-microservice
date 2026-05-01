def test_login_returns_bearer_token(client, active_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "123.456.789-01", "password": "senha12345"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_login_rejects_invalid_password(client, active_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "12345678901", "password": "errada123"},
    )

    assert response.status_code == 401
