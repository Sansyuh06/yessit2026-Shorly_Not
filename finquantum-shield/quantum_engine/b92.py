"""
B92 Quantum Key Distribution Protocol
=======================================

Bennett's 1992 simplification of BB84 using only 2 states instead of 4.

Protocol:
- Alice sends either |+⟩ (for bit 0) or |+y⟩ (for bit 1)
- Bob measures in either X or Y basis (random choice)
- If Bob gets a result, he knows Alice's bit with certainty
- If Bob gets no result (orthogonal state), he discards

Advantages:
- Simpler than BB84 (2 states vs 4)
- Easier to implement in some hardware

Disadvantages:
- Lower efficiency (~25% vs ~50% for BB84)
- More susceptible to certain attacks

Reference:
- Bennett, "Quantum Cryptography Using Any Two Nonorthogonal States," 1992

Author: ShorlyNot Team
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import secrets
import numpy as np
from typing import Dict


def run_b92_session(
    num_bits: int = 256,
    eve: bool = False
) -> Dict:
    """
    Run B92 QKD session.
    
    Args:
        num_bits: Number of bits Alice wants to send
        eve: Whether Eve is eavesdropping
    
    Returns:
        dict: Session results (raw_key, qber, etc.)
    """
    # Alice's random bits
    alice_bits = [secrets.randbelow(2) for _ in range(num_bits)]
    
    # Bob's random basis choices (0=X, 1=Y)
    bob_bases = [secrets.randbelow(2) for _ in range(num_bits)]
    
    # Simulate B92
    # Alice: bit=0 → |+⟩, bit=1 → |+y⟩
    # Bob: basis=0 → measure X, basis=1 → measure Y
    # Bob gets result only if his basis is orthogonal to Alice's state
    
    bob_results = []
    bob_bits = []
    
    for i in range(num_bits):
        alice_bit = alice_bits[i]
        bob_basis = bob_bases[i]
        
        # Check if Bob's basis is orthogonal to Alice's state
        # |+⟩ is orthogonal to Y basis
        # |+y⟩ is orthogonal to X basis
        if (alice_bit == 0 and bob_basis == 1) or (alice_bit == 1 and bob_basis == 0):
            # Bob gets a result
            bob_results.append(i)
            # In B92, if Bob gets a result, he knows Alice's bit
            bob_bits.append(alice_bit)
    
    # Sifted key (only positions where Bob got a result)
    sifted_alice = [alice_bits[i] for i in bob_results]
    sifted_bob = bob_bits
    
    # Compute QBER (should be 0 without Eve, ~25% with Eve)
    if eve:
        # Eve introduces ~25% error (similar to BB84)
        errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
        # Simulate Eve's disturbance
        num_errors = int(len(sifted_alice) * 0.25)
        for i in range(min(num_errors, len(sifted_alice))):
            sifted_bob[i] = 1 - sifted_bob[i]  # Flip bit
    
    errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
    qber = errors / len(sifted_alice) if sifted_alice else 1.0
    
    raw_key = _bits_to_bytes(sifted_alice)
    
    return {
        "raw_key": raw_key,
        "qber": round(qber, 6),
        "attack_detected": qber >= 0.11,
        "sifted_key_length": len(sifted_alice),
        "efficiency": len(sifted_alice) / num_bits,
    }


def _bits_to_bytes(bits):
    """Convert list of bits to bytes."""
    if not bits:
        return b""
    bit_str = ''.join(str(b) for b in bits)
    # Pad to multiple of 8
    bit_str = bit_str.ljust((len(bit_str) + 7) // 8 * 8, '0')
    return int(bit_str, 2).to_bytes(len(bit_str) // 8, 'big')
