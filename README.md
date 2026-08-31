# ShorlyNot
### Quantum-Inspired Cyber Threat Detection for Digital Signature Security (SIH 2026 · PS 26141)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.x](https://img.shields.io/badge/qiskit-2.x-613394.svg)](https://qiskit.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Protocol](https://img.shields.io/badge/protocol-ShorlyNot--QDS--T1-orange.svg)](docs/MODEL.md)
[![Detection](https://img.shields.io/badge/detection-Q--STDF%20(No--ML)-green.svg)](docs/MODEL.md)

> [!IMPORTANT]
> **Source of Truth Branch**: All active code, hardened security features, and evaluation deliverables are on the **`main`** branch. The `master` branch is a stale historical branch. Ensure your workspace is checked out to `main` (`git checkout main`).

---

## What is ShorlyNot?

**ShorlyNot** is a quantum security software framework and financial application proof-of-concept created for SIH 2026 Problem Statement 26141:
1. **`skeleton/`** (The Core Framework): An embeddable security SDK and REST API delivering **ShorlyNot-QDS-T1** (teleportation-assisted Quantum Digital Signatures) and **Q-STDF** (Quantum Statistical Threat Detection Framework) using rigorous Hoeffding statistical bounds instead of black-box ML.
2. **`bank/`** (The Operational Proof): A realistic mock banking application where every transaction is quantum-signed and verified. Signature attacks (forgery, impersonation, replay, unauthorized verification, channel tampering, parameter downgrade) are flagged in real-time, driving application-level lockouts.

---

## Key Highlights

- **Named Protocol**: `ShorlyNot-QDS-T1` — Pauli eigenstate encoding ($Z, X$), Bell-pair entanglement distribution ($|\Phi^+\rangle$), Bell measurement syndrome extraction, and Pauli unitary corrections ($I, X, Z, XZ$).
- **Zero-ML Statistical Threat Detection (Q-STDF)**: Hoeffding threshold calculation $\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$ with rigorous false-reject budgeting.
- **Five Attack Simulations**: Deterministically detects Forgery, Impersonation, Nonce Replay, Unauthorized Verification, and Channel Tampering.
- **App-Level Lockdown**: Stages $S_0$ through $S_4$ directly regulate banking operations without unsafe OS-level dependencies.
- **Quantum Backends**: Defaults to high-efficiency `sim` (Qiskit Aer with noise modeling); seamlessly switches to real `ibm` quantum processors when an IBM Quantum token is provided.

---

## Repository Structure

```
.
├── docs/                # PRD, mathematical models, architecture, and benchmarks
│   ├── ONE_SHOT_PRD.md  # Source of truth build specification
│   ├── MODEL.md         # Normative mathematical model & formulas
│   ├── ARCHITECTURE.md  # System architecture & dataflow
│   ├── BENCHMARKS.md    # Monte Carlo metrics & latency curves
│   └── DEPLOY.md        # Demo script & deployment manual
├── skeleton/            # The Core Quantum Framework & Microservice
│   ├── src/shorlynot_skeleton/
│   │   ├── qds/         # ShorlyNot-QDS-T1 Bell teleportation & Pauli verification
│   │   ├── detect/      # Q-STDF non-ML threshold engine (tau.py & classifier.py)
│   │   ├── stages/      # S0-S4 (signature) and Q0-Q4 (QKD) stage state machine
│   │   ├── qkd/         # BB84 session key exchange & QBER monitoring
│   │   ├── pqc/         # AES-256-GCM / ML-KEM classical syndrome encapsulation
│   │   ├── attacks/     # 5 executable attack vectors
│   │   ├── backends/    # Sim (Aer) and IBM Quantum Runtime
│   │   ├── analysis/    # Monte Carlo P_forge & latency benchmarks
│   │   ├── api/         # FastAPI REST service (:8000)
│   │   └── pipeline.py  # Atomic transfer pipeline
│   └── tests/           # Unit & integration tests
├── bank/                # The Mock Bank Application (:8080)
│   ├── app/             # Web routes, auth, ledger, and skeleton client
│   ├── static/          # Custom styling & SOC live feed scripts
│   └── tests/           # Bank application tests
├── scripts/             # Startup scripts (run_demo.bat, run_demo.sh)
└── legacy/              # Archived research and historical prototypes
```

---

## Quick Start

### 1. Launch Everything (Windows)
```cmd
.\scripts\run_demo.bat
```

### 2. Launch Everything (Linux / macOS)
```bash
chmod +x ./scripts/run_demo.sh
./scripts/run_demo.sh
```

### 3. One-Shot Automated Attack & Defense Suite
```bash
./scripts/demo_attacks.sh
# or on Windows:
python scripts/demo_attacks.py
```

- **Bank Web Application**: [http://127.0.0.1:8080](http://127.0.0.1:8080) (Log in with `alice` / `alice123`)
- **Real-Time SOC Console**: [http://127.0.0.1:8080/soc](http://127.0.0.1:8080/soc)
- **Skeleton OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Architecture Honesty & Scientific Grounding

| Architectural Layer | Implementation Truth | Scientific & Engineering Rationale |
|---|---|---|
| **Sign Path** | **Real 3-Qubit Qiskit Aer Circuits** | Alice executes real Bell teleportation circuits on `AerSimulator` to generate authentic syndromes $(m_1, m_2)$. |
| **Verify Path** | **$\mathcal{O}(n)$ Born-Rule Statevector Evaluation** | Bob evaluates syndrome consistency via analytical Born-rule projection under depolarizing noise $p_0$, ensuring sub-millisecond edge verification complexity without heavy QPU simulation overhead. Full Aer circuit mode is also supported. |
| **Detection Engine** | **Strict Zero-ML Hoeffding Bounds** | Thresholds derived from $\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$; asserted with test asserting 0 ML libraries in `sys.modules`. |
| **QKD Layer** | **BB84 Statistical Simulation** | Support layer generating 256-bit symmetric session keys and tracking channel QBER ($Q_0 \to Q_4$). |
| **PQC Layer** | **AES-256-GCM Classical Wrapping** | Authenticated encryption protecting classical correction bits, with `MlKem768Interface` reference stub. |
| **Hardware Backend** | **Qiskit Aer Default, Real IBM When Available** | Defaults to `sim` (Aer); gracefully switches to real IBM QPUs only when `IBM_QUANTUM_TOKEN` is supplied. Never fakes IBM hardware. |
| **Bank Enforcement** | **App-Level Session & Transfer Lockout** | Security stages $S_0 \to S_4$ act at the application gateway; no unsafe OS-level `iptables` or root hooks. |

See [SECURITY_ANALYSIS.md](docs/SECURITY_ANALYSIS.md) and [DELIVERY_TABLE.md](docs/DELIVERY_TABLE.md) for full formal derivations and compliance mappings.

---

## Running Tests

```bash
pytest -v
```
