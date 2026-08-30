"""
BB84 vs B92 vs E91 — Protocol Comparison
==========================================

Compares three QKD protocols:
- BB84: 4 states, 2 bases (our primary protocol)
- B92: 2 states, simpler but less efficient
- E91: Entanglement-based, requires Bell pairs

Metrics:
- QBER without Eve (should be low)
- QBER with Eve (should be ~25%)
- Efficiency (sifted bits / total bits)
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Add parent dir to path so we can import quantum_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quantum_engine.bb84_simulator import run_bb84_session
from quantum_engine.b92 import run_b92_session
from quantum_engine.e91 import run_e91_session

print("Running protocol comparison...")
print("This may take a few minutes.\n")

# Run each protocol 20 times (with and without Eve)
protocols = {
    "BB84": run_bb84_session,
    "B92": run_b92_session,
    "E91": run_e91_session,
}

results = {}

for name, func in protocols.items():
    print(f"Testing {name}...")
    
    # Without Eve
    secure_qbers = []
    secure_efficiencies = []
    for _ in range(20):
        if name == "E91":
            result = func(num_pairs=256, eve=False)
        else:
            result = func(num_bits=256, eve=False)
        secure_qbers.append(result["qber"])
        if "efficiency" in result:
            secure_efficiencies.append(result["efficiency"])
        elif "sifted_key_length" in result:
            secure_efficiencies.append(result["sifted_key_length"] / 256)
        else:
            secure_efficiencies.append(0.5)
    
    # With Eve
    eve_qbers = []
    for _ in range(20):
        if name == "E91":
            result = func(num_pairs=256, eve=True)
        else:
            result = func(num_bits=256, eve=True)
        eve_qbers.append(result["qber"])
    
    results[name] = {
        "secure_qber_mean": sum(secure_qbers) / len(secure_qbers),
        "secure_qber_std": float(np.std(secure_qbers)),
        "eve_qber_mean": sum(eve_qbers) / len(eve_qbers),
        "eve_qber_std": float(np.std(eve_qbers)),
        "efficiency": sum(secure_efficiencies) / len(secure_efficiencies),
    }
    
    print(f"  Secure QBER: {results[name]['secure_qber_mean']:.2%} ± {results[name]['secure_qber_std']:.2%}")
    print(f"  Eve QBER:    {results[name]['eve_qber_mean']:.2%} ± {results[name]['eve_qber_std']:.2%}")
    print(f"  Efficiency:  {results[name]['efficiency']:.2%}\n")

# Plotting the results
labels = list(results.keys())
secure_means = [results[n]['secure_qber_mean'] * 100 for n in labels]
eve_means = [results[n]['eve_qber_mean'] * 100 for n in labels]
efficiencies = [results[n]['efficiency'] * 100 for n in labels]

x = np.arange(len(labels))
width = 0.25

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width, secure_means, width, label='Secure QBER (%)', color='green')
rects2 = ax.bar(x, eve_means, width, label='Eve QBER (%)', color='red')
rects3 = ax.bar(x + width, efficiencies, width, label='Efficiency (%)', color='blue')

ax.set_ylabel('Percentage (%)')
ax.set_title('QKD Protocol Comparison (BB84 vs B92 vs E91)')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
ax.set_ylim(0, 100)

# Add horizontal line for 11% threshold
ax.axhline(y=11, color='r', linestyle='--', alpha=0.5, label='11% Threshold')

fig.tight_layout()
os.makedirs("analysis", exist_ok=True)
plt.savefig("analysis/protocol_comparison.png")
print("Saved comparison chart to analysis/protocol_comparison.png")
