"""
Skeleton Framework Client for Bank Application.
Communicates via HTTP to the Skeleton API (:8000) with fallback to local SDK instance.
Hard rule from PRD: Bank never reimplements QDS/QKD/PQC/detect logic.
"""

import httpx
from typing import Dict, Any, Optional, List
from shorlynot_skeleton.models import (
    TransferPipelineRequest,
    PipelineResult,
    StageState,
    StageEvent,
    MetricSummary
)
from shorlynot_skeleton.pipeline import QuantumTransferPipeline


class SkeletonServiceClient:
    """
    Client connecting Bank to the ShorlyNot Skeleton microservice.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self._local_pipeline = QuantumTransferPipeline()

    def execute_transfer(self, req: TransferPipelineRequest) -> PipelineResult:
        try:
            with httpx.Client(base_url=self.base_url, timeout=3.0) as client:
                resp = client.post("/v1/pipeline/transfer", json=req.model_dump())
                if resp.status_code in (200, 403, 423):
                    return PipelineResult(**resp.json())
        except Exception:
            pass
        # Graceful fallback to embedded framework pipeline
        return self._local_pipeline.execute_transfer(req)

    def get_stages(self) -> StageState:
        try:
            with httpx.Client(base_url=self.base_url, timeout=2.0) as client:
                resp = client.get("/v1/stages")
                if resp.status_code == 200:
                    return StageState(**resp.json())
        except Exception:
            pass
        return self._local_pipeline.stage_machine.get_state()

    def get_events(self, limit: int = 50) -> List[StageEvent]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=2.0) as client:
                resp = client.get(f"/v1/stages/events?limit={limit}")
                if resp.status_code == 200:
                    return [StageEvent(**e) for e in resp.json()]
        except Exception:
            pass
        return self._local_pipeline.stage_machine.get_events(limit=limit)

    def trigger_attack(self, attack_type: str, user: str = "alice", amount: float = 1000.0) -> PipelineResult:
        try:
            with httpx.Client(base_url=self.base_url, timeout=3.0) as client:
                resp = client.post(
                    f"/v1/attacks/{attack_type}",
                    json={"attack_type": attack_type, "target_user": user, "amount": amount}
                )
                if resp.status_code in (200, 403, 423):
                    return PipelineResult(**resp.json())
        except Exception:
            pass

        import uuid
        from shorlynot_skeleton.models import TransactionPayload, TauPreset
        tx = TransactionPayload(
            from_user=user,
            to_user="bob",
            amount=amount,
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
        return self._local_pipeline.execute_transfer(pipe_req)

    def reset_stages(self) -> Dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=2.0) as client:
                resp = client.post("/v1/stages/reset")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        self._local_pipeline.stage_machine.reset()
        self._local_pipeline.classifier.clear_replay_cache()
        return {"status": "success", "message": "Stages reset locally."}

    def get_metrics(self) -> MetricSummary:
        try:
            with httpx.Client(base_url=self.base_url, timeout=2.0) as client:
                resp = client.get("/v1/metrics")
                if resp.status_code == 200:
                    return MetricSummary(**resp.json())
        except Exception:
            pass
        from shorlynot_skeleton.detect.tau import TauCalculator
        return MetricSummary(
            protocol="ShorlyNot-QDS-T1",
            backend="sim",
            theoretical_p_forge=TauCalculator.calculate_theoretical_p_forge(0.2097, 64),
            tau_normal=0.2097,
            tau_strict=0.2523,
            tau_lenient=0.1730
        )
