"""
QBER Comparison — Secure vs Compromised Channel
=================================================
Generates publication-quality plot for technical report.
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quantum_engine.bb84_simulator import run_bb84_session


def run_comparison(n=50, num_bits=512):
    print(f"Running {n} secure sessions...")
    secure = [run_bb84_session(num_bits=num_bits)["qber"] for _ in range(n)]

    print(f"Running {n} compromised sessions...")
    eve = [run_bb84_session(num_bits=num_bits, eve=True)["qber"] for _ in range(n)]

    return secure, eve


def plot(secure, eve, out="analysis/qber_comparison.png"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("QBER Analysis: Secure vs Compromised", fontsize=14, fontweight="bold")

    # Time series
    sessions = range(1, len(secure) + 1)
    ax1.plot(
        sessions,
        secure,
        "o-",
        color="#10B981",
        markersize=3,
        label="Secure (no Eve)",
        alpha=0.8,
    )
    ax1.plot(
        sessions,
        eve,
        "s-",
        color="#EF4444",
        markersize=3,
        label="Eve active",
        alpha=0.8,
    )
    ax1.axhline(y=0.11, color="red", ls="--", lw=1.5, label="11% Threshold")
    ax1.axhline(y=0.05, color="orange", ls="--", lw=1.5, label="5% Warning")
    ax1.set_xlabel("Session")
    ax1.set_ylabel("QBER")
    ax1.set_ylim(0, 0.40)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Histogram
    bins = np.linspace(0, 0.40, 30)
    ax2.hist(
        secure,
        bins=bins,
        alpha=0.7,
        color="#10B981",
        label=f"Secure (μ={np.mean(secure):.3f})",
    )
    ax2.hist(
        eve, bins=bins, alpha=0.7, color="#EF4444", label=f"Eve (μ={np.mean(eve):.3f})"
    )
    ax2.axvline(x=0.11, color="red", ls="--", lw=2, label="11% threshold")
    ax2.set_xlabel("QBER")
    ax2.set_ylabel("Frequency")
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved: {out}")

    print(f"\n  Secure:   μ={np.mean(secure):.4f}  σ={np.std(secure):.4f}")
    print(f"  Eve:      μ={np.mean(eve):.4f}  σ={np.std(eve):.4f}")
    print(f"  Separation: {np.mean(eve) - np.mean(secure):.4f}")


if __name__ == "__main__":
    s, e = run_comparison()
    plot(s, e)
