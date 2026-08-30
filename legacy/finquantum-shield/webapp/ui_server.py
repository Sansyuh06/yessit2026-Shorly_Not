"""
ShorlyNot — Web UI Server
Serves defense.html / code.html and bridges WebSocket to KMS backend.

Architecture:
  Browser (defense.html) ←WebSocket→ ui_server.py ←HTTP→ kms_server.py

Run: python webapp/ui_server.py
Dashboard: http://localhost:8501/
Banking:   http://localhost:8501/banking
"""

import asyncio
import json
import os
import time
import websockets
from pathlib import Path
from http import HTTPStatus
import httpx

KMS_URL = os.getenv("KMS_URL", "http://localhost:8000")
UI_PORT = int(os.getenv("UI_PORT", "8501"))
UI_DIR = Path(__file__).parent.parent.parent / "UI"

connected_clients: set = set()


async def broadcast(event: dict):
    """Send event to all connected WebSocket clients."""
    global connected_clients
    if not connected_clients:
        return
    message = json.dumps(event)
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send(message)
        except websockets.ConnectionClosed:
            dead.add(ws)
    for ws in dead:
        connected_clients.discard(ws)


async def poll_kms():
    """Poll KMS every 2 seconds and broadcast status changes."""
    last_status = {}
    while True:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{KMS_URL}/link_status")
                status = r.json()
                if status != last_status:
                    await broadcast(
                        {
                            "type": "status_update",
                            "data": status,
                            "timestamp": time.time(),
                        }
                    )
                    last_status = status
        except Exception:
            pass
        await asyncio.sleep(2)


async def handle_client(websocket):
    """Handle WebSocket client connection."""
    connected_clients.add(websocket)
    try:
        # Send initial status
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{KMS_URL}/link_status")
                await websocket.send(
                    json.dumps({"type": "initial_status", "data": r.json()})
                )
        except Exception:
            await websocket.send(json.dumps({"type": "kms_offline"}))

        async for message in websocket:
            cmd = json.loads(message)
            await handle_command(cmd, websocket)
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)


async def handle_command(cmd: dict, websocket):
    """Route UI commands to KMS backend."""
    action = cmd.get("action", "")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if action == "create_session":
                r = await client.post(
                    f"{KMS_URL}/create_session",
                    json={
                        "initiator": cmd.get("initiator", "Alice"),
                        "peer": cmd.get("peer", "Bob"),
                        "pqc": cmd.get("pqc", False),
                    },
                )
                await broadcast({"type": "session_created", "data": r.json()})

            elif action == "activate_eve":
                await client.post(f"{KMS_URL}/activate_eve")
                await broadcast({"type": "eve_activated"})

            elif action == "deactivate_eve":
                await client.post(f"{KMS_URL}/deactivate_eve")
                await broadcast({"type": "eve_deactivated"})

            elif action == "trigger_attack":
                r = await client.post(f"{KMS_URL}/trigger_attack", timeout=30)
                await broadcast({"type": "attack_result", "data": r.json()})

            elif action == "reset":
                await client.post(f"{KMS_URL}/deactivate_eve")
                await client.post(f"{KMS_URL}/reset")
                await broadcast({"type": "system_reset"})

            elif action == "get_status":
                r = await client.get(f"{KMS_URL}/link_status")
                await websocket.send(
                    json.dumps({"type": "status_update", "data": r.json()})
                )
    except Exception as e:
        await websocket.send(json.dumps({"type": "error", "message": str(e)}))


from websockets.http11 import Response, Headers

async def serve_html(*args):
    """Serve static HTML files."""
    request = None
    for arg in args:
        if hasattr(arg, "headers"):
            request = arg
            break
            
    if request and request.headers.get("Upgrade", "").lower() == "websocket":
        return None
        
    path = "/"
    if request and hasattr(request, "path"):
        path = request.path
        
    if path == "/" or path == "/dashboard":
        serve_path = UI_DIR / "defense.html"
    elif path == "/banking":
        serve_path = UI_DIR / "code.html"
    else:
        clean = path.lstrip("/")
        serve_path = UI_DIR / clean
        if not serve_path.exists():
            return Response(404, "Not Found", Headers([]), b"Not Found")

    if not serve_path.exists():
        return Response(404, "Not Found", Headers([]), b"Not Found")

    content = serve_path.read_bytes()
    ct = {"html": "text/html", "js": "application/javascript", "css": "text/css"}.get(
        serve_path.suffix.lstrip("."), "application/octet-stream"
    )
    return Response(200, "OK", Headers([("Content-Type", ct)]), content)


async def main():
    print(f"[UI] Dashboard: http://localhost:{UI_PORT}/")
    print(f"[UI] Banking:   http://localhost:{UI_PORT}/banking")
    print(f"[UI] KMS:       {KMS_URL}")

    poll_task = asyncio.create_task(poll_kms())

    async with websockets.serve(
        handle_client,
        "0.0.0.0",
        UI_PORT,
        process_request=serve_html,
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
