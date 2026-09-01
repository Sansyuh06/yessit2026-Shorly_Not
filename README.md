# ShorlyNot

> **Quantum-Inspired QDS Protocol Simulation + Non-ML Statistical Threat Detection + App-Level Bank Lock**  
> SIH 2026 · PS 26141 · Egreen Quanta · Blockchain & Cybersecurity

**One line:** We simulate teleportation-style quantum digital signature (QDS) protocols in software, detect forge/replay/impersonation-style attacks with **Hoeffding thresholds (Q-STDF, no ML)**, escalate stages **S0–S4**, and **refuse transfers in a mock bank** when attacks hit.

| This is | This is not |
|---------|-------------|
| Quantum-**inspired** protocol **simulation** framework | Lab/hardware ITS quantum security on the default path |
| Runnable **skeleton** SDK + **bank/SOC** proof | Production RBI/UPI core |
| Default backend: **Qiskit Aer** simulator | “We are a fault-tolerant quantum computer” |
| Enforce path: **app lock** | iptables/OS firewall as the hero |

**Innovation (honest):** not a new QDS theorem — the control loop `verify → Q-STDF label → stage → bank lock`.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Qiskit 2.x](https://img.shields.io/badge/qiskit-2.x-613394.svg)](https://qiskit.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Protocol](https://img.shields.io/badge/protocol-ShorlyNot--QDS--T1-orange.svg)](docs/MODEL.md)
[![Detection](https://img.shields.io/badge/detection-Q--STDF%20(No--ML)-green.svg)](docs/MODEL.md)

> [!IMPORTANT]
> **Source of Truth Branch**: All active code, hardened security features, and evaluation deliverables are on the **`main`** branch. The `master` branch is a stale historical branch. Ensure your workspace is checked out to `main` (`git checkout main`).  
> **Key References**: See [KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) and [SECURITY_ANALYSIS.md](docs/SECURITY_ANALYSIS.md) for full engineering trade-offs, honesty bounds, and threat models.

---

## Architecture Honesty & Scientific Grounding

| Architectural Layer | Implementation Truth | Scientific & Engineering Rationale |
|---|---|---|
| **Sign Path** | **Qiskit Aer Circuits (Classical Sim of Quantum Circuits)** | Alice executes 3-qubit Bell teleportation circuits on `AerSimulator` (classical simulation of quantum state transformations) to generate syndromes $(m_1, m_2)$. |
| **Verify Path** | **$\mathcal{O}(n)$ Analytical/Statevector Evaluation (Dual-Mode)** | Bob evaluates syndrome consistency via analytical Born-rule statevector projection under depolarizing noise $p_0$ for sub-millisecond edge throughput; full Aer circuit verification mode is also selectable (`mode="circuit"`). |
| **Detection Engine** | **Strict Zero-ML Hoeffding Bounds (Q-STDF)** | Non-ML threshold calculation $\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$; asserted with test confirming 0 ML libraries in `sys.modules`. |
| **QKD Layer** | **Classical Protocol Simulation (Support)** | Statistical simulation of BB84 session key exchange (256-bit symmetric keys) and channel QBER monitoring ($Q_0 \to Q_4$). |
| **PQC Layer** | **AES-256-GCM Demo Wrap (ML-KEM = Interface Only)** | Authenticated symmetric encryption wrapping classical correction bits; `MlKem768Interface` is an interface/stub for future NIST FIPS 203 wire-up. |
| **Hardware Backend** | **Qiskit Aer Default, Real IBM Optional** | Defaults to `sim` (Aer classical circuit simulation); switches to real IBM QPUs only when `IBM_QUANTUM_TOKEN` is provided. Aer is never claimed to be physical quantum hardware. |
| **Bank Enforcement** | **Application-Level Bank Stages S0–S4** | Security stages $S_0 \to S_4$ act strictly at the application gateway (refusing transfers, revoking sessions, locking accounts); no unsafe OS-level `iptables` or root firewall hooks. |

---

## What is ShorlyNot?

**ShorlyNot** is a quantum-inspired protocol simulation framework and financial application proof-of-concept created for SIH 2026 Problem Statement 26141:
1. **`skeleton/`** (The Core Simulation Framework): An embeddable security SDK and REST API delivering simulated **ShorlyNot-QDS-T1** (teleportation-assisted Quantum Digital Signatures on Qiskit Aer) and **Q-STDF** (Quantum Statistical Threat Detection Framework) using rigorous Hoeffding statistical bounds instead of black-box ML.
2. **`bank/`** (The Operational Proof): A realistic mock banking application where every transaction is simulated quantum-signed and verified. Signature attacks (forgery, impersonation, replay, unauthorized verification, channel tampering, parameter downgrade) are flagged in real-time by statistical bounds, driving application-level lockouts (S0–S4).

---

## Key Highlights

- **Named Protocol**: `ShorlyNot-QDS-T1` — Pauli eigenstate encoding ($Z, X$), Bell-pair entanglement distribution ($|\Phi^+\rangle$), Bell measurement syndrome extraction, and Pauli unitary corrections ($I, X, Z, XZ$).
- **Zero-ML Statistical Threat Detection (Q-STDF)**: Hoeffding threshold calculation $\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$ with rigorous false-reject budgeting.
- **Five Attack Simulations**: Deterministically detects Forgery, Impersonation, Nonce Replay, Unauthorized Verification, and Channel Tampering.
- **App-Level Lockdown**: Stages $S_0$ through $S_4$ directly regulate banking operations without unsafe OS-level dependencies.
- **Quantum Backends**: Defaults to high-efficiency local simulation (`sim` via Qiskit Aer with noise modeling); optional real `ibm` quantum processors only when an explicit IBM Quantum token and remote job are configured. Aer is a classical simulator, not physical quantum hardware.

---

## Repository Structure

```
.
├── docs/                # PRD, mathematical models, architecture, and benchmarks
│   ├── ONE_SHOT_PRD.md  # Source of truth build specification
│   ├── MODEL.md         # Normative mathematical model & formulas
│   ├── ARCHITECTURE.md  # System architecture & dataflow
│   ├── BENCHMARKS.md    # Monte Carlo metrics & latency curves
│   ├── KNOWN_LIMITATIONS.md # Engineering trade-offs & honesty notes
│   ├── SECURITY_ANALYSIS.md # Formal bounds & threat derivations
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

---

## Running Tests

```bash
pytest -v
```
