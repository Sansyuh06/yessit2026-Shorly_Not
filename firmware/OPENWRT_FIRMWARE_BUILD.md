# FinQuantum Shield — Custom OpenWrt Quantum-Aware Router Firmware

## Target: D-Link DSL-2750U | OpenWrt Customization (NOT full rewrite)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  OPENWRT ROUTER                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  qberd   │ │  ledctl  │ │lockdownctl│            │
│  │ (policy  │ │ (LED     │ │(firewall  │            │
│  │  daemon) │ │  manager)│ │ lockdown) │            │
│  └────┬─────┘ └────┬─────┘ └─────┬────┘            │
│       │             │             │                  │
│  ┌────┴─────────────┴─────────────┴────┐            │
│  │         /tmp/quantum_state.json      │            │
│  └─────────────────────────────────────┘            │
│                                                      │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐        │
│  │  panic   │ │ usb_log_mgr  │ │ kms_client│        │
│  │  button  │ │              │ │           │        │
│  └──────────┘ └──────────────┘ └──────────┘        │
│       WPS          USB              HTTP polling     │
└──────────────────────┬──────────────────────────────┘
                       │ GET /link_status
                       ▼
              ┌────────────────┐
              │  KMS Server    │
              │  (Laptop)      │
              │  FastAPI:8000  │
              │  BB84 + Qiskit │
              └────────────────┘
```

**Flow:**
1. `qberd` polls KMS `GET /link_status` every 3s
2. KMS returns `{"status":"GREEN","qber":0.03,"threat_level":1,"attack_detected":false}`
3. `qberd` writes state to `/tmp/quantum_state.json`
4. `ledctl` reads state → sets LEDs
5. `lockdownctl` reads state → applies firewall rules
6. WPS button → panic handler → force Level 4
7. USB hotplug → mount drive → redirect logs

---

## 2. Threat Model — 4-Level Ladder

| Level | Name | QBER Range | Network Action | LED Action | Log Action |
|-------|------|-----------|---------------|-----------|-----------|
| 1 | SAFE | < 5% | Normal forwarding | LED1 solid green | Log to RAM |
| 2 | SUSPICIOUS | 5-11% | Rate-limit sensitive ports | LED2 solid yellow (or blink) | Log warning |
| 3 | ATTACK LIKELY | 11-25% | Block non-essential, keep admin | LED3 fast blink | Flush to USB if present |
| 4 | LOCKDOWN | >25% or panic | Drop forwarding, kill Wi-Fi, keep SSH on LAN | LED4 solid red / all blink | Emergency dump to USB |

**WPS panic button:** Short press → escalate +1 level. Long press (>3s) → jump to Level 4.

---

## 3. Feature Feasibility Matrix

| Feature | OpenWrt Support | Difficulty | HW Dependent | Notes |
|---------|---------------|-----------|-------------|-------|
| Poll KMS + parse JSON | ✅ `wget` + `jsonfilter` | Easy | No | BusyBox built-in |
| Threat-level firewall | ✅ `iptables` / `nftables` | Easy | No | Standard OpenWrt |
| Lockdown mode | ✅ `iptables -P DROP` | Easy | No | Keep admin exception |
| WPS panic button | ✅ `/etc/rc.button/wps` | Easy | Partial | Button must exist in DTS |
| USB detect/mount | ✅ `hotplug.d` | Easy | Partial | Needs USB port + drivers |
| Save logs to USB | ✅ Shell redirect | Easy | No | After mount confirmed |
| LED threat indicator | ⚠️ `sysfs` LED class | Medium | YES | Board must expose LEDs |
| LAN LED repurpose | ❌ Usually switch-driven | Hard | YES | Most LAN LEDs not controllable |
| Disable Wi-Fi lockdown | ✅ `wifi down` / `uci` | Easy | No | Standard OpenWrt |
| Keep admin SSH alive | ✅ iptables exception | Easy | No | Whitelist port 22 |

---

## 4. OpenWrt File Layout

```
/usr/bin/qberd                    # QBER policy daemon (main loop)
/usr/bin/ledctl                   # LED state updater
/usr/bin/lockdownctl              # Firewall lockdown manager
/usr/bin/kms_poll                 # KMS HTTP client helper
/etc/init.d/qberd                 # procd init script
/etc/rc.button/wps                # WPS panic button handler
/etc/hotplug.d/usb/20-quantum-usb # USB insert/remove handler
/etc/config/quantum               # UCI config for KMS host, thresholds
/tmp/quantum_state.json           # Runtime state (RAM)
/tmp/quantum.log                  # Current log buffer
/mnt/usb/quantum-logs/            # USB log destination
```

---

## 5. Code Skeletons

All scripts below are BusyBox/ash-compatible shell scripts for OpenWrt.

### 5A. `/etc/config/quantum` — UCI Configuration

```
config quantum 'main'
    option kms_host '192.168.1.100'
    option kms_port '8000'
    option poll_interval '3'
    option threshold_l2 '0.05'
    option threshold_l3 '0.11'
    option threshold_l4 '0.25'
    option usb_mount '/mnt/usb'
    option log_dir 'quantum-logs'
    option admin_port '22'
    option lockdown_kill_wifi '1'
```

### 5B. `/usr/bin/qberd` — Main QBER Policy Daemon

```sh
#!/bin/sh
# qberd — Quantum Policy Daemon for OpenWrt
# Polls KMS, evaluates threat level, writes state, triggers actions

. /lib/functions.sh
config_load quantum

config_get KMS_HOST main kms_host "192.168.1.100"
config_get KMS_PORT main kms_port "8000"
config_get POLL main poll_interval "3"
config_get T2 main threshold_l2 "0.05"
config_get T3 main threshold_l3 "0.11"
config_get T4 main threshold_l4 "0.25"

STATE_FILE="/tmp/quantum_state.json"
LOG_FILE="/tmp/quantum.log"
CURRENT_LEVEL=1
KMS_URL="http://${KMS_HOST}:${KMS_PORT}/link_status"
FAIL_COUNT=0
MAX_FAILS=5

log_event() {
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $*" >> "$LOG_FILE"
    echo "[$ts] $*"
}

# Compare floats using awk (BusyBox compatible)
float_ge() {
    echo "$1 $2" | awk '{if ($1 >= $2) exit 0; else exit 1}'
}

calc_threat_level() {
    local qber="$1"
    local attack="$2"

    if [ "$attack" = "true" ] || float_ge "$qber" "$T4"; then
        echo 4
    elif float_ge "$qber" "$T3"; then
        echo 3
    elif float_ge "$qber" "$T2"; then
        echo 2
    else
        echo 1
    fi
}

write_state() {
    cat > "$STATE_FILE" <<EOF
{
  "level": $1,
  "qber": $2,
  "status": "$3",
  "attack_detected": $4,
  "timestamp": "$(date -Iseconds)",
  "kms_reachable": $5,
  "panic": $6
}
EOF
}

apply_level() {
    local new_level="$1"
    if [ "$new_level" -ne "$CURRENT_LEVEL" ]; then
        log_event "LEVEL CHANGE: $CURRENT_LEVEL -> $new_level"
        CURRENT_LEVEL=$new_level
        /usr/bin/ledctl "$CURRENT_LEVEL"
        /usr/bin/lockdownctl "$CURRENT_LEVEL"
    fi
}

log_event "qberd starting — polling $KMS_URL every ${POLL}s"
write_state 1 0.0 "GREEN" false true false

while true; do
    RESPONSE=$(wget -qO- "$KMS_URL" 2>/dev/null)

    if [ -z "$RESPONSE" ]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
        log_event "KMS unreachable (fail $FAIL_COUNT/$MAX_FAILS)"
        if [ "$FAIL_COUNT" -ge "$MAX_FAILS" ]; then
            log_event "KMS lost — escalating to L3 (safe default)"
            apply_level 3
            write_state 3 1.0 "UNKNOWN" false false false
        fi
        sleep "$POLL"
        continue
    fi

    FAIL_COUNT=0

    # Parse JSON with jsonfilter (standard OpenWrt tool)
    STATUS=$(echo "$RESPONSE" | jsonfilter -e '@.status' 2>/dev/null)
    QBER=$(echo "$RESPONSE" | jsonfilter -e '@.qber' 2>/dev/null)
    ATTACK=$(echo "$RESPONSE" | jsonfilter -e '@.attack_detected' 2>/dev/null)

    [ -z "$STATUS" ] && STATUS="UNKNOWN"
    [ -z "$QBER" ] && QBER="0.0"
    [ -z "$ATTACK" ] && ATTACK="false"

    # Check for panic override
    PANIC=false
    if [ -f /tmp/quantum_panic ]; then
        PANIC=true
        NEW_LEVEL=4
        log_event "PANIC OVERRIDE ACTIVE"
    else
        NEW_LEVEL=$(calc_threat_level "$QBER" "$ATTACK")
    fi

    write_state "$NEW_LEVEL" "$QBER" "$STATUS" "$ATTACK" true "$PANIC"
    apply_level "$NEW_LEVEL"

    # Copy logs to USB if mounted and level >= 3
    if [ "$NEW_LEVEL" -ge 3 ] && mountpoint -q /mnt/usb 2>/dev/null; then
        cp "$LOG_FILE" "/mnt/usb/quantum-logs/quantum_$(date +%Y%m%d).log" 2>/dev/null
    fi

    sleep "$POLL"
done
```

### 5C. `/usr/bin/ledctl` — LED State Updater

```sh
#!/bin/sh
# ledctl — Set router LEDs based on threat level
# Usage: ledctl <level>
# Fallback: uses available LEDs with blink patterns

LEVEL="${1:-1}"

# Discover available LEDs
LED_DIR="/sys/class/leds"

# Try to find usable LEDs (board-specific names)
find_led() {
    local pattern="$1"
    ls "$LED_DIR" 2>/dev/null | grep -i "$pattern" | head -1
}

LED_POWER=$(find_led "power")
LED_WLAN=$(find_led "wlan\|wifi\|wireless")
LED_USB=$(find_led "usb")
LED_WPS=$(find_led "wps")
LED_INET=$(find_led "internet\|inet\|wan")

set_led() {
    local led="$1" brightness="$2" trigger="$3" delay_on="$4" delay_off="$5"
    [ -z "$led" ] && return
    local path="$LED_DIR/$led"
    [ -d "$path" ] || return

    if [ "$trigger" = "timer" ]; then
        echo "timer" > "$path/trigger" 2>/dev/null
        echo "$delay_on" > "$path/delay_on" 2>/dev/null
        echo "$delay_off" > "$path/delay_off" 2>/dev/null
    else
        echo "none" > "$path/trigger" 2>/dev/null
        echo "$brightness" > "$path/brightness" 2>/dev/null
    fi
}

all_off() {
    for led in $(ls "$LED_DIR" 2>/dev/null); do
        echo "none" > "$LED_DIR/$led/trigger" 2>/dev/null
        echo 0 > "$LED_DIR/$led/brightness" 2>/dev/null
    done
}

case "$LEVEL" in
    1)  # SAFE — Power LED solid, all others off
        all_off
        set_led "$LED_POWER" 1
        ;;
    2)  # SUSPICIOUS — Power + WLAN blink slow
        all_off
        set_led "$LED_POWER" 1
        set_led "$LED_WLAN" 0 "timer" 1000 1000
        ;;
    3)  # ATTACK LIKELY — Power + WLAN + WPS blink fast
        all_off
        set_led "$LED_POWER" 0 "timer" 250 250
        set_led "$LED_WLAN" 0 "timer" 250 250
        set_led "$LED_WPS" 0 "timer" 500 500
        ;;
    4)  # LOCKDOWN — All available LEDs blink rapidly
        for led in $(ls "$LED_DIR" 2>/dev/null); do
            echo "timer" > "$LED_DIR/$led/trigger" 2>/dev/null
            echo 100 > "$LED_DIR/$led/delay_on" 2>/dev/null
            echo 100 > "$LED_DIR/$led/delay_off" 2>/dev/null
        done
        ;;
esac
```

### 5D. `/usr/bin/lockdownctl` — Firewall/Lockdown Manager

```sh
#!/bin/sh
# lockdownctl — Apply firewall rules based on threat level
# Usage: lockdownctl <level>

. /lib/functions.sh
config_load quantum
config_get ADMIN_PORT main admin_port "22"
config_get KILL_WIFI main lockdown_kill_wifi "1"

LEVEL="${1:-1}"

# Ensure our chain exists
iptables -N QUANTUM 2>/dev/null
iptables -C FORWARD -j QUANTUM 2>/dev/null || iptables -I FORWARD 1 -j QUANTUM

apply_rules() {
    iptables -F QUANTUM

    case "$LEVEL" in
        1)  # SAFE — allow all
            iptables -A QUANTUM -j RETURN
            # Ensure wifi is up
            wifi up 2>/dev/null
            ;;
        2)  # SUSPICIOUS — rate limit, log
            iptables -A QUANTUM -p tcp --dport 443 -m limit --limit 50/min -j RETURN
            iptables -A QUANTUM -p tcp --dport 80 -m limit --limit 50/min -j RETURN
            iptables -A QUANTUM -j RETURN
            ;;
        3)  # ATTACK LIKELY — block non-essential, keep DNS/SSH
            iptables -A QUANTUM -p tcp --dport "$ADMIN_PORT" -j ACCEPT
            iptables -A QUANTUM -p udp --dport 53 -j ACCEPT
            iptables -A QUANTUM -p tcp --dport 53 -j ACCEPT
            iptables -A QUANTUM -p tcp --dport 8000 -j ACCEPT  # KMS
            iptables -A QUANTUM -p tcp -j DROP
            ;;
        4)  # LOCKDOWN — drop everything except admin SSH
            iptables -A QUANTUM -p tcp --dport "$ADMIN_PORT" -j ACCEPT
            iptables -A QUANTUM -p udp --dport 53 -j ACCEPT
            iptables -A QUANTUM -j DROP

            # Kill Wi-Fi if configured
            if [ "$KILL_WIFI" = "1" ]; then
                wifi down 2>/dev/null
                logger -t lockdownctl "Wi-Fi disabled — LOCKDOWN"
            fi
            ;;
    esac

    logger -t lockdownctl "Applied threat level $LEVEL"
}

apply_rules
```

### 5E. `/etc/rc.button/wps` — WPS Panic Button Handler

```sh
#!/bin/sh
# WPS button remapped as quantum panic button
# Short press (<3s): escalate +1 level
# Long press (>=3s): immediate LOCKDOWN (Level 4)

[ "$ACTION" = "released" ] || exit 0

LOG_TAG="panic_button"

if [ "$SEEN" -ge 3 ]; then
    # Long press — FULL LOCKDOWN
    logger -t "$LOG_TAG" "LONG PRESS — LOCKDOWN ACTIVATED"
    touch /tmp/quantum_panic
    /usr/bin/ledctl 4
    /usr/bin/lockdownctl 4
    echo "PANIC: Manual lockdown at $(date)" >> /tmp/quantum.log
elif [ "$SEEN" -gt 0 ]; then
    # Short press — escalate one level
    if [ -f /tmp/quantum_state.json ]; then
        CURRENT=$(jsonfilter -i /tmp/quantum_state.json -e '@.level' 2>/dev/null)
        [ -z "$CURRENT" ] && CURRENT=1
    else
        CURRENT=1
    fi
    NEXT=$((CURRENT + 1))
    [ "$NEXT" -gt 4 ] && NEXT=4
    logger -t "$LOG_TAG" "SHORT PRESS — escalate to L$NEXT"
    /usr/bin/ledctl "$NEXT"
    /usr/bin/lockdownctl "$NEXT"
fi

# To clear panic: rm /tmp/quantum_panic && /usr/bin/lockdownctl 1
```

### 5F. `/etc/hotplug.d/usb/20-quantum-usb` — USB Detection

```sh
#!/bin/sh
# USB hotplug handler for quantum log storage

USB_MOUNT="/mnt/usb"
LOG_DIR="quantum-logs"

case "$ACTION" in
    add)
        logger -t quantum-usb "USB device inserted"
        sleep 2
        mkdir -p "$USB_MOUNT"
        # Try to mount first partition
        mount /dev/sda1 "$USB_MOUNT" 2>/dev/null || \
        mount /dev/sdb1 "$USB_MOUNT" 2>/dev/null

        if mountpoint -q "$USB_MOUNT"; then
            mkdir -p "$USB_MOUNT/$LOG_DIR"
            echo "USB_READY" > /tmp/quantum_usb_status
            logger -t quantum-usb "USB mounted at $USB_MOUNT — logging enabled"
            # Copy existing logs
            cp /tmp/quantum.log "$USB_MOUNT/$LOG_DIR/quantum_$(date +%Y%m%d_%H%M%S).log" 2>/dev/null
        fi
        ;;
    remove)
        logger -t quantum-usb "USB device removed"
        echo "USB_REMOVED" > /tmp/quantum_usb_status
        umount "$USB_MOUNT" 2>/dev/null
        logger -t quantum-usb "Logging reverted to RAM"
        ;;
esac
```

### 5G. `/etc/init.d/qberd` — procd Init Script

```sh
#!/bin/sh /etc/rc.common
# procd init script for qberd

START=99
STOP=10
USE_PROCD=1

start_service() {
    procd_open_instance
    procd_set_param command /usr/bin/qberd
    procd_set_param respawn 3600 5 5
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
```

---

## 6. Lockdown Profiles

### Soft Lockdown (Level 3)
- Block non-essential TCP (keep SSH, DNS, KMS)
- Wi-Fi stays up but rate-limited
- Logs flushed to USB

### Hard Lockdown (Level 4)
- DROP all forwarding except SSH on admin port
- Wi-Fi radios disabled (`wifi down`)
- All LEDs blink rapidly
- Emergency log dump to USB

### Recovery Mode
```sh
# SSH into router and run:
rm /tmp/quantum_panic
/usr/bin/lockdownctl 1
/usr/bin/ledctl 1
wifi up
```

---

## 7. Build & Deploy Roadmap

| Phase | Goal | Success Criteria |
|-------|------|-----------------|
| 0 | Verify HW | Check DSL-2750U OpenWrt support, USB, LEDs |
| 1 | Flash OpenWrt | Boot OpenWrt, SSH access working |
| 2 | Identify LEDs | `ls /sys/class/leds/` shows controllable LEDs |
| 3 | USB detection | Insert USB → auto-mount → write test file |
| 4 | QBER daemon | `qberd` polls KMS, writes state file |
| 5 | Firewall switching | `lockdownctl` applies correct rules per level |
| 6 | Panic button | WPS press triggers level change |
| 7 | Integration | All modules work together end-to-end |
| 8 | Demo hardening | 2-minute demo runs flawlessly |

---

## 8. Demo Script (2 minutes)

```
0:00 — Router boots, power LED solid green → "Quantum-aware mode active"
0:15 — Show laptop KMS dashboard, QBER ~2%, all GREEN
0:30 — Trigger attack from attacker console, QBER rises to 12%
0:40 — Router LEDs start blinking (L3) — "Attack detected!"
0:50 — Insert USB drive → logs start saving automatically
1:00 — Press WPS button (long press) → LOCKDOWN
1:10 — All LEDs blink rapidly, Wi-Fi dies, traffic blocked
1:20 — Show SSH still works (admin recovery path alive)
1:30 — Reset system, LEDs return to green, Wi-Fi comes back
1:45 — "Questions?"
```

---

## 9. Hardware Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| DSL-2750U LEDs not in sysfs | Can't control LEDs via software | Use USB LED strip or single controllable LED |
| WPS button not exposed | No panic button | Use GPIO button or remote trigger via API |
| USB port power insufficient | Drive won't mount | Use powered hub or small flash drive |
| Limited flash storage | Can't fit all packages | Use overlay on USB or minimal packages |
| No official OpenWrt support | Firmware won't boot | Use closest supported D-Link variant |

---

## 10. Integration with Existing Project

This firmware connects to your existing `kms_server.py` (FastAPI on port 8000).
The router polls the same `/link_status` endpoint that `router_guard.sh` already uses.

**Existing project components that stay on the laptop:**
- `kms/kms_server.py` — FastAPI KMS server
- `quantum_engine/bb84_simulator.py` — Qiskit BB84 engine
- `webapp/` — Banking dashboard
- `attacker_console.py` — Demo attack triggers

**New components that go ON the router:**
- Everything in this `firmware/` folder
- Deployed via `scp` to the OpenWrt router

**Deploy command:**
```sh
scp firmware/scripts/* root@192.168.1.1:/usr/bin/
scp firmware/config/* root@192.168.1.1:/etc/config/
scp firmware/hotplug/* root@192.168.1.1:/etc/hotplug.d/usb/
scp firmware/init/* root@192.168.1.1:/etc/init.d/
scp firmware/button/* root@192.168.1.1:/etc/rc.button/
ssh root@192.168.1.1 "chmod +x /usr/bin/qberd /usr/bin/ledctl /usr/bin/lockdownctl && /etc/init.d/qberd enable && /etc/init.d/qberd start"
```
