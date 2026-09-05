"""
Security Parameter Tampering & Downgrade Attack Simulation.
SIH 2026 PS 26141 Hardened Defense.
"""

import uuid

from shorlynot_skeleton.models import SignatureBundle, QuantumBackend, QuantumEngine


class ParameterTamperingAttack:
    """
    Simulates an attacker attempting a classical parameter downgrade attack
    by supplying a manipulated security parameter (e.g. n_checks = 1 or truncated arrays)
    to artificially inflate tau and bypass statistical threshold detection.
    """

    @staticmethod
    def generate_downgraded_bundle(
        payload_hash: str,
        claimed_key_id: str = "alice-key-1",
        tampered_n: int = 1
    ) -> SignatureBundle:
        """
        Create an adversarial bundle with an insecure, downgraded check length (e.g. n_checks=1).
        """
        bundle = SignatureBundle(
            payload_hash=payload_hash,
            key_id=claimed_key_id,
            nonce=str(uuid.uuid4()),
            profile="T1",
            bases=[0] * max(tampered_n, 1),
            correction_bits=[[0, 0]] * max(tampered_n, 1),
            measurement_transcript={"attack": "parameter_downgrade", "adversary": "eve", "tampered_n": tampered_n},
            backend=QuantumBackend.SIM,
            engine=QuantumEngine.QISKIT,
            pqc_mode="aes-gcm-demo",
            n_checks=tampered_n,
            L=max(tampered_n, 1)
        )
        return bundle
