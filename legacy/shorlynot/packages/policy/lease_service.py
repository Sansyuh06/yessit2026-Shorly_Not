"""QKBNL lease issuance service.

Issues leases only when all security preconditions are met.
Never transmits the raw QKD key to the router.

PRD §15.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from packages.common.enums import LeaseStatus, SecurityStatus
from packages.common.errors import InsufficientKeyMaterialError, QKDSecurityThresholdFailedError
from packages.common.schemas import QKBNLLeasePayload, QKBNLLeaseRead
from packages.crypto.lease_signer import LeaseSigner


class LeaseService:
    """Issues and manages QKBNL leases."""

    def __init__(
        self,
        signer: LeaseSigner,
        default_ttl_seconds: int = 60,
        min_final_key_bits: int = 128,
        policy_version: str = "1.0.0",
    ) -> None:
        self._signer = signer
        self._default_ttl = default_ttl_seconds
        self._min_key_bits = min_final_key_bits
        self._policy_version = policy_version
        self._sequence_numbers: dict[str, int] = {}  # device_id -> last seq

    def issue_lease(
        self,
        device_id: str,
        qkd_session_id: str,
        final_key: list[int],
        security_status: SecurityStatus,
        finite_key_secure: bool,
        has_critical_event: bool = False,
        ttl_seconds: Optional[int] = None,
    ) -> tuple[QKBNLLeasePayload, str, str]:
        """Issue a new QKBNL lease.

        Preconditions (all must be true):
            - security_status == SECURE
            - final_key_length >= min_final_key_bits
            - finite_key_secure == True
            - no CRITICAL security event active

        Args:
            device_id: Target device UUID.
            qkd_session_id: Source QKD session UUID.
            final_key: The final privacy-amplified key bits.
            security_status: Current security assessment.
            finite_key_secure: Whether finite-key analysis passed.
            has_critical_event: Whether a CRITICAL event is active.
            ttl_seconds: Lease lifetime (uses default if None).

        Returns:
            Tuple of (lease_payload, signature, key_id).

        Raises:
            QKDSecurityThresholdFailedError: If security checks fail.
            InsufficientKeyMaterialError: If key is too short.
        """
        # Validate preconditions
        if security_status != SecurityStatus.SECURE:
            raise QKDSecurityThresholdFailedError(
                f"Cannot issue lease: security_status={security_status.value}"
            )

        if len(final_key) < self._min_key_bits:
            raise InsufficientKeyMaterialError(
                f"Final key length {len(final_key)} < minimum {self._min_key_bits}"
            )

        if not finite_key_secure:
            raise QKDSecurityThresholdFailedError(
                "Cannot issue lease: finite-key analysis indicates INSECURE"
            )

        if has_critical_event:
            raise QKDSecurityThresholdFailedError(
                "Cannot issue lease: CRITICAL security event is active"
            )

        # Generate lease fields
        ttl = ttl_seconds or self._default_ttl
        now = datetime.now(timezone.utc)
        lease_id = f"QKBNL-{uuid.uuid4().hex[:16].upper()}"
        nonce = secrets.token_hex(32)
        seq = self._next_sequence(device_id)

        # Key fingerprint (SHA-256 of the key bits — key is NOT transmitted)
        key_bytes = bytes(final_key)
        key_fingerprint = hashlib.sha256(key_bytes).hexdigest()

        payload = QKBNLLeasePayload(
            lease_id=lease_id,
            device_id=device_id,
            qkd_session_id=qkd_session_id,
            key_fingerprint=key_fingerprint,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl)).isoformat(),
            nonce=nonce,
            sequence_number=seq,
            policy_version=self._policy_version,
        )

        # Sign
        signature = self._signer.sign_lease(payload)
        key_id = self._signer.key_id

        return payload, signature, key_id

    def _next_sequence(self, device_id: str) -> int:
        """Get and increment the sequence number for a device."""
        current = self._sequence_numbers.get(device_id, 0)
        next_seq = current + 1
        self._sequence_numbers[device_id] = next_seq
        return next_seq
