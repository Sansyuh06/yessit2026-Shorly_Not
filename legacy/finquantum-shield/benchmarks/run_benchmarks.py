"""
Performance Benchmarks — ShorlyNot
============================================
Measures throughput, latency, and scalability.
"""

import time
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantum_engine.bb84_simulator import run_bb84_session
from kms.key_management_service import KeyManagementService


def bench_bb84_throughput():
    print("\n" + "=" * 60)
    print("  BB84 THROUGHPUT BENCHMARK")
    print("=" * 60)

    sizes = [128, 256, 512, 768, 1024]
    results = {}
    for n in sizes:
        start = time.perf_counter()
        run_bb84_session(num_bits=n)
        elapsed = time.perf_counter() - start
        qps = n / elapsed
        results[n] = {"time_s": round(elapsed, 3), "qubits_per_sec": round(qps, 0)}
        print(f"  {n:>5} qubits: {elapsed:.3f}s  ({qps:.0f} qubits/sec)")

    return results


def bench_kms_sessions():
    print("\n" + "=" * 60)
    print("  KMS SESSION CREATION BENCHMARK")
    print("=" * 60)

    kms = KeyManagementService()
    times = []
    for i in range(10):
        start = time.perf_counter()
        try:
            kms.create_session(f"bench_a_{i}", f"bench_b_{i}")
        except:
            pass
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg = sum(times) / len(times)
    p95 = sorted(times)[int(len(times) * 0.95)]
    print(f"  Mean:  {avg * 1000:.1f}ms")
    print(f"  Min:   {min(times) * 1000:.1f}ms")
    print(f"  Max:   {max(times) * 1000:.1f}ms")
    print(f"  P95:   {p95 * 1000:.1f}ms")

    return {"mean_ms": round(avg * 1000, 1), "p95_ms": round(p95 * 1000, 1)}


def bench_encryption():
    print("\n" + "=" * 60)
    print("  AES-256-GCM ENCRYPTION THROUGHPUT")
    print("=" * 60)

    from devices.client import SoldierDevice

    kms = KeyManagementService()
    device = SoldierDevice("bench_device", kms)
    device.request_key()

    msg = "A" * 1024  # 1KB message
    start = time.perf_counter()
    count = 1000
    for _ in range(count):
        device.send_encrypted_message("target", msg)
    elapsed = time.perf_counter() - start

    mps = count / elapsed
    print(f"  {count} messages ({msg.__len__()} bytes each)")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Throughput: {mps:.0f} msg/sec ({mps * 1024 / 1024:.1f} KB/sec)")

    return {"messages_per_sec": round(mps, 0)}


if __name__ == "__main__":
    print("\n ShorlyNot — Performance Benchmarks\n")

    results = {
        "bb84": bench_bb84_throughput(),
        "kms": bench_kms_sessions(),
        "encryption": bench_encryption(),
    }

    # Save results
    os.makedirs("benchmarks/results", exist_ok=True)
    with open("benchmarks/results/latest.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("  [SUCCESS] Benchmarks complete — saved to benchmarks/results/latest.json")
    print("=" * 60 + "\n")
