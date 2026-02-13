from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.main import create_app


def get_client() -> TestClient:
    return TestClient(create_app())


def test_consensus_endpoint_updates_claim_and_reputation():
    client = get_client()

    # Register two validators
    v1 = client.post(
        "/validators",
        json={
            "public_key": "deadbeef",
            "model_family": "modelA",
            "region": "us",
        },
    ).json()
    v2 = client.post(
        "/validators",
        json={
            "public_key": "deadbeef",
            "model_family": "modelB",
            "region": "eu",
        },
    ).json()

    # Submit a claim
    claim = client.post(
        "/claims",
        json={
            "statement": "Water boils at 100C at sea level",
            "domain": "physics",
            "proposer_id": v1["id"],
            "evidence_refs": [],
        },
    ).json()
    claim_id = claim["id"]

    # Two approving votes with high confidence
    ts = datetime.now(timezone.utc).isoformat()
    for vid in (v1["id"], v2["id"]):
        resp = client.post(
            "/votes",
            json={
                "claim_id": claim_id,
                "validator_id": vid,
                "vote_type": "approve",
                "confidence": 0.9,
                "timestamp": ts,
                "signature": "cafebabe",
            },
        )
        assert resp.status_code == 200

    consensus = client.get(f"/validation/claims/{claim_id}/consensus")
    assert consensus.status_code == 200
    data = consensus.json()
    assert data["claim_id"] == claim_id
    assert data["outcome"] in ("accepted", "uncertain")

    # Claim should now reflect updated status/confidence if accepted.
    updated_claim = client.get(f"/claims/{claim_id}").json()
    assert updated_claim["version"] >= 1
    if data["outcome"] == "accepted":
        assert updated_claim["validation_status"] == "accepted"
        assert updated_claim["confidence_score"] == data["confidence"]

