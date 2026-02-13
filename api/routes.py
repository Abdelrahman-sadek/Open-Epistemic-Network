from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from core.identity.models import ValidatorRegistrationRequest, ValidatorResponse
from core.identity.service import IdentityService
from core.ledger.models import ClaimCreateRequest, ClaimResponse
from core.ledger.service import LedgerService
from core.validation.models import VoteCreateRequest, VoteResponse
from core.validation.service import VoteService


def get_identity_service() -> IdentityService:
    # Phase 1: use a singleton in-process service.
    # Later, wire this to a proper repository backed by PostgreSQL.
    global _IDENTITY_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _IDENTITY_SERVICE
    except NameError:
        _IDENTITY_SERVICE = IdentityService()
        return _IDENTITY_SERVICE


def get_ledger_service() -> LedgerService:
    global _LEDGER_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _LEDGER_SERVICE
    except NameError:
        _LEDGER_SERVICE = LedgerService()
        return _LEDGER_SERVICE


def get_vote_service() -> VoteService:
    global _VOTE_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _VOTE_SERVICE
    except NameError:
        _VOTE_SERVICE = VoteService()
        return _VOTE_SERVICE


router = APIRouter()


@router.post("/validators", response_model=ValidatorResponse, tags=["identity"])
async def register_validator(
    payload: ValidatorRegistrationRequest,
    identity: IdentityService = Depends(get_identity_service),
) -> ValidatorResponse:
    return identity.register_validator(payload)


@router.get("/validators/{validator_id}", response_model=ValidatorResponse, tags=["identity"])
async def get_validator(
    validator_id: uuid.UUID,
    identity: IdentityService = Depends(get_identity_service),
) -> ValidatorResponse:
    validator = identity.get_validator(str(validator_id))
    if not validator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validator not found")
    return validator


@router.post("/claims", response_model=ClaimResponse, tags=["claims"])
async def create_claim(
    payload: ClaimCreateRequest,
    ledger: LedgerService = Depends(get_ledger_service),
) -> ClaimResponse:
    # Phase 1: skip full signature validation; will be added with identity+crypto wiring.
    return ledger.create_claim(payload)


@router.get("/claims/{claim_id}", response_model=ClaimResponse, tags=["claims"])
async def get_claim(
    claim_id: uuid.UUID,
    ledger: LedgerService = Depends(get_ledger_service),
) -> ClaimResponse:
    claim = ledger.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim


@router.post("/votes", response_model=VoteResponse, tags=["validation"])
async def submit_vote(
    payload: VoteCreateRequest,
    votes: VoteService = Depends(get_vote_service),
    identity: IdentityService = Depends(get_identity_service),
) -> VoteResponse:
    """
    Submit a signed vote from a validator for a given claim.
    """
    return votes.submit_vote(payload, identity)


@router.get("/claims/{claim_id}/votes", response_model=list[VoteResponse], tags=["validation"])
async def list_votes_for_claim(
    claim_id: uuid.UUID,
    votes: VoteService = Depends(get_vote_service),
) -> list[VoteResponse]:
    return votes.list_votes_for_claim(claim_id)


@router.get("/ledger/root", tags=["ledger"])
async def get_ledger_root(ledger: LedgerService = Depends(get_ledger_service)) -> dict:
    latest = ledger.get_latest_root()
    if not latest:
        return {"root_hash": None, "entry_count": 0}
    root_hash, count = latest
    return {"root_hash": root_hash, "entry_count": count}

