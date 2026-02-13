from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from core.reputation.models import ReputationUpdateRequest
from core.reputation.service import ReputationEngine
from core.stake.models import StakeLockRequest
from core.stake.service import StakeManager


def test_reputation_increases_for_correct_and_decreases_for_incorrect():
    engine = ReputationEngine()
    vid = uuid.uuid4()

    # Start with default
    state = engine.get_state(vid)
    base = state.score

    # Correct outcome
    state = engine.apply_outcome(
        ReputationUpdateRequest(validator_id=vid, was_correct=True, was_minority=False)
    )
    assert state.score > base

    # Incorrect outcome
    state = engine.apply_outcome(
        ReputationUpdateRequest(validator_id=vid, was_correct=False, was_minority=False)
    )
    assert state.score <= base * (1.0 + engine.correct_reward)  # bounded


def test_minority_boost_applied():
    engine = ReputationEngine()
    vid = uuid.uuid4()
    base = engine.get_state(vid).score

    state_majority = engine.apply_outcome(
        ReputationUpdateRequest(validator_id=vid, was_correct=True, was_minority=False)
    )
    score_majority = state_majority.score

    # Reset state
    engine = ReputationEngine()
    engine._states[vid] = engine.get_state(vid)
    state_minority = engine.apply_outcome(
        ReputationUpdateRequest(validator_id=vid, was_correct=True, was_minority=True)
    )
    score_minority = state_minority.score

    assert score_minority - base > score_majority - base


def test_stake_decay_and_slashing():
    manager = StakeManager(decay_half_life_days=10.0)
    vid = uuid.uuid4()

    lock_req = StakeLockRequest(
        validator_id=vid,
        amount=1000.0,
        lock_until=datetime.now(timezone.utc) + timedelta(days=365),
    )
    state = manager.lock_stake(lock_req)
    assert state.total_locked == 1000.0

    # Apply decay after some time
    future = state.last_updated + timedelta(days=10)
    decayed = manager.apply_decay(vid, now=future)
    assert decayed is not None
    assert decayed.effective_stake < state.effective_stake

    # Slash 10%
    event = manager.slash(vid, fraction=0.1, reason="test")
    assert event is not None
    new_state = manager.get_state(vid)
    assert new_state is not None
    assert new_state.total_locked < decayed.total_locked
    assert len(new_state.slashing_history) == 1

