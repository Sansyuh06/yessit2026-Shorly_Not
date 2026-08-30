"""
Tests for the ShorlyNot Mock Bank Application.
"""

import pytest
from fastapi.testclient import TestClient
from bank.app.main import app, auth_mgr, ledger, skeleton_client


@pytest.fixture(autouse=True)
def reset_bank_state():
    auth_mgr.reset_users()
    ledger.clear()
    skeleton_client.reset_stages()
    yield


def test_bank_login_and_home_access():
    client = TestClient(app)
    
    # 1. Login as alice
    login_resp = client.post("/login", data={"username": "alice", "password": "alice123"}, follow_redirects=False)
    assert login_resp.status_code == 303
    assert "session_token" in login_resp.cookies
    token = login_resp.cookies["session_token"]

    # 2. Access /home with session cookie
    client.cookies.set("session_token", token)
    home_resp = client.get("/home")
    assert home_resp.status_code == 200
    assert "₹50,000.00" in home_resp.text


def test_bank_transfer_moves_balances():
    client = TestClient(app)
    login_resp = client.post("/login", data={"username": "alice", "password": "alice123"}, follow_redirects=False)
    token = login_resp.cookies["session_token"]
    client.cookies.set("session_token", token)

    # Initial balances: Alice = 50,000, Bob = 20,000
    transfer_resp = client.post("/transfer", data={"to_user": "bob", "amount": 2500.0})
    assert transfer_resp.status_code == 200
    assert "successfully quantum-signed" in transfer_resp.text

    assert auth_mgr.users["alice"].balance == 47500.0
    assert auth_mgr.users["bob"].balance == 22500.0


def test_bank_transfers_blocked_when_attack_escalates_stage():
    client = TestClient(app)
    login_resp = client.post("/login", data={"username": "alice", "password": "alice123"}, follow_redirects=False)
    token = login_resp.cookies["session_token"]
    client.cookies.set("session_token", token)

    # Trigger a forgery attack via SOC
    atk_resp = client.post("/soc/attack/forgery")
    assert atk_resp.status_code == 200

    # Verify stage escalated to S2
    stage_state = skeleton_client.get_stages()
    assert stage_state.stage_s.value >= 2

    # Attempt honest transfer -> must be declined by security policy
    tx_resp = client.post("/transfer", data={"to_user": "bob", "amount": 1000.0})
    assert "Transfers Disabled by Security Policy" in tx_resp.text or "suspended by security policy" in tx_resp.text

    # Balances must remain unchanged
    assert auth_mgr.users["alice"].balance == 50000.0


def test_soc_reset_restores_operations():
    client = TestClient(app)
    login_resp = client.post("/login", data={"username": "ops", "password": "ops123"}, follow_redirects=False)
    token = login_resp.cookies["session_token"]
    client.cookies.set("session_token", token)
    
    # 1. Trigger channel attack -> escalates to S4
    atk_resp = client.post("/soc/attack/channel")
    assert atk_resp.status_code == 200
    assert skeleton_client.get_stages().stage_s.value >= 2

    # 2. Reset security stages via SOC
    reset_resp = client.post("/soc/reset")
    assert reset_resp.status_code == 200
    assert skeleton_client.get_stages().stage_s.value == 0


def test_soc_unauthenticated_write_rejected():
    client = TestClient(app)
    # Anonymous unauthenticated client attempting SOC modification
    atk_resp = client.post("/soc/attack/channel")
    assert atk_resp.status_code == 401
    assert "Authentication Required" in atk_resp.text


def test_bank_nan_amount_rejected():
    client = TestClient(app)
    login_resp = client.post("/login", data={"username": "alice", "password": "alice123"}, follow_redirects=False)
    token = login_resp.cookies["session_token"]
    client.cookies.set("session_token", token)

    # Attempting to post NaN or invalid non-finite amount must not crash with 500
    tx_resp = client.post("/transfer", data={"to_user": "bob", "amount": "nan"})
    assert tx_resp.status_code in (200, 422)  # Either clean form error or schema validation
    if tx_resp.status_code == 200:
        assert "Invalid" in tx_resp.text or "Insufficient" in tx_resp.text
    assert auth_mgr.users["alice"].balance == 50000.0
