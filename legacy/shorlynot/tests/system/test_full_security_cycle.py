"""System test for the full ShorlyNot security cycle.

PRD §31 requires testing the full sequence from QKD to lease revocation and PQC recovery.
In simulation mode, all adapters may be simulated.
"""

from __future__ import annotations

import datetime
import pytest
from uuid import uuid4

from packages.common.enums import PolicyState, SecurityStatus, FirewallAction, EnforcementStatus
from packages.common.schemas import QKBNLLeasePayload, FirewallEventRead
from packages.policy.state_machine import PolicyStateMachine
from packages.qkd.bb84 import run_bb84_protocol
from packages.crypto.lease_signer import LeaseSigner
from packages.pqc.recovery import execute_pqc_recovery


class MockRouterAdapter:
    """Mock router adapter for simulation mode testing."""
    def __init__(self):
        self.active_leases = {}
        self.flushed = False

    def apply_rule(self, lease_id: str, ip: str) -> FirewallEventRead:
        self.active_leases[lease_id] = ip
        return FirewallEventRead(
            id=str(uuid4()),
            lease_id=lease_id,
            router_id="mock-router",
            action=FirewallAction.ALLOW,
            target_ip=ip,
            rule_identifier=f"allow-{lease_id}",
            requested_at=datetime.datetime.now(datetime.timezone.utc),
            acknowledged_at=datetime.datetime.now(datetime.timezone.utc),
            status=EnforcementStatus.VERIFIED
        )

    def revoke_rule(self, lease_id: str, ip: str) -> FirewallEventRead:
        if lease_id in self.active_leases:
            del self.active_leases[lease_id]
        
        self.flushed = True
        return FirewallEventRead(
            id=str(uuid4()),
            lease_id=lease_id,
            router_id="mock-router",
            action=FirewallAction.REVOKE,
            target_ip=ip,
            rule_identifier=f"revoke-{lease_id}",
            requested_at=datetime.datetime.now(datetime.timezone.utc),
            acknowledged_at=datetime.datetime.now(datetime.timezone.utc),
            status=EnforcementStatus.VERIFIED
        )


def test_full_security_cycle():
    """Execute the complete QKBNL lifecycle."""
    sm = PolicyStateMachine()
    router = MockRouterAdapter()
    signer_priv, signer_pub = LeaseSigner.generate_keypair()
    signer = LeaseSigner(private_key=signer_priv)
    
    # 1. Start secure QKD session & complete security analysis
    qkd_result = run_bb84_protocol(num_qubits=500)
    assert qkd_result.qber < 0.11
    
    # 2. Issue QKBNL
    lease_id = "QKBNL-SYS-1"
    payload = QKBNLLeasePayload(
        lease_id=lease_id,
        device_id="client-ip",
        qkd_session_id=str(uuid4()),
        key_fingerprint="fp1",
        issued_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        expires_at=(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60)).isoformat(),
        nonce="nonce1",
        sequence_number=1,
        policy_version="1.0"
    )
    sig = signer.sign_lease(payload)
    assert signer.verify_lease(payload, sig)
    
    sm.transition(PolicyState.SECURE, "Initial QKD complete")
    
    # 3. Apply router authorization & verify access state
    apply_event = router.apply_rule(lease_id, "10.0.0.5")
    assert apply_event.status == EnforcementStatus.VERIFIED
    assert lease_id in router.active_leases
    
    # 4. Inject experiment attack / detect compromise
    # (Simulated by running protocol with attack)
    attack_result = run_bb84_protocol(num_qubits=500, attack_probability=1.0)
    assert attack_result.qber > 0.11
    
    sm.transition(PolicyState.COMPROMISED, "QBER exceeded threshold")
    
    # 5. Revoke lease
    sm.transition(PolicyState.REVOKING, "Initiating revocation")
    revoke_event = router.revoke_rule(lease_id, "10.0.0.5")
    
    # 6. Verify router revocation & connection-state flush
    assert revoke_event.status == EnforcementStatus.VERIFIED
    assert lease_id not in router.active_leases
    assert router.flushed is True
    
    sm.transition(PolicyState.ISOLATED, "Router applied BLOCK/REVOKE rule")
    
    # 7. Execute ML-KEM recovery
    sm.transition(PolicyState.PQC_RECOVERY, "Executing ML-KEM-768")
    recovery_record = execute_pqc_recovery()
    assert recovery_record.status == "handshake_complete"
    
    sm.transition(PolicyState.RESTORING, "Handshake complete")
    
    # 8. Issue replacement lease
    replacement_lease_id = "QKBNL-SYS-2"
    payload2 = payload.model_copy(update={"lease_id": replacement_lease_id, "sequence_number": 2})
    sig2 = signer.sign_lease(payload2)
    assert signer.verify_lease(payload2, sig2)
    
    # 9. Verify router restoration
    restore_event = router.apply_rule(replacement_lease_id, "10.0.0.5")
    assert restore_event.status == EnforcementStatus.VERIFIED
    assert replacement_lease_id in router.active_leases
    
    sm.transition(PolicyState.SECURE, "Recovery complete, replacement lease issued")
    
    assert sm.state == PolicyState.SECURE
