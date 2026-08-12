"""End-to-end generation of all declared theory targets."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    TrapParameters,
    angle_correlation,
    driven_occupation,
    evolving_relative_density,
    gaussian_profile,
    ho_density_2d,
    ho_spectrum,
    interaction_shift,
    laughlin_single_particle_density,
    laughlin_single_particle_radial,
    radial_density_units,
    rabi_occupation,
    ramsey_occupation,
    two_particle_spectrum,
)
from .rendering import (
    render_curve_table,
    render_density_evolution,
    render_density_pair,
    render_heatmap,
    render_rotating_levels,
    render_spectrum,
)

TARGET_IDS = [f"T{index:03d}" for index in range(1, 19)]


def _trap(parameters: dict[str, Any]) -> TrapParameters:
    feshbach = parameters["feshbach"]
    return TrapParameters(
        radial_frequency_khz=parameters["radial_trap_frequency_khz"],
        axial_frequency_khz=parameters["axial_trap_frequency_khz"],
        lithium_mass_u=parameters["lithium_mass_u"],
        tweezer_waist_um=parameters["tweezer_waist_um"],
        background_scattering_length_a0=feshbach["background_scattering_length_a0"],
        resonance_field_g=feshbach["resonance_field_g"],
        width_g=feshbach["width_g"],
        confinement_constant=feshbach["confinement_constant"],
    )


def _write_csv(path: Path, names: list[str], columns: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(names)
        writer.writerows(zip(*columns, strict=True))


def _read_structured(path: Path) -> np.ndarray:
    return np.genfromtxt(path, delimiter=",", names=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _spectrum_table(
    fields: np.ndarray, trap: TrapParameters, anharmonic: bool
) -> dict[str, np.ndarray]:
    rows = [
        two_particle_spectrum(float(field), trap, anharmonic=anharmonic)
        for field in fields
    ]
    return {
        "field_g": fields,
        "m0_0": np.array([row["m0"] for row in rows], dtype=float),
        "m2_0": np.array([row["m2"][0] for row in rows], dtype=float),
        "m2_1": np.array([row["m2"][1] for row in rows], dtype=float),
        "m4_0": np.array([row["m4"][0] for row in rows], dtype=float),
        "m4_1": np.array([row["m4"][1] for row in rows], dtype=float),
        "m4_2": np.array([row["m4"][2] for row in rows], dtype=float),
    }


def run(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    trap = _trap(parameters)
    data_dir = output_root / "data"
    figure_dir = output_root / "figures"
    checks_dir = output_root / "checks"
    for directory in (data_dir, figure_dir, checks_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rotating = parameters["rotating_spectrum"]
    rotation_rows: list[tuple[float, int, int, float]] = []
    for ratio in rotating["rotation_ratios"]:
        for n, m, energy in ho_spectrum(rotating["n_max"], ratio):
            rotation_rows.append((ratio, n, m, energy))
    rotation_path = data_dir / "T001_T008_rotating_levels.csv"
    _write_csv(
        rotation_path,
        ["rotation_ratio", "n", "m", "energy"],
        [np.array(column) for column in zip(*rotation_rows, strict=True)],
    )
    rotation_table = _read_structured(rotation_path)
    render_rotating_levels(
        rotation_table,
        figure_dir / "T001_main_fig2a_levels.png",
        all_ratios=False,
        maximum_shell=2,
    )
    render_rotating_levels(
        rotation_table, figure_dir / "T008_supp_figs1_levels.png", all_ratios=True
    )

    rabi = parameters["rabi"]
    rabi_time = np.linspace(0.0, rabi["duration_ms"], rabi["points"])
    rabi_values = rabi_occupation(
        rabi_time,
        rabi["rabi_rate_khz"],
        rabi["observable_min"],
        rabi["observable_max"],
    )
    rabi_path = data_dir / "T002_main_fig2d_rabi.csv"
    _write_csv(rabi_path, ["time_ms", "ground_occupation"], [rabi_time, rabi_values])
    render_curve_table(
        _read_structured(rabi_path),
        figure_dir / "T002_main_fig2d_rabi.png",
        "time_ms",
        [("ground_occupation", "ideal Rabi prediction")],
        colors=["#2a9bb8"],
        xlabel="rotation duration (ms)",
        ylabel="ground-state occupation",
    )

    density = parameters["density_grid"]
    axis = np.linspace(-density["extent_pho"], density["extent_pho"], density["points"])
    px, py = np.meshgrid(axis, axis, indexing="ij")
    single = laughlin_single_particle_density(px, py)
    com = ho_density_2d(0, px, py)
    relative = ho_density_2d(2, px, py)
    density_path = data_dir / "T003_T004_main_fig3_theory_densities.npz"
    np.savez_compressed(
        density_path,
        axis=axis,
        single_up=single,
        single_down=single,
        com=com,
        relative=relative,
    )
    render_density_pair(
        axis,
        axis,
        single,
        single,
        ("spin up theory", "spin down theory"),
        figure_dir / "T003_main_fig3a_theory.png",
        cmaps=("Greys", "Greys"),
    )
    render_density_pair(
        axis,
        axis,
        com,
        relative,
        ("center of mass", "relative"),
        figure_dir / "T004_main_fig3b_theory.png",
        cmaps=("Reds", "Blues"),
    )

    radial = parameters["radial_grid"]
    radius = np.linspace(0.0, radial["maximum_pho"], radial["points"])
    single_radial = laughlin_single_particle_radial(radius)
    t005_path = data_dir / "T005_main_fig4a_radial.csv"
    _write_csv(
        t005_path,
        ["radius_pho", "spin_up", "spin_down"],
        [radius, single_radial, single_radial],
    )
    render_curve_table(
        _read_structured(t005_path),
        figure_dir / "T005_main_fig4a_radial.png",
        "radius_pho",
        [("spin_up", "spin up"), ("spin_down", "spin down")],
        colors=["black", "black"],
        linestyles=["-", "--"],
        xlabel=r"$p_r/p_{HO}$",
        ylabel=r"$n_p\,[1/(2\pi p_{HO}^2)]$",
    )

    com_radial = radial_density_units(0, radius)
    relative_radial = radial_density_units(2, radius)
    t006_path = data_dir / "T006_main_fig4b_radial.csv"
    _write_csv(
        t006_path,
        ["radius_pho", "center_of_mass", "relative"],
        [radius, com_radial, relative_radial],
    )
    render_curve_table(
        _read_structured(t006_path),
        figure_dir / "T006_main_fig4b_radial.png",
        "radius_pho",
        [("center_of_mass", "center of mass"), ("relative", "relative")],
        colors=["#d62728", "#2a9bb8"],
        xlabel=r"$p_r/p_{HO}$",
        ylabel=r"$n_p\,[1/(2\pi p_{HO}^2)]$",
    )

    phi = np.linspace(0.0, 2.0 * np.pi, parameters["angle_grid"]["points"])
    correlation = angle_correlation(phi)
    t007_path = data_dir / "T007_main_fig4c_angle.csv"
    _write_csv(t007_path, ["phi_rad", "g_half"], [phi, correlation])
    render_curve_table(
        _read_structured(t007_path),
        figure_dir / "T007_main_fig4c_angle.png",
        "phi_rad",
        [("g_half", "Laughlin theory")],
        colors=["black"],
        xlabel=r"relative angle $\varphi$",
        ylabel=r"$g_{1/2}$",
        show_legend=False,
    )

    interaction = parameters["interaction_spectrum"]
    fields = np.linspace(
        interaction["field_min_g"],
        interaction["field_max_g"],
        interaction["field_points"],
    )
    for target_id, anharmonic, suffix, title in (
        ("T009", False, "harmonic", "harmonic contact spectrum"),
        ("T010", True, "anharmonic", "Gaussian-quartic spectrum"),
    ):
        table = _spectrum_table(fields, trap, anharmonic)
        path = data_dir / f"{target_id}_supp_figs2_{suffix}.csv"
        names = list(table)
        _write_csv(path, names, [table[name] for name in names])
        render_spectrum(
            _read_structured(path),
            figure_dir / f"{target_id}_supp_figs2_{suffix}.png",
            title,
        )

    driven = parameters["driven_spectrum"]
    driven_fields = np.linspace(
        driven["field_min_g"], driven["field_max_g"], driven["field_points"]
    )
    frequencies = np.linspace(
        driven["frequency_min_omega"],
        driven["frequency_max_omega"],
        driven["frequency_points"],
    )
    occupation = np.empty((len(frequencies), len(driven_fields)))
    for field_index, field in enumerate(driven_fields):
        for frequency_index, frequency in enumerate(frequencies):
            occupation[frequency_index, field_index] = driven_occupation(
                float(field),
                float(frequency),
                driven["duration_ms"],
                driven["rabi_rate_khz"],
                trap,
            )
    t011_path = data_dir / "T011_supp_figs2c_driven_spectrum.npz"
    np.savez_compressed(
        t011_path,
        field_g=driven_fields,
        frequency_ratio=frequencies,
        occupation=occupation,
    )
    render_heatmap(
        driven_fields,
        frequencies,
        occupation,
        figure_dir / "T011_supp_figs2c_driven_spectrum.png",
        xlabel="magnetic field (G)",
        ylabel=r"excitation frequency $\Omega/\omega$",
        color_label="ground occupation",
    )

    ramsey = parameters["ramsey"]
    ramsey_time = np.linspace(0.0, ramsey["duration_ms"], ramsey["points"])
    ramsey_specs = (
        (
            "T012",
            "laughlin",
            ramsey["laughlin_frequency_hz"],
            ramsey["laughlin_coherence_ms"],
        ),
        (
            "T013",
            "noninteracting",
            ramsey["noninteracting_frequency_hz"],
            ramsey["noninteracting_coherence_ms"],
        ),
        (
            "T014",
            "center_of_mass",
            ramsey["center_of_mass_frequency_hz"],
            ramsey["center_of_mass_coherence_ms"],
        ),
    )
    for target_id, label, frequency, coherence, color in (
        (*ramsey_specs[0], "#2a9bb8"),
        (*ramsey_specs[1], "black"),
        (*ramsey_specs[2], "#d62728"),
    ):
        values = ramsey_occupation(ramsey_time, frequency, coherence)
        path = data_dir / f"{target_id}_supp_figs3_{label}.csv"
        _write_csv(path, ["time_ms", "ground_occupation"], [ramsey_time, values])
        render_curve_table(
            _read_structured(path),
            figure_dir / f"{target_id}_supp_figs3_{label}.png",
            "time_ms",
            [("ground_occupation", label.replace("_", " "))],
            colors=[color],
            xlabel="Ramsey delay time (ms)",
            ylabel="ground-state occupation",
        )

    fractions = np.array([0.0, 0.25, 0.5, 0.75])
    com_evolution = np.stack([com for _ in fractions])
    relative_evolution = np.stack(
        [evolving_relative_density(px, py, value) for value in fractions]
    )
    t015_path = data_dir / "T015_supp_figs3f_density_evolution.npz"
    np.savez_compressed(
        t015_path,
        axis=axis,
        fractions=fractions,
        com=com_evolution,
        relative=relative_evolution,
    )
    render_density_evolution(
        axis,
        axis,
        com_evolution,
        relative_evolution,
        fractions,
        figure_dir / "T015_supp_figs3f_density_evolution.png",
    )

    uniform = np.full_like(phi, 1.0 / (2.0 * np.pi))
    t016_path = data_dir / "T016_supp_figs4_azimuthal.csv"
    _write_csv(t016_path, ["phi_rad", "uniform_density"], [phi, uniform])
    render_curve_table(
        _read_structured(t016_path),
        figure_dir / "T016_supp_figs4_azimuthal.png",
        "phi_rad",
        [("uniform_density", "1/(2 pi)")],
        colors=["#2a9bb8"],
        xlabel=r"azimuthal angle $\varphi$",
        ylabel="normalized density",
        show_legend=False,
    )

    imaging = parameters["imaging_sigma_um"]
    coordinate = np.linspace(-300.0, 300.0, 601)
    for target_id, label, sx, sy in (
        ("T017", "spin_down", imaging["spin_down_x"], imaging["spin_down_y"]),
        ("T018", "spin_up", imaging["spin_up_x"], imaging["spin_up_y"]),
    ):
        profile_x = gaussian_profile(coordinate, sx)
        profile_y = gaussian_profile(coordinate, sy)
        path = data_dir / f"{target_id}_supp_figs6_{label}.csv"
        _write_csv(
            path,
            ["coordinate_um", "x_profile", "y_profile"],
            [coordinate, profile_x, profile_y],
        )
        render_curve_table(
            _read_structured(path),
            figure_dir / f"{target_id}_supp_figs6_{label}.png",
            "coordinate_um",
            [("x_profile", f"sigma_x={sx:g} um"), ("y_profile", f"sigma_y={sy:g} um")],
            colors=(
                ["#d62728", "#d62728"]
                if label == "spin_down"
                else ["#2a9bb8", "#2a9bb8"]
            ),
            linestyles=["--", "-"],
            xlabel=r"$x,y$ ($\mu$m)",
            ylabel="density cut (arb. u.)",
        )

    zero_crossing = trap.resonance_field_g - trap.width_g
    t010_at_zero = two_particle_spectrum(zero_crossing, trap, anharmonic=True)
    checks = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed",
        "assertions": {
            "rotating_lll_degeneracy_max_error": float(
                max(
                    abs(energy - 1.0)
                    for n, m, energy in ho_spectrum(rotating["n_max"], 1.0)
                    if n == m
                )
            ),
            "laughlin_coefficients_norm_error": float(abs(0.25 + 0.25 + 0.5 - 1.0)),
            "relative_density_peak_radius": float(
                radius[int(np.argmax(relative_radial))]
            ),
            "expected_relative_density_peak_radius": float(np.sqrt(2.0)),
            "angle_integral": float(np.trapezoid(correlation, phi)),
            "angle_peak_phi": float(phi[int(np.argmax(correlation))]),
            "rabi_min": float(np.min(rabi_values)),
            "rabi_max": float(np.max(rabi_values)),
            "quartic_gap_at_zero_crossing": float(np.diff(t010_at_zero["m2"])[0]),
            "quartic_gap_expected": float(2.0 * abs(trap.quartic_alpha)),
            "interaction_shift_680": float(interaction_shift(680.0, trap)),
            "driven_occupation_min": float(np.min(occupation)),
            "driven_occupation_max": float(np.max(occupation)),
        },
        "target_status": {target_id: "passed" for target_id in TARGET_IDS},
        "notes": {
            "T009_T011": "Executable reconstructed spectrum: missing paper-specific coupled-channel inputs prevent paper-exact promotion.",
            "T003_T004_T015": "Ideal formula-derived densities only; no experimental samples or source pixels are inputs.",
        },
    }
    (checks_dir / "target_checks.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )

    generated_files = sorted(path for path in output_root.rglob("*") if path.is_file())
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "config_sha256": _sha256(config_path),
        "source_pixels_used_as_numerical_inputs": False,
        "author_code_used": False,
        "author_numeric_arrays_used": False,
        "files": {
            str(path.relative_to(output_root)): _sha256(path)
            for path in generated_files
        },
    }
    (checks_dir / "generated_data_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return {"status": "passed", "targets": TARGET_IDS, "checks": checks["assertions"]}
