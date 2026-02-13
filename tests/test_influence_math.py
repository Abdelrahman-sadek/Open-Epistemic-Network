from __future__ import annotations

import math

from core.validation.influence import ValidatorInfluenceContext, compute_influence_weight


def test_influence_sublinear_growth_with_stake_and_time():
    """
    Basic sanity: doubling stake or time should not more than double influence
    in typical ranges, due to log and slow time_factor.
    """
    base_ctx = ValidatorInfluenceContext(
        stake_locked=100.0,
        reputation_score=100.0,
        diversity_modifier=1.0,
        time_active_days=30.0,
    )
    iw_base = compute_influence_weight(base_ctx)

    ctx_more_stake = ValidatorInfluenceContext(
        stake_locked=200.0,
        reputation_score=100.0,
        diversity_modifier=1.0,
        time_active_days=30.0,
    )
    iw_more_stake = compute_influence_weight(ctx_more_stake)

    ctx_more_time = ValidatorInfluenceContext(
        stake_locked=100.0,
        reputation_score=100.0,
        diversity_modifier=1.0,
        time_active_days=60.0,
    )
    iw_more_time = compute_influence_weight(ctx_more_time)

    assert iw_more_stake / iw_base < 2.0
    assert iw_more_time / iw_base < 2.0


def test_influence_cap_enforced():
    ctx = ValidatorInfluenceContext(
        stake_locked=1e12,
        reputation_score=1e12,
        diversity_modifier=2.0,
        time_active_days=3650.0,
    )
    iw = compute_influence_weight(ctx, max_weight_cap=1e6)
    assert iw <= 1e6

