"""
ShorlyNot Router Guard & QKD KMS Client Service.
Bridges the OpenWrt TP-Link Archer C6 Router Guard & KMS Simulator
with the ShorlyNot Mock Bank and Dark SOC Threat Dashboard.

Default KMS Hardware IP Specification:
  KMS_URL="${KMS_URL:-http://192.168.1.2:8000}"
  Router Gateway IP: 192.168.1.1
  Subnet: 192.168.1.0/24
  Relay Port: 8765
"""

import os
import time
import random
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger("shorlynot.router_client")

# Hardware Specification Defaults
HARDWARE_KMS_DEFAULT_URL = "http://192.168.1.2:8000"
LOCAL_KMS_FALLBACK_URL = "http://127.0.0.1:8000"


class RouterGuardClient:
    """
    Client for OpenWrt Router Guard & QKD Key Management System (KMS).
    Built around default hardware address: http://192.168.1.2:8000
    with seamless local loopback fallback (http://127.0.0.1:8000).
    """

    def __init__(self, kms_url: Optional[str] = None):
        # Priority: explicit param > env var > hardware default (192.168.1.2:8000)
        self.explicit_kms_url = kms_url or os.environ.get("KMS_URL")
        self.hardware_kms_url = HARDWARE_KMS_DEFAULT_URL
        self.active_kms_url = self.explicit_kms_url or self.hardware_kms_url

        self.relay_port = int(os.environ.get("RELAY_PORT", 8765))
        self.hardware_info = {
            "device": "TP-Link Archer C6 v3.20",
            "soc": "MediaTek MT7621A MIPS 1004Kc (880 MHz)",
            "os": "OpenWrt 22.03.7 (Linux 5.10.215)",
            "firewall": "fw4 (nftables v1.0.2)",
            "guard_daemon": "router_guard.sh (KMS_URL=\"${KMS_URL:-http://192.168.1.2:8000}\")",
            "kms_hardware_url": self.hardware_kms_url,
            "router_ip": "192.168.1.1",
            "subnet": "192.168.1.0/24",
            "relay_port": self.relay_port,
            "enforcement_hook": "inet fw4 router_guard_forward (priority filter - 1)"
        }

        self._cached_status: Dict[str, Any] = {
            "status": "GREEN",
            "qber": 1.4,
            "key_rate": 2420,
            "polls": 0,
            "uptime": 0.0,
            "connected": False,
            "auto_demo": False,
            "dropped_packets": 0,
            "active_endpoint": self.active_kms_url,
            "hardware_kms_url": self.hardware_kms_url,
            "last_rule": "accept",
            "physical_router_connected": False,
            "physical_router_ip": "192.168.1.1",
            "physical_router_state": "UNKNOWN",
            "state_file": "/tmp/router_guard.state"
        }
        self._total_drops = 0
        self._last_probe_time = 0.0

    def _probe_physical_router_state(self) -> Optional[str]:
        """Directly probes /tmp/router_guard.state on the physical OpenWrt router via SSH."""
        now = time.time()
        # Throttle to once every 2 seconds to avoid excessive SSH overhead
        if now - self._last_probe_time < 2.0:
            return self._cached_status.get("physical_router_state")
        self._last_probe_time = now

        try:
            import subprocess
            res = subprocess.run(
                ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=1", "-o", "BatchMode=yes", "root@192.168.1.1", "cat /tmp/router_guard.state 2>/dev/null"],
                capture_output=True,
                text=True,
                timeout=1.5
            )
            if res.returncode == 0 and res.stdout.strip():
                state = res.stdout.strip().upper()
                self._cached_status["physical_router_connected"] = True
                self._cached_status["physical_router_state"] = state
                return state
        except Exception:
            pass

        return self._cached_status.get("physical_router_state")

    def _get_candidate_endpoints(self) -> List[str]:
        """Returns candidate endpoints to try in order: localhost:8000 first, then explicit env, hardware IP."""
        endpoints = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        if self.explicit_kms_url:
            endpoints.append(self.explicit_kms_url)
        endpoints.append(self.hardware_kms_url)
        seen = set()
        unique = []
        for ep in endpoints:
            clean = ep.rstrip("/")
            if clean not in seen:
                seen.add(clean)
                unique.append(clean)
        return unique

    def get_status(self) -> Dict[str, Any]:
        """Fetch real-time physical link status from /link_status and kernel telemetry."""
        connected = False
        candidates = self._get_candidate_endpoints()

        for candidate in candidates:
            try:
                with httpx.Client(timeout=0.6) as client:
                    # Primary check: /link_status as requested
                    resp = client.get(f"{candidate}/link_status")
                    if resp.status_code == 200:
                        data = resp.json()
                        self.active_kms_url = candidate
                        self._cached_status.update({
                            "status": data.get("status", "GREEN"),
                            "qber": float(data.get("qber", 1.4)),
                            "key_rate": int(data.get("key_rate", 2420)),
                            "connected": True,
                            "active_endpoint": f"{candidate}/link_status"
                        })
                        connected = True
                        break
            except Exception:
                continue

        if not connected:
            self._cached_status["connected"] = False

        # Live probe physical OpenWrt router /tmp/router_guard.state
        self._probe_physical_router_state()

        # Update dropped packet simulation based on current state
        status = self._cached_status["status"]
        if status == "RED":
            self._total_drops += random.randint(3, 9)
            router_action = f"DROP (Relay Port {self.relay_port} Severed)"
            last_rule = f"ip daddr 192.168.1.0/24 tcp dport {self.relay_port} drop"
        elif status == "YELLOW":
            router_action = f"ALLOW (Warning / Rate-Limited on Port {self.relay_port})"
            last_rule = f"log prefix \"[ROUTER_GUARD_WARN] QBER={self._cached_status['qber']}% \" limit rate 5/minute"
        else:
            router_action = f"ALLOW (Relay Port {self.relay_port} Line-Rate Open)"
            last_rule = "policy accept"

        self._cached_status["dropped_packets"] = self._total_drops
        self._cached_status["router_action"] = router_action
        self._cached_status["last_rule"] = last_rule
        self._cached_status["hardware"] = self.hardware_info
        self._cached_status["hardware_kms_url"] = self.hardware_kms_url
        self._cached_status["nftables_output"] = self._generate_nftables_syntax(status, self._cached_status["qber"])

        return self._cached_status

    def set_state(self, state: str) -> Dict[str, Any]:
        """Manually trigger GREEN / YELLOW / RED state on the router KMS."""
        state = state.upper()
        if state not in ("GREEN", "YELLOW", "RED"):
            return {"status": "error", "message": f"Invalid state: {state}"}

        candidates = self._get_candidate_endpoints()
        for candidate in candidates:
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.post(f"{candidate}/set/{state}")
                    if resp.status_code == 200:
                        self.active_kms_url = candidate
                        self._cached_status["status"] = state
                        self._cached_status["active_endpoint"] = candidate
                        return resp.json()
            except Exception:
                continue

        # Local state fallback if hardware KMS is offline
        self._cached_status["status"] = state
        if state == "GREEN":
            self._cached_status["qber"] = 1.4
            self._cached_status["key_rate"] = 2450
        elif state == "YELLOW":
            self._cached_status["qber"] = 6.8
            self._cached_status["key_rate"] = 1100
        else:
            self._cached_status["qber"] = 16.5
            self._cached_status["key_rate"] = 0
        return {"status": "ok", "new_status": state, "simulated": True}

    def set_qber(self, qber: float) -> Dict[str, Any]:
        """Manually inject arbitrary QBER value."""
        candidates = self._get_candidate_endpoints()
        for candidate in candidates:
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.post(f"{candidate}/set_qber/{qber}")
                    if resp.status_code == 200:
                        self.active_kms_url = candidate
                        self._cached_status["active_endpoint"] = candidate
                        return resp.json()
            except Exception:
                continue

        self._cached_status["qber"] = qber
        if qber < 4.0:
            self._cached_status["status"] = "GREEN"
        elif qber < 11.0:
            self._cached_status["status"] = "YELLOW"
        else:
            self._cached_status["status"] = "RED"
        return {"status": "ok", "new_status": self._cached_status["status"], "qber": qber}

    def toggle_demo(self, active: bool) -> Dict[str, Any]:
        """Start or stop automated 15-second QKD presentation cycle."""
        endpoint = "/demo/start" if active else "/demo/stop"
        candidates = self._get_candidate_endpoints()
        for candidate in candidates:
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.post(f"{candidate}{endpoint}")
                    if resp.status_code == 200:
                        self._cached_status["auto_demo"] = active
                        return resp.json()
            except Exception:
                continue

        self._cached_status["auto_demo"] = active
        return {"demo": "started" if active else "stopped", "simulated": True}

    def sync_from_quantum_stage(self, stage_s: int = 0, stage_q: int = 0, threat_label: str = "") -> str:
        """
        Synchronizes cryptographic QKD Link Stage and signature threat level directly to Router Guard.
        When ANY attack is triggered (forgery, impersonation, replay, channel, downgrade, unauth):
          - Immediately sets router state to RED so http://localhost:8000/link_status and /tmp/router_guard.state say RED.
        When reset:
          - Restores state to GREEN.
        """
        threat = str(threat_label).upper()
        if stage_s >= 2 or stage_q >= 2 or threat in ("FORGERY", "IMPERSONATION", "REPLAY", "UNAUTH", "UNAUTH_VERIFY", "CHANNEL", "CHANNEL_TAMPER", "DOWNGRADE", "PARAM_TAMPER"):
            self.set_state("RED")
            return "RED"
        elif stage_s == 1 or stage_q == 1:
            self.set_state("YELLOW")
            return "YELLOW"
        else:
            self.set_state("GREEN")
            return "GREEN"

    def _generate_nftables_syntax(self, status: str, qber: float) -> str:
        """Generates authentic OpenWrt fw4 / nftables terminal representation."""
        endpoint_display = self.active_kms_url if self._cached_status.get("connected") else f"{self.hardware_kms_url} [Hardware Default]"
        physical_state = self._cached_status.get("physical_router_state", "UNKNOWN")
        physical_info = f"# Physical Router: 192.168.1.1 (/tmp/router_guard.state = {physical_state})\n" if self._cached_status.get("physical_router_connected") else ""
        if status == "GREEN":
            return (
                f"# OpenWrt 22.03.7 / fw4 - table inet fw4\n"
                f"{physical_info}"
                f"# Router Guard: router_guard.sh (KMS: {endpoint_display})\n"
                f"# Hook: forward (priority filter - 1) | Policy: ACCEPT\n"
                f"table inet fw4 {{\n"
                f"    chain router_guard_forward {{\n"
                f"        type filter hook forward priority filter - 1; policy accept;\n"
                f"        # Channel Status: GREEN (QBER={qber:.1f}% < 4.0%)\n"
                f"        # Relay Port {self.relay_port} (192.168.1.0/24): ALLOWED [Normal Key Production]\n"
                f"    }}\n"
                f"}}"
            )
        elif status == "YELLOW":
            return (
                f"# OpenWrt 22.03.7 / fw4 - table inet fw4\n"
                f"{physical_info}"
                f"# Router Guard: router_guard.sh (KMS: {endpoint_display})\n"
                f"# Hook: forward (priority filter - 1) | Policy: ACCEPT [WARNING LOG ACTIVE]\n"
                f"table inet fw4 {{\n"
                f"    chain router_guard_forward {{\n"
                f"        type filter hook forward priority filter - 1; policy accept;\n"
                f"        # Optical Drift Detected: YELLOW (4.0% <= QBER={qber:.1f}% < 11.0%)\n"
                f"        tcp dport {self.relay_port} log prefix \"[ROUTER_GUARD_WARN] \" limit rate 5/minute\n"
                f"        tcp dport {self.relay_port} accept comment \"Key generation rate reduced\"\n"
                f"    }}\n"
                f"}}"
            )
        else: # RED
            return (
                f"# OpenWrt 22.03.7 / fw4 - table inet fw4\n"
                f"{physical_info}"
                f"# Router Guard: router_guard.sh (KMS: {endpoint_display})\n"
                f"# Hook: forward (priority filter - 1) | Policy: DROP [SECURITY LOCKDOWN]\n"
                f"table inet fw4 {{\n"
                f"    chain router_guard_forward {{\n"
                f"        type filter hook forward priority filter - 1; policy accept;\n"
                f"        # EAVESDROPPER / LINK FAILURE: RED (QBER={qber:.1f}% >= 11.0% BB84 Limit)\n"
                f"        # ENFORCEMENT: Hardware Netfilter Dropping Relay Traffic\n"
                f"        ip daddr 192.168.1.0/24 tcp dport {self.relay_port} drop comment \"QKD_EAVESDROP_SEVERED\"\n"
                f"        tcp dport {self.relay_port} drop comment \"FAIL_SECURE_BLOCK\"\n"
                f"    }}\n"
                f"}}"
            )


# Global singleton instance
GLOBAL_ROUTER_CLIENT = RouterGuardClient()
