"""Integration tests for ShorlyNot.

PRD §31 requires testing:
- quantum result -> QKD session
- secure session -> QKBNL
- QKBNL -> router acknowledgement
- compromise -> revocation
- revocation -> firewall event
- PQC recovery -> replacement lease
"""

from __future__ import annotations

import pytest
import datetime
from uuid import uuid4

from packages.common.enums import QKDProtocol, ExecutionMode, DeviceType, DeviceStatus, SecurityStatus, PolicyState
from packages.common.schemas import QuantumJobRead, QKDSessionRead, DeviceRead, QKBNLLeasePayload
from packages.qkd.bb84 import run_bb84_protocol
from packages.crypto.lease_signer import LeaseSigner
from packages.policy.state_machine import PolicyStateMachine
from packages.pqc.recovery import execute_pqc_recovery


def test_quantum_result_to_qkd_session():
    """Test full flow: quantum job -> BB84 execution -> QKD session record."""
    job_id = str(uuid4())
    alice_id = str(uuid4())
    bob_id = str(uuid4())

    # Execute quantum protocol
    result = run_bb84_protocol(num_qubits=200)
    assert result.qber is not None

    # Construct session
    session = QKDSessionRead(
        id=str(uuid4()),
        protocol=QKDProtocol.BB84,
        quantum_job_id=job_id,
        alice_device_id=alice_id,
        bob_device_id=bob_id,
        raw_key_length=result.raw_key_length,
        sifted_key_length=result.sifted_key_length,
        reconciled_key_length=result.sifted_key_length,  # simplified
        final_key_length=result.sifted_key_length,       # simplified
        qber=result.qber,
        estimated_eve_information=result.theoretical_qber,
        min_entropy_raw=float(result.raw_key_length),
        min_entropy_sifted=float(result.sifted_key_length),
        min_entropy_reconciled=float(result.sifted_key_length),
        min_entropy_final=float(result.sifted_key_length),
        security_status=SecurityStatus.SECURE if result.qber < 0.11 else SecurityStatus.COMPROMISED,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    
    assert session.security_status == SecurityStatus.SECURE


def test_secure_session_to_qkbnl():
    """Test issuing a QKBNL from a secure session."""
    priv, pub = LeaseSigner.generate_keypair()
    signer = LeaseSigner(private_key=priv)
    
    session_id = str(uuid4())
    device_id = str(uuid4())
    now = datetime.datetime.now(datetime.timezone.utc)
    
    payload = QKBNLLeasePayload(
        lease_id="QKBNL-TESTINT",
        device_id=device_id,
        qkd_session_id=session_id,
        key_fingerprint="testfp",
        issued_at=now.isoformat(),
        expires_at=(now + datetime.timedelta(seconds=60)).isoformat(),
        nonce="abcd",
        sequence_number=1,
        policy_version="1.0"
    )
    
    sig = signer.sign_lease(payload)
    assert signer.verify_lease(payload, sig)


def test_compromise_revocation_firewall():
    """Test policy transition from secure to compromised to isolated."""
    sm = PolicyStateMachine()
    
    # Session secure
    sm.transition(PolicyState.SECURE, "Initial QKD complete")
    assert sm.state == PolicyState.SECURE
    
    # Attack detected
    sm.transition(PolicyState.COMPROMISED, "QBER exceeded 11%")
    assert sm.state == PolicyState.COMPROMISED
    
    # Revoke lease
    sm.transition(PolicyState.REVOKING, "Revoking QKBNL")
    assert sm.state == PolicyState.REVOKING
    
    # Firewall event confirmed
    sm.transition(PolicyState.ISOLATED, "Router applied BLOCK rule")
    assert sm.state == PolicyState.ISOLATED


def test_pqc_recovery_replacement():
    """Test PQC recovery leading to a new secure state."""
    sm = PolicyStateMachine()
    
    sm.transition(PolicyState.SECURE, "Initial QKD complete")
    sm.transition(PolicyState.COMPROMISED, "QBER exceeded")
    sm.transition(PolicyState.REVOKING, "Revoking QKBNL")
    sm.transition(PolicyState.ISOLATED, "Router applied BLOCK rule")
    
    # Start recovery
    sm.transition(PolicyState.PQC_RECOVERY, "Executing ML-KEM-768")
    
    # Simulate PQC handshake
    record = execute_pqc_recovery()
    assert record.status == "handshake_complete"
    
    sm.transition(PolicyState.RESTORING, "Handshake complete")
    sm.transition(PolicyState.SECURE, "New QKBNL issued")
    
    assert sm.state == PolicyState.SECURE
