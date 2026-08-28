"""Pydantic models for PQC operations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KEMKeyPair(BaseModel):
    """Public/secret keypair for KEM operations."""

    algorithm: str
    public_key_size: int
    secret_key_size: int
    # Keys stored as hex — never logged
    public_key_hex: str = Field(exclude=True, repr=False)
    secret_key_hex: str = Field(exclude=True, repr=False)


class KEMEncapsulation(BaseModel):
    """Result of KEM encapsulation."""

    algorithm: str
    ciphertext_size: int
    shared_secret_size: int
    # Never displayed — only stored for verification hash
    ciphertext_hex: str = Field(exclude=True, repr=False)
    shared_secret_hash: str  # SHA-256 of shared secret (for verification only)


class RecoveryRecord(BaseModel):
    """Record of a PQC recovery operation."""

    id: str
    kem_algorithm: str
    public_key_size: int
    ciphertext_size: int
    shared_secret_size: int
    handshake_duration_ms: float
    transcript_hash: str
    replacement_lease_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "started"
