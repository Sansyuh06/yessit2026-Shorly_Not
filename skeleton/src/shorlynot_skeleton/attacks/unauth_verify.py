"""
Unauthorized Verification Attack Simulation.
SIH 2026 PS 26141.
"""



class UnauthVerifyAttack:
    """
    Simulates an unauthorized rogue party or invalid node attempting to execute verification
    without registered verifier credentials.
    """

    UNAUTHORIZED_VERIFIERS = ["rogue_node_99", "eve_observer", "mallory_interceptor", "unknown_external"]

    @classmethod
    def get_unauthorized_verifier_id(cls, index: int = 0) -> str:
        return cls.UNAUTHORIZED_VERIFIERS[index % len(cls.UNAUTHORIZED_VERIFIERS)]
