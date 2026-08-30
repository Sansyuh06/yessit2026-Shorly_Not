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
