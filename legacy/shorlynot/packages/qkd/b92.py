"""B92 Quantum Key Distribution engine using two non-orthogonal states.

B92 uses only two states:
    bit 0 → |0⟩   (Z-basis eigenstate)
    bit 1 → |+⟩   (X-basis eigenstate)

Bob measures in a basis that would give a conclusive result only
if Alice sent a specific state. Inconclusive results are discarded.

Bob's measurement strategy:
    To detect |0⟩: measure in X-basis (|+⟩ gives 50/50, |0⟩ can give |−⟩)
    To detect |+⟩: measure in Z-basis (|0⟩ gives 50/50, |+⟩ can give |1⟩)

Conclusive detection:
    Bob measures |−⟩ in X-basis → Alice sent |0⟩ → bit = 0
    Bob measures |1⟩ in Z-basis → Alice sent |+⟩ → bit = 1
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from packages.common.enums import ExecutionMode, QKDProtocol
from packages.common.errors import QuantumResultInvalidError


@dataclass
class B92Result:
    """Complete B92 protocol execution result."""

    protocol: QKDProtocol = QKDProtocol.B92
    alice_bits: list[int] = field(default_factory=list)
    bob_measurement_bases: list[int] = field(default_factory=list)
    bob_raw_results: list[int] = field(default_factory=list)
    conclusive_alice: list[int] = field(default_factory=list)
    conclusive_bob: list[int] = field(default_factory=list)
    conclusive_indices: list[int] = field(default_factory=list)
    transmitted_qubits: int = 0
    conclusive_measurements: int = 0
    inconclusive_measurements: int = 0
    conclusive_rate: float = 0.0
    detected_attack_rate: float = 0.0
    qber: Optional[float] = None
    error_count: int = 0
    compared_bits: int = 0
    backend_name: str = "aer_simulator"
    shots: int = 1
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    raw_result_hash: Optional[str] = None


def generate_b92_bits(n: int) -> list[int]:
    """Generate n random bits for Alice."""
    return [secrets.randbelow(2) for _ in range(n)]


def build_b92_circuits(
    alice_bits: list[int],
    attack_probability: float = 0.0,
) -> tuple[list[QuantumCircuit], list[int]]:
    """Build B92 circuits — one per qubit.

    Bob randomly chooses which state to try to detect:
        basis 0 (X-basis measurement): trying to detect |0⟩
        basis 1 (Z-basis measurement): trying to detect |+⟩

    Returns:
        Tuple of (circuits, bob_measurement_bases).
    """
    n = len(alice_bits)
    circuits = []
    bob_bases = []

    for i in range(n):
        qc = QuantumCircuit(1, 1, name=f"b92_q{i}")

        # Alice prepares her state
        if alice_bits[i] == 0:
            pass  # |0⟩ — do nothing
        else:
            qc.h(0)  # |+⟩

        qc.barrier()

        # Optional Eve intercept
        if attack_probability > 0 and secrets.randbelow(1000) < int(attack_probability * 1000):
            eve_basis = secrets.randbelow(2)
            if eve_basis == 1:
                qc.h(0)
            qc.measure(0, 0)
            qc.barrier()
            if eve_basis == 1:
                qc.h(0)

        # Bob randomly chooses measurement basis
        bob_basis = secrets.randbelow(2)
        bob_bases.append(bob_basis)

        if bob_basis == 0:
            # X-basis measurement to detect |0⟩
            qc.h(0)
        # else: Z-basis measurement to detect |+⟩ (no gate needed)

        qc.measure(0, 0)
        circuits.append(qc)

    return circuits, bob_bases


def execute_b92(
    circuits: list[QuantumCircuit],
    shots: int = 1,
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> tuple[list[dict[str, int]], str]:
    """Execute B92 circuits on AerSimulator."""
    if execution_mode == ExecutionMode.REAL:
        raise NotImplementedError("Real QPU B92 not yet implemented.")

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
            raise QuantumResultInvalidError(f"Empty counts for B92 circuit {i}")
        all_counts.append(counts)

    return all_counts, raw_hash


def parse_b92_measurements(
    counts_list: list[dict[str, int]], shots: int = 1
) -> list[int]:
    """Extract measurement results from B92 circuit counts."""
    measurements = []
    for counts in counts_list:
        if shots == 1:
            bit_str = list(counts.keys())[0]
            measurements.append(int(bit_str))
        else:
            zeros = counts.get("0", 0)
            ones = counts.get("1", 0)
            measurements.append(0 if zeros >= ones else 1)
    return measurements


def extract_conclusive_results(
    alice_bits: list[int],
    bob_bases: list[int],
    bob_results: list[int],
) -> tuple[list[int], list[int], list[int]]:
    """Extract conclusive B92 results.

    Conclusive detection rules:
        Bob used X-basis (basis=0) and measured |1⟩ (result=1) → Alice sent |0⟩ → bit=0
        Bob used Z-basis (basis=1) and measured |1⟩ (result=1) → Alice sent |+⟩ → bit=1

    In both cases, a result of 1 is the conclusive detection.
    A result of 0 is inconclusive (ambiguous).
    """
    conclusive_alice = []
    conclusive_bob = []
    indices = []

    for i in range(len(alice_bits)):
        if bob_results[i] == 1:
            # Conclusive detection
            if bob_bases[i] == 0:
                # X-basis measurement gave |−⟩ → Alice sent |0⟩
                conclusive_bob.append(0)
            else:
                # Z-basis measurement gave |1⟩ → Alice sent |+⟩
                conclusive_bob.append(1)
            conclusive_alice.append(alice_bits[i])
            indices.append(i)

    return conclusive_alice, conclusive_bob, indices


def calculate_detection_rate(
    total_qubits: int,
    conclusive_count: int,
) -> float:
    """Calculate the conclusive detection rate."""
    if total_qubits == 0:
        return 0.0
    return conclusive_count / total_qubits


def run_b92_protocol(
    num_qubits: int = 256,
    attack_probability: float = 0.0,
    shots: int = 1,
    backend_name: str = "aer_simulator",
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> B92Result:
    """Execute the complete B92 protocol pipeline."""
    alice_bits = generate_b92_bits(num_qubits)

    circuits, bob_bases = build_b92_circuits(alice_bits, attack_probability)

    counts_list, raw_hash = execute_b92(circuits, shots, execution_mode)

    bob_results = parse_b92_measurements(counts_list, shots)

    conclusive_alice, conclusive_bob, conclusive_indices = extract_conclusive_results(
        alice_bits, bob_bases, bob_results
    )

    conclusive_count = len(conclusive_alice)
    inconclusive_count = num_qubits - conclusive_count
    detection_rate = calculate_detection_rate(num_qubits, conclusive_count)

    # Calculate QBER from conclusive results
    qber = None
    error_count = 0
    compared = 0
    if conclusive_count > 0:
        error_count = sum(
            1 for i in range(conclusive_count)
            if conclusive_alice[i] != conclusive_bob[i]
        )
        compared = conclusive_count
        qber = error_count / compared

    return B92Result(
        protocol=QKDProtocol.B92,
        alice_bits=alice_bits,
        bob_measurement_bases=bob_bases,
        bob_raw_results=bob_results,
        conclusive_alice=conclusive_alice,
        conclusive_bob=conclusive_bob,
        conclusive_indices=conclusive_indices,
        transmitted_qubits=num_qubits,
        conclusive_measurements=conclusive_count,
        inconclusive_measurements=inconclusive_count,
        conclusive_rate=detection_rate,
        detected_attack_rate=0.0,
        qber=qber,
        error_count=error_count,
        compared_bits=compared,
        backend_name=backend_name,
        shots=shots,
        execution_mode=execution_mode,
        raw_result_hash=raw_hash,
    )
