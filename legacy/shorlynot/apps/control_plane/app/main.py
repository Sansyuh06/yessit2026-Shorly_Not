"""ShorlyNot Control Plane — FastAPI application entry point.

PRD §23.
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.common.config import ShorlyNotConfig
from packages.common.enums import ExecutionMode
from packages.common.errors import ShorlyNotError

# ── Logging ─────────────────────────────────────────────────

logger = logging.getLogger("shorlynot.control-plane")


# ── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown."""
    config = ShorlyNotConfig()
    app.state.config = config

    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    logger.info("ShorlyNot Control Plane starting")
    logger.info(f"Execution mode: {config.shorlynot_execution_mode.value}")
    logger.info(f"Database: {config.database_url}")

    # Initialize database
    from packages.common.database import Base

    if "sqlite" in config.database_url:
        from sqlalchemy import create_engine

        # Ensure runtime directory exists
        db_path = config.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            config.database_url,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        app.state.engine = engine
        logger.info("Database initialized")

    # Initialize evidence chain
    from packages.common.evidence import EvidenceChain

    app.state.evidence_chain = EvidenceChain()

    # Initialize policy engine
    from packages.policy.engine import PolicyEngine
    from packages.policy.state_machine import PolicyStateMachine

    sm = PolicyStateMachine()
    policy = PolicyEngine(
        state_machine=sm,
        qber_warning=config.qkd_qber_warning_threshold,
        qber_compromise=config.qkd_qber_compromise_threshold,
        chsh_threshold=config.qkd_chsh_threshold,
    )
    app.state.policy_engine = policy

    # Initialize lease signer (simulation mode generates ephemeral keys)
    from packages.crypto.lease_signer import LeaseSigner

    if config.shorlynot_execution_mode == ExecutionMode.SIMULATION:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        priv_key = Ed25519PrivateKey.generate()
        signer = LeaseSigner(private_key=priv_key)
        app.state.lease_signer = signer
        logger.info(f"Simulation signing key generated: {signer.key_id}")
    elif config.control_plane_signing_private_key_path:
        signer = LeaseSigner(private_key_path=config.control_plane_signing_private_key_path)
        app.state.lease_signer = signer
        logger.info(f"Signing key loaded: {signer.key_id}")

    # WebSocket clients
    app.state.ws_clients: set = set()

    yield

    logger.info("ShorlyNot Control Plane shutting down")


# ── Application ─────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="ShorlyNot — Quantum-Key-Bound Network Lease Control Plane",
        description="QKBNL enforcement platform control API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID Middleware ──
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Global Exception Handler ──
    @app.exception_handler(ShorlyNotError)
    async def shorlynot_error_handler(request: Request, exc: ShorlyNotError) -> JSONResponse:
        logger.error(
            f"[{getattr(request.state, 'request_id', 'unknown')}] "
            f"{exc.error_code}: {exc.message}"
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "unknown")
        logger.exception(f"[{req_id}] Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred.",
                "request_id": req_id,
            },
        )

    # ── Register Routes ──
    from apps.control_plane.app.api import router as api_router

    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    config = ShorlyNotConfig()
    uvicorn.run(
        "apps.control_plane.app.main:app",
        host=config.control_plane_host,
        port=config.control_plane_port,
        reload=True,
    )
