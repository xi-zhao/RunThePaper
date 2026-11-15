"""Run fixed-condition panels and complete parameter sweeps with the paper model."""

import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import birth, error_ssim, phase
from paper_filter import simulate


def inputs(protocol, name):
    data = protocol["fields"][name]
    xy = np.asarray(data["locations"])
    distance2 = np.sum((xy[:, None, :] - xy[None, :, :]) ** 2, axis=-1)
    if name == "ion":
        with np.load("config/binary_data.npz", allow_pickle=False) as source:
            bank = source["binary_data"]
        truth = phase(bank.mean(axis=1))
    else:
        truth = np.asarray(data["truth"])
        bank = np.empty((len(truth), 0), dtype=np.uint8)
    return data, distance2, truth, bank


def naive(rng, truth, bank, budget, shots):
    n = len(truth)
    if budget < n:
        locations, each = rng.choice(n, budget, replace=False), shots
    else:
        locations, each = np.arange(n), budget * shots // n
    estimate = np.full(n, rng.uniform(0, np.pi))
    for i in locations:
        if bank.shape[1]:
            proportion = rng.choice(bank[i], each, replace=False).mean()
        else:
            proportion = rng.binomial(each, birth(truth[i])) / each
        estimate[i] = phase(proportion)
    return estimate


def panel(field, kind, protocol, pairs, ntrials):
    data, distance2, truth, bank = inputs(protocol, field)
    budgets = data["budgets"]
    cases = data["tuned"] if kind != "fixed" else [data["fixed"]] * len(budgets)
    shots = int(kind.removeprefix("parallel")) if kind.startswith("parallel") else 1
    rows = []
    for budget, index in zip(budgets, cases):
        maps, nulls = [], []
        for trial in range(ntrials):
            seed = 1910000 + 100 * budget + trial
            estimate, route, null = simulate(distance2, truth, bank, budget, shots, pairs[index], seed)
            baseline = naive(np.random.default_rng(seed + 250000), truth, bank, budget, shots)
            if trial == 0:
                example = dict(path=route.tolist(), nmqa=estimate.tolist(), naive=baseline.tolist())
            maps.append((estimate.tolist(), baseline.tolist()))
            nulls.append(null)
        rows.append(dict(budget=budget, shots_per_iteration=shots, lambda_index=index,
                         pair=pairs[index].tolist(), maps=maps, null_alpha=nulls, example=example))
    return dict(field=field, kind=kind, truth=truth.tolist(), rows=rows)


def sweep(field, protocol, pairs, ntrials):
    data, distance2, truth, bank = inputs(protocol, field)
    values = np.r_[pairs, [[0.0, 0.0]]]
    loss = np.empty((len(data["sweep"]), len(values), ntrials, 3))
    null = np.empty(loss.shape[:-1], dtype=np.uint16)
    archival_const = 1e-5 if field == "ion" else 0.001
    for i, budget in enumerate(data["sweep"]):
        for j, pair in enumerate(values):
            maps = np.empty((ntrials, len(truth)))
            for trial in range(ntrials):
                seed = 1920000 + 100 * budget + trial
                maps[trial], _, null[i, j, trial] = simulate(
                    distance2, truth, bank, budget, 1, pair, seed,
                )
            loss[i, j, :, 0] = error_ssim(maps, truth)
            loss[i, j, :, 1] = error_ssim(maps, truth, True, archival_const)
            loss[i, j, :, 2] = np.sqrt(np.mean((maps - truth) ** 2, axis=1)) / np.pi
            if j % 50 == 0:
                print(field, budget, f"{j + 1}/{len(values)}", flush=True)
    return dict(budgets=data["sweep"], pairs=values, loss=loss, null_alpha=null)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage")
    args = parser.parse_args()
    protocol = json.loads(Path("config/paper-grid.json").read_text())
    pairs = np.asarray(json.loads(Path("config/lambda.json").read_text())["pairs"])
    assert pairs.shape == (250, 2)
    if args.stage == "panels":
        panels = [(f, k) for f in protocol["fields"] for k in ("tuned", "fixed")]
        panels.extend(("square", f"parallel{n}") for n in (2, 10, 15, 50))
        data = {}
        for field, kind in panels:
            key = f"{field}-{kind}"
            data[key] = panel(field, kind, protocol, pairs, 50)
            print(key, "complete", flush=True)
        Path("results/paper-panels.json").write_text(json.dumps(data, allow_nan=False) + "\n")
    else:
        result = sweep(args.stage, protocol, pairs, 50)
        np.savez_compressed(f"results/paper-sweep-{args.stage}.npz", **result)


if __name__ == "__main__":
    main()
