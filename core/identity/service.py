from __future__ import annotations

from typing import Dict

from .models import ValidatorIdentity, ValidatorRegistrationRequest, ValidatorResponse


class IdentityService:
    """
    Minimal in-memory identity registry for Phase 1.

    Later phases should replace this with a proper persistence layer (PostgreSQL),
    but the API surface should remain largely stable.
    """

    def __init__(self) -> None:
        self._validators: Dict[str, ValidatorIdentity] = {}

    def register_validator(self, req: ValidatorRegistrationRequest) -> ValidatorResponse:
        identity = ValidatorIdentity.new(
            public_key=req.public_key,
            model_family=req.model_family,
            region=req.region,
            domain_focus=req.domain_focus,
        )
        self._validators[str(identity.id)] = identity
        return ValidatorResponse(**identity.to_dict())

    def get_validator(self, validator_id: str) -> ValidatorResponse | None:
        identity = self._validators.get(validator_id)
        if not identity:
            return None
        return ValidatorResponse(**identity.to_dict())

    def get_public_key(self, validator_id: str) -> str | None:
        """
        Return the raw public key string for a validator, if known.
        """
        identity = self._validators.get(validator_id)
        if not identity:
            return None
        return identity.public_key


