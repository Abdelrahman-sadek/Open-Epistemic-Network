"""
Prometheus/OpenTelemetry metrics for the Open Epistemic Network
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client import start_http_server
import time
from functools import wraps
from typing import Callable, TypeVar, Any

# Metrics registry configuration
REGISTRY_PORT = 8001

# General metrics
REQUEST_COUNT = Counter(
    'open_epistemic_requests_total',
    'Total number of HTTP requests',
    ['method', 'path', 'status']
)

REQUEST_DURATION = Histogram(
    'open_epistemic_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'path'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Validator metrics
VALIDATOR_COUNT = Gauge(
    'open_epistemic_validators_total',
    'Total number of registered validators',
    ['status']
)

VALIDATOR_INFLUENCE = Gauge(
    'open_epistemic_validator_influence',
    'Influence weight of validators',
    ['validator_id']
)

# Claim metrics
CLAIM_COUNT = Counter(
    'open_epistemic_claims_total',
    'Total number of claims submitted',
    ['domain']
)

CLAIM_STATUS = Gauge(
    'open_epistemic_claim_status',
    'Status of claims (0=uncertain, 1=accepted, 2=rejected)',
    ['claim_id']
)

# Vote metrics
VOTE_COUNT = Counter(
    'open_epistemic_votes_total',
    'Total number of votes cast',
    ['vote_type']
)

VOTE_CONFIDENCE = Histogram(
    'open_epistemic_vote_confidence',
    'Confidence level of votes',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Consensus metrics
CONSENSUS_COUNT = Counter(
    'open_epistemic_consensus_total',
    'Total number of consensus processes completed',
    ['outcome']
)

CONSENSUS_ROUNDS = Histogram(
    'open_epistemic_consensus_rounds',
    'Number of rounds to reach consensus',
    buckets=[1, 2, 3, 4, 5]
)

CONSENSUS_CONFIDENCE = Histogram(
    'open_epistemic_consensus_confidence',
    'Confidence level of consensus decisions',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Stake and reputation metrics
STAKED_AMOUNT = Gauge(
    'open_epistemic_staked_amount',
    'Total amount of stake locked',
    ['validator_id']
)

REPUTATION_SCORE = Gauge(
    'open_epistemic_reputation_score',
    'Reputation score of validators',
    ['validator_id']
)

SLASHING_COUNT = Counter(
    'open_epistemic_slashing_total',
    'Total number of slashing events',
    ['reason']
)

# Validation session metrics
VALIDATION_SESSIONS = Gauge(
    'open_epistemic_validation_sessions',
    'Number of active validation sessions',
    ['round']
)

VALIDATORS_SAMPLED = Histogram(
    'open_epistemic_validators_sampled',
    'Number of validators sampled per round',
    buckets=[5, 10, 15, 20, 25, 30]
)

# Health metrics
HEALTH_STATUS = Gauge(
    'open_epistemic_health_status',
    'Overall health status (1=healthy, 0=unhealthy)'
)

API_LATENCY = Histogram(
    'open_epistemic_api_latency',
    'API endpoint latency in seconds',
    ['endpoint', 'method'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Helper decorator for measuring API latency
T = TypeVar('T')

def measure_latency(endpoint: str):
    """Decorator to measure API endpoint latency"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                API_LATENCY.labels(endpoint=endpoint, method=args[1].method).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                API_LATENCY.labels(endpoint=endpoint, method=args[1].method).observe(duration)
                raise
        return wrapper
    return decorator

def start_metrics_server():
    """Start the Prometheus metrics server"""
    try:
        start_http_server(REGISTRY_PORT)
        print(f"Metrics server running on http://localhost:{REGISTRY_PORT}")
        return True
    except Exception as e:
        print(f"Failed to start metrics server: {e}")
        return False

def update_health_status(healthy: bool):
    """Update health status metric"""
    HEALTH_STATUS.set(1 if healthy else 0)

def record_request(method: str, path: str, status: int, duration: float):
    """Record request metrics"""
    REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
    REQUEST_DURATION.labels(method=method, path=path).observe(duration)

def record_claim_submission(domain: str):
    """Record claim submission metrics"""
    CLAIM_COUNT.labels(domain=domain).inc()

def record_vote(vote_type: str, confidence: float):
    """Record vote metrics"""
    VOTE_COUNT.labels(vote_type=vote_type).inc()
    VOTE_CONFIDENCE.observe(confidence)

def record_consensus(outcome: str, rounds: int, confidence: float):
    """Record consensus metrics"""
    CONSENSUS_COUNT.labels(outcome=outcome).inc()
    CONSENSUS_ROUNDS.observe(rounds)
    CONSENSUS_CONFIDENCE.observe(confidence)

def record_slashing(validator_id: str, amount: float, reason: str):
    """Record slashing metrics"""
    SLASHING_COUNT.labels(reason=reason).inc()
    if validator_id:
        STAKED_AMOUNT.labels(validator_id=validator_id).dec(amount)

def update_validator_metrics(validator_id: str, influence: float, stake: float, reputation: float):
    """Update validator metrics"""
    VALIDATOR_INFLUENCE.labels(validator_id=validator_id).set(influence)
    STAKED_AMOUNT.labels(validator_id=validator_id).set(stake)
    REPUTATION_SCORE.labels(validator_id=validator_id).set(reputation)