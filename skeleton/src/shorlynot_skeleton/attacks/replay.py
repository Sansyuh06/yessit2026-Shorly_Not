"""
Replay Attack Simulation.
SIH 2026 PS 26141.
"""

from shorlynot_skeleton.models import SignatureBundle


class ReplayAttack:
    """
    Simulates an attacker capturing a legitimate, previously accepted SignatureBundle
    and re-submitting it for a duplicate transaction or repeated execution.
    """

    @staticmethod
    def create_replayed_bundle(original_bundle: SignatureBundle) -> SignatureBundle:
        # Re-use exact same nonce, payload hash, and quantum syndromes
        return original_bundle.model_copy(deep=True)
