"""CRC-16/CCITT-FALSE implementation for Arduino telemetry frames.

PRD §19: Frame format:
    QTEL,version,sequence,timestamp_ms,detector_raw,alice_basis,alice_bit,bob_basis,eve_flag,crc
"""

from __future__ import annotations


def crc16_ccitt_false(data: bytes, initial: int = 0xFFFF) -> int:
    """Calculate CRC-16/CCITT-FALSE.

    Polynomial: 0x1021
    Initial value: 0xFFFF
    Final XOR: 0x0000
    """
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return crc


def compute_frame_crc(frame_data: str) -> int:
    """Compute CRC for the data portion of a QTEL frame.

    The CRC covers everything before the last comma-separated CRC field.
    """
    # Everything up to (not including) the final ,<CRC>
    parts = frame_data.strip().rsplit(",", 1)
    if len(parts) != 2:
        raise ValueError(f"Cannot split frame for CRC: {frame_data}")

    payload = parts[0]
    return crc16_ccitt_false(payload.encode("ascii"))


def validate_frame_crc(frame_data: str) -> bool:
    """Validate the CRC of a complete QTEL frame.

    Returns True if the embedded CRC matches the computed CRC.
    """
    parts = frame_data.strip().rsplit(",", 1)
    if len(parts) != 2:
        return False

    try:
        embedded_crc = int(parts[1])
    except ValueError:
        return False

    computed = crc16_ccitt_false(parts[0].encode("ascii"))
    return embedded_crc == computed
