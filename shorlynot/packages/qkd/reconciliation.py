"""Cascade-style information reconciliation.

Implements a binary error correction protocol that corrects errors
between Alice's and Bob's sifted keys through interactive parity
comparisons. Each parity disclosure contributes to information leakage.

This is NOT a simple key copy — it tracks parity queries, disclosed
bits, and remaining errors across multiple passes.

PRD §13.
"""

from __future__ import annotations

import math
from typing import Optional

from packages.common.schemas import ReconciliationResult


def _parity(bits: list[int], start: int, end: int) -> int:
    """Calculate parity of a bit subsequence."""
    p = 0
    for i in range(start, min(end, len(bits))):
        p ^= bits[i]
    return p


def _binary_search_error(
    alice_bits: list[int],
    bob_bits: list[int],
    start: int,
    end: int,
    parity_queries: list[int],
) -> Optional[int]:
    """Binary search to find a single error position within a block.

    Each subdivision requires a parity query (information disclosure).
    Returns the index of the found error, or None.
    """
    if start >= end:
        return None

    if end - start == 1:
        if alice_bits[start] != bob_bits[start]:
            return start
        return None

    mid = (start + end) // 2

    # Query parity of left half
    alice_left_parity = _parity(alice_bits, start, mid)
    bob_left_parity = _parity(bob_bits, start, mid)
    parity_queries.append(1)  # Track disclosure

    if alice_left_parity != bob_left_parity:
        # Error is in left half
        return _binary_search_error(alice_bits, bob_bits, start, mid, parity_queries)
    else:
        # Error is in right half
        return _binary_search_error(alice_bits, bob_bits, mid, end, parity_queries)


def cascade_reconciliation(
    alice_key: list[int],
    bob_key: list[int],
    max_passes: int = 4,
    initial_block_size: Optional[int] = None,
) -> ReconciliationResult:
    """Perform Cascade-style error reconciliation.

    Algorithm:
        Pass 1: Divide key into blocks of size k1. Compare parities.
                 Binary-search blocks with parity mismatch.
        Pass 2: Double block size. Randomly shuffle. Repeat.
        ...
        Each pass may also trigger corrections in previous-pass blocks.

    Args:
        alice_key: Alice's sifted key (reference).
        bob_key: Bob's sifted key (to be corrected).
        max_passes: Maximum number of passes (default 4).
        initial_block_size: Starting block size. Default: 0.73/QBER estimate.

    Returns:
        ReconciliationResult with corrected key and leakage tracking.
    """
    n = len(alice_key)
    if n == 0:
        return ReconciliationResult(
            reconciled_key=[],
            corrected_error_count=0,
            remaining_error_count=0,
            disclosed_bits=0,
            leakage_bits=0.0,
            passes=0,
        )

    # Make a mutable copy of Bob's key
    bob_corrected = list(bob_key)

    # Estimate initial QBER for block size calculation
    initial_errors = sum(1 for i in range(n) if alice_key[i] != bob_corrected[i])
    estimated_qber = initial_errors / n if n > 0 else 0.01

    if initial_block_size is None:
        if estimated_qber > 0:
            initial_block_size = max(2, int(0.73 / estimated_qber))
        else:
            initial_block_size = max(2, n // 4)

    total_parity_queries: list[int] = []
    total_corrected = 0
    passes_done = 0

    import secrets

    for pass_num in range(max_passes):
        block_size = initial_block_size * (2 ** pass_num)
        if block_size >= n:
            block_size = n

        # Create a permutation for this pass (pass 0 uses natural order)
        if pass_num == 0:
            perm = list(range(n))
        else:
            perm = list(range(n))
            # Fisher-Yates shuffle with cryptographic randomness
            for i in range(n - 1, 0, -1):
                j = secrets.randbelow(i + 1)
                perm[i], perm[j] = perm[j], perm[i]

        # Process blocks
        num_blocks = math.ceil(n / block_size)
        corrections_this_pass = 0

        for b in range(num_blocks):
            block_start = b * block_size
            block_end = min((b + 1) * block_size, n)

            # Get permuted indices for this block
            block_indices = perm[block_start:block_end]

            # Calculate parities using permuted order
            alice_parity = 0
            bob_parity = 0
            for idx in block_indices:
                alice_parity ^= alice_key[idx]
                bob_parity ^= bob_corrected[idx]

            total_parity_queries.append(1)  # Block parity disclosure

            if alice_parity != bob_parity:
                # Parity mismatch — binary search for the error
                # Work on a temporary array for binary search
                alice_block = [alice_key[idx] for idx in block_indices]
                bob_block = [bob_corrected[idx] for idx in block_indices]

                error_pos = _binary_search_error(
                    alice_block, bob_block, 0, len(alice_block), total_parity_queries
                )

                if error_pos is not None:
                    # Correct the error in the original key
                    original_idx = block_indices[error_pos]
                    bob_corrected[original_idx] ^= 1  # Flip the bit
                    total_corrected += 1
                    corrections_this_pass += 1

        passes_done += 1

        # If no corrections in this pass, key might be clean
        if corrections_this_pass == 0 and pass_num > 0:
            break

    # Count remaining errors
    remaining_errors = sum(1 for i in range(n) if alice_key[i] != bob_corrected[i])

    # Calculate information leakage
    disclosed_bits = len(total_parity_queries)
    # Each parity bit disclosed leaks 1 bit of information
    leakage_bits = float(disclosed_bits)

    return ReconciliationResult(
        reconciled_key=bob_corrected,
        corrected_error_count=total_corrected,
        remaining_error_count=remaining_errors,
        disclosed_bits=disclosed_bits,
        leakage_bits=leakage_bits,
        passes=passes_done,
    )
