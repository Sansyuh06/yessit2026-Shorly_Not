"""
Tests for Q-STDF non-ML threat classifier and Hoeffding tau math.
"""

import sys
import pytest
from shorlynot_skeleton.detect.tau import TauCalculator
from shorlynot_skeleton.detect.classifier import QstdfClassifier
from shorlynot_skeleton.models import (
    SignatureBundle,
    VerifyResult,
    ThreatLabel,
    TauPreset
)


def test_no_ml_libraries_in_detect_module():
    """Verify that detect module contains ZERO machine learning dependencies."""
    import shorlynot_skeleton.detect.classifier as classifier_mod
    import shorlynot_skeleton.detect.tau as tau_mod

    forbidden_modules = ["sklearn", "torch", "tensorflow", "keras", "xgboost", "lightgbm"]
    for mod in forbidden_modules:
        assert mod not in sys.modules, f"Forbidden ML module {mod} was imported!"


def test_hoeffding_tau_formula():
    # p0=0.02, delta=0.01, n=64
    tau_normal = TauCalculator.calculate_tau(p0=0.02, delta=0.01, n=64)
    # Expected: 0.02 + sqrt(ln(100) / 128) = 0.02 + 0.18967 = 0.20967 ~ 0.210
    assert pytest.approx(tau_normal, 0.001) == 0.2097

    tau_strict = TauCalculator.calculate_tau(p0=0.02, delta=0.001, n=64)
    assert pytest.approx(tau_strict, 0.001) == 0.2523

    tau_lenient = TauCalculator.calculate_tau(p0=0.02, delta=0.05, n=64)
    assert pytest.approx(tau_lenient, 0.001) == 0.1730


def test_qstdf_decision_ladder_order():
    classifier = QstdfClassifier()
    
    bundle = SignatureBundle(
        payload_hash="0123456789abcdef" * 4,
        key_id="alice-key-1",
        nonce="test-nonce-1",
        bases=[0] * 128,
        correction_bits=[[0, 0]] * 64,
        n_checks=64,
        L=128
    )

    vr_pass = VerifyResult(
        candidate_accepted=True,
        mismatch_rate=0.015,
        mismatches=1,
        n_checks=64,
        tau=0.2097
    )

    # 1. Test UNAUTH_VERIFY (Step 1)
    res = classifier.classify(bundle, vr_pass, claimed_signer="alice", verifier_id="unauthorized_attacker")
    assert res.label == ThreatLabel.UNAUTH_VERIFY

    # 2. Test IMPERSONATION (Step 2)
    res = classifier.classify(bundle, vr_pass, claimed_signer="eve", verifier_id="bob")
    assert res.label == ThreatLabel.IMPERSONATION

    # 3. Test OK and record nonce
    res = classifier.classify(bundle, vr_pass, claimed_signer="alice", verifier_id="bob")
    assert res.label == ThreatLabel.OK

    # 4. Test REPLAY (Step 3: same nonce)
    res = classifier.classify(bundle, vr_pass, claimed_signer="alice", verifier_id="bob")
    assert res.label == ThreatLabel.REPLAY

    # 5. Test PARAM_TAMPER (Step 4)
    bundle_downgraded = bundle.model_copy(update={"nonce": "test-nonce-2", "n_checks": 1})
    res_param = classifier.classify(bundle_downgraded, vr_pass, claimed_signer="alice", verifier_id="bob")
    assert res_param.label == ThreatLabel.PARAM_TAMPER

    # 6. Test CHANNEL (Step 5)
    bundle_new = bundle.model_copy(update={"nonce": "test-nonce-3"})
    res = classifier.classify(bundle_new, vr_pass, claimed_signer="alice", verifier_id="bob", pqc_unprotect_success=False)
    assert res.label == ThreatLabel.CHANNEL

    # 7. Test FORGERY (Step 6)
    vr_fail = VerifyResult(
        candidate_accepted=False,
        mismatch_rate=0.45,
        mismatches=29,
        n_checks=64,
        tau=0.2097
    )
    bundle_new2 = bundle.model_copy(update={"nonce": "test-nonce-4"})
    res = classifier.classify(bundle_new2, vr_fail, claimed_signer="alice", verifier_id="bob")
    assert res.label == ThreatLabel.FORGERY
