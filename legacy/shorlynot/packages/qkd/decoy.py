"""Decoy-state BB84 engine with PNS attack detection.

Implements three pulse intensity classes (SIGNAL, DECOY, VACUUM) with
Poisson photon-number statistics. Demonstrates why raw QBER alone
may not detect PNS attacks — the decoy-state bounds comparison is
required.

PRD §10.
"""

from __future__ import annotations

import math
import secrets
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from packages.common.enums import ExecutionMode, PulseClass, QKDProtocol
from packages.common.errors import QuantumResultInvalidError


@dataclass
class PulseResult:
    """Results for a single intensity class."""

    pulse_class: PulseClass
    mu: float
    sent_count: int = 0
    detected_count: int = 0
    error_count: int = 0
    gain: float = 0.0
    qber: Optional[float] = None


@dataclass
class DecoyResult:
    """Complete decoy-state BB84 result."""

    protocol: QKDProtocol = QKDProtocol.DECOY_BB84
    signal: PulseResult = field(default_factory=lambda: PulseResult(PulseClass.SIGNAL, 0.5))
    decoy: PulseResult = field(default_factory=lambda: PulseResult(PulseClass.DECOY, 0.1))
    vacuum: PulseResult = field(default_factory=lambda: PulseResult(PulseClass.VACUUM, 0.0))
    estimated_single_photon_yield: float = 0.0
    estimated_single_photon_error_rate: float = 0.0
    pns_suspected: bool = False
    pns_evidence: str = ""
    total_qubits: int = 0
    sifted_key_length: int = 0
    raw_qber: Optional[float] = None
    backend_name: str = "aer_simulator"
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    raw_result_hash: Optional[str] = None


def _poisson_photon_number(mu: float) -> int:
    """Sample photon number from Poisson distribution."""
    if mu <= 0:
        return 0
    return int(np.random.poisson(mu))


def _assign_pulse_classes(
    n: int,
    signal_ratio: float = 0.6,
    decoy_ratio: float = 0.3,
    # vacuum_ratio = 1 - signal_ratio - decoy_ratio
) -> list[PulseClass]:
    """Randomly assign pulse classes to each transmission."""
    classes = []
    for _ in range(n):
        r = secrets.randbelow(1000) / 1000.0
        if r < signal_ratio:
            classes.append(PulseClass.SIGNAL)
        elif r < signal_ratio + decoy_ratio:
            classes.append(PulseClass.DECOY)
        else:
            classes.append(PulseClass.VACUUM)
    return classes


def run_decoy_bb84(
    num_qubits: int = 1024,
    signal_mu: float = 0.5,
    decoy_mu: float = 0.1,
    vacuum_mu: float = 0.0,
    attack_probability: float = 0.0,
    pns_attack: bool = False,
    channel_loss: float = 0.0,
    shots: int = 1,
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
) -> DecoyResult:
    """Execute decoy-state BB84 with intensity monitoring.

    In PNS attack mode, multi-photon pulses are selectively attacked
    while single-photon pulses pass through, showing why raw QBER
    may not detect the attack.
    """
    mu_map = {
        PulseClass.SIGNAL: signal_mu,
        PulseClass.DECOY: decoy_mu,
        PulseClass.VACUUM: vacuum_mu,
    }

    pulse_classes = _assign_pulse_classes(num_qubits)

    # Track per-class statistics
    class_sent: dict[PulseClass, int] = {pc: 0 for pc in PulseClass}
    class_detected: dict[PulseClass, int] = {pc: 0 for pc in PulseClass}
    class_errors: dict[PulseClass, int] = {pc: 0 for pc in PulseClass}

    sifted_alice: list[int] = []
    sifted_bob: list[int] = []

    simulator = AerSimulator()

    for i in range(num_qubits):
        pc = pulse_classes[i]
        mu = mu_map[pc]
        class_sent[pc] += 1

        # Sample photon number
        n_photons = _poisson_photon_number(mu)

        if n_photons == 0:
            # Vacuum — no detection possible
            continue

        # Channel loss
        if channel_loss > 0 and secrets.randbelow(1000) < int(channel_loss * 1000):
            continue

        alice_bit = secrets.randbelow(2)
        alice_basis = secrets.randbelow(2)
        bob_basis = secrets.randbelow(2)

        # PNS attack: Eve blocks single-photon, keeps one from multi-photon
        eve_intercepted = False
        if pns_attack and attack_probability > 0:
            if n_photons >= 2:
                # Eve takes one photon — no disturbance on Bob's photon
                eve_intercepted = True
                # Eve waits for basis announcement to extract the key
                # This does NOT introduce QBER
            elif n_photons == 1:
                # Eve cannot split — may block or let through
                if secrets.randbelow(1000) < int(attack_probability * 500):
                    continue  # Eve blocks to avoid detection

        # Build and run circuit
        qc = QuantumCircuit(1, 1)
        if alice_bit == 1:
            qc.x(0)
        if alice_basis == 1:
            qc.h(0)

        # Non-PNS intercept-resend attack
        if not pns_attack and attack_probability > 0:
            if secrets.randbelow(1000) < int(attack_probability * 1000):
                eve_basis = secrets.randbelow(2)
                if eve_basis == 1:
                    qc.h(0)
                qc.measure(0, 0)
                qc.barrier()
                if eve_basis == 1:
                    qc.h(0)

        if bob_basis == 1:
            qc.h(0)
        qc.measure(0, 0)

        transpiled = transpile(qc, simulator)
        job = simulator.run(transpiled, shots=1)
        result = job.result()
        counts = result.get_counts(0)
        bob_bit = int(list(counts.keys())[0])

        class_detected[pc] += 1

        # Sifting
        if alice_basis == bob_basis:
            sifted_alice.append(alice_bit)
            sifted_bob.append(bob_bit)
            if alice_bit != bob_bit:
                class_errors[pc] += 1

    # Calculate per-class gains and QBERs
    def make_pulse_result(pc: PulseClass) -> PulseResult:
        sent = class_sent[pc]
        detected = class_detected[pc]
        errors = class_errors[pc]
        gain = detected / sent if sent > 0 else 0.0
        qber = errors / detected if detected > 0 else None
        return PulseResult(
            pulse_class=pc,
            mu=mu_map[pc],
            sent_count=sent,
            detected_count=detected,
            error_count=errors,
            gain=gain,
            qber=qber,
        )

    signal_result = make_pulse_result(PulseClass.SIGNAL)
    decoy_result = make_pulse_result(PulseClass.DECOY)
    vacuum_result = make_pulse_result(PulseClass.VACUUM)

    # Estimate single-photon yield using decoy bounds
    # Y1 ≥ (μ_s / (μ_s*μ_d - μ_d²)) * (Q_μd * e^μd - Q_μv * e^μv * μ_d²/μ_s² - ...)
    # Simplified lower bound:
    y1 = 0.0
    e1 = 0.0
    pns_flag = False
    pns_evidence = ""

    if signal_mu > 0 and decoy_mu > 0:
        q_signal = signal_result.gain
        q_decoy = decoy_result.gain
        q_vacuum = vacuum_result.gain

        # Lower bound on single-photon yield
        denom = decoy_mu * (signal_mu - decoy_mu)
        if denom > 0:
            y1_raw = (
                (decoy_mu * q_signal * math.exp(signal_mu)
                 - signal_mu * q_decoy * math.exp(decoy_mu))
                / denom
            )
            y1 = max(0.0, y1_raw)

        # Single-photon error rate upper bound
        if y1 > 0 and decoy_result.detected_count > 0:
            e_decoy = decoy_result.qber if decoy_result.qber is not None else 0.0
            e1_raw = (q_decoy * math.exp(decoy_mu) * e_decoy - q_vacuum * 0.5) / (y1 * decoy_mu)
            e1 = min(0.5, max(0.0, e1_raw))

        # PNS detection: compare signal and decoy gains
        # Under PNS attack, signal gain should be anomalously high relative to decoy
        if q_signal > 0 and q_decoy > 0:
            expected_ratio = signal_mu / decoy_mu
            observed_ratio = q_signal / q_decoy
            if observed_ratio > expected_ratio * 1.5:
                pns_flag = True
                pns_evidence = (
                    f"Gain ratio anomaly: observed={observed_ratio:.3f}, "
                    f"expected≈{expected_ratio:.3f}. "
                    f"Signal gain={q_signal:.4f}, Decoy gain={q_decoy:.4f}"
                )

    # Raw QBER across all sifted bits
    raw_qber = None
    if sifted_alice:
        errors = sum(1 for i in range(len(sifted_alice)) if sifted_alice[i] != sifted_bob[i])
        raw_qber = errors / len(sifted_alice)

    return DecoyResult(
        protocol=QKDProtocol.DECOY_BB84,
        signal=signal_result,
        decoy=decoy_result,
        vacuum=vacuum_result,
        estimated_single_photon_yield=y1,
        estimated_single_photon_error_rate=e1,
        pns_suspected=pns_flag,
        pns_evidence=pns_evidence,
        total_qubits=num_qubits,
        sifted_key_length=len(sifted_alice),
        raw_qber=raw_qber,
        execution_mode=execution_mode,
    )
