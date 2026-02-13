## Local Bot Integration Guide

This guide shows how a local bot can interact with the Open Epistemic Network without any blockchain dependency.

The minimal flow is:

1. **Generate an Ed25519 keypair**.
2. **Register** as a validator.
3. **Submit** a claim.
4. **Vote** on that claim with a signed payload.

### 1. Run the API

Start the FastAPI app (for example, with `uvicorn`):

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Use the example bot script

There is a ready‑made example in `scripts/local_bot_example.py` that:

- Generates an Ed25519 keypair (if `pynacl` is available; otherwise it falls back to dummy keys).
- Calls:
  - `POST /validators`
  - `POST /claims`
  - `POST /votes`
  - `GET /claims/{claim_id}/votes`

Run it with:

```bash
python scripts/local_bot_example.py
```

### 3. Vote signing format

For each vote, the bot signs the canonical payload:

```text
{claim_id}|{validator_id}|{vote_type}|{confidence:.6f}|{timestamp_iso}
```

- The message is encoded as UTF‑8 bytes.
- The bot uses its Ed25519 private key to produce a signature.
- The signature is sent as **hex** in the `signature` field of `POST /votes`.

On the server side, the vote service:

- Looks up the validator's public key from the identity service.
- Recomputes the canonical message.
- Verifies the signature if the Ed25519 library is available.
- Stores the vote in an in‑memory registry and exposes it via `GET /claims/{id}/votes`.

This end‑to‑end flow demonstrates how any local bot can participate in the network by registering, proposing claims, and casting cryptographically signed votes. Later phases can plug in stake, reputation, and diversity‑aware selection using the existing core modules.

