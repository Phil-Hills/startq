"""Receipt integrity helpers for StartQ.

New receipts use HMAC-SHA256 with a workspace-local secret. Receipts created
before 0.5 used an unkeyed SHA-256 digest; they remain verifiable as legacy
records but do not provide authenticity against a writer with disk access.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path


ALGORITHM = "hmac-sha256"


def _canonical_payload(receipt: dict) -> bytes:
    payload = {key: value for key, value in receipt.items() if key != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def signing_key_path(root_dir: str | Path) -> Path:
    """Return the user-protected key path for a StartQ workspace."""
    override = os.environ.get("STARTQ_SIGNING_KEY_FILE")
    if override:
        return Path(override).expanduser()

    workspace = str(Path(root_dir).resolve())
    workspace_id = hashlib.sha256(workspace.encode("utf-8")).hexdigest()[:16]
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "startq" / "keys" / f"{workspace_id}.key"


def get_or_create_signing_key(root_dir: str | Path) -> bytes:
    """Load the local signing key, creating it with owner-only permissions."""
    path = signing_key_path(root_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        return bytes.fromhex(path.read_text(encoding="ascii").strip())
    except FileNotFoundError:
        pass
    except ValueError as exc:
        raise ValueError(f"Invalid StartQ signing key at {path}") from exc

    key = secrets.token_bytes(32)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as handle:
            handle.write(key.hex() + "\n")
    except FileExistsError:
        return bytes.fromhex(path.read_text(encoding="ascii").strip())

    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key


def sign_receipt(receipt: dict, root_dir: str | Path) -> dict:
    """Return a copy of *receipt* with an HMAC signature and key identifier."""
    signed = dict(receipt)
    key = get_or_create_signing_key(root_dir)
    signed["signature_algorithm"] = ALGORITHM
    signed["key_id"] = hashlib.sha256(key).hexdigest()[:16]
    signed["signature"] = hmac.new(key, _canonical_payload(signed), hashlib.sha256).hexdigest()
    return signed


def verify_receipt(receipt: dict, root_dir: str | Path) -> tuple[bool, str]:
    """Verify a receipt and return ``(valid, verification_profile)``."""
    stored = receipt.get("signature")
    if not isinstance(stored, str) or not stored:
        return False, "unsigned"

    algorithm = receipt.get("signature_algorithm")
    if algorithm == ALGORITHM:
        path = signing_key_path(root_dir)
        if not path.exists():
            return False, "missing-signing-key"
        try:
            key = bytes.fromhex(path.read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            return False, "invalid-signing-key"
        expected_key_id = hashlib.sha256(key).hexdigest()[:16]
        if receipt.get("key_id") != expected_key_id:
            return False, "wrong-signing-key"
        expected = hmac.new(key, _canonical_payload(receipt), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, stored), ALGORITHM

    if algorithm:
        return False, f"unsupported:{algorithm}"

    # Backward compatibility for receipts created by StartQ <= 0.4.
    legacy_payload = {key: value for key, value in receipt.items() if key != "signature"}
    serialized = json.dumps(legacy_payload, sort_keys=True).encode("utf-8")
    expected = hashlib.sha256(serialized).hexdigest()
    return hmac.compare_digest(expected, stored), "legacy-sha256"
