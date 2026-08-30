"""
Tests for end-to-end atomic transfer pipeline.
"""

from shorlynot_skeleton.pipeline import QuantumTransferPipeline
from shorlynot_skeleton.models import (
    TransactionPayload,
    TransferPipelineRequest,
    ThreatLabel,
    StageS,
    TauPreset
)


def test_honest_pipeline_transfer_success():
    pipeline = QuantumTransferPipeline()
    tx = TransactionPayload(from_user="alice", to_user="bob", amount=2500.0, currency="INR", tx_id="tx-honest-success")
    req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        verifier_id="bob",
        tau_preset=TauPreset.NORMAL
    )
    result = pipeline.execute_transfer(req)

    assert result.success is True
    assert result.status_code == 200
    assert result.threat_classification.label == ThreatLabel.OK
    assert result.verify_result.candidate_accepted is True
    assert result.verify_result.mismatch_rate <= result.verify_result.tau
    assert result.bank_lock_status == "active"
    assert result.stage_s == StageS.S0


def test_blocked_transfers_when_stage_escalated():
    pipeline = QuantumTransferPipeline()
    
    # 1. Trigger a forgery attack to escalate stage to S2
    tx_attack = TransactionPayload(from_user="alice", to_user="bob", amount=1000.0, tx_id="tx-atk-stage")
    req_attack = TransferPipelineRequest(
        transaction=tx_attack,
        signer_key_id="alice-key-1",
        simulate_attack="forgery"
    )
    res_attack = pipeline.execute_transfer(req_attack)
    assert res_attack.stage_s >= StageS.S2

    # 2. Subsequent legitimate transfer should be immediately blocked by security policy
    tx_legit = TransactionPayload(from_user="alice", to_user="bob", amount=500.0, tx_id="tx-legit-blocked")
    req_legit = TransferPipelineRequest(
        transaction=tx_legit,
        signer_key_id="alice-key-1"
    )
    res_legit = pipeline.execute_transfer(req_legit)
    assert res_legit.success is False
    assert res_legit.bank_lock_status == "transfers_blocked"
