"""Calculate the centered, normalized lag panel on the full source grid."""

import json
from pathlib import Path

import numpy as np

from physical import error_vectors


def main():
    rng = np.random.default_rng(1072701)
    n = 1000
    length = np.linalg.norm([error_vectors(k, "primitive", 0)[0] for k in range(24)], axis=1)
    gate = length[rng.integers(24, size=n)]
    lags = np.arange(101)
    data = []
    for block in range(1, 101):
        noise = np.abs(rng.normal(size=(200, (n+block-1)//block)))
        signal = np.repeat(noise, block, axis=1)[:, :n]*gate
        signal -= signal.mean(axis=1, keepdims=True)
        spec = np.fft.rfft(signal, n=2048, axis=1)
        corr = np.fft.irfft(abs(spec)**2, axis=1)[:, :101] / (n-lags)
        data.append((corr/corr[:, :1]).mean(axis=0).tolist())
    out = dict(blocks=list(range(1, 101)), lags=lags.tolist(), centered_acf=data,
               gates=n, repetitions=200, seed=1072701)
    Path("results/autocorrelation.json").write_text(json.dumps(out, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
