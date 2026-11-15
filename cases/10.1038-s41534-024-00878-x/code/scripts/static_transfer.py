"""A frozen image-only baseline for transfer between the two QFlow devices."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import zipfile

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax

from extract_qflow_lite import read_npy_dict


def features(sensor, side):
    sensor = np.asarray(sensor, float)
    scale = np.percentile(sensor, 75)-np.percentile(sensor, 25)
    if scale <= 0:
        scale = float(np.std(sensor))
    if scale <= 0:
        return np.zeros(3*side*side)
    normalized = np.clip((sensor-np.median(sensor))/scale, -6., 6.)
    yy, xx = np.meshgrid(np.linspace(0, sensor.shape[0]-1, side),
                         np.linspace(0, sensor.shape[1]-1, side), indexing="ij")
    image = map_coordinates(normalized, np.stack((yy, xx)), order=1, mode="nearest")
    dy, dx = np.gradient(image)
    return np.concatenate((image.ravel(), dx.ravel(), dy.ravel()))


def load_data(cfg):
    names, labels, batches, vectors, degenerate, hashes = [], [], [], [], [], []
    with zipfile.ZipFile(cfg["input"]) as archive:
        for name in sorted(archive.namelist()):
            if "/exp_small/" not in name:
                continue
            value = read_npy_dict(archive.read(name))
            label = np.asarray(value["label"], float)
            assert label.shape == (5,) and abs(label.sum()-1) < 1e-12 and np.min(label) >= 0
            sensor = np.asarray(value["sensor"], float)
            assert np.isfinite(sensor).all()
            names.append(name)
            labels.append(label)
            batches.append(int(value["dataset"]))
            vectors.append(features(sensor, cfg["image_size"]))
            degenerate.append(len(np.unique(value["x"])) == 1 or len(np.unique(value["y"])) == 1)
            hashes.append(sha256(sensor.tobytes()).hexdigest())
    assert len(names) == 756 and Counter(batches) == {0: 82, 1: 503, 2: 171}
    return np.array(vectors), np.array(labels), np.array(batches), np.array(degenerate), names, hashes


def metrics(target, probabilities):
    dominant = target.argmax(axis=1)
    predicted = probabilities.argmax(axis=1)
    hard = predicted == dominant
    credit = target[np.arange(len(target)), predicted]
    return dict(accuracy=float(hard.mean()), soft_credit=float(credit.mean()),
        balanced_accuracy=float(np.mean([hard[dominant == k].mean() for k in np.unique(dominant)])),
        brier=float(np.mean(np.sum((probabilities-target)**2, axis=1))),
        cross_entropy=float(-np.mean(np.sum(target*np.log(np.maximum(probabilities, 1e-300)), axis=1))))


def fit(x, y, training, testing, cfg):
    center = x[training].mean(axis=0)
    _, singular, right = np.linalg.svd(x[training]-center, full_matrices=False)
    pca = right[:cfg["pca_components"]]
    scale = np.maximum(singular[:len(pca)]/np.sqrt(len(training)-1), 1e-12)
    projected = ((x-center)@pca.T)/scale
    design = np.column_stack((projected, np.ones(len(x))))
    xx, yy = design[training], y[training]
    ridge = cfg["ridge"]
    def objective(flat):
        weights = flat.reshape(xx.shape[1], 5)
        logits = xx@weights
        loss = np.mean(logsumexp(logits, axis=1)-np.sum(yy*logits, axis=1))+.5*ridge*np.sum(weights**2)
        gradient = xx.T@(softmax(logits, axis=1)-yy)/len(training)+ridge*weights
        return float(loss), gradient.ravel()
    initial = np.zeros((xx.shape[1], 5))
    initial[-1] = np.log((yy.sum(axis=0)+1)/(len(training)+5))
    fit = minimize(objective, initial.ravel(), jac=True, method="L-BFGS-B",
                   options={"maxiter":cfg["max_iterations"], "ftol":1e-14, "gtol":1e-9})
    weights = fit.x.reshape(initial.shape)
    probability = softmax(design[testing]@weights, axis=1)
    prior = (yy.sum(axis=0)+1)/(len(training)+5)
    baseline = np.tile(prior, (len(testing), 1))
    delta = y[testing, probability.argmax(axis=1)]-y[testing, baseline.argmax(axis=1)]
    draws = np.random.default_rng(cfg["seed"]).integers(0, len(testing), (cfg["bootstrap_replicates"], len(testing)))
    interval = np.percentile(delta[draws].mean(axis=1), [2.5, 97.5])
    return dict(training=training.tolist(), testing=testing.tolist(), center=center.tolist(), pca=pca.tolist(),
                scale=scale.tolist(), weights=weights.tolist(), prior=prior.tolist(),
                probabilities=probability.tolist(), metrics=metrics(y[testing], probability),
                baseline=metrics(y[testing], baseline), soft_credit_gain_ci=interval.tolist(),
                objective=float(fit.fun), initial_objective=objective(initial.ravel())[0],
                gradient_max=float(np.max(abs(fit.jac))), iterations=int(fit.nit), converged=bool(fit.success))


def main():
    cfg = json.loads(Path("config/static-transfer.json").read_text())
    x, y, batch, bad, names, hashes = load_data(cfg)
    splits = {}
    for name, mask in [("A_to_B", batch != 2), ("B_to_A", batch == 2),
                       ("cooldown0_to_1", batch == 0), ("cooldown1_to_0", batch == 1)]:
        testmask = ~mask if name in {"A_to_B", "B_to_A"} else batch == (1 if name.startswith("cooldown0") else 0)
        splits[name] = (np.flatnonzero(mask), np.flatnonzero(testmask))
    rng = np.random.default_rng(cfg["seed"])
    testing = []
    for b in range(3):
        for label in range(5):
            choices = np.flatnonzero((batch == b) & (y.argmax(axis=1) == label))
            testing.extend(rng.permutation(choices)[:max(1, round(.2*len(choices)))])
    test = np.array(sorted(testing), int)
    splits["mixed_scan_holdout"] = (np.setdiff1d(np.arange(len(x)), test), test)
    for name in ("A_to_B", "B_to_A"):
        train, test = splits[name]
        splits[name+"_valid_axes"] = (train[~bad[train]], test[~bad[test]])
    results = {}
    for name, (training, testing) in splits.items():
        assert not set(training) & set(testing)
        assert not set(hashes[i] for i in training) & set(hashes[i] for i in testing)
        results[name] = fit(x, y, training, testing, cfg)
        print(name, results[name]["metrics"], flush=True)
    np.savez_compressed("results/static-transfer-features.npz", features=x, labels=y, batches=batch, bad_axes=bad)
    Path("results/static-transfer.json").write_text(json.dumps(dict(config=cfg, names=names, sensor_sha256=hashes,
        batch_counts=dict(Counter(batch.tolist())), mixed_label_count=int(np.sum((y > 0).sum(axis=1) > 1)),
        degenerate_axes=int(bad.sum()), experiments=results), ensure_ascii=False, indent=2)+"\n")


if __name__ == "__main__":
    main()
