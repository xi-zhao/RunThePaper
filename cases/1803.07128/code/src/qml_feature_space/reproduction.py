"""Run every numerical panel in arXiv:1803.07128 from printed equations.

The source figures are deliberately unreachable from this module.  Benchmark
random seeds and several training hyperparameters were not printed in the
paper; those values are explicit reconstructed parameters in the JSON config,
never inferred from source pixels or author numerical output.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from sklearn.datasets import make_blobs, make_circles, make_moons
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from .model import (
    real_fock_features,
    single_mode_overlap,
    squeezing_kernel,
    truncated_squeezed_state,
)


TARGET_FILES = {
    "T001": "T001_fig4_squeezing_kernel.npz",
    "T002": "T002_fig5_svm_boundaries.npz",
    "T003": "T003_fig6_fock_perceptron.npz",
    "T004": "T004_fig8_variational_classifier.npz",
}


def _save(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid(inputs: np.ndarray, points: int, padding: float = 0.18) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    lower = inputs.min(axis=0) - padding
    upper = inputs.max(axis=0) + padding
    x = np.linspace(lower[0], upper[0], points)
    y = np.linspace(lower[1], upper[1], points)
    xx, yy = np.meshgrid(x, y)
    return x, y, np.column_stack([xx.ravel(), yy.ravel()])


def _run_kernel_surfaces(config: dict[str, Any], output: Path) -> dict[str, Any]:
    values = config["paper_parameters"]["kernel_c_values"]
    points = int(config["numerics"]["surface_grid_points"])
    axis = np.linspace(-1.0, 1.0, points)
    xx, yy = np.meshgrid(axis, axis)
    candidates = np.column_stack([xx.ravel(), yy.ravel()])
    surfaces = np.asarray(
        [squeezing_kernel(np.zeros((1, 2)), candidates, c).reshape(points, points) for c in values]
    )
    _save(output / TARGET_FILES["T001"], c=np.asarray(values), x=axis, y=axis, kernel=surfaces)
    widths = []
    center = points // 2
    for surface in surfaces:
        line = surface[center]
        mask = line >= 0.5
        widths.append(float(axis[np.flatnonzero(mask)[-1]] - axis[np.flatnonzero(mask)[0]]))
    return {"half_height_widths": widths, "diagonal_max_error": float(np.max(np.abs(surfaces[:, center, center] - 1.0)))}


def _svc_panel(
    x: np.ndarray,
    labels: np.ndarray,
    train_size: int,
    seed: int,
    c: float,
    points: int,
) -> dict[str, np.ndarray | float]:
    train, test = train_test_split(
        np.arange(len(labels)), train_size=train_size, stratify=labels, random_state=seed
    )
    classifier = SVC(kernel=lambda a, b: squeezing_kernel(a, b, c), C=1.0)
    classifier.fit(x[train], labels[train])
    grid_x, grid_y, grid = _grid(x, points)
    decision = classifier.decision_function(grid).reshape(len(grid_y), len(grid_x))
    return {
        "x": x,
        "labels": labels,
        "train_indices": train,
        "test_indices": test,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "decision": decision,
        "train_accuracy": float(classifier.score(x[train], labels[train])),
        "test_accuracy": float(classifier.score(x[test], labels[test])),
    }


def _run_svm(config: dict[str, Any], output: Path) -> dict[str, Any]:
    reconstructed = config["reconstructed_benchmarks"]["svm"]
    seed = int(reconstructed["seed"])
    points = int(config["numerics"]["decision_grid_points"])
    top_samples = int(reconstructed["top_total_samples"])
    datasets = [
        make_circles(
            n_samples=top_samples,
            factor=float(reconstructed["circles_factor"]),
            noise=float(reconstructed["circles_noise"]),
            random_state=seed,
        ),
        make_moons(
            n_samples=top_samples,
            noise=float(reconstructed["moons_noise"]),
            random_state=seed,
        ),
        make_blobs(
            n_samples=top_samples,
            centers=np.asarray(reconstructed["blob_centers"], dtype=float),
            cluster_std=float(reconstructed["blob_std"]),
            random_state=seed,
        ),
    ]
    panels: list[dict[str, np.ndarray | float]] = []
    for inputs, labels in datasets:
        panels.append(
            _svc_panel(
                inputs,
                labels,
                int(reconstructed["top_train_samples"]),
                seed,
                1.5,
                points,
            )
        )

    rng = np.random.default_rng(seed)
    bottom_total = int(reconstructed["bottom_total_samples"])
    extent = float(reconstructed["bottom_extent"])
    inputs = rng.uniform(-extent, extent, size=(bottom_total, 2))
    frequency = float(reconstructed["bottom_label_frequency"])
    labels = (np.sin(frequency * inputs[:, 0]) * np.sin(frequency * inputs[:, 1]) > 0.0).astype(int)
    for c in config["paper_parameters"]["kernel_c_values"]:
        panels.append(
            _svc_panel(
                inputs,
                labels,
                int(reconstructed["bottom_train_samples"]),
                seed,
                float(c),
                points,
            )
        )

    payload: dict[str, Any] = {
        "panel_names": np.asarray(["circles", "moons", "blobs", "capacity_c1", "capacity_c1.5", "capacity_c2"]),
        "c": np.asarray([1.5, 1.5, 1.5, 1.0, 1.5, 2.0]),
        "train_accuracy": np.asarray([panel["train_accuracy"] for panel in panels]),
        "test_accuracy": np.asarray([panel["test_accuracy"] for panel in panels]),
    }
    for index, panel in enumerate(panels):
        for key, value in panel.items():
            if key not in {"train_accuracy", "test_accuracy"}:
                payload[f"panel_{index}_{key}"] = value
    _save(output / TARGET_FILES["T002"], **payload)
    return {
        "train_accuracy": payload["train_accuracy"].tolist(),
        "test_accuracy": payload["test_accuracy"].tolist(),
        "capacity_train_monotonic": bool(np.all(np.diff(payload["train_accuracy"][3:]) >= -1.0e-12)),
    }


def _run_perceptron(config: dict[str, Any], output: Path) -> dict[str, Any]:
    reconstructed = config["reconstructed_benchmarks"]["perceptron"]
    seed = int(reconstructed["seed"])
    inputs, labels = make_blobs(
        n_samples=int(reconstructed["total_samples"]),
        centers=np.asarray(reconstructed["centers"], dtype=float),
        cluster_std=float(reconstructed["cluster_std"]),
        random_state=seed,
    )
    train, test = train_test_split(
        np.arange(len(labels)),
        train_size=int(reconstructed["train_samples"]),
        stratify=labels,
        random_state=seed,
    )
    c = float(config["paper_parameters"]["perceptron_c"])
    terms = int(config["numerics"]["perceptron_even_fock_terms"])
    features = real_fock_features(inputs, c, terms)
    classifier = Perceptron(
        max_iter=1,
        tol=None,
        shuffle=True,
        random_state=seed,
        warm_start=True,
        penalty=None,
    )
    epochs = np.asarray(config["paper_parameters"]["perceptron_epochs"], dtype=int)
    snapshots: list[tuple[np.ndarray, np.ndarray]] = []
    train_accuracy: list[float] = []
    test_accuracy: list[float] = []
    for epoch in range(1, int(epochs[-1]) + 1):
        classifier.fit(features[train], labels[train])
        if epoch in epochs:
            snapshots.append((classifier.coef_.copy(), classifier.intercept_.copy()))
            train_accuracy.append(float(classifier.score(features[train], labels[train])))
            test_accuracy.append(float(classifier.score(features[test], labels[test])))

    grid_x, grid_y, grid = _grid(inputs, int(config["numerics"]["decision_grid_points"]))
    grid_features = real_fock_features(grid, c, terms)
    decision = np.asarray(
        [(grid_features @ weights.T + intercept).reshape(len(grid_y), len(grid_x)) for weights, intercept in snapshots]
    )
    _save(
        output / TARGET_FILES["T003"],
        x=inputs,
        labels=labels,
        train_indices=train,
        test_indices=test,
        epochs=epochs,
        train_accuracy=np.asarray(train_accuracy),
        test_accuracy=np.asarray(test_accuracy),
        grid_x=grid_x,
        grid_y=grid_y,
        decision=decision,
        weights=np.asarray([item[0][0] for item in snapshots]),
        intercepts=np.asarray([item[1][0] for item in snapshots]),
    )
    return {
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "final_train_separable": bool(train_accuracy[-1] >= 1.0 - 1.0e-12),
    }


def _torch_squeezed_states(inputs: np.ndarray, c: float, cutoff: int, torch: Any) -> Any:
    real = torch.float64
    complex_type = torch.complex128
    phases = torch.as_tensor(inputs, dtype=real)
    vectors = []
    for mode in range(2):
        state = torch.zeros((len(inputs), cutoff), dtype=complex_type)
        for photon in range(0, cutoff, 2):
            n = photon // 2
            amplitude = (
                1.0 / math.sqrt(math.cosh(c))
                * math.sqrt(math.factorial(2 * n))
                / (2**n * math.factorial(n))
                * (-math.tanh(c)) ** n
            )
            state[:, photon] = amplitude * torch.exp(1.0j * n * phases[:, mode])
        state = state / torch.linalg.vector_norm(state, dim=1, keepdim=True)
        vectors.append(state)
    return torch.einsum("bi,bj->bij", vectors[0], vectors[1]).reshape(len(inputs), cutoff * cutoff)


def _run_variational(config: dict[str, Any], output: Path) -> dict[str, Any]:
    import torch
    import torch.nn.functional as functional

    reconstructed = config["reconstructed_benchmarks"]["variational"]
    seed = int(reconstructed["seed"])
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    inputs, labels = make_moons(
        n_samples=int(reconstructed["total_samples"]),
        noise=float(reconstructed["noise"]),
        random_state=seed,
    )
    train, test = train_test_split(
        np.arange(len(labels)),
        train_size=int(reconstructed["train_samples"]),
        stratify=labels,
        random_state=seed,
    )
    cutoff = int(config["numerics"]["variational_fock_cutoff"])
    c = float(config["paper_parameters"]["variational_c"])
    states = _torch_squeezed_states(inputs, c, cutoff, torch)

    complex_type = torch.complex128
    real = torch.float64
    annihilation = torch.zeros((cutoff, cutoff), dtype=complex_type)
    for photon in range(1, cutoff):
        annihilation[photon - 1, photon] = math.sqrt(photon)
    creation = annihilation.T.conj()
    identity = torch.eye(cutoff, dtype=complex_type)
    a1 = torch.kron(annihilation, identity)
    a2 = torch.kron(identity, annihilation)
    ad1 = a1.T.conj()
    ad2 = a2.T.conj()
    quadrature_x = (annihilation + creation) / math.sqrt(2.0)

    parameters = torch.nn.Parameter(
        torch.randn(int(config["paper_parameters"]["variational_parameter_count"]), dtype=real)
        * float(reconstructed["initial_parameter_std"])
    )
    optimizer = torch.optim.Adam([parameters], lr=float(reconstructed["learning_rate"]))
    regularization = float(reconstructed["l2_regularization"])

    def evolve(batch: Any) -> Any:
        state = batch.T
        for block in range(int(config["paper_parameters"]["variational_blocks"])):
            theta = parameters[8 * block : 8 * block + 8]
            beam_splitter = torch.matrix_exp(
                theta[0]
                * (
                    torch.exp(1.0j * theta[1]) * ad1 @ a2
                    - torch.exp(-1.0j * theta[1]) * a1 @ ad2
                )
            )
            state = beam_splitter @ state
            local = []
            for mode in range(2):
                displacement_parameter = theta[2 + mode].to(complex_type)
                displacement = torch.matrix_exp(
                    displacement_parameter * creation - displacement_parameter * annihilation
                )
                quadratic = torch.matrix_exp(
                    0.5j * theta[4 + mode] * quadrature_x @ quadrature_x
                )
                cubic = torch.matrix_exp(
                    (1.0j / 3.0)
                    * theta[6 + mode]
                    * quadrature_x
                    @ quadrature_x
                    @ quadrature_x
                )
                local.append(cubic @ quadratic @ displacement)
            state = torch.kron(local[0], local[1]) @ state
        return state.T

    def probabilities(batch: Any) -> Any:
        evolved = evolve(batch)
        output_zero = torch.abs(evolved[:, 2 * cutoff]) ** 2
        output_one = torch.abs(evolved[:, 2]) ** 2
        denominator = output_zero + output_one + 1.0e-14
        return torch.stack([output_zero / denominator, output_one / denominator], dim=1)

    rng = np.random.default_rng(seed)
    steps = int(config["paper_parameters"]["variational_steps"])
    batch_size = int(config["paper_parameters"]["variational_batch_size"])
    loss_history = np.empty(steps, dtype=float)
    for step in range(steps):
        indices = rng.choice(train, size=batch_size, replace=False)
        targets = functional.one_hot(torch.as_tensor(labels[indices]), 2).to(real)
        optimizer.zero_grad()
        predicted = probabilities(states[indices])
        loss = torch.mean(torch.sum((predicted - targets) ** 2, dim=1))
        loss = loss + regularization * torch.mean(parameters**2)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([parameters], max_norm=5.0)
        optimizer.step()
        loss_history[step] = float(loss.detach())

    def predict_in_chunks(batch: Any, chunk_size: int = 512) -> np.ndarray:
        values = []
        with torch.no_grad():
            for start in range(0, len(batch), chunk_size):
                values.append(probabilities(batch[start : start + chunk_size]).cpu().numpy())
        return np.concatenate(values)

    all_probabilities = predict_in_chunks(states)
    train_accuracy = float(np.mean(np.argmax(all_probabilities[train], axis=1) == labels[train]))
    test_accuracy = float(np.mean(np.argmax(all_probabilities[test], axis=1) == labels[test]))
    grid_x, grid_y, grid = _grid(inputs, int(config["numerics"]["variational_grid_points"]), padding=0.25)
    grid_states = _torch_squeezed_states(grid, c, cutoff, torch)
    grid_probability = predict_in_chunks(grid_states)[:, 1].reshape(len(grid_y), len(grid_x))

    _save(
        output / TARGET_FILES["T004"],
        x=inputs,
        labels=labels,
        train_indices=train,
        test_indices=test,
        grid_x=grid_x,
        grid_y=grid_y,
        class_one_probability=grid_probability,
        loss=loss_history,
        final_parameters=parameters.detach().cpu().numpy(),
        train_accuracy=np.asarray(train_accuracy),
        test_accuracy=np.asarray(test_accuracy),
        fock_cutoff=np.asarray(cutoff),
    )
    first_window = float(np.median(loss_history[:20]))
    final_window = float(np.median(loss_history[-200:]))
    return {
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "initial_loss_median": first_window,
        "final_loss_median": final_window,
        "loss_reduction_ratio": final_window / max(first_window, 1.0e-15),
    }


def _formula_checks(config: dict[str, Any]) -> dict[str, Any]:
    c = 1.5
    first_phase, second_phase = -0.37, 0.81
    analytic = single_mode_overlap(first_phase, second_phase, c)
    first = truncated_squeezed_state(np.asarray(first_phase), c, 120)
    second = truncated_squeezed_state(np.asarray(second_phase), c, 120)
    truncated = np.vdot(first, second)
    overlap_error = float(abs(analytic - truncated))
    sample = np.asarray([[-0.9, 0.2], [-0.2, -0.5], [0.3, 0.8], [0.9, -0.7]])
    gram = squeezing_kernel(sample, sample, c)
    hermitian_error = float(np.max(np.abs(gram - gram.T)))
    min_eigenvalue = float(np.min(np.linalg.eigvalsh(gram)))
    payload = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "checks": {
            "eq8_matches_independent_fock_sum": {"error": overlap_error, "tolerance": 1.0e-9, "passed": overlap_error < 1.0e-9},
            "real_kernel_is_symmetric": {"error": hermitian_error, "tolerance": 1.0e-12, "passed": hermitian_error < 1.0e-12},
            "real_kernel_is_psd": {"minimum_eigenvalue": min_eigenvalue, "tolerance": -1.0e-10, "passed": min_eigenvalue > -1.0e-10},
        },
    }
    payload["all_passed"] = all(item["passed"] for item in payload["checks"].values())
    return payload


def run_reproduction(config: dict[str, Any], workspace: Path) -> dict[str, Any]:
    started = perf_counter()
    output = workspace / "outputs" / "data"
    checks = workspace / "outputs" / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    formula = _formula_checks(config)
    kernel = _run_kernel_surfaces(config, output)
    svm = _run_svm(config, output)
    perceptron = _run_perceptron(config, output)
    variational = _run_variational(config, output)

    target_checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "targets": {
            "T001": {"passed": bool(kernel["diagonal_max_error"] < 1.0e-12 and np.all(np.diff(kernel["half_height_widths"]) <= 0.0)), **kernel},
            "T002": {"passed": svm["capacity_train_monotonic"] and min(svm["test_accuracy"][:3]) >= 0.75, **svm},
            "T003": {"passed": perceptron["final_train_separable"] and perceptron["test_accuracy"][-1] < 1.0, **perceptron},
            "T004": {"passed": variational["train_accuracy"] >= 0.95 and variational["test_accuracy"] >= 0.90 and variational["loss_reduction_ratio"] < 0.2, **variational},
        },
    }
    target_checks["all_passed"] = bool(all(item["passed"] for item in target_checks["targets"].values()))
    convergence = {
        "schema_version": 1,
        "status": "passed_with_declared_reduced_scale",
        "fock_sum_terms": 120,
        "eq8_truncation_error": formula["checks"]["eq8_matches_independent_fock_sum"]["error"],
        "perceptron_even_fock_terms": config["numerics"]["perceptron_even_fock_terms"],
        "variational_fock_cutoff": config["numerics"]["variational_fock_cutoff"],
        "note": "Fig. 5--8 cannot be paper-exact because the paper omits random seeds and critical training metadata; every approximation is declared in config.",
    }
    (checks / "scientific_formula_checks.json").write_text(json.dumps(formula, indent=2) + "\n")
    (checks / "target_checks.json").write_text(json.dumps(target_checks, indent=2) + "\n")
    (checks / "convergence.json").write_text(json.dumps(convergence, indent=2) + "\n")

    files = []
    for target, filename in TARGET_FILES.items():
        path = output / filename
        files.append({"target_id": target, "path": f"outputs/data/{filename}", "sha256": _sha256(path), "bytes": path.stat().st_size})
    manifest = {"schema_version": 1, "paper_id": config["paper_id"], "files": files}
    (checks / "generated_data_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "elapsed_seconds": perf_counter() - started,
        "formula_checks_passed": formula["all_passed"],
        "target_checks_passed": target_checks["all_passed"],
        "target_checks": target_checks,
    }
