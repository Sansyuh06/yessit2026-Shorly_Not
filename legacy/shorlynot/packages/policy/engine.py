"""Policy engine — evaluates QKD results and drives state transitions.

Connects QBER/CHSH analysis to policy state machine decisions.
All thresholds are configuration-driven.

PRD §21.
"""

from __future__ import annotations

from typing import Any, Optional

from packages.common.enums import PolicyState, QKDProtocol, SecurityStatus
from packages.common.errors import QKDSecurityThresholdFailedError
from packages.policy.state_machine import PolicyStateMachine


class PolicyEngine:
    """Evaluates security metrics and drives policy transitions."""

    def __init__(
        self,
        state_machine: Optional[PolicyStateMachine] = None,
        qber_warning: float = 0.08,
        qber_compromise: float = 0.11,
        chsh_threshold: float = 2.0,
    ) -> None:
        self._sm = state_machine or PolicyStateMachine()
        self._qber_warning = qber_warning
        self._qber_compromise = qber_compromise
        self._chsh_threshold = chsh_threshold
        
        # Security Escalation State (L1-L4)
        self.eve_active = False
        self.attacks_detected = 0
        self.escalation_level = 0
        self.escalation_label = "L0 — Normal"
        self.current_port = 8000
        self.current_ip = "192.168.1.100"
        self.current_network = "192.168.1.0/24"

    @property
    def state_machine(self) -> PolicyStateMachine:
        return self._sm

    @property
    def state(self) -> PolicyState:
        return self._sm.state

    def evaluate_bb84(
        self,
        qber: float,
        finite_key_secure: bool = True,
        protocol: QKDProtocol = QKDProtocol.BB84,
    ) -> tuple[SecurityStatus, PolicyState]:
        """Evaluate BB84/Decoy QBER against thresholds.

        Returns the security status and the new policy state.
        """
        # Process escalation logic
        self.process_escalation(qber)

        if qber < self._qber_warning and finite_key_secure and not self.eve_active:
            status = SecurityStatus.SECURE
            target = PolicyState.SECURE
        elif self.escalation_level < 4 and (qber < self._qber_compromise or self.eve_active):
            status = SecurityStatus.WARNING
            target = PolicyState.DEGRADED
        else:
            status = SecurityStatus.COMPROMISED
            target = PolicyState.COMPROMISED

        # Attempt transition
        if self._sm.can_transition_to(target):
            self._sm.transition(
                target,
                reason=f"{protocol.value} QBER={qber:.4f}, threshold_warn={self._qber_warning}, "
                       f"threshold_compromise={self._qber_compromise}",
                metadata={"qber": qber, "protocol": protocol.value},
            )
        elif target == PolicyState.COMPROMISED:
            # Force through COMPROMISED via available path
            self._force_compromise(f"{protocol.value} QBER={qber:.4f} exceeds threshold")

        return status, self._sm.state

    def evaluate_e91(
        self,
        chsh_s: float,
        confidence_conclusive: bool = True,
    ) -> tuple[SecurityStatus, PolicyState]:
        """Evaluate E91 CHSH S value against threshold."""
        if abs(chsh_s) > self._chsh_threshold and confidence_conclusive:
            status = SecurityStatus.SECURE
            target = PolicyState.SECURE
        elif not confidence_conclusive:
            status = SecurityStatus.WARNING
            target = PolicyState.DEGRADED
        else:
            status = SecurityStatus.COMPROMISED
            target = PolicyState.COMPROMISED

        # Attempt transition
        if self._sm.can_transition_to(target):
            self._sm.transition(
                target,
                reason=f"E91 CHSH S={chsh_s:.4f}, threshold={self._chsh_threshold}",
                metadata={"chsh_s": chsh_s},
            )
        elif target == PolicyState.COMPROMISED:
            self._force_compromise(f"E91 CHSH |S|={abs(chsh_s):.4f} ≤ threshold")

        return status, self._sm.state

    def initiate_revocation(self, reason: str) -> PolicyState:
        """Transition to REVOKING state when compromise is confirmed."""
        if self._sm.state == PolicyState.COMPROMISED:
            self._sm.transition(PolicyState.REVOKING, reason=reason)
        return self._sm.state

    def confirm_isolation(self, reason: str) -> PolicyState:
        """Confirm firewall isolation after revocation."""
        if self._sm.state == PolicyState.REVOKING:
            self._sm.transition(PolicyState.ISOLATED, reason=reason)
        return self._sm.state

    def start_pqc_recovery(self, reason: str) -> PolicyState:
        """Initiate PQC recovery from isolated state."""
        if self._sm.state == PolicyState.ISOLATED:
            self._sm.transition(PolicyState.PQC_RECOVERY, reason=reason)
        return self._sm.state

    def complete_recovery(self, reason: str) -> PolicyState:
        """Complete PQC recovery — restore to SECURE via RESTORING."""
        if self._sm.state == PolicyState.PQC_RECOVERY:
            self._sm.transition(PolicyState.RESTORING, reason=reason)
        if self._sm.state == PolicyState.RESTORING:
            self._sm.transition(PolicyState.SECURE, reason="Recovery complete")
        return self._sm.state

    def report_error(self, reason: str) -> PolicyState:
        """Transition to ERROR state."""
        if self._sm.can_transition_to(PolicyState.ERROR):
            self._sm.transition(PolicyState.ERROR, reason=reason)
        return self._sm.state

    def activate_eve(self) -> None:
        self.eve_active = True

    def deactivate_eve(self) -> None:
        self.eve_active = False

    def reset_escalation(self) -> None:
        self.eve_active = False
        self.attacks_detected = 0
        self.escalation_level = 0
        self.escalation_label = "L0 — Normal"
        self.current_port = 8000
        self.current_ip = "192.168.1.100"
        self.current_network = "192.168.1.0/24"
        self._sm.reset()

    def process_escalation(self, qber: float) -> int:
        """Process L1-L4 escalation based on repeated attacks."""
        if qber >= self._qber_warning or self.eve_active:
            self.attacks_detected += 1

            if self.attacks_detected < 7:
                self.escalation_level = 1
                self.escalation_label = "L1 — Port Rotation"
                self.current_port = 8000 + self.attacks_detected
            elif self.attacks_detected < 10:
                self.escalation_level = 2
                self.escalation_label = "L2 — IP Failover"
                self.current_ip = f"192.168.1.{100 + (self.attacks_detected - 7) * 50}"
            elif self.attacks_detected < 13:
                self.escalation_level = 3
                self.escalation_label = "L3 — Interface Switch"
                self.current_network = f"192.168.{self.attacks_detected - 8}.0/24"
                self.current_ip = f"192.168.{self.attacks_detected - 8}.100"
            else:
                self.escalation_level = 4
                self.escalation_label = "L4 — EMERGENCY LOCKDOWN"
                self._force_compromise("Escalation L4 Reached")

        return self.escalation_level

    def _force_compromise(self, reason: str) -> None:
        """Navigate to COMPROMISED through valid intermediate states."""
        current = self._sm.state

        # Path to COMPROMISED depends on current state
        if current == PolicyState.INITIALIZING:
            # Can't directly reach COMPROMISED from INITIALIZING
            # Must go through SECURE first
            if self._sm.can_transition_to(PolicyState.SECURE):
                self._sm.transition(PolicyState.SECURE, reason="Auto-transition for compromise path")
                self._sm.transition(PolicyState.COMPROMISED, reason=reason)
        elif current in (PolicyState.SECURE, PolicyState.OBSERVING, PolicyState.DEGRADED):
            if self._sm.can_transition_to(PolicyState.COMPROMISED):
                self._sm.transition(PolicyState.COMPROMISED, reason=reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self._sm.state.value,
            "thresholds": {
                "qber_warning": self._qber_warning,
                "qber_compromise": self._qber_compromise,
                "chsh_threshold": self._chsh_threshold,
            },
            "eve_active": self.eve_active,
            "attacks_detected": self.attacks_detected,
            "escalation_level": self.escalation_level,
            "escalation_label": self.escalation_label,
            "current_port": self.current_port,
            "current_ip": self.current_ip,
            "current_network": self.current_network,
            "state_machine": self._sm.to_dict(),
        }
