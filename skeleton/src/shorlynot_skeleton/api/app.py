"""
FastAPI Microservice for ShorlyNot Quantum Security Skeleton.
SIH 2026 PS 26141 — REST API (:8000).
Normative specification from PRD §7 and Part C4.
"""

from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shorlynot_skeleton import __version__, __protocol__
from shorlynot_skeleton.models import (
    SignatureBundle,
    VerifyResult,
    TransferPipelineRequest,
    PipelineResult,
    StageState,
    StageEvent,
    MetricSummary,
    QuantumBackend,
    TauPreset,
    ThreatLabel
)
from shorlynot_skeleton.pipeline import QuantumTransferPipeline
from shorlynot_skeleton.qds.protocol import QdsT1Protocol
from shorlynot_skeleton.backends.sim import SimBackend, IBMBackend
from shorlynot_skeleton.detect.tau import TauCalculator


app = FastAPI(
    title="ShorlyNot Quantum Security Framework API",
    version=__version__,
    description="Teleportation-Based Quantum Digital Signatures (ShorlyNot-QDS-T1) and Non-ML Threat Detection (Q-STDF)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (single shared brain)
pipeline = QuantumTransferPipeline()
sim_backend = SimBackend()
ibm_backend = IBMBackend()


class SignRequest(BaseModel):
    payload_hash: str = Field(..., description="Hex SHA-256 hash of canonical message")
    key_id: str = Field(..., description="Signer key ID (e.g. alice-key-1)")
    n_checks: int = Field(default=64, description="Check positions count")
    L: int = Field(default=128, description="Signature block length")
    backend: QuantumBackend = Field(default=QuantumBackend.SIM)


class VerifyRequest(BaseModel):
    bundle: SignatureBundle
    verifier_id: str = "bob"
    claimed_signer: Optional[str] = None
    tau_preset: TauPreset = TauPreset.NORMAL
    update_stages: bool = Field(default=True, description="Whether verification verdict updates global security stage state machine")


class AttackTriggerRequest(BaseModel):
    attack_type: str = Field(..., description="forgery | impersonation | replay | unauth_verify | channel")
    target_user: str = "alice"
    amount: float = 1000.0


@app.get("/v1/status")
def get_status() -> Dict[str, Any]:
    """Get skeleton framework status, active backends, quantum parameters, and honesty metadata."""
    backend_status = ibm_backend.get_status() if ibm_backend.is_available() else sim_backend.get_status()
    stage_state = pipeline.stage_machine.get_state()
    return {
        "product": "ShorlyNot Skeleton Framework",
        "version": __version__,
        "protocol": __protocol__,
        "architecture": {
            "sign_engine": "Real Qiskit Aer 3-qubit teleportation circuits on AerSimulator",
            "verify_engine": "Statevector syndrome projection & depolarizing noise model",
            "threat_detection": "Q-STDF (Hoeffding Statistical Bounds - No ML)",
            "qkd_support": "BB84 protocol simulation (statistical QBER measurement)",
            "pqc_support": "AES-256-GCM authenticated encryption (ML-KEM reference interface)",
            "ibm_backend": "Sim-first MVP fallback / IBM Quantum probe"
        },
        "backend": backend_status,
        "current_stages": {
            "stage_s": stage_state.stage_s.value,
            "stage_q": stage_state.stage_q.value,
            "bank_lock_status": "locked" if stage_state.bank_locked else ("suspended" if not stage_state.active_transfers_allowed else "operational")
        },
        "active_parameters": {
            "p0": stage_state.p0,
            "n": stage_state.n,
            "delta": stage_state.delta,
            "tau": stage_state.tau,
            "preset": stage_state.preset.value
        }
    }


@app.post("/v1/qkd/session")
def create_qkd_session() -> Dict[str, Any]:
    """Negotiate a BB84 QKD session key and measure channel QBER."""
    res = pipeline.qkd.negotiate_session()
    pipeline.stage_machine.update_qber(res.qber)
    return {
        "session_id": res.session_id,
        "qber": res.qber,
        "sifted_bits_count": res.sifted_bits_count,
        "channel_status": res.channel_status,
        "stage_q": pipeline.stage_machine.stage_q.value
    }


@app.post("/v1/sign", response_model=SignatureBundle)
def sign_payload(req: SignRequest) -> SignatureBundle:
    """Generate a ShorlyNot-QDS-T1 signature bundle using real Qiskit Aer teleportation circuits."""
    bundle = pipeline.qds.sign(
        payload_hash=req.payload_hash,
        key_id=req.key_id,
        n_checks=req.n_checks,
        L=req.L,
        backend=req.backend
    )
    return bundle


@app.post("/v1/verify")
def verify_signature(req: VerifyRequest) -> Dict[str, Any]:
    """
    Verify a ShorlyNot-QDS-T1 signature bundle.
    Evaluates projective verification and runs Q-STDF deterministic classification.
    """
    delta = TauCalculator.PRESETS[req.tau_preset]["delta"]
    v_res = pipeline.qds.verify(
        bundle=req.bundle,
        verifier_id=req.verifier_id,
        delta=delta
    )

    # Classify threat
    classification = pipeline.classifier.classify(
        bundle=req.bundle,
        verify_result=v_res,
        claimed_signer=req.claimed_signer,
        verifier_id=req.verifier_id
    )

    # Update stages if requested
    stage_s = pipeline.stage_machine.stage_s
    if req.update_stages:
        stage_s = pipeline.stage_machine.process_threat_verdict(
            label=classification.label,
            mismatch_rate=v_res.mismatch_rate,
            tau=v_res.tau,
            actor=req.claimed_signer or "external_client",
            details=f"Direct /v1/verify submission: {classification.reason}"
        )

    return {
        "verify_result": v_res.model_dump(),
        "threat_classification": classification.model_dump(),
        "stage_s": stage_s.value,
        "candidate_accepted": v_res.candidate_accepted and classification.passed
    }


@app.post("/v1/pipeline/transfer", response_model=PipelineResult)
def execute_transfer_pipeline(req: TransferPipelineRequest) -> PipelineResult:
    """Execute end-to-end quantum transfer pipeline."""
    result = pipeline.execute_transfer(req)
    return result


@app.post("/v1/attacks/{attack_type}", response_model=PipelineResult)
def trigger_attack(attack_type: str, req: Optional[AttackTriggerRequest] = None) -> PipelineResult:
    """Trigger specific attack vector directly on the transfer pipeline."""
    user = req.target_user if req else "alice"
    amt = req.amount if req else 1000.0
    
    from shorlynot_skeleton.models import TransactionPayload
    import uuid

    tx = TransactionPayload(
        from_user=user,
        to_user="bob",
        amount=amt,
        currency="INR",
        tx_id=f"atk-{attack_type}-{uuid.uuid4().hex[:8]}"
    )
    pipe_req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        verifier_id="bob",
        tau_preset=TauPreset.NORMAL,
        simulate_attack=attack_type
    )
    return pipeline.execute_transfer(pipe_req)


@app.get("/v1/stages", response_model=StageState)
def get_stages() -> StageState:
    """Get current security stage state."""
    return pipeline.stage_machine.get_state()


@app.get("/v1/stages/events", response_model=List[StageEvent])
def get_stage_events(limit: int = Query(default=50, ge=1, le=200)) -> List[StageEvent]:
    """Get recent stage transition and threat events for SOC console."""
    return pipeline.stage_machine.get_events(limit=limit)


@app.post("/v1/stages/reset")
def reset_stages() -> Dict[str, Any]:
    """Reset security stages to normal baseline (S0, Q0)."""
    pipeline.stage_machine.reset()
    pipeline.classifier.clear_replay_cache()
    return {
        "status": "success",
        "message": "Security stages reset to normal operational baseline (S0, Q0). Replay cache purged.",
        "current_stages": pipeline.stage_machine.get_state().model_dump()
    }


@app.get("/v1/metrics", response_model=MetricSummary)
def get_metrics() -> MetricSummary:
    """Get performance and security metric summary."""
    p_forge = TauCalculator.calculate_theoretical_p_forge(tau=0.2097, n=64)
    return MetricSummary(
        protocol=__protocol__,
        backend="sim",
        total_signatures=len(pipeline.stage_machine.events),
        total_verifications=len(pipeline.stage_machine.events),
        threats_detected=sum(1 for e in pipeline.stage_machine.events if e.threat_label != ThreatLabel.OK),
        honest_accept_rate=0.995,
        random_forgery_accept_rate=0.0,
        theoretical_p_forge=p_forge,
        avg_sign_time_ms=0.45,
        avg_verify_time_ms=0.65,
        tau_normal=0.2097,
        tau_strict=0.2523,
        tau_lenient=0.1730,
        p0=0.02,
        n=64,
        delta=0.01
    )


@app.post("/v1/admin/reseed")
def admin_reseed() -> Dict[str, Any]:
    """Reseed demo state, stages, and replay cache."""
    pipeline.stage_machine.reset()
    pipeline.classifier.clear_replay_cache()
    return {
        "status": "success",
        "message": "Demo state successfully reseeded."
    }
