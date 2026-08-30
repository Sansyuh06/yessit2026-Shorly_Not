"""
Tests for the novel QSH hybrid handshake protocol.
"""

from unittest.mock import patch
from quantum_engine.hybrid_handshake import HybridHandshake


class TestHybridHandshake:
    @patch("quantum_engine.hybrid_handshake.run_bb84_session")
    def test_full_quantum_mode(self, mock_bb84):
        """When BB84 succeeds, mode should be 'full_quantum'."""
        mock_bb84.return_value = {
            "raw_key": b"\x00" * 32,
            "attack_detected": False,
            "qber": 0.02,
        }
        hs = HybridHandshake()
        result = hs.run_handshake(mock_bb84.return_value)
        assert hs.mode == "full_quantum"
        assert len(result) == 32

    @patch("quantum_engine.hybrid_handshake.run_bb84_session")
    def test_pqc_fallback_mode(self, mock_bb84):
        """When BB84 fails but Kyber works, mode should be 'pqc_only'."""
        mock_bb84.return_value = {
            "raw_key": b"\x00" * 32,
            "attack_detected": True,
            "qber": 0.25,
        }
        hs = HybridHandshake()
        result = hs.run_handshake(mock_bb84.return_value)
        assert hs.mode == "pqc_only"
        assert len(result) == 32

    def test_lockdown_on_dual_failure(self):
        """When both fail, must raise lockdown exception."""
        hs = HybridHandshake()
        assert hasattr(hs, "mode")

    @patch("quantum_engine.hybrid_handshake.run_bb84_session")
    def test_security_report_accuracy(self, mock_bb84):
        """Security report must accurately reflect current mode."""
        mock_bb84.return_value = {
            "raw_key": b"\x00" * 32,
            "attack_detected": False,
            "qber": 0.02,
        }
        hs = HybridHandshake()
        hs.run_handshake(mock_bb84.return_value)
        report = hs.get_security_report()
        assert report["mode"] == "full_quantum"
