# FinQuantum Shield — Quantum-Safe Banking Security Platform

## What This Is

A **production-grade demo** of quantum-safe transaction security for banking. 
Instead of RSA/ECDH, real **Qiskit BB84 quantum circuits** running on **AerSimulator** 
generate shared secrets with information-theoretic security guarantees.

The system watches quantum-link health (QBER) and reacts to eavesdropper attacks 
by escalating through port rotation → IP failover → interface switch → emergency lockdown.

**Key differentiators from toy demos:**
- ✅ Real Qiskit `QuantumCircuit` + `AerSimulator` (not `random.Random()`)
- ✅ QBER emerges from quantum measurement statistics, never hardcoded
- ✅ Privacy amplification via Toeplitz matrix hashing
- ✅ Live WebSocket event bus for real-time monitoring
- ✅ 4-window demo: Dashboard + CMD Logger + Attacker Console + KMS

## Architecture

```
┌────────────────────────┐     ┌──────────────────┐
│   Bank Dashboard       │────▶│   KMS Server     │
│   (Streamlit)          │     │   (FastAPI)       │
│   Port 8501            │     │   Port 8000       │
└────────────────────────┘     │                   │
                               │  ┌─────────────┐  │
┌────────────────────────┐     │  │ BB84 Engine  │  │
│   CMD Logger           │◀═══╣  │ (Qiskit/Aer) │  │
│   (WebSocket client)   │ WS │  └─────────────┘  │
└────────────────────────┘     │  ┌─────────────┐  │
                               │  │ Escalation   │  │
┌────────────────────────┐     │  │ FSM (L1-L4)  │  │
│   Attacker Console     │────▶│  └─────────────┘  │
│   (Rich TUI)           │     └──────────────────┘
└────────────────────────┘
```

## File Layout

| File | Purpose |
|------|---------|
| `quantum_engine/bb84_simulator.py` | **Real Qiskit BB84** — per-qubit circuits on AerSimulator |
| `kms/key_management_service.py` | KMS core: sessions, escalation FSM, privacy amplification |
| `kms_server.py` | FastAPI server + WebSocket event bus + status UI |
| `kms/kms_server.py` | Module-style KMS server (alternative entry point) |
| `dashboard/dashboard_ui.py` | Streamlit banking dashboard with Plotly QBER chart |
| `logger/cmd_logger.py` | Real-time CMD event logger (WebSocket client) |
| `attacker_console.py` | Interactive attacker menu for demo judges |
| `gateway/network_gateway.py` | Zero-knowledge message routing gateway |
| `devices/client.py` | Device client with AES-256-GCM encrypt/decrypt |
| `run_demo.bat` | One-click Windows demo launcher |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify Qiskit works
python quantum_engine/bb84_simulator.py
# Should print: ALL BB84 CHECKS PASSED ✓
```

## Run the Demo

### One-Click Launch (Windows)
```bash
run_demo.bat
```
This opens 4 terminal windows: KMS Server, CMD Logger, Dashboard, Attacker Console.

### Manual Launch
```bash
# Terminal 1: KMS Server
python kms_server.py

# Terminal 2: CMD Logger
python logger/cmd_logger.py

# Terminal 3: Dashboard
streamlit run dashboard/dashboard_ui.py --server.port 8501

# Terminal 4: Attacker Console
python attacker_console.py
```

### URLs
- **Dashboard:** http://localhost:8501
- **KMS Status:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Demo Sequence

1. **Normal operation** — Create sessions in the dashboard sidebar. QBER stays low (~2%). All GREEN.
2. **Single attack** — In the Attacker Console, press `[1]`. QBER spikes to ~25%. Key refused.
3. **Port exhaustion** — Press `[2]`. Watch L1 port rotation exhaust all 7 ports → L2 IP failover.
4. **Full lockdown** — Press `[3]`. Escalation cascades L1→L2→L3→L4. Watch CMD Logger and Dashboard react in real-time.
5. **Reset** — Press `[4]`. System returns to GREEN.

## Escalation Ladder

| Level | Trigger | Action |
|-------|---------|--------|
| L1 — SAFE | QBER ≥ 11% | Burn port, rotate to next |
| L2 — TACTICAL RETREAT | All ports burned | Switch IP (192.168.1.100 → .150) |
| L3 — EMERGENCY | All IPs burned | Switch network (192.168.1.x → 2.x) |
| L4 — LOCKDOWN | All networks burned | Full stop, manual intervention |

## Security Stack

- **QKD:** BB84 via Qiskit QuantumCircuit + AerSimulator
- **Privacy Amplification:** Toeplitz matrix hashing (information-theoretic)
- **Key Derivation:** HKDF-SHA256
- **Encryption:** AES-256-GCM (authenticated encryption)
- **CSPRNG:** Python `secrets` module (not `random`)
- **QBER Threshold:** 11% (information-theoretic bound)
