"""
Tests for security stage machine and QBER thresholds.
"""

from shorlynot_skeleton.stages.state_machine import StageStateMachine
from shorlynot_skeleton.models import StageS, StageQ, ThreatLabel


def test_stage_state_machine_transitions():
    sm = StageStateMachine()
    assert sm.stage_s == StageS.S0
    assert sm.stage_q == StageQ.Q0

    # Forgery escalates to S2
    s = sm.process_threat_verdict(ThreatLabel.FORGERY, 0.45, 0.21, tx_id="tx-1")
    assert s == StageS.S2
    assert sm.get_state().active_transfers_allowed is False

    # Replay escalates to S3
    s = sm.process_threat_verdict(ThreatLabel.REPLAY, 0.01, 0.21, tx_id="tx-2")
    assert s == StageS.S3

    # Channel escalates to S4 (Full Bank Lock)
    s = sm.process_threat_verdict(ThreatLabel.CHANNEL, 0.0, 0.21, tx_id="tx-3")
    assert s == StageS.S4
    assert sm.get_state().bank_locked is True

    # Admin reset restores S0
    sm.reset()
    assert sm.stage_s == StageS.S0
    assert sm.get_state().active_transfers_allowed is True
    assert sm.get_state().bank_locked is False


def test_q_stage_qber_bands():
    sm = StageStateMachine()
    assert sm.calculate_q_stage(0.03) == StageQ.Q0
    assert sm.calculate_q_stage(0.06) == StageQ.Q1
    assert sm.calculate_q_stage(0.09) == StageQ.Q2
    assert sm.calculate_q_stage(0.15) == StageQ.Q3
    assert sm.calculate_q_stage(0.25) == StageQ.Q4
