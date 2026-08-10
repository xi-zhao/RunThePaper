"""Method-faithful three-dimensional Gross--Pitaevskii evolution.

The target paper's supplement specifies a two-component local-density LHY
functional, imaginary-time preparation in the experimental harmonic trap,
an instantaneous 50/50 transfer, and split-step Fourier propagation after
release.  This module implements exactly that numerical object without using
paper pixels, author arrays, or author code.

The implementation supports NumPy for local smoke tests and CuPy for the
paper-scale GPU campaign.  CuPy is deliberately optional: requesting it on a
machine where it is unavailable raises a direct, actionable error.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable

import numpy as np
from scipy.constants import atomic_mass, g, hbar, physical_constants


BOHR_M = physical_constants["Bohr radius"][0]
POTASSIUM39_MASS_KG = 38.9637064864 * atomic_mass


def load_backend(name: str) -> tuple[Any, Callable[[Any], np.ndarray]]:
    """Return an array module and a lossless host-conversion function."""

    if name == "numpy":
        return np, np.asarray
    if name != "cupy":
        raise ValueError(f"unsupported FFT backend {name!r}; expected 'numpy' or 'cupy'")
    try:
        import cupy as cp  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised on GPU host
        raise RuntimeError(
            "paper-scale backend 'cupy' was requested, but CuPy is not installed; "
            "install the CUDA-matched cupy package on the declared A100 host or "
            "select the smoke profile's numpy backend"
        ) from exc
    return cp, cp.asnumpy


@dataclass(frozen=True)
class CartesianGrid:
    """Periodic Cartesian FFT grid in SI units."""

    shape: tuple[int, int, int]
    lengths_m: tuple[float, float, float]
    axes_m: tuple[Any, Any, Any]
    k_squared: Any
    cell_volume_m3: float


def make_grid(spec: dict[str, Any], xp: Any) -> CartesianGrid:
    shape = tuple(int(value) for value in spec["shape"])
    if len(shape) != 3 or min(shape) < 8:
        raise ValueError("grid.shape must contain three integers >= 8")
    lengths_m = tuple(float(value) * 1e-6 for value in spec["lengths_micrometre"])
    if len(lengths_m) != 3 or min(lengths_m) <= 0.0:
        raise ValueError("grid.lengths_micrometre must contain three positive values")

    axes: list[Any] = []
    wavevectors: list[Any] = []
    for count, length in zip(shape, lengths_m, strict=True):
        spacing = length / count
        axes.append((xp.arange(count, dtype=xp.float64) - count // 2) * spacing)
        wavevectors.append(2.0 * np.pi * xp.fft.fftfreq(count, d=spacing))
    k_squared = (
        wavevectors[0][:, None, None] ** 2
        + wavevectors[1][None, :, None] ** 2
        + wavevectors[2][None, None, :] ** 2
    )
    return CartesianGrid(
        shape=shape,
        lengths_m=lengths_m,
        axes_m=(axes[0], axes[1], axes[2]),
        k_squared=k_squared,
        cell_volume_m3=float(np.prod([length / count for length, count in zip(lengths_m, shape, strict=True)])),
    )


def coupling_joule_m3(scattering_length_bohr: float) -> float:
    return float(
        4.0
        * np.pi
        * hbar**2
        * float(scattering_length_bohr)
        * BOHR_M
        / POTASSIUM39_MASS_KG
    )


def particle_number(field: Any, cell_volume_m3: float, xp: Any) -> float:
    return float(xp.sum(xp.abs(field) ** 2).item() * cell_volume_m3)


def normalize(field: Any, target_number: float, cell_volume_m3: float, xp: Any) -> Any:
    current = particle_number(field, cell_volume_m3, xp)
    if not np.isfinite(current) or current <= 0.0:
        raise RuntimeError(f"cannot normalize a field with particle number {current}")
    field *= np.sqrt(float(target_number) / current)
    return field


def harmonic_potential(grid: CartesianGrid, frequencies_hz: list[float], xp: Any) -> Any:
    if len(frequencies_hz) != 3:
        raise ValueError("harmonic frequencies must contain x, y, and z values")
    x, y, z = grid.axes_m
    omega = 2.0 * np.pi * np.asarray(frequencies_hz, dtype=float)
    return 0.5 * POTASSIUM39_MASS_KG * (
        float(omega[0] ** 2) * x[:, None, None] ** 2
        + float(omega[1] ** 2) * y[None, :, None] ** 2
        + float(omega[2] ** 2) * z[None, None, :] ** 2
    )


def levitation_potential(
    grid: CartesianGrid,
    spec: dict[str, Any],
    xp: Any,
) -> Any:
    """Return the gravity-compensated, period-averaged optical potential."""

    z_host = np.asarray(grid.axes_m[2].get() if hasattr(grid.axes_m[2], "get") else grid.axes_m[2])
    samples = int(spec["quadrature_samples"])
    if samples < 101:
        raise ValueError("levitation quadrature requires at least 101 phase samples")
    phase = np.linspace(0.0, 1.0, samples, dtype=float)
    amplitude = float(spec["amplitude_micrometre"]) * 1e-6
    offset = float(spec["offset_micrometre"]) * 1e-6
    waist = float(spec["waist_micrometre"]) * 1e-6
    centers = amplitude * (2.0 * np.sqrt(np.abs(1.0 - 2.0 * phase)) - 1.0) + offset

    def averaged_gaussian(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        base_parts: list[np.ndarray] = []
        derivative_parts: list[np.ndarray] = []
        for start in range(0, values.size, 128):
            displacement = values[start : start + 128, None] - centers[None, :]
            gaussian = np.exp(-2.0 * displacement**2 / waist**2)
            base_parts.append(np.mean(gaussian, axis=1))
            derivative_parts.append(
                np.mean(-4.0 * displacement / waist**2 * gaussian, axis=1)
            )
        return np.concatenate(base_parts), np.concatenate(derivative_parts)

    base, _ = averaged_gaussian(z_host)
    base_zero, derivative_zero = averaged_gaussian(np.asarray([0.0]))
    optical_amplitude = -POTASSIUM39_MASS_KG * g / float(derivative_zero[0])
    vertical = optical_amplitude * base + POTASSIUM39_MASS_KG * g * z_host
    vertical -= float(optical_amplitude * base_zero[0])
    potential = xp.asarray(vertical, dtype=xp.float64)[None, None, :]

    residual_xy_hz = spec.get("residual_xy_hz", [2.2, 7.0])
    x, y, _ = grid.axes_m
    omega_x, omega_y = 2.0 * np.pi * np.asarray(residual_xy_hz, dtype=float)
    potential = potential + 0.5 * POTASSIUM39_MASS_KG * (
        float(omega_x**2) * x[:, None, None] ** 2
        + float(omega_y**2) * y[None, :, None] ** 2
    )
    return potential


def lhy_energy_density(
    density_1_m3: Any,
    density_2_m3: Any,
    a11_bohr: float,
    a22_bohr: float,
    xp: Any,
) -> Any:
    """Simplified near-collapse LHY energy density from the supplement."""

    weighted_density = (
        float(a11_bohr) * BOHR_M * density_1_m3
        + float(a22_bohr) * BOHR_M * density_2_m3
    )
    coefficient = (
        256.0
        * np.sqrt(np.pi)
        * hbar**2
        / (15.0 * POTASSIUM39_MASS_KG)
    )
    return coefficient * xp.maximum(weighted_density, 0.0) ** 2.5


def lhy_chemical_potentials(
    density_1_m3: Any,
    density_2_m3: Any,
    a11_bohr: float,
    a22_bohr: float,
    xp: Any,
) -> tuple[Any, Any]:
    weighted_density = (
        float(a11_bohr) * BOHR_M * density_1_m3
        + float(a22_bohr) * BOHR_M * density_2_m3
    )
    common = xp.maximum(weighted_density, 0.0) ** 1.5
    coefficient = 32.0 / (3.0 * np.sqrt(np.pi))
    return (
        coefficient * coupling_joule_m3(a11_bohr) * common,
        coefficient * coupling_joule_m3(a22_bohr) * common,
    )


def lhy_finite_difference_check(
    a11_bohr: float,
    a22_bohr: float,
    density_pairs_m3: list[list[float]],
) -> dict[str, float | bool]:
    """Check the analytic LHY derivatives against finite differences."""

    worst = 0.0
    for n1, n2 in density_pairs_m3:
        analytic_1, analytic_2 = lhy_chemical_potentials(
            np.asarray(n1), np.asarray(n2), a11_bohr, a22_bohr, np
        )
        for species, analytic in [(0, float(analytic_1)), (1, float(analytic_2))]:
            density = [float(n1), float(n2)]
            step = max(1e-6 * density[species], 1e8)
            plus = density.copy()
            minus = density.copy()
            plus[species] += step
            minus[species] = max(0.0, minus[species] - step)
            denominator = plus[species] - minus[species]
            finite = float(
                (
                    lhy_energy_density(plus[0], plus[1], a11_bohr, a22_bohr, np)
                    - lhy_energy_density(minus[0], minus[1], a11_bohr, a22_bohr, np)
                )
                / denominator
            )
            scale = max(abs(analytic), abs(finite), 1e-40)
            worst = max(worst, abs(analytic - finite) / scale)
    return {"passed": worst < 2e-6, "maximum_relative_error": worst}


def _kinetic_step(field: Any, phase: Any, xp: Any) -> Any:
    return xp.fft.ifftn(xp.fft.fftn(field) * phase)


def _density_observables(
    field_1: Any,
    field_2: Any,
    grid: CartesianGrid,
    xp: Any,
) -> dict[str, float]:
    density_1 = xp.abs(field_1) ** 2
    density_2 = xp.abs(field_2) ** 2
    density = density_1 + density_2
    total = float(xp.sum(density).item() * grid.cell_volume_m3)
    x, _, z = grid.axes_m
    rms_x = np.sqrt(
        float(xp.sum(density * x[:, None, None] ** 2).item() * grid.cell_volume_m3)
        / total
    )
    rms_z = np.sqrt(
        float(xp.sum(density * z[None, None, :] ** 2).item() * grid.cell_volume_m3)
        / total
    )
    # Periodic FFT propagation is scientifically useful only while negligible
    # probability reaches the box edge.  Measure the union of the outer 10%
    # slab on every axis; unlike a size-only test this catches dilute tails.
    edge_masks = []
    for count in grid.shape:
        width = max(1, int(np.ceil(0.1 * count)))
        mask = xp.zeros(count, dtype=bool)
        mask[:width] = True
        mask[-width:] = True
        edge_masks.append(mask)
    boundary_mask = (
        edge_masks[0][:, None, None]
        | edge_masks[1][None, :, None]
        | edge_masks[2][None, None, :]
    )
    boundary_mass_fraction = float(
        xp.sum(density[boundary_mask]).item() * grid.cell_volume_m3 / total
    )
    return {
        "number_1": float(xp.sum(density_1).item() * grid.cell_volume_m3),
        "number_2": float(xp.sum(density_2).item() * grid.cell_volume_m3),
        "rms_x_micrometre": rms_x * 1e6,
        "rms_z_micrometre": rms_z * 1e6,
        # A Gaussian exp(-2 x^2/sigma_x^2) has sigma_x = 2*rms_x.
        "sigma_micrometre": 2.0 * np.sqrt(rms_x * rms_z) * 1e6,
        # A 3D inverted-parabola Thomas--Fermi profile has <z^2>=R_z^2/7.
        "tf_radius_z_micrometre": np.sqrt(7.0) * rms_z * 1e6,
        "boundary_mass_fraction": boundary_mass_fraction,
        "peak_density_cm3": float(xp.max(density).item() * 1e-6),
    }


def _atomic_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            np.savez(handle, **arrays)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def run_split_step_scenario(
    scenario: dict[str, Any],
    profile: dict[str, Any],
    interactions: dict[str, float],
    checkpoint_path: Path,
    *,
    resume: bool,
    task_hash: str,
    stop_after_real_steps: int | None = None,
) -> dict[str, np.ndarray | dict[str, Any]]:
    """Prepare and evolve one configured GPE scenario.

    The checkpoint binds the full task hash.  A changed configuration can
    never silently resume fields produced by a different numerical problem.
    """

    backend_name = str(profile["backend"])
    xp, to_host = load_backend(backend_name)
    grid = make_grid(profile["grid"], xp)
    complex_dtype = xp.complex64 if profile.get("complex_dtype") == "complex64" else xp.complex128

    total_number = float(scenario["initial_total_atom_number"])
    if total_number <= 0.0:
        raise ValueError("initial_total_atom_number must be positive")
    initial_component = str(scenario["initial_component"])
    if initial_component not in {"1", "2"}:
        raise ValueError("initial_component must be '1' or '2'")

    imaginary = profile["imaginary_time"]
    real = profile["real_time"]
    real_step_seconds = float(real["step_microsecond"]) * 1e-6
    total_steps = int(round(float(real["duration_millisecond"]) * 1e-3 / real_step_seconds))
    output_every = int(real["output_every_steps"])
    checkpoint_every = int(real["checkpoint_every_steps"])
    if total_steps < 1 or output_every < 1 or checkpoint_every < 1:
        raise ValueError("real-time step counts and intervals must be positive")

    records: list[dict[str, float]] = []
    start_step = 0
    imaginary_iterations = 0
    imaginary_converged = True
    field_1: Any
    field_2: Any
    if resume and checkpoint_path.exists():
        with np.load(checkpoint_path, allow_pickle=False) as saved:
            saved_hash = str(saved["task_hash"].item())
            if saved_hash != task_hash:
                raise RuntimeError(
                    f"checkpoint {checkpoint_path} belongs to task hash {saved_hash}, "
                    f"not current hash {task_hash}"
                )
            field_1 = xp.asarray(saved["field_1"], dtype=complex_dtype)
            field_2 = xp.asarray(saved["field_2"], dtype=complex_dtype)
            start_step = int(saved["step"].item())
            imaginary_iterations = int(saved["imaginary_iterations"].item())
            imaginary_converged = bool(saved["imaginary_converged"].item())
            decoded = json.loads(str(saved["records_json"].item()))
            records = [{key: float(value) for key, value in row.items()} for row in decoded]
    else:
        trap = harmonic_potential(grid, scenario["initial_trap_hz"], xp)
        axes = grid.axes_m
        trap_omega = 2.0 * np.pi * np.asarray(scenario["initial_trap_hz"], dtype=float)
        oscillator_lengths = np.sqrt(hbar / (POTASSIUM39_MASS_KG * trap_omega))
        gaussian = xp.exp(
            -0.5
            * (
                axes[0][:, None, None] ** 2 / oscillator_lengths[0] ** 2
                + axes[1][None, :, None] ** 2 / oscillator_lengths[1] ** 2
                + axes[2][None, None, :] ** 2 / oscillator_lengths[2] ** 2
            )
        ).astype(complex_dtype)
        ground = normalize(gaussian, total_number, grid.cell_volume_m3, xp)
        ground_scattering = interactions["a11_bohr"] if initial_component == "1" else interactions["a22_bohr"]
        ground_coupling = coupling_joule_m3(ground_scattering)
        imaginary_step = float(imaginary["step_microsecond"]) * 1e-6
        imaginary_phase = xp.exp(
            -hbar * grid.k_squared * imaginary_step / (4.0 * POTASSIUM39_MASS_KG)
        )
        prior_density: Any | None = None
        converged = False
        for iteration in range(int(imaginary["maximum_steps"])):
            ground = _kinetic_step(ground, imaginary_phase, xp)
            density = xp.abs(ground) ** 2
            ground *= xp.exp(-(trap + ground_coupling * density) * imaginary_step / hbar)
            ground = _kinetic_step(ground, imaginary_phase, xp)
            normalize(ground, total_number, grid.cell_volume_m3, xp)
            if (iteration + 1) % int(imaginary["check_every_steps"]) == 0:
                density = xp.abs(ground) ** 2
                if prior_density is not None:
                    numerator = float(xp.linalg.norm((density - prior_density).ravel()).item())
                    denominator = max(float(xp.linalg.norm(density.ravel()).item()), 1e-30)
                    if numerator / denominator < float(imaginary["density_relative_tolerance"]):
                        converged = True
                        break
                prior_density = density.copy()
        imaginary_iterations = iteration + 1
        imaginary_converged = converged
        if not converged and bool(imaginary.get("require_convergence", True)):
            raise RuntimeError(
                "imaginary-time ground state did not meet density_relative_tolerance; "
                "increase maximum_steps or use the declared convergence profile"
            )

        fraction_1 = float(scenario["post_transfer_fraction_1"])
        if not 0.0 <= fraction_1 <= 1.0:
            raise ValueError("post_transfer_fraction_1 must lie in [0, 1]")
        field_1 = ground * np.sqrt(fraction_1)
        field_2 = ground * np.sqrt(1.0 - fraction_1)
        if bool(scenario.get("single_component", False)):
            if initial_component == "1":
                field_1 = ground
                field_2 = xp.zeros_like(ground)
            else:
                field_1 = xp.zeros_like(ground)
                field_2 = ground

    release_kind = str(scenario["release_potential"])
    if release_kind == "free":
        release = xp.zeros(grid.shape, dtype=xp.float64)
    elif release_kind == "harmonic_vertical":
        release = harmonic_potential(
            grid, [0.0, 0.0, float(scenario["residual_vertical_hz"])], xp
        )
    elif release_kind == "levitation":
        release = levitation_potential(grid, scenario["levitation"], xp)
    else:
        raise ValueError(f"unsupported release_potential {release_kind!r}")

    kinetic_phase = xp.exp(
        -1j * hbar * grid.k_squared * real_step_seconds / (4.0 * POTASSIUM39_MASS_KG)
    )
    g11 = coupling_joule_m3(interactions["a11_bohr"])
    g22 = coupling_joule_m3(interactions["a22_bohr"])
    g12 = coupling_joule_m3(interactions["a12_bohr"])

    if not records:
        records.append({"time_millisecond": 0.0, **_density_observables(field_1, field_2, grid, xp)})
    requested_stop = total_steps
    if stop_after_real_steps is not None:
        requested_stop = min(total_steps, start_step + int(stop_after_real_steps))
        if requested_stop <= start_step:
            raise ValueError("stop_after_real_steps must be positive")
    include_lhy = bool(scenario.get("include_lhy", True))
    for step in range(start_step + 1, requested_stop + 1):
        field_1 = _kinetic_step(field_1, kinetic_phase, xp)
        field_2 = _kinetic_step(field_2, kinetic_phase, xp)
        density_1 = xp.abs(field_1) ** 2
        density_2 = xp.abs(field_2) ** 2
        if include_lhy:
            mu_lhy_1, mu_lhy_2 = lhy_chemical_potentials(
                density_1,
                density_2,
                interactions["a11_bohr"],
                interactions["a22_bohr"],
                xp,
            )
        else:
            mu_lhy_1 = 0.0
            mu_lhy_2 = 0.0
        field_1 *= xp.exp(
            -1j
            * (release + g11 * density_1 + g12 * density_2 + mu_lhy_1)
            * real_step_seconds
            / hbar
        )
        field_2 *= xp.exp(
            -1j
            * (release + g22 * density_2 + g12 * density_1 + mu_lhy_2)
            * real_step_seconds
            / hbar
        )
        field_1 = _kinetic_step(field_1, kinetic_phase, xp)
        field_2 = _kinetic_step(field_2, kinetic_phase, xp)

        if step % output_every == 0 or step == requested_stop:
            records.append(
                {
                    "time_millisecond": step * real_step_seconds * 1e3,
                    **_density_observables(field_1, field_2, grid, xp),
                }
            )
        if step % checkpoint_every == 0 and step < total_steps:
            _atomic_npz(
                checkpoint_path,
                task_hash=np.asarray(task_hash),
                step=np.asarray(step, dtype=np.int64),
                field_1=to_host(field_1),
                field_2=to_host(field_2),
                records_json=np.asarray(json.dumps(records, sort_keys=True)),
                imaginary_iterations=np.asarray(imaginary_iterations, dtype=np.int64),
                imaginary_converged=np.asarray(imaginary_converged),
            )

    complete = requested_stop == total_steps
    if not complete:
        _atomic_npz(
            checkpoint_path,
            task_hash=np.asarray(task_hash),
            step=np.asarray(requested_stop, dtype=np.int64),
            field_1=to_host(field_1),
            field_2=to_host(field_2),
            records_json=np.asarray(json.dumps(records, sort_keys=True)),
            imaginary_iterations=np.asarray(imaginary_iterations, dtype=np.int64),
            imaginary_converged=np.asarray(imaginary_converged),
        )

    initial_total = records[0]["number_1"] + records[0]["number_2"]
    final_total = records[-1]["number_1"] + records[-1]["number_2"]
    norm_drift = abs(final_total - initial_total) / initial_total
    result: dict[str, np.ndarray | dict[str, Any]] = {
        key: np.asarray([row[key] for row in records], dtype=float)
        for key in records[0]
    }
    result["diagnostics"] = {
        "backend": backend_name,
        "grid_shape": list(grid.shape),
        "cell_volume_m3": grid.cell_volume_m3,
        "steps_required": total_steps,
        "steps_completed": requested_stop,
        "last_step": requested_stop,
        "complete": complete,
        "norm_relative_drift": norm_drift,
        "task_hash": task_hash,
        "imaginary_time_iterations": imaginary_iterations,
        "imaginary_time_converged": imaginary_converged,
        "imaginary_time_convergence_required": bool(
            imaginary.get("require_convergence", True)
        ),
    }
    if complete and checkpoint_path.exists():
        checkpoint_path.unlink()
    return result
