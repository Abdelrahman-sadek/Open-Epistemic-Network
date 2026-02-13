from __future__ import annotations

from fastapi import APIRouter, Depends

from core.governance.models import GovernanceParams, ProposalCreateRequest
from core.governance.service import GovernanceService


def get_governance_service() -> GovernanceService:
    global _GOVERNANCE_SERVICE  # type: ignore[annotation-unchecked]
    try:
        return _GOVERNANCE_SERVICE
    except NameError:
        _GOVERNANCE_SERVICE = GovernanceService()
        return _GOVERNANCE_SERVICE


router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/params", response_model=GovernanceParams)
async def get_params(svc: GovernanceService = Depends(get_governance_service)) -> GovernanceParams:
    return svc.get_params()


@router.post("/proposals")
async def create_proposal(
    payload: ProposalCreateRequest,
    svc: GovernanceService = Depends(get_governance_service),
) -> dict:
    proposal = svc.create_proposal(payload)
    return {
        "id": str(proposal.id),
        "title": proposal.title,
        "activation_time": proposal.activation_time.isoformat(),
    }

