"""
ShorlyNot — Attacker Console (Window 3)

Third-user attacker interface for demo judges.
Connects to KMS API and lets a volunteer trigger quantum attacks.
Runs in its own terminal.

Usage:
    python attacker_console.py
    python attacker_console.py --kms http://192.168.1.100:8000
"""

import sys
import argparse
import time

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.markup import escape
except ImportError:
    print("ERROR: rich not installed. Run: pip install rich")
    sys.exit(1)


console = Console()


BANNER = """
[bold cyan]  ╔═══════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]  ║[/bold cyan]   [bold red]ATTACKER CONSOLE[/bold red] — ShorlyNot               [bold cyan]║[/bold cyan]
[bold cyan]  ║[/bold cyan]   [dim]Quantum Channel Interception Toolkit[/dim]               [bold cyan]║[/bold cyan]
[bold cyan]  ╚═══════════════════════════════════════════════════════╝[/bold cyan]
"""

MENU = f"""
  [red]{escape("[1]")}[/red] Intercept-Resend Attack      [dim](raises QBER → ~25%)[/dim]
  [yellow]{escape("[2]")}[/yellow] Sustained Port Exhaustion   [dim](triggers L1→L2)[/dim]
  [red]{escape("[3]")}[/red] Multi-Path Compromise        [dim](triggers L1→L2→L3→L4)[/dim]
  [green]{escape("[4]")}[/green] Stop All Attacks / Reset     [dim](deactivate Eve)[/dim]
  [cyan]{escape("[5]")}[/cyan] Show Current Status          [dim](query KMS)[/dim]
  [dim]{escape("[q]")}[/dim] Quit
"""


def safe_api_call(method: str, url: str, **kwargs):
    """Wrap all API calls with consistent error handling."""
    try:
        r = getattr(httpx, method.lower())(
            url, timeout=kwargs.pop("timeout", 10), **kwargs
        )
        r.raise_for_status()
        return r.json() if r.content else {}
    except httpx.ConnectError:
        console.print(f"[bold red]Cannot reach server at {url}[/bold red]")
        return None
    except httpx.TimeoutException:
        console.print(f"[bold red]Request to {url} timed out[/bold red]")
        return None
    except httpx.HTTPStatusError as e:
        console.print(
            f"[bold red]HTTP {e.response.status_code}: {e.response.text}[/bold red]"
        )
        return None
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        return None


def safe_get(url: str, timeout: int = 5):
    return safe_api_call("GET", url, timeout=timeout)


def safe_post(url: str, timeout: int = 5):
    return safe_api_call("POST", url, timeout=timeout)


def show_status(kms_url: str):
    d = safe_get(f"{kms_url}/link_status", timeout=5)
    if not d:
        return

    level = d.get("escalation_level", 0)
    level_colors = {0: "green", 1: "green", 2: "yellow", 3: "red", 4: "bold red"}
    level_labels = {
        0: "L0 — Normal / All Systems Operational",
        1: "L1 — Port Rotation",
        2: "L2 — IP Failover",
        3: "L3 — Interface Switch",
        4: "L4 — EMERGENCY LOCKDOWN",
    }

    table = Table(title="KMS Status", border_style="cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row(
        "Status", f"[{'green' if d['status'] == 'GREEN' else 'red'}]{d['status']}[/]"
    )
    table.add_row("QBER", f"{d.get('qber', 0):.4f}")
    table.add_row(
        "Escalation",
        f"[{level_colors.get(level, 'white')}]{level_labels.get(level, '?')}[/]",
    )
    table.add_row("Port", str(d.get("current_port", "?")))
    table.add_row("IP", str(d.get("current_ip", "?")))
    table.add_row("Network", str(d.get("current_network", "?")))
    table.add_row("Attacks Detected", str(d.get("attacks_detected", 0)))
    table.add_row(
        "Eve Mode",
        "🔴 ACTIVE" if d.get("eve_mode") or d.get("eve_active") else "🟢 OFF",
    )

    console.print(table)


def attack_single(kms_url: str):
    console.print("\n[red]Activating Eve on quantum channel...[/red]")
    if not safe_post(f"{kms_url}/activate_eve", timeout=5):
        return
    console.print("[red]Triggering BB84 intercept-resend attack...[/red]")
    d = safe_post(f"{kms_url}/trigger_attack", timeout=30)
    if not d:
        return
    console.print(f"[red]  ⚠ QBER spike → {d.get('qber', 0):.4f} | Key REFUSED[/red]")
    console.print(f"[yellow]  Escalation: L{d.get('escalation_level', '?')}[/yellow]")
    show_status(kms_url)


def attack_port_exhaust(kms_url: str):
    console.print("\n[yellow]Exhausting all 7 ports...[/yellow]")
    if not safe_post(f"{kms_url}/activate_eve", timeout=5):
        return
    for i in range(8):
        console.print(f"[yellow]  Attack #{i + 1}...[/yellow]", end="")
        d = safe_post(f"{kms_url}/trigger_attack", timeout=30)
        if not d:
            return
        console.print(
            f" QBER={d.get('qber', 0):.4f} | L{d.get('escalation_level', '?')}"
        )
        time.sleep(0.3)
    console.print("[yellow]Port pool exhausted — L2 should be active[/yellow]")
    show_status(kms_url)


def attack_full(kms_url: str):
    console.print(
        "\n[bold red]Initiating multi-path compromise — targeting all escalation levels[/bold red]"
    )
    if not safe_post(f"{kms_url}/activate_eve", timeout=5):
        return
    for i in range(20):
        console.print(f"[red]  Attack #{i + 1}...[/red]", end="")
        d = safe_post(f"{kms_url}/trigger_attack", timeout=30)
        if not d:
            return
        level = d.get("escalation_level", 0)
        label = d.get("escalation_label", "?")
        console.print(f" L{level} ({label}) | QBER={d.get('qber', 0):.4f}")
        if level >= 4:
            console.print(
                "[bold red on white]  *** LOCKDOWN ACHIEVED ***[/bold red on white]"
            )
            break
        time.sleep(0.2)
    show_status(kms_url)


def reset(kms_url: str):
    if safe_post(f"{kms_url}/deactivate_eve", timeout=5) is None:
        return
    if safe_post(f"{kms_url}/reset", timeout=5) is None:
        return
    console.print("[green]Eve deactivated. System reset to GREEN.[/green]")
    show_status(kms_url)


def main():
    parser = argparse.ArgumentParser(description="ShorlyNot Attacker Console")
    parser.add_argument(
        "--kms",
        default="http://localhost:8000",
        help="KMS server URL",
    )
    args = parser.parse_args()
    kms_url = args.kms.rstrip("/")

    console.print(BANNER)
    console.print(f"[dim]  Connected to KMS: {kms_url}[/dim]\n")

    while True:
        console.print(Panel(MENU, title="[red]Attack Menu[/red]", border_style="red"))
        choice = Prompt.ask("[bold]Select[/bold]").strip().lower()

        if choice == "1":
            attack_single(kms_url)
        elif choice == "2":
            attack_port_exhaust(kms_url)
        elif choice == "3":
            attack_full(kms_url)
        elif choice == "4":
            reset(kms_url)
        elif choice == "5":
            show_status(kms_url)
        elif choice == "q":
            console.print("[dim]Exiting attacker console.[/dim]")
            break
        else:
            console.print("[dim]Invalid choice. Try 1-5 or q.[/dim]")


if __name__ == "__main__":
    main()
