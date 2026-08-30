"""
ShorlyNot Smoke Verification Script.
Fails loud if either the Skeleton API (:8000) or Bank/SOC Portal (:8080) is unreachable.
"""

import sys
import time
import httpx

def check_services(skeleton_url="http://127.0.0.1:8000", bank_url="http://127.0.0.1:8080", timeout_sec=15):
    print(f"[*] Verifying services health within {timeout_sec}s...")
    start_time = time.time()
    
    skeleton_ok = False
    bank_ok = False
    
    while time.time() - start_time < timeout_sec:
        # Check Skeleton
        if not skeleton_ok:
            try:
                resp = httpx.get(f"{skeleton_url}/v1/status", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"  [+] Skeleton API is HEALTHY on {skeleton_url} (Version: {data.get('version')}, Protocol: {data.get('protocol')})")
                    skeleton_ok = True
            except Exception:
                pass
                
        # Check Bank
        if not bank_ok:
            try:
                resp = httpx.get(f"{bank_url}/login", timeout=2.0)
                if resp.status_code == 200:
                    print(f"  [+] Bank Customer Portal is HEALTHY on {bank_url}")
                    bank_ok = True
            except Exception:
                pass
                
        if skeleton_ok and bank_ok:
            print("\n[SUCCESS] All ShorlyNot services are operational and responding!")
            return True
            
        time.sleep(1)
        
    print("\n[FAILURE] Smoke check failed! One or more services did not respond in time:")
    if not skeleton_ok:
        print(f"  [-] Skeleton API at {skeleton_url} did not respond.")
    if not bank_ok:
        print(f"  [-] Bank Portal at {bank_url} did not respond.")
        
    return False

if __name__ == "__main__":
    success = check_services()
    if not success:
        sys.exit(1)
    sys.exit(0)
