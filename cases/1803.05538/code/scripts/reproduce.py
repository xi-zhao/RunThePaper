"""Generate all frozen QC31 figure inputs without author result data."""

import json
from pathlib import Path
import warnings

import numpy as np

from filters import window_figures
from spectra import all_spectra


def unpack(value):
    if isinstance(value,np.ndarray):
        return value.tolist()
    if isinstance(value,np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    with warnings.catch_warnings():
        # macOS BLAS can leave sticky exception flags even for bounded finite
        # matrix products. Serialization below rejects any nonfinite value.
        warnings.filterwarnings("ignore",message=".*encountered in matmul",category=RuntimeWarning,module="spectra")
        result={**window_figures(),**all_spectra(382031)}
    output=Path("results/model.json")
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, default=unpack, allow_nan=False, separators=(",",":"))+"\n")


if __name__=="__main__":
    main()

