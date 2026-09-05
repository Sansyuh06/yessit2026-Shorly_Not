"""
Bob-side Entanglement Session Store for ShorlyNot-QDS-T1.
SIH 2026 PS 26141 — Ground Truth Session Management.

Physical Justification:
With real quantum hardware, Bob's measurement of his half of the pre-shared
Bell pair (|Phi+>) provides the physical ground truth. The session store
simulates Bob's side of the distributed entanglement resource.
"""

import time
import collections
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EntanglementSession:
    """
    Session record representing Bob's half of the pre-shared Bell state.
    """
    nonce: str
    key_id: str
    alice_bell_measurements: List[List[int]]
    bases: List[int]
    payload_hash: str
    created_at: float = field(default_factory=time.time)
    n_checks: int = 64
    L: int = 128


class EntanglementSessionStore:
    """
    In-memory / server-side session registry simulating Bob's entanglement resource.
    During sign(), Alice's teleportation outcomes are bound to the session.
    During verify(), Bob reads ground truth solely from this store — never from the bundle transcript.
    """

    def __init__(self, max_sessions: int = 10000, ttl_seconds: float = 3600.0) -> None:
        self._sessions: collections.OrderedDict[str, EntanglementSession] = collections.OrderedDict()
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds

    def record_session(
        self,
        nonce: str,
        key_id: str,
        alice_bell_measurements: List[List[int]],
        bases: List[int],
        payload_hash: str,
        n_checks: int = 64,
        L: int = 128
    ) -> EntanglementSession:
        """
        Record Bob's ground-truth entanglement session upon signature generation.
        """
        if len(self._sessions) >= self.max_sessions:
            self._sessions.popitem(last=False)

        session = EntanglementSession(
            nonce=nonce,
            key_id=key_id,
            alice_bell_measurements=alice_bell_measurements,
            bases=bases,
            payload_hash=payload_hash,
            created_at=time.time(),
            n_checks=n_checks,
            L=L
        )
        self._sessions[nonce] = session
        return session

    def get_session(self, nonce: str) -> Optional[EntanglementSession]:
        """
        Retrieve ground truth session for Bob's verification check.
        Returns None if session does not exist or has expired.
        """
        session = self._sessions.get(nonce)
        if not session:
            return None

        # Check TTL expiration
        if time.time() - session.created_at > self.ttl_seconds:
            self._sessions.pop(nonce, None)
            return None

        return session

    def clear(self) -> None:
        """Purge all active sessions (e.g. on admin reset)."""
        self._sessions.clear()


# Global Bob-side session store instance
GLOBAL_ENTANGLEMENT_STORE = EntanglementSessionStore()
