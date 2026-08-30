"""Typed application errors for ShorlyNot.

Each error maps to a specific HTTP status and system behavior
as defined in PRD section 28.
"""

from __future__ import annotations


class ShorlyNotError(Exception):
    """Base exception for all ShorlyNot errors."""

    error_code: str = "UNKNOWN_ERROR"
    http_status: int = 500
    message: str = "An unknown error occurred."

    def __init__(self, message: str | None = None, **kwargs: object) -> None:
        self.message = message or self.__class__.message
        self.details = kwargs
        super().__init__(self.message)


# ── Configuration ───────────────────────────────────────────

class ConfigInvalidError(ShorlyNotError):
    error_code = "CONFIG_INVALID"
    http_status = 500
    message = "Configuration is invalid. Dependent services will not start."


# ── Database ────────────────────────────────────────────────

class DatabaseUnavailableError(ShorlyNotError):
    error_code = "DATABASE_UNAVAILABLE"
    http_status = 503
    message = "Database is unavailable after retry attempts."


# ── IBM Quantum ─────────────────────────────────────────────

class IBMAuthFailedError(ShorlyNotError):
    error_code = "IBM_AUTH_FAILED"
    http_status = 503
    message = "IBM Quantum authentication failed. No fallback to simulation."


class IBMBackendUnavailableError(ShorlyNotError):
    error_code = "IBM_BACKEND_UNAVAILABLE"
    http_status = 503
    message = "IBM Quantum backend is unavailable. Quantum job FAILED."


class QuantumJobTimeoutError(ShorlyNotError):
    error_code = "QUANTUM_JOB_TIMEOUT"
    http_status = 504
    message = "Quantum job timed out. Provider job ID preserved."


class QuantumResultInvalidError(ShorlyNotError):
    error_code = "QUANTUM_RESULT_INVALID"
    http_status = 422
    message = "Quantum result is invalid. Cannot calculate QBER."


# ── QKD ─────────────────────────────────────────────────────

class InsufficientKeyMaterialError(ShorlyNotError):
    error_code = "INSUFFICIENT_KEY_MATERIAL"
    http_status = 422
    message = "Insufficient key material. Cannot issue lease."


class QKDSecurityThresholdFailedError(ShorlyNotError):
    error_code = "QKD_SECURITY_THRESHOLD_FAILED"
    http_status = 409
    message = "QKD security threshold exceeded. Transition to COMPROMISED."


# ── Arduino / Telemetry ────────────────────────────────────

class ArduinoNotConnectedError(ShorlyNotError):
    error_code = "ARDUINO_NOT_CONNECTED"
    http_status = 503
    message = "Arduino is not connected. Optical telemetry unavailable."


class SerialFrameInvalidError(ShorlyNotError):
    error_code = "SERIAL_FRAME_INVALID"
    http_status = 422
    message = "Serial frame is malformed. Frame not persisted."


class SerialCRCFailedError(ShorlyNotError):
    error_code = "SERIAL_CRC_FAILED"
    http_status = 422
    message = "Serial frame CRC check failed. Frame not persisted."


class CalibrationInvalidError(ShorlyNotError):
    error_code = "CALIBRATION_INVALID"
    http_status = 422
    message = "Calibration invalid: bright_level must exceed dark_level."


# ── Router / Firewall ──────────────────────────────────────

class RouterUnreachableError(ShorlyNotError):
    error_code = "ROUTER_UNREACHABLE"
    http_status = 503
    message = "Router agent is unreachable. Firewall state unknown."


class FirewallAckTimeoutError(ShorlyNotError):
    error_code = "FIREWALL_ACK_TIMEOUT"
    http_status = 504
    message = "Firewall acknowledgement timed out. Status UNKNOWN."


# ── Lease ───────────────────────────────────────────────────

class InvalidLeaseSignatureError(ShorlyNotError):
    error_code = "INVALID_LEASE_SIGNATURE"
    http_status = 401
    message = "Lease signature verification failed. CRITICAL security event."


class LeaseReplayError(ShorlyNotError):
    error_code = "LEASE_REPLAY"
    http_status = 409
    message = "Lease replay detected. CRITICAL security event."


class LeaseExpiredError(ShorlyNotError):
    error_code = "LEASE_EXPIRED"
    http_status = 409
    message = "Lease has expired."


# ── Policy ──────────────────────────────────────────────────

class InvalidPolicyTransitionError(ShorlyNotError):
    error_code = "INVALID_POLICY_TRANSITION"
    http_status = 409
    message = "Invalid policy state transition. Current state preserved."


# ── PQC ─────────────────────────────────────────────────────

class MLKEMUnavailableError(ShorlyNotError):
    error_code = "MLKEM_UNAVAILABLE"
    http_status = 503
    message = "ML-KEM library unavailable. PQC recovery cannot proceed."


# ── Evidence ────────────────────────────────────────────────

class EvidenceChainInvalidError(ShorlyNotError):
    error_code = "EVIDENCE_CHAIN_INVALID"
    http_status = 500
    message = "Evidence chain integrity compromised."


# ── QPU-specific ────────────────────────────────────────────

class QPUUnavailableError(ShorlyNotError):
    error_code = "IBM_QPU_UNAVAILABLE"
    http_status = 503
    message = "IBM QPU is unavailable."
