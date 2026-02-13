## Slashing Policy (Skeleton)

The stake manager in `core/stake` supports **slashing** by applying a fractional reduction to a validator's:

- `total_locked` stake
- `effective_stake` (used in influence calculations)

Each slashing event records:

- Validator ID
- Amount slashed
- Reason
- Timestamp

In a full deployment, slashing would be triggered when:

- Validators repeatedly vote against later consensus beyond a tolerance threshold.
- Validators fail adversarial tests injected by the audit engine.
- Collusion clusters with high correlation and coordinated misbehavior are detected.

All slashing events should be logged to the append-only ledger as dedicated entries.

## Audit and Drift Detection (Skeleton)

`core/audit` contains an `AuditEngine` that records:

- **Drift signals** per domain (e.g., sudden shifts in consensus behavior).
- **Anomaly signals** per validator (e.g., unusually fast reputation growth or suspicious behavior).

Future work will:

- Persist audit events to PostgreSQL.
- Use Neo4j correlation graphs to detect validator clusters and cartel behavior.
- Drive governance proposals or slashing decisions from accumulated audit findings.

