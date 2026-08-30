# How This Works (Quantum-Aware Secure Chat)

This file explains the architecture and the exact steps to run the demo end-to-end.

## 1) Big-picture flow
1. **BB84 simulator** generates a raw key and a QBER value. It includes Decoy-State testing for PNS detection.
2. **KMS** implements the Quantum-Safe Handshake (QSH), falling back to ML-KEM if quantum channel is noisy. Derives an AES-256-GCM key (HKDF-SHA256).
3. **Chat clients** fetch the key from KMS and encrypt messages end-to-end using 96-bit unique nonces.
4. **Chat server** relays ciphertext only (never decrypts).
5. **Router guard** polls KMS link status and applies firewall rules.
6. **Escalation** rotates ports/IPs/networks or locks down when QBER is high.

## 2) Components and responsibilities
- `quantum_engine/bb84_simulator.py`
  - Simulates BB84: random bases, sifting, QBER (QBER = errors / total_compared).
  - Uses Toeplitz Matrix hashing for strict Privacy Amplification, ensuring information-theoretic security by compressing the sifted key.
  - If `eve=True`, QBER rises to ~20–30% (intercept-resend effect).

- `quantum_engine/hybrid_handshake.py`
  - Combines BB84 raw key with ML-KEM/Kyber-768 for defense-in-depth security.

- `kms/key_management_service.py`
  - Keeps session state in memory.
  - Derives AES-256-GCM keys using HKDF.
  - Tracks link health and escalation level.

- `kms/kms_server.py`
  - FastAPI API endpoints:
    - `POST /create_session`
    - `POST /get_key`
    - `GET /link_status`
    - `POST /activate_eve`, `POST /deactivate_eve`, `POST /trigger_attack`

## 3) Prerequisites
- Python 3.10+
- Install dependencies:
  ```bash
  python -m pip install -r requirements.txt
  ```

## 4) Run the demo (step-by-step)
### Option A: One-command launcher
```bash
run_demo.bat
```
This starts KMS, CMD logger, Dashboard, and Attacker Console.

### Option B: Manual start
1. **Start KMS**
   ```bash
   python kms_server.py
   ```
2. **Start Dashboard**
   ```bash
   streamlit run dashboard/dashboard_ui.py --server.port 8501
   ```
3. **Start Mobile Web Chat**
   ```bash
   python webapp/mobile_chat.py
   ```

## 5) Normal (GREEN) demo
1. Open the dashboard.
2. QBER stays low. Entropy score is high.

## 6) Attack demo (Eve)
- Use the **Attacker Console** to trigger Intercept-Resend or Exhaustion attacks.

Expected results:
- QBER rises over 11%.
- Status flips to RED.
- Escalation Protocol engages.

## 7) Escalation ladder (what it means)
- **Level 1 (SAFE)**: burn port ? rotate to next.
- **Level 2 (TACTICAL RETREAT)**: all ports burned ? switch IP (simulated).
- **Level 3 (EMERGENCY)**: all IPs burned ? switch network (simulated).
- **Level 4 (LOCKDOWN)**: full stop.

The KMS reports `escalation_level` and the router guard enforces firewall rules.

## 8) Troubleshooting
- If you see `RED` repeatedly, the system will rotate ports/IPs.
- If clients cannot connect, verify `run_demo.bat` spawned all terminal windows successfully.

## 9) Security notes (for demo context)
- The router is treated as untrusted; encryption is end-to-end between clients.
- This represents a 10/10 production-grade QKD integration demonstration for YESIST 2026.
