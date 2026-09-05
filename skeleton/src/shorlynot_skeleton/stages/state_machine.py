"""
Security Stage State Machine for ShorlyNot.
S-Stages (Signature threat driving bank lock) & Q-Stages (QKD link QBER).
Normative specification from PRD §4.4 and §8.4.
Includes progressive escalation (repeated forgeries escalate S2 -> S3 -> S4).
"""

import collections
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from shorlynot_skeleton.models import (
    StageS,
    StageQ,
    ThreatLabel,
    StageEvent,
    StageState,
    TauPreset,
    QuantumBackend
)
from shorlynot_skeleton.detect.tau import TauCalculator


class StageStateMachine:
    """
    Manages security stage escalation and event logging for SOC and Bank enforcement.
    Features progressive escalation: repeated attacks elevate severity all the way to S4 lockdown.
    """

    def __init__(self, event_history_limit: int = 200) -> None:
        self.stage_s: StageS = StageS.S0
        self.stage_q: StageQ = StageQ.Q0
        self.last_threat: ThreatLabel = ThreatLabel.OK
        self.last_mismatch: float = 0.0
        self.preset: TauPreset = TauPreset.NORMAL
        self.backend: QuantumBackend = QuantumBackend.SIM
        self.event_limit = event_history_limit
        self.events: collections.deque = collections.deque(maxlen=event_history_limit)
        self.consecutive_threats: int = 0
        self.quarantined_accounts: set = set()
        self.lock_scope: str = "none"

    def get_state(self) -> StageState:
        tau = TauCalculator.get_preset_tau(self.preset)
        p0 = 0.02
        n = 64
        delta = float(TauCalculator.PRESETS[self.preset]["delta"])
        transfers_allowed = (self.stage_s.value < StageS.S2.value)
        bank_locked = (self.stage_s.value >= StageS.S4.value)

        return StageState(
            stage_s=self.stage_s,
            stage_q=self.stage_q,
            last_threat=self.last_threat,
            last_mismatch=self.last_mismatch,
            tau=round(tau, 4),
            p0=p0,
            n=n,
            delta=delta,
            preset=self.preset,
            backend=self.backend,
            active_transfers_allowed=transfers_allowed,
            bank_locked=bank_locked,
            lock_scope=self.lock_scope,
            quarantined_accounts=sorted(list(self.quarantined_accounts)),
            events_count=len(self.events)
        )

    def is_actor_blocked(self, actor: str) -> bool:
        """
        Scope-aware enforcement gate (read by the pipeline and the bank).

        - Below S2: nobody is blocked.
        - lock_scope == "account": only actors in quarantined_accounts are blocked
          (other users keep transacting — no global DoS from a single forgery).
        - lock_scope == "global" (or any unknown scope at S2+): everyone is blocked
          (conservative default).
        """
        if self.stage_s.value < StageS.S2.value:
            return False
        if self.lock_scope == "account":
            return actor in self.quarantined_accounts
        return True

    def calculate_q_stage(self, qber: float) -> StageQ:
        """
        Map QBER percentage to Q stage according to Shor-Preskill literature bounds:
        Q0: < 5%
        Q1: 5% - 8%
        Q2: 8% - 11%
        Q3: 11% - 20%
        Q4: >= 20%
        """
        if qber < 0.05:
            return StageQ.Q0
        elif qber < 0.08:
            return StageQ.Q1
        elif qber < 0.11:
            return StageQ.Q2
        elif qber < 0.20:
            return StageQ.Q3
        else:
            return StageQ.Q4

    def update_qber(self, qber: float) -> None:
        self.stage_q = self.calculate_q_stage(qber)

    def process_threat_verdict(
        self,
        label: ThreatLabel,
        mismatch_rate: float,
        tau: float,
        tx_id: Optional[str] = None,
        actor: Optional[str] = None,
        details: str = ""
    ) -> StageS:
        """
        Escalate S-stage based on threat label, actor, and progressive attack history.
        - Single Forgery/Impersonation: S2 (transfers suspended for actor / system)
        - Repeated Attack under S2: Escalates to S3 (read-only) -> S4 (full lockdown)
        - Channel tampering / Parameter downgrade / Severe QBER: S4 immediately
        """
        self.last_threat = label
        self.last_mismatch = mismatch_rate

        new_stage = self.stage_s

        if label == ThreatLabel.OK:
            self.consecutive_threats = 0
            if self.stage_s == StageS.S1:
                new_stage = StageS.S0
                self.lock_scope = "none"
        else:
            self.consecutive_threats += 1
            if actor:
                self.quarantined_accounts.add(actor)

            if label in (ThreatLabel.CHANNEL, ThreatLabel.PARAM_TAMPER):
                # Critical channel or protocol downgrade compromise -> immediate full bank lockdown
                new_stage = StageS.S4
                self.lock_scope = "global"
            elif label in (ThreatLabel.REPLAY, ThreatLabel.UNAUTH_VERIFY):
                # Pattern attack / unauthorized entity
                if self.stage_s.value < StageS.S3.value:
                    new_stage = StageS.S3
                    self.lock_scope = "account" if self.consecutive_threats == 1 else "global"
                elif self.consecutive_threats >= 2:
                    new_stage = StageS.S4
                    self.lock_scope = "global"
            elif label in (ThreatLabel.FORGERY, ThreatLabel.IMPERSONATION):
                # Initial signature violation -> S2
                if self.stage_s.value < StageS.S2.value:
                    new_stage = StageS.S2
                    self.lock_scope = "account"
                elif self.stage_s == StageS.S2:
                    # Repeated forgery attack while already under S2 alert -> escalate to S3
                    new_stage = StageS.S3
                    self.lock_scope = "global"
                elif self.stage_s == StageS.S3 or self.consecutive_threats >= 3:
                    # Persistent attack wave -> escalate to S4 lockdown
                    new_stage = StageS.S4
                    self.lock_scope = "global"

        self.stage_s = new_stage

        # Record event
        event = StageEvent(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="SIGNATURE_VERIFICATION" if label == ThreatLabel.OK else "SECURITY_ALERT",
            threat_label=label,
            stage_s=self.stage_s,
            stage_q=self.stage_q,
            mismatch_rate=mismatch_rate,
            tau=tau,
            tx_id=tx_id,
            actor=actor,
            details=details or f"Verdict: {label.value} (Mismatch: {mismatch_rate:.4f} vs Tau: {tau:.4f})"
        )
        self.events.appendleft(event)

        return self.stage_s

    def reset(self) -> None:
        """Reset stages to normal operational baseline."""
        self.stage_s = StageS.S0
        self.stage_q = StageQ.Q0
        self.last_threat = ThreatLabel.OK
        self.last_mismatch = 0.0
        self.consecutive_threats = 0
        self.quarantined_accounts.clear()
        self.lock_scope = "none"

        event = StageEvent(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="ADMIN_RESET",
            threat_label=ThreatLabel.OK,
            stage_s=StageS.S0,
            stage_q=StageQ.Q0,
            mismatch_rate=0.0,
            tau=TauCalculator.get_preset_tau(self.preset),
            actor="ops",
            details="Security stages reset to normal baseline (S0, Q0) by administrator."
        )
        self.events.appendleft(event)

    def get_events(self, limit: int = 50) -> List[StageEvent]:
        return list(self.events)[:limit]
