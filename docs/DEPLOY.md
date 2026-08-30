# DEPLOY.md — ShorlyNot Deployment & Demo Guide

## System Requirements
- OS: Windows 10/11 or Linux / macOS
- Python: 3.11 or 3.12
- Memory: 4 GB+ RAM
- Ports:
  - `8000`: ShorlyNot Skeleton Framework API
  - `8080`: Bank Portal & Real-time SOC Dashboard

---

## One-Command Quick Start

### Windows (PowerShell / Command Prompt)
```powershell
.\scripts\run_demo.bat
```

### Linux / macOS (Bash)
```bash
chmod +x ./scripts/run_demo.sh
./scripts/run_demo.sh
```

---

## Manual Multi-Terminal Startup

### Terminal 1: Start Skeleton Framework API
```bash
cd skeleton
pip install -e .
uvicorn shorlynot_skeleton.api.app:app --host 127.0.0.1 --port 8000 --reload
```
- OpenAPI Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/v1/status`

### Terminal 2: Start Mock Bank & SOC
```bash
cd bank
pip install -r requirements.txt
python -m app.main
```
- Bank Customer Web Portal: `http://127.0.0.1:8080`
- Dark SOC Threat Monitoring: `http://127.0.0.1:8080/soc`

---

## Pre-Seeded Demonstration Accounts

| Username | Password | Role | Starting Balance | Purpose |
|---|---|---|---|---|
| `alice` | `alice123` | Customer | ₹50,000 | Legitimate sender |
| `bob` | `bob123` | Customer | ₹20,000 | Legitimate receiver |
| `carol` | `carol123` | Customer | ₹10,000 | Third-party customer |
| `eve` | `eve123` | Attacker | ₹1,000 | Attacker attempting signature spoofing |
| `ops` | `ops123` | SOC Officer | ₹0 | Security operations admin |

---

## 3-Minute Live Pitch Demo Script

1. **Baseline Operations**:
   - Open `http://127.0.0.1:8080/soc` in one window. Observe **Stage S0**, **SIM Backend**, **Zero Threat Rate**.
   - Open `http://127.0.0.1:8080` in another window. Log in as `alice`.
   - Transfer ₹1,000 to `bob`.
   - **Result**: Transfer succeeds. SOC logs `OK`, empirical mismatch $\hat{p} < \tau$ (e.g. $\hat{p} = 0.015 \le 0.210$).
2. **Execute Forgery Attack**:
   - On the SOC console or using the attack panel, trigger `Simulate Signature Forgery`.
   - **Result**: Quantum projective verification yields high mismatch ($\hat{p} \approx 0.50 > 0.210$). Q-STDF flags `FORGERY` in bold red.
   - Stage escalates to **Stage S2 (Transfers Suspended)**.
3. **Show Bank Application Lockdown**:
   - Switch to Alice's bank tab and attempt another transfer of ₹2,500.
   - **Result**: Bank blocks the transfer instantly with *“New transfers suspended (security stage S2)”*.
4. **Execute Replay Attack**:
   - Trigger `Simulate Nonce Replay Attack`.
   - **Result**: Nonce duplication detected instantly by Q-STDF binding layer $\rightarrow$ Stage escalates to **Stage S3 / S4**.
   - Bank enters full lockdown.
5. **Review Metrics & Reset**:
   - Show Hoeffding $\tau$ parameters ($p_0=0.02, n=64, \delta=0.01, \tau=0.210$), $P_{\text{forge}} < 10^{-5}$, and sub-millisecond classification latency.
   - Click **Reset Security Stage** to restore operational readiness.
