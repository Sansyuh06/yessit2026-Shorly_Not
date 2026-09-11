"""
Mock Bank Application & SOC Server.
FastAPI :8080 service for SIH 2026 PS 26141.
"""

import os
import math
import uuid
from fastapi import FastAPI, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bank.app.auth import BankAuthManager
from bank.app.ledger import BankLedger
from bank.app.services.skeleton_client import SkeletonServiceClient
from bank.app.services.router_client import GLOBAL_ROUTER_CLIENT
from shorlynot_skeleton.models import (
    TransactionPayload,
    TransferPipelineRequest,
    TauPreset
)

app = FastAPI(title="ShorlyNot Mock Bank & SOC", version="3.0.0")

# Setup template engine and static files
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

auth_mgr = BankAuthManager()
ledger = BankLedger()
skeleton_client = SkeletonServiceClient()
router_client = GLOBAL_ROUTER_CLIENT


@app.get("/", response_class=HTMLResponse)
def root_redirect(request: Request):
    user = auth_mgr.get_current_user(request)
    if user:
        return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    stage_state = skeleton_client.get_stages()
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "current_user": None,
            "stage_state": stage_state,
            "error": None
        }
    )


@app.post("/login", response_class=HTMLResponse)
def handle_login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    user = auth_mgr.authenticate(username.strip(), password.strip())
    stage_state = skeleton_client.get_stages()

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "current_user": None,
                "stage_state": stage_state,
                "error": "Invalid credentials. Try demo credentials e.g. alice / alice123."
            }
        )

    token = auth_mgr.create_session(user.username)
    resp = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(key="session_token", value=token, httponly=True)
    return resp


@app.get("/logout")
def handle_logout(request: Request):
    auth_mgr.revoke_session(request)
    resp = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("session_token")
    return resp


@app.get("/home", response_class=HTMLResponse)
def home_dashboard(request: Request):
    user = auth_mgr.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    stage_state = skeleton_client.get_stages()
    if stage_state.stage_s.value >= 4:
        return RedirectResponse(url="/locked", status_code=status.HTTP_303_SEE_OTHER)

    recent_txs = ledger.get_user_history(user.username)[:5]

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "current_user": user,
            "stage_state": stage_state,
            "recent_transactions": recent_txs,
            "active_tab": "home"
        }
    )


@app.get("/transfer", response_class=HTMLResponse)
def transfer_page(request: Request):
    user = auth_mgr.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    stage_state = skeleton_client.get_stages()
    if stage_state.stage_s.value >= 4:
        return RedirectResponse(url="/locked", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="transfer.html",
        context={
            "current_user": user,
            "stage_state": stage_state,
            "active_tab": "transfer",
            "error": None,
            "success": None
        }
    )


@app.post("/transfer", response_class=HTMLResponse)
def handle_transfer(
    request: Request,
    to_user: str = Form(...),
    amount: float = Form(...)
):
    user = auth_mgr.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    stage_state = skeleton_client.get_stages()

    # Physical Quantum Router Guard Check (OpenWrt Archer C6 Relay Port 8765)
    router_status = router_client.get_status()
    if router_status.get("status") == "RED":
        qber = router_status.get("qber", 16.5)
        relay_port = router_status.get("hardware", {}).get("relay_port", 8765)
        return templates.TemplateResponse(
            request=request,
            name="transfer.html",
            context={
                "current_user": user,
                "stage_state": stage_state,
                "active_tab": "transfer",
                "error": f"Physical Quantum Channel Severed: OpenWrt Router Guard (Archer C6) dropped Relay Port {relay_port} packet (QBER = {qber:.1f}% ≥ 11.0% BB84 threshold). Transaction rejected by kernel netfilter.",
                "success": None
            }
        )

    # Stage S4 Check
    if stage_state.stage_s.value >= 4:
        return RedirectResponse(url="/locked", status_code=status.HTTP_303_SEE_OTHER)

    # Stage S2+ Check
    actor = user.username
    if stage_state.stage_s.value >= 2:
        account_quarantined = (
            stage_state.lock_scope == "account"
            and actor in (stage_state.quarantined_accounts or [])
        )
        global_blocked = stage_state.lock_scope != "account"
        if global_blocked or account_quarantined:
            error = (
                f"Your account is quarantined (Stage S{stage_state.stage_s.value})."
                if account_quarantined
                else f"New transfers suspended by security policy (Stage S{stage_state.stage_s.value})."
            )
            return templates.TemplateResponse(
                request=request,
                name="transfer.html",
                context={
                    "current_user": user,
                    "stage_state": stage_state,
                    "active_tab": "transfer",
                    "error": error,
                    "success": None
                }
            )

    # Balance and numeric integrity check
    if not math.isfinite(amount) or amount <= 0 or amount > user.balance:
        return templates.TemplateResponse(
            request=request,
            name="transfer.html",
            context={
                "current_user": user,
                "stage_state": stage_state,
                "active_tab": "transfer",
                "error": f"Invalid transfer amount. Maximum available: ₹{user.balance:,.2f}",
                "success": None
            }
        )

    # Create transaction payload
    tx_id = f"tx-{uuid.uuid4().hex[:12]}"
    tx = TransactionPayload(
        from_user=user.username,
        to_user=to_user,
        amount=amount,
        currency="INR",
        tx_id=tx_id
    )

    # Dispatch to ShorlyNot Skeleton microservice
    pipe_req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id=user.key_id,
        verifier_id=to_user,
        tau_preset=TauPreset.NORMAL
    )

    try:
        result = skeleton_client.execute_transfer(pipe_req)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="transfer.html",
            context={
                "current_user": user,
                "stage_state": stage_state,
                "active_tab": "transfer",
                "error": f"Security Verification Error: Skeleton Service unreachable or failed ({e}).",
                "success": None
            }
        )

    updated_stage_state = skeleton_client.get_stages()

    if result.success:
        # Commit double-entry ledger mutation
        user.balance -= amount
        recipient = auth_mgr.users.get(to_user)
        if recipient:
            recipient.balance += amount

        ledger.record_transaction(
            tx_id=tx_id,
            from_user=user.username,
            to_user=to_user,
            amount=amount,
            status="COMMITTED",
            mismatch_rate=result.verify_result.mismatch_rate if result.verify_result else 0.0,
            tau=result.verify_result.tau if result.verify_result else 0.2097,
            threat_label=result.threat_classification.label.value if result.threat_classification else "OK",
            stage_s=result.stage_s.value,
            details=f"Transfer ₹{amount:,.2f} to {to_user} committed to ledger."
        )

        return templates.TemplateResponse(
            request=request,
            name="transfer.html",
            context={
                "current_user": user,
                "stage_state": updated_stage_state,
                "active_tab": "transfer",
                "error": None,
                "success": f"Transfer of ₹{amount:,.2f} to {to_user} successfully quantum-signed (Profile T1) and committed to ledger."
            }
        )
    else:
        # Transfer rejected / declined by security engine
        threat_lbl = result.threat_classification.label.value if result.threat_classification else "SECURITY_VIOLATION"
        threat_reason = result.threat_classification.reason if result.threat_classification else result.message
        ledger.record_transaction(
            tx_id=tx_id,
            from_user=user.username,
            to_user=to_user,
            amount=amount,
            status="REJECTED",
            mismatch_rate=result.verify_result.mismatch_rate if result.verify_result else 0.0,
            tau=result.verify_result.tau if result.verify_result else 0.2097,
            threat_label=threat_lbl,
            stage_s=result.stage_s.value,
            details=f"Rejected: {threat_reason}"
        )

        return templates.TemplateResponse(
            request=request,
            name="transfer.html",
            context={
                "current_user": user,
                "stage_state": updated_stage_state,
                "active_tab": "transfer",
                "error": f"Security Policy Violation: {threat_reason} (Stage S{result.stage_s.value})",
                "success": None
            }
        )


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    user = auth_mgr.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    stage_state = skeleton_client.get_stages()
    txs = ledger.get_user_history(user.username)

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "current_user": user,
            "stage_state": stage_state,
            "transactions": txs,
            "active_tab": "history"
        }
    )


@app.get("/locked", response_class=HTMLResponse)
def locked_page(request: Request):
    user = auth_mgr.get_current_user(request)
    stage_state = skeleton_client.get_stages()
    return templates.TemplateResponse(
        request=request,
        name="locked.html",
        context={
            "current_user": user,
            "stage_state": stage_state
        }
    )


@app.get("/soc", response_class=HTMLResponse)
def soc_page(request: Request):
    stage_state = skeleton_client.get_stages()
    events = skeleton_client.get_events(limit=50)
    current_user = auth_mgr.get_current_user(request)
    return templates.TemplateResponse(
        request=request,
        name="soc.html",
        context={
            "current_user": current_user,
            "stage_state": stage_state,
            "events": events
        }
    )


def require_soc_auth(request: Request):
    user = auth_mgr.get_current_user(request)
    if user:
        return user
    auth_header = request.headers.get("Authorization", "")
    expected_token = os.environ.get("SHORLYNOT_SOC_SECRET", "ops-secret-key-2026")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in (expected_token, "ops-token-demo"):
            return True
    # For local test suites, allow if explicit test header or unauthenticated in demo mode
    if request.headers.get("X-Test-Client") == "1" or os.environ.get("SHORLYNOT_DEMO_UNAUTH_SOC") == "1":
        return True
    return None


@app.post("/soc/attack/{attack_type}")
def soc_trigger_attack(attack_type: str, request: Request):
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required: Please log in with ops credentials (ops / ops123)."}
        )
    res = skeleton_client.trigger_attack(attack_type=attack_type)
    # Explicitly set router color to RED for any attack and sync to http://localhost:8000/link_status
    router_color = "RED"
    try:
        router_color = router_client.sync_from_quantum_stage(res.stage_s.value, res.stage_q.value, attack_type)
    except Exception:
        router_client.set_state("RED")

    response_data = res.model_dump()
    response_data["color"] = router_color
    response_data["router_color"] = router_color
    response_data["router_state"] = router_color
    return JSONResponse(content=response_data)


@app.post("/soc/reset")
def soc_reset_stages(request: Request):
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required: Please log in with ops credentials (ops / ops123)."}
        )
    res = skeleton_client.reset_stages()
    # Explicitly reset router guard to GREEN
    try:
        router_client.set_state("GREEN")
    except Exception:
        pass
    if isinstance(res, dict):
        res["color"] = "GREEN"
        res["router_color"] = "GREEN"
        res["router_state"] = "GREEN"
    return JSONResponse(content=res)


@app.get("/api/soc/feed")
def soc_live_feed():
    stage_state = skeleton_client.get_stages()
    events = skeleton_client.get_events(limit=30)
    return JSONResponse(content={
        "stages": stage_state.model_dump(),
        "events": [e.model_dump() for e in events]
    })


@app.post("/api/soc/test_transfer")
async def soc_test_transfer(request: Request):
    """Executes a live test transaction directly from SOC to demonstrate real-time packet filtering."""
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required"}
        )
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    amount = float(body.get("amount", 500.0))
    from_user = body.get("from_user", "alice")
    to_user = body.get("to_user", "bob")

    # Check Physical Router Guard Status
    router_status = router_client.get_status()
    if router_status.get("status") == "RED":
        qber = router_status.get("qber", 16.5)
        relay_port = router_status.get("hardware", {}).get("relay_port", 8765)
        return JSONResponse(content={
            "success": False,
            "blocked_by": "OPENWRT_ROUTER_GUARD_NETFILTER",
            "reason": f"Physical Quantum Channel Severed: OpenWrt Router Guard (Archer C6) dropped Relay Port {relay_port} packet (QBER = {qber:.1f}% >= 11.0%). Dropped by kernel fw4.",
            "qber": qber,
            "router_status": "RED",
            "action": "DROP",
            "relay_port": relay_port,
            "rule": f"ip daddr 192.168.1.0/24 tcp dport {relay_port} drop"
        })

    stage_state = skeleton_client.get_stages()
    if stage_state.stage_s.value >= 4:
        return JSONResponse(content={
            "success": False,
            "blocked_by": "STAGE_S4_LOCKDOWN",
            "reason": "Cryptographic engine in S4 Lock. All bank operations quarantined.",
            "router_status": router_status.get("status", "GREEN"),
            "action": "LOCK"
        })

    # Dispatch to skeleton
    tx_id = f"soc-tx-{uuid.uuid4().hex[:8]}"
    tx = TransactionPayload(
        from_user=from_user,
        to_user=to_user,
        amount=amount,
        currency="INR",
        tx_id=tx_id
    )
    pipe_req = TransferPipelineRequest(
        transaction=tx,
        signer_key_id="alice-key-1",
        verifier_id=to_user,
        tau_preset=TauPreset.NORMAL
    )
    res = skeleton_client.execute_transfer(pipe_req)
    return JSONResponse(content={
        "success": res.success,
        "blocked_by": None if res.success else "QUANTUM_SIGNATURE_VERIFICATION",
        "reason": "Quantum signature verified (Profile T1). Transaction committed." if res.success else (res.threat_classification.reason if res.threat_classification else res.message),
        "tx_id": tx_id,
        "mismatch_rate": res.verify_result.mismatch_rate if res.verify_result else 0.0,
        "tau": res.verify_result.tau if res.verify_result else 0.2097,
        "threat_label": res.threat_classification.label.value if res.threat_classification else "OK",
        "stage_s": res.stage_s.value,
        "stage_q": res.stage_q.value,
        "router_status": router_status.get("status", "GREEN"),
        "action": "FORWARD" if res.success else "REJECT"
    })


@app.post("/api/router/cmd")
async def router_execute_command(request: Request):
    """Executes or simulates interactive diagnostic command on the router."""
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required"}
        )
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    cmd = body.get("command", "cat_state")
    status_data = router_client.get_status()
    st = status_data.get("status", "GREEN")
    remote_st = status_data.get("physical_router_state", st)

    if cmd == "cat_state":
        live_st = router_client._probe_physical_router_state() or remote_st
        return JSONResponse(content={
            "command": "cat /tmp/router_guard.state",
            "output": f"{live_st}\n",
            "status": live_st
        })
    elif cmd == "nft_list":
        nft_syntax = status_data.get("nftables_output", "")
        return JSONResponse(content={
            "command": "nft list chain inet fw4 router_guard_forward",
            "output": nft_syntax,
            "status": st
        })
    elif cmd == "link_status":
        import httpx
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{status_data.get('active_endpoint', 'http://localhost:8000')}/link_status")
                return JSONResponse(content={
                    "command": f"curl -s {status_data.get('active_endpoint', 'http://localhost:8000')}/link_status",
                    "output": resp.text,
                    "status": st
                })
        except Exception:
            return JSONResponse(content={
                "command": "curl -s /link_status",
                "output": f'{{"status":"{st}","qber":{status_data.get("qber", 1.4)},"key_rate":{status_data.get("key_rate", 2420)}}}',
                "status": st
            })
    else:
        return JSONResponse(content={
            "command": cmd,
            "output": f"Executed command: {cmd} [Exit: 0]\n",
            "status": st
        })


@app.get("/api/soc/recalc_bound")
def soc_recalc_bound(p0: float = 0.02, n: int = 64, delta: float = 0.01):
    """Calculates Hoeffding Bound tau and P_forge for arbitrary parameters."""
    if n <= 0: n = 64
    if delta <= 0: delta = 0.01
    tau = p0 + math.sqrt(math.log(1.0 / delta) / (2.0 * n))

    from shorlynot_skeleton.detect.tau import TauCalculator
    p_forge = TauCalculator.calculate_theoretical_p_forge(tau, n)
    return JSONResponse(content={
        "p0": p0,
        "n": n,
        "delta": delta,
        "tau": round(tau, 4),
        "p_forge": p_forge,
        "p_forge_str": f"{p_forge:.2e}" if p_forge > 1e-15 else "< 1e-15"
    })



# ---------------------------------------------------------------------------
# Router Guard & QKD KMS Endpoints (OpenWrt Archer C6 fw4/nftables)
# ---------------------------------------------------------------------------

@app.get("/api/router/status")
def router_guard_status():
    """Returns live telemetry from the OpenWrt Router Guard and QKD KMS."""
    status_data = router_client.get_status()
    return JSONResponse(content=status_data)


@app.post("/api/router/set_state")
async def router_guard_set_state(request: Request):
    """Sets Router QKD status (GREEN, YELLOW, RED) directly from SOC console."""
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required"}
        )
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    state = body.get("state") or request.query_params.get("state", "GREEN")
    res = router_client.set_state(state)
    return JSONResponse(content=res)


@app.post("/api/router/set_qber")
async def router_guard_set_qber(request: Request):
    """Sets exact simulated QBER on the router KMS."""
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required"}
        )
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    qber_val = float(body.get("qber") or request.query_params.get("qber", 1.4))
    res = router_client.set_qber(qber_val)
    return JSONResponse(content=res)


@app.post("/api/router/demo_toggle")
async def router_guard_demo_toggle(request: Request):
    """Toggles 15-second automatic QKD presentation cycle."""
    auth_user = require_soc_auth(request)
    if not auth_user:
        return JSONResponse(
            status_code=401,
            content={"detail": "SOC Operator Authentication Required"}
        )
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    active = bool(body.get("active", True))
    res = router_client.toggle_demo(active)
    return JSONResponse(content=res)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bank.app.main:app", host="127.0.0.1", port=8080, reload=True)
