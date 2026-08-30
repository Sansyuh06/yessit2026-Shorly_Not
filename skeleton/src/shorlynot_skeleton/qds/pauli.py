"""
Pauli Correction Lookup Table and Unitary Operations for ShorlyNot-QDS-T1.
Normative specification from PRD §3.7 and MODEL.md §5 & §6.
"""

from typing import Tuple
import numpy as np


class PauliCorrections:
    """
    Standard Pauli teleportation correction lookup table:
    (m1, m2) -> Unitary Gate U:
    00 -> I  (Identity)
    01 -> X  (Bit flip)
    10 -> Z  (Phase flip)
    11 -> XZ (Bit & Phase flip == -iY up to global phase)
    """

    I_MAT = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
    X_MAT = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    Z_MAT = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    XZ_MAT = np.dot(X_MAT, Z_MAT)  # [[0, -1], [1, 0]]
    H_MAT = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)

    LOOKUP = {
        (0, 0): "I",
        (0, 1): "X",
        (1, 0): "Z",
        (1, 1): "XZ",
    }

    MATRIX_LOOKUP = {
        (0, 0): I_MAT,
        (0, 1): X_MAT,
        (1, 0): Z_MAT,
        (1, 1): XZ_MAT,
    }

    @classmethod
    def get_gate_name(cls, m1: int, m2: int) -> str:
        return cls.LOOKUP.get((m1, m2), "I")

    @classmethod
    def get_unitary_matrix(cls, m1: int, m2: int) -> np.ndarray:
        return cls.MATRIX_LOOKUP.get((m1, m2), cls.I_MAT)

    @classmethod
    def apply_correction(cls, state: np.ndarray, m1: int, m2: int) -> np.ndarray:
        """Apply Pauli correction matrix to 2-component statevector."""
        U = cls.get_unitary_matrix(m1, m2)
        return np.dot(U, state)

    @classmethod
    def apply_hadamard(cls, state: np.ndarray) -> np.ndarray:
        """Apply Hadamard matrix for X-basis measurement."""
        return np.dot(cls.H_MAT, state)
