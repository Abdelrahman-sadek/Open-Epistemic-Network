from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import Claim, ClaimCreateRequest, ClaimResponse, LedgerEntry, hash_claim


@dataclass
class MerkleSnapshot:
    root_hash: str
    entry_ids: List[uuid.UUID]
    created_at: datetime


class LedgerService:
    """
    In-memory append-only ledger with Merkle root snapshots.

    This is a Phase 1 implementation; later we will back this with PostgreSQL
    and epoch-based snapshots.
    """

    def __init__(self) -> None:
        self._claims: Dict[uuid.UUID, Claim] = {}
        self._ledger_entries: List[LedgerEntry] = []
        self._latest_entry_by_claim: Dict[uuid.UUID, LedgerEntry] = {}
        self._latest_merkle_snapshot: Optional[MerkleSnapshot] = None

    # ---- Claims ----

    def create_claim(self, req: ClaimCreateRequest) -> ClaimResponse:
        claim_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        claim = Claim(
            id=claim_id,
            statement=req.statement,
            domain=req.domain,
            proposer_id=req.proposer_id,
            evidence_refs=req.evidence_refs,
            version=1,
            parent_version=None,
            created_at=now,
            confidence_score=0.0,
            validation_status="pending",
        )
        self._claims[claim_id] = claim
        self._append_ledger_entry(claim)
        self._recompute_merkle_root()
        return ClaimResponse(**claim.__dict__)

    def get_claim(self, claim_id: uuid.UUID) -> Optional[ClaimResponse]:
        claim = self._claims.get(claim_id)
        if not claim:
            return None
        return ClaimResponse(**claim.__dict__)

    def apply_consensus(
        self,
        claim_id: uuid.UUID,
        outcome: str,
        confidence: float,
    ) -> Optional[ClaimResponse]:
        """
        Record a consensus outcome for a claim by creating a new version and
        appending a ledger entry. The latest version is kept in _claims.
        """
        existing = self._claims.get(claim_id)
        if existing is None:
            return None

        new_version = existing.version + 1
        updated = Claim(
            id=existing.id,
            statement=existing.statement,
            domain=existing.domain,
            proposer_id=existing.proposer_id,
            evidence_refs=existing.evidence_refs,
            version=new_version,
            parent_version=existing.version,
            created_at=existing.created_at,
            confidence_score=confidence,
            validation_status=outcome,
        )

        self._claims[claim_id] = updated
        self._append_ledger_entry(updated)
        self._recompute_merkle_root()
        return ClaimResponse(**updated.__dict__)

    # ---- Ledger & Merkle tree ----

    def _append_ledger_entry(self, claim: Claim) -> None:
        previous_entry = self._latest_entry_by_claim.get(claim.id)
        entry = LedgerEntry(
            id=uuid.uuid4(),
            claim_id=claim.id,
            version=claim.version,
            previous_entry_id=previous_entry.id if previous_entry else None,
            payload_hash=hash_claim(claim),
            created_at=datetime.now(timezone.utc),
        )
        self._ledger_entries.append(entry)
        self._latest_entry_by_claim[claim.id] = entry

    def _recompute_merkle_root(self) -> None:
        """
        Simple Merkle tree over current ledger entries.

        Leaves are ordered by insertion; this is sufficient for Phase 1
        and can later be replaced by epoch-based snapshots.
        """
        if not self._ledger_entries:
            self._latest_merkle_snapshot = None
            return

        leaves = [entry.payload_hash for entry in self._ledger_entries]
        root = self._build_merkle_root(leaves)
        self._latest_merkle_snapshot = MerkleSnapshot(
            root_hash=root,
            entry_ids=[e.id for e in self._ledger_entries],
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _build_merkle_root(leaves: List[str]) -> str:
        """
        Build a Merkle root from a list of hex-encoded leaf hashes.
        """
        if not leaves:
            return ""
        level = leaves[:]
        while len(level) > 1:
            next_level: List[str] = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                combined = (left + right).encode("utf-8")
                from hashlib import sha256

                next_level.append(sha256(combined).hexdigest())
            level = next_level
        return level[0]

    def get_latest_root(self) -> Optional[Tuple[str, int]]:
        """
        Return (root_hash, entry_count) if available.
        """
        if not self._latest_merkle_snapshot:
            return None
        return self._latest_merkle_snapshot.root_hash, len(self._latest_merkle_snapshot.entry_ids)

