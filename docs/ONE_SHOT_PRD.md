# SHORLYNOT — PRD SPECIFICATION
### SIH 2026 · PS 26141 · Complete Build Spec (Single Document)

| Field | Value |
|---|---|
| Product | ShorlyNot |
| PS ID | 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security |
| Org / Theme | Egreen Quanta · Blockchain & Cybersecurity · Software |
| Version | v3.0 (Final) |
| Date | 2026-08-30 |

---

## 1. WHAT WE ARE BUILDING

### 1.1 One Sentence
**ShorlyNot** is (1) a quantum security skeleton framework that performs teleportation-based Quantum Digital Signatures (**ShorlyNot-QDS-T1**) with non-ML statistical threshold threat detection (**Q-STDF**), supported by QKD and PQC layers; and (2) a high-fidelity mock bank application built on that skeleton where every transaction is quantum-signed, signature attacks are instantly detected via Hoeffding statistical bounds, and the bank enters application-level lockdown.

### 1.2 Exactly Two Products
- `skeleton/`: **THE FRAMEWORK** (The core invention) — embeddable quantum security SDK and FastAPI microservice.
- `bank/`: **THE APP** (The operational proof) — mock bank portal + real-time dark SOC console, consuming the skeleton.
- `legacy/`: Historical parts bin and exploration archives (not advertised as a product).
- `docs/`: Formal specifications, mathematical foundations, and architecture.

#### Hard Rules
1. **Bank never reimplements crypto/detection**: Bank is a pure consumer of the skeleton framework.
2. **Quantum is always on for transfers**: Backend switches between simulation (`sim`) and real quantum hardware (`ibm`).
3. **Lockdown is app-level**: Governed by security stages S0–S4; zero reliance on iptables or kernel hooks.
4. **Zero AI/ML for detection**: Pure Hoeffding statistical bounding $\tau$ and deterministic protocol verification.
5. **QDS is the hero**: Pauli eigenstate encoding, Bell teleportation measurements, and projective verification. Ed25519 is not used as the digital signature for this PS.

---

## 2. NORTH STAR (FIT TEST)
> Show a digital signature forged or replayed $\rightarrow$ caught by quantum measurement / threshold logic $\rightarrow$ bank refuses service — in **under 2 minutes**.

---

## 3. PROTOCOL SPECIFICATION: ShorlyNot-QDS-T1

### 3.1 Mathematical Foundation
- Gottesman & Chuang (arXiv:quant-ph/0105032) — Quantum Digital Signatures
- Bennett et al. (PRL 70, 1895, 1993) — Teleportation & Pauli Corrections
- Wallden, Dunjko, Kent, Andersson (PRA 91, 042304, 2015) — QDS with QKD components
- Flammia & Liu (arXiv:1104.4695) — Pauli measurement statistics

### 3.2 Pauli Eigenstate Encoding
| Bit $b$ | Basis $\beta$ | Prepared State $|\psi\rangle$ | Bloch Label |
|---|---|---|---|
| 0 | 0 ($Z$) | $\|0\rangle$ | Computational $\|0\rangle$ |
| 1 | 0 ($Z$) | $\|1\rangle$ | Computational $\|1\rangle$ |
| 0 | 1 ($X$) | $\|+\rangle = (\|0\rangle + \|1\rangle)/\sqrt{2}$ | Diagonal $\|+\rangle$ |
| 1 | 1 ($X$) | $\|-\rangle = (\|0\rangle - \|1\rangle)/\sqrt{2}$ | Diagonal $\|-\rangle$ |

### 3.3 Bell State Resource
$$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$$

### 3.4 Teleportation-Based Signing Procedure
For each bit index $i \in \{1, \dots, L\}$:
1. Alice prepares state $|\psi_i\rangle$ according to payload-derived bit $b_i$ and basis $\beta_i$.
2. Alice shares Bell state $|\Phi^+\rangle_{AB}$ with Bob.
3. Alice performs a Bell-basis measurement on $(\text{Message} \otimes A)$.
4. Measurement yields classical syndrome $(m_1, m_2) \in \{00, 01, 10, 11\}$.
5. Bob's state collapses to $U_{(m_1, m_2)} |\psi_i\rangle$.
6. Alice records $(m_1, m_2)$, $\beta_i$, canonical payload hash, nonce, and key ID in the `SignatureBundle`.

### 3.5 Pauli Correction Table
| Measurement $(m_1, m_2)$ | Required Unitary Correction $U$ on Bob's Qubit |
|---|---|
| `00` | $I$ (Identity) |
| `01` | $X$ (Bit Flip) |
| `10` | $Z$ (Phase Flip) |
| `11` | $XZ$ (Bit & Phase Flip $\equiv -iY$) |

### 3.6 Projective Verification Procedure
For each check position $i \in \{1, \dots, n\}$:
1. Bob unprotects classical correction bits using PQC/AES-GCM session key.
2. Bob applies unitary correction $U_{(m_1, m_2)}$ to his state.
3. If basis $\beta_i = 1$ ($X$ basis), Bob applies Hadamard gate $H$.
4. Bob performs projective measurement in the computational $Z$ basis, yielding $b_i'$.
5. Check failure (mismatch) occurs if $b_i' \ne b_i$.
6. Calculate mismatch rate:
$$\hat{p} = \frac{\sum_{i=1}^n \mathbb{I}(b_i' \ne b_i)}{n}$$
7. Signature is candidate accepted if $\hat{p} \le \tau$ and classical protocol binding passes.

### 3.7 Hoeffding Threshold $\tau$ (Reference Derivation)
Under honest noise floor $p_0$, the probability of false rejection is bounded by Hoeffding's inequality:
$$\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$$

| Preset | Target False Reject $\delta$ | Check Positions $n$ | Noise Floor $p_0$ | Acceptance Threshold $\tau$ |
|---|---|---|---|---|
| `strict` | 0.001 | 64 | 0.02 | $\approx 0.252$ |
| `normal` | 0.01 | 64 | 0.02 | $\approx 0.210$ |
| `lenient` | 0.05 | 64 | 0.02 | $\approx 0.173$ |

---

## 4. THREAT DETECTION ENGINE: Q-STDF

### 4.1 Decision Ladder (Strict Evaluation Order)
```
1. Verify Authorization Entitlement? ──No──> UNAUTH_VERIFY
2. Signer key_id binding valid?     ──No──> IMPERSONATION
3. Nonce unseen (not in cache)?     ──No──> REPLAY
4. PQC unprotect/syndrome valid?    ──No──> CHANNEL
5. Mismatch rate p̂ ≤ τ?             ──No──> FORGERY
6. All checks passed?               ──Yes─> OK
```

### 4.2 Security Stages
- **Signature Threat Stages ($S_0 - S_4$)**:
  - **$S_0$**: Normal operation (All transactions permitted)
  - **$S_1$**: Soft anomaly / warning logged to SOC
  - **$S_2$**: Forgery or Impersonation detected $\rightarrow$ New transfers suspended
  - **$S_3$**: Replay or repeated unauthorized attempts $\rightarrow$ Read-only history, session reset
  - **$S_4$**: Channel attack storm / critical threshold exceeded $\rightarrow$ Full application lockdown
- **QKD Link Stages ($Q_0 - Q_4$)**:
  - $Q_0$: $\text{QBER} < 5\%$ (Healthy)
  - $Q_1$: $5\% \le \text{QBER} < 8\%$ (Elevated noise)
  - $Q_2$: $8\% \le \text{QBER} < 11\%$ (Warning)
  - $Q_3$: $11\% \le \text{QBER} < 20\%$ (Link compromised)
  - $Q_4$: $\text{QBER} \ge 20\%$ (Eve interception alert)

---

## 5. REPO & API ARCHITECTURE
- Skeleton API runs on `http://127.0.0.1:8000` with OpenAPI documentation at `/docs`.
- Bank Web App runs on `http://127.0.0.1:8080` and SOC console at `/soc`.
- Interactive attack suite triggers real-time responses and stage updates.
