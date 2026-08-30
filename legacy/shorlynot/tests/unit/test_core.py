"""Unit tests for QKD protocols, policy, crypto, and evidence chain.

Covers PRD §31 unit test requirements.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── BB84 Tests ──────────────────────────────────────────────

class TestBB84:
    def test_basis_mapping(self):
        """BB84 basis mapping: 0=Z, 1=X (Hadamard)."""
        from packages.qkd.bb84 import build_bb84_circuits

        circuits = build_bb84_circuits([0, 1, 0, 1], [0, 0, 1, 1], [0, 0, 0, 0])
        assert len(circuits) == 4
        # Verify circuits have correct structure
        for qc in circuits:
            assert qc.num_qubits == 1
            assert qc.num_clbits == 1

    def test_sifting(self):
        """Matching bases keep bits, mismatched discard."""
        from packages.qkd.bb84 import sift_key

        alice = [0, 1, 0, 1]
        a_bases = [0, 0, 1, 1]
        b_bases = [0, 1, 1, 0]
        bob_meas = [0, 1, 0, 1]

        sa, sb, idx = sift_key(alice, a_bases, b_bases, bob_meas)
        assert len(sa) == 2  # Only bases [0]==0,0 and [2]==1,1 match
        assert idx == [0, 2]

    def test_qber_calculation_no_errors(self):
        """QBER should be 0 with identical sifted keys."""
        from packages.qkd.bb84 import calculate_qber

        qber, errors, compared = calculate_qber([0, 1, 0, 1], [0, 1, 0, 1])
        assert qber == 0.0
        assert errors == 0
        assert compared == 4

    def test_qber_calculation_with_errors(self):
        """QBER should reflect actual error count."""
        from packages.qkd.bb84 import calculate_qber

        qber, errors, compared = calculate_qber([0, 1, 0, 1], [1, 1, 0, 0])
        assert qber == 0.5
        assert errors == 2

    def test_qber_empty_raises(self):
        """Empty sifted key raises InsufficientKeyMaterialError."""
        from packages.common.errors import InsufficientKeyMaterialError
        from packages.qkd.bb84 import calculate_qber

        with pytest.raises(InsufficientKeyMaterialError):
            calculate_qber([], [])

    def test_full_protocol_no_attack(self):
        """Complete BB84 run without attack should produce low QBER."""
        from packages.qkd.bb84 import run_bb84_protocol

        result = run_bb84_protocol(num_qubits=200)
        assert result.qber is not None
        assert result.qber < 0.05  # No attack should give ~0% QBER
        assert result.sifted_key_length > 0
        assert result.raw_result_hash is not None

    def test_full_protocol_with_attack(self):
        """BB84 with 100% intercept-resend should produce ~25% QBER."""
        from packages.qkd.bb84 import run_bb84_protocol

        result = run_bb84_protocol(num_qubits=500, attack_probability=1.0)
        assert result.qber is not None
        assert result.qber > 0.1  # Should be near 25%
        assert result.theoretical_qber == 0.25

    def test_eve_information_estimate(self):
        """Eve information should increase with QBER."""
        from packages.qkd.bb84 import estimate_eve_information

        e0 = estimate_eve_information(0.0)
        e5 = estimate_eve_information(0.05)
        e25 = estimate_eve_information(0.25)
        assert e0 == 0.0
        assert e5 > 0
        assert e25 > e5


# ── B92 Tests ───────────────────────────────────────────────

class TestB92:
    def test_conclusive_extraction(self):
        """B92 conclusive extraction should filter correctly."""
        from packages.qkd.b92 import extract_conclusive_results

        alice = [0, 1, 0, 1]
        bob_bases = [0, 1, 0, 1]
        bob_results = [1, 1, 0, 0]  # 1 = conclusive

        ca, cb, idx = extract_conclusive_results(alice, bob_bases, bob_results)
        assert len(ca) == 2
        assert cb[0] == 0  # X-basis (0) gave |−⟩ → bit 0
        assert cb[1] == 1  # Z-basis (1) gave |1⟩ → bit 1

    def test_full_protocol(self):
        """B92 protocol should complete and produce results."""
        from packages.qkd.b92 import run_b92_protocol

        result = run_b92_protocol(num_qubits=200)
        assert result.transmitted_qubits == 200
        assert result.conclusive_measurements >= 0
        assert result.conclusive_rate >= 0


# ── E91 Tests ───────────────────────────────────────────────

class TestE91:
    def test_correlation_calculation(self):
        """E91 correlation should be computed from observed data."""
        from packages.qkd.e91 import calculate_correlation

        # Perfect correlations
        alice_r = [0, 0, 1, 1]
        bob_r = [0, 0, 1, 1]
        alice_s = [0, 0, 0, 0]
        bob_s = [0, 0, 0, 0]

        corr = calculate_correlation(alice_r, bob_r, alice_s, bob_s, 0, 0)
        assert corr == 1.0  # All same

    def test_chsh_calculation(self):
        """CHSH S value should be computed from correlations."""
        from packages.qkd.e91 import calculate_chsh

        correlations = {
            "E(0,0)": 0.7071,
            "E(0,1)": -0.7071,
            "E(1,0)": 0.7071,
            "E(1,1)": 0.7071,
        }
        s = calculate_chsh(correlations)
        assert abs(s - 2.8284) < 0.01  # ≈ 2√2

    def test_chsh_security_evaluation(self):
        """CHSH security evaluation should classify correctly."""
        from packages.qkd.e91 import evaluate_chsh_security

        assert evaluate_chsh_security(2.5) == "secure"
        assert evaluate_chsh_security(1.5) == "compromised"
        assert evaluate_chsh_security(2.0) == "compromised"  # ≤ threshold

    def test_full_protocol(self):
        """E91 protocol should produce CHSH S value."""
        from packages.qkd.e91 import run_e91_protocol

        result = run_e91_protocol(num_pairs=200)
        assert result.chsh_s is not None
        assert -4 <= result.chsh_s <= 4


# ── Finite-Key Tests ────────────────────────────────────────

class TestFiniteKey:
    def test_qber_confidence_bound(self):
        """Confidence bound should be above observed QBER."""
        from packages.qkd.finite_key import qber_confidence_upper_bound

        bound = qber_confidence_upper_bound(0.05, 1000)
        assert bound > 0.05
        assert bound < 0.5

    def test_small_sample_insecure(self):
        """Small sample with moderate QBER should be insecure."""
        from packages.qkd.finite_key import estimate_secure_key_length

        result = estimate_secure_key_length(50, 0.05)
        # Very small sample — finite-key penalty dominates
        assert result.estimated_secret_bits == 0 or not result.secure

    def test_large_sample_secure(self):
        """Large sample with low QBER should be secure."""
        from packages.qkd.finite_key import estimate_secure_key_length

        result = estimate_secure_key_length(1000000, 0.02)
        assert result.secure
        assert result.estimated_secret_bits > 0

    def test_compare_key_lengths(self):
        """Different key lengths should show finite-key effect."""
        from packages.qkd.finite_key import compare_key_lengths

        results = compare_key_lengths(0.03)
        assert len(results) == 3
        # Larger keys should have more secure bits
        bits = [r.estimated_secret_bits for r in results]
        assert bits[-1] >= bits[0]


# ── Reconciliation Tests ────────────────────────────────────

class TestReconciliation:
    def test_identical_keys(self):
        """No errors → no corrections needed."""
        from packages.qkd.reconciliation import cascade_reconciliation

        key = [0, 1, 0, 1, 0, 1, 0, 1] * 4
        result = cascade_reconciliation(key, list(key))
        assert result.corrected_error_count == 0
        assert result.remaining_error_count == 0

    def test_error_correction(self):
        """Should correct at least some errors."""
        from packages.qkd.reconciliation import cascade_reconciliation

        alice = [0, 1, 0, 1, 0, 1, 0, 1] * 8
        bob = list(alice)
        # Introduce 5% errors
        import random
        random.seed(42)
        for i in random.sample(range(len(bob)), len(bob) // 20):
            bob[i] ^= 1

        result = cascade_reconciliation(alice, bob)
        assert result.corrected_error_count > 0
        assert result.disclosed_bits > 0


# ── Privacy Amplification Tests ─────────────────────────────

class TestPrivacyAmplification:
    def test_output_length_bound(self):
        """Output must not exceed extractable length."""
        from packages.qkd.privacy_amplification import (
            calculate_extractable_length,
            privacy_amplification,
        )

        key = [0, 1] * 100
        max_len = calculate_extractable_length(200, 150.0)
        assert max_len <= 150

        amplified, ledger = privacy_amplification(key, 150.0)
        assert len(amplified) <= max_len

    def test_entropy_ledger(self):
        """Entropy ledger should track all stages."""
        from packages.qkd.privacy_amplification import build_entropy_ledger

        ledger = build_entropy_ledger(
            raw_key_length=1000,
            sifted_key_length=500,
            reconciled_key_length=480,
            final_key_length=200,
            raw_min_entropy=1000.0,
            sifted_min_entropy=450.0,
            reconciled_min_entropy=400.0,
            final_min_entropy=200.0,
        )
        assert len(ledger) == 4
        assert ledger[0].stage.value == "raw"
        assert ledger[3].stage.value == "privacy_amplified"


# ── Lease Signing Tests ─────────────────────────────────────

class TestLeaseSigning:
    def test_sign_and_verify(self):
        """Ed25519 sign → verify round-trip."""
        from packages.common.schemas import QKBNLLeasePayload
        from packages.crypto.lease_signer import LeaseSigner

        priv, pub = LeaseSigner.generate_keypair()
        signer = LeaseSigner(private_key=priv)

        payload = QKBNLLeasePayload(
            lease_id="QKBNL-TEST123",
            device_id="device-1",
            qkd_session_id="session-1",
            key_fingerprint="abc123",
            issued_at="2024-01-01T00:00:00Z",
            expires_at="2024-01-01T00:01:00Z",
            nonce="deadbeef" * 8,
            sequence_number=1,
            policy_version="1.0.0",
        )

        sig = signer.sign_lease(payload)
        assert signer.verify_lease(payload, sig)

    def test_tampered_payload_fails(self):
        """Tampered payload should fail verification."""
        from packages.common.schemas import QKBNLLeasePayload
        from packages.crypto.lease_signer import LeaseSigner

        priv, pub = LeaseSigner.generate_keypair()
        signer = LeaseSigner(private_key=priv)

        payload = QKBNLLeasePayload(
            lease_id="QKBNL-TEST123",
            device_id="device-1",
            qkd_session_id="session-1",
            key_fingerprint="abc123",
            issued_at="2024-01-01T00:00:00Z",
            expires_at="2024-01-01T00:01:00Z",
            nonce="deadbeef" * 8,
            sequence_number=1,
            policy_version="1.0.0",
        )

        sig = signer.sign_lease(payload)

        # Tamper
        tampered = payload.model_copy(update={"sequence_number": 999})
        assert not signer.verify_lease(tampered, sig)

    def test_canonical_json_deterministic(self):
        """Canonical JSON must be deterministic."""
        from packages.common.schemas import QKBNLLeasePayload

        p1 = QKBNLLeasePayload(
            lease_id="QKBNL-A",
            device_id="d1",
            qkd_session_id="s1",
            key_fingerprint="fp",
            issued_at="2024-01-01T00:00:00Z",
            expires_at="2024-01-01T00:01:00Z",
            nonce="nonce1",
            sequence_number=1,
            policy_version="1.0.0",
        )
        assert p1.canonical_json() == p1.canonical_json()


# ── Policy State Machine Tests ──────────────────────────────

class TestPolicyStateMachine:
    def test_valid_transitions(self):
        """Full security cycle should succeed."""
        from packages.common.enums import PolicyState
        from packages.policy.state_machine import PolicyStateMachine

        sm = PolicyStateMachine()
        sm.transition(PolicyState.SECURE, "ok")
        sm.transition(PolicyState.COMPROMISED, "attack")
        sm.transition(PolicyState.REVOKING, "rev")
        sm.transition(PolicyState.ISOLATED, "iso")
        sm.transition(PolicyState.PQC_RECOVERY, "pqc")
        sm.transition(PolicyState.RESTORING, "rest")
        sm.transition(PolicyState.SECURE, "done")
        assert sm.state == PolicyState.SECURE

    def test_invalid_transition_raises(self):
        """Invalid transitions must raise InvalidPolicyTransitionError."""
        from packages.common.enums import PolicyState
        from packages.common.errors import InvalidPolicyTransitionError
        from packages.policy.state_machine import PolicyStateMachine

        sm = PolicyStateMachine()
        sm.transition(PolicyState.SECURE, "ok")

        with pytest.raises(InvalidPolicyTransitionError):
            sm.transition(PolicyState.ISOLATED, "invalid")

    def test_history_recording(self):
        """Transitions should be recorded in history."""
        from packages.common.enums import PolicyState
        from packages.policy.state_machine import PolicyStateMachine

        sm = PolicyStateMachine()
        sm.transition(PolicyState.SECURE, "ok")
        sm.transition(PolicyState.DEGRADED, "warn")
        assert len(sm.history) == 2
        assert sm.history[0].from_state == PolicyState.INITIALIZING


# ── Evidence Chain Tests ────────────────────────────────────

class TestEvidenceChain:
    def test_chain_integrity(self):
        """Valid chain should pass verification."""
        from packages.common.enums import ExecutionMode
        from packages.common.evidence import EvidenceChain

        chain = EvidenceChain()
        chain.append("E1", ExecutionMode.SIMULATION, "test", {"a": 1})
        chain.append("E2", ExecutionMode.SIMULATION, "test", {"b": 2})
        chain.append("E3", ExecutionMode.SIMULATION, "test", {"c": 3})

        valid, idx = chain.verify()
        assert valid
        assert idx is None

    def test_tampered_chain_fails(self):
        """Modified record should fail verification."""
        from packages.common.enums import ExecutionMode
        from packages.common.evidence import EvidenceChain

        chain = EvidenceChain()
        chain.append("E1", ExecutionMode.SIMULATION, "test", {"a": 1})
        chain.append("E2", ExecutionMode.SIMULATION, "test", {"b": 2})

        # Tamper with record
        chain._records[0]["payload_hash"] = "tampered"

        valid, idx = chain.verify()
        assert not valid
        assert idx == 0

    def test_genesis_hash(self):
        """First record should have GENESIS as previous_hash."""
        from packages.common.enums import ExecutionMode
        from packages.common.evidence import EvidenceChain

        chain = EvidenceChain()
        chain.append("E1", ExecutionMode.SIMULATION, "test", {})
        assert chain.records[0]["previous_hash"] == "GENESIS"


# ── CRC Tests ──────────────────────────────────────────────

class TestCRC:
    def test_crc16_ccitt(self):
        """CRC-16/CCITT-FALSE known test vector."""
        from apps.arduino_bridge.crc import crc16_ccitt_false

        # Standard test: "123456789" → 0x29B1
        result = crc16_ccitt_false(b"123456789")
        assert result == 0x29B1

    def test_frame_crc_validation(self):
        """Valid frame CRC should pass."""
        from apps.arduino_bridge.crc import compute_frame_crc, validate_frame_crc

        payload = "QTEL,1,42,13520,713,0,1,0,0"
        crc = compute_frame_crc(f"{payload},0")  # dummy CRC to split
        # Reconstruct with correct CRC
        frame = f"{payload},{crc}"
        assert validate_frame_crc(frame)


# ── Optical Calibration Tests ──────────────────────────────

class TestOpticalCalibration:
    def test_normalize_intensity(self):
        """Intensity normalization should clamp to [0,1]."""
        from apps.arduino_bridge.parser import normalize_intensity

        assert normalize_intensity(500, 0, 1000) == 0.5
        assert normalize_intensity(0, 0, 1000) == 0.0
        assert normalize_intensity(1000, 0, 1000) == 1.0
        assert normalize_intensity(1500, 0, 1000) == 1.0  # Clamped

    def test_calibration_invalid(self):
        """bright_level <= dark_level should raise."""
        from apps.arduino_bridge.parser import normalize_intensity
        from packages.common.errors import CalibrationInvalidError

        with pytest.raises(CalibrationInvalidError):
            normalize_intensity(500, 100, 100)

        with pytest.raises(CalibrationInvalidError):
            normalize_intensity(500, 200, 100)
