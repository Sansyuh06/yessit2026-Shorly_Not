"""
Quantum Key Management and Registration Subsystem.
SIH 2026 PS 26141 — ShorlyNot-QDS-T1 Key Provisioning & Binding.

Manages the quantum key generation ceremony, binding classical user identities
to QKD session keys and QDS signature credentials.
"""

import hashlib
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from shorlynot_skeleton.qkd.bb84 import Bb84Simulator


class KeyRecord(BaseModel):
    key_id: str
    user_id: str
    role: str = "customer"
    qkd_session_id: str
    key_fingerprint: str
    qber: float = 0.02
    created_at: float = Field(default_factory=time.time)
    status: str = "active"


class QuantumKeyRegistry:
    """
    Central registry for quantum digital signature (QDS) keys and QKD session bindings.
    """

    def __init__(self) -> None:
        self._keys: Dict[str, KeyRecord] = {}
        self._user_to_keys: Dict[str, List[str]] = {}
        self._simulator = Bb84Simulator()
        self._seed_default_keys()

    def _seed_default_keys(self) -> None:
        """Seed initial key bindings for demo accounts."""
        defaults = [
            ("alice", "alice-key-1", "customer"),
            ("bob", "bob-key-1", "customer"),
            ("carol", "carol-key-1", "customer"),
            ("eve", "eve-key-1", "attacker"),
            ("ops", "ops-key-1", "soc")
        ]
        for user_id, key_id, role in defaults:
            qkd_res = self._simulator.negotiate_session()
            fingerprint = hashlib.sha256(qkd_res.session_key).hexdigest()[:16]
            record = KeyRecord(
                key_id=key_id,
                user_id=user_id,
                role=role,
                qkd_session_id=qkd_res.session_id,
                key_fingerprint=f"QKD-SHA256:{fingerprint}",
                qber=qkd_res.qber,
                status="active"
            )
            self._keys[key_id] = record
            self._user_to_keys.setdefault(user_id, []).append(key_id)

    def provision_key_pair(
        self,
        user_id: str,
        role: str = "customer",
        custom_key_id: Optional[str] = None
    ) -> KeyRecord:
        """
        Execute a simulated QKD ceremony (BB84) and provision a new QDS key binding.
        """
        key_id = custom_key_id or f"{user_id}-qds-{uuid.uuid4().hex[:8]}"
        qkd_res = self._simulator.negotiate_session()
        fingerprint = hashlib.sha256(qkd_res.session_key).hexdigest()[:16]

        record = KeyRecord(
            key_id=key_id,
            user_id=user_id,
            role=role,
            qkd_session_id=qkd_res.session_id,
            key_fingerprint=f"QKD-SHA256:{fingerprint}",
            qber=qkd_res.qber,
            status="active"
        )
        self._keys[key_id] = record
        self._user_to_keys.setdefault(user_id, []).append(key_id)
        return record

    def validate_key_binding(self, key_id: str, claimed_user: str) -> bool:
        """
        Verify if a given key_id is registered and bound to the claimed user.
        """
        if key_id not in self._keys:
            return False
        return self._keys[key_id].user_id == claimed_user and self._keys[key_id].status == "active"

    def get_key(self, key_id: str) -> Optional[KeyRecord]:
        return self._keys.get(key_id)

    def list_keys(self) -> List[KeyRecord]:
        return list(self._keys.values())


# Global singleton registry
GLOBAL_KEY_REGISTRY = QuantumKeyRegistry()
