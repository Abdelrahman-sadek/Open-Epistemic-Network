from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class GovernanceParams(BaseModel):
    version: int = 1
    description: str = "Default governance parameters"
    max_influence_weight: float = 1e6
    stake_cap: float = 1e9
    diversity_model_cap: float = 0.6
    diversity_region_cap: float = 0.7
    slashing_confirmation_rounds: int = 2


class ProposalCreateRequest(BaseModel):
    title: str
    body: str
    parameters_diff: Dict[str, float] = Field(
        default_factory=dict, description="Key-value overrides for GovernanceParams numerical fields."
    )
    activation_delay_hours: int = Field(default=24, ge=1)


@dataclass
class Proposal:
    id: uuid.UUID
    title: str
    body: str
    parameters_diff: Dict[str, float]
    created_at: datetime
    activation_time: datetime
    enacted: bool = False


@dataclass
class GovernanceState:
    active_params: GovernanceParams
    proposals: Dict[uuid.UUID, Proposal]

