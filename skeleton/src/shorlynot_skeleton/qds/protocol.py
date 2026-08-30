"""
ShorlyNot-QDS-T1 Protocol Implementation.
Teleportation Profile T1 (MVP) for SIH 2026 PS 26141.
Normative specification from PRD §3 and MODEL.md.
"""

import time
import uuid
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from shorlynot_skeleton.models import SignatureBundle, VerifyResult, QuantumBackend, QuantumEngine
from shorlynot_skeleton.qds.encoding import PauliEncoding
from shorlynot_skeleton.engines.qiskit_aer import QiskitAerEngine


class QdsT1Protocol:
    """
    ShorlyNot-QDS-T1 Protocol Manager.
    Performs quantum digital signature generation and verification using Bell-state teleportation
    and Pauli eigenstate projective measurements.
    """

    def __init__(self, p0: float = 0.02, default_delta: float = 0.01):
        self.p0 = p0
        self.default_delta = default_delta
        self.engine = QiskitAerEngine(p0=p0)

    def sign(
        self,
        payload_hash: str,
        key_id: str,
        bases: Optional[List[int]] = None,
        n_checks: int = 64,
        L: int = 128,
        backend: QuantumBackend = QuantumBackend.SIM,
        nonce: Optional[str] = None
    ) -> SignatureBundle:
        """
        Sign a payload hash using ShorlyNot-QDS-T1 teleportation-based protocol.
        """
        t_start = time.perf_counter()
        
        # 1. Derive payload bits
        bits = PauliEncoding.derive_payload_bits(payload_hash, length=L)
        
        # 2. Select bases for all L positions (0 = Z basis, 1 = X basis)
        if bases is None:
            bases = [int(np.random.randint(0, 2)) for _ in range(L)]
        else:
            if len(bases) < L:
                bases = bases + [int(np.random.randint(0, 2)) for _ in range(L - len(bases))]
            bases = bases[:L]

        # 3. Nonce generation
        tx_nonce = nonce or str(uuid.uuid4())

        # 4. Perform Bell measurements on check positions
        syndromes = [
            list(self.engine.generate_bell_measurement())
            for _ in range(n_checks)
        ]

        t_end = time.perf_counter()
        telemetry = {
            "sign_latency_ms": round((t_end - t_start) * 1000, 3),
            "check_positions": n_checks,
            "bell_pair_type": "Phi+",
            "state_preparation": "Pauli-Eigenstates",
            "alice_bell_measurements": [list(s) for s in syndromes]
        }

        bundle = SignatureBundle(
            payload_hash=payload_hash,
            key_id=key_id,
            nonce=tx_nonce,
            profile="T1",
            bases=bases,
            correction_bits=syndromes,
            measurement_transcript=telemetry,
            backend=backend,
            engine=QuantumEngine.QISKIT,
            pqc_mode="aes-gcm-demo",
            n_checks=n_checks,
            L=L
        )

        return bundle

    def verify(
        self,
        bundle: SignatureBundle,
        verifier_id: str = "bob",
        delta: Optional[float] = None,
        p0: Optional[float] = None,
        override_syndromes: Optional[List[List[int]]] = None
    ) -> VerifyResult:
        """
        Verify a ShorlyNot-QDS-T1 signature bundle.
        """
        t_start = time.perf_counter()
        
        noise_floor = p0 if p0 is not None else self.p0
        reject_budget = delta if delta is not None else self.default_delta
        n = bundle.n_checks
        
        # 1. Derive expected payload bits
        expected_bits = PauliEncoding.derive_payload_bits(bundle.payload_hash, length=bundle.L)[:n]
        bases = bundle.bases[:n]
        provided_syndromes = override_syndromes if override_syndromes is not None else bundle.correction_bits[:n]

        # 2. Retrieve actual physical Bell measurement outcomes on shared pairs
        alice_measurements = bundle.measurement_transcript.get("alice_bell_measurements")

        engine = QiskitAerEngine(p0=noise_floor)
        mismatches = 0

        for i in range(n):
            b_exp = expected_bits[i]
            beta = bases[i]
            
            if alice_measurements and i < len(alice_measurements):
                true_syn = tuple(alice_measurements[i])
            else:
                # If unentangled adversary created bundle without Alice's Bell state
                true_syn = (int(np.random.randint(0, 2)), int(np.random.randint(0, 2)))

            prov_syn = tuple(provided_syndromes[i]) if i < len(provided_syndromes) else (0, 0)

            measured_bit = engine.simulate_bob_verification(
                bit=b_exp,
                basis=beta,
                true_syndrome=true_syn,
                provided_syndrome=prov_syn,
                inject_noise=True
            )

            if measured_bit != b_exp:
                mismatches += 1

        mismatch_rate = float(mismatches) / float(n) if n > 0 else 1.0

        # Hoeffding threshold: tau = p0 + sqrt(ln(1/delta) / (2n))
        tau = noise_floor + np.sqrt(np.log(1.0 / reject_budget) / (2.0 * n))
        candidate_accepted = bool(mismatch_rate <= tau)
        t_end = time.perf_counter()

        return VerifyResult(
            candidate_accepted=candidate_accepted,
            mismatch_rate=round(mismatch_rate, 4),
            mismatches=mismatches,
            n_checks=n,
            tau=round(float(tau), 4),
            p0=noise_floor,
            delta=reject_budget,
            profile=bundle.profile,
            backend=bundle.backend.value,
            verification_time_ms=round((t_end - t_start) * 1000, 3)
        )
