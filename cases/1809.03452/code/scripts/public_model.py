"""Independent rectangular-pulse benchmark and exact Bell-state control."""
import json
from pathlib import Path
import numpy as np
from reproduce import outcomes, response, simulate

dt = 1e-6
frequency = np.r_[0.0, np.logspace(0, 6, 601)]
pulse = np.full(10, np.pi/(10*dt), dtype=complex)
filter_values = response(pulse, dt, frequency)
bell = [
    {"name":"u2", "qubits":[0], "params":[0, np.pi]},
    {"name":"cx", "qubits":[0, 1]},
    {"name":"measure", "qubits":[0, 1], "memory":[0, 1]},
]
out = {
    "frequency_hz": frequency.tolist(),
    "dephasing": (4*filter_values[0]).tolist(),
    "amplitude": filter_values[1].tolist(),
    "bell_probabilities": outcomes(simulate(bell, 2)),
}
Path("results/independent-pulse.json").write_text(json.dumps(out, allow_nan=False) + "\n", encoding="utf-8")
