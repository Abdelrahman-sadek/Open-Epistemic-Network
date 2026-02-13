"""
Minimal local bot example for the Open Epistemic Network.

This script shows how a bot would:
- generate an Ed25519 keypair (if nacl is available)
- register as a validator
- submit a claim
- submit a signed vote for that claim
"""

from __future__ import annotations

import binascii
from datetime import datetime, timezone

import httpx

API_BASE = "http://localhost:8000"

try:
    from nacl.signing import SigningKey  # type: ignore[import]
except Exception:  # pragma: no cover - optional
    SigningKey = None  # type: ignore[assignment]


def generate_keypair() -> tuple[str, str]:
    """
    Return (public_key_hex, private_key_hex).
    """
    if SigningKey is None:
        # Fallback dummy keys; server will accept but cannot verify.
        return "deadbeef", "deadbeef"
    sk = SigningKey.generate()
    vk = sk.verify_key
    return binascii.hexlify(vk.encode()).decode("ascii"), binascii.hexlify(sk.encode()).decode("ascii")


def sign_vote(private_key_hex: str, message: bytes) -> str:
    if SigningKey is None:
        return "deadbeef"
    sk = SigningKey(binascii.unhexlify(private_key_hex))
    sig = sk.sign(message).signature
    return binascii.hexlify(sig).decode("ascii")


def canonical_vote_message(claim_id: str, validator_id: str, vote_type: str, confidence: float, ts_iso: str) -> bytes:
    payload = "|".join(
        [
            claim_id,
            validator_id,
            vote_type,
            f"{confidence:.6f}",
            ts_iso,
        ]
    )
    return payload.encode("utf-8")


def main() -> None:
    public_key_hex, private_key_hex = generate_keypair()

    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        # 1) Register validator
        v_resp = client.post(
            "/validators",
            json={
                "public_key": public_key_hex,
                "model_family": "example-model",
                "region": "eu",
                "domain_focus": "demo",
            },
        )
        v_resp.raise_for_status()
        validator = v_resp.json()
        validator_id = validator["id"]
        print("Registered validator:", validator_id)

        # 2) Submit claim
        c_resp = client.post(
            "/claims",
            json={
                "statement": "Example claim from local bot",
                "domain": "demo",
                "proposer_id": validator_id,
                "evidence_refs": [],
            },
        )
        c_resp.raise_for_status()
        claim = c_resp.json()
        claim_id = claim["id"]
        print("Submitted claim:", claim_id)

        # 3) Submit a signed vote
        ts_iso = datetime.now(timezone.utc).isoformat()
        vote_type = "approve"
        confidence = 0.8
        msg = canonical_vote_message(claim_id, validator_id, vote_type, confidence, ts_iso)
        signature_hex = sign_vote(private_key_hex, msg)

        v2_resp = client.post(
            "/votes",
            json={
                "claim_id": claim_id,
                "validator_id": validator_id,
                "vote_type": vote_type,
                "confidence": confidence,
                "timestamp": ts_iso,
                "signature": signature_hex,
            },
        )
        v2_resp.raise_for_status()
        vote = v2_resp.json()
        print("Submitted vote; signature_valid:", vote["signature_valid"])

        # 4) List votes for claim
        list_resp = client.get(f"/claims/{claim_id}/votes")
        list_resp.raise_for_status()
        votes = list_resp.json()
        print("Votes for claim:", votes)


if __name__ == "__main__":  # pragma: no cover - manual example
    main()

