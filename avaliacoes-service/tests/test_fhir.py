from app.models import Avaliacao


def test_search_observations_returns_bundle(client, db_session):
    db_session.add(Avaliacao(gestante=1, idade_gestacional=10, corrimento_vaginal=True))
    db_session.commit()

    response = client.get("/fhir/Observation", params={"subject": "Patient/1"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["resourceType"] == "Bundle"
    assert payload["total"] == 1
    observation = payload["entry"][0]["resource"]
    assert observation["resourceType"] == "Observation"
    assert observation["subject"]["reference"] == "Patient/1"


def test_create_observation(client, monkeypatch):
    async def fake_calcular_e_salvar_risco(db, avaliacao, access_token=None):
        avaliacao.resultado_integralidade_saude = {"top_fatores": ["diabetes_gestacao"]}
        db.add(avaliacao)
        db.commit()
        db.refresh(avaliacao)
        return avaliacao.resultado_integralidade_saude

    import app.fhir.router as fhir_router

    monkeypatch.setattr(fhir_router, "calcular_e_salvar_risco", fake_calcular_e_salvar_risco)

    response = client.post(
        "/fhir/Observation",
        json={
            "resourceType": "Observation",
            "subject": {"reference": "Patient/1"},
            "component": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "https://integrai.ufma.br/fhir/CodeSystem/avaliacao-gestacional",
                                "code": "diabetes_gestacao",
                            }
                        ]
                    },
                    "valueBoolean": True,
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["resourceType"] == "Observation"
    assert payload["subject"]["reference"] == "Patient/1"
    assert any(extension["url"].endswith("avaliacao-resultado-integralidade-saude") for extension in payload["extension"])
