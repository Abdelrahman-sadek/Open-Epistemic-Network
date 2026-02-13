from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from .models import ReputationState, ReputationUpdateRequest


class ReputationEngine:
    """
    Simple reputation engine with decay and minority boosts.
    """

    def __init__(
        self,
        *,
        decay_rate_per_day: float = 0.001,
        correct_reward: float = 0.05,
        incorrect_penalty: float = 0.1,
        minority_boost_multiplier: float = 2.0,
        min_score: float = 1.0,
        max_score: float = 1e6,
    ) -> None:
        self._states: Dict[uuid.UUID, ReputationState] = {}
        self.decay_rate_per_day = decay_rate_per_day
        self.correct_reward = correct_reward
        self.incorrect_penalty = incorrect_penalty
        self.min_score = min_score
        self.max_score = max_score
        self.minority_boost_multiplier = minority_boost_multiplier

    def get_state(self, validator_id: uuid.UUID) -> ReputationState:
        state = self._states.get(validator_id)
        if state is None:
            state = ReputationState.new(validator_id)
            self._states[validator_id] = state
        return state

    def _apply_decay(self, state: ReputationState, now: Optional[datetime] = None) -> ReputationState:
        now = now or datetime.now(timezone.utc)
        elapsed_days = (now - state.last_updated).total_seconds() / 86400.0
        if elapsed_days <= 0:
            return state
        # Exponential decay toward min_score.
        decay_factor = math.exp(-self.decay_rate_per_day * elapsed_days)
        state.score = max(self.min_score, self.min_score + (state.score - self.min_score) * decay_factor)
        state.last_updated = now
        return state

    def apply_outcome(self, req: ReputationUpdateRequest, now: Optional[datetime] = None) -> ReputationState:
        state = self.get_state(req.validator_id)
        state = self._apply_decay(state, now)

        if req.was_correct:
            delta = self.correct_reward
            if req.was_minority:
                delta *= self.minority_boost_multiplier
            new_score = min(self.max_score, state.score * (1.0 + delta))
        else:
            new_score = max(self.min_score, state.score * (1.0 - self.incorrect_penalty))

        state.score = new_score
        state.last_updated = now or datetime.now(timezone.utc)
        return state

