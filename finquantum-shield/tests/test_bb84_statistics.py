"""
Statistical validation of BB84 implementation.
Runs 100 sessions and verifies QBER follows expected distributions.
"""

import numpy as np
from quantum_engine.bb84_simulator import run_bb84_session


class TestBB84Statistics:
    def test_no_eve_qber_below_threshold(self):
        """Without Eve, QBER should stay below 5% (only noise)."""
        qbers = [run_bb84_session(num_bits=512)["qber"] for _ in range(50)]
        assert np.mean(qbers) < 0.05, f"Mean QBER {np.mean(qbers):.4f} too high"
        assert max(qbers) < 0.11, f"Max QBER {max(qbers):.4f} breached threshold"

    def test_eve_qber_near_25_percent(self):
        """With Eve intercept-resend, QBER should be ~25%."""
        qbers = [run_bb84_session(num_bits=512, eve=True)["qber"] for _ in range(50)]
        mean_qber = np.mean(qbers)
        assert 0.18 < mean_qber < 0.32, f"Mean Eve QBER {mean_qber:.4f} not ~25%"

    def test_sifted_key_length_approximately_half(self):
        """~50% of bases should match (sifting retains ~half)."""
        for _ in range(20):
            result = run_bb84_session(num_bits=1024)
            ratio = result["sifted_key_length"] / 1024
            assert 0.35 < ratio < 0.65, f"Sift ratio {ratio:.2f} outside expected range"

    def test_privacy_amplification_reduces_key(self):
        """Privacy amplification must compress the key."""
        from quantum_engine.bb84_simulator import privacy_amplification
        import secrets

        bits = [secrets.randbelow(2) for _ in range(512)]
        amplified = privacy_amplification(bits, output_bits=128)
        assert len(amplified) == 16  # 128 bits = 16 bytes

    def test_different_sessions_produce_different_keys(self):
        """Two sessions should never produce the same key."""
        r1 = run_bb84_session(num_bits=256)
        r2 = run_bb84_session(num_bits=256)
        assert r1["raw_key"] != r2["raw_key"], "Key collision detected!"

    def test_qber_with_high_noise(self):
        """With high depolarizing noise, QBER should rise."""
        result = run_bb84_session(num_bits=512, noise_epsilon=0.20)
        assert result["qber"] > 0.05, "High noise should raise QBER"
