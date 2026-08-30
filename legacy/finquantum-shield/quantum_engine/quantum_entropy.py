"""
Quantum Entropy Score — Composite Security Metric
====================================================
Combines QBER, key quality, and attack history into a single 0-100 score.
Displayed prominently on the dashboard.
"""


def quantum_entropy_score(
    qber: float,
    sifted_length: int = 0,
    amplified_length: int = 0,
    attacks_recent: int = 0,
    total_sessions: int = 0,
    successful_sessions: int = 0,
) -> dict:
    """
    Calculate composite security score (0-100).

    Components:
      - QBER distance from threshold (0-40 points)
      - Key quality / compression ratio (0-30 points)
      - Attack frequency (0-30 points)
    """

    # ── QBER Component (0-40 points) ──
    if qber < 0.02:
        qber_score = 40
    elif qber < 0.05:
        qber_score = 30 + (0.05 - qber) / 0.03 * 10
    elif qber < 0.08:
        qber_score = 20 + (0.08 - qber) / 0.03 * 10
    elif qber < 0.11:
        qber_score = 10 + (0.11 - qber) / 0.03 * 10
    else:
        qber_score = 0

    # ── Key Quality Component (0-30 points) ──
    if sifted_length > 0 and amplified_length > 0:
        compression = amplified_length / sifted_length
        key_score = min(30, compression * 40)
    elif sifted_length > 0:
        key_score = 20
    else:
        key_score = 0

    # ── Attack Frequency Component (0-30 points) ──
    if attacks_recent == 0:
        attack_score = 30
    elif attacks_recent <= 2:
        attack_score = 20
    elif attacks_recent <= 5:
        attack_score = 10
    else:
        attack_score = 0

    total = round(qber_score + key_score + attack_score)
    total = max(0, min(100, total))

    # Determine grade
    if total >= 85:
        grade = "A"
        label = "EXCELLENT"
    elif total >= 70:
        grade = "B"
        label = "GOOD"
    elif total >= 50:
        grade = "C"
        label = "ELEVATED"
    elif total >= 25:
        grade = "D"
        label = "CRITICAL"
    else:
        grade = "F"
        label = "COMPROMISED"

    return {
        "score": total,
        "grade": grade,
        "label": label,
        "components": {
            "qber_score": round(qber_score, 1),
            "key_score": round(key_score, 1),
            "attack_score": round(attack_score, 1),
        },
        "inputs": {
            "qber": qber,
            "sifted_length": sifted_length,
            "amplified_length": amplified_length,
            "attacks_recent": attacks_recent,
        },
    }
