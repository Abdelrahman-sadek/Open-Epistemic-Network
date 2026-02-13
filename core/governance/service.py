from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from .models import GovernanceParams, GovernanceState, Proposal, ProposalCreateRequest


class GovernanceService:
    """
    Minimal in-memory governance module.

    Phase 4 will attach this to validation results for proposal voting and
    record all changes in the ledger.
    """

    def __init__(self, initial_params: Optional[GovernanceParams] = None) -> None:
        self._state = GovernanceState(
            active_params=initial_params or GovernanceParams(),
            proposals={},
        )

    def get_params(self) -> GovernanceParams:
        return self._state.active_params

    def create_proposal(self, req: ProposalCreateRequest) -> Proposal:
        now = datetime.now(timezone.utc)
        activation_time = now + timedelta(hours=req.activation_delay_hours)
        proposal = Proposal(
            id=uuid.uuid4(),
            title=req.title,
            body=req.body,
            parameters_diff=req.parameters_diff,
            created_at=now,
            activation_time=activation_time,
            enacted=False,
        )
        self._state.proposals[proposal.id] = proposal
        return proposal

    def list_proposals(self) -> Dict[uuid.UUID, Proposal]:
        return dict(self._state.proposals)

    def maybe_enact_proposals(self, now: Optional[datetime] = None) -> None:
        """
        Enact proposals whose activation time has passed.
        In a full implementation, this would be guarded by governance voting.
        """
        now = now or datetime.now(timezone.utc)
        params = self._state.active_params.model_copy()
        changed = False
        for proposal in self._state.proposals.values():
            if proposal.enacted or proposal.activation_time > now:
                continue
            for key, value in proposal.parameters_diff.items():
                if hasattr(params, key):
                    setattr(params, key, value)
                    changed = True
            proposal.enacted = True
        if changed:
            params.version += 1
            self._state.active_params = params

