from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VoteType = Literal["approve", "reject", "uncertain"]


class VoteCreateRequest(BaseModel):
    claim_id: uuid.UUID
    validator_id: uuid.UUID
    vote_type: VoteType
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
    signature: str = Field(..., description="Ed25519 signature encoded as hex over the canonical vote payload")


class VoteResponse(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    validator_id: uuid.UUID
    vote_type: VoteType
    confidence: float
    timestamp: datetime
    signature: str
    signature_valid: bool


@dataclass
class Vote:
    id: uuid.UUID
    claim_id: uuid.UUID
    validator_id: uuid.UUID
    vote_type: str
    confidence: float
    timestamp: datetime
    signature: str
    signature_valid: bool

