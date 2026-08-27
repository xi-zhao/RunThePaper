from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import math
import time

import numpy as np
import scipy.linalg

from lyapunov_band import (
    density_from_potential,
    density_overlap,
    normalized_positive_density,
    smoothed_spectral_histogram,
    write_csv,
    write_json,
)


@dataclass(frozen=True)
class OffDiagonalHatanoNelsonModel:
    t: float = 1.0
    gamma: float = 1.4


@dataclass(frozen=True)
class QuasiperiodicHatanoNelsonModel:
    t: float = 1.0
    gamma: float = 1.1
    b: float = 0.7
    lam: float = 1.0
    omega: float = (math.sqrt(5.0) - 1.0) / 2.0


def sample_offdiag_bonds(length: int, disorder_strength: float, rng: np.random.Generator) -> np.ndarray:
    if length < 2:
        raise ValueError("off-diagonal chain length must be at least 2")
    return rng.uniform(-disorder_strength, disorder_strength, size=length - 1)


def quasiperiodic_onsite(length: int, model: QuasiperiodicHatanoNelsonModel) -> np.ndarray:
    if length < 2:
        raise ValueError("quasiperiodic chain length must be at least 2")
    index = np.arange(1, length + 1, dtype=float)
    phase = 2.0 * np.pi * model.omega * index
    return 2.0 * model.lam * np.cos(phase) / (1.0 - model.b * np.cos(phase))


def offdiag_hamiltonian(bonds: np.ndarray, model: OffDiagonalHatanoNelsonModel) -> np.ndarray:
    length = int(np.asarray(bonds).size + 1)
    matrix = np.zeros((length, length), dtype=complex)
    for site, disorder in enumerate(np.asarray(bonds, dtype=float)):
        matrix[site + 1, site] = model.t - model.gamma + disorder
        matrix[site, site + 1] = model.t + model.gamma + disorder
    return matrix


def quasiperiodic_hamiltonian(length: int, model: QuasiperiodicHatanoNelsonModel) -> np.ndarray:
    onsite = quasiperiodic_onsite(length, model)
    matrix = np.diag(onsite.astype(complex))
    for site in range(length - 1):
        matrix[site + 1, site] = model.t - model.gamma
        matrix[site, site + 1] = model.t + model.gamma
    return matrix


def finite_eigensystem(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values, vectors = scipy.linalg.eig(matrix, check_finite=False, overwrite_a=False)
    norms = np.linalg.norm(vectors, axis=0)
    vectors = vectors / np.maximum(norms, np.finfo(float).tiny)
    return values, vectors


def _qr_lyapunov(transfer_sequence: list[np.ndarray], shape: tuple[int, ...], qr_interval: int) -> np.ndarray:
    flat_count = int(np.prod(shape))
    q = np.broadcast_to(np.eye(2, dtype=complex), (flat_count, 2, 2)).copy()
    log_growth = np.zeros((flat_count, 2), dtype=float)
    tiny = np.finfo(float).tiny
    for step, transfer in enumerate(transfer_sequence, start=1):
        q = transfer @ q
        if step % qr_interval == 0 or step == len(transfer_sequence):
            q, r = np.linalg.qr(q)
            log_growth += np.log(np.maximum(np.abs(np.diagonal(r, axis1=-2, axis2=-1)), tiny))
    exponents = np.sort(log_growth / len(transfer_sequence), axis=-1)
    return exponents.reshape(shape + (2,))


def offdiag_lyapunov_exponents(
    energies: np.ndarray | complex,
    bonds: np.ndarray,
    model: OffDiagonalHatanoNelsonModel,
    *,
    qr_interval: int = 1,
    epsilon: float = 1e-12,
) -> np.ndarray:
    energies_array = np.asarray(energies, dtype=complex)
    flat = energies_array.reshape(-1)
    bonds = np.asarray(bonds, dtype=float)
    if bonds.size < 3:
        raise ValueError("off-diagonal Lyapunov estimate needs at least three bonds")
    transfers: list[np.ndarray] = []
    for step in range(bonds.size - 1):
        transfers.append(
            offdiag_transfer_matrices(
                flat,
                left_bond=float(bonds[step]),
                right_bond=float(bonds[step + 1]),
                model=model,
                epsilon=epsilon,
            )
        )
    return _qr_lyapunov(transfers, energies_array.shape, qr_interval)


def offdiag_transfer_matrices(
    energies: np.ndarray | complex,
    *,
    left_bond: float,
    right_bond: float,
    model: OffDiagonalHatanoNelsonModel,
    epsilon: float = 1e-12,
) -> np.ndarray:
    """Return the transfer step for the same row as ``offdiag_hamiltonian``.

    Eq. (S32) and ``offdiag_hamiltonian`` give the row equation

    ``(t+gamma+w_j) psi_(j+1) + (t-gamma+w_(j-1)) psi_(j-1) = E psi_j``.

    Keeping this rearrangement in one named function prevents the forward and
    backward hopping amplitudes from silently drifting apart again.
    """

    energies_array = np.asarray(energies, dtype=complex)
    forward = complex(model.t + model.gamma + right_bond)
    backward = complex(model.t - model.gamma + left_bond)
    if abs(forward) < epsilon:
        forward = complex(epsilon if forward == 0 else epsilon * forward / abs(forward))
    transfer = np.zeros(energies_array.shape + (2, 2), dtype=complex)
    transfer[..., 0, 0] = energies_array / forward
    transfer[..., 0, 1] = -backward / forward
    transfer[..., 1, 0] = 1.0
    return transfer


def quasiperiodic_lyapunov_exponents(
    energies: np.ndarray | complex,
    onsite: np.ndarray,
    model: QuasiperiodicHatanoNelsonModel,
    *,
    qr_interval: int = 1,
    epsilon: float = 1e-12,
) -> np.ndarray:
    energies_array = np.asarray(energies, dtype=complex)
    flat = energies_array.reshape(-1)
    onsite = np.asarray(onsite, dtype=float)
    if onsite.size < 2:
        raise ValueError("quasiperiodic Lyapunov estimate needs at least two sites")
    transfers: list[np.ndarray] = []
    for potential in onsite:
        transfers.append(
            quasiperiodic_transfer_matrices(
                flat,
                onsite=float(potential),
                model=model,
                epsilon=epsilon,
            )
        )
    return _qr_lyapunov(transfers, energies_array.shape, qr_interval)


def quasiperiodic_transfer_matrices(
    energies: np.ndarray | complex,
    *,
    onsite: float,
    model: QuasiperiodicHatanoNelsonModel,
    epsilon: float = 1e-12,
) -> np.ndarray:
    """Return the Eq. (S33) transfer step in the ED Hamiltonian convention."""

    energies_array = np.asarray(energies, dtype=complex)
    forward = complex(model.t + model.gamma)
    backward = complex(model.t - model.gamma)
    if abs(forward) < epsilon:
        forward = complex(epsilon if forward == 0 else epsilon * forward / abs(forward))
    transfer = np.zeros(energies_array.shape + (2, 2), dtype=complex)
    transfer[..., 0, 0] = (energies_array - onsite) / forward
    transfer[..., 0, 1] = -backward / forward
    transfer[..., 1, 0] = 1.0
    return transfer


def nn_potentials(exponents: np.ndarray, forward_log_mean: float) -> tuple[np.ndarray, np.ndarray]:
    exponents = np.asarray(exponents, dtype=float)
    obc = exponents[..., 1] + forward_log_mean
    pbc = np.sum(np.where(exponents > 0.0, exponents, 0.0), axis=-1) + forward_log_mean
    return obc, pbc


def essential_lyapunov_nn(exponents: np.ndarray) -> np.ndarray:
    exponents = np.asarray(exponents, dtype=float)
    lower = exponents[..., 0]
    upper = exponents[..., 1]
    return np.where(np.abs(lower) <= np.abs(upper), lower, upper)


def classify_state_nn(exponents: np.ndarray, tolerance: float) -> np.ndarray:
    exponents = np.asarray(exponents, dtype=float)
    lower = exponents[..., 0]
    upper = exponents[..., 1]
    critical = (np.abs(lower) <= tolerance) | (np.abs(upper) <= tolerance)
    alm = (lower < -tolerance) & (upper > tolerance)
    return np.where(critical, 0, np.where(alm, 1, -1))


def run_supplement_case(workspace: Path, config: dict, *, render_figures: bool = True) -> dict:
    output_root = workspace / "outputs" / "supplement_feature"
    data_dir = output_root / "data"
    figures_dir = output_root / "figures"
    checks_dir = output_root / "checks"
    started = time.perf_counter()

    offdiag = run_offdiag_example(
        data_dir,
        figures_dir,
        config["off_diagonal"],
        int(config["seed"]) + 100,
        render_figure=render_figures,
    )
    quasi = run_quasiperiodic_example(
        data_dir,
        figures_dir,
        config["quasiperiodic"],
        int(config["seed"]) + 200,
        render_figure=render_figures,
    )

    summary = {
      "status": "physically_consistent" if offdiag["status"] == "physically_consistent" and quasi["status"] == "physically_consistent" else "partial",
      "artifact_stage": config["artifact_stage"],
      "parameter_match": config["parameter_match"],
      "render_figures": render_figures,
      "runtime_seconds": time.perf_counter() - started,
      "off_diagonal": offdiag,
      "quasiperiodic": quasi,
    }
    write_json(checks_dir / "supplement_feature_checks.json", summary)
    return summary


def run_offdiag_example(
    data_dir: Path,
    figures_dir: Path,
    config: dict,
    seed: int,
    *,
    render_figure: bool = True,
) -> dict:
    model = OffDiagonalHatanoNelsonModel()
    rng = np.random.default_rng(seed)
    real_axis, imag_axis, energies = _grid(config["grid"])
    transfer_bonds = sample_offdiag_bonds(int(config["transfer_length"]) + 1, float(config["W"]), np.random.default_rng(seed + 1))
    exponents = offdiag_lyapunov_exponents(energies, transfer_bonds, model, qr_interval=int(config["qr_interval"]))
    obc_potential, _ = nn_potentials(
        exponents,
        float(
            np.mean(
                np.log(
                    np.maximum(
                        np.abs(model.t + model.gamma + transfer_bonds[1:]),
                        np.finfo(float).tiny,
                    )
                )
            )
        ),
    )
    theory_density = density_from_potential(obc_potential, real_axis, imag_axis, smoothing_sigma=float(config["grid"]["density_smoothing_sigma_cells"]))
    gamma_ess = essential_lyapunov_nn(exponents)
    theory_state = classify_state_nn(exponents, tolerance=2.0 / int(config["transfer_length"]))

    spectra_rows: list[dict] = []
    all_spectra = []
    for realization in range(int(config["ed_realizations"])):
        bonds = sample_offdiag_bonds(int(config["ed_length"]), float(config["W"]), rng)
        values = scipy.linalg.eigvals(offdiag_hamiltonian(bonds, model), check_finite=False, overwrite_a=False)
        all_spectra.append(values)
        for level, value in enumerate(values):
            spectra_rows.append(
                {
                    "target_group": "figs1",
                    "realization": realization,
                    "level": level,
                    "real_energy": value.real,
                    "imag_energy": value.imag,
                    "W": float(config["W"]),
                }
            )
    ed_spectra = np.vstack(all_spectra)
    ed_density = smoothed_spectral_histogram(ed_spectra, real_axis, imag_axis, smoothing_sigma=float(config["grid"]["density_smoothing_sigma_cells"]))

    profile_bonds = sample_offdiag_bonds(int(config["ed_length"]), float(config["W"]), np.random.default_rng(seed + 2))
    profile_values, profile_vectors = finite_eigensystem(offdiag_hamiltonian(profile_bonds, model))
    profile_probabilities = np.abs(profile_vectors) ** 2
    profile_probabilities /= np.maximum(profile_probabilities.sum(axis=0, keepdims=True), np.finfo(float).tiny)
    profile_exponents = offdiag_lyapunov_exponents(profile_values, profile_bonds, model, qr_interval=int(config["qr_interval"]))
    profile_state = classify_state_nn(profile_exponents, tolerance=2.0 / int(config["ed_length"]))
    chosen = choose_profiles(profile_values, profile_probabilities, essential_lyapunov_nn(profile_exponents), profile_state, int(config["profile_count_per_class"]))

    grid_rows = _grid_rows(real_axis, imag_axis, theory_density, ed_density, gamma_ess, theory_state, "figs1")
    profile_rows = _profile_rows(chosen, "figs1")
    write_csv(data_dir / "supplement_offdiag_grid.csv", grid_rows)
    write_csv(data_dir / "supplement_offdiag_profiles.csv", profile_rows)
    figure_path = figures_dir / "figs1_reproduction.png"
    if render_figure:
        plot_supplement_figure(
            figure_path,
            "Fig. S1 Off-diagonal Disorder",
            real_axis,
            imag_axis,
            theory_density,
            ed_density,
            gamma_ess,
            chosen,
        )

    overlap = density_overlap(theory_density, ed_density)
    result = {
        "status": "physically_consistent" if overlap >= 0.25 and chosen["alm"]["count"] > 0 and chosen["skin"]["count"] > 0 else "partial",
        "paper_item": "Fig. S1",
        "model": asdict(model),
        "generated_parameters": {
            "W": float(config["W"]),
            "ed_length": int(config["ed_length"]),
            "ed_realizations": int(config["ed_realizations"]),
            "transfer_length": int(config["transfer_length"]),
            "grid_shape": list(energies.shape),
        },
        "metrics": {
            "density_overlap": overlap,
            "alm_profiles": chosen["alm"]["count"],
            "skin_profiles": chosen["skin"]["count"],
            "critical_profiles": chosen["critical"]["count"],
        },
        "outputs": {
            "grid_csv": "outputs/supplement_feature/data/supplement_offdiag_grid.csv",
            "profile_csv": "outputs/supplement_feature/data/supplement_offdiag_profiles.csv",
            "figure": "outputs/supplement_feature/figures/figs1_reproduction.png",
        },
    }
    return result


def run_quasiperiodic_example(
    data_dir: Path,
    figures_dir: Path,
    config: dict,
    seed: int,
    *,
    render_figure: bool = True,
) -> dict:
    model = QuasiperiodicHatanoNelsonModel()
    real_axis, imag_axis, energies = _grid(config["grid"])
    onsite = quasiperiodic_onsite(int(config["transfer_length"]), model)
    exponents = quasiperiodic_lyapunov_exponents(energies, onsite, model, qr_interval=int(config["qr_interval"]))
    obc_potential, _ = nn_potentials(exponents, math.log(abs(model.t + model.gamma)))
    theory_density = density_from_potential(obc_potential, real_axis, imag_axis, smoothing_sigma=float(config["grid"]["density_smoothing_sigma_cells"]))
    gamma_ess = essential_lyapunov_nn(exponents)
    theory_state = classify_state_nn(exponents, tolerance=2.0 / int(config["transfer_length"]))

    matrix = quasiperiodic_hamiltonian(int(config["ed_length"]), model)
    values, vectors = finite_eigensystem(matrix)
    probabilities = np.abs(vectors) ** 2
    probabilities /= np.maximum(probabilities.sum(axis=0, keepdims=True), np.finfo(float).tiny)
    ed_density = smoothed_spectral_histogram(values, real_axis, imag_axis, smoothing_sigma=float(config["grid"]["density_smoothing_sigma_cells"]))
    profile_exponents = quasiperiodic_lyapunov_exponents(values, quasiperiodic_onsite(int(config["ed_length"]), model), model, qr_interval=int(config["qr_interval"]))
    profile_state = classify_state_nn(profile_exponents, tolerance=2.0 / int(config["ed_length"]))
    chosen = choose_profiles(values, probabilities, essential_lyapunov_nn(profile_exponents), profile_state, int(config["profile_count_per_class"]))

    grid_rows = _grid_rows(real_axis, imag_axis, theory_density, ed_density, gamma_ess, theory_state, "figs2")
    profile_rows = _profile_rows(chosen, "figs2")
    write_csv(data_dir / "supplement_quasiperiodic_grid.csv", grid_rows)
    write_csv(data_dir / "supplement_quasiperiodic_profiles.csv", profile_rows)
    figure_path = figures_dir / "figs2_reproduction.png"
    if render_figure:
        plot_supplement_figure(
            figure_path,
            "Fig. S2 Quasiperiodic Onsite",
            real_axis,
            imag_axis,
            theory_density,
            ed_density,
            gamma_ess,
            chosen,
        )

    overlap = density_overlap(theory_density, ed_density)
    result = {
        "status": "physically_consistent" if overlap >= 0.25 and chosen["alm"]["count"] > 0 and chosen["skin"]["count"] > 0 else "partial",
        "paper_item": "Fig. S2",
        "model": asdict(model),
        "generated_parameters": {
            "ed_length": int(config["ed_length"]),
            "transfer_length": int(config["transfer_length"]),
            "grid_shape": list(energies.shape),
        },
        "metrics": {
            "density_overlap": overlap,
            "alm_profiles": chosen["alm"]["count"],
            "skin_profiles": chosen["skin"]["count"],
            "critical_profiles": chosen["critical"]["count"],
        },
        "outputs": {
            "grid_csv": "outputs/supplement_feature/data/supplement_quasiperiodic_grid.csv",
            "profile_csv": "outputs/supplement_feature/data/supplement_quasiperiodic_profiles.csv",
            "figure": "outputs/supplement_feature/figures/figs2_reproduction.png",
        },
    }
    return result


def choose_profiles(
    values: np.ndarray,
    probabilities: np.ndarray,
    gamma_ess: np.ndarray,
    state_code: np.ndarray,
    count_per_class: int,
) -> dict[str, dict]:
    selection: dict[str, dict] = {}
    for label, code in (("alm", 1), ("critical", 0), ("skin", -1)):
        indices = np.where(state_code == code)[0]
        order = indices[np.argsort(np.abs(gamma_ess[indices]))] if indices.size else indices
        keep = order[:count_per_class]
        selection[label] = {
            "count": int(keep.size),
            "energies": values[keep],
            "profiles": probabilities[:, keep].T if keep.size else np.empty((0, probabilities.shape[0])),
        }
    return selection


def plot_supplement_figure(
    path: Path,
    title: str,
    real_axis: np.ndarray,
    imag_axis: np.ndarray,
    theory_density: np.ndarray,
    ed_density: np.ndarray,
    gamma_ess: np.ndarray,
    profiles: dict[str, dict],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    extent = [real_axis[0], real_axis[-1], imag_axis[0], imag_axis[-1]]
    axes[0].imshow(normalized_positive_density(theory_density), origin="lower", extent=extent, aspect="auto", cmap="viridis")
    axes[0].contour(real_axis, imag_axis, gamma_ess, levels=[0.0], colors="magenta", linewidths=1.0)
    axes[0].set_title("Theory density")
    axes[1].imshow(normalized_positive_density(ed_density), origin="lower", extent=extent, aspect="auto", cmap="viridis")
    axes[1].contour(real_axis, imag_axis, gamma_ess, levels=[0.0], colors="magenta", linewidths=1.0)
    axes[1].set_title("ED density")
    site_axis = None
    for label, color in (("alm", "tab:blue"), ("critical", "tab:orange"), ("skin", "tab:red")):
        profile_array = profiles[label]["profiles"]
        if profile_array.size == 0:
            continue
        site_axis = np.arange(profile_array.shape[1])
        for row in profile_array:
            axes[2].plot(site_axis, row, color=color, alpha=0.55, linewidth=1.0)
    axes[2].set_title("Representative profiles")
    axes[2].set_yscale("log")
    axes[2].set_ylim(bottom=1e-8)
    for axis in axes[:2]:
        axis.set_xlabel("Re E")
        axis.set_ylabel("Im E")
    axes[2].set_xlabel("site")
    axes[2].set_ylabel(r"$|\psi|^2$")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _grid(config: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    real_axis = np.linspace(float(config["real_min"]), float(config["real_max"]), int(config["real_points"]))
    imag_axis = np.linspace(float(config["imag_min"]), float(config["imag_max"]), int(config["imag_points"]))
    real_grid, imag_grid = np.meshgrid(real_axis, imag_axis)
    return real_axis, imag_axis, real_grid + 1j * imag_grid


def _grid_rows(
    real_axis: np.ndarray,
    imag_axis: np.ndarray,
    theory_density: np.ndarray,
    ed_density: np.ndarray,
    gamma_ess: np.ndarray,
    state_code: np.ndarray,
    group: str,
) -> list[dict]:
    rows: list[dict] = []
    for index in np.ndindex(theory_density.shape):
        rows.append(
            {
                "group": group,
                "real_energy": float(real_axis[index[1]]),
                "imag_energy": float(imag_axis[index[0]]),
                "theory_density": float(theory_density[index]),
                "ed_density": float(ed_density[index]),
                "gamma_ess": float(gamma_ess[index]),
                "state_code": int(state_code[index]),
            }
        )
    return rows


def _profile_rows(selection: dict[str, dict], group: str) -> list[dict]:
    rows: list[dict] = []
    for label, payload in selection.items():
        for profile_index, (energy, profile) in enumerate(zip(payload["energies"], payload["profiles"])):
            for site, value in enumerate(profile):
                rows.append(
                    {
                        "group": group,
                        "state_class": label,
                        "profile_index": int(profile_index),
                        "site": int(site),
                        "real_energy": float(np.real(energy)),
                        "imag_energy": float(np.imag(energy)),
                        "probability": float(value),
                    }
                )
    return rows
