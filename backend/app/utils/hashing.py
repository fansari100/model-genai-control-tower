"""Cryptographic hashing utilities for evidence and audit trail."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_dict(data: dict[str, Any]) -> str:
    """Compute SHA-256 of a canonicalized JSON dict."""
    canonical = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 of a file on disk."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hash(data: bytes, expected_hash: str) -> bool:
    """Verify that data matches expected SHA-256 hash."""
    return sha256_bytes(data) == expected_hash
