# KNOWN_LIMITATIONS.md — ShorlyNot Framework & App Scope

**SIH 2026 Problem Statement 26141**  
**Classification**: Engineering Trade-Offs, Assumptions & Limitations  

---

## 1. Global Gateway Stage Lock vs. Per-Account Lockdown

- **Current Architecture**: The `StageStateMachine` operates as a central financial transaction gateway monitor. When critical quantum violations (e.g. channel compromise or active forgery) are intercepted, the system escalates the global stage ($S_0 \to S_4$), protecting all accounts connected to the gateway.
- **Rationale**: Replicates an enterprise banking SOC declaring an active cryptographic incident.
- **Future Scope**: Fine-grained per-account quarantine alongside global threshold escalations.

---

## 2. Real Circuit Signing vs. $\mathcal{O}(n)$ Statevector Verification

- **Sign Path**: Executes real 3-qubit Bell teleportation circuits on `AerSimulator` per check position to generate authentic Bell syndromes $(m_1, m_2)$.
- **Verify Path**: Uses single-qubit projective Born-rule statevector evaluation under depolarizing noise $p_0$.
- **Rationale**: Guarantees sub-millisecond edge router verification throughput ($< 1$ ms) required for real-time banking, while retaining full circuit semantics. Full Aer circuit mode is also selectable (`mode="circuit"`).

---

## 3. Two-Party Profile T1 Scope (Alice Signer, Bob Verifier)

- **Current Architecture**: Focuses on point-to-point payer-to-payee transaction authentication using shared Bell pairs and Pauli corrections.
- **Future Scope**: Three-party arbitrated signatures (Profile T2-AQS) with Trent arbiter or optical multiports for transferable non-repudiation.

---

## 4. PQC Layer (AES-256-GCM Demo Wrap with ML-KEM Interface)

- **Current Architecture**: Classical Pauli correction bits are encrypted via AES-256-GCM using 256-bit symmetric session keys derived from the BB84 QKD link layer.
- **ML-KEM Interface**: Provided as `MlKem768Interface` in `pqc/kem_interface.py` to allow drop-in replacement with NIST FIPS 203 ML-KEM packages when available.

---

## 5. Hardware Backends (Qiskit Aer Default, IBM Quantum Optional)

- **Default Engine**: High-fidelity local simulation on Qiskit Aer (`backend="sim"`).
- **IBM Quantum**: Switches gracefully to real IBM QPUs only when `IBM_QUANTUM_TOKEN` is present. Never fakes IBM hardware output.

---

## 6. Demonstration Authentication & Session Management

- **Demo Auth**: Accounts (`alice`, `bob`, `carol`, `eve`, `ops`) are pre-seeded in RAM with initial balances for clean, repeatable demo resets.
- **Persistence**: All executed transfers and security telemetry are persisted to SQLite (`bank_ledger.db`). Production systems would replace this with hardware-backed KMS/OAuth2.
