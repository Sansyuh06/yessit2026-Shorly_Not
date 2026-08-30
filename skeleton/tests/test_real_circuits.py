"""
Tests for real Qiskit Aer circuit execution in ShorlyNot-QDS-T1.
Validates that teleportation circuits actually run on AerSimulator,
not random number generators.
"""

import pytest
from shorlynot_skeleton.engines.qiskit_aer import QiskitAerEngine


class TestRealCircuits:
    """Verify all quantum operations go through real Qiskit Aer circuits."""

    def test_teleportation_z_basis_bit0(self):
        """Teleport |0> in Z basis — Bob must measure 0."""
        engine = QiskitAerEngine()
        result = engine.run_teleportation_circuit(bit=0, basis=0, shots=1)
        assert result["bob_bit"] == 0, f"Bob should measure 0 for |0>, got {result['bob_bit']}"

    def test_teleportation_z_basis_bit1(self):
        """Teleport |1> in Z basis — Bob must measure 1."""
        engine = QiskitAerEngine()
        result = engine.run_teleportation_circuit(bit=1, basis=0, shots=1)
        assert result["bob_bit"] == 1, f"Bob should measure 1 for |1>, got {result['bob_bit']}"

    def test_teleportation_x_basis_bit0(self):
        """Teleport |+> in X basis — Bob measures in X, should get 0."""
        engine = QiskitAerEngine()
        result = engine.run_teleportation_circuit(bit=0, basis=1, shots=1)
        assert result["bob_bit"] == 0, f"Bob should measure 0 for |+> in X basis, got {result['bob_bit']}"

    def test_teleportation_x_basis_bit1(self):
        """Teleport |-> in X basis — Bob measures in X, should get 1."""
        engine = QiskitAerEngine()
        result = engine.run_teleportation_circuit(bit=1, basis=1, shots=1)
        assert result["bob_bit"] == 1, f"Bob should measure 1 for |-> in X basis, got {result['bob_bit']}"

    def test_bell_measurement_from_real_circuit(self):
        """generate_bell_measurement must return valid (m1,m2) from real circuit."""
        engine = QiskitAerEngine()
        m1, m2 = engine.generate_bell_measurement()
        assert m1 in (0, 1), f"m1 must be 0 or 1, got {m1}"
        assert m2 in (0, 1), f"m2 must be 0 or 1, got {m2}"

    def test_circuit_has_real_gates(self):
        """The built circuit must contain H, CX, and measure instructions."""
        qc = QiskitAerEngine.build_teleportation_circuit(0, 0)
        gate_names = [inst.operation.name for inst in qc.data]
        assert "h" in gate_names, "Circuit must contain Hadamard gate"
        assert "cx" in gate_names, "Circuit must contain CNOT gate"
        assert "measure" in gate_names, "Circuit must contain measurement"

    def test_full_verify_via_circuit(self):
        """verify_via_circuit runs end-to-end real circuit and confirms match."""
        engine = QiskitAerEngine()
        for bit in [0, 1]:
            for basis in [0, 1]:
                result = engine.verify_via_circuit(bit, basis)
                assert result["match"] is True, (
                    f"Noiseless teleportation must always match: "
                    f"bit={bit}, basis={basis}, got bob_bit={result['bob_bit']}"
                )

    def test_sign_uses_real_circuits(self):
        """Sign must populate circuit_verification_results from real Aer runs."""
        from shorlynot_skeleton.qds.protocol import QdsT1Protocol
        protocol = QdsT1Protocol()
        bundle = protocol.sign(
            payload_hash="abcdef0123456789" * 4,
            key_id="alice-key-1",
            n_checks=8,  # small for speed
            L=16
        )
        # Check that real circuit results are recorded
        transcript = bundle.measurement_transcript
        assert transcript.get("real_circuits") is True
        assert transcript.get("circuit_backend") == "qiskit_aer"
        results = transcript.get("circuit_verification_results", [])
        assert len(results) == 8
        for r in results:
            assert "m1" in r and "m2" in r and "bob_bit" in r
