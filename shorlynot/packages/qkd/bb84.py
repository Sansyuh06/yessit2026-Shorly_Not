"""BB84 Quantum Key Distribution engine using real Qiskit circuits.

State mapping (PRD §7):
    basis 0, bit 0 → |0⟩   (Z-basis)
    basis 0, bit 1 → |1⟩   (Z-basis)
    basis 1, bit 0 → |+⟩   (X-basis, via Hadamard)
    basis 1, bit 1 → |−⟩   (X-basis, via X then Hadamard)

Measurement counts originate from actual Qiskit backend result objects.
QBER is calculated from sifted-key comparison, never hardcoded.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from packages.common.enums import ExecutionMode, QKDProtocol
from packages.common.errors import (
    InsufficientKeyMaterialError,
    QuantumResultInvalidError,
)


@dataclass
class BB84Result:
    """Complete BB84 protocol execution result."""

    protocol: QKDProtocol = QKDProtocol.BB84
    alice_bits: list[int] = field(default_factory=list)
    alice_bases: list[int] = field(default_factory=list)
    bob_bases: list[int] = field(default_factory=list)
    bob_measurements: list[int] = field(default_factory=list)
    sifted_alice: list[int] = field(default_factory=list)
    sifted_bob: list[int] = field(default_factory=list)
    sifted_indices: list[int] = field(default_factory=list)
    raw_key_length: int = 0
    sifted_key_length: int = 0
    qber: Optional[float] = None
    error_count: int = 0
    compared_bits: int = 0
    backend_name: str = "aer_simulator"
    shots: int = 1
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    raw_result_hash: Optional[str] = None
    # Attack tracking
    attacked_qubit_count: int = 0
    attack_probability: float = 0.0
    theoretical_qber: float = 0.0


def generate_alice_bits(n: int) -> list[int]:
    """Generate n random bits for Alice using cryptographic RNG."""
    return [secrets.randbelow(2) for _ in range(n)]


def generate_alice_bases(n: int) -> list[int]:
    """Generate n random basis choices (0=Z, 1=X) for Alice."""
    return [secrets.randbelow(2) for _ in range(n)]


def generate_bob_bases(n: int) -> list[int]:
    """Generate n random basis choices (0=Z, 1=X) for Bob."""
    return [secrets.randbelow(2) for _ in range(n)]


def build_bb84_circuits(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bases: list[int],
    attack_probability: float = 0.0,
) -> list[QuantumCircuit]:
    """Build one quantum circuit per qubit for BB84 protocol.

    Each circuit prepares Alice's state and measures in Bob's basis.
    If attack_probability > 0, an intercept-resend attack is simulated
    by measuring in a random Eve basis before Bob.

    Args:
        alice_bits: Alice's random bit string.
        alice_bases: Alice's basis choices (0=Z, 1=X).
        bob_bases: Bob's basis choices (0=Z, 1=X).
        attack_probability: Probability that Eve intercepts each qubit.

    Returns:
        List of QuantumCircuit objects, one per qubit.
    """
    n = len(alice_bits)
    circuits = []

    for i in range(n):
        qc = QuantumCircuit(1, 1, name=f"bb84_q{i}")

        # ── Alice prepares her qubit ──
        if alice_bits[i] == 1:
            qc.x(0)
        if alice_bases[i] == 1:
            qc.h(0)

        qc.barrier()

        # ── Eve's intercept-resend attack (probabilistic) ──
        is_attacked = secrets.randbelow(1000) < int(attack_probability * 1000)
        if is_attacked and attack_probability > 0:
            # Eve measures in a random basis
            eve_basis = secrets.randbelow(2)
            if eve_basis == 1:
                qc.h(0)
            qc.measure(0, 0)
            # Eve resends based on her measurement — this is handled by
            # the circuit collapsing. We reset and re-prepare.
            qc.barrier()
            # Reset qubit and re-prepare in Eve's basis with measured result.
            # In Qiskit simulation, the measurement already collapses the state.
            # We just need to rotate back to the computational basis if Eve
            # used X-basis, then apply Bob's measurement basis.
            if eve_basis == 1:
                qc.h(0)
            # Note: In a real attack model, Eve's interception causes errors
            # when her basis differs from Alice's. The Qiskit measurement
            # collapse naturally models this.

        # Reset classical bit for Bob's final measurement
        qc.barrier()

        # ── Bob measures in his chosen basis ──
        if bob_bases[i] == 1:
            qc.h(0)
        qc.measure(0, 0)

        circuits.append(qc)

    return circuits


def execute_bb84(
    circuits: list[QuantumCircuit],
    shots: int = 1,
    backend_name: str = "aer_simulator",
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> tuple[list[dict[str, int]], str]:
    """Execute BB84 circuits on the specified backend.

    Args:
        circuits: List of single-qubit circuits.
        shots: Number of shots per circuit.
        backend_name: Backend identifier.
        execution_mode: Current execution mode.

    Returns:
        Tuple of (list of count dicts, raw result hash).

    Raises:
        QuantumResultInvalidError: If results are malformed.
    """
    if execution_mode == ExecutionMode.REAL:
        # Real IBM execution path — requires qiskit-ibm-runtime
        raise NotImplementedError(
            "Real IBM QPU execution requires qiskit-ibm-runtime integration. "
            "Use SHORLYNOT_EXECUTION_MODE=simulation for local testing."
        )

    # Simulation path using AerSimulator
    simulator = AerSimulator()
    all_counts: list[dict[str, int]] = []

    # Execute circuits in batches for efficiency
    from qiskit import transpile

    transpiled = transpile(circuits, simulator)
    job = simulator.run(transpiled, shots=shots)
    result = job.result()

    # Hash the raw result for evidence
    raw_data = json.dumps(
        [result.get_counts(i) for i in range(len(circuits))],
        sort_keys=True,
    )
    raw_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    for i in range(len(circuits)):
        counts = result.get_counts(i)
        if not counts:
            raise QuantumResultInvalidError(
                f"Empty counts for circuit {i}"
            )
        all_counts.append(counts)

    return all_counts, raw_hash


def parse_measurements(counts_list: list[dict[str, int]], shots: int = 1) -> list[int]:
    """Extract measurement results from circuit execution counts.

    For single-shot execution, returns the measured bit directly.
    For multi-shot, returns the majority vote.
    """
    measurements = []
    for counts in counts_list:
        if shots == 1:
            # Single shot — take the one result
            bit_str = list(counts.keys())[0]
            measurements.append(int(bit_str))
        else:
            # Multi-shot — majority vote
            zeros = counts.get("0", 0)
            ones = counts.get("1", 0)
            measurements.append(0 if zeros >= ones else 1)
    return measurements


def sift_key(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bases: list[int],
    bob_measurements: list[int],
) -> tuple[list[int], list[int], list[int]]:
    """Perform basis sifting — keep only matching-basis bits.

    Returns:
        Tuple of (sifted_alice, sifted_bob, matching_indices).
    """
    sifted_alice = []
    sifted_bob = []
    indices = []

    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_measurements[i])
            indices.append(i)

    return sifted_alice, sifted_bob, indices


def calculate_qber(
    sifted_alice: list[int],
    sifted_bob: list[int],
    sample_fraction: float = 1.0,
) -> tuple[float, int, int]:
    """Calculate Quantum Bit Error Rate from sifted keys.

    Args:
        sifted_alice: Alice's sifted key bits.
        sifted_bob: Bob's sifted key bits.
        sample_fraction: Fraction of sifted bits to use for QBER estimation.

    Returns:
        Tuple of (qber, error_count, compared_bits).

    Raises:
        InsufficientKeyMaterialError: If no bits to compare.
    """
    n = len(sifted_alice)
    if n == 0:
        raise InsufficientKeyMaterialError("No sifted bits available for QBER calculation.")

    # Sample a fraction for QBER estimation
    sample_size = max(1, int(n * sample_fraction))
    indices = list(range(n))
    if sample_fraction < 1.0:
        rng = np.random.default_rng()
        indices = sorted(rng.choice(n, size=sample_size, replace=False).tolist())

    errors = sum(
        1 for i in indices if sifted_alice[i] != sifted_bob[i]
    )
    compared = len(indices)
    qber = errors / compared

    return qber, errors, compared


def estimate_eve_information(qber: float) -> float:
    """Estimate Eve's information using the binary entropy function.

    For BB84, Eve's information ≤ h(QBER) where h is binary Shannon entropy.
    """
    if qber <= 0.0 or qber >= 1.0:
        return 0.0 if qber <= 0.0 else 1.0

    h = -qber * np.log2(qber) - (1 - qber) * np.log2(1 - qber)
    return float(h)


def run_bb84_protocol(
    num_qubits: int = 256,
    attack_probability: float = 0.0,
    shots: int = 1,
    backend_name: str = "aer_simulator",
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
    qber_sample_fraction: float = 0.5,
) -> BB84Result:
    """Execute the complete BB84 protocol pipeline.

    Steps:
        1. Generate Alice's bits and bases
        2. Generate Bob's bases
        3. Build circuits (with optional attack)
        4. Execute on backend
        5. Parse measurements
        6. Sift key
        7. Calculate QBER
        8. Estimate Eve information

    Args:
        num_qubits: Number of qubits to transmit.
        attack_probability: Eve intercept probability per qubit [0,1].
        shots: Shots per circuit.
        backend_name: Qiskit backend name.
        execution_mode: Execution mode.
        qber_sample_fraction: Fraction of sifted bits for QBER estimation.

    Returns:
        Complete BB84Result with all metrics.
    """
    # Step 1-2: Generate random bits and bases
    alice_bits = generate_alice_bits(num_qubits)
    alice_bases = generate_alice_bases(num_qubits)
    bob_bases = generate_bob_bases(num_qubits)

    # Step 3: Build circuits
    circuits = build_bb84_circuits(
        alice_bits, alice_bases, bob_bases, attack_probability
    )

    # Count attacked qubits (approximate — actual attacks are probabilistic)
    attacked_count = int(num_qubits * attack_probability)

    # Step 4: Execute
    counts_list, raw_hash = execute_bb84(
        circuits, shots, backend_name, execution_mode
    )

    # Step 5: Parse
    bob_measurements = parse_measurements(counts_list, shots)

    # Step 6: Sift
    sifted_alice, sifted_bob, sifted_indices = sift_key(
        alice_bits, alice_bases, bob_bases, bob_measurements
    )

    # Step 7-8: QBER and Eve info
    qber = None
    error_count = 0
    compared = 0
    eve_info = 0.0

    if sifted_alice:
        qber, error_count, compared = calculate_qber(
            sifted_alice, sifted_bob, qber_sample_fraction
        )
        eve_info = estimate_eve_information(qber)

    return BB84Result(
        protocol=QKDProtocol.BB84,
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        bob_measurements=bob_measurements,
        sifted_alice=sifted_alice,
        sifted_bob=sifted_bob,
        sifted_indices=sifted_indices,
        raw_key_length=num_qubits,
        sifted_key_length=len(sifted_alice),
        qber=qber,
        error_count=error_count,
        compared_bits=compared,
        backend_name=backend_name,
        shots=shots,
        execution_mode=execution_mode,
        raw_result_hash=raw_hash,
        attacked_qubit_count=attacked_count,
        attack_probability=attack_probability,
        theoretical_qber=0.25 * attack_probability,
    )
