# ShorlyNot Mock Bank

A mock financial web portal and Security Operations Center (SOC) dashboard that demonstrates application-level security responses to quantum signature verification failures.

## Features

- **Customer Banking Portal**: Demonstrates authenticated transfer requests signed and verified via the Skeleton QDS microservice.
- **Security Operations Console (`/soc`)**: Real-time telemetry feed displaying current mismatch rates ($\hat{p}$), Hoeffding thresholds ($\tau$), active security stages ($S_0 \to S_4$), and buttons to execute simulated attacks.
- **App-Level Stage Enforcement**: Directly rejects transfers and quarantines affected accounts when the threat engine escalates stages, without requiring OS firewall modifications.

## Setup & Running

Ensure the Skeleton API is running on port 8000 first, then:

```bash
cd bank
pip install -r requirements.txt
python -m app.main
```

The bank portal will be available at `http://127.0.0.1:8080`.

## Test Accounts

| Username | Password | Role |
|---|---|---|
| `alice` | `alice123` | Sender account |
| `bob` | `bob123` | Receiver account |
| `carol` | `carol123` | Third-party customer |
| `eve` | `eve123` | Attacker account |
| `ops` | `ops123` | SOC operations officer |

## OpenWrt Router Guard & Hardware Telemetry

The SOC console (`/soc`) integrates with a physical or simulated TP-Link Archer C6 OpenWrt router (`192.168.1.1`):
- **Live Netfilter Guard**: Injects dynamic `nftables` forward rules based on link quality.
- **Link States**:
  - `GREEN` (QBER < 5%): Normal transmission, full relay bandwidth on port `8765`.
  - `YELLOW` (QBER 5–11%): Elevated channel noise, audit rate-limiting triggered.
  - `RED` (QBER > 11%): Channel compromised, netfilter severs packet relay forward chain.
- **Feed Search & Filter Tags**: Real-time filtering by category (`ALL`, `THREATS`, `FORGERY`, `REPLAY`, `CHANNEL`, `ROUTER GUARD`) with instant client-side text search.

