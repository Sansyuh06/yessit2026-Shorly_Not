"""Critical verification test — must pass both assertions."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum_engine.bb84_simulator import run_bb84_session, privacy_amplification

print("=" * 60)
print("  FinQuantum Shield — Critical Verification")
print("=" * 60)

# Test 1: Clean channel
print("\n[1] Clean channel (no Eve)...")
r = run_bb84_session(eve=False)
print(f"    QBER = {r['qber']:.4f}")
assert r["qber"] < 0.11, f"FAIL: Clean channel QBER too high: {r['qber']}"
print("    ✓ PASS")

# Test 2: Eve present
print("\n[2] Eve intercept-resend...")
r2 = run_bb84_session(eve=True)
print(f"    QBER = {r2['qber']:.4f}")
assert r2["qber"] > 0.11, f"FAIL: Eve not detected: {r2['qber']}"
print("    ✓ PASS")

# Test 3: Privacy amplification
print("\n[3] Privacy amplification...")
r3 = run_bb84_session(num_bits=768, eve=False)
amp = privacy_amplification(r3["sifted_bits"], output_bits=256)
assert len(amp) == 32
print(f"    Amplified key: {amp.hex()[:32]}... ({len(amp)} bytes)")
print("    ✓ PASS")

# Test 4: KMS integration
print("\n[4] KMS create_session (with privacy amplification)...")
from kms.key_management_service import KeyManagementService
kms = KeyManagementService()
session = kms.create_session("Bank_HQ", "Branch_001")
print(f"    Session: {session['session_id'][:12]}...")
print(f"    QBER: {session['qber']:.4f}")
print(f"    Key: {session['key_hex'][:16]}...")
assert session["qber"] < 0.11
assert len(session["key_hex"]) == 64  # 256-bit key = 32 bytes = 64 hex chars
print("    ✓ PASS")

# Test 5: KMS attack detection
print("\n[5] KMS trigger_attack...")
result = kms.trigger_attack()
assert result["status"] == "RED"
print(f"    Status: {result['status']} | QBER: {result['qber']:.4f}")
print("    ✓ PASS")

# Test 6: Compat wrapper
print("\n[6] simulate_bb84 compat wrapper...")
from quantum_engine.bb84_simulator import simulate_bb84, QBER_SECURITY_THRESHOLD
assert QBER_SECURITY_THRESHOLD == 0.11
key, qber, det = simulate_bb84(num_bits=256, eve_present=False)
assert len(key) == 32
print(f"    Key: {key.hex()[:16]}... QBER={qber:.4f}")
print("    ✓ PASS")

# Test 7: KMS server import
print("\n[7] KMS server import check...")
from kms.kms_server import app as kms_app
print("    kms.kms_server imports OK")
print("    ✓ PASS")

print("\n" + "=" * 60)
print("  ALL CRITICAL CHECKS PASSED ✓")
print("=" * 60)
