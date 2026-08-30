"""Typed, validated application configuration using pydantic-settings.

Every environment variable from .env.example is represented here with
validation and documentation. Secret values are never logged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.common.enums import ExecutionMode


class ShorlyNotConfig(BaseSettings):
    """Master configuration — loaded from env vars / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Execution Mode ──────────────────────────────────────
    shorlynot_execution_mode: ExecutionMode = ExecutionMode.SIMULATION

    # ── Database ────────────────────────────────────────────
    database_url: str = "sqlite:///./runtime/shorlynot.db"

    # ── Control Plane ───────────────────────────────────────
    control_plane_host: str = "127.0.0.1"
    control_plane_port: int = Field(8000, ge=1, le=65535)

    # ── Router Agent ────────────────────────────────────────
    router_agent_url: str = "http://192.168.1.1:9100"
    router_request_timeout_seconds: int = Field(5, ge=1, le=60)

    # ── Signing Keys ────────────────────────────────────────
    control_plane_signing_private_key_path: Optional[str] = None
    router_signing_public_key_path: Optional[str] = None

    # ── IBM Quantum (SECRET) ────────────────────────────────
    ibm_quantum_token: Optional[str] = Field(None, json_schema_extra={"secret": True})
    ibm_quantum_instance: Optional[str] = None
    ibm_quantum_backend: Optional[str] = None

    # ── QKD Thresholds ──────────────────────────────────────
    qkd_qber_warning_threshold: float = Field(0.08, ge=0.0, le=1.0)
    qkd_qber_compromise_threshold: float = Field(0.11, ge=0.0, le=1.0)
    qkd_chsh_threshold: float = Field(2.0, ge=0.0, le=4.0)
    qkd_security_epsilon: float = Field(1e-10, gt=0.0)
    qkd_min_final_key_bits: int = Field(128, ge=1)

    # ── QKBNL Lease ─────────────────────────────────────────
    qkbnl_default_ttl_seconds: int = Field(60, ge=10, le=3600)
    qkbnl_max_clock_skew_seconds: int = Field(5, ge=0, le=60)

    # ── Arduino / Optical Telemetry ─────────────────────────
    arduino_serial_port: Optional[str] = None
    arduino_baudrate: int = Field(115200, ge=9600)
    arduino_dark_level: Optional[int] = None
    arduino_bright_level: Optional[int] = None
    arduino_decision_threshold: float = Field(0.5, ge=0.0, le=1.0)

    # ── PQC ─────────────────────────────────────────────────
    mlkem_variant: str = "ML-KEM-768"

    # ── Logging ─────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Validation ──────────────────────────────────────────

    @field_validator("mlkem_variant")
    @classmethod
    def validate_mlkem(cls, v: str) -> str:
        allowed = {"ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"}
        if v not in allowed:
            raise ValueError(f"mlkem_variant must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v

    def require_real_quantum(self) -> None:
        """Raise if execution mode is REAL but IBM credentials are missing."""
        if self.shorlynot_execution_mode == ExecutionMode.REAL:
            if not self.ibm_quantum_token:
                raise ValueError("IBM_QUANTUM_TOKEN required for REAL execution mode")
            if not self.ibm_quantum_backend:
                raise ValueError("IBM_QUANTUM_BACKEND required for REAL execution mode")

    def require_real_signing_keys(self) -> None:
        """Raise if execution mode is REAL but signing keys are missing."""
        if self.shorlynot_execution_mode == ExecutionMode.REAL:
            if not self.control_plane_signing_private_key_path:
                raise ValueError(
                    "CONTROL_PLANE_SIGNING_PRIVATE_KEY_PATH required for REAL execution mode"
                )
            path = Path(self.control_plane_signing_private_key_path)
            if not path.exists():
                raise FileNotFoundError(f"Signing key not found: {path}")

    def safe_dict(self) -> dict:
        """Return config dict with secrets redacted."""
        d = self.model_dump()
        for key in ("ibm_quantum_token",):
            if d.get(key):
                d[key] = "***REDACTED***"
        return d
