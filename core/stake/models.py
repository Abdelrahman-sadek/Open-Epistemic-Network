from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class StakeLockRequest(BaseModel):
    validator_id: uuid.UUID
    amount: float = Field(..., gt=0.0)
    lock_until: datetime


class SlashingEventModel(BaseModel):
    id: uuid.UUID
    validator_id: uuid.UUID
    amount_slashed: float
    reason: str
    created_at: datetime


@dataclass
class SlashingEvent:
    id: uuid.UUID
    validator_id: uuid.UUID
    amount_slashed: float
    reason: str
    created_at: datetime


@dataclass
class StakeState:
    validator_id: uuid.UUID
    total_locked: float
    effective_stake: float
    last_updated: datetime
    slashing_history: List[SlashingEvent]

    @classmethod
    def new(cls, validator_id: uuid.UUID, amount: float) -> "StakeState":
        now = datetime.now(timezone.utc)
        return cls(
            validator_id=validator_id,
            total_locked=amount,
            effective_stake=amount,
            last_updated=now,
            slashing_history=[],
        )

