"""
PQC Correction Bit Protector using AES-256-GCM / HKDF.
Protects classical syndrome bits (m1, m2) transmitted across classical channels.
Normative specification from PRD §B6.
"""

import base64
import json
import os
from typing import List, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


class CorrectionBitProtector:
    """
    Wraps and unwraps Pauli correction syndrome bits using AES-256-GCM
    with keys derived from QKD session material.
    """

    @staticmethod
    def derive_encryption_key(session_key: bytes, context: str = "shorlynot-pqc-wrap") -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=context.encode(),
        )
        return hkdf.derive(session_key)

    @classmethod
    def protect(cls, correction_bits: List[List[int]], session_key: bytes) -> str:
        """
        Encrypt and authenticate correction bits.
        Returns base64 encoded payload: nonce (12B) + ciphertext + tag (16B).
        """
        key = cls.derive_encryption_key(session_key)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        plaintext = json.dumps(correction_bits).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        payload = nonce + ciphertext
        return base64.b64encode(payload).decode("utf-8")

    @classmethod
    def unprotect(cls, protected_base64: str, session_key: bytes) -> Tuple[bool, Optional[List[List[int]]]]:
        """
        Decrypt and verify authenticated correction bits.
        Returns (success, correction_bits).
        """
        try:
            payload = base64.b64decode(protected_base64)
            if len(payload) < 28:
                return False, None
            nonce = payload[:12]
            ciphertext = payload[12:]
            key = cls.derive_encryption_key(session_key)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            bits = json.loads(plaintext.decode("utf-8"))
            return True, bits
        except Exception:
            return False, None
