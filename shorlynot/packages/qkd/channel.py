"""Quantum channel noise models.

Implements depolarizing, amplitude damping, phase damping channels
and fiber attenuation model. All values are clearly labeled as
simulated channel-model values.

PRD §12.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ChannelParameters:
    """Quantum channel characteristics."""

    distance_km: float = 0.0
    attenuation_db_per_km: float = 0.2  # Standard telecom fiber
    channel_loss_db: float = 0.0
    transmission_probability: float = 1.0
    detected_events: int = 0
    lost_events: int = 0
    depolarizing_probability: float = 0.0
    amplitude_damping_gamma: float = 0.0
    phase_damping_lambda: float = 0.0


def calculate_fiber_attenuation(
    distance_km: float,
    attenuation_db_per_km: float = 0.2,
) -> tuple[float, float]:
    """Calculate fiber channel loss and transmission probability.

    Args:
        distance_km: Fiber length in kilometers.
        attenuation_db_per_km: Loss coefficient (default 0.2 dB/km for telecom).

    Returns:
        Tuple of (loss_db, transmission_probability).
    """
    loss_db = attenuation_db_per_km * distance_km
    transmission_prob = 10 ** (-loss_db / 10)
    return loss_db, transmission_prob


def depolarizing_channel(qber_base: float, p: float) -> float:
    """Apply depolarizing channel noise to base QBER.

    Depolarizing probability p causes each qubit to be replaced with
    a maximally mixed state with probability p.

    Effective QBER = (1-p)*QBER_base + p/2
    """
    return (1 - p) * qber_base + p / 2


def amplitude_damping_qber(gamma: float) -> float:
    """Calculate QBER contribution from amplitude damping.

    Amplitude damping with parameter γ causes |1⟩ → |0⟩ with probability γ.
    This affects only |1⟩ states, contributing γ/4 to QBER on average
    (assuming uniform bit distribution and random bases).
    """
    return gamma / 4


def phase_damping_qber(lambda_param: float) -> float:
    """Calculate QBER contribution from phase damping.

    Phase damping with parameter λ causes decoherence in the X-basis.
    Only affects X-basis measurements, contributing λ/4 to QBER on average.
    """
    return lambda_param / 4


def secret_key_rate(
    qber: float,
    sifting_fraction: float = 0.5,
    efficiency_ec: float = 1.16,
) -> float:
    """Calculate asymptotic secret key rate per transmitted qubit.

    R = sifting * [1 - h(QBER) - efficiency_ec * h(QBER)]

    where h is binary Shannon entropy.

    This is a theoretical/analytical metric.
    """
    if qber <= 0.0:
        return sifting_fraction
    if qber >= 0.5:
        return 0.0

    h_qber = -qber * math.log2(qber) - (1 - qber) * math.log2(1 - qber)
    rate = sifting_fraction * (1 - h_qber - efficiency_ec * h_qber)
    return max(0.0, rate)


def simulate_channel(
    distance_km: float,
    num_qubits: int,
    base_qber: float = 0.0,
    attenuation_db_per_km: float = 0.2,
    depolarizing_p: float = 0.0,
    amplitude_gamma: float = 0.0,
    phase_lambda: float = 0.0,
) -> ChannelParameters:
    """Simulate a complete quantum channel with all noise sources.

    Returns channel parameters with calculated metrics.
    All values are labeled as simulated/theoretical, not measured.
    """
    loss_db, trans_prob = calculate_fiber_attenuation(distance_km, attenuation_db_per_km)

    # Estimate detected/lost events based on transmission probability
    detected = int(num_qubits * trans_prob)
    lost = num_qubits - detected

    # Combined QBER from all channel effects
    effective_qber = base_qber
    if depolarizing_p > 0:
        effective_qber = depolarizing_channel(effective_qber, depolarizing_p)
    if amplitude_gamma > 0:
        effective_qber += amplitude_damping_qber(amplitude_gamma)
    if phase_lambda > 0:
        effective_qber += phase_damping_qber(phase_lambda)

    effective_qber = min(0.5, effective_qber)

    return ChannelParameters(
        distance_km=distance_km,
        attenuation_db_per_km=attenuation_db_per_km,
        channel_loss_db=loss_db,
        transmission_probability=trans_prob,
        detected_events=detected,
        lost_events=lost,
        depolarizing_probability=depolarizing_p,
        amplitude_damping_gamma=amplitude_gamma,
        phase_damping_lambda=phase_lambda,
    )


def generate_distance_analysis(
    distances: Optional[list[float]] = None,
    num_qubits: int = 10000,
    base_qber: float = 0.02,
    attenuation_db_per_km: float = 0.2,
) -> list[dict]:
    """Generate key rate vs distance analysis for dashboard charts.

    All values are clearly marked as simulated channel-model values.
    """
    if distances is None:
        distances = [0, 5, 10, 20, 30, 50, 75, 100, 150, 200]

    results = []
    for d in distances:
        loss_db, trans_prob = calculate_fiber_attenuation(d, attenuation_db_per_km)
        # Distance adds depolarizing noise proportional to loss
        distance_qber = base_qber + 0.001 * d  # Simple linear model
        distance_qber = min(0.5, distance_qber)
        rate = secret_key_rate(distance_qber)

        results.append({
            "distance_km": d,
            "channel_loss_db": round(loss_db, 2),
            "transmission_probability": round(trans_prob, 6),
            "effective_qber": round(distance_qber, 4),
            "secret_key_rate": round(rate, 6),
            "estimated_detected_events": int(num_qubits * trans_prob),
            "data_type": "SIMULATED_CHANNEL_MODEL",  # Clear labeling
        })

    return results
