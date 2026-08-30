"""
E91 Entanglement-Based QKD Protocol
=====================================

Ekert's 1991 protocol using entangled Bell pairs.

Protocol:
- Source generates Bell pairs |Φ+⟩ = (|00⟩ + |11⟩)/√2
- Alice and Bob each receive one qubit
- They measure in randomly chosen bases
- Correlations reveal eavesdropping (Bell inequality violation)

Advantages:
- Device-independent security (Bell test)
- No need to trust the source

Disadvantages:
- Requires entanglement distribution (harder than single photons)
- More complex hardware

Reference:
- Ekert, "Quantum Cryptography Based on Bell's Theorem," 1991

Author: ShorlyNot Team
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import secrets
import numpy as np
from typing import Dict


def run_e91_session(
    num_pairs: int = 256,
    eve: bool = False
) -> Dict:
    """
    Run E91 QKD session using entangled Bell pairs.
    
    Args:
        num_pairs: Number of Bell pairs to generate
        eve: Whether Eve is eavesdropping
    
    Returns:
        dict: Session results
    """
    backend = AerSimulator()
    
    # Alice and Bob's random basis choices
    # E91 uses 3 bases for Bell test, but we simplify to 2 for key generation
    alice_bases = [secrets.randbelow(2) for _ in range(num_pairs)]
    bob_bases = [secrets.randbelow(2) for _ in range(num_pairs)]
    
    alice_bits = []
    bob_bits = []
    
    for i in range(num_pairs):
        # Create Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        
        if eve:
            # Eve intercepts and measures (breaks entanglement)
            qc.measure([0, 1], [0, 1])
        else:
            # Alice and Bob measure in their chosen bases
            if alice_bases[i] == 1:
                qc.h(0)  # Rotate to X basis
            if bob_bases[i] == 1:
                qc.h(1)  # Rotate to X basis
            qc.measure([0, 1], [0, 1])
        
        # Simulate
        job = backend.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        # Extract bits
        outcome = list(counts.keys())[0]
        alice_bit = int(outcome[1])  # Qubit 0
        bob_bit = int(outcome[0])    # Qubit 1
        
        alice_bits.append(alice_bit)
        bob_bits.append(bob_bit)
    
    # Sift: keep only matching bases
    sifted_alice = []
    sifted_bob = []
    for i in range(num_pairs):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])
    
    # Compute QBER
    errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
    qber = errors / len(sifted_alice) if sifted_alice else 1.0
    
    raw_key = _bits_to_bytes(sifted_alice)
    
    return {
        "raw_key": raw_key,
        "qber": round(qber, 6),
        "attack_detected": qber >= 0.11,
        "sifted_key_length": len(sifted_alice),
        "efficiency": len(sifted_alice) / num_pairs,
    }


def _bits_to_bytes(bits):
    """Convert list of bits to bytes."""
    if not bits:
        return b""
    bit_str = ''.join(str(b) for b in bits)
    bit_str = bit_str.ljust((len(bit_str) + 7) // 8 * 8, '0')
    return int(bit_str, 2).to_bytes(len(bit_str) // 8, 'big')
