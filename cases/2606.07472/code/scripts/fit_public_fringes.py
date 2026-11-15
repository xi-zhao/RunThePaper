"""Profile a shared physical pulse model against all three published center traces."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, least_squares

from exchange import C, TAU, quadrature, schedule


GAMMAS = (0.0, 1.0, .699)
PANELS = ("reference", "net", "quasi")
AMPLITUDE_SCALE_MV = 357.4
LIMITS = ([1., 0., 0., 3.], [40., 50., 100., 180.])


def responses(timing, gamma, repeats=25, order=20):
    """Propagate the within-period response and its geometric prior-period memory."""
    nodes, weights = quadrature(order)
    pieces = schedule(timing, gamma)
    period = sum(timing)
    memory = np.zeros_like(TAU)
    for duration, value in pieces:
        memory = value + (memory - value)*np.exp(-duration / TAU)
    fixed_point = memory / -np.expm1(-period / TAU)
    initial = fixed_point * -np.expm1(-np.arange(repeats)[:, None] * period / TAU)
    trace, durations = [], []
    for duration, value in pieces:
        t = (nodes + 1) * duration / 2
        d = np.exp(-t[:, None] / TAU)
        trace.append(value + np.einsum("ij,kj,j->ik", initial - value, d, C))
        durations.append(weights * duration / 2)
        initial = value + (initial - value)*np.exp(-duration / TAU)
    return np.concatenate(trace, axis=1), np.concatenate(durations)


def integrated(amplitude, scale, voltage, weights):
    scaled = (amplitude[..., None, None] * voltage - AMPLITUDE_SCALE_MV) / scale
    response = np.exp(scaled) * weights
    area = np.cumsum(response.sum(axis=-1), axis=-1)
    return area


def compare(parameters, measured, indices, order=20, exact=False):
    positive, middle, final, scale = parameters
    timing = (positive, middle, positive, final)
    traces = [responses(timing, gamma, order=order) for gamma in GAMMAS]
    vref, wref = traces[0]
    base = float(integrated(measured[0, 0], scale, vref[:1], wref)[0])
    result = []
    for observed, (v, w) in zip(measured, traces):
        if exact:
            roots = [
                brentq(lambda a: integrated(np.asarray(a), scale, v[:n], w)[-1] / n - base,
                       300., 420., xtol=1e-10)
                for n in indices + 1
            ]
            result.append(np.asarray(roots) - observed[indices])
            continue
        v = v[:indices[-1]+1]
        area = integrated(observed[indices], scale, v, w)[np.arange(len(indices)), indices]
        phase = area / (indices + 1) / base
        response = np.exp((observed[indices,None,None] * v - AMPLITUDE_SCALE_MV) / scale) * w
        derivative = np.cumsum(np.sum(response * v, axis=-1), axis=-1)[np.arange(len(indices)), indices] / area / scale
        result.append(np.log(phase) / derivative)
    return np.stack(result)


def solve(measured, train, seed, limits, count=9):
    rng = np.random.default_rng(seed)
    first = np.array([[10, 0, 10, 45], [10, 0, 4, 45], [20, 5, 20, 30]])
    starts = [*first, *rng.uniform([2, 0, 0, 8], [30, 35, 65, 145], size=(count-len(first), 4))]
    trials = []
    for start in starts:
        opt = least_squares(lambda p: compare(p, measured, train).ravel(),
            start, bounds=limits, x_scale=[10, 10, 20, 40], max_nfev=120, ftol=2e-9, xtol=2e-9, gtol=2e-9)
        trial = dict(parameters=opt.x.tolist(), approximate_training_rmse_mv=float(np.sqrt(np.mean(opt.fun**2))),
                     evaluations=opt.nfev, success=bool(opt.success))
        trials.append(trial)
    return trials


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("full", "early", "wide"))
    p.add_argument("output", type=Path)
    args = p.parse_args()
    source = json.loads(Path("reference/figures-table.json").read_text())["fig3"]
    measured = np.array([source[panel]["voltage_mv"] for panel in PANELS])
    assert measured.shape == (3, 25)
    train = np.arange(12 if args.mode == "early" else 25)
    limits = (LIMITS[0], [80., 150., 200., 180.]) if args.mode == "wide" else LIMITS
    trials = solve(measured, train, 260607472+len(train), limits)
    best = min(trials, key=lambda x: x["approximate_training_rmse_mv"])
    residual = compare(best["parameters"], measured, np.arange(25), order=32, exact=True)
    args.output.write_text(json.dumps(dict(mode=args.mode, calibrated_from_panel="reference",
        calibrator_voltage_mv=measured[0,0], train_count=len(train), limits=limits, trials=trials, best=best,
        predicted_mv=(measured+residual).tolist(), residual_mv=residual.tolist()), indent=2, allow_nan=False)+"\n")
    print(args.mode, best, "exact rms", np.sqrt(np.mean(residual**2,axis=1)).tolist(),flush=True)


if __name__ == "__main__":
    main()
