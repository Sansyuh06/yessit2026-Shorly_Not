"""
Tests for ShorlyNot-QDS-T1 protocol implementation.
"""

import pytest
import numpy as np
from shorlynot_skeleton.qds.protocol import QdsT1Protocol
from shorlynot_skeleton.qds.encoding import PauliEncoding
from shorlynot_skeleton.qds.pauli import PauliCorrections
from shorlynot_skeleton.models import QuantumBackend


def test_pauli_encoding_eigenstates():
    # Z basis
    s0 = PauliEncoding.get_statevector(bit=0, basis=0)
    s1 = PauliEncoding.get_statevector(bit=1, basis=0)
    assert np.allclose(s0, [1.0, 0.0])
    assert np.allclose(s1, [0.0, 1.0])

    # X basis
    sp = PauliEncoding.get_statevector(bit=0, basis=1)
    sm = PauliEncoding.get_statevector(bit=1, basis=1)
    assert np.allclose(sp, [1.0 / np.sqrt(2), 1.0 / np.sqrt(2)])
    assert np.allclose(sm, [1.0 / np.sqrt(2), -1.0 / np.sqrt(2)])


def test_pauli_corrections_lookup():
    assert PauliCorrections.get_gate_name(0, 0) == "I"
    assert PauliCorrections.get_gate_name(0, 1) == "X"
    assert PauliCorrections.get_gate_name(1, 0) == "Z"
    assert PauliCorrections.get_gate_name(1, 1) == "XZ"


def test_honest_qds_sign_and_verify_accept():
    protocol = QdsT1Protocol(p0=0.02, default_delta=0.01)
    dummy_hash = "abcdef0123456789" * 4
    
    bundle = protocol.sign(
        payload_hash=dummy_hash,
        key_id="alice-key-1",
        n_checks=64,
        L=128,
        backend=QuantumBackend.SIM
    )
    
    assert bundle.profile == "T1"
    assert len(bundle.correction_bits) == 64
    assert len(bundle.bases) == 128

    result = protocol.verify(bundle=bundle, verifier_id="bob", delta=0.01, p0=0.02)
    assert result.candidate_accepted is True
    assert result.mismatch_rate <= result.tau
    assert result.tau >= 0.20


def test_random_forgery_qds_reject():
    protocol = QdsT1Protocol(p0=0.02, default_delta=0.01)
    dummy_hash = "1234567890abcdef" * 4
    
    bundle = protocol.sign(
        payload_hash=dummy_hash,
        key_id="alice-key-1",
        n_checks=64,
        L=128
    )

    # Forger provides random uncorrelated syndromes
    random_syndromes = [[int(np.random.randint(0, 2)), int(np.random.randint(0, 2))] for _ in range(64)]
    bundle.correction_bits = random_syndromes

    result = protocol.verify(bundle=bundle, verifier_id="bob", delta=0.01, p0=0.02)
    # Random guessers should experience mismatch around 0.50 >> tau (0.210)
    assert result.mismatch_rate > result.tau
    assert result.candidate_accepted is False
