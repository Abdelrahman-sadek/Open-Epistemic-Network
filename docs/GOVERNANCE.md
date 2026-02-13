## Governance Overview

The governance module controls configurable protocol parameters such as:

- Maximum influence weight
- Stake caps
- Diversity caps by model and region
- Slashing confirmation rounds

Parameters are represented by `GovernanceParams` and versioned. Proposals are created via the `/governance/proposals` endpoint and carry:

- A human-readable title and body
- A `parameters_diff` map describing numeric overrides
- An activation delay before changes can become active

In this initial implementation, proposals are automatically enacted after their activation time when `maybe_enact_proposals` is called, incrementing the governance `version`. A production deployment would wire this to validator voting and record all parameter changes in the append-only ledger.

