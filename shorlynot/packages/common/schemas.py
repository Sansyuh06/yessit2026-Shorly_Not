"""Pydantic v2 domain schemas for all ShorlyNot entities.

These are the API-facing and service-layer models. SQLAlchemy ORM models
live in packages.common.database.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from ipaddress import IPv4Address
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.common.enums import (
    AttackType,
    DeviceStatus,
    DeviceType,
    EnforcementStatus,
    EntropyStage,
    ExecutionMode,
    FirewallAction,
    LeaseStatus,
    PolicyState,
    PulseClass,
    QKDProtocol,
    QuantumJobStatus,
    SecurityEventType,
    SecurityStatus,
    Severity,
)

MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ────────────────────────────────────────────────────────────
# Device
# ────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    mac_address: str
    ipv4_address: IPv4Address
    device_type: DeviceType = DeviceType.UNKNOWN

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        v = v.lower()
        if not MAC_RE.match(v):
            raise ValueError(
                "MAC address must be lowercase colon-separated hex: aa:bb:cc:dd:ee:ff"
            )
        return v


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    mac_address: str
    ipv4_address: str
    device_type: DeviceType
    status: DeviceStatus
    created_at: datetime
    updated_at: datetime


# ────────────────────────────────────────────────────────────
# Quantum Job
# ────────────────────────────────────────────────────────────

class QuantumJobCreate(BaseModel):
    protocol: QKDProtocol
    backend_name: str = "aer_simulator"
    requested_shots: int = Field(..., ge=100, le=1_000_000)
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION


class QuantumJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    protocol: QKDProtocol
    backend_name: str
    provider_job_id: Optional[str] = None
    execution_mode: ExecutionMode
    requested_shots: int
    completed_shots: int
    status: QuantumJobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    raw_result_hash: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# ────────────────────────────────────────────────────────────
# QKD Session
# ────────────────────────────────────────────────────────────

class QKDSessionCreate(BaseModel):
    protocol: QKDProtocol
    alice_device_id: str
    bob_device_id: str
    requested_shots: int = Field(1024, ge=100, le=1_000_000)
    attack_type: AttackType = AttackType.NONE
    attack_probability: float = Field(0.0, ge=0.0, le=1.0)


class QKDSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    protocol: QKDProtocol
    quantum_job_id: str
    alice_device_id: str
    bob_device_id: str
    raw_key_length: int
    sifted_key_length: int
    reconciled_key_length: int
    final_key_length: int
    qber: Optional[float] = None
    chsh_s: Optional[float] = None
    estimated_eve_information: float = 0.0
    min_entropy_raw: float = 0.0
    min_entropy_sifted: float = 0.0
    min_entropy_reconciled: float = 0.0
    min_entropy_final: float = 0.0
    security_status: SecurityStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


# ────────────────────────────────────────────────────────────
# QKBNL Lease
# ────────────────────────────────────────────────────────────

class QKBNLLeaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lease_id: str
    device_id: str
    qkd_session_id: str
    key_fingerprint: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    status: LeaseStatus
    policy_version: str
    nonce: str
    sequence_number: int
    signature_algorithm: str
    signature: str


class QKBNLLeasePayload(BaseModel):
    """Canonical JSON payload for signing."""

    lease_id: str
    device_id: str
    qkd_session_id: str
    key_fingerprint: str
    issued_at: str  # ISO 8601
    expires_at: str  # ISO 8601
    nonce: str
    sequence_number: int
    policy_version: str

    def canonical_json(self) -> str:
        """Produce deterministic JSON with sorted keys matching PRD field order."""
        import json

        ordered = {
            "lease_id": self.lease_id,
            "device_id": self.device_id,
            "qkd_session_id": self.qkd_session_id,
            "key_fingerprint": self.key_fingerprint,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "sequence_number": self.sequence_number,
            "policy_version": self.policy_version,
        }
        return json.dumps(ordered, separators=(",", ":"))


# ────────────────────────────────────────────────────────────
# Firewall Event
# ────────────────────────────────────────────────────────────

class FirewallEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lease_id: str
    router_id: str
    action: FirewallAction
    target_ip: str
    target_mac: Optional[str] = None
    rule_identifier: str
    requested_at: datetime
    acknowledged_at: Optional[datetime] = None
    status: EnforcementStatus
    router_response_hash: Optional[str] = None
    error_code: Optional[str] = None


# ────────────────────────────────────────────────────────────
# Optical Telemetry
# ────────────────────────────────────────────────────────────

class OpticalTelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence: int
    timestamp: datetime
    detector_value: int
    normalized_intensity: float = Field(..., ge=0.0, le=1.0)
    alice_basis: Optional[int] = Field(None, ge=0, le=1)
    alice_bit: Optional[int] = Field(None, ge=0, le=1)
    bob_basis: Optional[int] = Field(None, ge=0, le=1)
    bob_bit: Optional[int] = Field(None, ge=0, le=1)
    eve_present: Optional[bool] = None
    serial_port: str
    frame_crc_valid: bool


# ────────────────────────────────────────────────────────────
# Security Event
# ────────────────────────────────────────────────────────────

class SecurityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: SecurityEventType
    severity: Severity
    qkd_session_id: Optional[str] = None
    lease_id: Optional[str] = None
    device_id: Optional[str] = None
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    evidence_hash: str
    timestamp: datetime
    metadata_json: dict[str, Any] = Field(default_factory=dict)


# ────────────────────────────────────────────────────────────
# Evidence Record
# ────────────────────────────────────────────────────────────

class EvidenceRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    timestamp: datetime
    execution_mode: ExecutionMode
    source: str
    payload_hash: str
    previous_hash: str
    record_hash: str


# ────────────────────────────────────────────────────────────
# Entropy Ledger
# ────────────────────────────────────────────────────────────

class EntropyLedgerEntry(BaseModel):
    stage: EntropyStage
    input_bits: int
    output_bits: int
    estimated_min_entropy: float
    disclosed_bits: int = 0
    eve_information_bound: float = 0.0


# ────────────────────────────────────────────────────────────
# Finite-Key Result
# ────────────────────────────────────────────────────────────

class FiniteKeyResult(BaseModel):
    observed_qber: float
    qber_upper_bound: float
    sample_size: int
    epsilon: float
    leakage_ec: float
    finite_size_penalty: float
    estimated_secret_bits: int
    secure: bool


# ────────────────────────────────────────────────────────────
# Reconciliation Result
# ────────────────────────────────────────────────────────────

class ReconciliationResult(BaseModel):
    reconciled_key: list[int]
    corrected_error_count: int
    remaining_error_count: int
    disclosed_bits: int
    leakage_bits: float
    passes: int


# ────────────────────────────────────────────────────────────
# PQC Recovery
# ────────────────────────────────────────────────────────────

class PQCRecoveryRecord(BaseModel):
    id: str = Field(default_factory=_new_uuid)
    kem_algorithm: str
    public_key_size: int
    ciphertext_size: int
    shared_secret_size: int
    handshake_duration_ms: float
    transcript_hash: str
    replacement_lease_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "started"


# ────────────────────────────────────────────────────────────
# WebSocket Event Envelope
# ────────────────────────────────────────────────────────────

class WSEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=_new_uuid)
    event_type: str
    timestamp: datetime = Field(default_factory=_utc_now)
    sequence: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


# ────────────────────────────────────────────────────────────
# Protocol Comparison
# ────────────────────────────────────────────────────────────

class ProtocolComparisonEntry(BaseModel):
    protocol: QKDProtocol
    transmitted_qubits: int
    sifted_bits: int
    attack_detection_point: Optional[int] = None
    observed_qber: Optional[float] = None
    chsh_s: Optional[float] = None
    secure_key_estimate: int
    protocol_efficiency: float
    detected_eve_information: float
    backend: str
    shots: int
    execution_mode: ExecutionMode
