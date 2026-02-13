## Architecture Overview

This project implements the core of an open, non‑blockchain epistemic network with:

- Hybrid **stake + reputation** influence
- Cryptographic identities
- An **append-only knowledge ledger** with Merkle roots
- Diversity-aware validation
- Governance and audit scaffolding

The system is organized into core domain modules under `core/` and a FastAPI application under `api/`.

High-level data flow:

- Validators register with the identity service.
- Claims are submitted and stored in the ledger module.
- Ledger entries are append-only and feed into a Merkle tree; the latest root is exposed via `/ledger/root`.
- Stake, reputation, and influence math live in `core/stake`, `core/reputation`, and `core/validation`.
- Governance parameters and proposals live in `core/governance` and are surfaced via `/governance` endpoints.

