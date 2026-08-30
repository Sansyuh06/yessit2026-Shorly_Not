"""Optical telemetry anomaly detection engine.

Uses rolling windows to detect anomalies in optical channel data.
This is labelled as an OPTICAL QKD PRINCIPLE DEMONSTRATOR, NOT
a true single-photon QKD device.

PRD §20.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class AnomalyReport:
    """Report from the optical anomaly detector."""

    window_size: int = 0
    valid_frames: int = 0
    intensity_mean: float = 0.0
    intensity_std: float = 0.0
    bit_disagreement_rate: float = 0.0
    basis_matched_disagreement_rate: float = 0.0
    frame_loss_rate: float = 0.0
    sequence_gaps: int = 0
    anomaly_detected: bool = False
    anomaly_reasons: list[str] = field(default_factory=list)
    # Label: OPTICAL QKD PRINCIPLE DEMONSTRATOR
    demonstrator_type: str = "OPTICAL QKD PRINCIPLE DEMONSTRATOR"


class OpticalAnomalyEngine:
    """Rolling-window anomaly detector for optical telemetry frames.

    Maintains a window of valid frames and computes statistical
    measures to detect channel anomalies.
    """

    def __init__(
        self,
        window_size: int = 100,
        intensity_anomaly_threshold: float = 3.0,  # std deviations
        disagreement_threshold: float = 0.15,
    ) -> None:
        self._window_size = window_size
        self._intensity_threshold = intensity_anomaly_threshold
        self._disagreement_threshold = disagreement_threshold

        # Rolling window data
        self._intensities: deque[float] = deque(maxlen=window_size)
        self._alice_bits: deque[Optional[int]] = deque(maxlen=window_size)
        self._alice_bases: deque[Optional[int]] = deque(maxlen=window_size)
        self._bob_bits: deque[Optional[int]] = deque(maxlen=window_size)
        self._bob_bases: deque[Optional[int]] = deque(maxlen=window_size)
        self._sequences: deque[int] = deque(maxlen=window_size)

        self._total_frames = 0
        self._valid_frames = 0
        self._invalid_frames = 0
        self._last_sequence: Optional[int] = None
        self._total_gaps = 0

    def ingest_frame(
        self,
        sequence: int,
        normalized_intensity: float,
        alice_basis: Optional[int] = None,
        alice_bit: Optional[int] = None,
        bob_basis: Optional[int] = None,
        bob_bit: Optional[int] = None,
        frame_valid: bool = True,
    ) -> None:
        """Ingest a validated telemetry frame into the rolling window."""
        self._total_frames += 1

        if not frame_valid:
            self._invalid_frames += 1
            return

        self._valid_frames += 1

        # Track sequence gaps
        if self._last_sequence is not None:
            gap = sequence - self._last_sequence - 1
            if gap > 0:
                self._total_gaps += gap
        self._last_sequence = sequence

        # Add to rolling window
        self._intensities.append(normalized_intensity)
        self._alice_bits.append(alice_bit)
        self._alice_bases.append(alice_basis)
        self._bob_bits.append(bob_bit)
        self._bob_bases.append(bob_basis)
        self._sequences.append(sequence)

    def analyze(self) -> AnomalyReport:
        """Analyze current window for anomalies."""
        n = len(self._intensities)
        if n == 0:
            return AnomalyReport()

        # Intensity statistics
        intensities = np.array(list(self._intensities))
        mean_i = float(np.mean(intensities))
        std_i = float(np.std(intensities)) if n > 1 else 0.0

        # Bit disagreement rate (all pairs)
        disagreements = 0
        compared = 0
        for i in range(n):
            if self._alice_bits[i] is not None and self._bob_bits[i] is not None:
                compared += 1
                if self._alice_bits[i] != self._bob_bits[i]:
                    disagreements += 1
        bit_disagreement = disagreements / compared if compared > 0 else 0.0

        # Basis-matched disagreement rate
        basis_disagreements = 0
        basis_compared = 0
        for i in range(n):
            if (self._alice_bits[i] is not None
                    and self._bob_bits[i] is not None
                    and self._alice_bases[i] is not None
                    and self._bob_bases[i] is not None
                    and self._alice_bases[i] == self._bob_bases[i]):
                basis_compared += 1
                if self._alice_bits[i] != self._bob_bits[i]:
                    basis_disagreements += 1
        basis_disagreement = basis_disagreements / basis_compared if basis_compared > 0 else 0.0

        # Frame loss rate
        frame_loss = self._invalid_frames / self._total_frames if self._total_frames > 0 else 0.0

        # Sequence gaps in window
        gaps = 0
        seqs = list(self._sequences)
        for i in range(1, len(seqs)):
            if seqs[i] - seqs[i - 1] > 1:
                gaps += seqs[i] - seqs[i - 1] - 1

        # Anomaly detection
        reasons = []
        anomaly = False

        if std_i > 0 and n >= 10:
            # Check for intensity anomalies (sudden changes)
            recent = intensities[-min(10, n):]
            recent_mean = float(np.mean(recent))
            if abs(recent_mean - mean_i) > self._intensity_threshold * std_i:
                anomaly = True
                reasons.append(
                    f"Intensity shift: recent_mean={recent_mean:.3f}, "
                    f"window_mean={mean_i:.3f}, std={std_i:.3f}"
                )

        if basis_disagreement > self._disagreement_threshold:
            anomaly = True
            reasons.append(
                f"High basis-matched disagreement: {basis_disagreement:.3f} "
                f"> threshold {self._disagreement_threshold:.3f}"
            )

        if frame_loss > 0.2:
            anomaly = True
            reasons.append(f"High frame loss rate: {frame_loss:.3f}")

        if gaps > n * 0.1:
            anomaly = True
            reasons.append(f"Excessive sequence gaps: {gaps} in window of {n}")

        return AnomalyReport(
            window_size=n,
            valid_frames=self._valid_frames,
            intensity_mean=round(mean_i, 4),
            intensity_std=round(std_i, 4),
            bit_disagreement_rate=round(bit_disagreement, 4),
            basis_matched_disagreement_rate=round(basis_disagreement, 4),
            frame_loss_rate=round(frame_loss, 4),
            sequence_gaps=gaps,
            anomaly_detected=anomaly,
            anomaly_reasons=reasons,
        )

    def reset(self) -> None:
        """Reset the anomaly engine."""
        self._intensities.clear()
        self._alice_bits.clear()
        self._alice_bases.clear()
        self._bob_bits.clear()
        self._bob_bases.clear()
        self._sequences.clear()
        self._total_frames = 0
        self._valid_frames = 0
        self._invalid_frames = 0
        self._last_sequence = None
        self._total_gaps = 0
