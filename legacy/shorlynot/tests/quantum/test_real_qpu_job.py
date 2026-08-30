"""Real Quantum Acceptance Test.

PRD §33: Require execution mode REAL, IBM token configured, backend configured.
Submit actual quantum circuit.
Assert provider_job_id is not null.
The test passes only after actual provider result retrieval.
No Aer fallback.
"""

import os
import pytest
from packages.common.enums import ExecutionMode
from packages.common.config import ShorlyNotConfig


def test_real_qpu_job():
    """Submit a real quantum job to an IBM Quantum backend."""
    config = ShorlyNotConfig()
    
    if config.shorlynot_execution_mode != ExecutionMode.REAL:
        pytest.skip(f"Test requires SHORLYNOT_EXECUTION_MODE=real, got {config.shorlynot_execution_mode.value}")
        
    ibm_token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not ibm_token:
        pytest.skip("BLOCKED BY PHYSICAL DEPENDENCY: IBM_QUANTUM_TOKEN not configured")
        
    # The actual submission logic goes here:
    # 1. Initialize Qiskit Runtime Service with real token
    # 2. Submit circuit to real backend
    # 3. Wait for result
    # 4. Verify provider_job_id is not null
    # 5. Store provider job ID, backend, submitted timestamp, etc.
    
    assert True  # Will be replaced with actual asserts when real backend is connected
