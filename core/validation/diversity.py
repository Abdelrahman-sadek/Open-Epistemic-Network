from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class ValidatorProfile:
    id: uuid.UUID
    model_family: str
    region: str


def compute_correlation_penalty(correlation: float, *, max_penalty: float = 0.5) -> float:
    """
    Map correlation in [0,1] to a multiplicative penalty in [1-max_penalty, 1].
    """
    correlation = max(0.0, min(1.0, correlation))
    return 1.0 - max_penalty * correlation


def diversity_aware_sample(
    validators: Iterable[ValidatorProfile],
    *,
    max_same_model_fraction: float = 0.4,
    max_same_region_fraction: float = 0.5,
    target_count: int = 10,
) -> List[ValidatorProfile]:
    """
    Simple diversity-aware sampler:
    - Greedily picks validators while ensuring per-model and per-region caps.
    """
    population = list(validators)
    if not population or target_count <= 0:
        return []

    selected: List[ValidatorProfile] = []
    model_counts: Dict[str, int] = {}
    region_counts: Dict[str, int] = {}

    def within_caps(candidate: ValidatorProfile) -> bool:
        next_total = len(selected) + 1
        next_model_count = model_counts.get(candidate.model_family, 0) + 1
        next_region_count = region_counts.get(candidate.region, 0) + 1

        if next_model_count / next_total > max_same_model_fraction:
            return False
        if next_region_count / next_total > max_same_region_fraction:
            return False
        return True

    for v in population:
        if len(selected) >= target_count:
            break
        if within_caps(v):
            selected.append(v)
            model_counts[v.model_family] = model_counts.get(v.model_family, 0) + 1
            region_counts[v.region] = region_counts.get(v.region, 0) + 1

    return selected

