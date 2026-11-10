"""Recompute the offline single-tone and pulsed filter blocks."""
import json
from pathlib import Path
import numpy as np
from reproduce import pulsed, single_tone

def encode(value):
    return value.tolist() if isinstance(value, np.ndarray) else value.item()

out = {"F1": single_tone(), "F8": pulsed()}
Path("results/independent-filters.json").write_text(
    json.dumps(out, default=encode, allow_nan=False) + "\n", encoding="utf-8")
