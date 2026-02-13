from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import create_app


def get_client() -> TestClient:
    return TestClient(create_app())


def test_basic_local_bot_flow_without_real_crypto():
    """
    Exercise the main flow a local bot would use:
    - register
    - submit claim
    - submit vote

    This test uses a dummy signature; in environments with Ed25519 keys,
    the LOCAL_BOT.md example shows how to generate real signatures.
    """
    client = get_client()

    # Register validator
    v_resp = client.post(
        "/validators",
        json={
            "public_key": "deadbeef",  # dummy key for this test
            "model_family": "test-model",
            "region": "us",
        },
    )
    assert v_resp.status_code == 200
    validator_id = v_resp.json()["id"]

    # Submit claim
    c_resp = client.post(
        "/claims",
        json={
            "statement": "Rain is wet",
            "domain": "physics",
            "proposer_id": validator_id,
            "evidence_refs": [],
        },
    )
    assert c_resp.status_code == 200
    claim_id = c_resp.json()["id"]

    # Submit vote
    now = datetime.now(timezone.utc).isoformat()
    vote_resp = client.post(
        "/votes",
        json={
            "claim_id": claim_id,
            "validator_id": validator_id,
            "vote_type": "approve",
            "confidence": 0.9,
            "timestamp": now,
            "signature": "cafebabe",  # dummy
        },
    )
    assert vote_resp.status_code == 200
    vote = vote_resp.json()
    assert vote["claim_id"] == claim_id
    assert vote["validator_id"] == validator_id

    # Fetch votes for claim
    list_resp = client.get(f"/claims/{claim_id}/votes")
    assert list_resp.status_code == 200
    votes = list_resp.json()
    assert len(votes) >= 1

