"""Ed25519 lease signer for QKBNL leases.

Uses the `cryptography` library for constant-time signature
verification. Never implements custom cryptographic primitives.

PRD §15.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from packages.common.schemas import QKBNLLeasePayload


class LeaseSigner:
    """Signs QKBNL lease payloads using Ed25519."""

    def __init__(
        self,
        private_key: Optional[Ed25519PrivateKey] = None,
        private_key_path: Optional[str] = None,
    ) -> None:
        if private_key is not None:
            self._private_key = private_key
        elif private_key_path is not None:
            self._private_key = self._load_private_key(private_key_path)
        else:
            raise ValueError("Either private_key or private_key_path must be provided")

        self._public_key = self._private_key.public_key()
        self._key_id = self._compute_key_id()

    @property
    def key_id(self) -> str:
        """SHA-256 fingerprint of the public key (first 16 hex chars)."""
        return self._key_id

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self._public_key

    def sign_lease(self, payload: QKBNLLeasePayload) -> str:
        """Sign a canonical lease payload.

        Args:
            payload: The lease payload to sign.

        Returns:
            Base64-encoded Ed25519 signature string.
        """
        canonical = payload.canonical_json()
        signature_bytes = self._private_key.sign(canonical.encode("utf-8"))
        return base64.b64encode(signature_bytes).decode("ascii")

    def verify_lease(self, payload: QKBNLLeasePayload, signature_b64: str) -> bool:
        """Verify a lease signature.

        Uses constant-time verification through the cryptography library.

        Args:
            payload: The lease payload.
            signature_b64: Base64-encoded signature.

        Returns:
            True if signature is valid.
        """
        try:
            canonical = payload.canonical_json()
            signature_bytes = base64.b64decode(signature_b64)
            self._public_key.verify(signature_bytes, canonical.encode("utf-8"))
            return True
        except Exception:
            return False

    def export_public_key_pem(self) -> bytes:
        """Export the public key in PEM format."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def _compute_key_id(self) -> str:
        """Compute a key ID from the public key bytes."""
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return hashlib.sha256(pub_bytes).hexdigest()[:16]

    @staticmethod
    def _load_private_key(path: str) -> Ed25519PrivateKey:
        """Load an Ed25519 private key from a PEM file."""
        key_path = Path(path)
        if not key_path.exists():
            raise FileNotFoundError(f"Private key file not found: {path}")

        key_data = key_path.read_bytes()
        private_key = serialization.load_pem_private_key(key_data, password=None)

        if not isinstance(private_key, Ed25519PrivateKey):
            raise TypeError(f"Expected Ed25519 private key, got {type(private_key).__name__}")

        return private_key

    @staticmethod
    def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """Generate a new Ed25519 keypair for development/testing."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def save_keypair(
        private_key: Ed25519PrivateKey,
        private_key_path: str,
        public_key_path: str,
    ) -> None:
        """Save an Ed25519 keypair to PEM files."""
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        Path(private_key_path).write_bytes(priv_pem)
        Path(public_key_path).write_bytes(pub_pem)


class LeaseVerifier:
    """Verifies QKBNL lease signatures using Ed25519 public keys.

    Used by the router agent to validate incoming leases.
    """

    def __init__(self) -> None:
        self._known_keys: dict[str, Ed25519PublicKey] = {}

    def register_key(self, key_id: str, public_key: Ed25519PublicKey) -> None:
        """Register a known signing public key."""
        self._known_keys[key_id] = public_key

    def load_public_key(self, key_id: str, path: str) -> None:
        """Load and register a public key from PEM file."""
        key_data = Path(path).read_bytes()
        public_key = serialization.load_pem_public_key(key_data)
        if not isinstance(public_key, Ed25519PublicKey):
            raise TypeError(f"Expected Ed25519 public key, got {type(public_key).__name__}")
        self._known_keys[key_id] = public_key

    def verify(self, key_id: str, payload: QKBNLLeasePayload, signature_b64: str) -> bool:
        """Verify a lease signature using a registered public key.

        Args:
            key_id: The signing key identifier.
            payload: The lease payload.
            signature_b64: Base64-encoded signature.

        Returns:
            True if valid.

        Raises:
            KeyError: If key_id is not registered.
        """
        if key_id not in self._known_keys:
            raise KeyError(f"Unknown signing key ID: {key_id}")

        try:
            public_key = self._known_keys[key_id]
            canonical = payload.canonical_json()
            signature_bytes = base64.b64decode(signature_b64)
            public_key.verify(signature_bytes, canonical.encode("utf-8"))
            return True
        except Exception:
            return False

    @property
    def registered_key_ids(self) -> list[str]:
        return list(self._known_keys.keys())
