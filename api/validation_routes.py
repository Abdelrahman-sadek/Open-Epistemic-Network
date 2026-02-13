from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from core.ledger.service import LedgerService
from core.reputation.service import ReputationEngine
from core.stake.service import StakeManager
from core.identity.service import IdentityService
from core.validation.models import VoteCreateRequest
from core.validation.session import ValidationSessionService
from core.validation.service import VoteService
from core.observability.metrics import record_vote, record_consensus, record_slashing

from .routes import get_vote_service, get_ledger_service


def get_stake_manager() -> StakeManager:
    global _STAKE_MANAGER  # type: ignore[annotation-unchecked]
    try:
        return _STAKE_MANAGER
    except NameError:
        _STAKE_MANAGER = StakeManager()
        return _STAKE_MANAGER


def get_reputation_engine() -> ReputationEngine:
    global _REPUTATION_ENGINE  # type: ignore[annotation-unchecked]
    try:
        return _REPUTATION_ENGINE
    except NameError:
        _REPUTATION_ENGINE = ReputationEngine()
        return _REPUTATION_ENGINE


def get_identity_service() -> IdentityService:
    global _IDENTITY_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _IDENTITY_SERVICE
    except NameError:
        _IDENTITY_SERVICE = IdentityService()
        return _IDENTITY_SERVICE


def get_validation_session_service(
    votes: VoteService = Depends(get_vote_service),
    stake: StakeManager = Depends(get_stake_manager),
    reputation: ReputationEngine = Depends(get_reputation_engine),
    identity: IdentityService = Depends(get_identity_service),
) -> ValidationSessionService:
    global _VALIDATION_SESSION_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _VALIDATION_SESSION_SERVICE
    except NameError:
        _VALIDATION_SESSION_SERVICE = ValidationSessionService(
            votes=votes, 
            stake=stake, 
            reputation=reputation,
            identity=identity
        )
        return _VALIDATION_SESSION_SERVICE


router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/claims/{claim_id}/consensus")
async def get_claim_consensus(
    claim_id: uuid.UUID,
    svc: ValidationSessionService = Depends(get_validation_session_service),
    votes: VoteService = Depends(get_vote_service),
    reputation: ReputationEngine = Depends(get_reputation_engine),
    ledger: LedgerService = Depends(get_ledger_service),
) -> dict:
    session = svc.compute_consensus(claim_id)

    # If we have a strong outcome, apply it to the claim and update reputations.
    if session.outcome in ("accepted", "rejected") and session.confidence > 0.0:
        # Update claim status and confidence in the ledger (append-only via new version).
        ledger.apply_consensus(claim_id, session.outcome, session.confidence)

        # Update validator reputations based on alignment with outcome.
        from core.reputation.models import ReputationUpdateRequest

        vote_list = votes.list_votes_for_claim(claim_id)
        for v in vote_list:
            if not v.signature_valid or v.vote_type == "uncertain":
                continue
            was_correct = (v.vote_type == "approve" and session.outcome == "accepted") or (
                v.vote_type == "reject" and session.outcome == "rejected"
            )
            req = ReputationUpdateRequest(
                validator_id=v.validator_id,
                was_correct=was_correct,
                was_minority=False,  # minority detection will be added later
            )
            reputation.apply_outcome(req)

    return {
        "claim_id": str(session.claim_id),
        "round": session.round,
        "outcome": session.outcome,
        "confidence": session.confidence,
        "created_at": session.created_at.isoformat(),
    }

