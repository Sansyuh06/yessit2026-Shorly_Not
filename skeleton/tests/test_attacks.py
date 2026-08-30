"""
Tests for the 5 attack simulation vectors.
"""

from shorlynot_skeleton.pipeline import QuantumTransferPipeline
from shorlynot_skeleton.models import (
    TransactionPayload,
    TransferPipelineRequest,
    ThreatLabel,
    StageS,
    TauPreset
)


def test_forgery_attack_vector():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-forgery-1")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        simulate_attack="forgery"
    )
    res = pipeline.execute_transfer(req)
    assert res.success is False
    assert res.threat_classification.label == ThreatLabel.FORGERY
    assert res.stage_s >= StageS.S2


def test_impersonation_attack_vector():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-impersonate-1")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        simulate_attack="impersonation"
    )
    res = pipeline.execute_transfer(req)
    assert res.success is False
    assert res.threat_classification.label == ThreatLabel.IMPERSONATION
    assert res.stage_s >= StageS.S2


def test_replay_attack_vector():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-replay-1")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        simulate_attack="replay"
    )
    res = pipeline.execute_transfer(req)
    assert res.success is False
    assert res.threat_classification.label == ThreatLabel.REPLAY
    assert res.stage_s >= StageS.S3


def test_unauth_verify_attack_vector():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-unauth-1")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        simulate_attack="unauth_verify"
    )
    res = pipeline.execute_transfer(req)
    assert res.success is False
    assert res.threat_classification.label == ThreatLabel.UNAUTH_VERIFY
    assert res.stage_s >= StageS.S3


def test_channel_attack_vector():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-channel-1")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        simulate_attack="channel"
    )
    res = pipeline.execute_transfer(req)
    assert res.success is False
    assert res.threat_classification.label in (ThreatLabel.CHANNEL, ThreatLabel.FORGERY)
    assert res.stage_s >= StageS.S2


def test_parameter_tampering_downgrade_attack_vector():
    """
    Test that an adversary attempting to tamper with security parameters (e.g. n_checks=1)
    is caught immediately by Q-STDF and rejected.
    """
    from shorlynot_skeleton.attacks.param_tamper import ParameterTamperingAttack
    from shorlynot_skeleton.qds.protocol import QdsT1Protocol
    from shorlynot_skeleton.detect.classifier import QstdfClassifier

    protocol = QdsT1Protocol()
    classifier = QstdfClassifier()

    downgraded_bundle = ParameterTamperingAttack.generate_downgraded_bundle(
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        claimed_key_id="alice-key-1",
        tampered_n=1
    )

    verify_res = protocol.verify(downgraded_bundle, verifier_id="bob")
    assert verify_res.candidate_accepted is False
    assert verify_res.mismatch_rate == 1.0

    classification = classifier.classify(
        bundle=downgraded_bundle,
        verify_result=verify_res,
        verifier_id="bob",
        claimed_signer="alice"
    )
    assert classification.passed is False
    assert classification.label == ThreatLabel.CHANNEL
    assert classification.stage_s_recommendation == StageS.S4
