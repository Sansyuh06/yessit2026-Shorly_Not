"""
FastAPI server exposing the KMS API, WebSocket event bus, and a minimal status UI.
Module entry point: python -m kms.kms_server
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
import base64
from datetime import datetime, timezone
from typing import Dict, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from kms.key_management_service import KeyManagementService


# ── Event Bus ───────────────────────────────────────────────────────────────

class EventBus:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: dict):
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        msg = json.dumps(event, default=str)
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.connections:
                self.connections.remove(ws)


app = FastAPI(
    title="FinQuantum Shield — KMS",
    description="Quantum-safe key distribution API for banking security",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kms = KeyManagementService()
bus = EventBus()

# ── Webapp static files ─────────────────────────────────────────────────
webapp_dir = os.path.join(os.path.dirname(__file__), "..", "webapp")
if os.path.isdir(os.path.join(webapp_dir, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(webapp_dir, "static")),
              name="static")

# ── Banking simulation state ────────────────────────────────────────────
BANK_ACCOUNTS: Dict[str, dict] = {
    "ACC001": {"name": "Priya Sharma",    "balance": 250000.00, "ifsc": "FQBS0001"},
    "ACC002": {"name": "Arjun Mehta",     "balance": 180000.00, "ifsc": "FQBS0002"},
    "ACC003": {"name": "Divya Nair",      "balance": 320000.00, "ifsc": "FQBS0003"},
    "ACC004": {"name": "Rahul Gupta",     "balance": 95000.00,  "ifsc": "FQBS0004"},
    "HQ001":  {"name": "FinQuantum HQ",   "balance": 5000000.00,"ifsc": "FQBS0000"},
}
TRANSACTION_LEDGER: List[dict] = []


# ── Models ──────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    client_a: str = ""
    client_b: str = ""
    initiator: str = ""
    peer: str = ""
    use_hybrid: bool = False
    pqc: bool = False


class JoinSessionRequest(BaseModel):
    session_id: str
    device_id: str


class GetKeyRequest(BaseModel):
    session_id: str
    client_id: str


class TransferRequest(BaseModel):
    from_acc: str
    to_acc: str
    amount: float
    note: str = ""


# ── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await bus.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        bus.disconnect(websocket)
    except Exception:
        bus.disconnect(websocket)


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.post("/create_session")
async def create_session(req: CreateSessionRequest):
    try:
        initiator = req.client_a or req.initiator or "bank_a"
        peer = req.client_b or req.peer or "bank_b"
        hybrid = req.use_hybrid or req.pqc
        res = kms.create_session(initiator, peer, hybrid)
        res.pop("key", None)
        await bus.broadcast({
            "event": "session",
            "session_id": res.get("session_id"),
            "qber": res.get("qber"),
            "status": res.get("status"),
        })
        return res
    except Exception as e:
        health = kms.check_link_health()
        await bus.broadcast({
            "event": "attack",
            "qber": health["last_qber"],
            "status": "RED",
        })
        return {"error": str(e), "qber": health["last_qber"], "status": "RED"}


@app.post("/join_session")
async def join_session(req: JoinSessionRequest):
    """Join an existing session and retrieve the shared key."""
    try:
        result = kms.join_session(req.session_id, req.device_id)
        return {
            "session_id": result["session_id"],
            "key_hex": result["key_hex"],
            "qber": result["qber"],
            "status": result["status"],
            "joined": result["joined"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/get_key")
async def get_key(req: GetKeyRequest):
    try:
        return kms.get_key(req.session_id, req.client_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Client not in session")


@app.get("/link_status")
async def link_status():
    """Current quantum link health + escalation info."""
    ls = kms.get_link_status()
    health = kms.check_link_health()
    return {
        "status": ls["status"],
        "qber": ls["qber"],
        "attacks_detected": ls["attacks_detected"],
        "eve_mode": ls["eve_mode"],
        "eve_active": health["eve_active"],
        "escalation_level": ls["escalation_level"],
        "escalation_label": ls["escalation_label"],
        "current_port": ls["current_port"],
        "current_ip": ls["current_ip"],
        "current_network": ls["current_network"],
        "total_keys_issued": health["total_keys_issued"],
        "total_sessions": health["total_sessions"],
        "active_sessions": health["active_sessions"],
    }


@app.get("/sessions")
async def list_sessions():
    return {"sessions": kms.list_sessions()}


@app.post("/activate_eve")
async def activate_eve():
    kms.set_eve_mode(True)
    await bus.broadcast({"event": "attack", "action": "eve_activated"})
    return {"eve_mode": True}


@app.post("/deactivate_eve")
async def deactivate_eve():
    kms.set_eve_mode(False)
    await bus.broadcast({"event": "session", "action": "eve_deactivated", "status": "GREEN"})
    return {"eve_mode": False}


@app.post("/trigger_attack")
async def trigger_attack():
    result = kms.trigger_attack()
    ls = kms.get_link_status()
    level = ls["escalation_level"]
    labels = {0: "Normal", 1: "Port Rotation", 2: "IP Failover",
              3: "Interface Switch", 4: "LOCKDOWN"}
    await bus.broadcast({
        "event": "attack",
        "session_id": result["session_id"],
        "qber": result["qber"],
        "attacks_detected": result.get("attacks_detected", 0),
    })
    await bus.broadcast({
        "event": "escalation" if level < 4 else "lockdown",
        "level": level,
        "action": labels.get(level, "Unknown"),
        "escalation_label": ls["escalation_label"],
        "port": ls["current_port"],
        "ip": ls["current_ip"],
        "current_network": ls["current_network"],
        "eve_active": ls["eve_mode"],
    })
    return {
        "status": result["status"],
        "qber": result["qber"],
        "attacks_detected": result.get("attacks_detected", 0),
        "escalation_level": level,
        "escalation_label": ls["escalation_label"],
    }


@app.post("/reset")
async def reset_system():
    """Clear all sessions, metrics, Eve state, and reset bank."""
    kms.reset()
    # Reset bank state too
    BANK_ACCOUNTS["ACC001"]["balance"] = 250000.00
    BANK_ACCOUNTS["ACC002"]["balance"] = 180000.00
    BANK_ACCOUNTS["ACC003"]["balance"] = 320000.00
    BANK_ACCOUNTS["ACC004"]["balance"] = 95000.00
    BANK_ACCOUNTS["HQ001"]["balance"] = 5000000.00
    TRANSACTION_LEDGER.clear()
    await bus.broadcast({"event": "session", "action": "system_reset", "status": "GREEN", "qber": 0.0})
    return {"status": "reset_complete", "message": "All state cleared. Link GREEN."}


# ── Banking simulation endpoints ────────────────────────────────────────

@app.get("/accounts")
async def get_accounts():
    return {"accounts": [
        {"id": k, "name": v["name"],
         "balance": v["balance"], "ifsc": v["ifsc"]}
        for k, v in BANK_ACCOUNTS.items()
    ]}


@app.post("/transfer")
async def transfer_funds(req: TransferRequest):
    """
    Real quantum-secured transfer:
    1. Run BB84 session to get quantum key
    2. Encrypt transaction payload with AES-256-GCM using that key
    3. Log the encrypted payload
    4. Apply the transfer
    5. Broadcast event to all windows via WebSocket
    """

    if req.from_acc not in BANK_ACCOUNTS:
        raise HTTPException(400, "Unknown source account")
    if req.to_acc not in BANK_ACCOUNTS:
        raise HTTPException(400, "Unknown destination account")
    if BANK_ACCOUNTS[req.from_acc]["balance"] < req.amount:
        raise HTTPException(400, "Insufficient funds")
    if req.amount <= 0:
        raise HTTPException(400, "Invalid amount")

    # Check quantum channel health first
    health = kms.check_link_health()
    if health["status"] == "RED":
        await bus.broadcast({
            "event": "attack",
            "message": "Transfer BLOCKED — quantum channel compromised",
            "qber": health["last_qber"],
        })
        raise HTTPException(503,
            f"Transfer blocked: quantum channel compromised (QBER={health['last_qber']:.2%})")

    # Run real BB84 session to derive transaction key
    try:
        session_result = kms.create_session(
            client_a=req.from_acc,
            client_b=req.to_acc,
            use_hybrid=False,
        )
    except Exception as e:
        err_msg = str(e)
        if "compromised" in err_msg.lower() or "qber" in err_msg.lower():
            await bus.broadcast({
                "event": "attack",
                "message": "Transfer BLOCKED — quantum channel compromised mid-exchange",
                "qber": kms.check_link_health()["last_qber"],
            })
            raise HTTPException(503, f"Transfer blocked: quantum channel compromised")
        raise HTTPException(500, f"Transfer error: {err_msg}")

    # AES-256-GCM encrypt the transaction payload
    tx_id = uuid.uuid4().hex
    tx_payload = {
        "from": req.from_acc,
        "to": req.to_acc,
        "amount": req.amount,
        "note": req.note,
        "timestamp": time.time(),
        "tx_id": tx_id,
    }
    payload_bytes = json.dumps(tx_payload).encode()

    aes_key = session_result["key"]   # bytes from KMS
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, payload_bytes, None)

    # Apply transfer
    BANK_ACCOUNTS[req.from_acc]["balance"] -= req.amount
    BANK_ACCOUNTS[req.to_acc]["balance"] += req.amount

    # Log to ledger
    ledger_entry = {
        "tx_id": tx_id,
        "from_acc": req.from_acc,
        "from_name": BANK_ACCOUNTS[req.from_acc]["name"],
        "to_acc": req.to_acc,
        "to_name": BANK_ACCOUNTS[req.to_acc]["name"],
        "amount": req.amount,
        "note": req.note,
        "qber": session_result["qber"],
        "session_id": session_result["session_id"],
        "encrypted_payload": ciphertext.hex()[:64] + "...",
        "nonce": nonce.hex(),
        "timestamp": time.time(),
        "status": "COMPLETED",
    }
    TRANSACTION_LEDGER.insert(0, ledger_entry)
    if len(TRANSACTION_LEDGER) > 100:
        TRANSACTION_LEDGER.pop()

    # Broadcast to all windows
    await bus.broadcast({
        "event": "transaction",
        "tx_id": tx_id[:12],
        "from": BANK_ACCOUNTS[req.from_acc]["name"],
        "to": BANK_ACCOUNTS[req.to_acc]["name"],
        "amount": req.amount,
        "qber": session_result["qber"],
        "session_id": session_result["session_id"][:12],
        "encrypted_preview": ciphertext.hex()[:32] + "...",
    })

    return {
        "tx_id": tx_id,
        "status": "COMPLETED",
        "from_name": BANK_ACCOUNTS[req.from_acc]["name"],
        "to_name": BANK_ACCOUNTS[req.to_acc]["name"],
        "amount": req.amount,
        "new_balance": BANK_ACCOUNTS[req.from_acc]["balance"],
        "qber": session_result["qber"],
        "session_id": session_result["session_id"],
        "encrypted_payload_preview": ciphertext.hex()[:64] + "...",
        "nonce": nonce.hex(),
        "encryption": "AES-256-GCM",
        "key_source": "BB84 QKD via AerSimulator",
    }


@app.get("/transactions")
async def get_transactions():
    return {"transactions": TRANSACTION_LEDGER}


@app.post("/reset_bank")
async def reset_bank():
    """Reset bank balances and ledger for demo restart."""
    BANK_ACCOUNTS["ACC001"]["balance"] = 250000.00
    BANK_ACCOUNTS["ACC002"]["balance"] = 180000.00
    BANK_ACCOUNTS["ACC003"]["balance"] = 320000.00
    BANK_ACCOUNTS["ACC004"]["balance"] = 95000.00
    BANK_ACCOUNTS["HQ001"]["balance"] = 5000000.00
    TRANSACTION_LEDGER.clear()
    return {"status": "bank_reset"}


# ── Webapp serving ──────────────────────────────────────────────────────

@app.get("/app", response_class=FileResponse)
async def serve_webapp():
    """Serve the banking web application."""
    index_file = os.path.join(webapp_dir, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file, media_type="text/html")
    return HTMLResponse("<h2>Webapp not found. Check webapp/index.html</h2>")


@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    return HTMLResponse('<meta http-equiv="refresh" content="0;url=/app">')


@app.on_event("startup")
async def startup_banner():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "127.0.0.1"
    print()
    print("=" * 70)
    print("  FinQuantum Shield — KMS v4.0 — ONLINE")
    print("=" * 70)
    print(f"  Bank App:  http://127.0.0.1:8000/app")
    print(f"  API Docs:  http://127.0.0.1:8000/docs")
    print(f"  LAN:       http://{lan_ip}:8000")
    print(f"  WebSocket: ws://{lan_ip}:8000/ws/events")
    print("=" * 70)
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FinQuantum Shield KMS API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("kms.kms_server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
