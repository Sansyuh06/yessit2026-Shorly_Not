"""
Cascade Error Correction Protocol
==================================

Simplified implementation of the Cascade protocol for BB84 error correction.

Alice and Bob have sifted keys that may differ due to channel noise or eavesdropping.
Cascade uses binary search to find and correct errors through public discussion.

Protocol:
1. Split key into blocks
2. Compare parities (public)
3. If parities differ, binary search for error
4. Correct error (flip Bob's bit)
5. Repeat with shuffled blocks (multiple passes)

Real implementation would use full Cascade or Winnow protocol with:
- Adaptive block sizes
- Interactive parity checks
- Privacy preservation (minimal information leakage)

Author: ShorlyNot Team
"""

import hashlib
import random
from typing import List, Tuple


def cascade_reconcile(
    alice_bits: List[int],
    bob_bits: List[int],
    num_passes: int = 4,
    initial_block_size: int = 8
) -> Tuple[List[int], List[int], int, List[int]]:
    """
    Reconcile Alice and Bob's bits using simplified Cascade protocol.
    
    Args:
        alice_bits: Alice's sifted bits (reference)
        bob_bits: Bob's sifted bits (to be corrected)
        num_passes: Number of reconciliation passes (default: 4)
        initial_block_size: Starting block size (default: 8)
    
    Returns:
        tuple: (corrected_alice, corrected_bob, num_corrections, corrected_indices)
    
    Note:
        - Alice's bits are unchanged (she's the reference)
        - Bob's bits are corrected to match Alice
        - corrected_indices lists which bit positions were flipped
        - In real Cascade, Alice and Bob would interactively exchange parities
          Here we simulate by directly comparing (cheating, but educational)
    
    Example:
        >>> alice = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> bob =   [1, 0, 0, 1, 0, 1, 1, 0]  # 2 errors at positions 2, 5
        >>> alice_c, bob_c, n_corr, indices = cascade_reconcile(alice, bob)
        >>> assert bob_c == alice_c  # Now identical
        >>> assert n_corr == 2
        >>> assert set(indices) == {2, 5}
    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Alice and Bob must have same number of bits")
    
    alice = alice_bits.copy()
    bob = bob_bits.copy()
    corrections = 0
    corrected_indices = []
    
    for pass_num in range(num_passes):
        # Shuffle bits (different permutation each pass)
        # This helps find errors that were masked in previous passes
        seed = hashlib.sha256(f"cascade_pass_{pass_num}".encode()).digest()
        random.seed(int.from_bytes(seed[:4], 'big'))
        
        indices = list(range(len(alice)))
        random.shuffle(indices)
        
        # Decrease block size each pass (more granular)
        block_size = max(4, initial_block_size // (2 ** pass_num))
        
        # Process blocks
        for i in range(0, len(alice), block_size):
            block_indices = indices[i:i+block_size]
            
            # Compute parity for this block
            alice_parity = sum(alice[j] for j in block_indices) % 2
            bob_parity = sum(bob[j] for j in block_indices) % 2
            
            # If parities differ, there's at least one error in this block
            if alice_parity != bob_parity:
                # Binary search for the error
                left, right = 0, len(block_indices) - 1
                
                while left < right:
                    mid = (left + right) // 2
                    sub_indices = block_indices[left:mid+1]
                    
                    alice_sub_parity = sum(alice[j] for j in sub_indices) % 2
                    bob_sub_parity = sum(bob[j] for j in sub_indices) % 2
                    
                    if alice_sub_parity != bob_sub_parity:
                        # Error is in left half
                        right = mid
                    else:
                        # Error is in right half
                        left = mid + 1
                
                # Found the error — correct Bob's bit to match Alice
                error_index = block_indices[left]
                bob[error_index] = alice[error_index]
                corrections += 1
                corrected_indices.append(error_index)
    
    return alice, bob, corrections, corrected_indices


def estimate_error_rate(
    alice_bits: List[int],
    bob_bits: List[int],
    sample_size: int = 100
) -> float:
    """
    Estimate error rate by sampling (before reconciliation).
    
    Args:
        alice_bits: Alice's bits
        bob_bits: Bob's bits
        sample_size: Number of bits to sample (default: 100)
    
    Returns:
        float: Estimated error rate (0.0 to 1.0)
    
    Note:
        In real BB84, Alice and Bob would publicly compare a random subset
        of their bits to estimate QBER, then discard those bits.
        Here we just sample without discarding (simplified).
    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Alice and Bob must have same number of bits")
    
    # Sample random positions
    sample_indices = random.sample(range(len(alice_bits)), min(sample_size, len(alice_bits)))
    
    # Count errors in sample
    errors = sum(1 for i in sample_indices if alice_bits[i] != bob_bits[i])
    
    return errors / len(sample_indices)
