"""SQLAlchemy 2.0 ORM models for ShorlyNot QKBNL platform.

All relations use RESTRICT on delete (no cascading deletes in production).
Soft-state transitions are used instead of hard deletes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# ────────────────────────────────────────────────────────────
# Device
# ────────────────────────────────────────────────────────────

class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    ipv4_address: Mapped[str] = mapped_column(String(15), nullable=False)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    # Relationships
    alice_sessions: Mapped[list["QKDSessionModel"]] = relationship(
        back_populates="alice_device", foreign_keys="QKDSessionModel.alice_device_id"
    )
    bob_sessions: Mapped[list["QKDSessionModel"]] = relationship(
        back_populates="bob_device", foreign_keys="QKDSessionModel.bob_device_id"
    )
    leases: Mapped[list["QKBNLLeaseModel"]] = relationship(back_populates="device")


# ────────────────────────────────────────────────────────────
# Quantum Job
# ────────────────────────────────────────────────────────────

class QuantumJobModel(Base):
    __tablename__ = "quantum_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    backend_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_shots: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_shots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_result_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    qkd_session: Mapped["QKDSessionModel | None"] = relationship(back_populates="quantum_job")


# ────────────────────────────────────────────────────────────
# QKD Session
# ────────────────────────────────────────────────────────────

class QKDSessionModel(Base):
    __tablename__ = "qkd_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    quantum_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quantum_jobs.id", ondelete="RESTRICT"), nullable=False
    )
    alice_device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="RESTRICT"), nullable=False
    )
    bob_device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="RESTRICT"), nullable=False
    )
    raw_key_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sifted_key_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reconciled_key_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    final_key_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qber: Mapped[float | None] = mapped_column(Float, nullable=True)
    chsh_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_eve_information: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_entropy_raw: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_entropy_sifted: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_entropy_reconciled: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_entropy_final: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    security_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    quantum_job: Mapped["QuantumJobModel"] = relationship(back_populates="qkd_session")
    alice_device: Mapped["DeviceModel"] = relationship(
        back_populates="alice_sessions", foreign_keys=[alice_device_id]
    )
    bob_device: Mapped["DeviceModel"] = relationship(
        back_populates="bob_sessions", foreign_keys=[bob_device_id]
    )
    leases: Mapped[list["QKBNLLeaseModel"]] = relationship(back_populates="qkd_session")
    security_events: Mapped[list["SecurityEventModel"]] = relationship(
        back_populates="qkd_session",
        foreign_keys="SecurityEventModel.qkd_session_id",
    )


# ────────────────────────────────────────────────────────────
# QKBNL Lease
# ────────────────────────────────────────────────────────────

class QKBNLLeaseModel(Base):
    __tablename__ = "qkbnl_leases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    lease_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="RESTRICT"), nullable=False
    )
    qkd_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("qkd_sessions.id", ondelete="RESTRICT"), nullable=False
    )
    key_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="ED25519")
    signature: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    device: Mapped["DeviceModel"] = relationship(back_populates="leases")
    qkd_session: Mapped["QKDSessionModel"] = relationship(back_populates="leases")
    firewall_events: Mapped[list["FirewallEventModel"]] = relationship(
        back_populates="lease"
    )
    security_events: Mapped[list["SecurityEventModel"]] = relationship(
        back_populates="lease",
        foreign_keys="SecurityEventModel.lease_id",
    )


# ────────────────────────────────────────────────────────────
# Firewall Event
# ────────────────────────────────────────────────────────────

class FirewallEventModel(Base):
    __tablename__ = "firewall_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    lease_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("qkbnl_leases.id", ondelete="RESTRICT"), nullable=False
    )
    router_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    target_ip: Mapped[str] = mapped_column(String(15), nullable=False)
    target_mac: Mapped[str | None] = mapped_column(String(17), nullable=True)
    rule_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="requested")
    router_response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    lease: Mapped["QKBNLLeaseModel"] = relationship(back_populates="firewall_events")


# ────────────────────────────────────────────────────────────
# Optical Telemetry
# ────────────────────────────────────────────────────────────

class OpticalTelemetryModel(Base):
    __tablename__ = "optical_telemetry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    detector_value: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_intensity: Mapped[float] = mapped_column(Float, nullable=False)
    alice_basis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alice_bit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bob_basis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bob_bit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eve_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    serial_port: Mapped[str] = mapped_column(String(64), nullable=False)
    frame_crc_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)


# ────────────────────────────────────────────────────────────
# Security Event
# ────────────────────────────────────────────────────────────

class SecurityEventModel(Base):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    qkd_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("qkd_sessions.id", ondelete="RESTRICT"), nullable=True
    )
    lease_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("qkbnl_leases.id", ondelete="RESTRICT"), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="RESTRICT"), nullable=True
    )
    observed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    qkd_session: Mapped["QKDSessionModel | None"] = relationship(
        back_populates="security_events", foreign_keys=[qkd_session_id]
    )
    lease: Mapped["QKBNLLeaseModel | None"] = relationship(
        back_populates="security_events", foreign_keys=[lease_id]
    )


# ────────────────────────────────────────────────────────────
# Evidence Record
# ────────────────────────────────────────────────────────────

class EvidenceRecordModel(Base):
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    execution_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
