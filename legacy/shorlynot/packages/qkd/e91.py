"""E91 (Ekert 1991) QKD engine using entangled Bell pairs and CHSH inequality.

Creates |Φ+⟩ Bell pairs and distributes one qubit to Alice and one to Bob.
Alice and Bob each measure in randomly selected bases. CHSH S value is
calculated from observed measurement correlations — never hardcoded.

Security criterion (PRD §9):
    |S| > configured_chsh_threshold → potentially quantum-correlated
    |S| ≤ configured_chsh_threshold → CHSH violation lost
"""

from __future__ import annotations

import hashlib
import json
import math
import secrets
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from packages.common.enums import ExecutionMode, QKDProtocol
from packages.common.errors import QuantumResultInvalidError


# E91 measurement angles (in radians)
# Alice: 0, π/8, π/4
# Bob: π/8, π/4, 3π/8
ALICE_ANGLES = [0.0, math.pi / 8, math.pi / 4]
BOB_ANGLES = [math.pi / 8, math.pi / 4, 3 * math.pi / 8]

# Basis pair indices for CHSH: (alice_setting, bob_setting)
# S = E(a1,b1) - E(a1,b2) + E(a2,b1) + E(a2,b2)
# Using settings: a1=0, a2=π/8, b1=π/8, b2=π/4
CHSH_PAIRS = [
    (0, 0),  # a1=0,   b1=π/8      → E(a1,b1)
    (0, 1),  # a1=0,   b2=π/4      → E(a1,b2)
    (1, 0),  # a2=π/8, b1=π/8      → E(a2,b1)
    (1, 1),  # a2=π/8, b2=π/4      → E(a2,b2)
]

# Key generation pairs: where Alice and Bob use the same angle
KEY_GEN_PAIRS = [(1, 0), (2, 1)]  # Alice π/8 = Bob π/8, Alice π/4 = Bob π/4


@dataclass
class E91Result:
    """Complete E91 protocol execution result."""

    protocol: QKDProtocol = QKDProtocol.E91
    num_pairs: int = 0
    alice_settings: list[int] = field(default_factory=list)
    bob_settings: list[int] = field(default_factory=list)
    alice_results: list[int] = field(default_factory=list)
    bob_results: list[int] = field(default_factory=list)
    correlations: dict[str, float] = field(default_factory=dict)
    chsh_s: Optional[float] = None
    chsh_s_theoretical: float = 2 * math.sqrt(2)
    sifted_alice: list[int] = field(default_factory=list)
    sifted_bob: list[int] = field(default_factory=list)
    sifted_key_length: int = 0
    qber: Optional[float] = None
    error_count: int = 0
    backend_name: str = "aer_simulator"
    shots: int = 1
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    raw_result_hash: Optional[str] = None
    chsh_threshold: float = 2.0
    security_evaluation: str = "unknown"


def create_bell_pair_circuit() -> QuantumCircuit:
    """Create a |Φ+⟩ = (|00⟩ + |11⟩)/√2 Bell state."""
    qc = QuantumCircuit(2, name="bell_phi_plus")
    qc.h(0)
    qc.cx(0, 1)
    return qc


def configure_measurement_basis(
    bell_circuit: QuantumCircuit,
    alice_angle: float,
    bob_angle: float,
) -> QuantumCircuit:
    """Add measurement in rotated bases to a Bell pair circuit.

    Applies Ry(-2θ) rotations to rotate measurement basis, then measures.
    """
    qc = bell_circuit.copy()
    qc.add_register(qc._create_creg(2, "c"))

    qc.barrier()

    # Alice's measurement rotation (qubit 0)
    if alice_angle != 0.0:
        qc.ry(-2 * alice_angle, 0)

    # Bob's measurement rotation (qubit 1)
    if bob_angle != 0.0:
        qc.ry(-2 * bob_angle, 1)

    qc.measure([0, 1], [0, 1])
    return qc


def _build_e91_circuits(
    num_pairs: int,
    alice_settings: list[int],
    bob_settings: list[int],
) -> list[QuantumCircuit]:
    """Build measurement circuits for all entangled pairs."""
    circuits = []
    for i in range(num_pairs):
        bell = create_bell_pair_circuit()
        a_angle = ALICE_ANGLES[alice_settings[i]]
        b_angle = BOB_ANGLES[bob_settings[i]]

        qc = QuantumCircuit(2, 2, name=f"e91_pair{i}")
        # Create Bell pair
        qc.h(0)
        qc.cx(0, 1)
        qc.barrier()

        # Apply measurement rotations
        if a_angle != 0.0:
            qc.ry(-2 * a_angle, 0)
        if b_angle != 0.0:
            qc.ry(-2 * b_angle, 1)

        qc.measure([0, 1], [0, 1])
        circuits.append(qc)

    return circuits


def execute_e91(
    circuits: list[QuantumCircuit],
    shots: int = 1,
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> tuple[list[dict[str, int]], str]:
    """Execute E91 circuits on simulator."""
    if execution_mode == ExecutionMode.REAL:
        raise NotImplementedError("Real QPU E91 not yet implemented.")

    simulator = AerSimulator()
    transpiled = transpile(circuits, simulator)
    job = simulator.run(transpiled, shots=shots)
    result = job.result()

    raw_data = json.dumps(
        [result.get_counts(i) for i in range(len(circuits))],
        sort_keys=True,
    )
    raw_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    all_counts = []
    for i in range(len(circuits)):
        counts = result.get_counts(i)
        if not counts:
            raise QuantumResultInvalidError(f"Empty counts for E91 circuit {i}")
        all_counts.append(counts)

    return all_counts, raw_hash


def _parse_e91_results(
    counts_list: list[dict[str, int]],
    shots: int = 1,
) -> tuple[list[int], list[int]]:
    """Parse Alice and Bob measurement results from counts."""
    alice_results = []
    bob_results = []

    for counts in counts_list:
        if shots == 1:
            bit_str = list(counts.keys())[0]
            # Qiskit bit ordering: bit_str[0] is qubit 1 (Bob), bit_str[1] is qubit 0 (Alice)
            bob_bit = int(bit_str[0])
            alice_bit = int(bit_str[1])
        else:
            # Multi-shot: compute individual qubit results from marginals
            alice_0, alice_1, bob_0, bob_1 = 0, 0, 0, 0
            for bitstr, count in counts.items():
                bob_bit = int(bitstr[0])
                alice_bit = int(bitstr[1])
                if alice_bit == 0:
                    alice_0 += count
                else:
                    alice_1 += count
                if bob_bit == 0:
                    bob_0 += count
                else:
                    bob_1 += count
            alice_bit = 0 if alice_0 >= alice_1 else 1
            bob_bit = 0 if bob_0 >= bob_1 else 1

        alice_results.append(alice_bit)
        bob_results.append(bob_bit)

    return alice_results, bob_results


def calculate_correlation(
    alice_results: list[int],
    bob_results: list[int],
    alice_settings: list[int],
    bob_settings: list[int],
    target_alice_setting: int,
    target_bob_setting: int,
) -> float:
    """Calculate E(a,b) correlation for a specific setting pair.

    E(a,b) = (N_same - N_diff) / (N_same + N_diff)
    where outcomes are mapped: 0 → +1, 1 → -1
    """
    n_same = 0
    n_diff = 0

    for i in range(len(alice_results)):
        if (alice_settings[i] == target_alice_setting
                and bob_settings[i] == target_bob_setting):
            # Map 0 → +1, 1 → -1
            a_val = 1 - 2 * alice_results[i]
            b_val = 1 - 2 * bob_results[i]
            if a_val == b_val:
                n_same += 1
            else:
                n_diff += 1

    total = n_same + n_diff
    if total == 0:
        return 0.0

    return (n_same - n_diff) / total


def calculate_chsh(correlations: dict[str, float]) -> float:
    """Calculate CHSH S value from measured correlations.

    S = E(a1,b1) - E(a1,b2) + E(a2,b1) + E(a2,b2)
    """
    e_a1_b1 = correlations.get("E(0,0)", 0.0)
    e_a1_b2 = correlations.get("E(0,1)", 0.0)
    e_a2_b1 = correlations.get("E(1,0)", 0.0)
    e_a2_b2 = correlations.get("E(1,1)", 0.0)

    s = e_a1_b1 - e_a1_b2 + e_a2_b1 + e_a2_b2
    return s


def evaluate_chsh_security(
    chsh_s: float,
    threshold: float = 2.0,
) -> str:
    """Evaluate security based on CHSH S value.

    Returns:
        'secure': |S| > threshold (quantum correlations detected)
        'compromised': |S| ≤ threshold (CHSH violation lost)
    """
    if abs(chsh_s) > threshold:
        return "secure"
    return "compromised"


def run_e91_protocol(
    num_pairs: int = 512,
    shots: int = 1,
    backend_name: str = "aer_simulator",
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
    chsh_threshold: float = 2.0,
) -> E91Result:
    """Execute the complete E91 protocol pipeline."""
    # Generate random measurement settings
    alice_settings = [secrets.randbelow(3) for _ in range(num_pairs)]
    bob_settings = [secrets.randbelow(3) for _ in range(num_pairs)]

    # Build and execute circuits
    circuits = _build_e91_circuits(num_pairs, alice_settings, bob_settings)
    counts_list, raw_hash = execute_e91(circuits, shots, execution_mode)
    alice_results, bob_results = _parse_e91_results(counts_list, shots)

    # Calculate correlations for CHSH pairs
    correlations = {}
    for a_set, b_set in CHSH_PAIRS:
        key = f"E({a_set},{b_set})"
        correlations[key] = calculate_correlation(
            alice_results, bob_results,
            alice_settings, bob_settings,
            a_set, b_set,
        )

    # Calculate CHSH S
    chsh_s = calculate_chsh(correlations)
    security = evaluate_chsh_security(chsh_s, chsh_threshold)

    # Extract key from matching-basis pairs
    sifted_alice = []
    sifted_bob = []
    for i in range(num_pairs):
        for a_key, b_key in KEY_GEN_PAIRS:
            if alice_settings[i] == a_key and bob_settings[i] == b_key:
                sifted_alice.append(alice_results[i])
                sifted_bob.append(bob_results[i])
                break

    # QBER from key bits
    qber = None
    error_count = 0
    if sifted_alice:
        error_count = sum(
            1 for i in range(len(sifted_alice))
            if sifted_alice[i] != sifted_bob[i]
        )
        qber = error_count / len(sifted_alice)

    return E91Result(
        protocol=QKDProtocol.E91,
        num_pairs=num_pairs,
        alice_settings=alice_settings,
        bob_settings=bob_settings,
        alice_results=alice_results,
        bob_results=bob_results,
        correlations=correlations,
        chsh_s=chsh_s,
        sifted_alice=sifted_alice,
        sifted_bob=sifted_bob,
        sifted_key_length=len(sifted_alice),
        qber=qber,
        error_count=error_count,
        backend_name=backend_name,
        shots=shots,
        execution_mode=execution_mode,
        raw_result_hash=raw_hash,
        chsh_threshold=chsh_threshold,
        security_evaluation=security,
    )
