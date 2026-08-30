"""
Recovery Manager — Incident Logging & Structured Recovery
==========================================================
When L4 lockdown is triggered, log the full incident and provide
a structured recovery workflow requiring authentication.
"""

import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SecurityIncident:
    id: str
    timestamp: float
    trigger: str
    escalation_level: int
    qber_at_trigger: float
    sessions_affected: int
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_notes: str = ""


class RecoveryManager:
    """Manages security incidents and system recovery."""

    RECOVERY_TOKEN = "RECOVERY-ADMIN-2026"

    def __init__(self):
        self.incidents: List[SecurityIncident] = []
        self.recovery_log: List[Dict] = []

    def log_incident(
        self,
        trigger: str,
        escalation_level: int,
        qber: float,
        sessions_affected: int = 0,
    ) -> SecurityIncident:
        """Log a new security incident."""
        incident = SecurityIncident(
            id=uuid.uuid4().hex[:8],
            timestamp=time.time(),
            trigger=trigger,
            escalation_level=escalation_level,
            qber_at_trigger=qber,
            sessions_affected=sessions_affected,
        )
        self.incidents.append(incident)
        return incident

    def recover(self, incident_id: str, auth_token: str) -> Dict:
        """
        Structured recovery process.
        Requires authentication token.
        """
        if auth_token != self.RECOVERY_TOKEN:
            raise PermissionError("Invalid recovery token. Contact security officer.")

        incident = None
        for inc in self.incidents:
            if inc.id == incident_id and not inc.resolved:
                inc.resolved = True
                inc.resolved_at = time.time()
                incident = inc
                break

        if incident is None:
            raise ValueError(f"Incident {incident_id} not found or already resolved")

        recovery_entry = {
            "timestamp": time.time(),
            "incident_id": incident_id,
            "action": "system_recovery",
            "status": "recovered",
        }
        self.recovery_log.append(recovery_entry)

        return {
            "status": "recovered",
            "incident_id": incident_id,
            "message": "System restored to L0. All resources reset.",
        }

    def get_incidents(self, limit: int = 10) -> List[Dict]:
        """Get recent incidents."""
        recent = self.incidents[-limit:]
        return [
            {
                "id": inc.id,
                "timestamp": inc.timestamp,
                "trigger": inc.trigger,
                "escalation_level": inc.escalation_level,
                "qber": inc.qber_at_trigger,
                "resolved": inc.resolved,
            }
            for inc in reversed(recent)
        ]

    def get_stats(self) -> Dict:
        """Get incident statistics."""
        total = len(self.incidents)
        resolved = sum(1 for i in self.incidents if i.resolved)
        return {
            "total_incidents": total,
            "resolved": resolved,
            "unresolved": total - resolved,
        }
