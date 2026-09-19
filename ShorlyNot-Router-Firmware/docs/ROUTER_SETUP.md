# OpenWrt TP-Link Archer C6 Hardware Setup Guide

This document details the configuration, network topology, and verification commands for the **ShorlyNot Router Guard** running on physical OpenWrt hardware.

---

## 1. Hardware Specifications

| Component | Specification |
|---|---|
| **Model** | TP-Link Archer C6 v3.20 |
| **SoC** | MediaTek MT7621A MIPS 1004Kc (Dual-core, 880 MHz) |
| **RAM / Flash** | 128 MB DDR3 / 16 MB SPI Flash |
| **Firmware** | OpenWrt 22.03.7 (Linux 5.10.215) |
| **Firewall Engine** | `fw4` (nftables v1.0.2) |
| **Router IP** | `192.168.1.1` |
| **KMS Host IP** | `192.168.1.2:8000` |
| **Relay Port** | `8765` |

---

## 2. Quick Connect & Key Management

If reconnecting to a freshly flashed or reset router, clear stale SSH host keys:
```bash
ssh-keygen -R 192.168.1.1
ssh root@192.168.1.1
```

---

## 3. Starting the Router Guard Daemon

Transfer the guard script to the router `/root/` or `/usr/sbin/router_guard.sh`:
```bash
# Start KMS simulator on host machine
python src/mock_kms.py --port 8000 --demo

# On the Archer C6 router:
/usr/sbin/router_guard.sh --kms-url "http://192.168.1.2:8000" --poll-interval 1
```

---

## 4. Live Inspection

To inspect the real-time guard state and nftables rules on the router:
```bash
# Quick state inspection
cat /tmp/router_guard.state

# View nftables forward chain
nft list chain inet fw4 router_guard_forward

# Continuous monitoring via host machine
./tools/monitor_router.sh
```
