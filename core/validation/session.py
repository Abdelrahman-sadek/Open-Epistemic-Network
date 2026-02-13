from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from core.reputation.service import ReputationEngine
from core.stake.service import StakeManager
from core.identity.service import IdentityService

from .influence import ValidatorInfluenceContext, compute_influence_weight
from .diversity import diversity_sampler
from .models import Vote
from .service import VoteService


ConsensusOutcome = Literal["accepted", "rejected", "uncertain"]


@dataclass
class ValidationSession:
    claim_id: uuid.UUID
    created_at: datetime
    round: int
    outcome: Optional[ConsensusOutcome] = None
    confidence: float = 0.0
    validators_sampled: List[str] = None


class ValidationSessionService:
    """
    In-memory validation session and influence-weighted consensus.

    This implementation includes:
    - Multi-round validator sampling
    - Diversity-aware validator selection
    - Influence-weighted consensus calculation
    - Automatic reputation and stake updates
    """

    def __init__(
        self,
        votes: VoteService,
        stake: StakeManager,
        reputation: ReputationEngine,
        identity: IdentityService,
        max_rounds: int = 3,
        confidence_threshold: float = 0.6,
        sample_size: int = 20,
    ) -> None:
        self._votes = votes
        self._stake = stake
        self._reputation = reputation
        self._identity = identity
        self._max_rounds = max_rounds
        self._confidence_threshold = confidence_threshold
        self._sample_size = sample_size
        self._sessions: Dict[uuid.UUID, ValidationSession] = {}

    def _get_or_create_session(self, claim_id: uuid.UUID) -> ValidationSession:
        if claim_id not in self._sessions:
            self._sessions[claim_id] = ValidationSession(
                claim_id=claim_id,
                created_at=datetime.now(timezone.utc),
                round=1,
                validators_sampled=[],
            )
        return self._sessions[claim_id]

    def compute_consensus(self, claim_id: uuid.UUID) -> ValidationSession:
        """
        Compute multi-round, influence-weighted consensus for a claim.

        Features:
        - Multi-round sampling with up to 3 rounds
        - Diversity-aware validator selection
        - Influence-weighted voting
        - Automatic reputation and stake updates
        """
        session = self._get_or_create_session(claim_id)
        
        # Run multi-round consensus
        while session.round <= self._max_rounds:
            # Sample validators for this round
            validators = self._sample_validators(session)
            session.validators_sampled.extend(validators)
            
            # Get votes for this claim
            votes = self._votes.list_votes_for_claim(claim_id)
            
            # Compute influence-weighted consensus
            outcome, confidence = self._compute_round_consensus(votes)
            
            # Check if we have sufficient confidence
            if confidence >= self._confidence_threshold:
                session.outcome = outcome
                session.confidence = confidence
                self._apply_outcome_updates(claim_id, outcome, votes)
                return session
            
            # Move to next round
            session.round += 1
        
        # If we didn't reach sufficient confidence after all rounds
        session.outcome = "uncertain"
        session.confidence = 0.5
        return session

    def _sample_validators(self, session: ValidationSession) -> List[str]:
        """
        Sample validators with diversity constraints.
        """
        all_validators = self._identity.list_validators()
        
        # Exclude already sampled validators
        available_validators = [
            v for v in all_validators 
            if str(v.id) not in session.validators_sampled
        ]
        
        # Apply diversity sampling
        sampled_validators = diversity_sampler(
            available_validators,
            self._sample_size,
            max_model_family_fraction=0.3,
            max_region_fraction=0.4
        )
        
        return [str(v.id) for v in sampled_validators]

    def _compute_round_consensus(self, votes: List[Vote]) -> tuple[ConsensusOutcome, float]:
        """
        Compute influence-weighted consensus for current votes.
        """
        approve_weight = 0.0
        reject_weight = 0.0
        uncertain_weight = 0.0

        now = datetime.now(timezone.utc)
        for v in votes:
            if not v.signature_valid:
                continue

            iw = self._influence_for_vote(v, now)
            if v.vote_type == "approve":
                approve_weight += iw * v.confidence
            elif v.vote_type == "reject":
                reject_weight += iw * v.confidence
            else:
                uncertain_weight += iw * v.confidence

        total = approve_weight + reject_weight + uncertain_weight
        if total <= 0:
            return "uncertain", 0.0

        approve_frac = approve_weight / total
        reject_frac = reject_weight / total

        if approve_frac >= self._confidence_threshold:
            return "accepted", approve_frac
        elif reject_frac >= self._confidence_threshold:
            return "rejected", reject_frac
        else:
            return "uncertain", max(approve_frac, reject_frac)

    def _apply_outcome_updates(self, claim_id: uuid.UUID, outcome: ConsensusOutcome, votes: List[Vote]):
        """
        Apply automatic reputation and stake updates based on consensus outcome.
        """
        from core.reputation.models import ReputationUpdateRequest
        from core.stake.models import StakeUpdateRequest
        from core.observability.metrics import record_consensus, record_slashing, update_validator_metrics

        # First, determine which votes were correct
        correct_votes = []
        incorrect_votes = []
        
        for v in votes:
            if not v.signature_valid or v.vote_type == "uncertain":
                continue
                
            is_correct = (v.vote_type == "approve" and outcome == "accepted") or \
                       (v.vote_type == "reject" and outcome == "rejected")
            
            if is_correct:
                correct_votes.append(v)
            else:
                incorrect_votes.append(v)
        
        # Apply reputation updates
        for v in correct_votes:
            req = ReputationUpdateRequest(
                validator_id=v.validator_id,
                was_correct=True,
                was_minority=self._is_minority_vote(v, votes, outcome)
            )
            self._reputation.apply_outcome(req)
            
        for v in incorrect_votes:
            req = ReputationUpdateRequest(
                validator_id=v.validator_id,
                was_correct=False,
                was_minority=False
            )
            self._reputation.apply_outcome(req)
        
        # Apply stake updates (for slashing)
        for v in incorrect_votes:
            # Slash stake for incorrect votes
            req = StakeUpdateRequest(
                validator_id=v.validator_id,
                amount=-0.1  # Slash 10% of stake for incorrect votes
            )
            self._stake.apply_update(req)
            
            # Record slashing event
            record_slashing(
                validator_id=str(v.validator_id),
                amount=0.1,
                reason="incorrect_vote"
            )
        
        # Update validator metrics after outcome
        for v in votes:
            if not v.signature_valid:
                continue
                
            # Get current validator state
            stake_state = self._stake.get_state(v.validator_id)
            rep_state = self._reputation.get_state(v.validator_id)
            
            # Calculate current influence
            from core.validation.influence import ValidatorInfluenceContext, compute_influence_weight
            from datetime import datetime, timezone
            
            now = datetime.now(timezone.utc)
            time_active_days = (now - rep_state.last_updated).total_seconds() / 86400.0
            
            validator = self._identity.get_validator(str(v.validator_id))
            diversity_modifier = self._compute_diversity_modifier(validator)
            
            ctx = ValidatorInfluenceContext(
                stake_locked=stake_state.effective_stake,
                reputation_score=rep_state.score,
                diversity_modifier=diversity_modifier,
                time_active_days=time_active_days
            )
            
            influence = compute_influence_weight(ctx)
            
            # Update metrics
            update_validator_metrics(
                validator_id=str(v.validator_id),
                influence=influence,
                stake=stake_state.effective_stake,
                reputation=rep_state.score
            )

    def _is_minority_vote(self, vote: Vote, all_votes: List[Vote], outcome: ConsensusOutcome) -> bool:
        """
        Determine if a vote was a minority correct vote.
        """
        if not (vote.vote_type == "approve" and outcome == "accepted" or 
                vote.vote_type == "reject" and outcome == "rejected"):
            return False
            
        # Count votes
        approve_count = sum(1 for v in all_votes if v.vote_type == "approve" and v.signature_valid)
        reject_count = sum(1 for v in all_votes if v.vote_type == "reject" and v.signature_valid)
        
        # Determine if vote type was minority
        if outcome == "accepted":
            return reject_count < approve_count and vote.vote_type == "reject"
        else:
            return approve_count < reject_count and vote.vote_type == "approve"

    def _influence_for_vote(self, v: Vote, now: datetime) -> float:
        # Stake
        stake_state = self._stake.get_state(v.validator_id)
        stake_locked = stake_state.effective_stake if stake_state else 1.0

        # Reputation
        rep_state = self._reputation.get_state(v.validator_id)
        reputation_score = rep_state.score

        # Time active: approximate as days since we first saw the validator.
        time_active_days = (now - rep_state.last_updated).total_seconds() / 86400.0

        # Diversity modifier
        validator = self._identity.get_validator(str(v.validator_id))
        diversity_modifier = self._compute_diversity_modifier(validator)

        ctx = ValidatorInfluenceContext(
            stake_locked=stake_locked,
            reputation_score=reputation_score,
            diversity_modifier=diversity_modifier,
            time_active_days=max(0.0, time_active_days),
        )
        return compute_influence_weight(ctx)

    def _compute_diversity_modifier(self, validator) -> float:
        """
        Compute diversity modifier based on validator's model family and region.
        """
        if not validator:
            return 1.0
            
        # For now, use a simple diversity modifier based on model family and region
        # In production, this should use Neo4j correlation data
        return 0.8 + (hash(validator.model_family + validator.region) % 40) / 100.0

