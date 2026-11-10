"""Recompute ion state labels from the archived calibration and Ramsey frames."""

import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks


HEIGHT, WIDTH, CYCLES, BLOCKS = 11, 38, 500, 51
BRIGHT = "ROI_ref_bright_11x38_500_cyc_115321.txt"
DARK = "ROI_ref_bgnd_11x38_500_cyc_115302.txt"
RUN = "20181010-115434"
SEED = 190407225


def calibration(archive, name):
    with ZipFile(io.BytesIO(archive.read(name + ".zip"))) as nested, nested.open(name) as stream:
        values = np.loadtxt(stream, dtype=np.float32)
    return values.reshape(CYCLES, HEIGHT, WIDTH)


def apertures(bright, dark):
    projection = (bright.mean(axis=0) - dark.mean(axis=0)).sum(axis=0, dtype=float)
    x = np.arange(WIDTH)
    y = projection / max(projection)
    guesses, _ = find_peaks(y, height=y.min() + 0.5 * np.ptp(y), distance=2)
    if len(guesses) != 6:
        raise ValueError(f"expected six calibration peaks, found {guesses}")

    def residual(params):
        height, center, width = params.reshape(3, 6)
        terms = height[:, None] * np.exp(-0.5 * ((x - center[:, None]) / width[:, None]) ** 2)
        return terms.sum(axis=0) - y

    initial = np.r_[y[guesses], guesses, np.full(6, 0.5)]
    low = np.r_[np.zeros(6), guesses - 2, np.full(6, 0.1)]
    high = np.r_[np.full(6, np.inf), guesses + 2, np.full(6, 4.0)]
    fit = least_squares(residual, initial, bounds=(low, high), xtol=1e-12, ftol=1e-12, gtol=1e-12)
    if not fit.success:
        raise RuntimeError(fit.message)
    centers = fit.x[6:12]
    edges = np.r_[0, ((centers[:-1] + centers[1:]) / 2).astype(int) + 1, WIDTH]
    if not np.all(np.diff(edges) > 0):
        raise ValueError(f"invalid ion aperture edges {edges}")
    return edges, dict(peak_columns=guesses.tolist(), centers=centers.tolist(),
                       edges=edges.tolist(), fit_rms=float(np.sqrt(np.mean(fit.fun**2))))


def features(frames, left, right):
    return frames[:, :, left:right].reshape(len(frames), -1)


def threshold_model(x, labels):
    summed = x.sum(axis=1, dtype=float)
    sorted_unique = np.unique(summed)
    candidates = (sorted_unique[1:] + sorted_unique[:-1]) / 2
    errors = np.count_nonzero((summed[:, None] >= candidates) != labels[:, None], axis=0)
    best = np.flatnonzero(errors == errors.min())
    threshold = float(candidates[best[len(best) // 2]])
    return threshold


def fit_threshold(x, labels):
    prediction = np.empty(len(labels), dtype=bool)
    folds = [np.array_split(np.flatnonzero(labels == state), 5) for state in (0, 1)]
    for dark, bright in zip(*folds):
        held = np.r_[dark, bright]
        train = np.ones(len(labels), dtype=bool)
        train[held] = False
        split = threshold_model(x[train], labels[train])
        prediction[held] = x[held].sum(axis=1, dtype=float) >= split
    split = threshold_model(x, labels)
    return lambda z: z.sum(axis=1, dtype=float) >= split, dict(
        threshold=split,
        dark_false_positive=float(prediction[labels == 0].mean()),
        bright_false_negative=float(1 - prediction[labels == 1].mean()),
    )


def fit_forests(x, labels, ion):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import RandomizedSearchCV

    params = dict(n_estimators=[50, 100, 150, 200, 250], max_depth=[None, 5, 10, 15],
                  criterion=["gini", "entropy"], bootstrap=[False])
    rng = np.random.default_rng(SEED + ion)
    best_cv, best_archive = -1, -1
    cv_model = archive_model = None
    selection = []
    for _ in range(10):
        seeds = rng.integers(0, 2**31, size=3).tolist()
        search = RandomizedSearchCV(RandomForestClassifier(random_state=seeds[0]), params,
                                    n_iter=7, cv=5, random_state=seeds[1], n_jobs=1)
        search.fit(x, labels)
        row = dict(params=search.best_params_, cv_accuracy=search.best_score_)
        if search.best_score_ > best_cv:
            best_cv, cv_model = search.best_score_, search.best_estimator_

        lo, hi = np.min(search.predict_proba(x)[:, 1]), np.max(search.predict_proba(x)[:, 1])
        # The calibration has equal numbers of dark and bright frames. On this
        # prior the archived flip-rate formulas reduce to lo and 1 - hi.
        if lo < 0.5 < hi and lo + 1 - hi < 0.5:
            train = rng.integers(0, 900, size=800)
            score = rng.integers(800, 1000, size=100)
            model = RandomForestClassifier(**search.best_params_, random_state=seeds[2])
            model.fit(x[train], labels[train])
            value = model.score(x[score], labels[score])
            row.update(archive_selector_accuracy=value, selection_overlap=len(set(train) & set(score)))
            if value > best_archive:
                best_archive, archive_model = value, model
        selection.append(row)
    if cv_model is None or archive_model is None:
        raise RuntimeError(f"no fitted forest for ion {ion + 1}")
    return (cv_model.predict, archive_model.predict), dict(
        best_cv_accuracy=best_cv, archive_selector_accuracy=best_archive, search=selection,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=("threshold", "rf"))
    args = parser.parse_args()
    archive_path = Path("input/ramseydata.zip")
    with ZipFile(archive_path) as outer:
        bright, dark = calibration(outer, BRIGHT), calibration(outer, DARK)
        edges, geometry = apertures(bright, dark)
        frames = np.concatenate((dark, bright), axis=0)
        labels = np.repeat([0, 1], CYCLES)
        methods = ("threshold",) if args.method == "threshold" else ("rf_cv", "rf_archive_selector")
        models, training = [], []
        for ion, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
            x = features(frames, left, right)
            if args.method == "threshold":
                predictor, row = fit_threshold(x, labels)
                models.append((predictor,))
            else:
                predictors, row = fit_forests(x, labels, ion)
                models.append(predictors)
            training.append(row)
            print(f"{args.method}: fitted ion {ion + 1}/6", flush=True)
        raw_hash = hashlib.sha256()
        raw_git = hashlib.sha1(b"blob 53295051\0")
        states = np.empty((len(methods), 6, BLOCKS, CYCLES), dtype=np.uint8)
        with ZipFile(io.BytesIO(outer.read(RUN + ".zip"))) as run_zip:
            scan = np.loadtxt(io.BytesIO(run_zip.read(f"{RUN}/cexc{RUN}.dat")), comments="%")[:, 0]
            camera_zip = run_zip.read(f"{RUN}/cimg{RUN}.zip")
        with ZipFile(io.BytesIO(camera_zip)) as camera, camera.open(f"cimg{RUN}.dat") as stream:
            for block in range(BLOCKS):
                line = stream.readline(2 * 1024 * 1024)
                raw_hash.update(line)
                raw_git.update(line)
                row = np.fromstring(line.decode("ascii"), sep=" ", dtype=np.float32)
                current = row.reshape(CYCLES, HEIGHT, WIDTH)
                for ion, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
                    x = features(current, left, right)
                    for m, predict in enumerate(models[ion]):
                        states[m, ion, block] = predict(x)
            if stream.read(1):
                raise ValueError("camera archive has unexpected data after block 51")
    if raw_git.hexdigest() != "4d9967551c64636e8cc1d93b0a92e0cbdd5e275d":
        raise ValueError("camera frames differ from the pinned Git blob")
    np.savez_compressed(f"results/camera-{args.method}.npz", **dict(zip(methods, states)),
                       scan=scan, mean_bright=bright.mean(axis=0), mean_dark=dark.mean(axis=0))
    with archive_path.open("rb") as stream:
        archive_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    meta = dict(methods=methods, shape=[6, BLOCKS, CYCLES], training=training,
                source_sha256=archive_sha, raw_camera_sha256=raw_hash.hexdigest(),
                raw_camera_git_sha1=raw_git.hexdigest(), seed=SEED, geometry=geometry)
    Path(f"results/camera-{args.method}.json").write_text(json.dumps(meta, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
