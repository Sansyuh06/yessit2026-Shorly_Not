"""
ShorlyNot-QDS-T1 Quantum Digital Signature package.
"""

# Lazy imports to avoid circular dependency with engines
from shorlynot_skeleton.qds.encoding import PauliEncoding
from shorlynot_skeleton.qds.pauli import PauliCorrections

__all__ = ["PauliEncoding", "PauliCorrections", "QdsT1Protocol"]


def __getattr__(name):
    if name == "QdsT1Protocol":
        from shorlynot_skeleton.qds.protocol import QdsT1Protocol
        return QdsT1Protocol
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
