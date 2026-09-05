"""
Signature Forgery Attack Simulation.
SIH 2026 PS 26141.
"""

import uuid
import numpy as np

from shorlynot_skeleton.models import SignatureBundle, QuantumBackend, QuantumEngine


class ForgeryAttack:
    """
    Simulates an attacker fabricating a signature bundle by generating random correction bits
    or uncorrelated basis choices without quantum entanglement with the verifier.
    Expected mismatch rate: ~0.50 (well above tau ~0.210).
    """

    @staticmethod
    def generate_forged_bundle(
        payload_hash: str,
        claimed_key_id: str = "alice-key-1",
        L: int = 128,
        n_checks: int = 64
    ) -> SignatureBundle:
        # Attacker picks random bases
        random_bases = [int(np.random.randint(0, 2)) for _ in range(L)]
        
        # Attacker guesses random Pauli syndromes (00, 01, 10, 11)
        random_syndromes = [
            [int(np.random.randint(0, 2)), int(np.random.randint(0, 2))]
            for _ in range(n_checks)
        ]

        bundle = SignatureBundle(
            payload_hash=payload_hash,
            key_id=claimed_key_id,
            nonce=str(uuid.uuid4()),
            profile="T1",
            bases=random_bases,
            correction_bits=random_syndromes,
            measurement_transcript={"attack": "forged_random_syndromes", "adversary": "eve"},
            backend=QuantumBackend.SIM,
            engine=QuantumEngine.QISKIT,
            pqc_mode="aes-gcm-demo",
            n_checks=n_checks,
            L=L
        )

        return bundle
