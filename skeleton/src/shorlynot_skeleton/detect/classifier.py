"""
Q-STDF Threat Classification Engine.
Strict 6-step Non-ML Decision Ladder for SIH 2026 PS 26141.
Normative specification from PRD §4.3 and MODEL.md §10.
"""

import collections
import time
from typing import Dict, Optional, Set, Any
from shorlynot_skeleton.models import (
    ThreatLabel,
    ThreatClassification,
    SignatureBundle,
    VerifyResult,
    StageS,
    TauPreset
)
from shorlynot_skeleton.detect.tau import TauCalculator


class QstdfClassifier:
    """
    Quantum Statistical Threat Detection Framework (Q-STDF).
    Strict non-ML rule-based ladder:
    1. UNAUTH_VERIFY -> verifier lacks entitlement
    2. IMPERSONATION -> key_id / identity binding invalid
    3. REPLAY -> duplicate nonce in replay window
    4. CHANNEL -> PQC unwrap failure or transmission bit flips
    5. FORGERY -> mismatch rate p_hat > tau
    6. OK -> all tests pass
    """

    DEFAULT_KEYS = {
        "alice": "alice-key-1",
        "bob": "bob-key-1",
        "carol": "carol-key-1",
        "eve": "eve-key-1",
    }

    AUTHORIZED_VERIFIERS = {"bob", "alice", "carol", "ops", "bank_validator", "system"}

    def __init__(self, replay_cache_size: int = 10000):
        # In-memory LRU/OrderedDict for nonce replay cache
        self.seen_nonces: collections.OrderedDict[str, float] = collections.OrderedDict()
        self.max_nonces = replay_cache_size
        self.key_bindings: Dict[str, str] = dict(self.DEFAULT_KEYS)
        self.authorized_verifiers: Set[str] = set(self.AUTHORIZED_VERIFIERS)

    def register_key(self, user: str, key_id: str):
        self.key_bindings[user] = key_id

    def is_nonce_seen(self, nonce: str) -> bool:
        return nonce in self.seen_nonces

    def record_nonce(self, nonce: str):
        if len(self.seen_nonces) >= self.max_nonces:
            self.seen_nonces.popitem(last=False)
        self.seen_nonces[nonce] = time.time()

    def clear_replay_cache(self):
        self.seen_nonces.clear()

    def classify(
        self,
        bundle: SignatureBundle,
        verify_result: VerifyResult,
        claimed_signer: Optional[str] = None,
        verifier_id: str = "bob",
        pqc_unprotect_success: bool = True,
        channel_tampered: bool = False
    ) -> ThreatClassification:
        """
        Evaluate signature verification against the strict 6-stage Q-STDF decision ladder.
        """
        p0 = verify_result.p0
        n = verify_result.n_checks
        delta = verify_result.delta
        tau = verify_result.tau
        mismatch_rate = verify_result.mismatch_rate

        # -------------------------------------------------------------
        # STEP 1: UNAUTH_VERIFY (Verifier Authorization Check)
        # -------------------------------------------------------------
        if verifier_id not in self.authorized_verifiers:
            return ThreatClassification(
                label=ThreatLabel.UNAUTH_VERIFY,
                passed=False,
                reason=f"Verifier '{verifier_id}' lacks verification entitlement credentials.",
                mismatch_rate=mismatch_rate,
                tau=tau,
                p0=p0,
                n=n,
                delta=delta,
                stage_s_recommendation=StageS.S3,
                details={"verifier_id": verifier_id, "step": 1}
            )

        # -------------------------------------------------------------
        # STEP 2: IMPERSONATION (Signer Key ID Binding Check)
        # -------------------------------------------------------------
        from shorlynot_skeleton.qkd.key_registry import GLOBAL_KEY_REGISTRY
        if claimed_signer:
            is_valid_in_registry = GLOBAL_KEY_REGISTRY.validate_key_binding(bundle.key_id, claimed_signer)
            expected_key = self.key_bindings.get(claimed_signer)
            
            if not is_valid_in_registry and (not expected_key or bundle.key_id != expected_key):
                return ThreatClassification(
                    label=ThreatLabel.IMPERSONATION,
                    passed=False,
                    reason=f"Signer identity mismatch: Claimed '{claimed_signer}' does not own key_id '{bundle.key_id}'.",
                    mismatch_rate=mismatch_rate,
                    tau=tau,
                    p0=p0,
                    n=n,
                    delta=delta,
                    stage_s_recommendation=StageS.S2,
                    details={"claimed_signer": claimed_signer, "provided_key": bundle.key_id, "step": 2}
                )
        else:
            # Standalone verify without claimed_signer: key_id must exist in registry
            if bundle.key_id not in self.key_bindings and not GLOBAL_KEY_REGISTRY.get_key(bundle.key_id):
                return ThreatClassification(
                    label=ThreatLabel.IMPERSONATION,
                    passed=False,
                    reason=f"Unregistered signer key_id '{bundle.key_id}' submitted without authenticated identity.",
                    mismatch_rate=mismatch_rate,
                    tau=tau,
                    p0=p0,
                    n=n,
                    delta=delta,
                    stage_s_recommendation=StageS.S2,
                    details={"provided_key": bundle.key_id, "step": 2}
                )

        # -------------------------------------------------------------
        # STEP 3: REPLAY (Nonce Replay Check)
        # -------------------------------------------------------------
        if self.is_nonce_seen(bundle.nonce):
            return ThreatClassification(
                label=ThreatLabel.REPLAY,
                passed=False,
                reason=f"Nonce replay detected: Nonce '{bundle.nonce}' has already been processed.",
                mismatch_rate=mismatch_rate,
                tau=tau,
                p0=p0,
                n=n,
                delta=delta,
                stage_s_recommendation=StageS.S3,
                details={"nonce": bundle.nonce, "step": 3}
            )

        # -------------------------------------------------------------
        # STEP 4: CHANNEL & PARAMETER TAMPERING (Integrity Check)
        # -------------------------------------------------------------
        if bundle.n_checks < 32 or len(bundle.bases) < bundle.n_checks or len(bundle.correction_bits) < bundle.n_checks:
            return ThreatClassification(
                label=ThreatLabel.CHANNEL,
                passed=False,
                reason=f"Security parameter downgrade / array length tampering detected (n_checks={bundle.n_checks} < 32).",
                mismatch_rate=1.0,
                tau=tau,
                p0=p0,
                n=n,
                delta=delta,
                stage_s_recommendation=StageS.S4,
                details={"n_checks": bundle.n_checks, "step": 4, "param_tampering": True}
            )

        if not pqc_unprotect_success or channel_tampered:
            return ThreatClassification(
                label=ThreatLabel.CHANNEL,
                passed=False,
                reason="PQC correction bits decryption failure or active quantum channel tampering detected.",
                mismatch_rate=mismatch_rate,
                tau=tau,
                p0=p0,
                n=n,
                delta=delta,
                stage_s_recommendation=StageS.S4,
                details={"pqc_unprotect_success": pqc_unprotect_success, "channel_tampered": channel_tampered, "step": 4}
            )

        # -------------------------------------------------------------
        # STEP 5: FORGERY (Hoeffding Statistical Threshold Check)
        # -------------------------------------------------------------
        if mismatch_rate > tau:
            return ThreatClassification(
                label=ThreatLabel.FORGERY,
                passed=False,
                reason=f"Quantum measurement mismatch rate ({mismatch_rate:.4f}) exceeds Hoeffding threshold tau ({tau:.4f}). Potential signature forgery.",
                mismatch_rate=mismatch_rate,
                tau=tau,
                p0=p0,
                n=n,
                delta=delta,
                stage_s_recommendation=StageS.S2,
                details={"mismatch_rate": mismatch_rate, "tau": tau, "step": 5}
            )

        # -------------------------------------------------------------
        # STEP 6: OK (All Checks Passed)
        # -------------------------------------------------------------
        # Record valid nonce to prevent subsequent replay attacks
        self.record_nonce(bundle.nonce)

        return ThreatClassification(
            label=ThreatLabel.OK,
            passed=True,
            reason="Quantum digital signature verified successfully within honest Hoeffding bound.",
            mismatch_rate=mismatch_rate,
            tau=tau,
            p0=p0,
            n=n,
            delta=delta,
            stage_s_recommendation=StageS.S0,
            details={"mismatch_rate": mismatch_rate, "tau": tau, "step": 6}
        )
