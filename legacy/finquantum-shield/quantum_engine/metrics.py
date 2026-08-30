"""
Quantum Metrics — Scoring and observability functions.
"""


def quantum_entropy_score(
    qber: float, sifted_len: int, amplified_len: int, attacks_recent: int
) -> int:
    """
    Composite security score (0-100).

    Based on:
    - QBER distance from Shor-Preskill bound (11%)
    - Key compression ratio (privacy amplification efficiency)
    - Recent attack frequency (temporal risk)
    """
    # QBER component (0-40 points): lower is better
    if qber < 0.02:
        qber_score = 40
    elif qber < 0.05:
        qber_score = 30
    elif qber < 0.08:
        qber_score = 20
    elif qber < 0.11:
        qber_score = 10
    else:
        qber_score = 0

    # Key quality component (0-30 points): more amplified key = better
    if sifted_len > 0:
        compression = amplified_len / sifted_len
        key_score = min(30, int(compression * 40))
    else:
        key_score = 0

    # Attack frequency component (0-30 points): fewer recent attacks = better
    attack_penalty = min(30, attacks_recent * 10)
    attack_score = 30 - attack_penalty

    return qber_score + key_score + attack_score
