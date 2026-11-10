"""Recalculate held-out NMQA and uniform-mapping trials using frozen tuning."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import mkdtemp

import numpy as np

from metrics import birth, crossover, error_ssim, phase
from paper_filter import simulate

PARAMETERS = Path(__file__).resolve().parents[1] / "parameters.json"
LABELS_SHA256 = "0a4a5acc8ca31a93879caf4e1cc3364d0eaca95f98ea949ac04d97e88e3fcab2"


def published_labels(path):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != LABELS_SHA256:
            raise ValueError("Expected the pinned rf_fulldata_ramsey.npz from the authors")
    with np.load(path, allow_pickle=False) as data:
        return data["binary_data"].astype(np.uint8)


def naive(rng, truth, bank, budget, shots):
    """Uniform allocation and an uninformative estimate for unmeasured sites."""
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


def main():
    conditions = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", choices=conditions, default="square")
    parser.add_argument("--tuning", choices=("retuned", "published"), default="retuned")
    parser.add_argument("--labels-file", type=Path, help="Pinned authors' NPZ required for the ion field")
    parser.add_argument("--output", type=Path, help="New output directory")
    args = parser.parse_args()
    if (args.field == "ion") != (args.labels_file is not None):
        parser.error("--labels-file is required for the ion field only")
    data = conditions[args.field]
    xy = np.asarray(data["locations"])
    distance2 = np.sum((xy[:, None, :] - xy[None, :, :]) ** 2, axis=-1)
    if args.labels_file is None:
        truth = np.asarray(data["synthetic_truth_rad"])
        bank = np.empty((len(truth), 0), dtype=np.uint8)
    else:
        bank = published_labels(args.labels_file)
        truth = phase(bank.mean(axis=1))
    rows = []
    for setting in data["settings"]:
        budget = setting["budget"]
        shots = setting["shots_per_iteration"]
        pair = np.asarray(setting[f"{args.tuning}_pair"])
        maps, null_counts = [], []
        for trial in range(50):
            seed = 1910000 + 100 * budget + trial
            estimate, _, null_count = simulate(distance2, truth, bank, budget, shots, pair, seed)
            baseline = naive(np.random.default_rng(seed + 250000), truth, bank, budget, shots)
            maps.append([estimate.tolist(), baseline.tolist()])
            null_counts.append(int(null_count))
        rows.append(dict(budget=budget, shots_per_iteration=shots, pair=pair.tolist(),
                         maps=maps, null_alpha=null_counts))
    budgets = np.array([row["budget"] for row in rows])
    mean_loss = error_ssim(np.asarray([row["maps"] for row in rows]), truth).mean(axis=1)
    low = 0.01 if args.field == "ion" or args.field.startswith("parallel") else 0.05
    thresholds = np.linspace(low, 0.6, round((0.6 - low) * 1000) + 1)
    ratio, observed = crossover(budgets, mean_loss, thresholds)
    peak = float(ratio[observed].max()) if observed.any() else None
    result = dict(field=args.field, tuning=args.tuning, truth=truth.tolist(), rows=rows,
                  mean_ssim_error=mean_loss.tolist(), peak_budget_ratio=peak)
    if args.output is None:
        output = Path(mkdtemp(prefix="qc28-rerun-"))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    path = output / "recalculation.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Peak budget ratio {peak}. Wrote {path}")


if __name__ == "__main__":
    main()
