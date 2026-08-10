"""Independent resource-bound reproduction for qDRIFT."""

from .model import (
    Molecule,
    first_order_gate_count,
    higher_order_gate_count,
    phase_estimation_counts,
    qdrift_gate_count,
    suzuki_gate_count,
)

__all__ = [
    "Molecule",
    "first_order_gate_count",
    "higher_order_gate_count",
    "phase_estimation_counts",
    "qdrift_gate_count",
    "suzuki_gate_count",
]
