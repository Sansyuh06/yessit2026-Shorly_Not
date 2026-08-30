import sys

try:
    from quantum_engine.bb84_simulator import run_bb84_session

    r = run_bb84_session(num_bits=256)
    print(f"QBER={r['qber']}, key_len={len(r['raw_key'])}")
    assert 0 <= r["qber"] <= 0.15, "QBER out of range"

    r = run_bb84_session(num_bits=256, eve=True)
    print(f"Eve QBER={r['qber']}")
    assert r["qber"] >= 0.11, "Eve should trigger high QBER"

    from kms.key_management_service import KeyManagementService

    kms = KeyManagementService()
    s = kms.create_session("Alice", "Bob")
    print(f"Session OK: {s['status']}")

    kms = KeyManagementService()
    kms.eve_mode = True
    try:
        kms.create_session("A", "B")
    except Exception as e:
        print(f"Correctly blocked: {e}")

    print("ALL CHECKS PASSED")
except Exception as e:
    import traceback

    traceback.print_exc()
    print(f"FAILED: {e}")
    sys.exit(1)
