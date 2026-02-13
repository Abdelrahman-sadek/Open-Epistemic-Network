## Reputation and Influence

Reputation is maintained per validator in `core/reputation`:

- Validators start from a minimum score (default 1.0).
- Scores **decay exponentially** over time toward the minimum.
- Correct outcomes increase reputation multiplicatively.
- Incorrect outcomes decrease reputation.
- Correct minority positions receive an additional multiplicative **minority boost**.

Influence is computed in `core/validation/influence.py` as:

\\[
IW = \\log(stake\_locked) \\times \\sqrt{reputation\_score} \\times diversity\_modifier \\times time\_factor
\\]

with global caps and floors on each component to ensure sublinear growth and to prevent any single validator from exceeding a configured maximum weight.

## Diversity Enforcement

The diversity module in `core/validation/diversity.py` implements a simple diversity-aware sampler:

- Validators carry `model_family` and `region` attributes.
- The sampler greedily selects validators while enforcing caps on:
  - Maximum fraction from the same **model family**
  - Maximum fraction from the same **region**

In later phases, voting correlation data from Neo4j will feed into these diversity modifiers and correlation penalties, further reducing the influence of tightly correlated validator clusters.

