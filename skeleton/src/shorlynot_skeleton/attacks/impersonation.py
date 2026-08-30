"""
Impersonation Attack Simulation.
SIH 2026 PS 26141.
"""

from shorlynot_skeleton.models import SignatureBundle
from shorlynot_skeleton.qds.protocol import QdsT1Protocol


class ImpersonationAttack:
    """
    Simulates Eve attempting to sign a transfer claiming to be Alice,
    using either Eve's key_id or a forged arbitrary key_id.
    """

    @staticmethod
    def generate_impersonated_bundle(
        payload_hash: str,
        attacker_key_id: str = "eve-key-1",
        qds_protocol: QdsT1Protocol = None
    ) -> SignatureBundle:
        protocol = qds_protocol or QdsT1Protocol()
        # Eve signs properly with her own quantum device, but will submit it with claimed_signer='alice'
        bundle = protocol.sign(
            payload_hash=payload_hash,
            key_id=attacker_key_id,
            n_checks=64,
            L=128
        )
        return bundle
