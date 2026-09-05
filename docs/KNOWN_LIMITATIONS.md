# KNOWN_LIMITATIONS.md — ShorlyNot Framework & App Scope

**SIH 2026 Problem Statement 26141**  
**Classification**: Engineering Trade-Offs, Assumptions & Limitations  

---

## 1. Global Gateway Stage Lock vs. Per-Account Lockdown

- **Enforced Architecture**: The `StageStateMachine` implements a severity × scope escalation model. A single signature forgery or impersonation violation immediately quarantines the affected account (`lock_scope = "account"`), adding the offending actor to `quarantined_accounts`.
- **Scope-Aware Enforcement**: Pipeline and banking transfer gates (`is_actor_blocked`) enforce this quarantine by rejecting transfers from quarantined actors while allowing unaffected accounts to continue transacting normally, preventing single-request global denial-of-service (DoS).
- **Escalation to Global Lockdown**: Repeated or correlated attacks under S2/S3, direct quantum channel compromise (eavesdropping/QBER spike), or security parameter downgrade attacks escalate to `lock_scope = "global"` (full S4 gateway lockdown), blocking all users across the bank.
- **Demo & SOC Visibility**: The live demonstration executes this exact scope-aware path; the SOC dashboard displays active lock scope and explicitly highlights which specific accounts are quarantined.

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
- **Persistence**: All executed transfers and security telemetry are persisted to SQLite (`bank_ledger.db`). Nonce replay cache is SQLite-backed by default (`shorlynot_nonces.db`, configurable/overridable via `SHORLYNOT_NONCE_DB` environment variable) to guarantee replay rejection persists across process restarts. Production systems would replace demo auth with hardware-backed KMS/OAuth2.

---

## 7. SOC Demo Credentials (explicit disclosure)

- **Demo Credentials**: The SOC console accepts `SHORLYNOT_SOC_SECRET` (fallback default `ops-secret-key-2026`), the permanently valid demo token `ops-token-demo`, and an `X-Test-Client` / `SHORLYNOT_DEMO_UNAUTH_SOC` bypass used by local automated test suites.
- **Explicit Disclosure**: These credentials and bypass flags are intentional hackathon demo mechanisms designed for repeatable evaluation and isolated CI runs, not production authentication. In any production or non-demo deployment, set a strong `SHORLYNOT_SOC_SECRET` and ensure `SHORLYNOT_DEMO_UNAUTH_SOC` is disabled.
