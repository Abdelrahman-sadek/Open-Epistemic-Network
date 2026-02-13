from __future__ import annotations

from locust import HttpUser, between, task, tag, constant
import uuid
from datetime import datetime, timezone
import random
import string


def random_string(length: int = 10) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def random_uuid() -> str:
    return str(uuid.uuid4())


def random_domain() -> str:
    domains = ["science", "technology", "health", "finance", "politics", "culture"]
    return random.choice(domains)


def random_vote_type() -> str:
    return random.choice(["approve", "reject", "uncertain"])


def random_confidence() -> float:
    return round(random.uniform(0.1, 1.0), 2)


class EpistemicUser(HttpUser):
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Called when a new user starts"""
        self.validator_id = random_uuid()
        self.public_key = f"test-key-{self.validator_id}"
        self.model_family = random.choice(["gpt-4", "claude-3", "llama-3", "gemini-pro"])
        self.region = random.choice(["na", "eu", "ap", "sa", "af"])
        self.domain_focus = random_domain()
        
        # Register validator
        try:
            self.client.post("/validators", json={
                "public_key": self.public_key,
                "model_family": self.model_family,
                "region": self.region,
                "domain_focus": self.domain_focus
            })
        except Exception as e:
            self.environment.runner.stats.log_error(
                f"Validator registration failed: {e}"
            )


    @tag("health", "basic")
    @task(2)
    def health(self):
        self.client.get("/health")


    @tag("ledger", "basic")
    @task(1)
    def ledger_root(self):
        self.client.get("/ledger/root")


    @tag("claims", "submit")
    @task(3)
    def submit_claim(self):
        claim_id = random_uuid()
        statement = f"Test claim {random_string(20)}"
        
        try:
            response = self.client.post("/claims", json={
                "statement": statement,
                "domain": random_domain(),
                "proposer_id": self.validator_id,
                "evidence_refs": [f"https://example.com/evidence/{random_string(10)}"]
            })
            
            if response.status_code == 200:
                self.last_claim_id = response.json()["id"]
        except Exception as e:
            self.environment.runner.stats.log_error(
                f"Claim submission failed: {e}"
            )


    @tag("votes", "submit")
    @task(4)
    def submit_vote(self):
        if hasattr(self, "last_claim_id"):
            try:
                self.client.post("/votes", json={
                    "claim_id": self.last_claim_id,
                    "validator_id": self.validator_id,
                    "vote_type": random_vote_type(),
                    "confidence": random_confidence(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "signature": f"signature-{random_string(16)}"
                })
            except Exception as e:
                self.environment.runner.stats.log_error(
                    f"Vote submission failed: {e}"
                )


    @tag("votes", "get")
    @task(2)
    def get_votes(self):
        if hasattr(self, "last_claim_id"):
            try:
                self.client.get(f"/claims/{self.last_claim_id}/votes")
            except Exception as e:
                self.environment.runner.stats.log_error(
                    f"Get votes failed: {e}"
                )


    @tag("consensus", "compute")
    @task(1)
    def compute_consensus(self):
        if hasattr(self, "last_claim_id"):
            try:
                self.client.get(f"/validation/claims/{self.last_claim_id}/consensus")
            except Exception as e:
                self.environment.runner.stats.log_error(
                    f"Consensus computation failed: {e}"
                )


    @tag("validators", "get")
    @task(1)
    def get_validator(self):
        try:
            self.client.get(f"/validators/{self.validator_id}")
        except Exception as e:
            self.environment.runner.stats.log_error(
                f"Get validator failed: {e}"
            )


class HighVolumeUser(EpistemicUser):
    """User class for high-volume testing (100k+ bots)"""
    wait_time = constant(0.1)  # Very fast pacing
    weight = 10


class ExtremeVolumeUser(HighVolumeUser):
    """User class for extreme volume testing (1M+ bots)"""
    wait_time = constant(0.05)  # Ultra fast pacing
    weight = 50


# Test scenarios configuration
class LoadTestScenarios:
    """Configuration for different load test scenarios"""
    
    # 1k bots scenario
    SCENARIO_1K_BOTS = {
        "users": 1000,
        "spawn_rate": 50,
        "run_time": "10m",
        "description": "1000 concurrent bots - realistic production load"
    }
    
    # 100k bots scenario
    SCENARIO_100K_BOTS = {
        "users": 100000,
        "spawn_rate": 1000,
        "run_time": "30m",
        "description": "100,000 concurrent bots - extreme load test"
    }
    
    # 1M bots scenario
    SCENARIO_1M_BOTS = {
        "users": 1000000,
        "spawn_rate": 5000,
        "run_time": "60m",
        "description": "1,000,000 concurrent bots - maximum capacity test"
    }


# Command examples for running different scenarios:
#
# 1. 1k bots scenario (realistic production load):
#    locust -f locustfile.py -u 1000 -r 50 -t 10m --headless --only-summary --csv=results/1k-bots
#
# 2. 100k bots scenario (extreme load):
#    locust -f locustfile.py -u 100000 -r 1000 -t 30m --headless --only-summary --csv=results/100k-bots
#
# 3. 1M bots scenario (maximum capacity):
#    locust -f locustfile.py -u 1000000 -r 5000 -t 60m --headless --only-summary --csv=results/1m-bots
#
# For distributed testing with multiple worker nodes:
#    locust -f locustfile.py --master
#    locust -f locustfile.py --worker --master-host=localhost
#
# To run specific tags:
#    locust -f locustfile.py -T "health,basic" -u 100 -r 10 -t 5m
