"""
Tests for the novel QSH hybrid handshake protocol.
"""
import pytest
from quantum_engine.hybrid_handshake import HybridHandshake

class TestHybridHandshake:
    
    def test_full_quantum_mode(self):
        """When BB84 succeeds, mode should be 'full_quantum'."""
        hs = HybridHandshake()
        result = {"raw_key": b'\x00' * 32, "attack_detected": False, "qber": 0.02}
        key = hs.run_handshake(result)
        assert hs.mode == "full_quantum"
        assert len(key) == 32
    
    def test_pqc_fallback_mode(self):
        """When BB84 fails but Kyber works, mode should be 'pqc_only'."""
        hs = HybridHandshake()
        result = {"raw_key": b'\x00' * 32, "attack_detected": True, "qber": 0.25}
        key = hs.run_handshake(result)
        assert hs.mode == "pqc_only"
        assert len(key) == 32
    
    def test_lockdown_on_dual_failure(self):
        """When both fail, must raise lockdown exception."""
        hs = HybridHandshake()
        result = {"raw_key": b'\x00' * 32, "attack_detected": True, "qber": 0.25}
        with pytest.raises(Exception, match="DUAL FAILURE"):
            hs.run_handshake(result, use_kyber=False)
    
    def test_security_report_accuracy(self):
        """Security report must accurately reflect current mode."""
        hs = HybridHandshake()
        result = {"raw_key": b'\x00' * 32, "attack_detected": False, "qber": 0.02}
        hs.run_handshake(result)
        report = hs.get_security_report()
        assert report["mode"] == "full_quantum"
        assert report["bb84_used"] is True
        assert report["kyber_used"] is True
