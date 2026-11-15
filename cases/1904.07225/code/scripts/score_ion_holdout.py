"""Score predictions on measured, held-out labels and resample complete groups."""
import hashlib
import json
from pathlib import Path

import numpy as np


TRIAL_MAPS = Path("results/ion-holdout-maps.npz")
TUNED_MAPS = Path("results/ion-holdout-tuned.npz")
ORIGINAL_READOUTS = Path("config/binary_data.npz")
DRAW_COUNT = 4096
RESAMPLING_SEED = 2828026


def means_under_resampling(probabilities, counts):
    trials = len(probabilities)
    first = np.einsum("dt,ti->di", counts, probabilities)
    second = np.einsum("dt,ti->di", counts, probabilities**2)
    return first / trials, second / trials


def brier(probabilities, measured):
    return ((probabilities**2 - 2 * probabilities * measured + measured).mean(axis=-1)).mean(axis=0)


def exact_uniform_brier(groups, test, budget):
    """Take the hypergeometric expectation for balanced sampling without replacement."""
    train = np.setdiff1d(np.arange(groups.shape[1]), test)
    measured = groups[:, test].mean(axis=(1, 2))
    training = groups[:, train].mean(axis=(1, 2))
    pool = len(train) * groups.shape[-1]
    sites = len(training)
    shots = max(1, budget // sites)
    fraction = min(1., budget / sites)
    irreducible = measured * (1 - measured)
    shots_variance = shots * training * (1 - training) * (pool - shots) / (pool - 1)
    raw = shots_variance / shots**2 + (training - measured)**2
    smoothed = shots_variance / (shots + 1)**2 + ((shots * training + .5) / (shots + 1) - measured)**2
    missing = (.5 - measured)**2
    return [(irreducible + fraction * raw + (1 - fraction) * (missing + .125)).mean(),
            (irreducible + fraction * smoothed + (1 - fraction) * missing).mean()]


def analyze(rng, probabilities, neutral, groups, folds, budget):
    levels = len(budget)
    direct = np.empty((len(folds), levels, 3))
    exact_baselines = np.empty((len(folds), levels, 2))
    neutral_brier = np.empty((len(folds), levels))
    empirical_reference_loss = np.empty((len(folds), levels, 3))
    bootstrap = np.zeros((DRAW_COUNT, levels, 2))
    max_identity_error = 0.
    for fold, test in enumerate(folds):
        measured = groups[:, test].mean(axis=-1).T
        target = measured.mean(axis=0)
        target_resample = measured[rng.integers(len(measured), size=(DRAW_COUNT, len(measured)))].mean(axis=1)
        for index, maps in enumerate(probabilities[fold]):
            exact_baselines[fold, index] = exact_uniform_brier(groups, test, budget[index])
            ntrials = len(maps)
            distribution = np.full(ntrials, 1 / ntrials)
            nmqa_counts = rng.multinomial(ntrials, distribution, size=DRAW_COUNT)
            uniform_counts = rng.multinomial(ntrials, distribution, size=DRAW_COUNT)
            boot_arms = np.empty((DRAW_COUNT, 3))
            for arm, counts in enumerate((nmqa_counts, uniform_counts, uniform_counts)):
                pred = maps[:, arm]
                score = brier(pred, target)
                # An independent evaluation of the binary losses using
                # the measured number of bright and dark outcomes per ion.
                bright = groups[:, test].sum(axis=(1, 2))
                total = groups.shape[-1] * len(test)
                expanded = (((1 - pred)**2 * bright + pred**2 * (total - bright)) / total).mean()
                max_identity_error = max(max_identity_error, abs(expanded - score))
                direct[fold, index, arm] = score
                empirical_reference_loss[fold, index, arm] = np.mean((pred - target)**2)
                first, second = means_under_resampling(pred, counts)
                boot_arms[:, arm] = (second - 2 * first * target_resample).mean(axis=1)
            bootstrap[:, index] += (boot_arms[:, :1] - boot_arms[:, 1:]) / len(folds)
            neutral_brier[fold, index] = brier(neutral[fold, index], target)
    if max_identity_error > 1e-14:
        raise ValueError("The direct bright/dark losses disagree with the expected Brier score")
    avg = direct.mean(axis=0)
    point = avg[:, :1] - avg[:, 1:]
    stderr = bootstrap.std(axis=0, ddof=1)
    if not np.all(np.isfinite(bootstrap)) or np.any(stderr == 0):
        raise ValueError("Invalid bootstrap distribution")
    mult = np.quantile(np.abs((bootstrap - point) / stderr).max(axis=(1, 2)), .95)
    entries = []
    for j, shots in enumerate(budget):
        bounds = np.stack((point[j] - mult * stderr[j], point[j] + mult * stderr[j]), axis=1)
        favored = ["NMQA" if row[1] < 0 else other if row[0] > 0 else "undetermined"
                   for row, other in zip(bounds, ("uniform_naive", "uniform_jeffreys"))]
        entries.append({"shots": int(shots), "brier_means": avg[j].tolist(),
                        "exact_uniform_baseline_brier_means": exact_baselines[:, j].mean(axis=0).tolist(),
                        "mse_to_holdout_readout_fraction": empirical_reference_loss[:, j].mean(axis=0).tolist(),
                        "difference_nmqa_minus_naive": point[j, 0],
                        "simultaneous_95_interval": bounds[0].tolist(), "favored": favored[0],
                        "difference_nmqa_minus_jeffreys": point[j, 1],
                        "simultaneous_95_interval_vs_jeffreys": bounds[1].tolist(),
                        "favored_vs_jeffreys": favored[1],
                        "fold_differences": (direct[:, j, 0] - direct[:, j, 1]).tolist(),
                        "nmqa_minus_naive_with_neutral_unseen_prior": avg[j, 0] - neutral_brier[:, j].mean()})
    return {"comparisons": entries, "max_brier_identity_error": max_identity_error,
            "bootstrap_simultaneous_multiplier": float(mult)}


def main():
    with np.load(ORIGINAL_READOUTS, allow_pickle=False) as raw:
        g = raw["binary_data"].reshape(6, 51, 500)
    with np.load(TRIAL_MAPS, allow_pickle=False) as archive:
        phase = archive["phases"]
        probs = np.cos(phase / 2)**2
        folds = archive["test_indices"]
        budgets = archive["budgets"]
        recorded_p = archive["group_probabilities"]
        roundoff = float(archive["phase_roundoff_rad"])
        neutral_alpha = archive["null_alpha"]
        fitting_seed = int(archive["seed"])
        pair = archive["lambdas"].tolist()
    np.testing.assert_array_equal(recorded_p, g.mean(axis=-1))
    for scheme in folds:
        np.testing.assert_array_equal(np.sort(scheme.ravel()), np.arange(51))
    naive = probs[..., 1, :]
    neutral = naive.copy()
    smoothed = np.empty_like(naive)
    for index, budget in enumerate(budgets):
        raw = naive[:, :, index]
        if budget < 6:
            phases = phase[:, :, index, :, 1]
            unmapped = (phases > 0) & (phases < np.pi)
            np.testing.assert_array_equal(unmapped.sum(axis=-1), np.full(phases.shape[:-1], 6 - budget))
            neutral[:, :, index] = np.where(unmapped, .5, raw)
            count = (~unmapped).astype(int)
        else:
            count = budget // 6
        bright = np.rint(count * raw)
        np.testing.assert_allclose(bright, count * raw, rtol=0, atol=2e-14)
        smoothed[:, :, index] = (bright + .5) / (count + 1)
    probs = np.concatenate((probs, smoothed[..., None, :]), axis=-2)
    rng = np.random.default_rng(RESAMPLING_SEED)
    variants = {tag: analyze(rng, probs[i], neutral[i], g, folds[i], budgets)
                for i, tag in enumerate(("contiguous", "interleaved"))}
    with np.load(TUNED_MAPS, allow_pickle=False) as archive:
        tuning_budgets = archive["budgets"]
        selected = archive["pair_indices"]
        np.testing.assert_array_equal(selected, archive["calibration_scores"].argmin(axis=-1))
        candidates = np.asarray(json.loads(Path("config/lambda.json").read_bytes())["pairs"])
        np.testing.assert_array_equal(archive["pair_values"], candidates[selected])
        indices = np.searchsorted(budgets, tuning_budgets)
        np.testing.assert_array_equal(budgets[indices], tuning_budgets)
        tuned = probs[0][:, indices].copy()
        tuned[..., 0, :] = np.cos(archive["phases"] / 2)**2
        tuned_result = analyze(rng, tuned, neutral[0][:, indices], g, folds[0], tuning_budgets)
        tuned_result.update(selected_pair_indices=selected.tolist(), selected_pairs=candidates[selected].tolist(),
                            fitting_seed=int(archive["seed"]),
                            training_trials_per_direction=int(archive["training_trials_per_direction"]))
    variants["contiguous_train_only_tuned"] = tuned_result
    result = {"fixed_lambdas": pair, "n_trials_per_arm_fold_budget": phase.shape[3],
              "arm_order": ["NMQA", "uniform_naive", "uniform_jeffreys"],
              "probability_convention": "p=cos(phi/2)^2",
              "phase_roundoff_rad": roundoff, "null_alpha_count": int(neutral_alpha.sum()),
              "fitting_seed": fitting_seed, "resampling_seed": RESAMPLING_SEED,
              "bootstrap_draws": DRAW_COUNT,
              "raw_readout_sha256": hashlib.sha256(ORIGINAL_READOUTS.read_bytes()).hexdigest(),
              "trial_maps_sha256": hashlib.sha256(TRIAL_MAPS.read_bytes()).hexdigest(),
              "tuned_maps_sha256": hashlib.sha256(TUNED_MAPS.read_bytes()).hexdigest(),
              "test_indices": folds.tolist(), "results": variants}
    Path("results/ion-holdout-scores.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
