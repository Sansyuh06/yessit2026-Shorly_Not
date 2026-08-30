"""Unified error handling for ShorlyNot."""

import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger("shorlynot")


class ShorlyNotError(Exception):
    """Base exception."""

    pass


class QuantumChannelError(ShorlyNotError):
    """Raised when quantum channel is compromised."""

    pass


class KeyManagementError(ShorlyNotError):
    """Raised when key operations fail."""

    pass


class NetworkError(ShorlyNotError):
    """Raised when network operations fail."""

    pass


def safe_api_call(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Wrap all HTTP calls with consistent error handling."""
    try:
        r = getattr(httpx, method)(url, timeout=kwargs.pop("timeout", 10), **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        logger.error(f"Cannot reach {url}")
        return {"error": f"Cannot reach {url}", "status": "OFFLINE"}
    except httpx.TimeoutException:
        logger.error(f"Timeout: {url}")
        return {"error": f"Timeout: {url}", "status": "TIMEOUT"}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code}: {url}")
        return {"error": f"HTTP {e.response.status_code}", "status": "ERROR"}
    except Exception as e:
        logger.exception(f"Unexpected error: {url}")
        return {"error": str(e), "status": "ERROR"}
