"""Privacy amplification using universal hashing (Toeplitz matrix).

Extracts a shorter, information-theoretically secure key from the
reconciled key. Output length must not exceed the calculated
extractable secret length based on entropy accounting.

This is NOT SHA256(raw_key) — it uses proper Toeplitz matrix hashing
with entropy-length accounting.

PRD §14.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Optional

import numpy as np

from packages.common.enums import EntropyStage
from packages.common.schemas import EntropyLedgerEntry


def _generate_toeplitz_seed(n: int) -> list[int]:
    """Generate random seed bits for Toeplitz matrix construction.

    A Toeplitz matrix of size m×n requires (m + n - 1) random bits.
    We generate n bits here; the full seed is (output_len + n - 1).
    """
    return [secrets.randbelow(2) for _ in range(n)]


def _toeplitz_hash(
    input_bits: list[int],
    output_length: int,
    seed: list[int],
) -> list[int]:
    """Apply Toeplitz matrix universal hash function.

    Constructs an output_length × input_length Toeplitz matrix from
    the seed and multiplies it (mod 2) with the input bit vector.

    Args:
        input_bits: Input bit string to hash.
        output_length: Desired output length in bits.
        seed: Random seed of length (output_length + input_length - 1).

    Returns:
        Hashed output bit string of specified length.
    """
    n = len(input_bits)
    m = output_length

    if len(seed) < m + n - 1:
        raise ValueError(
            f"Seed length {len(seed)} < required {m + n - 1} "
            f"for Toeplitz({m}×{n})"
        )

    output = []
    for i in range(m):
        # Row i of Toeplitz matrix: seed[i], seed[i+1], ..., seed[i+n-1]
        bit = 0
        for j in range(n):
            bit ^= seed[i + j] & input_bits[j]
        output.append(bit)

    return output


def calculate_extractable_length(
    reconciled_key_length: int,
    estimated_min_entropy: float,
    security_parameter: float = 1e-10,
    disclosed_bits: float = 0.0,
    eve_information_bound: float = 0.0,
) -> int:
    """Calculate maximum extractable secure key length.

    output_length ≤ min_entropy - disclosed_bits - eve_info - log2(1/ε)

    The output must never exceed this bound.
    """
    import math

    security_bits = math.log2(1.0 / security_parameter) if security_parameter > 0 else 0

    extractable = (
        estimated_min_entropy
        - disclosed_bits
        - eve_information_bound
        - security_bits
    )

    return max(0, int(extractable))


def privacy_amplification(
    reconciled_key: list[int],
    estimated_min_entropy: float,
    security_parameter: float = 1e-10,
    disclosed_bits: float = 0.0,
    eve_information_bound: float = 0.0,
    target_length: Optional[int] = None,
) -> tuple[list[int], EntropyLedgerEntry]:
    """Perform privacy amplification on reconciled key.

    Args:
        reconciled_key: Input bit string after reconciliation.
        estimated_min_entropy: Estimated min-entropy of input.
        security_parameter: Security parameter ε.
        disclosed_bits: Bits disclosed during reconciliation.
        eve_information_bound: Upper bound on Eve's information.
        target_length: Desired output length (must not exceed extractable).

    Returns:
        Tuple of (amplified_key, entropy_ledger_entry).

    Raises:
        ValueError: If target_length exceeds extractable bound.
    """
    n = len(reconciled_key)

    # Calculate maximum extractable length
    max_length = calculate_extractable_length(
        n, estimated_min_entropy, security_parameter,
        disclosed_bits, eve_information_bound,
    )

    if target_length is None:
        target_length = max_length
    elif target_length > max_length:
        raise ValueError(
            f"Requested output length {target_length} exceeds "
            f"extractable bound {max_length}"
        )

    if target_length <= 0:
        return [], EntropyLedgerEntry(
            stage=EntropyStage.PRIVACY_AMPLIFIED,
            input_bits=n,
            output_bits=0,
            estimated_min_entropy=0.0,
            disclosed_bits=int(disclosed_bits),
            eve_information_bound=eve_information_bound,
        )

    # Generate Toeplitz seed
    seed_length = target_length + n - 1
    seed = _generate_toeplitz_seed(seed_length)

    # Apply Toeplitz hash
    amplified_key = _toeplitz_hash(reconciled_key, target_length, seed)

    ledger = EntropyLedgerEntry(
        stage=EntropyStage.PRIVACY_AMPLIFIED,
        input_bits=n,
        output_bits=target_length,
        estimated_min_entropy=float(target_length),  # Output has full entropy
        disclosed_bits=int(disclosed_bits),
        eve_information_bound=eve_information_bound,
    )

    return amplified_key, ledger


def build_entropy_ledger(
    raw_key_length: int,
    sifted_key_length: int,
    reconciled_key_length: int,
    final_key_length: int,
    raw_min_entropy: float,
    sifted_min_entropy: float,
    reconciled_min_entropy: float,
    final_min_entropy: float,
    disclosed_bits: int = 0,
    eve_information_bound: float = 0.0,
) -> list[EntropyLedgerEntry]:
    """Build the complete entropy pipeline ledger for dashboard visualization.

    Tracks entropy at each stage: RAW → SIFTED → RECONCILED → PRIVACY_AMPLIFIED
    """
    return [
        EntropyLedgerEntry(
            stage=EntropyStage.RAW,
            input_bits=raw_key_length,
            output_bits=raw_key_length,
            estimated_min_entropy=raw_min_entropy,
            disclosed_bits=0,
            eve_information_bound=0.0,
        ),
        EntropyLedgerEntry(
            stage=EntropyStage.SIFTED,
            input_bits=raw_key_length,
            output_bits=sifted_key_length,
            estimated_min_entropy=sifted_min_entropy,
            disclosed_bits=0,
            eve_information_bound=eve_information_bound,
        ),
        EntropyLedgerEntry(
            stage=EntropyStage.RECONCILED,
            input_bits=sifted_key_length,
            output_bits=reconciled_key_length,
            estimated_min_entropy=reconciled_min_entropy,
            disclosed_bits=disclosed_bits,
            eve_information_bound=eve_information_bound,
        ),
        EntropyLedgerEntry(
            stage=EntropyStage.PRIVACY_AMPLIFIED,
            input_bits=reconciled_key_length,
            output_bits=final_key_length,
            estimated_min_entropy=final_min_entropy,
            disclosed_bits=disclosed_bits,
            eve_information_bound=eve_information_bound,
        ),
    ]
