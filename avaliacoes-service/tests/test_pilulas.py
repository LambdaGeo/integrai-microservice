from app.models import Avaliacao, Pilula


def test_list_pilulas(client, db_session):
    avaliacao = Avaliacao(gestante=1)
    db_session.add(avaliacao)
    db_session.commit()
    db_session.refresh(avaliacao)

    db_session.add(Pilula(avaliacao_id=avaliacao.id, titulo="Alimentacao", semana_num=1))
    db_session.commit()

    response = client.get("/api/pilulas/", params={"avaliacao": avaliacao.id})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["titulo"] == "Alimentacao"
    assert payload[0]["avaliacao"] == avaliacao.id


def test_marcar_pilula_enviada(client, db_session):
    avaliacao = Avaliacao(gestante=1)
    db_session.add(avaliacao)
    db_session.commit()
    db_session.refresh(avaliacao)

    pilula = Pilula(avaliacao_id=avaliacao.id, titulo="Hidratacao", status="pendente")
    db_session.add(pilula)
    db_session.commit()
    db_session.refresh(pilula)

    response = client.post(f"/api/pilulas/{pilula.id}/marcar_enviada/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "enviada"
    assert payload["data_envio"] is not None
