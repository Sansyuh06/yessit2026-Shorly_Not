"""
BB84 QKD Session Key Exchange Simulator.
Support layer for ShorlyNot Quantum Security Pipeline.
"""

import hashlib
import os
import time
import uuid
from typing import Tuple, List, Optional
import numpy as np


class QkdSessionResult:
    def __init__(
        self,
        session_id: str,
        session_key: bytes,
        qber: float,
        sifted_bits_count: int,
        channel_status: str
    ):
        self.session_id = session_id
        self.session_key = session_key
        self.qber = qber
        self.sifted_bits_count = sifted_bits_count
        self.channel_status = channel_status


class Bb84Simulator:
    """
    Simulates BB84 protocol for quantum key distribution between Alice and Bob.
    Computes Quantum Bit Error Rate (QBER) and outputs a 256-bit symmetric session key.
    """

    def __init__(self, baseline_qber: float = 0.025, raw_bits_count: int = 512):
        self.baseline_qber = baseline_qber
        self.raw_bits_count = raw_bits_count

    def negotiate_session(self, inject_eavesdropper: bool = False, eve_intercept_prob: float = 0.5) -> QkdSessionResult:
        """
        Execute BB84 key exchange session simulation.
        """
        session_id = f"qkd-sess-{uuid.uuid4().hex[:12]}"
        
        # 1. Alice generates random bits and random bases (0 = Z, 1 = X)
        alice_bits = np.random.randint(0, 2, size=self.raw_bits_count)
        alice_bases = np.random.randint(0, 2, size=self.raw_bits_count)

        # 2. Channel transmission (optional Eve interception)
        channel_bits = np.copy(alice_bits)
        if inject_eavesdropper:
            # Eve intercepts and measures in random bases
            eve_bases = np.random.randint(0, 2, size=self.raw_bits_count)
            # When Eve's basis mismatches Alice's, state collapses with 50% error probability
            for i in range(self.raw_bits_count):
                if np.random.random() < eve_intercept_prob:
                    if eve_bases[i] != alice_bases[i]:
                        channel_bits[i] = np.random.randint(0, 2)

        # 3. Bob chooses random measurement bases
        bob_bases = np.random.randint(0, 2, size=self.raw_bits_count)
        bob_bits = np.copy(channel_bits)

        # Simulate honest channel noise (depolarizing)
        for i in range(self.raw_bits_count):
            if np.random.random() < self.baseline_qber:
                bob_bits[i] = 1 - bob_bits[i]

        # 4. Sifting (keep only matching bases)
        matching_indices = np.where(alice_bases == bob_bases)[0]
        alice_sifted = alice_bits[matching_indices]
        bob_sifted = bob_bits[matching_indices]

        sifted_len = len(alice_sifted)
        if sifted_len < 64:
            # If sifted pool too small, fallback with fresh random bytes
            raw_key = os.urandom(32)
            return QkdSessionResult(session_id, raw_key, self.baseline_qber, sifted_len, "suboptimal_sifting")

        # 5. Error estimation on 25% of sifted bits
        test_sample_size = min(64, sifted_len // 4)
        sample_indices = np.random.choice(sifted_len, size=test_sample_size, replace=False)
        
        errors = np.sum(alice_sifted[sample_indices] != bob_sifted[sample_indices])
        qber = float(errors) / float(test_sample_size)

        # Remaining bits used for key material
        key_indices = np.setdiff1d(np.arange(sifted_len), sample_indices)
        final_key_bits = alice_sifted[key_indices]

        # 6. Privacy amplification: hash sifted bits to derive 256-bit session key
        bit_bytes = np.packbits(final_key_bits).tobytes()
        session_key = hashlib.sha256(bit_bytes + session_id.encode()).digest()

        channel_status = "healthy" if qber < 0.08 else ("elevated_noise" if qber < 0.11 else "intercepted")

        return QkdSessionResult(
            session_id=session_id,
            session_key=session_key,
            qber=round(qber, 4),
            sifted_bits_count=sifted_len,
            channel_status=channel_status
        )
