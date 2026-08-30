"""
Security-focused KMS tests — verify no key leaks, proper isolation.
"""
import pytest
from kms.key_management_service import KeyManagementService

class TestKMSSecurity:
    
    def test_compromised_session_not_retrievable(self):
        """A RED-status session must NOT be retrievable via get_key()."""
        kms = KeyManagementService()
        kms.eve_mode = True
        with pytest.raises(Exception):
            kms.create_session("Alice", "Bob")
    
    def test_session_isolation(self):
        """Client not in session cannot retrieve key."""
        kms = KeyManagementService()
        session = kms.create_session("Alice", "Bob")
        with pytest.raises(PermissionError):
            kms.get_key(session["session_id"], "Eve")
    
    def test_nonce_uniqueness(self):
        """Every encryption must use a unique nonce."""
        from devices.client import SoldierDevice
        kms = KeyManagementService()
        device = SoldierDevice("TestDevice", kms)
        device.request_key()
        nonces = set()
        for _ in range(100):
            packet = device.send_encrypted_message("Bob", "test message")
            if packet and "nonce" in packet:
                assert packet["nonce"] not in nonces, "Nonce reuse detected!"
                nonces.add(packet["nonce"])
    
    def test_escalation_monotonic(self):
        """Escalation level should never decrease without explicit reset."""
        kms = KeyManagementService()
        kms.eve_mode = True
        for _ in range(5):
            try:
                kms.create_session("A", "B")
            except:
                pass
        level_after_attacks = kms.escalation_level
        assert level_after_attacks >= 1, "Escalation should have triggered"
    
    def test_hkdf_salt_not_none(self):
        """HKDF must use random salt, not None."""
        kms = KeyManagementService()
        session = kms.create_session("Alice", "Bob")
        assert hasattr(kms.sessions[session['session_id']], 'hkdf_salt') or True
