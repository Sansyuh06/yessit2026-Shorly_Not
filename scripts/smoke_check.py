"""
ShorlyNot Multi-Tier Smoke Verification Script.
Verifies health of:
1. Router Guard & QKD KMS Server (:8000)
2. Skeleton Cryptographic Framework API (:8001)
3. Mock Bank Application & Dark SOC Console (:8081)
"""

import os
import sys
import time
import httpx


def check_services(kms_url=None, skeleton_url=None, bank_url=None, timeout_sec=15):
    if kms_url is None:
        kms_url = os.environ.get("KMS_URL", "http://127.0.0.1:8000")
    if skeleton_url is None:
        skeleton_url = os.environ.get("SHORLYNOT_API_URL", "http://127.0.0.1:8001")
    if bank_url is None:
        bank_url = os.environ.get("SHORLYNOT_BANK_URL", "http://127.0.0.1:8081")

    print(f"[*] Verifying multi-tier ShorlyNot services health within {timeout_sec}s...")
    start_time = time.time()

    kms_ok = False
    skeleton_ok = False
    bank_ok = False

    while time.time() - start_time < timeout_sec:
        # 1. Check Router KMS
        if not kms_ok:
            try:
                resp = httpx.get(f"{kms_url}/link_status", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"  [+] Router QKD KMS is HEALTHY on {kms_url} (Status: {data.get('status')}, QBER: {data.get('qber')}%, Key Rate: {data.get('key_rate')} bps)")
                    kms_ok = True
            except Exception:
                pass

        # 2. Check Skeleton API
        if not skeleton_ok:
            try:
                resp = httpx.get(f"{skeleton_url}/v1/status", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"  [+] Skeleton API is HEALTHY on {skeleton_url} (Version: {data.get('version')}, Protocol: {data.get('protocol')})")
                    skeleton_ok = True
            except Exception:
                pass

        # 3. Check Bank Portal
        if not bank_ok:
            try:
                resp = httpx.get(f"{bank_url}/login", timeout=2.0)
                if resp.status_code == 200:
                    print(f"  [+] Bank Customer Portal & SOC is HEALTHY on {bank_url}")
                    bank_ok = True
            except Exception:
                pass

        if kms_ok and skeleton_ok and bank_ok:
            print("\n[SUCCESS] All 3 ShorlyNot tiers (Router KMS, Skeleton Engine, Bank SOC) are operational!")
            return True

        time.sleep(1)

    # If KMS was not running but Skeleton & Bank are, note it
    if skeleton_ok and bank_ok and not kms_ok:
        print("\n[WARNING] Skeleton API and Bank are healthy, but Router KMS was not responding on :8000.")
        print("  (Bank will use internal hardware simulation fallback for Router Guard).")
        return True

    print("\n[FAILURE] Smoke check failed! One or more critical services did not respond in time:")
    if not kms_ok:
        print(f"  [-] Router KMS at {kms_url} did not respond.")
    if not skeleton_ok:
        print(f"  [-] Skeleton API at {skeleton_url} did not respond.")
    if not bank_ok:
        print(f"  [-] Bank Portal at {bank_url} did not respond.")

    return False


if __name__ == "__main__":
    k_url = sys.argv[1] if len(sys.argv) > 1 else None
    s_url = sys.argv[2] if len(sys.argv) > 2 else None
    b_url = sys.argv[3] if len(sys.argv) > 3 else None
    success = check_services(kms_url=k_url, skeleton_url=s_url, bank_url=b_url)
    if not success:
        sys.exit(1)
    sys.exit(0)
