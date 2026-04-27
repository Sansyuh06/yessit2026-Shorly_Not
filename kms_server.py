# DEPRECATED — This file is the legacy root-level server.
# The active server is kms/kms_server.py
# Run with: python -m uvicorn kms.kms_server:app --port 8000
# Do not use this file directly. It is kept for reference only.
"""
KMS Server (FastAPI) — LEGACY / DEPRECATED
===========================================
FinQuantum Shield — Quantum-Safe Banking Security Platform

⚠ WARNING: Use kms/kms_server.py instead. This file is missing:
  - Banking simulation (/accounts, /transfer, /transactions)
  - Webapp serving (/app)
  - Full CORS middleware
  - Updated escalation levels (L0-L4)

The canonical server is: python -m uvicorn kms.kms_server:app --port 8000
"""

import sys
import os
import socket
import asyncio
import json
from datetime import datetime, timezone
from typing import List

import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
WEBAPP_DIR = BASE_DIR / "webapp"
STATIC_DIR = WEBAPP_DIR / "static"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kms.key_management_service import KeyManagementService


# =============================================================================
# EVENT BUS (WebSocket broadcast)
# =============================================================================

class EventBus:
    """Broadcast events to all connected WebSocket clients."""

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


def _fire(event: dict):
    """Schedule a broadcast from sync context."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(bus.broadcast(event))
    except RuntimeError:
        pass  # no event loop running (e.g. tests)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateSessionRequest(BaseModel):
    initiator: str
    peer: str
    pqc: bool = False

class JoinSessionRequest(BaseModel):
    session_id: str
    device_id: str

class LegacyKeyRequest(BaseModel):
    """Backward compat for simple key requests."""
    device_id: str
    peer_id: str = "_broadcast_"
    force_attack: bool = False
    pqc: bool = False


# =============================================================================
# APPLICATION
# =============================================================================

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


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """Real-time event stream for CMD logger and monitoring tools."""
    await bus.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        bus.disconnect(websocket)
    except Exception:
        bus.disconnect(websocket)


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@app.post("/create_session")
async def create_session(req: CreateSessionRequest):
    """
    Create a key exchange session between two devices.
    Runs BB84 QKD, validates QBER, derives AES-256 key via HKDF.
    """
    try:
        result = kms.create_session(
            initiator=req.initiator,
            peer=req.peer,
            pqc_enabled=req.pqc,
        )
        # Broadcast session event
        await bus.broadcast({
            "event": "session",
            "session_id": result["session_id"],
            "qber": result["qber"],
            "status": result["status"],
            "initiator": result["initiator"],
            "peer": result["peer"],
            "sifted_key_length": 0,
        })
        await bus.broadcast({
            "event": "key",
            "key_preview": result["key_hex"][:16],
            "algorithm": "HKDF-SHA256 → AES-256-GCM",
        })
        return {
            "session_id": result["session_id"],
            "key_hex": result["key_hex"],
            "qber": result["qber"],
            "status": result["status"],
            "initiator": result["initiator"],
            "peer": result["peer"],
            "pqc_enabled": result["pqc_enabled"],
        }
    except Exception as e:
        health = kms.check_link_health()
        qber_val = health["last_qber"]
        await bus.broadcast({
            "event": "session",
            "session_id": "REFUSED",
            "qber": qber_val,
            "status": "RED",
            "error": str(e),
        })
        return {
            "error": str(e),
            "qber": qber_val,
            "status": health["status"],
        }


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


@app.post("/get_session_key")
async def get_session_key(req: LegacyKeyRequest):
    """Simplified key request (backward compatible)."""
    try:
        old_eve = kms.eve_active
        if req.force_attack:
            kms.activate_eve()

        key_bytes = kms.get_fresh_key(
            device_id=req.device_id,
            peer_id=req.peer_id,
            pqc_enabled=req.pqc,
        )

        if req.force_attack:
            if not old_eve:
                kms.deactivate_eve()

        health = kms.check_link_health()
        return {
            "key_hex": key_bytes.hex(),
            "qber": health["last_qber"],
            "status": health["status"],
        }
    except Exception as e:
        health = kms.check_link_health()
        return {
            "error": str(e),
            "qber": health["last_qber"],
            "status": health["status"],
        }


@app.get("/link_status")
async def link_status():
    """Current quantum link health + escalation info."""
    ls = kms.get_link_status()
    health = kms.check_link_health()
    return {
        "status": ls["status"],
        "qber": ls["qber"],
        "total_keys_issued": health["total_keys_issued"],
        "total_sessions": health["total_sessions"],
        "attacks_detected": ls["attacks_detected"],
        "active_sessions": health["active_sessions"],
        "eve_active": health["eve_active"],
        "eve_mode": ls["eve_mode"],
        "escalation_level": ls["escalation_level"],
        "escalation_label": ls["escalation_label"],
        "current_port": ls["current_port"],
        "current_ip": ls["current_ip"],
        "current_network": ls["current_network"],
    }


@app.get("/sessions")
async def list_sessions():
    """List all active sessions (key material is NOT included)."""
    return {"sessions": kms.list_sessions()}


@app.post("/activate_eve")
async def activate_eve():
    """Turn on the eavesdropper."""
    kms.activate_eve()
    await bus.broadcast({
        "event": "attack",
        "action": "eve_activated",
        "message": "Eve is now intercepting the quantum channel",
    })
    return {"eve_active": True, "message": "Eve is now intercepting the quantum channel."}


@app.post("/deactivate_eve")
async def deactivate_eve():
    """Turn off the eavesdropper."""
    kms.deactivate_eve()
    await bus.broadcast({
        "event": "session",
        "action": "eve_deactivated",
        "status": "GREEN",
        "qber": 0.0,
    })
    return {"eve_active": False, "message": "Eve deactivated. Quantum channel clear."}


@app.post("/trigger_attack")
async def trigger_attack():
    """Run a single BB84 probe with Eve active → RED status."""
    result = kms.trigger_attack()
    ls = kms.get_link_status()
    await bus.broadcast({
        "event": "attack",
        "session_id": result["session_id"],
        "qber": result["qber"],
        "status": "RED",
        "attacks_detected": result.get("attacks_detected", 0),
    })
    # Broadcast escalation status
    level = ls["escalation_level"]
    labels = {1: "Port Rotation", 2: "IP Failover",
              3: "Interface Switch", 4: "LOCKDOWN"}
    await bus.broadcast({
        "event": "escalation" if level < 4 else "lockdown",
        "level": level,
        "action": labels.get(level, "Unknown"),
        "port": ls["current_port"],
        "ip": ls["current_ip"],
        "network": ls["current_network"],
    })
    return {
        "status": result["status"],
        "qber": result["qber"],
        "attacks_detected": result.get("attacks_detected", 0),
        "escalation_level": level,
        "escalation_label": ls["escalation_label"],
        "message": "Attack detected — link status RED.",
    }


@app.post("/reset")
async def reset_system():
    """Clear all sessions, metrics, and Eve state."""
    kms.reset()
    await bus.broadcast({
        "event": "session",
        "action": "system_reset",
        "status": "GREEN",
        "qber": 0.0,
    })
    return {"status": "reset_complete", "message": "All state cleared. Link GREEN."}


# =============================================================================
# STATUS PAGE (HTML)
# =============================================================================

STATUS_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FinQuantum Shield — KMS Status</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --green: #10b981;
      --yellow: #f59e0b;
      --red: #ef4444;
      --ink: #0f172a;
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      color: #e2e8f0;
      background: var(--bg);
      min-height: 100vh;
    }
    .wrap { max-width: 960px; margin: 0 auto; padding: 24px 20px; }
    .header {
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 24px;
    }
    .header h1 { font-size: 1.5rem; font-weight: 700; }
    .header h1 span { color: var(--green); }
    .status-badge {
      font-size: 14px; font-weight: 700;
      padding: 6px 16px; border-radius: 999px;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 20px; margin-bottom: 16px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .tile {
      background: #0f172a; border: 1px solid var(--border);
      border-radius: 8px; padding: 14px;
    }
    .tile strong { color: #94a3b8; font-size: 12px; text-transform: uppercase; }
    .tile .val { font-size: 20px; font-weight: 700; margin-top: 4px; }
    .esc-bar {
      margin-top: 16px; padding: 12px 16px; border-radius: 8px;
      font-weight: 700; font-size: 14px;
    }
    .btns { margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
    button {
      border: none; border-radius: 8px; padding: 10px 16px;
      font-weight: 600; cursor: pointer; font-size: 13px;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.8; }
    .btn-green { background: #065f46; color: #6ee7b7; }
    .btn-red { background: #7f1d1d; color: #fca5a5; }
    .btn-yellow { background: #78350f; color: #fcd34d; }
    .btn-blue { background: #1e3a5f; color: #93c5fd; }
    #log {
      background: #020617; border: 1px solid var(--border);
      border-radius: 8px; padding: 12px; margin-top: 16px;
      font-family: 'Courier New', monospace; font-size: 12px;
      height: 200px; overflow-y: auto; color: #94a3b8;
    }
    .log-entry { margin-bottom: 2px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>🛡️ <span>FinQuantum</span> Shield — KMS</h1>
      <div id="status" class="status-badge">CONNECTING...</div>
    </div>

    <div class="card">
      <div class="grid">
        <div class="tile"><strong>QBER</strong><div class="val" id="qber">—</div></div>
        <div class="tile"><strong>Eve Mode</strong><div class="val" id="eve">—</div></div>
        <div class="tile"><strong>Attacks</strong><div class="val" id="attacks">—</div></div>
        <div class="tile"><strong>Escalation</strong><div class="val" id="escalation">—</div></div>
        <div class="tile"><strong>Port</strong><div class="val" id="port">—</div></div>
        <div class="tile"><strong>IP</strong><div class="val" id="ip">—</div></div>
        <div class="tile"><strong>Keys Issued</strong><div class="val" id="keys">—</div></div>
        <div class="tile"><strong>Sessions</strong><div class="val" id="sessions">—</div></div>
      </div>

      <div id="esc-bar" class="esc-bar" style="background:#065f46;color:#6ee7b7">
        ESCALATION: L1 — Normal
      </div>

      <div class="btns">
        <button class="btn-green" onclick="callApi('/activate_eve')">🔴 Activate Eve</button>
        <button class="btn-yellow" onclick="callApi('/deactivate_eve')">🟢 Deactivate Eve</button>
        <button class="btn-red" onclick="callApi('/trigger_attack')">💥 Trigger Attack</button>
        <button class="btn-blue" onclick="callApi('/reset')">🔄 Reset</button>
      </div>
    </div>

    <div class="card">
      <strong style="color:#94a3b8;font-size:12px;text-transform:uppercase">Live Event Log</strong>
      <div id="log"></div>
    </div>
  </div>

  <script>
    const $ = id => document.getElementById(id);
    const colors = { GREEN: 'var(--green)', YELLOW: 'var(--yellow)', RED: 'var(--red)' };
    const escColors = {
      0: {bg:'#065f46',fg:'#6ee7b7'},
      1: {bg:'#065f46',fg:'#6ee7b7'},
      2: {bg:'#78350f',fg:'#fcd34d'},
      3: {bg:'#7f1d1d',fg:'#fca5a5'},
      4: {bg:'#7f1d1d',fg:'#ffffff'},
    };
    const escLabels = {
      0:'L0 — Normal / All Systems Operational',
      1:'L1 — Port Rotation',
      2:'L2 — IP Failover',
      3:'L3 — Interface Switch',
      4:'L4 — EMERGENCY LOCKDOWN',
    };

    async function refresh() {
      try {
        const res = await fetch('/link_status');
        const d = await res.json();
        $('status').textContent = d.status;
        $('status').style.background = colors[d.status] || '#475569';
        $('status').style.color = '#fff';
        $('qber').textContent = (d.qber || 0).toFixed(4);
        $('eve').textContent = d.eve_mode ? '🔴 ACTIVE' : '🟢 OFF';
        $('eve').style.color = d.eve_mode ? '#ef4444' : '#10b981';
        $('attacks').textContent = d.attacks_detected;
        $('escalation').textContent = `L${d.escalation_level}`;
        $('port').textContent = d.current_port;
        $('ip').textContent = d.current_ip;
        $('keys').textContent = d.total_keys_issued || 0;
        $('sessions').textContent = d.total_sessions || 0;
        const lv = d.escalation_level || 1;
        const ec = escColors[lv] || escColors[1];
        $('esc-bar').style.background = ec.bg;
        $('esc-bar').style.color = ec.fg;
        $('esc-bar').textContent = 'ESCALATION: ' + (escLabels[lv] || 'L1');
      } catch(e) {
        $('status').textContent = 'OFFLINE';
        $('status').style.background = '#475569';
      }
    }

    async function callApi(path) {
      await fetch(path, { method: 'POST' });
      await refresh();
    }

    // WebSocket live log
    function connectWS() {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${proto}://${location.host}/ws/events`);
      ws.onmessage = (e) => {
        const ev = JSON.parse(e.data);
        const ts = (ev.timestamp || '').slice(11, 19);
        const type = (ev.event || 'info').toUpperCase();
        const color = {SESSION:'#10b981',ATTACK:'#ef4444',ESCALATION:'#f59e0b',LOCKDOWN:'#ef4444',KEY:'#6ee7b7'}[type] || '#94a3b8';
        const log = $('log');
        const div = document.createElement('div');
        div.className = 'log-entry';
        div.innerHTML = `<span style="color:${color}">[${ts}] [${type}]</span> ${JSON.stringify(ev).slice(0,120)}`;
        log.appendChild(div);
        log.scrollTop = log.scrollHeight;
        refresh();
      };
      ws.onclose = () => setTimeout(connectWS, 2000);
    }

    refresh();
    setInterval(refresh, 3000);
    connectWS();
  </script>
</body>
</html>
"""


# Mount static files for the banking webapp
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def banking_app():
    """Serve the banking web application."""
    index_file = WEBAPP_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    return HTMLResponse(STATUS_PAGE)


@app.get("/status", response_class=HTMLResponse)
async def status_page():
    """Legacy KMS status page."""
    return HTMLResponse(STATUS_PAGE)


@app.on_event("startup")
async def startup_banner():
    lan_ip = get_lan_ip()
    print()
    print("=" * 70)
    print("  FinQuantum Shield — KMS v4.0 — ONLINE")
    print("=" * 70)
    print(f"  Banking App:  http://127.0.0.1:8000")
    print(f"  LAN:          http://{lan_ip}:8000")
    print(f"  KMS Status:   http://{lan_ip}:8000/status")
    print(f"  API Docs:     http://{lan_ip}:8000/docs")
    print(f"  WebSocket:    ws://{lan_ip}:8000/ws/events")
    print("=" * 70)
    print()


if __name__ == "__main__":
    uvicorn.run("kms_server:app", host="0.0.0.0", port=8000, log_level="info")
