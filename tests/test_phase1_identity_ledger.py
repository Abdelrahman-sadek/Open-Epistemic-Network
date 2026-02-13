import uuid

from fastapi.testclient import TestClient

from api.main import create_app


def get_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_register_validator_and_retrieve():
    client = get_client()

    payload = {
        "public_key": "test-pubkey",
        "model_family": "test-model",
        "region": "eu",
        "domain_focus": "test-domain",
    }
    resp = client.post("/validators", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["public_key"] == payload["public_key"]
    validator_id = data["id"]

    get_resp = client.get(f"/validators/{validator_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == validator_id


def test_create_claim_and_ledger_root_updates():
    client = get_client()

    # First register a validator as proposer
    v_resp = client.post(
        "/validators",
        json={
            "public_key": "test-pubkey-2",
            "model_family": "test-model",
            "region": "us",
        },
    )
    assert v_resp.status_code == 200
    proposer_id = v_resp.json()["id"]

    # Initially, ledger has no root
    root_resp = client.get("/ledger/root")
    assert root_resp.status_code == 200
    root_data = root_resp.json()
    assert root_data["entry_count"] in (0, 1)  # health check may or may not touch ledger

    # Create a claim
    claim_payload = {
        "statement": "Snow is white",
        "domain": "physics",
        "proposer_id": proposer_id,
        "evidence_refs": ["http://example.com/evidence"],
    }
    c_resp = client.post("/claims", json=claim_payload)
    assert c_resp.status_code == 200
    claim = c_resp.json()
    assert claim["statement"] == "Snow is white"
    claim_id = claim["id"]

    # Fetch claim
    get_resp = client.get(f"/claims/{claim_id}")
    assert get_resp.status_code == 200
    got = get_resp.json()
    assert got["id"] == claim_id
    assert got["version"] == 1
    assert got["validation_status"] == "pending"

    # Ledger root should now be non-empty
    root_resp2 = client.get("/ledger/root")
    assert root_resp2.status_code == 200
    root_data2 = root_resp2.json()
    assert root_data2["entry_count"] >= 1
    assert isinstance(root_data2["root_hash"], str)
    assert len(root_data2["root_hash"]) > 0

