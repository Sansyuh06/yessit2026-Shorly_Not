"""
Channel Tampering / Man-in-the-Middle Attack Simulation.
SIH 2026 PS 26141.
"""

from typing import List
import numpy as np
from shorlynot_skeleton.models import SignatureBundle


class ChannelTamperingAttack:
    """
    Simulates man-in-the-middle channel manipulation by flipping Pauli correction syndromes
    or corrupting the PQC payload in transit.
    """

    @staticmethod
    def tamper_correction_bits(bundle: SignatureBundle, flip_rate: float = 0.5) -> SignatureBundle:
        tampered_bundle = bundle.model_copy(deep=True)
        tampered_corrections = []
        for pair in tampered_bundle.correction_bits:
            m1, m2 = pair
            if np.random.random() < flip_rate:
                m1 = 1 - m1
            if np.random.random() < flip_rate:
                m2 = 1 - m2
            tampered_corrections.append([m1, m2])
        
        tampered_bundle.correction_bits = tampered_corrections
        tampered_bundle.measurement_transcript["channel_tampered"] = True
        return tampered_bundle

    @staticmethod
    def corrupt_pqc_ciphertext(bundle: SignatureBundle) -> SignatureBundle:
        tampered_bundle = bundle.model_copy(deep=True)
        if tampered_bundle.protected_corrections:
            # Corrupt ciphertext bytes
            raw = list(tampered_bundle.protected_corrections)
            if len(raw) > 10:
                raw[5] = 'X' if raw[5] != 'X' else 'Y'
            tampered_bundle.protected_corrections = "".join(raw)
        return tampered_bundle
