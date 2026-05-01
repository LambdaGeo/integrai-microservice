def test_list_usuarios_requires_authentication(client):
    response = client.get("/api/v1/usuarios")

    assert response.status_code == 401


def test_list_usuarios_returns_authenticated_users(client, active_user, auth_headers):
    response = client.get("/api/v1/usuarios", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["username"] == active_user.username


def test_create_usuario(client, auth_headers):
    response = client.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "username": "10987654321",
            "email": "nova@example.com",
            "password": "senha12345",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "10987654321"
    assert payload["email"] == "nova@example.com"
    assert "hashed_password" not in payload


def test_get_my_profile(client, active_user_profile, auth_headers):
    response = client.get("/api/v1/usuarios/profile/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["nome"] == "Maria Agente"
    assert payload["user_id"] == active_user_profile.user_id
