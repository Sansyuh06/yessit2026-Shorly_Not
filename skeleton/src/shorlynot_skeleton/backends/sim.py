"""
Quantum execution backends for ShorlyNot:
1. SimBackend (default simulation with Aer and noise modeling)
2. IBMBackend (IBM Quantum runtime adapter with honest fallback)
"""

import os
from typing import Dict, Any, Optional
from shorlynot_skeleton.models import QuantumBackend
from shorlynot_skeleton.engines.qiskit_aer import QiskitAerEngine


class SimBackend:
    """
    Default simulation backend running locally on Qiskit Aer.
    """
    def __init__(self, p0: float = 0.02):
        self.p0 = p0
        self.engine = QiskitAerEngine(p0=p0)
        self.name = QuantumBackend.SIM

    def get_status(self) -> Dict[str, Any]:
        return {
            "backend": QuantumBackend.SIM.value,
            "status": "online",
            "p0": self.p0,
            "simulator": "Qiskit Aer Simulator",
            "qiskit_version": "2.x",
            "hardware_type": "classical-quantum-simulator"
        }


class IBMBackend:
    """
    IBM Quantum hardware backend.
    Checks IBM_QUANTUM_TOKEN environment variable.
    Gracefully and honestly reports unavailable if token is missing.
    Never pretends Aer is IBM.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("IBM_QUANTUM_TOKEN")
        self.name = QuantumBackend.IBM
        self._service = None
        self._initialize()

    def _initialize(self):
        if not self.token:
            return
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            self._service = QiskitRuntimeService(channel="ibm_quantum", token=self.token)
        except Exception:
            self._service = None

    def is_available(self) -> bool:
        return self._service is not None

    def get_status(self) -> Dict[str, Any]:
        if self.is_available():
            return {
                "backend": QuantumBackend.IBM.value,
                "status": "online",
                "hardware_type": "IBM Quantum QPU",
                "service": "Qiskit Runtime Service",
                "token_configured": True
            }
        else:
            return {
                "backend": QuantumBackend.IBM.value,
                "status": "unavailable",
                "reason": "IBM_QUANTUM_TOKEN not configured or IBM Runtime service unreachable",
                "token_configured": bool(self.token),
                "fallback": "sim"
            }
