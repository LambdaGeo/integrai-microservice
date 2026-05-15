def test_fhir_metadata_exposes_only_practitioner(client, auth_headers):
    response = client.get("/fhir/metadata", headers=auth_headers)

    assert response.status_code == 200
    resources = response.json()["rest"][0]["resource"]
    assert [resource["type"] for resource in resources] == ["Practitioner"]


def test_fhir_patient_is_not_exposed_by_users_service(client, auth_headers):
    response = client.get("/fhir/Patient", headers=auth_headers)

    assert response.status_code == 404


def test_search_practitioners_returns_agent_profile(client, active_user_profile, auth_headers):
    response = client.get("/fhir/Practitioner", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["resourceType"] == "Bundle"
    assert payload["total"] == 1
    assert payload["entry"][0]["resource"]["resourceType"] == "Practitioner"
    assert payload["entry"][0]["resource"]["name"][0]["text"] == active_user_profile.nome
