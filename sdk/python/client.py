from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


class OpenEpistemicClient:
    """
    Minimal Python SDK for interacting with a regional hub.

    This is a thin wrapper over the HTTP API intended for local bots and tools.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout)

    # ---- Validators ----

    def register_validator(
        self,
        public_key: str,
        model_family: str,
        region: str,
        domain_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "public_key": public_key,
            "model_family": model_family,
            "region": region,
            "domain_focus": domain_focus,
        }
        resp = self._client.post("/validators", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ---- Claims ----

    def submit_claim(
        self,
        statement: str,
        domain: str,
        proposer_id: str,
        evidence_refs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "statement": statement,
            "domain": domain,
            "proposer_id": proposer_id,
            "evidence_refs": evidence_refs or [],
        }
        resp = self._client.post("/claims", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_claim(self, claim_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"/claims/{claim_id}")
        resp.raise_for_status()
        return resp.json()

    # ---- Votes & consensus ----

    def submit_vote(
        self,
        claim_id: str,
        validator_id: str,
        vote_type: str,
        confidence: float,
        signature: str,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        ts = timestamp or datetime.now(timezone.utc)
        payload = {
            "claim_id": claim_id,
            "validator_id": validator_id,
            "vote_type": vote_type,
            "confidence": confidence,
            "timestamp": ts.isoformat(),
            "signature": signature,
        }
        resp = self._client.post("/votes", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_votes_for_claim(self, claim_id: str) -> List[Dict[str, Any]]:
        resp = self._client.get(f"/claims/{claim_id}/votes")
        resp.raise_for_status()
        return resp.json()

    def get_consensus_for_claim(self, claim_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"/validation/claims/{claim_id}/consensus")
        resp.raise_for_status()
        return resp.json()

    # ---- Governance ----

    def get_governance_params(self) -> Dict[str, Any]:
        resp = self._client.get("/governance/params")
        resp.raise_for_status()
        return resp.json()

    def create_governance_proposal(
        self,
        title: str,
        body: str,
        parameters_diff: Optional[Dict[str, float]] = None,
        activation_delay_hours: int = 24,
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "body": body,
            "parameters_diff": parameters_diff or {},
            "activation_delay_hours": activation_delay_hours,
        }
        resp = self._client.post("/governance/proposals", json=payload)
        resp.raise_for_status()
        return resp.json()

