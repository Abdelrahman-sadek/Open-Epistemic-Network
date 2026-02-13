from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DriftSignal:
    domain: str
    drift_score: float


@dataclass
class AnomalySignal:
    validator_id: str
    reason: str
    severity: float


class AuditEngine:
    """
    Minimal audit engine skeleton.

    Phase 3 will extend this to use Neo4j for correlation graphs and
    store findings in PostgreSQL.
    """

    def __init__(self) -> None:
        self._drift_signals: List[DriftSignal] = []
        self._anomaly_signals: List[AnomalySignal] = []

    def record_drift(self, domain: str, drift_score: float) -> None:
        self._drift_signals.append(DriftSignal(domain=domain, drift_score=drift_score))

    def record_anomaly(self, validator_id: str, reason: str, severity: float) -> None:
        self._anomaly_signals.append(AnomalySignal(validator_id=validator_id, reason=reason, severity=severity))

    def get_recent_drift(self) -> List[DriftSignal]:
        return list(self._drift_signals)

    def get_recent_anomalies(self) -> List[AnomalySignal]:
        return list(self._anomaly_signals)

