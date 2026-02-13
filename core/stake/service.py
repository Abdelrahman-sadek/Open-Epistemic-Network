from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from .models import SlashingEvent, SlashingEventModel, StakeLockRequest, StakeState


class StakeManager:
    """
    In-memory stake manager with simple decay and slashing.

    Phase 2 implementation; backing store will be PostgreSQL later.
    """

    def __init__(
        self,
        *,
        decay_half_life_days: float = 365.0,
        max_stake_cap: float = 1e9,
    ) -> None:
        self._states: Dict[uuid.UUID, StakeState] = {}
        self.decay_half_life_days = decay_half_life_days
        self.max_stake_cap = max_stake_cap

    # ---- Stake locking ----

    def lock_stake(self, req: StakeLockRequest) -> StakeState:
        """
        Lock stake for a validator. Stake is non-transferable; this simply increases locked stake.
        """
        vid = req.validator_id
        state = self._states.get(vid)
        if state is None:
            state = StakeState.new(validator_id=vid, amount=req.amount)
        else:
            state.total_locked = min(state.total_locked + req.amount, self.max_stake_cap)
            state.effective_stake = min(state.effective_stake + req.amount, self.max_stake_cap)
            state.last_updated = datetime.now(timezone.utc)
        self._states[vid] = state
        return state

    def get_state(self, validator_id: uuid.UUID) -> Optional[StakeState]:
        return self._states.get(validator_id)

    # ---- Decay ----

    def apply_decay(self, validator_id: uuid.UUID, now: Optional[datetime] = None) -> Optional[StakeState]:
        """
        Apply time-based decay to effective stake. Total locked remains as an upper bound.
        """
        state = self._states.get(validator_id)
        if state is None:
            return None
        now = now or datetime.now(timezone.utc)
        elapsed_days = (now - state.last_updated).total_seconds() / 86400.0
        if elapsed_days <= 0:
            return state
        # Exponential decay toward a floor of 1.0 (to keep log domain valid).
        half_life = max(self.decay_half_life_days, 1e-3)
        decay_factor = 0.5 ** (elapsed_days / half_life)
        new_effective = max(1.0, state.effective_stake * decay_factor)
        state.effective_stake = new_effective
        state.last_updated = now
        return state

    # ---- Slashing ----

    def slash(
        self,
        validator_id: uuid.UUID,
        fraction: float,
        reason: str,
    ) -> Optional[SlashingEventModel]:
        """
        Slash a fraction of the validator's total_locked and effective_stake.
        """
        if fraction <= 0.0:
            raise ValueError("fraction must be > 0")
        if fraction > 1.0:
            raise ValueError("fraction must be <= 1")

        state = self._states.get(validator_id)
        if state is None:
            return None

        amount = state.total_locked * fraction
        state.total_locked = max(0.0, state.total_locked - amount)
        state.effective_stake = max(1.0, state.effective_stake - amount)
        state.last_updated = datetime.now(timezone.utc)

        ev = SlashingEvent(
            id=uuid.uuid4(),
            validator_id=validator_id,
            amount_slashed=amount,
            reason=reason,
            created_at=state.last_updated,
        )
        state.slashing_history.append(ev)
        return SlashingEventModel(**ev.__dict__)

