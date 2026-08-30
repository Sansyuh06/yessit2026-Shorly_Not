"""Policy state machine with strict transition validation.

Defines exactly the allowed transitions from PRD §21.
Invalid transitions raise INVALID_POLICY_TRANSITION.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from packages.common.enums import PolicyState
from packages.common.errors import InvalidPolicyTransitionError

# ── Allowed Transitions (PRD §21) ──────────────────────────

ALLOWED_TRANSITIONS: dict[PolicyState, set[PolicyState]] = {
    PolicyState.INITIALIZING: {PolicyState.SECURE, PolicyState.ERROR},
    PolicyState.SECURE: {PolicyState.OBSERVING, PolicyState.DEGRADED, PolicyState.COMPROMISED},
    PolicyState.OBSERVING: {PolicyState.SECURE, PolicyState.DEGRADED, PolicyState.COMPROMISED},
    PolicyState.DEGRADED: {PolicyState.SECURE, PolicyState.COMPROMISED},
    PolicyState.COMPROMISED: {PolicyState.REVOKING},
    PolicyState.REVOKING: {PolicyState.ISOLATED, PolicyState.ERROR},
    PolicyState.ISOLATED: {PolicyState.PQC_RECOVERY},
    PolicyState.PQC_RECOVERY: {PolicyState.RESTORING, PolicyState.ERROR},
    PolicyState.RESTORING: {PolicyState.SECURE, PolicyState.ERROR},
    PolicyState.ERROR: set(),  # Terminal — requires manual intervention or restart
}


class PolicyTransition:
    """Record of a single state transition."""

    def __init__(
        self,
        from_state: PolicyState,
        to_state: PolicyState,
        reason: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class PolicyStateMachine:
    """Strict finite state machine for system security policy.

    No transition is permitted outside the allowed set.
    All transitions are logged for audit purposes.
    """

    def __init__(self, initial_state: PolicyState = PolicyState.INITIALIZING) -> None:
        self._state = initial_state
        self._history: list[PolicyTransition] = []

    @property
    def state(self) -> PolicyState:
        """Current policy state."""
        return self._state

    @property
    def history(self) -> list[PolicyTransition]:
        """Complete transition history."""
        return list(self._history)

    def can_transition_to(self, target: PolicyState) -> bool:
        """Check if a transition to the target state is permitted."""
        allowed = ALLOWED_TRANSITIONS.get(self._state, set())
        return target in allowed

    def transition(
        self,
        target: PolicyState,
        reason: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> PolicyTransition:
        """Execute a state transition.

        Args:
            target: The target state.
            reason: Human-readable reason for the transition.
            metadata: Optional metadata to record.

        Returns:
            The recorded PolicyTransition.

        Raises:
            InvalidPolicyTransitionError: If transition is not allowed.
        """
        if not self.can_transition_to(target):
            allowed = ALLOWED_TRANSITIONS.get(self._state, set())
            allowed_names = [s.value for s in allowed]
            raise InvalidPolicyTransitionError(
                f"Transition {self._state.value} → {target.value} is not permitted. "
                f"Allowed transitions from {self._state.value}: {allowed_names}"
            )

        transition = PolicyTransition(
            from_state=self._state,
            to_state=target,
            reason=reason,
            metadata=metadata,
        )

        self._state = target
        self._history.append(transition)

        return transition

    def get_allowed_transitions(self) -> list[PolicyState]:
        """Get list of states reachable from current state."""
        return sorted(
            ALLOWED_TRANSITIONS.get(self._state, set()),
            key=lambda s: s.value,
        )

    def reset(self) -> None:
        """Reset to INITIALIZING state. Preserves history."""
        if self._state != PolicyState.INITIALIZING:
            self._history.append(PolicyTransition(
                from_state=self._state,
                to_state=PolicyState.INITIALIZING,
                reason="Manual reset",
            ))
            self._state = PolicyState.INITIALIZING

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_state": self._state.value,
            "allowed_transitions": [s.value for s in self.get_allowed_transitions()],
            "transition_count": len(self._history),
            "history": [t.to_dict() for t in self._history],
        }
