from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ReputationUpdateRequest(BaseModel):
    validator_id: uuid.UUID
    was_correct: bool
    was_minority: bool = Field(
        default=False, description="True if validator supported a minority position that became correct."
    )


@dataclass
class ReputationState:
    validator_id: uuid.UUID
    score: float
    last_updated: datetime

    @classmethod
    def new(cls, validator_id: uuid.UUID, initial_score: float = 1.0) -> "ReputationState":
        return cls(validator_id=validator_id, score=initial_score, last_updated=datetime.now(timezone.utc))

