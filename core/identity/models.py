from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ValidatorRegistrationRequest(BaseModel):
    public_key: str = Field(..., description="Ed25519 public key, base64 or hex encoded")
    model_family: str = Field(..., description="Model family identifier, e.g. gpt, llama")
    region: str = Field(..., description="Geographic/jurisdictional region code")
    domain_focus: Optional[str] = Field(
        default=None, description="Optional domain specialization (e.g. medicine, economics)"
    )


class ValidatorResponse(BaseModel):
    id: uuid.UUID
    public_key: str
    model_family: str
    region: str
    domain_focus: Optional[str]
    created_at: datetime
    is_active: bool


@dataclass
class ValidatorIdentity:
    id: uuid.UUID
    public_key: str
    model_family: str
    region: str
    domain_focus: Optional[str]
    created_at: datetime
    is_active: bool = True

    @classmethod
    def new(cls, public_key: str, model_family: str, region: str, domain_focus: Optional[str] = None) -> "ValidatorIdentity":
        return cls(
            id=uuid.uuid4(),
            public_key=public_key,
            model_family=model_family,
            region=region,
            domain_focus=domain_focus,
            created_at=datetime.now(timezone.utc),
            is_active=True,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "public_key": self.public_key,
            "model_family": self.model_family,
            "region": self.region,
            "domain_focus": self.domain_focus,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }

