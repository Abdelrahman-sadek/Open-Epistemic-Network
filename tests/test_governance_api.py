from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def get_client() -> TestClient:
    return TestClient(create_app())


def test_governance_params_and_proposal_creation():
    client = get_client()

    resp = client.get("/governance/params")
    assert resp.status_code == 200
    params = resp.json()
    assert "version" in params
    assert params["version"] >= 1

    payload = {
        "title": "Increase stake cap",
        "body": "Raise stake cap to support larger validators.",
        "parameters_diff": {"stake_cap": 2e9},
        "activation_delay_hours": 24,
    }
    pr = client.post("/governance/proposals", json=payload)
    assert pr.status_code == 200
    data = pr.json()
    assert "id" in data
    assert data["title"] == payload["title"]

