"""
Qiskit Aer Quantum Circuit and Simulation Engine for ShorlyNot-QDS-T1.
SIH 2026 PS 26141.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister

from shorlynot_skeleton.qds.encoding import PauliEncoding
from shorlynot_skeleton.qds.pauli import PauliCorrections


class QiskitAerEngine:
    """
    Quantum circuit builder and executor for teleportation-based QDS (ShorlyNot-QDS-T1).
    """

    def __init__(self, p0: float = 0.02):
        self.p0 = p0

    @staticmethod
    def build_teleportation_circuit(bit: int, basis: int) -> QuantumCircuit:
        """
        Construct a complete 3-qubit Qiskit teleportation circuit for ShorlyNot-QDS-T1.
        Qubit 0: Message qubit |psi(b, beta)>
        Qubit 1: Alice's entangled qubit (half of Bell pair |Phi+>)
        Qubit 2: Bob's entangled qubit (receiver)
        """
        qr = QuantumRegister(3, 'q')
        cr = ClassicalRegister(3, 'c')
        qc = QuantumCircuit(qr, cr)

        # Step 1: Prepare message state |psi(b, beta)> on q[0]
        if basis == 0:  # Z basis
            if bit == 1:
                qc.x(qr[0])
        else:  # X basis
            if bit == 0:
                qc.h(qr[0])  # |+>
            else:
                qc.x(qr[0])
                qc.h(qr[0])  # |->

        # Step 2: Prepare Bell pair |Phi+> on q[1] and q[2]
        qc.h(qr[1])
        qc.cx(qr[1], qr[2])

        # Step 3: Alice Bell-basis measurement on (q[0], q[1])
        qc.cx(qr[0], qr[1])
        qc.h(qr[0])
        qc.measure(qr[0], cr[0])  # m1
        qc.measure(qr[1], cr[1])  # m2

        # Step 4: Bob applies Pauli correction on q[2] based on (m1, m2)
        qc.x(qr[2]).c_if(cr[1], 1)
        qc.z(qr[2]).c_if(cr[0], 1)

        # Step 5: Bob basis rotation if basis == X (beta == 1)
        if basis == 1:
            qc.h(qr[2])

        # Step 6: Bob projective measurement in Z basis
        qc.measure(qr[2], cr[2])

        return qc

    def generate_bell_measurement(self) -> Tuple[int, int]:
        """
        Simulate Alice's Bell-basis measurement on (Message ⊗ A).
        Yields (m1, m2) uniformly in {00, 01, 10, 11}.
        """
        m1 = int(np.random.randint(0, 2))
        m2 = int(np.random.randint(0, 2))
        return m1, m2

    def simulate_bob_verification(
        self,
        bit: int,
        basis: int,
        true_syndrome: Tuple[int, int],
        provided_syndrome: Tuple[int, int],
        inject_noise: bool = True
    ) -> int:
        """
        Simulate Bob's verification of a check qubit.
        """
        # 1. Message state
        state = PauliEncoding.get_statevector(bit, basis)

        # 2. Bob's state before correction is U_true^\dagger |psi>
        m1_t, m2_t = true_syndrome
        U_true = PauliCorrections.get_unitary_matrix(m1_t, m2_t)
        U_true_dag = U_true.conj().T
        bob_received_state = np.dot(U_true_dag, state)

        # 3. Bob applies provided correction U_provided
        m1_p, m2_p = provided_syndrome
        U_provided = PauliCorrections.get_unitary_matrix(m1_p, m2_p)
        corrected_state = np.dot(U_provided, bob_received_state)

        # 4. If basis is X (beta == 1), apply Hadamard
        if basis == 1:
            projected_state = PauliCorrections.apply_hadamard(corrected_state)
        else:
            projected_state = corrected_state

        # 5. Probability of measuring |0> vs |1>
        prob_0 = float(np.abs(projected_state[0]) ** 2)
        prob_1 = float(np.abs(projected_state[1]) ** 2)
        total_p = prob_0 + prob_1
        prob_0 /= total_p
        prob_1 /= total_p

        # 6. Channel/hardware depolarizing noise floor (p0)
        if inject_noise and self.p0 > 0:
            prob_0 = (1.0 - self.p0) * prob_0 + (self.p0 / 2.0)
            prob_1 = 1.0 - prob_0

        measured_bit = int(np.random.choice([0, 1], p=[prob_0, prob_1]))
        return measured_bit
