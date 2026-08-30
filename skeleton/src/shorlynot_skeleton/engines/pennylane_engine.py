"""
PennyLane Quantum Circuit and Simulation Engine for ShorlyNot-QDS-T1.
SIH 2026 PS 26141.

Provides PennyLane teleportation circuits on default.qubit alongside Qiskit Aer,
satisfying the dual-engine architecture specification.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pennylane as qml

from shorlynot_skeleton.qds.encoding import PauliEncoding
from shorlynot_skeleton.qds.pauli import PauliCorrections


class PennyLaneEngine:
    """
    PennyLane engine for ShorlyNot-QDS-T1 teleportation circuits.
    Executes 3-qubit teleportation circuits on PennyLane's default.qubit simulator device.
    """

    def __init__(self, p0: float = 0.02):
        self.p0 = p0

    def run_teleportation_circuit(self, bit: int, basis: int, shots: int = 1) -> Dict[str, Any]:
        """
        Build and execute a complete teleportation circuit on PennyLane default.qubit.
        Returns dict with 'm1', 'm2' (Alice's Bell measurement) and 'bob_bit'.
        """
        dev = qml.device("default.qubit", wires=3)

        def circuit():
            # Step 1: Prepare message state |psi(b, beta)> on wire 0
            if basis == 0:  # Z basis
                if bit == 1:
                    qml.PauliX(wires=0)
            else:  # X basis
                if bit == 0:
                    qml.Hadamard(wires=0)  # |+>
                else:
                    qml.PauliX(wires=0)
                    qml.Hadamard(wires=0)  # |->

            # Step 2: Prepare Bell pair |Phi+> on wires 1 and 2
            qml.Hadamard(wires=1)
            qml.CNOT(wires=[1, 2])

            # Step 3: Alice Bell-basis measurement on (0, 1)
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=0)
            m1 = qml.measure(0)
            m2 = qml.measure(1)

            # Step 4: Bob applies Pauli correction on wire 2 based on (m1, m2)
            qml.cond(m2, qml.PauliX)(wires=2)
            qml.cond(m1, qml.PauliZ)(wires=2)

            # Step 5: Bob basis rotation if basis == X
            if basis == 1:
                qml.Hadamard(wires=2)

            # Step 6: Sample all wires
            return qml.sample(wires=[0, 1, 2])

        qnode = qml.QNode(circuit, dev, shots=shots)
        raw_res = qnode()
        arr = np.array(raw_res).squeeze()

        # If multiple shots, take the first shot
        if arr.ndim > 1:
            arr = arr[0]

        m1_val = int(arr[0])
        m2_val = int(arr[1])
        bob_val = int(arr[2])

        return {"m1": m1_val, "m2": m2_val, "bob_bit": bob_val}

    def generate_bell_measurement(self) -> Tuple[int, int]:
        """
        Generate Alice's Bell-basis measurement outcomes (m1, m2) via PennyLane circuit.
        """
        bit = int(np.random.randint(0, 2))
        basis = int(np.random.randint(0, 2))
        result = self.run_teleportation_circuit(bit, basis, shots=1)
        return result["m1"], result["m2"]

    def simulate_bob_verification(
        self,
        bit: int,
        basis: int,
        true_syndrome: Tuple[int, int],
        provided_syndrome: Tuple[int, int],
        inject_noise: bool = True
    ) -> int:
        """
        Bob verification with PennyLane engine (statevector Born-rule evaluation).
        """
        state = PauliEncoding.get_statevector(bit, basis)
        m1_t, m2_t = true_syndrome
        U_true = PauliCorrections.get_unitary_matrix(m1_t, m2_t)
        bob_received_state = np.dot(U_true.conj().T, state)

        m1_p, m2_p = provided_syndrome
        U_provided = PauliCorrections.get_unitary_matrix(m1_p, m2_p)
        corrected_state = np.dot(U_provided, bob_received_state)

        if basis == 1:
            projected_state = PauliCorrections.apply_hadamard(corrected_state)
        else:
            projected_state = corrected_state

        prob_0 = float(np.abs(projected_state[0]) ** 2)
        prob_1 = float(np.abs(projected_state[1]) ** 2)
        total_p = prob_0 + prob_1
        prob_0 /= total_p
        prob_1 /= total_p

        if inject_noise and self.p0 > 0:
            prob_0 = (1.0 - self.p0) * prob_0 + (self.p0 / 2.0)
            prob_1 = 1.0 - prob_0

        return int(np.random.choice([0, 1], p=[prob_0, prob_1]))
