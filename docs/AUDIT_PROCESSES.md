## Audit and Slashing Processes (Draft)

This document refines how the audit engine and slashing mechanisms can be used in practice.

### Routine Audit Loop

1. **Data Collection**:
   - Periodically aggregate votes, outcomes, and reputations per validator and per domain.
2. **Drift Detection**:
   - Compute domain-level statistics (e.g., fraction of claims accepted vs. rejected, disagreement rates).
   - Flag domains where behavior changes significantly over a defined window.
3. **Anomaly Detection**:
   - Identify validators whose reputation grows unusually quickly or whose behavior deviates sharply from peers.
   - Use Neo4j correlation graphs (future work) to detect tightly coupled voting clusters.
4. **Recording**:
   - Write drift and anomaly events into `core/audit` and, in a full implementation, persist them in PostgreSQL and/or Neo4j.

### Adversarial Test Injection

1. **Test Design**:
   - Construct claims with known truth values (true and false) in various domains.
2. **Injection**:
   - Submit these claims like normal user claims, but mark them internally as tests.
3. **Evaluation**:
   - Compare validator votes against the known ground truth.
   - Use results to adjust reputation and, if necessary, to trigger slashing or governance review.

### Slashing Pipeline (Future Implementation)

1. **Trigger Detection**:
   - Accumulated evidence from:
     - Repeated disagreement with eventual consensus.
     - Failing adversarial tests.
     - Collusion indicators from correlation analysis.
2. **Case Build**:
   - Summarize evidence into a proposed slashing action (validator, fraction, reason).
3. **Confirmation Rounds**:
   - Run multiple, independent audit passes or require governance confirmation before applying slashing.
4. **Execution**:
   - Apply slashing via the stake manager (reducing locked and effective stake, possibly freezing the validator).
   - Log the slashing event in both the stake history and the append-only ledger.
5. **Review**:
   - Publish a human-readable summary of major slashing events to support transparency and external audit.

These processes give concrete meaning to the hooks already present in `core/audit`, `core/stake`, and the ledger, and are intended to evolve as real-world threats and behaviors are better understood.

