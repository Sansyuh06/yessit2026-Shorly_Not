# 🛡️ ShorlyNot
### Quantum-safe communication, secured by physics — not math.

> **Winner/Finalist at YESIST 2026** — [Watch the 2-min demo →](https://youtube.com/...)

---

**The problem:** Quantum computers will break RSA/ECC within this decade. 
Every encrypted message sent today could be decrypted tomorrow. This is 
called "harvest now, decrypt later" — and it's already happening.

**Our solution:** ShorlyNot uses **real BB84 Quantum Key Distribution** 
(QKD) on Qiskit to generate encryption keys secured by the laws of physics. 
If anyone eavesdrops, quantum mechanics guarantees we detect it. No assumptions 
about computational hardness. No trust in math. Just physics.

## What makes this different from other QKD demos?

| Feature | Toy Demos | ShorlyNot |
|---------|-----------|-------------------|
| Qubit simulation | `random.randint()` | Real Qiskit `QuantumCircuit` on `AerSimulator` |
| QBER | Hardcoded ~25% | Emerges from quantum measurement statistics |
| Privacy amplification | ❌ Missing | ✅ Toeplitz matrix hashing (IEEE, Bennett 1995) |
| Key derivation | None | HKDF-SHA256 (RFC 5869) |
| Encryption | XOR | AES-256-GCM authenticated encryption |
| Hybrid PQC | ❌ | ✅ BB84 + ML-KEM fallback (novel QSH protocol) |
| Attack response | Print statement | 4-level escalation FSM with port/IP/network rotation |
| Live monitoring | ❌ | ✅ WebSocket event bus + Streamlit dashboard |
| Cross-device | ❌ | ✅ Mobile web chat on phones |
| Physical indicator | ❌ | ✅ USB LED showing real-time quantum link health |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Verify quantum engine
python quantum_engine/bb84_simulator.py
# Expected: ALL BB84 CHECKS PASSED ✓

# Run the demo (opens 4 windows)
./run_demo.bat          # Windows
python start_all.py     # Linux/Mac
```

## 📐 Architecture
```text
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

## 📄 Paper & Research
[Read the full paper (PDF)](#)

## 🎬 Demo Video
[Demo Video Placeholder](https://youtube.com/...)

## 📸 Screenshots
See `screenshots/` directory for full-res images.

## 🧪 Running Tests
```bash
# Full test suite
python -m pytest tests/ -v

# Statistical validation (runs 50 BB84 sessions)
python -m pytest tests/test_bb84_statistics.py -v

# Security tests
python -m pytest tests/test_kms_security.py -v

# Benchmarks
python benchmarks/run_benchmarks.py
```

## 🏗️ Built With
- **Qiskit** — Quantum circuit simulation
- **FastAPI** — KMS server + WebSocket
- **Streamlit** — Real-time dashboard
- **cryptography** — AES-256-GCM + HKDF
- **Rich** — Terminal UI

## 📚 Research & Standards
| Reference | What It Proves |
|-----------|----------------|
| Bennett & Brassard 1984 | BB84 protocol design |
| Shor & Preskill 2000 (arXiv) | 11% QBER security bound |
| Tomamichel et al. 2011 (arXiv) | Finite-key security analysis |
| Bennett et al. 1995 (IEEE TIT) | Privacy amplification via universal hashing |
| Hwang 2003 (arXiv) | Decoy-state PNS detection |
| RFC 5869 | HKDF key derivation |
| RFC 5116 | AES-GCM authenticated encryption |
| NIST SP 800-56C | Key derivation standards |
| NIST FIPS 203 | ML-KEM (Kyber) post-quantum standard |

## 👥 Team
| Name | Role |
|------|------|
| Akash Santhnu Sundar | Quantum Engine + KMS |
| Partner Name | Dashboard + Networking |

## License
MIT © 2026 ShorlyNot Team
