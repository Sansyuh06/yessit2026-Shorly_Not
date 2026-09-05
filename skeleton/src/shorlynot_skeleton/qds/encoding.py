"""
Pauli Eigenstate Encoding for ShorlyNot-QDS-T1.
Normative specification from PRD §3.4 and MODEL.md §3.
"""

import hashlib
from typing import List
import numpy as np


class PauliEncoding:
    """
    Encodes classical bits into single-qubit Pauli eigenstates:
    - b=0, beta=0 (Z basis): |0> = [1, 0]^T
    - b=1, beta=0 (Z basis): |1> = [0, 1]^T
    - b=0, beta=1 (X basis): |+> = (|0> + |1>) / sqrt(2)
    - b=1, beta=1 (X basis): |-> = (|0> - |1>) / sqrt(2)
    """

    STATE_0 = np.array([1.0, 0.0], dtype=np.complex128)
    STATE_1 = np.array([0.0, 1.0], dtype=np.complex128)
    STATE_PLUS = np.array([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)], dtype=np.complex128)
    STATE_MINUS = np.array([1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)], dtype=np.complex128)

    @classmethod
    def get_statevector(cls, bit: int, basis: int) -> np.ndarray:
        """
        Return the 2-element statevector for (bit, basis).
        bit in {0, 1}
        basis in {0 (Z), 1 (X)}
        """
        if basis == 0:
            return cls.STATE_0 if bit == 0 else cls.STATE_1
        elif basis == 1:
            return cls.STATE_PLUS if bit == 0 else cls.STATE_MINUS
        else:
            raise ValueError(f"Invalid basis choice: {basis}. Must be 0 (Z) or 1 (X).")

    @classmethod
    def derive_payload_bits(cls, payload_hash_hex: str, length: int = 128) -> List[int]:
        """
        Derive deterministic pseudorandom bit string from payload hash.
        """
        # Convert hex hash to bit array, expanding if necessary
        raw_bytes = bytes.fromhex(payload_hash_hex)
        bits = []
        for b in raw_bytes:
            for shift in range(7, -1, -1):
                bits.append((b >> shift) & 1)
        
        # Extend or slice to desired length
        while len(bits) < length:
            raw_bytes = hashlib.sha256(raw_bytes).digest()
            for b in raw_bytes:
                for shift in range(7, -1, -1):
                    bits.append((b >> shift) & 1)
                    
        return bits[:length]
