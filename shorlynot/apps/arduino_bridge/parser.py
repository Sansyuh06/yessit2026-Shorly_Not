"""QTEL frame parser for Arduino optical telemetry.

Parses newline-delimited frames in format:
    QTEL,version,sequence,timestamp_ms,detector_raw,alice_basis,alice_bit,bob_basis,eve_flag,crc

PRD §19.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apps.arduino_bridge.crc import validate_frame_crc
from packages.common.errors import SerialCRCFailedError, SerialFrameInvalidError


@dataclass
class QTELFrame:
    """Parsed QTEL telemetry frame."""

    version: int
    sequence: int
    timestamp_ms: int
    detector_raw: int
    alice_basis: int
    alice_bit: int
    bob_basis: int
    eve_flag: int
    crc_valid: bool
    raw_line: str


def parse_qtel_frame(line: str) -> QTELFrame:
    """Parse a single QTEL frame line.

    Args:
        line: Raw line from serial port.

    Returns:
        Parsed QTELFrame.

    Raises:
        SerialFrameInvalidError: If the frame is malformed.
        SerialCRCFailedError: If CRC validation fails.
    """
    line = line.strip()
    if not line:
        raise SerialFrameInvalidError("Empty frame")

    parts = line.split(",")
    if len(parts) != 10:
        raise SerialFrameInvalidError(
            f"Expected 10 comma-separated fields, got {len(parts)}: {line}"
        )

    # Validate header
    if parts[0] != "QTEL":
        raise SerialFrameInvalidError(f"Invalid header: expected 'QTEL', got '{parts[0]}'")

    try:
        version = int(parts[1])
        sequence = int(parts[2])
        timestamp_ms = int(parts[3])
        detector_raw = int(parts[4])
        alice_basis = int(parts[5])
        alice_bit = int(parts[6])
        bob_basis = int(parts[7])
        eve_flag = int(parts[8])
        crc_value = int(parts[9])
    except ValueError as e:
        raise SerialFrameInvalidError(f"Non-integer field in frame: {e}")

    # Validate field ranges
    if version != 1:
        raise SerialFrameInvalidError(f"Unsupported protocol version: {version}")

    if alice_basis not in (0, 1):
        raise SerialFrameInvalidError(f"Invalid alice_basis: {alice_basis}")

    if alice_bit not in (0, 1):
        raise SerialFrameInvalidError(f"Invalid alice_bit: {alice_bit}")

    if bob_basis not in (0, 1):
        raise SerialFrameInvalidError(f"Invalid bob_basis: {bob_basis}")

    if eve_flag not in (0, 1):
        raise SerialFrameInvalidError(f"Invalid eve_flag: {eve_flag}")

    # CRC validation
    crc_valid = validate_frame_crc(line)
    if not crc_valid:
        raise SerialCRCFailedError(f"CRC mismatch for frame seq={sequence}")

    return QTELFrame(
        version=version,
        sequence=sequence,
        timestamp_ms=timestamp_ms,
        detector_raw=detector_raw,
        alice_basis=alice_basis,
        alice_bit=alice_bit,
        bob_basis=bob_basis,
        eve_flag=eve_flag,
        crc_valid=crc_valid,
        raw_line=line,
    )


def normalize_intensity(
    raw_value: int,
    dark_level: int,
    bright_level: int,
) -> float:
    """Normalize detector value to [0, 1] range.

    Args:
        raw_value: Raw ADC reading from detector.
        dark_level: Calibrated dark reference.
        bright_level: Calibrated bright reference.

    Returns:
        Normalized intensity clamped to [0, 1].

    Raises:
        CalibrationInvalidError: If bright_level <= dark_level.
    """
    from packages.common.errors import CalibrationInvalidError

    if bright_level <= dark_level:
        raise CalibrationInvalidError(
            f"bright_level ({bright_level}) must exceed dark_level ({dark_level})"
        )

    normalized = (raw_value - dark_level) / (bright_level - dark_level)
    return max(0.0, min(1.0, normalized))
