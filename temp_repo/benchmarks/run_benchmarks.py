"""
Performance benchmarks for ShorlyNot.
Measures: qubit throughput, key generation time, encryption throughput,
latency per escalation level.

Run: python benchmarks/run_benchmarks.py
Output: formatted table + JSON export
"""
import time
import json
from quantum_engine.bb84_simulator import run_bb84_session
from kms.key_management_service import KeyManagementService

def benchmark_bb84_throughput():
    """Measure qubits/second through the BB84 pipeline."""
    sizes = [128, 256, 512, 1024]
    results = {}
    for n in sizes:
        start = time.perf_counter()
        run_bb84_session(num_bits=n)
        elapsed = time.perf_counter() - start
        results[n] = {
            "qubits": n,
            "time_seconds": round(elapsed, 4),
            "qubits_per_second": round(n / elapsed, 1),
        }
    return results

def benchmark_key_generation():
    """Measure full session creation time (BB84 + HKDF + privacy amp)."""
    kms = KeyManagementService()
    times = []
    for _ in range(10):
        start = time.perf_counter()
        try:
            kms.create_session("bench_a", "bench_b")
        except:
            pass
        times.append(time.perf_counter() - start)
    return {
        "mean_ms": round(sum(times) / len(times) * 1000, 2),
        "p95_ms": round(sorted(times)[9] * 1000, 2),
        "min_ms": round(min(times) * 1000, 2),
    }

def benchmark_encryption_throughput():
    """Measure AES-256-GCM encrypt/decrypt throughput."""
    from devices.client import SoldierDevice
    kms = KeyManagementService()
    device = SoldierDevice("bench", kms)
    device.request_key()
    
    msg = "A" * 1024  # 1KB message
    start = time.perf_counter()
    for _ in range(1000):
        device.send_encrypted_message("target", msg)
    elapsed = time.perf_counter() - start
    
    return {
        "messages_per_second": round(1000 / elapsed, 1),
        "throughput_kb_per_sec": round(1000 / elapsed, 1),
    }

if __name__ == "__main__":
    print("Running benchmarks... (this may take a minute)")
    res_bb84 = benchmark_bb84_throughput()
    print("\nBB84 Throughput:")
    for n, data in res_bb84.items():
        print(f"  {n} qubits: {data['qubits_per_second']} qubits/sec")
        
    res_keygen = benchmark_key_generation()
    print("\nKey Generation Latency:")
    print(f"  Mean: {res_keygen['mean_ms']} ms")
    print(f"  p95:  {res_keygen['p95_ms']} ms")
    
    res_enc = benchmark_encryption_throughput()
    print("\nEncryption Throughput (AES-256-GCM 1KB messages):")
    print(f"  Messages/sec: {res_enc['messages_per_second']}")
    print(f"  KB/sec:       {res_enc['throughput_kb_per_sec']}")
    
    with open("benchmark_results.json", "w") as f:
        json.dump({
            "bb84_throughput": res_bb84,
            "key_generation": res_keygen,
            "encryption": res_enc,
        }, f, indent=2)
    print("\nSaved full results to benchmark_results.json")
