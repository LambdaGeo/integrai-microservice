from app.auth import create_access_token, get_password_hash
from app.models.usuario import Usuario


def test_create_audit_log_uses_authenticated_user(client, active_user, auth_headers):
    response = client.post(
        "/api/v1/audit",
        headers=auth_headers,
        json={
            "action": "teste.executado",
            "resource_type": "teste",
            "resource_id": "1",
            "description": "Evento de teste.",
            "detalhes": {"origem": "pytest"},
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["actor_id"] == active_user.id
    assert payload["actor_username"] == active_user.username
    assert payload["action"] == "teste.executado"


def test_list_audit_logs_requires_admin(client, db_session):
    user = Usuario(
        username="10987654321",
        email="normal@example.com",
        hashed_password=get_password_hash("senha12345"),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": user.username})
    response = client.get("/api/v1/audit", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
