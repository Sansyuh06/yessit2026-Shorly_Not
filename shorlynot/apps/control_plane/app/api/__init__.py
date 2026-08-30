"""Control Plane API router — aggregates all endpoint modules.

PRD §23: All endpoints under /api/v1 prefix.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from packages.common.enums import (
    AttackType,
    ExecutionMode,
    PolicyState,
    QKDProtocol,
    SecurityStatus,
)
from packages.common.schemas import (
    DeviceCreate,
    FiniteKeyResult,
    QKDSessionCreate,
    WSEventEnvelope,
)

router = APIRouter(prefix="/api/v1")


# ── Helper: broadcast WebSocket event ──

async def _broadcast(request: Request, event_type: str, payload: dict) -> None:
    envelope = WSEventEnvelope(
        event_type=event_type,
        payload=payload,
    )
    data = envelope.model_dump_json()
    dead: set = set()
    for ws in getattr(request.app.state, "ws_clients", set()):
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    for ws in dead:
        request.app.state.ws_clients.discard(ws)


# ── Health ──────────────────────────────────────────────────

@router.get("/health")
async def health(request: Request) -> dict:
    config = request.app.state.config
    policy = request.app.state.policy_engine
    return {
        "status": "ok",
        "execution_mode": config.shorlynot_execution_mode.value,
        "policy_state": policy.state.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Devices ─────────────────────────────────────────────────

@router.post("/devices")
async def create_device(device: DeviceCreate, request: Request) -> dict:
    from sqlalchemy.orm import Session

    from packages.common.database import DeviceModel

    engine = request.app.state.engine
    with Session(engine) as session:
        db_device = DeviceModel(
            name=device.name,
            mac_address=device.mac_address,
            ipv4_address=str(device.ipv4_address),
            device_type=device.device_type.value,
            status="online",
        )
        session.add(db_device)
        session.commit()
        session.refresh(db_device)
        return {
            "id": db_device.id,
            "name": db_device.name,
            "mac_address": db_device.mac_address,
            "ipv4_address": db_device.ipv4_address,
            "device_type": db_device.device_type,
            "status": db_device.status,
        }


@router.get("/devices")
async def list_devices(request: Request) -> list[dict]:
    from sqlalchemy.orm import Session

    from packages.common.database import DeviceModel

    engine = request.app.state.engine
    with Session(engine) as session:
        devices = session.query(DeviceModel).all()
        return [
            {
                "id": d.id,
                "name": d.name,
                "mac_address": d.mac_address,
                "ipv4_address": d.ipv4_address,
                "device_type": d.device_type,
                "status": d.status,
            }
            for d in devices
        ]


@router.get("/devices/{device_id}")
async def get_device(device_id: str, request: Request) -> dict:
    from sqlalchemy.orm import Session

    from packages.common.database import DeviceModel

    engine = request.app.state.engine
    with Session(engine) as session:
        device = session.query(DeviceModel).filter_by(id=device_id).first()
        if not device:
            return JSONResponse(status_code=404, content={"error": "Device not found"})
        return {
            "id": device.id,
            "name": device.name,
            "mac_address": device.mac_address,
            "ipv4_address": device.ipv4_address,
            "device_type": device.device_type,
            "status": device.status,
        }


# ── QKD Sessions ────────────────────────────────────────────

@router.post("/qkd/sessions")
async def create_qkd_session(session_req: QKDSessionCreate, request: Request) -> dict:
    """Run a complete QKD session including protocol execution and analysis."""
    config = request.app.state.config
    policy = request.app.state.policy_engine

    result: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "protocol": session_req.protocol.value,
        "execution_mode": config.shorlynot_execution_mode.value,
        "status": "running",
    }

    if session_req.protocol == QKDProtocol.BB84:
        from packages.qkd.bb84 import run_bb84_protocol

        bb84 = run_bb84_protocol(
            num_qubits=session_req.requested_shots,
            attack_probability=session_req.attack_probability,
            execution_mode=config.shorlynot_execution_mode,
        )
        result.update({
            "raw_key_length": bb84.raw_key_length,
            "sifted_key_length": bb84.sifted_key_length,
            "qber": bb84.qber,
            "error_count": bb84.error_count,
            "compared_bits": bb84.compared_bits,
            "theoretical_qber": bb84.theoretical_qber,
            "attacked_qubit_count": bb84.attacked_qubit_count,
            "backend": bb84.backend_name,
            "raw_result_hash": bb84.raw_result_hash,
            "status": "completed",
        })

        # Evaluate security
        if bb84.qber is not None:
            from packages.qkd.finite_key import estimate_secure_key_length

            fk = estimate_secure_key_length(
                bb84.sifted_key_length,
                bb84.qber,
                config.qkd_security_epsilon,
            )
            status, state = policy.evaluate_bb84(bb84.qber, fk.secure)
            result["security_status"] = status.value
            result["policy_state"] = state.value
            result["finite_key"] = fk.model_dump()

    elif session_req.protocol == QKDProtocol.E91:
        from packages.qkd.e91 import run_e91_protocol

        e91 = run_e91_protocol(
            num_pairs=session_req.requested_shots,
            execution_mode=config.shorlynot_execution_mode,
            chsh_threshold=config.qkd_chsh_threshold,
        )
        result.update({
            "num_pairs": e91.num_pairs,
            "sifted_key_length": e91.sifted_key_length,
            "qber": e91.qber,
            "chsh_s": e91.chsh_s,
            "chsh_threshold": e91.chsh_threshold,
            "correlations": e91.correlations,
            "security_evaluation": e91.security_evaluation,
            "backend": e91.backend_name,
            "raw_result_hash": e91.raw_result_hash,
            "status": "completed",
        })

        if e91.chsh_s is not None:
            status, state = policy.evaluate_e91(e91.chsh_s)
            result["security_status"] = status.value
            result["policy_state"] = state.value

    elif session_req.protocol == QKDProtocol.B92:
        from packages.qkd.b92 import run_b92_protocol

        b92 = run_b92_protocol(
            num_qubits=session_req.requested_shots,
            attack_probability=session_req.attack_probability,
            execution_mode=config.shorlynot_execution_mode,
        )
        result.update({
            "transmitted_qubits": b92.transmitted_qubits,
            "conclusive_measurements": b92.conclusive_measurements,
            "inconclusive_measurements": b92.inconclusive_measurements,
            "conclusive_rate": b92.conclusive_rate,
            "qber": b92.qber,
            "backend": b92.backend_name,
            "raw_result_hash": b92.raw_result_hash,
            "status": "completed",
        })

    elif session_req.protocol == QKDProtocol.DECOY_BB84:
        from packages.qkd.decoy import run_decoy_bb84

        decoy = run_decoy_bb84(
            num_qubits=session_req.requested_shots,
            attack_probability=session_req.attack_probability,
            pns_attack=(session_req.attack_type == AttackType.PNS),
            execution_mode=config.shorlynot_execution_mode,
        )
        result.update({
            "total_qubits": decoy.total_qubits,
            "sifted_key_length": decoy.sifted_key_length,
            "raw_qber": decoy.raw_qber,
            "pns_suspected": decoy.pns_suspected,
            "pns_evidence": decoy.pns_evidence,
            "signal_gain": decoy.signal.gain,
            "decoy_gain": decoy.decoy.gain,
            "single_photon_yield": decoy.estimated_single_photon_yield,
            "single_photon_error_rate": decoy.estimated_single_photon_error_rate,
            "status": "completed",
        })

    # Broadcast event
    await _broadcast(request, "qkd_session_completed", result)

    return result


@router.get("/qkd/sessions")
async def list_sessions(request: Request) -> dict:
    return {"sessions": [], "message": "Query from database - not yet implemented"}


@router.get("/qkd/sessions/{session_id}")
async def get_session(session_id: str, request: Request) -> dict:
    return {"session_id": session_id, "message": "Retrieve from database"}


@router.get("/qkd/sessions/{session_id}/entropy")
async def get_session_entropy(session_id: str, request: Request) -> dict:
    return {"session_id": session_id, "entropy_ledger": []}


# ── Leases ──────────────────────────────────────────────────

@router.post("/leases")
async def create_lease(request: Request) -> dict:
    return {"message": "Lease issuance — requires a completed QKD session"}


@router.get("/leases")
async def list_leases(request: Request) -> list:
    return []


@router.get("/leases/{lease_id}")
async def get_lease(lease_id: str, request: Request) -> dict:
    return {"lease_id": lease_id}


@router.post("/leases/{lease_id}/revoke")
async def revoke_lease(lease_id: str, request: Request) -> dict:
    return {"lease_id": lease_id, "status": "revoked"}


# ── Firewall ────────────────────────────────────────────────

@router.get("/firewall/events")
async def firewall_events(request: Request) -> list:
    return []


@router.get("/firewall/state")
async def firewall_state(request: Request) -> dict:
    return {"state": "unknown", "rules": []}


# ── Telemetry ───────────────────────────────────────────────

@router.get("/telemetry/latest")
async def telemetry_latest(request: Request) -> dict:
    return {"status": "no_data"}


@router.get("/telemetry/history")
async def telemetry_history(request: Request) -> list:
    return []


# ── Security Events ────────────────────────────────────────

@router.get("/security/events")
async def security_events(request: Request) -> list:
    return []

@router.post("/security/activate_eve")
async def activate_eve(request: Request) -> dict:
    policy = request.app.state.policy_engine
    policy.activate_eve()
    await _broadcast(request, "attack", {
        "action": "eve_activated",
        "message": "Eve is now intercepting the quantum channel"
    })
    return {"eve_active": True}

@router.post("/security/deactivate_eve")
async def deactivate_eve(request: Request) -> dict:
    policy = request.app.state.policy_engine
    policy.deactivate_eve()
    await _broadcast(request, "session", {
        "action": "eve_deactivated",
        "status": "GREEN"
    })
    return {"eve_active": False}

@router.post("/security/trigger_attack")
async def trigger_attack(request: Request) -> dict:
    config = request.app.state.config
    policy = request.app.state.policy_engine
    
    # Force a compromised session evaluation
    qber = 0.25 # High QBER
    status, state = policy.evaluate_bb84(qber, False)
    
    result = {
        "status": status.value,
        "qber": qber,
        "policy_state": state.value,
        "escalation_level": policy.escalation_level,
        "escalation_label": policy.escalation_label
    }
    
    await _broadcast(request, "attack", result)
    
    if policy.escalation_level > 0:
        await _broadcast(request, "escalation" if policy.escalation_level < 4 else "lockdown", {
            "level": policy.escalation_level,
            "action": policy.escalation_label.split("—")[-1].strip() if "—" in policy.escalation_label else policy.escalation_label,
            "port": policy.current_port,
            "ip": policy.current_ip,
            "network": policy.current_network
        })
        
    return result

@router.post("/security/reset")
async def reset_system(request: Request) -> dict:
    policy = request.app.state.policy_engine
    policy.reset_escalation()
    await _broadcast(request, "session", {
        "action": "system_reset",
        "status": "SECURE",
        "qber": 0.0
    })
    return {"status": "reset_complete"}

@router.get("/security/status")
async def get_security_status(request: Request) -> dict:
    policy = request.app.state.policy_engine
    d = policy.to_dict()
    return {
        "status": "SECURE" if d["state"] == "secure" else "RED",
        "qber": 0.0 if d["state"] == "secure" else 0.25,
        "attacks_detected": d["attacks_detected"],
        "eve_active": d["eve_active"],
        "escalation_level": d["escalation_level"],
        "escalation_label": d["escalation_label"],
        "current_port": d["current_port"],
        "current_ip": d["current_ip"],
        "current_network": d["current_network"],
        "policy_state": d["state"]
    }



# ── Recovery ────────────────────────────────────────────────

@router.post("/recovery/start")
async def start_recovery(request: Request) -> dict:
    config = request.app.state.config
    policy = request.app.state.policy_engine

    from packages.pqc.recovery import execute_pqc_recovery

    record = execute_pqc_recovery(
        variant=config.mlkem_variant,
        execution_mode=config.shorlynot_execution_mode,
    )

    await _broadcast(request, "pqc_recovery_completed", {
        "id": record.id,
        "kem_algorithm": record.kem_algorithm,
        "handshake_duration_ms": record.handshake_duration_ms,
        "transcript_hash": record.transcript_hash,
        "status": record.status,
    })

    return record.model_dump()


@router.get("/recovery/{recovery_id}")
async def get_recovery(recovery_id: str, request: Request) -> dict:
    return {"recovery_id": recovery_id}


# ── Protocol Comparison ────────────────────────────────────

@router.get("/protocols/compare")
async def compare_protocols(request: Request) -> dict:
    return {"comparison": [], "message": "Run sessions first, then compare"}


# ── WebSocket ───────────────────────────────────────────────

@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    request = websocket
    # Register
    websocket.app.state.ws_clients.add(websocket)
    try:
        while True:
            # Keep alive — client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket.app.state.ws_clients.discard(websocket)
