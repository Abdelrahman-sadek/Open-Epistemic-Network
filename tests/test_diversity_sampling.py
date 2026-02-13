from __future__ import annotations

import uuid

from core.validation.diversity import ValidatorProfile, diversity_aware_sample


def test_diversity_sampler_respects_model_and_region_caps():
    validators = []
    # 6 validators from same model/region, 4 from another
    for _ in range(6):
        validators.append(
            ValidatorProfile(
                id=uuid.uuid4(),
                model_family="modelA",
                region="us",
            )
        )
    for _ in range(4):
        validators.append(
            ValidatorProfile(
                id=uuid.uuid4(),
                model_family="modelB",
                region="eu",
            )
        )

    sample = diversity_aware_sample(validators, max_same_model_fraction=0.6, max_same_region_fraction=0.7, target_count=8)
    assert len(sample) <= 8

    model_counts = {}
    region_counts = {}
    for v in sample:
        model_counts[v.model_family] = model_counts.get(v.model_family, 0) + 1
        region_counts[v.region] = region_counts.get(v.region, 0) + 1

    total = len(sample)
    for count in model_counts.values():
        assert count / total <= 0.6 + 1e-6
    for count in region_counts.values():
        assert count / total <= 0.7 + 1e-6

