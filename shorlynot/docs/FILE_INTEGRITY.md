# File Integrity Guide

This document maps all backend source files in the ShorlyNot repository as required by PRD §34.

## Core Domain & Configuration

| File | Responsibility | Exports | Tests |
|------|----------------|---------|-------|
| `packages/common/enums.py` | Global enums | `ExecutionMode`, `QKDProtocol`, `PolicyState`, etc. | `test_core.py` |
| `packages/common/schemas.py` | Pydantic v2 domain schemas | `QuantumJobRead`, `QKDSessionRead`, `DeviceRead`, `QKBNLLeasePayload`, etc. | `test_core.py`, `test_integration.py` |
| `packages/common/database.py` | SQLAlchemy ORM Models | `Base`, `DeviceModel`, `QuantumJobModel`, `QKDSessionModel` | N/A |
| `packages/common/config.py` | pydantic-settings config | `ShorlyNotConfig` | N/A |
| `packages/common/evidence.py` | Evidence chain management | `EvidenceChain` | `test_core.py` |
| `packages/common/errors.py` | Typed application errors | `ShorlyNotError`, `InsufficientKeyMaterialError`, etc. | `test_core.py` |

## Quantum Engine (QKD & Channel)

| File | Responsibility | Exports | Tests |
|------|----------------|---------|-------|
| `packages/qkd/bb84.py` | BB84 Protocol | `run_bb84_protocol`, `build_bb84_circuits` | `test_core.py` |
| `packages/qkd/b92.py` | B92 Protocol | `run_b92_protocol`, `extract_conclusive_results` | `test_core.py` |
| `packages/qkd/e91.py` | E91 Protocol | `run_e91_protocol`, `calculate_chsh` | `test_core.py` |
| `packages/qkd/decoy.py` | Decoy-state BB84 | `run_decoy_bb84` | `test_core.py` |
| `packages/qkd/channel.py` | Channel models | `simulate_channel` | `test_core.py` |
| `packages/qkd/finite_key.py` | Finite-key bounds | `estimate_secure_key_length`, `qber_confidence_upper_bound` | `test_core.py` |
| `packages/qkd/reconciliation.py` | Cascade reconciliation | `cascade_reconciliation` | `test_core.py` |
| `packages/qkd/privacy_amplification.py` | PA and entropy | `privacy_amplification` | `test_core.py` |

## Cryptography & Policy

| File | Responsibility | Exports | Tests |
|------|----------------|---------|-------|
| `packages/crypto/lease_signer.py` | Ed25519 QKBNL signing | `LeaseSigner` | `test_core.py` |
| `packages/policy/state_machine.py` | Policy state transitions | `PolicyStateMachine` | `test_core.py`, `test_integration.py` |
| `packages/policy/engine.py` | Core policy orchestrator | `PolicyEngine` | N/A |

## PQC & Telemetry

| File | Responsibility | Exports | Tests |
|------|----------------|---------|-------|
| `packages/pqc/mlkem.py` | ML-KEM encapsulation | `keygen`, `encapsulate`, `decapsulate` | N/A |
| `packages/pqc/recovery.py` | PQC Recovery Handshake | `execute_pqc_recovery` | `test_integration.py` |
| `packages/telemetry/optical_anomaly.py` | Optical anomaly detection | `OpticalAnomalyEngine` | `test_core.py` |

## Applications

| File | Responsibility | Exports | Tests |
|------|----------------|---------|-------|
| `apps/control-plane/app/main.py` | FastAPI application | `app` | N/A |
| `apps/router-agent/agent.py` | POSIX/Python router agent | `RouterAgent` | N/A |
| `apps/arduino_bridge/crc.py` | UART CRC parser | `compute_frame_crc` | `test_core.py` |
| `apps/arduino_bridge/parser.py` | UART Serial parsing | `parse_optical_frame` | `test_core.py` |
| `apps/dashboard/src/App.tsx` | React Dashboard UI | `App` | N/A |
