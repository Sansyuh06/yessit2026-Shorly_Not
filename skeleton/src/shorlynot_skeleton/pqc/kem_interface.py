import hashlib
import hmac
import os
from typing import Tuple
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


class MlKem768Interface:
    """
    Demo KEM with an ML-KEM-768-shaped API (NIST FIPS 203 key sizes). NOT a real ML-KEM implementation — a self-consistent HKDF/HMAC commit-verify scheme. Swap in kyber-py or liboqs-python for a real FIPS 203 KEM without changing this interface.
    """

    ALGORITHM_NAME = "HKDF/HMAC demo KEM (ML-KEM-768-shaped API, not real ML-KEM)"
    PUBLIC_KEY_SIZE = 1184
    CIPHERTEXT_SIZE = 1088
    SHARED_SECRET_SIZE = 32

    @classmethod
    def keypair(cls) -> Tuple[bytes, bytes]:
        """
        Generate (public_key, secret_key).
        """
        seed = os.urandom(32)
        # Seed-derived public and private key buffers adhering to FIPS 203 byte lengths
        pk_hash = hashlib.sha3_256(seed + b"ml-kem-768-pk").digest()
        public_key = pk_hash + (b"\x00" * (cls.PUBLIC_KEY_SIZE - 32))
        secret_key = seed + pk_hash + (b"\x00" * (cls.PUBLIC_KEY_SIZE - 32))
        return public_key, secret_key

    @classmethod
    def encapsulate(cls, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Encapsulate shared secret using public key.
        Returns (ciphertext, shared_secret).
        """
        ephemeral_seed = os.urandom(32)
        pk_hash = public_key[:32]
        
        # Derive 32-byte shared secret via HKDF
        hkdf_ss = HKDF(
            algorithm=hashes.SHA256(),
            length=cls.SHARED_SECRET_SIZE,
            salt=pk_hash,
            info=b"ml-kem-768-shared-secret"
        )
        shared_secret = hkdf_ss.derive(ephemeral_seed)

        # Ciphertext commits to ephemeral seed and authenticated tag
        tag = hmac.new(shared_secret, ephemeral_seed + pk_hash, hashlib.sha256).digest()
        ciphertext = ephemeral_seed + tag + (b"\x00" * (cls.CIPHERTEXT_SIZE - 64))
        return ciphertext, shared_secret

    @classmethod
    def decapsulate(cls, ciphertext: bytes, secret_key: bytes) -> bytes:
        """
        Decapsulate shared secret using secret key.
        Verifies authentication tag and recovers exact shared secret.
        """
        if len(ciphertext) < 64:
            raise ValueError("Invalid ciphertext length for ML-KEM-768")

        ephemeral_seed = ciphertext[:32]
        received_tag = ciphertext[32:64]
        pk_hash = secret_key[32:64]

        # Re-derive shared secret
        hkdf_ss = HKDF(
            algorithm=hashes.SHA256(),
            length=cls.SHARED_SECRET_SIZE,
            salt=pk_hash,
            info=b"ml-kem-768-shared-secret"
        )
        shared_secret = hkdf_ss.derive(ephemeral_seed)

        # Verify integrity tag
        expected_tag = hmac.new(shared_secret, ephemeral_seed + pk_hash, hashlib.sha256).digest()
        if not hmac.compare_digest(received_tag, expected_tag):
            raise ValueError("ML-KEM-768 decapsulation authentication tag mismatch (tampered ciphertext)")

        return shared_secret
