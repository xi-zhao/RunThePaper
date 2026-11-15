"""Read only the numeric NumPy dictionaries in the author ZIP."""
from pathlib import Path
import pickle
import numpy as np


class NumericReader(pickle.Unpickler):
    def find_class(self,module,name):
        if module=="numpy" and name in {"ndarray","dtype"}:
            return getattr(np,name)
        if module in {"numpy.core.multiarray","numpy._core.multiarray"} and name in {"_reconstruct","scalar"}:
            from numpy._core import multiarray
            return getattr(multiarray,name)
        raise pickle.UnpicklingError(f"Unexpected pickle global {module}.{name}")

    def persistent_load(self,pid):
        raise pickle.UnpicklingError("Persistent references are not supported")


def load(path):
    with Path(path).open("rb") as stream:
        return NumericReader(stream).load()
