"""All domain enumerations for ShorlyNot QKBNL platform."""

from __future__ import annotations

import enum


class ExecutionMode(str, enum.Enum):
    """System execution mode — controls whether real hardware is required."""

    REAL = "real"
    SIMULATION = "simulation"
    REPLAY = "replay"


class DeviceType(str, enum.Enum):
    """Classification of a network device."""

    CONTROL_PLANE = "control_plane"
    CLIENT = "client"
    ROUTER = "router"
    ARDUINO = "arduino"
    UNKNOWN = "unknown"


class DeviceStatus(str, enum.Enum):
    """Current operational status of a device."""

    ONLINE = "online"
    OFFLINE = "offline"
    BLOCKED = "blocked"
    AUTHORIZED = "authorized"
    UNKNOWN = "unknown"


class QKDProtocol(str, enum.Enum):
    """Supported QKD protocol families."""

    BB84 = "BB84"
    B92 = "B92"
    E91 = "E91"
    DECOY_BB84 = "DECOY_BB84"


class QuantumJobStatus(str, enum.Enum):
    """Lifecycle status of a quantum circuit job."""

    CREATED = "created"
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SecurityStatus(str, enum.Enum):
    """Security assessment of a QKD session."""

    UNKNOWN = "unknown"
    SECURE = "secure"
    WARNING = "warning"
    COMPROMISED = "compromised"
    INSUFFICIENT_KEY_MATERIAL = "insufficient_key_material"


class LeaseStatus(str, enum.Enum):
    """Lifecycle status of a QKBNL lease."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REPLACED = "replaced"
    REJECTED = "rejected"


class FirewallAction(str, enum.Enum):
    """Firewall rule action type."""

    ALLOW = "allow"
    BLOCK = "block"
    REVOKE = "revoke"
    FLUSH_CONNECTIONS = "flush_connections"
    RESTORE = "restore"


class EnforcementStatus(str, enum.Enum):
    """Status of a firewall enforcement operation."""

    REQUESTED = "requested"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class SecurityEventType(str, enum.Enum):
    """Classification of security events."""

    QBER_THRESHOLD_EXCEEDED = "qber_threshold_exceeded"
    CHSH_VIOLATION_LOST = "chsh_violation_lost"
    PNS_SUSPECTED = "pns_suspected"
    PARTIAL_INTERCEPT_SUSPECTED = "partial_intercept_suspected"
    OPTICAL_ANOMALY = "optical_anomaly"
    LEASE_REPLAY = "lease_replay"
    LEASE_EXPIRED = "lease_expired"
    INVALID_SIGNATURE = "invalid_signature"
    ROUTER_ACK_FAILURE = "router_ack_failure"
    ENTROPY_INSUFFICIENT = "entropy_insufficient"


class Severity(str, enum.Enum):
    """Severity level for security events."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyState(str, enum.Enum):
    """System policy state machine states."""

    INITIALIZING = "initializing"
    SECURE = "secure"
    OBSERVING = "observing"
    DEGRADED = "degraded"
    COMPROMISED = "compromised"
    REVOKING = "revoking"
    ISOLATED = "isolated"
    PQC_RECOVERY = "pqc_recovery"
    RESTORING = "restoring"
    ERROR = "error"


class EntropyStage(str, enum.Enum):
    """Key entropy pipeline stages."""

    RAW = "raw"
    SIFTED = "sifted"
    RECONCILED = "reconciled"
    PRIVACY_AMPLIFIED = "privacy_amplified"


class AttackType(str, enum.Enum):
    """Supported experimental attack models."""

    NONE = "none"
    INTERCEPT_RESEND = "intercept_resend"
    PARTIAL_INTERCEPT_RESEND = "partial_intercept_resend"
    PNS = "pns"
    BEAM_SPLITTING = "beam_splitting"


class PulseClass(str, enum.Enum):
    """Decoy-state pulse intensity classes."""

    SIGNAL = "signal"
    DECOY = "decoy"
    VACUUM = "vacuum"
