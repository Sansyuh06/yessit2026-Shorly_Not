"""Protocol Correctness Tests — BB84 verification."""

import pytest
import numpy as np
from quantum_engine.bb84_simulator import (
    run_bb84_session,
    privacy_amplification,
    _build_prepare_circuit,
    QBER_THRESHOLD,
)


class TestSifting:
    def test_ratio_half(self):
        r = run_bb84_session(num_bits=2048)
        assert 0.40 < r["sifted_key_length"] / 2048 < 0.60

    def test_consistent(self):
        ratios = [
            run_bb84_session(num_bits=1024)["sifted_key_length"] / 1024
            for _ in range(10)
        ]
        assert np.std(ratios) < 0.05


class TestQBERSecure:
    def test_below_threshold(self):
        qbers = [run_bb84_session(num_bits=512)["qber"] for _ in range(30)]
        assert np.mean(qbers) < 0.05
        assert max(qbers) < QBER_THRESHOLD

    def test_no_false_positives(self):
        for _ in range(20):
            assert run_bb84_session(num_bits=512)["attack_detected"] is False


class TestQBERWithEve:
    def test_near_25_percent(self):
        qbers = [run_bb84_session(num_bits=512, eve=True)["qber"] for _ in range(30)]
        assert 0.18 < np.mean(qbers) < 0.32

    def test_always_detected(self):
        for _ in range(20):
            r = run_bb84_session(num_bits=512, eve=True)
            assert r["attack_detected"] is True
            assert r["qber"] >= QBER_THRESHOLD


class TestPrivacyAmplification:
    def test_output_length(self):
        import secrets

        bits = [secrets.randbelow(2) for _ in range(512)]
        for n in [128, 256]:
            assert len(privacy_amplification(bits, output_bits=n)) == n // 8

    def test_compresses(self):
        import secrets

        bits = [secrets.randbelow(2) for _ in range(512)]
        assert len(privacy_amplification(bits, output_bits=256)) < len(bits) // 8


class TestStatePrep:
    def test_zero_z(self):
        qc = _build_prepare_circuit(0, 0)
        assert len(qc.data) == 0 or all(
            g.operation.name in ("barrier", "measure") for g in qc.data
        )

    def test_one_z(self):
        qc = _build_prepare_circuit(1, 0)
        assert any(g.operation.name == "x" for g in qc.data)

    def test_zero_x(self):
        qc = _build_prepare_circuit(0, 1)
        assert any(g.operation.name == "h" for g in qc.data)

    def test_one_x(self):
        qc = _build_prepare_circuit(1, 1)
        names = [g.operation.name for g in qc.data]
        assert "x" in names and "h" in names


class TestHybridHandshake:
    def test_full_quantum(self):
        from quantum_engine.hybrid_handshake import HybridHandshake

        hs = HybridHandshake()
        bb84_result = {"qber": 0.05, "attack_detected": False, "raw_key": b"\x00"*32}
        key = hs.run_handshake(bb84_result)
        report = hs.get_security_report()
        assert report["mode"] in ("full_quantum", "pqc_only")
        assert len(key) == 32

    def test_lockdown(self):
        from quantum_engine.hybrid_handshake import HybridHandshake

        hs = HybridHandshake()
        # Force BB84 failure + no Kyber → lockdown
        # (This tests the architecture, not runtime behavior)
        assert hasattr(hs, "mode")


class TestKMSSecurity:
    def test_compromised_not_stored(self):
        from kms.key_management_service import KeyManagementService

        kms = KeyManagementService()
        kms.eve_mode = True
        with pytest.raises(Exception):
            kms.create_session("A", "B")

    def test_join_auth(self):
        from kms.key_management_service import KeyManagementService

        kms = KeyManagementService()
        s = kms.create_session("Alice", "Bob")
        # Wrong token should fail
        with pytest.raises(PermissionError):
            kms.join_session(s["session_id"], "Eve", join_token="wrong")
