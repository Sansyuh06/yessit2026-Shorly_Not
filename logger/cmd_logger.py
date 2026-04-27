"""
FinQuantum Shield — CMD Event Logger (Window 2)

Connects to ws://localhost:8000/ws/events and prints every event
to terminal with color coding using Rich.

Usage:
    python logger/cmd_logger.py
    python logger/cmd_logger.py --url ws://192.168.1.100:8000/ws/events
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    print("ERROR: rich not installed. Run: pip install rich")
    sys.exit(1)


console = Console()

COLORS = {
    "session":    "cyan",
    "attack":     "bold red",
    "escalation": "yellow",
    "lockdown":   "bold red on white",
    "transaction": "white",
    "heartbeat":  "dim green",
    "key":        "green",
}

BANNER = """[bold cyan]
  ╔═══════════════════════════════════════════════════╗
  ║   FinQuantum Shield — CMD Event Logger            ║
  ║   Real-time quantum security event monitor         ║
  ╚═══════════════════════════════════════════════════╝
[/bold cyan]"""


async def listen(uri: str):
    console.print(BANNER)
    console.print(f"[dim]Connecting to {uri}...[/dim]")

    reconnect_delay = 1
    while True:
        try:
            async with websockets.connect(uri) as ws:
                reconnect_delay = 1
                console.print("[green]✓ CMD Logger connected — watching all events[/green]\n")

                async for raw in ws:
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    ts = event.get("timestamp", datetime.utcnow().isoformat())[:19]
                    ev_type = event.get("event", "unknown")
                    color = COLORS.get(ev_type, "white")

                    # Format based on event type
                    if ev_type == "session":
                        action = event.get("action", "")
                        if action == "system_reset":
                            msg = f"[{ts}] [SYSTEM ] System reset → GREEN"
                        elif action == "eve_deactivated":
                            msg = f"[{ts}] [SYSTEM ] Eve deactivated — channel clear"
                        else:
                            sid = event.get("session_id", "")
                            if isinstance(sid, str) and len(sid) > 8:
                                sid = sid[:8]
                            msg = (
                                f"[{ts}] [QUANTUM] BB84 session {sid} | "
                                f"QBER={event.get('qber', 0):.4f} | "
                                f"Status={event.get('status', '?')}"
                            )
                    elif ev_type == "attack":
                        qber = event.get("qber", 0)
                        if isinstance(qber, (int, float)):
                            msg = (
                                f"[{ts}] [ATTACK ] ⚠ Eve detected! "
                                f"QBER={qber:.4f} | Key REFUSED"
                            )
                        else:
                            msg = f"[{ts}] [ATTACK ] ⚠ Eve activated on quantum channel"
                    elif ev_type == "escalation":
                        level = event.get("level", 0)
                        labels = {
                            1: "Port Rotation",
                            2: "IP Failover",
                            3: "Interface Switch",
                            4: "LOCKDOWN",
                        }
                        action = event.get("action", labels.get(level, ""))
                        msg = (
                            f"[{ts}] [ESCALAT] LEVEL {level} — {action} | "
                            f"Port={event.get('port')} | "
                            f"IP={event.get('ip')}"
                        )
                    elif ev_type == "lockdown":
                        msg = (
                            f"[{ts}] [LOCKDWN] *** EMERGENCY LOCKDOWN *** "
                            f"All interfaces down"
                        )
                        color = "bold red on white"
                    elif ev_type == "key":
                        msg = (
                            f"[{ts}] [CRYPTO ] AES key derived | "
                            f"HKDF-SHA256 | "
                            f"key={event.get('key_preview', '??')}..."
                        )
                    elif ev_type == "transaction":
                        amount = event.get("amount", 0)
                        msg = (
                            f"[{ts}] [TX     ] ₹{amount:,.2f} | "
                            f"{event.get('from','?')} → {event.get('to','?')} | "
                            f"QBER={event.get('qber',0):.4f} | "
                            f"Payload={event.get('encrypted_preview','??')}"
                        )
                        color = "white"
                    else:
                        msg = (
                            f"[{ts}] [{ev_type.upper()[:7]:7s}] "
                            f"{json.dumps(event)[:100]}"
                        )

                    console.print(f"[{color}]{msg}[/{color}]")

        except (ConnectionRefusedError, OSError):
            console.print(
                f"[dim red]Connection failed. Retrying in {reconnect_delay}s...[/dim red]"
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 10)
        except KeyboardInterrupt:
            console.print("\n[dim]Logger stopped.[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}. Reconnecting...[/red]")
            await asyncio.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="FinQuantum CMD Logger")
    parser.add_argument(
        "--url",
        default="ws://localhost:8000/ws/events",
        help="WebSocket URL to connect to",
    )
    args = parser.parse_args()
    asyncio.run(listen(args.url))


if __name__ == "__main__":
    main()
