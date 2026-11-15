"""Repeat the paper's ion sweep budgets with tuning confined to training groups."""
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_filter import simulate


TRAIN_TRIALS = 16
TEST_TRIALS = 128
SEED = 28024096


def main():
    with np.load("config/binary_data.npz", allow_pickle=False) as captured:
        groups = captured["binary_data"].reshape(6, 3, 17 * 500)
    settings = json.loads(Path("config/paper-grid.json").read_bytes())["fields"]["ion"]
    budgets = np.asarray(settings["sweep"])
    pairs = np.asarray(json.loads(Path("config/lambda.json").read_bytes())["pairs"])
    if len(pairs) != 250 or budgets.tolist() != [24, 96]:
        raise ValueError("The selected source sweep must contain 250 pairs at 24 and 96 shots")
    positions = np.asarray(settings["locations"])
    squared_distances = ((positions[:, None, :] - positions[None, :, :]) ** 2).sum(axis=-1)
    unused_truth = np.full(6, np.nan)
    scores = np.empty((3, len(budgets), len(pairs)))
    chosen = np.empty(scores.shape[:-1], dtype=int)
    maps = np.empty((*chosen.shape, TEST_TRIALS, 6))
    null_counts = np.zeros(chosen.shape, dtype=int)

    for fold in range(3):
        train = [other for other in range(3) if other != fold]
        training_banks = [np.ascontiguousarray(groups[:, block]) for block in train]
        calibration_targets = [bank.mean(axis=1) for bank in training_banks]
        final_bank = np.ascontiguousarray(groups[:, train].reshape(6, -1))
        for index, budget in enumerate(budgets):
            rng = np.random.default_rng(np.random.SeedSequence([SEED, fold, int(budget)]))
            seeds = rng.integers(2**32, size=(2, TRAIN_TRIALS), dtype=np.uint32)
            for candidate, pair in enumerate(pairs):
                score = 0.
                for direction, bank in enumerate(training_banks):
                    target = calibration_targets[1 - direction]
                    for seed in seeds[direction]:
                        phase, _, _ = simulate(squared_distances, unused_truth, bank, int(budget),
                                               1, tuple(pair), int(seed))
                        score += np.mean((np.cos(phase / 2)**2 - target)**2)
                scores[fold, index, candidate] = score / (2 * TRAIN_TRIALS)
            best = int(np.argmin(scores[fold, index]))
            chosen[fold, index] = best
            for trial, seed in enumerate(rng.integers(2**32, size=TEST_TRIALS, dtype=np.uint32)):
                phase, _, neutral = simulate(squared_distances, unused_truth, final_bank, int(budget),
                                             1, tuple(pairs[best]), int(seed))
                maps[fold, index, trial] = phase
                null_counts[fold, index] += neutral
            print(f"Completed fold {fold + 1}, budget {budget}, pair {best}.", flush=True)
    allowed_roundoff = 16 * np.finfo(float).eps * np.pi
    if not np.all(np.isfinite(scores)) or not np.all(np.isfinite(maps)):
        raise ValueError("Expected finite training scores and fitted phases")
    if maps.min() < -allowed_roundoff or maps.max() > np.pi + allowed_roundoff:
        raise ValueError("Fitted phases are outside the physical interval")
    np.savez_compressed("results/ion-holdout-tuned.npz", budgets=budgets, pair_indices=chosen,
                        pair_values=pairs[chosen], calibration_scores=scores,
                        phases=np.clip(maps, 0, np.pi), null_alpha=null_counts,
                        seed=np.array(SEED), training_trials_per_direction=np.array(TRAIN_TRIALS))


if __name__ == "__main__":
    main()
