# ShorlyNot Router Guard 🛡️

Firmware enforcement and automated security layer for the **ShorlyNot Quantum Key Distribution (QKD) Key Management System (KMS)**, specifically engineered for the **TP-Link Archer C6 v3.20** running **OpenWrt 22.03.7** with modern `fw4` / `nftables`.

The router serves as a semi-trusted enforcer: it never holds quantum key material itself. It continuously polls the KMS `/link_status` endpoint and dynamically manipulates the kernel's netfilter firewall to allow or completely sever relay traffic (TCP port 8765) based on real-time quantum channel integrity.

---

## Architecture & Security Model

```text
+-----------------------+          +------------------------------------+          +--------------------+
|  Quantum Link / KMS   |          |    OpenWrt Archer C6 v3 Router     |          |   Relay Clients    |
| (QBER & Key Metrics)  |  HTTP    |                                    |  TCP     | (Client & Server)  |
|                       | -------> |  router_guard.sh (procd daemon)    | -------> |                    |
|   - QBER < 4% (GREEN) |  :8000   |                 │                  |  :8765   |                    |
|   - QBER 4-11% (YEL)  |          |                 ▼                  |          |                    |
|   - QBER >= 11% (RED) |          |  nftables base chain               |          |                    |
+-----------------------+          |  (priority filter - 1)             |          +--------------------+
```

### QKD State Thresholds (BB84 Protocol)

| State | QBER Threshold | Physical Channel Meaning | Router Action | Relay Port 8765 |
| :--- | :--- | :--- | :--- | :--- |
| **🟢 GREEN** | `QBER < 4.0%` | Channel healthy, high key rate (>2000 bps) | `enforce_allow` (chain empty) | **ALLOWED** |
| **🟡 YELLOW**| `4.0% ≤ QBER < 11%` | Optical noise / thermal drift / warning | `enforce_allow` (logged) | **ALLOWED** |
| **🔴 RED** | `QBER ≥ 11.0%` | **Eavesdropping detected!** (BB84 limit exceeded) | `enforce_drop` (`dport 8765 drop`) | **BLOCKED** |
| **🔴 RED** | Unreachable (5x) | KMS unreachable / link severed (Fail-Secure) | `enforce_drop` (`dport 8765 drop`) | **BLOCKED** |

---

## Project Structure

```
ShorlyNot-Router-Firmware/
├── Makefile                       # Top-level build and demo automation
├── README.md                      # Project documentation and guide
├── .gitignore                     # Git ignore rules
│
├── src/                           # Host-side tools & simulators
│   ├── mock_kms.py                # QKD KMS simulator with Web Dashboard & QBER physics
│   ├── router_guard.sh            # Standalone router guard script (dry-run & live)
│   └── fake_relay.py              # Mock TCP relay server for port 8765 testing
│
├── openwrt/                       # Firmware build files
│   ├── build_image.sh             # ImageBuilder wrapper script (WSL/Linux compatible)
│   └── files/                     # Rootfs overlay files baked into the image
│       ├── etc/
│       │   ├── config/router_guard        # UCI configuration (kms_host, ports, etc.)
│       │   ├── firewall.router_guard      # fw4 table include (priority filter - 1 base chain)
│       │   ├── init.d/router_guard        # procd init service
│       │   └── uci-defaults/
│       │       └── 99-router-guard        # First-boot automatic firewall registration
│       └── usr/bin/
│           └── router_guard.sh            # Production router guard daemon
│
├── tests/                         # Test suite
└── tools/
    └── demo.sh                    # Automated interactive demo runner
```

---

## 1. Building & Flashing Firmware

### Step 1: Build the Firmware Image
From the repository root (in WSL or Linux):
```bash
make firmware
```
*(Or directly: `cd openwrt && ./build_image.sh`)*

This compiles the rootfs overlay using the official OpenWrt 22.03.7 ImageBuilder for `ramips/mt7621` (profile `tplink_archer-c6-v3`). The generated binaries are saved to `firmware/`:
* `openwrt-22.03.7-ramips-mt7621-tplink_archer-c6-v3-squashfs-sysupgrade.bin`
* `openwrt-22.03.7-ramips-mt7621-tplink_archer-c6-v3-squashfs-factory.bin`

### Step 2: (Optional) Verify Rootfs Files Inside the Binary
To ensure all custom guard files are correctly bundled inside the SquashFS:
```bash
unsquashfs -f -o 2734206 -d /tmp/fw_inspect firmware/*sysupgrade.bin \
  etc/firewall.router_guard \
  etc/uci-defaults/99-router-guard \
  etc/init.d/router_guard \
  usr/bin/router_guard.sh \
  etc/config/router_guard
```

### Step 3: Transfer to the Router
OpenWrt uses Dropbear SSH, so pass the `-O` flag to specify legacy SCP:
```bash
scp -O firmware/*sysupgrade.bin root@192.168.1.1:/tmp/sysupgrade.bin
```

### Step 4: Flash on the Router
SSH into the router:
```bash
ssh root@192.168.1.1
```
Perform the safety test run:
```bash
sysupgrade -T /tmp/sysupgrade.bin
```
Flash without preserving old conflicting configuration (`-n`):
```bash
sysupgrade -n /tmp/sysupgrade.bin
```
*The router will write to flash and reboot (~2–3 minutes).*

---

## 2. Router Operations & Commands

### Find Connected Host IP
On the router, check the active DHCP leases to find your PC's IP:
```bash
cat /tmp/dhcp.leases
```

### Configure KMS Server Host
```bash
uci set router_guard.main.kms_host='192.168.1.123'
uci commit router_guard
/etc/init.d/router_guard restart
```

### Service Lifecycle Commands
```bash
/etc/init.d/router_guard status     # Check service status (running/stopped)
/etc/init.d/router_guard restart    # Restart service with latest UCI config
/etc/init.d/router_guard stop       # Stop service (triggers fail-secure cleanup)
/etc/init.d/router_guard start      # Start service
```

### Verify Active Firewall Enforcement
Check the kernel `router_guard_forward` base chain:
```bash
nft list chain inet fw4 router_guard_forward
```
* **When Link is GREEN**:
  ```text
  table inet fw4 {
          chain router_guard_forward {
                  type filter hook forward priority filter - 1; policy accept;
          }
  }
  ```
* **When Link is RED (Attacked / Down)**:
  ```text
  table inet fw4 {
          chain router_guard_forward {
                  type filter hook forward priority filter - 1; policy accept;
                  tcp dport 8765 drop
          }
  }
  ```

### Live Log Monitoring
```bash
logread -f | grep router_guard
```

### Check Current Guard State
```bash
/usr/bin/router_guard.sh --status
# Or view the state file directly:
cat /tmp/router_guard.state
```

---

## 3. QKD KMS Simulator & Judge Demonstration

The included `src/mock_kms.py` provides a live quantum simulation with an interactive Web Presentation Dashboard.

### Starting the KMS Server
Run on your PC in Windows PowerShell (or WSL with port forwarding):
```powershell
python src/mock_kms.py --port 8000
```

### Presentation Dashboard
Open your browser at:
👉 **`http://localhost:8000/`** (or `http://192.168.1.123:8000/`)

The dashboard displays:
* **Live QBER Gauge**: Real-time percentage readouts.
* **Live Key Rate**: Real-time bits/second generation rate.
* **Router Enforcement Status**: Shows whether router firewall is `ALLOW` or `BLOCK`.
* **Total Router Polls**: Live counter showing checks from the physical router.
* **Interactive Scenario Buttons**: 1-click simulation triggers.

### Demonstrating to Judges

#### Option A: 1-Click Interactive Buttons
On the web dashboard (or via `curl` / `wget`), trigger:
1. **Low Error Rate** (QBER `1.5%` -> 🟢 **GREEN**):
   ```bash
   wget -qO- http://192.168.1.123:8000/set_qber/1.5
   ```
   * Router clears `drop` rule; port 8765 traffic is allowed.
2. **Medium Optical Noise** (QBER `6.8%` -> 🟡 **YELLOW**):
   ```bash
   wget -qO- http://192.168.1.123:8000/set_qber/6.8
   ```
   * Router updates state to `YELLOW`; traffic remains allowed.
3. **Simulate Eavesdropping Attack** (QBER `16.2%` -> 🔴 **RED**):
   ```bash
   wget -qO- http://192.168.1.123:8000/set_qber/16.2
   ```
   * Within 3 seconds, `tcp dport 8765 drop` appears in the router's firewall!

#### Option B: Automated Hands-Free Demo Loop
Click **`⏱️ Start Automated Judge Demo`** on the web UI or start the script with `--demo`:
```powershell
python src/mock_kms.py --port 8000 --demo
```
The simulator automatically cycles through:
* **0–15s**: Normal channel (QBER `1.4%`) -> 🟢 GREEN (Firewall OPEN)
* **15–30s**: Channel degradation (QBER `6.8%`) -> 🟡 YELLOW (Warning logged)
* **30–45s**: Eavesdropping attack (QBER `16.5%`) -> 🔴 RED (Firewall BLOCKS 8765)
* **45s+**: Eavesdropper detached (QBER `1.2%`) -> 🟢 GREEN (Firewall RESTORES 8765)

---

## 4. Troubleshooting & Gotchas

1. **`Failed to send request: Operation not permitted` on router**:
   * Windows Defender Firewall is blocking inbound connections on port 8000.
   * Run in an elevated PowerShell:
     ```powershell
     netsh advfirewall firewall add rule name="MockKMS" dir=in action=allow protocol=TCP localport=8000
     ```
2. **`ash: /usr/libexec/sftp-server: not found` during SCP**:
   * OpenWrt uses Dropbear SSH, which does not have SFTP installed. Always use `scp -O` (legacy SCP protocol).
3. **`WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED`**:
   * Flashing fresh firmware regenerates the router's SSH host keys. Clear the old key:
     ```bash
     ssh-keygen -R 192.168.1.1
     ```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
