from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class ClaimCreateRequest(BaseModel):
    statement: str
    domain: str
    proposer_id: uuid.UUID
    evidence_refs: List[str] = Field(default_factory=list)


class ClaimResponse(BaseModel):
    id: uuid.UUID
    statement: str
    domain: str
    proposer_id: uuid.UUID
    evidence_refs: List[str]
    version: int
    parent_version: Optional[int]
    created_at: datetime
    confidence_score: float
    validation_status: str


@dataclass
class Claim:
    id: uuid.UUID
    statement: str
    domain: str
    proposer_id: uuid.UUID
    evidence_refs: List[str]
    version: int
    parent_version: Optional[int]
    created_at: datetime
    confidence_score: float
    validation_status: str


@dataclass
class LedgerEntry:
    id: uuid.UUID
    claim_id: uuid.UUID
    version: int
    previous_entry_id: Optional[uuid.UUID]
    payload_hash: str
    created_at: datetime


def hash_claim(claim: Claim) -> str:
    """
    Compute a deterministic SHA256 hash for a claim payload.
    This will later be part of the Merkle tree leaves.
    """
    payload = "|".join(
        [
            str(claim.id),
            claim.statement,
            claim.domain,
            str(claim.proposer_id),
            ",".join(claim.evidence_refs),
            str(claim.version),
            str(claim.parent_version or ""),
            f"{claim.confidence_score:.6f}",
            claim.validation_status,
        ]
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

