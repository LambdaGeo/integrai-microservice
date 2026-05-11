from app.models import Avaliacao


def test_list_avaliacoes_requires_authentication(unauthenticated_client):
    response = unauthenticated_client.get("/api/avaliacoes/")

    assert response.status_code == 401


def test_create_avaliacao(client):
    response = client.post(
        "/api/avaliacoes/",
        json={
            "gestante": 1,
            "idade_gestacional": 18,
            "corrimento_vaginal": True,
            "diabetes_gestacao": False,
            "consumo_alcool": False,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["gestante"] == 1
    assert payload["data_aplicacao"] is not None
    assert payload["idade_gestacional"] == 18
    assert payload["corrimento_vaginal"] is True
    assert payload["status_processamento_llm"] == "PENDING"


def test_list_avaliacoes_only_returns_authorized_gestantes(client, db_session):
    db_session.add(Avaliacao(gestante=1, idade_gestacional=12))
    db_session.add(Avaliacao(gestante=3, idade_gestacional=20))
    db_session.commit()

    response = client.get("/api/avaliacoes/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["gestante"] == 1


def test_create_avaliacao_denies_unauthorized_gestante(client):
    response = client.post("/api/avaliacoes/", json={"gestante": 99})

    assert response.status_code == 403
