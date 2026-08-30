"""PQC recovery flow — ML-KEM handshake and replacement lease issuance.

Recovery sequence (PRD §22):
    1. Security compromise detected
    2. Active QKBNL revoked
    3. Router confirms firewall enforcement
    4. ML-KEM handshake initiated
    5. Shared secret established
    6. Transcript hash calculated
    7. Replacement authorization material derived using HKDF-SHA256
    8. Replacement QKBNL generated
    9. Replacement QKBNL signed
    10. Router validates lease
    11. Firewall access restored
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from packages.common.enums import ExecutionMode
from packages.pqc import mlkem
from packages.pqc.models import RecoveryRecord


def execute_pqc_recovery(
    variant: str = "ML-KEM-768",
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> RecoveryRecord:
    """Execute the ML-KEM handshake portion of PQC recovery.

    Returns a RecoveryRecord with handshake metrics.
    The shared secret is NEVER stored or returned — only its hash.
    """
    record_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    start_time = time.monotonic()

    # Step 1: Generate keypair (Bob/server side)
    keypair = mlkem.keygen(variant, execution_mode)

    # Step 2: Encapsulate (Alice/client side)
    encap = mlkem.encapsulate(keypair.public_key_hex, variant, execution_mode)

    # Step 3: Decapsulate (Bob/server side)
    decap_hash = mlkem.decapsulate(
        keypair.secret_key_hex, encap.ciphertext_hex, variant, execution_mode
    )

    handshake_ms = (time.monotonic() - start_time) * 1000

    # Step 4: Calculate transcript hash
    transcript = (
        f"kem={variant};"
        f"pk_size={keypair.public_key_size};"
        f"ct_size={encap.ciphertext_size};"
        f"ss_hash={encap.shared_secret_hash};"
        f"timestamp={started.isoformat()}"
    )
    transcript_hash = hashlib.sha256(transcript.encode()).hexdigest()

    return RecoveryRecord(
        id=record_id,
        kem_algorithm=variant,
        public_key_size=keypair.public_key_size,
        ciphertext_size=encap.ciphertext_size,
        shared_secret_size=32,  # ML-KEM always produces 32-byte secrets
        handshake_duration_ms=round(handshake_ms, 2),
        transcript_hash=transcript_hash,
        started_at=started,
        completed_at=datetime.now(timezone.utc),
        status="handshake_complete",
    )


def derive_replacement_key_material(
    shared_secret_hash: str,
    context: str = "SHORLYNOT-PQC-RECOVERY-v1",
    key_length: int = 32,
) -> bytes:
    """Derive replacement authorization material using HKDF-SHA256.

    This is used to create replacement key material for QKBNL issuance
    after a PQC recovery handshake.

    Args:
        shared_secret_hash: Hash of the KEM shared secret.
        context: Application context string.
        key_length: Desired key length in bytes.

    Returns:
        Derived key material bytes.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=None,
        info=context.encode("utf-8"),
    )
    return hkdf.derive(bytes.fromhex(shared_secret_hash))
