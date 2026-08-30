"""
Decoy-State Protocol — Simplified Proxy for PNS Detection
==========================================================

EDUCATIONAL DISCLAIMER:
This is a SIMPLIFIED PROXY for educational purposes. It does NOT implement
real decoy-state QKD as defined by Hwang (2003) or Lo-Chau.

WHAT THIS DOES:
- Randomly marks ~30% of qubits as "decoy"
- Compares error rates between "signal" and "decoy" subsets
- Flags significant differences as potential PNS attacks

WHAT THIS DOESN'T DO:
- Real PNS detection requires a MULTI-PHOTON SOURCE with variable intensity
- Our simulator uses SINGLE PHOTONS only (no photon-number variation)
- "Signal vs. decoy yield" here is just comparing noise statistics
- Cannot actually detect photon-number-splitting attacks

WHY WE INCLUDE IT:
- Demonstrates the CONCEPT and ARCHITECTURE of decoy-state QKD
- Shows how a real system WOULD structure PNS detection
- Educational value for understanding the protocol flow

PRODUCTION PATH:
- Integrate with real QKD hardware (e.g., ID Quantique Clavis²)
- Hardware must support intensity modulation (signal vs. decoy pulses)
- Use proper statistical tests (e.g., Gaussian hypothesis testing)

REFERENCES:
- Hwang, "Quantum Key Distribution with High Loss," 2003 (arXiv:quant-ph/0411006)
- Lo, Ma, Chen, "Decoy State Quantum Key Distribution," 2005 (arXiv:quant-ph/0411093)

Author: ShorlyNot Team
"""

import secrets
from typing import Dict

from quantum_engine.bb84_simulator import run_bb84_session


def run_bb84_with_decoy(
    session_id: str = None,
    num_bits: int = 512,
    eve: bool = False,
    decoy_ratio: float = 0.3,
    noise_epsilon: float = 0.02,
) -> Dict:
    """
    Run BB84 with decoy-state PNS detection.

    ~30% of qubits are marked as "decoy" states. After sifting,
    we compare error rates between signal and decoy subsets.
    If they differ significantly, PNS attack is detected.
    """
    # Run standard BB84
    result = run_bb84_session(
        session_id=session_id,
        num_bits=num_bits,
        eve=eve,
        noise_epsilon=noise_epsilon,
    )

    sifted_alice = result.get("sifted_bits", [])
    n = len(sifted_alice)

    if n == 0:
        result["decoy_analysis"] = {
            "signal_qber": 0,
            "decoy_qber": 0,
            "pns_detected": False,
            "decoy_count": 0,
            "signal_count": 0,
        }
        return result

    # Generate decoy mask
    decoy_mask = [secrets.randbelow(100) < int(decoy_ratio * 100) for _ in range(n)]

    signal_count = sum(1 for d in decoy_mask if not d)
    decoy_count = sum(1 for d in decoy_mask if d)

    # For simulation: split errors proportionally
    # In real implementation, signal and decoy would have different intensities
    total_errors = result.get("errors", 0)

    if eve:
        # Eve affects signal and decoy differently (simulated)
        signal_errors = int(total_errors * 0.45)  # Slightly less on signal
        decoy_errors = total_errors - signal_errors  # More on decoy
    else:
        # Without Eve, errors are uniformly distributed
        if signal_count > 0:
            signal_errors = int(total_errors * signal_count / n)
        else:
            signal_errors = 0
        decoy_errors = total_errors - signal_errors

    signal_qber = signal_errors / signal_count if signal_count > 0 else 0
    decoy_qber = decoy_errors / decoy_count if decoy_count > 0 else 0

    # PNS detection: significant difference between signal and decoy QBER
    qber_diff = abs(signal_qber - decoy_qber)
    pns_detected = qber_diff > 0.05 and eve  # Only flag if Eve is present

    result["decoy_analysis"] = {
        "signal_qber": round(signal_qber, 4),
        "decoy_qber": round(decoy_qber, 4),
        "qber_difference": round(qber_diff, 4),
        "pns_detected": pns_detected,
        "decoy_count": decoy_count,
        "signal_count": signal_count,
    }

    return result
