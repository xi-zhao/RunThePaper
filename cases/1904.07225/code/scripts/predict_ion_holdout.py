"""Use disjoint records for mapping six ions and testing the predicted readout."""
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_filter import simulate
from paper_scan import naive


GROUPS = 51
FRAMES = 500
FOLDS = 3
TRIALS = 128
LAMBDA = (0.95, 0.99)
BASE_SEED = 2802026


def main():
    with np.load("config/binary_data.npz", allow_pickle=False) as archive:
        source = archive["binary_data"]
    if source.shape != (6, GROUPS * FRAMES) or np.any((source != 0) & (source != 1)):
        raise ValueError("Expected the six-ion archive with 51 blocks of 500 binary readouts")
    groups = source.reshape(6, GROUPS, FRAMES)
    protocol = json.loads(Path("config/paper-grid.json").read_bytes())["fields"]["ion"]
    budgets = np.asarray(protocol["budgets"])
    if np.any((budgets >= 6) & (budgets % 6 != 0)):
        raise ValueError("Uniform baseline must use the entire selected budget")
    locations = np.asarray(protocol["locations"])
    squared_distances = ((locations[:, None, :] - locations[None, :, :]) ** 2).sum(axis=-1)
    indices = np.arange(GROUPS)
    test_groups = np.stack((indices.reshape(FOLDS, -1), indices.reshape(-1, FOLDS).T))
    rates = groups.mean(axis=-1)
    shape = (len(test_groups), FOLDS, len(budgets), TRIALS)
    estimates = np.empty((*shape, 2, 6))
    zero_likelihood = np.empty(shape, dtype=int)
    # The bank supplies all physical observations. Nothing from a held-out group
    # can reach either estimator, including a reference phase.
    unused_truth = np.full(6, np.nan)

    for scheme, splits in enumerate(test_groups):
        for fold, test in enumerate(splits):
            training = np.setdiff1d(indices, test)
            bank = np.ascontiguousarray(groups[:, training].reshape(6, -1))
            if bank.shape[1] <= budgets.max():
                raise ValueError("Not enough mapping records in the training groups")
            for level, budget in enumerate(budgets):
                for trial in range(TRIALS):
                    streams = np.random.SeedSequence(
                        [BASE_SEED, scheme, fold, int(budget), trial],
                    ).generate_state(2)
                    fitted, _, neutral = simulate(squared_distances, unused_truth, bank, int(budget),
                                                  1, LAMBDA, int(streams[0]))
                    baseline = naive(np.random.default_rng(streams[1]), unused_truth, bank, int(budget), 1)
                    estimates[scheme, fold, level, trial] = [fitted, baseline]
                    zero_likelihood[scheme, fold, level, trial] = neutral
            print(f"Completed split {scheme + 1}, fold {fold + 1}.", flush=True)

    # Averaging identical endpoint particles can exceed pi by one floating-point ULP.
    excess = float(max(0, -estimates.min(), estimates.max() - np.pi))
    if not np.all(np.isfinite(estimates)) or excess > 16 * np.finfo(float).eps * np.pi:
        raise ValueError("Invalid phase estimates")
    np.clip(estimates, 0, np.pi, out=estimates)
    print(f"Maximum roundoff outside [0, pi]: {excess:.17g} rad.", flush=True)
    np.savez_compressed("results/ion-holdout-maps.npz", phases=estimates, budgets=budgets,
                        group_probabilities=rates, test_indices=test_groups,
                        labels=np.array(["NMQA", "uniform_naive"]), lambdas=np.asarray(LAMBDA),
                        null_alpha=zero_likelihood, seed=np.array(BASE_SEED, dtype=int),
                        phase_roundoff_rad=np.array(excess))


if __name__ == "__main__":
    main()
