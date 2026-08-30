"""Finite-key security analysis.

Implements finite-sample confidence bounds for QBER estimation
and secure key length calculation. Security evaluation includes
finite-key correction — a key is not labeled secure solely because
observed QBER is low.

PRD §11.
"""

from __future__ import annotations

import math
from typing import Optional

from packages.common.schemas import FiniteKeyResult


def qber_confidence_upper_bound(
    observed_qber: float,
    sample_size: int,
    epsilon: float = 1e-10,
) -> float:
    """Calculate QBER upper confidence bound using Hoeffding's inequality.

    P(QBER_true > observed_qber + δ) ≤ exp(-2nδ²)

    Solving for δ at confidence level ε:
        δ = sqrt(ln(1/ε) / (2n))
    """
    if sample_size <= 0:
        return 1.0

    delta = math.sqrt(math.log(1.0 / epsilon) / (2 * sample_size))
    return min(0.5, observed_qber + delta)


def binary_entropy(p: float) -> float:
    """Binary Shannon entropy h(p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def estimate_leakage_ec(
    qber: float,
    sifted_length: int,
    efficiency: float = 1.16,
) -> float:
    """Estimate error correction leakage in bits.

    leakage = n * efficiency * h(QBER)
    """
    if qber <= 0.0:
        return 0.0
    return sifted_length * efficiency * binary_entropy(qber)


def finite_size_penalty(
    sample_size: int,
    epsilon: float = 1e-10,
) -> float:
    """Calculate finite-size correction penalty.

    Finite-size penalty accounts for the statistical uncertainty
    in parameter estimation with limited samples.

    penalty ≈ 7 * sqrt(n) * log2(2/ε)

    This is a conservative bound.
    """
    if sample_size <= 0:
        return float("inf")
    return 7 * math.sqrt(sample_size) * math.log2(2.0 / epsilon)


def estimate_secure_key_length(
    sifted_key_length: int,
    observed_qber: float,
    epsilon: float = 1e-10,
    ec_efficiency: float = 1.16,
) -> FiniteKeyResult:
    """Calculate estimated secure key length with finite-key corrections.

    Steps:
        1. Calculate QBER upper confidence bound
        2. Estimate error correction leakage
        3. Calculate finite-size penalty
        4. Compute estimated secret bits

    A key is secure only if estimated_secret_bits > 0 AND the
    finite-key correction has been applied.
    """
    # Step 1: QBER confidence bound
    qber_upper = qber_confidence_upper_bound(observed_qber, sifted_key_length, epsilon)

    # Step 2: Error correction leakage (using upper bound QBER)
    leakage = estimate_leakage_ec(qber_upper, sifted_key_length, ec_efficiency)

    # Step 3: Finite-size penalty
    penalty = finite_size_penalty(sifted_key_length, epsilon)

    # Step 4: Estimated secret bits
    # secret_bits = n * [1 - h(qber_upper)] - leakage_ec - penalty
    if qber_upper >= 0.5:
        secret_bits = 0
    else:
        raw_secret = sifted_key_length * (1 - binary_entropy(qber_upper))
        secret_bits = max(0, int(raw_secret - leakage - penalty))

    secure = secret_bits > 0

    return FiniteKeyResult(
        observed_qber=observed_qber,
        qber_upper_bound=qber_upper,
        sample_size=sifted_key_length,
        epsilon=epsilon,
        leakage_ec=leakage,
        finite_size_penalty=penalty,
        estimated_secret_bits=secret_bits,
        secure=secure,
    )


def compare_key_lengths(
    observed_qber: float,
    key_lengths: Optional[list[int]] = None,
    epsilon: float = 1e-10,
) -> list[FiniteKeyResult]:
    """Compare finite-key security across different key lengths.

    Default comparison: 100, 1000, 10000 bits (PRD requirement).
    """
    if key_lengths is None:
        key_lengths = [100, 1000, 10000]

    results = []
    for n in key_lengths:
        result = estimate_secure_key_length(n, observed_qber, epsilon)
        results.append(result)

    return results
