"""Router agent — QKBNL lease enforcement daemon.

Validates leases, manages iptables rules via the SHORLYNOT chain,
and runs a lease expiry watchdog.

PRD §16-18.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from packages.common.enums import EnforcementStatus, FirewallAction, LeaseStatus
from packages.common.errors import (
    FirewallAckTimeoutError,
    InvalidLeaseSignatureError,
    LeaseExpiredError,
    LeaseReplayError,
)
from packages.common.schemas import QKBNLLeasePayload
from packages.crypto.lease_signer import LeaseVerifier

logger = logging.getLogger("shorlynot.router-agent")

MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


# ── Models ──────────────────────────────────────────────────

class LeaseApplyRequest(BaseModel):
    lease: dict[str, Any]
    signature: str
    key_id: str


class LeaseApplyResponse(BaseModel):
    request_id: str
    lease_id: str
    rule_identifier: str
    applied_at: str
    verified: bool
    router_id: str


class ActiveLease(BaseModel):
    lease_id: str
    device_id: str
    target_ip: str
    target_mac: Optional[str] = None
    rule_identifier: str
    issued_at: datetime
    expires_at: datetime
    sequence_number: int
    nonce_hash: str


class RouterCapabilities(BaseModel):
    iptables: bool = False
    ipset: bool = False
    conntrack: bool = False
    ubus: bool = False
    platform: str = "unknown"


# ── Replay Guard ────────────────────────────────────────────

class ReplayGuard:
    """Prevents replay attacks by tracking nonces and sequence numbers."""

    def __init__(self, max_nonce_cache: int = 10000) -> None:
        self._sequence_numbers: dict[str, int] = {}  # device_id -> highest seq
        self._seen_nonces: set[str] = set()
        self._max_cache = max_nonce_cache

    def check_and_record(
        self,
        device_id: str,
        sequence_number: int,
        nonce: str,
    ) -> None:
        """Validate replay protection fields.

        Raises:
            LeaseReplayError: If nonce was seen or sequence is stale.
        """
        import hashlib

        nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()[:32]

        # Check nonce
        if nonce_hash in self._seen_nonces:
            raise LeaseReplayError(f"Nonce replay detected for device {device_id}")

        # Check sequence number
        highest = self._sequence_numbers.get(device_id, 0)
        if sequence_number <= highest:
            raise LeaseReplayError(
                f"Stale sequence {sequence_number} ≤ {highest} for device {device_id}"
            )

        # Record
        if len(self._seen_nonces) >= self._max_cache:
            # Evict oldest (simple approach — in production use LRU)
            self._seen_nonces.clear()

        self._seen_nonces.add(nonce_hash)
        self._sequence_numbers[device_id] = sequence_number

    def get_nonce_hash(self, nonce: str) -> str:
        import hashlib

        return hashlib.sha256(nonce.encode()).hexdigest()[:32]


# ── Firewall Manager (simulation) ──────────────────────────

class FirewallManager:
    """Manages the SHORLYNOT iptables chain.

    In simulation mode, tracks rules in memory.
    In real mode, executes iptables commands via subprocess.

    PRD §17: Never flush INPUT/OUTPUT/FORWARD. Never modify unrelated rules.
    All commands use argument arrays with shell=False.
    """

    CHAIN_NAME = "SHORLYNOT"

    def __init__(self, simulation: bool = True) -> None:
        self._simulation = simulation
        self._rules: dict[str, dict[str, Any]] = {}  # rule_id -> rule details
        self._chain_exists = False

    def ensure_chain(self) -> bool:
        """Create SHORLYNOT chain if it doesn't exist."""
        if self._simulation:
            self._chain_exists = True
            return True

        import subprocess

        # Check if chain exists
        result = subprocess.run(
            ["iptables", "-L", self.CHAIN_NAME, "-n"],
            capture_output=True,
            shell=False,
        )
        if result.returncode != 0:
            # Create chain
            subprocess.run(
                ["iptables", "-N", self.CHAIN_NAME],
                check=True,
                shell=False,
            )
            # Insert jump from FORWARD (or INPUT depending on topology)
            subprocess.run(
                ["iptables", "-I", "FORWARD", "-j", self.CHAIN_NAME],
                check=True,
                shell=False,
            )

        self._chain_exists = True
        return True

    def apply_allow_rule(
        self,
        lease_id: str,
        target_ip: str,
        target_mac: Optional[str] = None,
    ) -> str:
        """Install an ALLOW rule for the given target.

        Returns the rule identifier.
        """
        # Validate IP
        ipaddress.IPv4Address(target_ip)
        if target_mac and not MAC_RE.match(target_mac.lower()):
            raise ValueError(f"Invalid MAC address: {target_mac}")

        rule_id = f"shorlynot:{lease_id}"

        if self._simulation:
            self._rules[rule_id] = {
                "action": "ALLOW",
                "target_ip": target_ip,
                "target_mac": target_mac,
                "lease_id": lease_id,
                "installed_at": datetime.now(timezone.utc).isoformat(),
            }
            return rule_id

        # Real iptables command
        import subprocess

        cmd = [
            "iptables", "-A", self.CHAIN_NAME,
            "-s", target_ip,
            "-j", "ACCEPT",
            "-m", "comment", "--comment", rule_id,
        ]
        if target_mac:
            cmd.extend(["-m", "mac", "--mac-source", target_mac.upper()])

        subprocess.run(cmd, check=True, shell=False)

        self._rules[rule_id] = {
            "action": "ALLOW",
            "target_ip": target_ip,
            "target_mac": target_mac,
            "lease_id": lease_id,
        }
        return rule_id

    def remove_lease_rule(self, lease_id: str) -> bool:
        """Remove the rule associated with a lease."""
        rule_id = f"shorlynot:{lease_id}"

        if self._simulation:
            return self._rules.pop(rule_id, None) is not None

        import subprocess

        # Find and remove the rule by comment
        result = subprocess.run(
            ["iptables", "-L", self.CHAIN_NAME, "-n", "--line-numbers", "-v"],
            capture_output=True,
            text=True,
            shell=False,
        )
        # Parse output to find the rule number
        for line in result.stdout.split("\n"):
            if rule_id in line:
                parts = line.split()
                if parts:
                    rule_num = parts[0]
                    subprocess.run(
                        ["iptables", "-D", self.CHAIN_NAME, rule_num],
                        check=True,
                        shell=False,
                    )
                    self._rules.pop(rule_id, None)
                    return True

        return False

    def verify_rule(self, lease_id: str) -> bool:
        """Verify that a rule exists for the lease."""
        rule_id = f"shorlynot:{lease_id}"

        if self._simulation:
            return rule_id in self._rules

        import subprocess

        result = subprocess.run(
            ["iptables", "-L", self.CHAIN_NAME, "-n", "-v"],
            capture_output=True,
            text=True,
            shell=False,
        )
        return rule_id in result.stdout

    def list_managed_rules(self) -> dict[str, dict[str, Any]]:
        """List all rules managed by ShorlyNot."""
        return dict(self._rules)

    def flush_conntrack(self, target_ip: str) -> bool:
        """Flush connection tracking state for a specific IP.

        Never flushes the complete conntrack table.

        PRD §17: Use conntrack only for the target client.
        """
        ipaddress.IPv4Address(target_ip)  # Validate

        if self._simulation:
            logger.info(f"[SIM] Flushed conntrack for {target_ip}")
            return True

        import subprocess

        result = subprocess.run(
            ["conntrack", "-D", "-s", target_ip],
            capture_output=True,
            shell=False,
        )
        if result.returncode != 0:
            logger.warning(f"conntrack flush failed for {target_ip}: {result.stderr}")
            return False
        return True


# ── Lease Watchdog ──────────────────────────────────────────

class LeaseWatchdog:
    """Monitors active leases and revokes expired ones.

    Checks every 1 second. Router enforces expiry without waiting
    for the control plane. No automatic infinite fail-open mode.

    PRD §18.
    """

    def __init__(
        self,
        firewall: FirewallManager,
        check_interval: float = 1.0,
    ) -> None:
        self._firewall = firewall
        self._interval = check_interval
        self._active_leases: dict[str, ActiveLease] = {}
        self._running = False

    def register_lease(self, lease: ActiveLease) -> None:
        """Register an active lease for watchdog monitoring."""
        self._active_leases[lease.lease_id] = lease

    def remove_lease(self, lease_id: str) -> None:
        """Remove a lease from monitoring (e.g., after explicit revocation)."""
        self._active_leases.pop(lease_id, None)

    def check_expirations(self) -> list[str]:
        """Check and revoke expired leases. Returns list of revoked lease IDs."""
        now = datetime.now(timezone.utc)
        expired = []

        for lease_id, lease in list(self._active_leases.items()):
            if now >= lease.expires_at:
                logger.info(f"Watchdog: lease {lease_id} expired, revoking")
                self._firewall.remove_lease_rule(lease_id)
                self._firewall.flush_conntrack(lease.target_ip)
                del self._active_leases[lease_id]
                expired.append(lease_id)

        return expired

    async def run(self) -> None:
        """Run the watchdog loop."""
        self._running = True
        while self._running:
            self.check_expirations()
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        """Stop the watchdog loop."""
        self._running = False

    @property
    def active_count(self) -> int:
        return len(self._active_leases)

    @property
    def active_leases(self) -> dict[str, ActiveLease]:
        return dict(self._active_leases)


# ── Router Agent Core ───────────────────────────────────────

class RouterAgent:
    """Core router agent orchestrating lease validation and enforcement.

    Validation order (PRD §16):
        1. JSON schema
        2. Signature
        3. Expiry
        4. issued_at clock skew
        5. Device
        6. Nonce replay
        7. Sequence number
        8. Policy version
    """

    def __init__(
        self,
        router_id: Optional[str] = None,
        simulation: bool = True,
        max_clock_skew_seconds: int = 5,
    ) -> None:
        self.router_id = router_id or str(uuid.uuid4())
        self._verifier = LeaseVerifier()
        self._replay_guard = ReplayGuard()
        self._firewall = FirewallManager(simulation=simulation)
        self._watchdog = LeaseWatchdog(self._firewall)
        self._max_skew = max_clock_skew_seconds
        self._simulation = simulation
        self._known_devices: set[str] = set()
        self._accepted_policy_versions: set[str] = {"1.0.0"}

        # Initialize chain
        self._firewall.ensure_chain()

    @property
    def firewall(self) -> FirewallManager:
        return self._firewall

    @property
    def watchdog(self) -> LeaseWatchdog:
        return self._watchdog

    @property
    def replay_guard(self) -> ReplayGuard:
        return self._replay_guard

    def register_signing_key(self, key_id: str, public_key: Any) -> None:
        """Register a control-plane signing public key."""
        self._verifier.register_key(key_id, public_key)

    def register_device(self, device_id: str) -> None:
        """Register a known device."""
        self._known_devices.add(device_id)

    def apply_lease(self, request: LeaseApplyRequest) -> LeaseApplyResponse:
        """Validate and apply a lease.

        Follows the strict validation order from PRD §16.
        """
        request_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 1. Parse lease payload
        payload = QKBNLLeasePayload(**request.lease)

        # 2. Verify signature
        try:
            valid = self._verifier.verify(request.key_id, payload, request.signature)
        except KeyError:
            raise InvalidLeaseSignatureError(f"Unknown key ID: {request.key_id}")

        if not valid:
            raise InvalidLeaseSignatureError("Ed25519 signature verification failed")

        # 3. Check expiry
        expires_at = datetime.fromisoformat(payload.expires_at)
        if now >= expires_at:
            raise LeaseExpiredError(f"Lease expired at {payload.expires_at}")

        # 4. Check clock skew
        issued_at = datetime.fromisoformat(payload.issued_at)
        skew = abs((now - issued_at).total_seconds())
        if skew > self._max_skew:
            raise LeaseExpiredError(
                f"Clock skew {skew:.1f}s exceeds maximum {self._max_skew}s"
            )

        # 5. Check device is known
        if self._known_devices and payload.device_id not in self._known_devices:
            logger.warning(f"Unknown device {payload.device_id}, allowing in permissive mode")

        # 6-7. Replay protection (nonce + sequence)
        self._replay_guard.check_and_record(
            payload.device_id, payload.sequence_number, payload.nonce
        )

        # 8. Policy version
        if payload.policy_version not in self._accepted_policy_versions:
            raise ValueError(f"Unknown policy version: {payload.policy_version}")

        # ── All checks passed — install firewall rule ──
        rule_id = self._firewall.apply_allow_rule(
            payload.lease_id,
            payload.device_id,  # In real use, this would be resolved to an IP
        )

        # Verify rule
        verified = self._firewall.verify_rule(payload.lease_id)

        # Register with watchdog
        nonce_hash = self._replay_guard.get_nonce_hash(payload.nonce)
        self._watchdog.register_lease(ActiveLease(
            lease_id=payload.lease_id,
            device_id=payload.device_id,
            target_ip=payload.device_id,  # Placeholder
            rule_identifier=rule_id,
            issued_at=issued_at,
            expires_at=expires_at,
            sequence_number=payload.sequence_number,
            nonce_hash=nonce_hash,
        ))

        return LeaseApplyResponse(
            request_id=request_id,
            lease_id=payload.lease_id,
            rule_identifier=rule_id,
            applied_at=now.isoformat(),
            verified=verified,
            router_id=self.router_id,
        )

    def revoke_lease(self, lease_id: str) -> bool:
        """Revoke a lease — remove firewall rule and flush conntrack."""
        removed = self._firewall.remove_lease_rule(lease_id)
        if removed:
            # Verify rule is absent
            still_exists = self._firewall.verify_rule(lease_id)
            if still_exists:
                logger.error(f"Rule for {lease_id} still exists after removal!")
                return False

            # Remove from watchdog
            self._watchdog.remove_lease(lease_id)
            return True
        return False

    def get_capabilities(self) -> RouterCapabilities:
        """Detect and report runtime capabilities."""
        import platform
        import shutil

        return RouterCapabilities(
            iptables=shutil.which("iptables") is not None,
            ipset=shutil.which("ipset") is not None,
            conntrack=shutil.which("conntrack") is not None,
            ubus=shutil.which("ubus") is not None,
            platform=platform.system(),
        )

    def get_health(self) -> dict[str, Any]:
        """Return health status."""
        return {
            "router_id": self.router_id,
            "simulation": self._simulation,
            "chain_exists": self._firewall._chain_exists,
            "active_rules": len(self._firewall.list_managed_rules()),
            "active_leases": self._watchdog.active_count,
            "capabilities": self.get_capabilities().model_dump(),
        }
