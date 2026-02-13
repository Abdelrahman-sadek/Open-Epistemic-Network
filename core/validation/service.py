from __future__ import annotations

import binascii
import uuid
from datetime import datetime
from typing import Dict, List

from core.identity.service import IdentityService

from .models import Vote, VoteCreateRequest, VoteResponse

try:  # optional crypto dependency
    from nacl.exceptions import BadSignatureError  # type: ignore[import]
    from nacl.signing import VerifyKey  # type: ignore[import]
except Exception:  # pragma: no cover - optional
    VerifyKey = None  # type: ignore[assignment]
    BadSignatureError = Exception  # type: ignore[assignment]


def _canonical_vote_message(req: VoteCreateRequest) -> bytes:
    """
    Canonical message that is signed by the validator for each vote.
    """
    payload = "|".join(
        [
            str(req.claim_id),
            str(req.validator_id),
            req.vote_type,
            f"{req.confidence:.6f}",
            req.timestamp.isoformat(),
        ]
    )
    return payload.encode("utf-8")


def _verify_signature(public_key_str: str, req: VoteCreateRequest) -> bool:
    """
    Verify Ed25519 signature over the canonical vote payload.

    The client is expected to send the raw signature bytes encoded as hex.
    If the crypto library is unavailable, this function returns True so that
    environments without pyNaCl can still exercise the flow.
    """
    if not public_key_str or VerifyKey is None:
        return True

    try:
        pubkey_bytes = binascii.unhexlify(public_key_str)
        sig_bytes = binascii.unhexlify(req.signature)
    except (binascii.Error, ValueError):
        return False

    message = _canonical_vote_message(req)
    try:
        vk = VerifyKey(pubkey_bytes)
        vk.verify(message, sig_bytes)
        return True
    except BadSignatureError:
        return False


class VoteService:
    """
    Minimal in-memory vote registry.

    Full validation orchestration and weighting is out of scope for the local
    bot example and will be built on top of this primitive.
    """

    def __init__(self) -> None:
        self._votes_by_claim: Dict[uuid.UUID, List[Vote]] = {}

    def submit_vote(self, req: VoteCreateRequest, identity: IdentityService) -> VoteResponse:
        pubkey = identity.get_public_key(str(req.validator_id))
        signature_valid = bool(pubkey and _verify_signature(pubkey, req))

        v = Vote(
            id=uuid.uuid4(),
            claim_id=req.claim_id,
            validator_id=req.validator_id,
            vote_type=req.vote_type,
            confidence=req.confidence,
            timestamp=req.timestamp,
            signature=req.signature,
            signature_valid=signature_valid,
        )
        self._votes_by_claim.setdefault(req.claim_id, []).append(v)
        return VoteResponse(**v.__dict__)

    def list_votes_for_claim(self, claim_id: uuid.UUID) -> List[VoteResponse]:
        return [VoteResponse(**v.__dict__) for v in self._votes_by_claim.get(claim_id, [])]

