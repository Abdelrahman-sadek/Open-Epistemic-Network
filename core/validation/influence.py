from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ValidatorInfluenceContext:
    stake_locked: float
    reputation_score: float
    diversity_modifier: float
    time_active_days: float


def compute_time_factor(time_active_days: float, *, k: float = 0.01) -> float:
    """
    Slowly increasing time factor: 1 - exp(-k * t), bounded in (0, 1).
    """
    if time_active_days <= 0:
        return 0.1  # small initial trust
    return 1.0 - math.exp(-k * time_active_days)


def compute_influence_weight(
    ctx: ValidatorInfluenceContext,
    *,
    max_weight_cap: float = 1e6,
    min_stake: float = 1.0,
    min_reputation: float = 1.0,
    min_diversity: float = 0.2,
    max_diversity: float = 1.5,
) -> float:
    """
    Influence weight:

        IW = log(stake_locked) * sqrt(reputation_score) * diversity_modifier * time_factor

    with caps and floors to enforce constraints.
    """
    stake = max(min_stake, min(ctx.stake_locked, max_weight_cap))
    rep = max(min_reputation, min(ctx.reputation_score, max_weight_cap))
    diversity = max(min_diversity, min(ctx.diversity_modifier, max_diversity))
    t_factor = compute_time_factor(ctx.time_active_days)

    iw = math.log(stake) * math.sqrt(rep) * diversity * t_factor
    if iw > max_weight_cap:
        iw = max_weight_cap
    return iw

