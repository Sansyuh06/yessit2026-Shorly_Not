# MODEL.md — ShorlyNot-QDS-T1 Mathematical Model

**Normative Specification**  
**Profile**: ShorlyNot-QDS-T1 (Teleportation Profile T1, MVP)  
**Problem Statement**: SIH 2026 PS 26141 — Quantum-Inspired Cyber Threat Detection for Digital Signature Security

---

## 1. Protocol Identity & Scientific Literature

**ShorlyNot-QDS-T1** is an explicit software-simulated realization of a teleportation-assisted Quantum Digital Signature verification pathway.

### Foundational References
1. **Gottesman & Chuang**, *Quantum Digital Signatures*, arXiv:quant-ph/0105032.
2. **Bennett et al.**, *Teleporting an unknown quantum state via dual classical and Einstein-Podolsky-Rosen channels*, Phys. Rev. Lett. 70, 1895 (1993).
3. **Wallden, Dunjko, Kent, Andersson**, *Quantum digital signatures with quantum-key-distribution components*, Phys. Rev. A 91, 042304 (2015) / arXiv:1403.5551.
4. **Dunjko, Wallden, Andersson**, *Quantum digital signatures without quantum memory*, Phys. Rev. Lett. 112, 040502 (2014).
5. **Flammia & Liu**, *Direct Fidelity Estimation from Few Pauli Measurements*, Phys. Rev. Lett. 106, 230501 (2011) / arXiv:1104.4695.
6. **Shor & Preskill**, *Simple Proof of Security of the BB84 Quantum Key Distribution Protocol*, Phys. Rev. Lett. 85, 441 (2000).

---

## 2. Cryptographic Parties (Two-Party MVP)
- **Alice**: Signer (prepares quantum state $|\psi\rangle$, performs Bell-state measurement with entangled resource, outputs classical signature transcript).
- **Bob**: Verifier (receives entangled half, applies Pauli corrections, executes projective basis measurements, computes sample mismatch rate $\hat{p}$, verifies against statistical threshold $\tau$).

*(Three-party arbiter Trent / Lu et al. controlled teleportation is designated as profile T2-AQS for future expansion).*

---

## 3. Pauli Eigenstate Preparation Table

Let payload bit be $b \in \{0, 1\}$ and basis choice be $\beta \in \{0, 1\}$:

$$\begin{aligned}
|0\rangle_Z &= \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \quad |1\rangle_Z = \begin{pmatrix} 0 \\ 1 \end{pmatrix} \\
|+\rangle_X &= \frac{|0\rangle + |1\rangle}{\sqrt{2}} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix}, \quad |-\rangle_X = \frac{|0\rangle - |1\rangle}{\sqrt{2}} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ -1 \end{pmatrix}
\end{aligned}$$

| Bit $b$ | Basis $\beta$ | Prepared Quantum State $|\psi\rangle$ | Density Matrix $\rho$ |
|---|---|---|---|
| 0 | 0 ($Z$) | $|0\rangle$ | $|0\rangle\langle 0| = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}$ |
| 1 | 0 ($Z$) | $|1\rangle$ | $|1\rangle\langle 1| = \begin{pmatrix} 0 & 0 \\ 0 & 1 \end{pmatrix}$ |
| 0 | 1 ($X$) | $|+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$ | $|+\rangle\langle +| = \frac{1}{2}\begin{pmatrix} 1 & 1 \\ 1 & 1 \end{pmatrix}$ |
| 1 | 1 ($X$) | $|-\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$ | $|-\rangle\langle -| = \frac{1}{2}\begin{pmatrix} 1 & -1 \\ -1 & 1 \end{pmatrix}$ |

---

## 4. Quantum Entangled Resource

Alice and Bob share maximally entangled EPR Bell pairs $|\Phi^+\rangle$:

$$|\Phi^+\rangle_{AB} = \frac{1}{\sqrt{2}}\left(|00\rangle_{AB} + |11\rangle_{AB}\right)$$

In tensor product notation with message qubit $M$ in state $|\psi\rangle = \alpha |0\rangle + \beta |1\rangle$:

$$|\Psi\rangle_{MAB} = |\psi\rangle_M \otimes |\Phi^+\rangle_{AB} = \frac{1}{2}\left[ |\Phi^+\rangle_{MA} (I|\psi\rangle_B) + |\Phi^-\rangle_{MA} (Z|\psi\rangle_B) + |\Psi^+\rangle_{MA} (X|\psi\rangle_B) + |\Psi^-\rangle_{MA} (XZ|\psi\rangle_B) \right]$$

where:
$$\begin{aligned}
|\Phi^+\rangle &= \frac{|00\rangle + |11\rangle}{\sqrt{2}} \implies \text{Syndrome } (m_1=0, m_2=0) \\
|\Psi^+\rangle &= \frac{|01\rangle + |10\rangle}{\sqrt{2}} \implies \text{Syndrome } (m_1=0, m_2=1) \\
|\Phi^-\rangle &= \frac{|00\rangle - |11\rangle}{\sqrt{2}} \implies \text{Syndrome } (m_1=1, m_2=0) \\
|\Psi^-\rangle &= \frac{|01\rangle - |10\rangle}{\sqrt{2}} \implies \text{Syndrome } (m_1=1, m_2=1)
\end{aligned}$$

---

## 5. Pauli Correction Lookup

When Alice projects qubits $(M, A)$ onto the Bell basis, Bob's qubit $B$ collapses into $U_{(m_1, m_2)}^\dagger |\psi\rangle$. Bob recovers $|\psi\rangle$ by applying unitary $U_{(m_1, m_2)}$:

$$\begin{aligned}
I &= \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \\
X &= \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} \\
Z &= \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix} \\
XZ &= X \cdot Z = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix} \equiv -iY
\end{aligned}$$

| Alice Measurement $(m_1, m_2)$ | Bob State Before Correction | Required Bob Unitary $U$ | State After Correction |
|---|---|---|---|
| `00` | $|\psi\rangle$ | $I$ | $|\psi\rangle$ |
| `01` | $X|\psi\rangle$ | $X$ | $X^2|\psi\rangle = |\psi\rangle$ |
| `10` | $Z|\psi\rangle$ | $Z$ | $Z^2|\psi\rangle = |\psi\rangle$ |
| `11` | $ZX|\psi\rangle$ | $XZ$ | $(XZ)(ZX)|\psi\rangle = |\psi\rangle$ |

---

## 6. Projective Verification & Mismatch Statistic

1. For each verification position $i \in \{1, \dots, n\}$, Bob applies unitary correction $U_{(m_1^{(i)}, m_2^{(i)})}$.
2. If basis $\beta_i = 1$ ($X$ basis), Bob applies Hadamard transformation:
$$H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$
3. Bob performs standard computational projection onto $\{|0\rangle, |1\rangle\}$, recording measurement bit $b_i'$.
4. Let mismatch indicator $X_i = \mathbb{I}(b_i' \ne b_i) \in \{0, 1\}$.
5. The empirical mismatch rate is:
$$\hat{p} = \frac{1}{n}\sum_{i=1}^n X_i$$

---

## 7. Hoeffding Threshold $\tau$ Derivation

Under honest channel and simulator noise, $X_i$ are independent Bernoulli random variables with $\mathbb{E}[X_i] \le p_0$.

By **Hoeffding's Inequality**, for any deviation threshold $t > 0$:
$$\Pr\left(\hat{p} - p_0 \ge t\right) \le \exp\left(-2nt^2\right)$$

To bound the false rejection rate (honest signature rejected) by a preset security budget $\delta$:
$$\exp\left(-2nt^2\right) \le \delta \implies -2nt^2 \le \ln(\delta) \implies t \ge \sqrt{\frac{\ln(1/\delta)}{2n}}$$

Therefore, the exact statistical acceptance threshold $\tau$ is:
$$\tau = p_0 + \sqrt{\frac{\ln(1/\delta)}{2n}}$$

A signature is accepted if and only if $\hat{p} \le \tau$.

### Presets ($p_0 = 0.02, n = 64$)
1. **Normal ($\delta = 0.01$)**:
$$t = \sqrt{\frac{\ln(100)}{128}} = \sqrt{\frac{4.60517}{128}} \approx 0.18967 \implies \tau \approx 0.02 + 0.1897 = \mathbf{0.2097 \approx 0.210}$$
2. **Strict ($\delta = 0.001$)**:
$$t = \sqrt{\frac{\ln(1000)}{128}} = \sqrt{\frac{6.90775}{128}} \approx 0.2323 \implies \tau \approx 0.02 + 0.2323 = \mathbf{0.2523 \approx 0.233}$$
3. **Lenient ($\delta = 0.05$)**:
$$t = \sqrt{\frac{\ln(20)}{128}} = \sqrt{\frac{2.99573}{128}} \approx 0.1530 \implies \tau \approx 0.02 + 0.1530 = \mathbf{0.1730 \approx 0.168}$$

---

## 8. Forgery Probability Model (Random Transcript Guessing)

An unentangled adversary without Alice's keys or quantum channel guessing Pauli correction bits or states faces a binomial distribution of independent measurement outcomes with success probability per check $q \approx 1/2$.

The random forgery acceptance probability is:
$$P_{\text{forge, random}} = \sum_{k=0}^{\lfloor \tau n \rfloor} \binom{n}{k} \left(\frac{1}{2}\right)^n = I_{1/2}(n - \lfloor \tau n \rfloor, \lfloor \tau n \rfloor + 1)$$

For $n=64, \tau=0.210 \implies \lfloor \tau n \rfloor = 13$:
$$P_{\text{forge}} \approx \sum_{k=0}^{13} \binom{64}{k} \left(\frac{1}{2}\right)^{64} \approx 2.4 \times 10^{-6}$$

As $n$ increases to 128:
$$P_{\text{forge}} < 10^{-11}$$

This exponential suppression guarantees Information-Theoretic Security bounds in the stated model without any machine learning heuristics.

---

## 9. Non-ML Threat Engine (Q-STDF) Ladder

```
[Received SignatureBundle & Verification Request]
                       │
       1. Is Verifier Authorized?
             ├─ No  ───> [UNAUTH_VERIFY]
             └─ Yes ───> 2. Is key_id bound to Signer?
                               ├─ No  ───> [IMPERSONATION]
                               └─ Yes ───> 3. Is Nonce unique/unseen?
                                                 ├─ No  ───> [REPLAY]
                                                 └─ Yes ───> 4. Does PQC Unprotect succeed?
                                                                   ├─ No  ───> [CHANNEL]
                                                                   └─ Yes ───> 5. Compute mismatch p̂
                                                                                     ├─ p̂ > τ ───> [FORGERY]
                                                                                     └─ p̂ ≤ τ ───> [OK]
```
