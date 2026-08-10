"""Generate every declared numerical target from the independently coded model."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .model import PaperParameters, PhysicalScales, fizeau_shift, physical_scales
from .observables import (
    fock_energies_from_ratios,
    fock_energies_over_u,
    required_k_for_resonance,
    solve_observables,
)
from .rendering import (
    COLORS,
    plot_analytic_numeric,
    plot_energy_cases,
    plot_fizeau,
    plot_main_fig2,
    plot_main_multiphonon,
    plot_nonspinning_diagnostics,
    plot_rotation_sweep,
    plot_s8,
    plot_s9,
)


@dataclass
class ReproductionContext:
    parameters: PaperParameters
    scales: PhysicalScales
    settings: dict[str, Any]
    cache: dict[tuple, dict] = field(default_factory=dict)

    def point(
        self,
        *,
        k: float,
        direction: int,
        omega_khz: float,
        power_w: float,
        cutoff: int | None = None,
    ) -> dict:
        selected_cutoff = int(cutoff or self.parameters.fock_cutoff)
        key = (
            round(float(k), 12),
            int(direction),
            round(float(omega_khz), 12),
            float(power_w),
            selected_cutoff,
        )
        if key not in self.cache:
            self.cache[key] = solve_observables(
                self.parameters,
                self.scales,
                k=float(k),
                direction=int(direction),
                omega_khz=float(omega_khz),
                input_power_w=float(power_w),
                cutoff=selected_cutoff,
            )
        return self.cache[key]

    def grid(self, name: str) -> np.ndarray:
        start, stop, count = self.settings["grids"][name]
        return np.linspace(float(start), float(stop), int(count))

    def sweep(
        self,
        *,
        grid_name: str,
        directions: list[int],
        omega_khz: float,
        power_w: float,
    ) -> list[dict]:
        return [
            self.point(k=float(k), direction=direction, omega_khz=omega_khz, power_w=power_w)
            for direction in directions
            for k in self.grid(grid_name)
        ]


@dataclass(frozen=True)
class EnergyCaseSpec:
    title: str
    direction: int
    omega_khz: float
    k: float
    resonant_targets: tuple[int, ...]
    ideal_fizeau_over_u: float | None = None


class ArtifactWriter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.data_files: list[Path] = []

    def csv(self, relative: str, rows: list[dict], fields: list[str]) -> Path:
        path = self.root / "outputs" / "data" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({field: _scalar(row.get(field)) for field in fields})
        self.data_files.append(path)
        return path

    def json(self, category: str, relative: str, payload: Any) -> Path:
        path = self.root / "outputs" / category / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if category == "data":
            self.data_files.append(path)
        return path

    def figure(self, relative: str) -> Path:
        return self.root / "outputs" / "figures" / relative


CORRELATION_FIELDS = [
    "k",
    "direction",
    "omega_khz",
    "input_power_w",
    "cutoff",
    "delta_l_over_u",
    "delta_f_over_u",
    "mean_n",
    "g1",
    "g2",
    "g3",
    "g4",
    "analytic_g2",
    "analytic_g3",
    "f",
    "f2",
    "one_photon_blockade",
    "two_photon_blockade",
    "pit_2_to_4",
    "residual_norm",
    "trace_error",
    "hermiticity_error",
    "minimum_eigenvalue",
    "tail_probability",
]


def run_reproduction(config_path: Path) -> dict:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    settings = payload["parameters"]
    parameters = PaperParameters.from_mapping(settings)
    context = ReproductionContext(parameters, physical_scales(parameters), settings)
    root = config_path.resolve().parents[1]
    writer = ArtifactWriter(root)
    checks: dict[str, dict] = {}

    _generate_formula_targets(context, writer, checks)
    _generate_main_figures(context, writer, checks)
    _generate_supplement_correlations(context, writer, checks)
    convergence = _convergence_check(context)
    writer.json("checks", "convergence.json", convergence)
    checks["convergence"] = {
        "passed": convergence["passed"],
        "metrics": convergence,
    }

    scale_payload = {
        "omega0_rad_s": context.scales.omega0_rad_s,
        "gamma_rad_s": context.scales.gamma_rad_s,
        "kerr_u_rad_s": context.scales.kerr_u_rad_s,
        "u_over_gamma": context.scales.u_over_gamma,
        "fizeau_eta": context.scales.fizeau_eta,
        "delta_f_over_u_at_29khz": fizeau_shift(context.scales, 1, 29.0) / context.scales.kerr_u_rad_s,
    }
    writer.json("checks", "physical_scales.json", scale_payload)

    failures = [target for target, item in checks.items() if not bool(item.get("passed"))]
    check_payload = {
        "status": "passed" if not failures else "failed",
        "paper_id": "1807.10084",
        "targets_total": 15,
        "targets_passed": sum(bool(item.get("passed")) for key, item in checks.items() if key.startswith("T")),
        "failed": failures,
        "checks": checks,
    }
    writer.json("checks", "target_checks.json", check_payload)
    if failures:
        raise RuntimeError(f"scientific target checks failed: {failures}")

    manifest = {
        "schema_version": 1,
        "paper_id": "1807.10084",
        "provenance": "independent_numerics",
        "files": [
            {
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(writer.data_files)
        ],
    }
    writer.json("checks", "generated_data_manifest.json", manifest)
    return {
        "status": "passed",
        "targets_passed": 15,
        "data_files": len(writer.data_files),
        "cached_steady_states": len(context.cache),
    }


def _generate_formula_targets(context: ReproductionContext, writer: ArtifactWriter, checks: dict) -> None:
    parameters = context.parameters
    scales = context.scales

    main_fig1_cases = _energy_cases(
        context,
        [
            EnergyCaseSpec("left: 1PB", 1, 29.0, 1.5, (1,), 0.5),
            EnergyCaseSpec("right: two-photon resonance", -1, 29.0, 1.5, (2,), 0.5),
        ],
        maximum_n=2,
    )
    writer.csv("main_fig1_levels.csv", _flatten_energy_cases("T001", main_fig1_cases), _energy_fields())
    plot_energy_cases(main_fig1_cases, writer.figure("main_fig1_levels.png"), columns=2)
    checks["T001"] = {"passed": True, "metrics": _energy_resonance_metrics(main_fig1_cases)}

    main_fig3_cases = _energy_cases(
        context,
        [
            EnergyCaseSpec("left: 2PB", 1, 29.0, 2.5, (2,), 0.5),
            EnergyCaseSpec("right: three-photon resonance", -1, 29.0, 2.5, (3,), 0.5),
        ],
        maximum_n=3,
    )
    writer.csv("main_fig3_levels.csv", _flatten_energy_cases("T004", main_fig3_cases), _energy_fields())
    plot_energy_cases(main_fig3_cases, writer.figure("main_fig3d.png"), columns=2)
    checks["T004"] = {"passed": True, "metrics": _energy_resonance_metrics(main_fig3_cases)}

    omega_values = np.linspace(0.0, 60.0, 121)
    fizeau_rows = [
        {
            "omega_khz": float(omega),
            "direction": direction,
            "delta_f_mhz": fizeau_shift(scales, direction, float(omega)) / 1e6,
            "delta_f_over_u": fizeau_shift(scales, direction, float(omega)) / scales.kerr_u_rad_s,
        }
        for direction in [1, -1]
        for omega in omega_values
    ]
    writer.csv("supp_fig_s1_fizeau.csv", fizeau_rows, ["omega_khz", "direction", "delta_f_mhz", "delta_f_over_u"])
    plot_fizeau(fizeau_rows, writer.figure("supp_fig_s1.png"))
    checks["T006"] = {
        "passed": np.isclose(fizeau_rows[60]["delta_f_mhz"], -fizeau_rows[-61]["delta_f_mhz"]),
        "metrics": {"delta_f_mhz_at_60khz": fizeau_rows[120]["delta_f_mhz"]},
    }

    supplement_s2_cases = _energy_cases(
        context,
        [
            EnergyCaseSpec("1PB: k=1", 0, 0.0, 1.0, (1,), 0.0),
            EnergyCaseSpec("2PB: k=2", 0, 0.0, 2.0, (2,), 0.0),
        ],
        maximum_n=3,
    )
    writer.csv("supp_fig_s2_levels.csv", _flatten_energy_cases("T007", supplement_s2_cases), _energy_fields())
    plot_energy_cases(supplement_s2_cases, writer.figure("supp_fig_s2.png"), columns=2)
    checks["T007"] = {"passed": True, "metrics": _energy_resonance_metrics(supplement_s2_cases)}

    table_specs = [
        (1, 58.0, 1.0, 1, "1PB", 3, "PIT (3PR)", True),
        (2, 58.0, 1.0, 3, "PIT (3PR)", 1, "1PB", False),
        (3, 58.0, 1.0, 2, "2PB", 4, "PIT (4PR)", True),
        (4, 58.0, 1.0, 4, "PIT (4PR)", 2, "2PB", False),
        (5, 29.0, 0.5, 2, "2PB", 3, "PIT (3PR)", True),
        (6, 29.0, 0.5, 3, "PIT (3PR)", 2, "2PB", False),
        (7, 29.0, 0.5, 1, "1PB", 2, "2PB", True),
        (8, 29.0, 0.5, 2, "2PB", 1, "1PB", False),
    ]
    supplement_s3_specs: list[EnergyCaseSpec] = []
    table_rows: list[dict] = []
    table_passed = True
    for number, omega, fizeau_over_u, positive_order, expected_positive, negative_order, expected_negative, allowed in table_specs:
        positive_k = required_k_for_resonance(
            direction=1,
            fizeau_over_u=fizeau_over_u,
            photon_order=positive_order,
        )
        negative_k = required_k_for_resonance(
            direction=-1,
            fizeau_over_u=fizeau_over_u,
            photon_order=negative_order,
        )
        common_drive_compatible = np.isclose(positive_k, negative_k, atol=1e-12)
        positive_stats = context.point(
            k=positive_k,
            direction=1,
            omega_khz=omega,
            power_w=parameters.strong_power_w,
        )
        negative_stats = context.point(
            k=negative_k,
            direction=-1,
            omega_khz=omega,
            power_w=parameters.strong_power_w,
        )
        actual_positive = _classification(positive_stats)
        actual_negative = _classification(negative_stats)
        classification_matches = (
            actual_positive == expected_positive.split(" ")[0]
            and actual_negative == expected_negative.split(" ")[0]
        )
        row_passed = classification_matches and common_drive_compatible == allowed
        table_passed &= row_passed
        table_rows.append(
            {
                "case_number": number,
                "omega_khz": omega,
                "ideal_fizeau_over_u": fizeau_over_u,
                "required_k_positive": positive_k,
                "required_k_negative": negative_k,
                "shared_k": positive_k if common_drive_compatible else "",
                "common_drive_gap": abs(positive_k - negative_k),
                "positive_expected": expected_positive,
                "positive_computed": actual_positive,
                "negative_expected": expected_negative,
                "negative_computed": actual_negative,
                "allowed": allowed,
                "common_drive_compatible": common_drive_compatible,
                "check_passed": row_passed,
                "reason": (
                    "both resonances require the same laser detuning"
                    if common_drive_compatible
                    else "the two resonances require different laser detunings"
                ),
            }
        )
        supplement_s3_specs.extend(
            [
                EnergyCaseSpec(
                    f"({number}) +: {expected_positive}; k={positive_k:g}",
                    1,
                    omega,
                    positive_k,
                    (positive_order,),
                    fizeau_over_u,
                ),
                EnergyCaseSpec(
                    f"({number}) -: {expected_negative}; k={negative_k:g}",
                    -1,
                    omega,
                    negative_k,
                    (negative_order,),
                    fizeau_over_u,
                ),
            ]
        )
    supplement_s3_cases = _energy_cases(context, supplement_s3_specs, maximum_n=4)
    writer.csv("supp_fig_s3_levels.csv", _flatten_energy_cases("T008", supplement_s3_cases), _energy_fields())
    plot_energy_cases(supplement_s3_cases, writer.figure("supp_fig_s3.png"), columns=4)
    checks["T008"] = {
        "passed": table_passed and len(supplement_s3_cases) == 16,
        "metrics": {
            "directional_panels": len(supplement_s3_cases),
            "allowed_pairs": sum(bool(row["allowed"]) for row in table_rows),
            "prohibited_pairs": sum(not bool(row["allowed"]) for row in table_rows),
            "levels": _energy_resonance_metrics(supplement_s3_cases),
        },
    }

    writer.csv(
        "supp_table_s2_cases.csv",
        table_rows,
        [
            "case_number",
            "omega_khz",
            "ideal_fizeau_over_u",
            "required_k_positive",
            "required_k_negative",
            "shared_k",
            "common_drive_gap",
            "positive_expected",
            "positive_computed",
            "negative_expected",
            "negative_computed",
            "allowed",
            "common_drive_compatible",
            "check_passed",
            "reason",
        ],
    )
    writer.json("checks", "supp_table_s2_check.json", {"passed": table_passed, "rows": table_rows})
    checks["T015"] = {
        "passed": table_passed,
        "metrics": {"rows": len(table_rows), "allowed_rows": 4, "prohibited_rows": 4},
    }


def _generate_main_figures(context: ReproductionContext, writer: ArtifactWriter, checks: dict) -> None:
    p = context.parameters
    rows_fig2 = context.sweep(grid_name="main_fig2", directions=[-1, 0, 1], omega_khz=29.0, power_w=p.weak_power_w)
    writer.csv("main_fig2_correlations.csv", rows_fig2, CORRELATION_FIELDS)
    plot_main_fig2(rows_fig2, writer.figure("main_fig2.png"))
    plus = context.point(k=1.5, direction=1, omega_khz=29.0, power_w=p.weak_power_w)
    minus = context.point(k=1.5, direction=-1, omega_khz=29.0, power_w=p.weak_power_w)
    checks["T002"] = {
        "passed": plus["g2"] < 0.002 and 500.0 < minus["g2"] < 800.0,
        "metrics": {"g2_positive": plus["g2"], "g2_negative": minus["g2"], "paper_reported": [0.001, 673]},
    }

    rows_fig3 = context.sweep(grid_name="main_fig3", directions=[1, -1], omega_khz=29.0, power_w=p.strong_power_w)
    distributions_fig3 = _distribution_rows(context, [(2.5, 1, 29.0), (2.5, -1, 29.0)], p.strong_power_w)
    writer.csv("main_fig3_correlations.csv", rows_fig3, CORRELATION_FIELDS)
    writer.csv("main_fig3_distributions.csv", distributions_fig3, _distribution_fields())
    plot_main_multiphonon(
        rows_fig3,
        distributions_fig3,
        writer.figure("main_fig3_abc.png"),
        focus_k=2.5,
        focus_direction=1,
        xlim=(2.0, 3.0),
        title_left="(c-i) left: 2PB",
        title_right="(c-ii) right: PIT",
    )
    positive_25 = context.point(k=2.5, direction=1, omega_khz=29.0, power_w=p.strong_power_w)
    negative_25 = context.point(k=2.5, direction=-1, omega_khz=29.0, power_w=p.strong_power_w)
    checks["T003"] = {
        "passed": positive_25["two_photon_blockade"] and negative_25["pit_2_to_4"] and 25.0 < negative_25["g2"] < 50.0 and 800.0 < negative_25["g3"] < 1300.0,
        "metrics": {"positive_g2": positive_25["g2"], "positive_g3": positive_25["g3"], "negative_g2": negative_25["g2"], "negative_g3": negative_25["g3"]},
    }

    rows_fig4 = context.sweep(grid_name="main_fig4", directions=[1, -1], omega_khz=29.0, power_w=p.strong_power_w)
    distributions_fig4 = _distribution_rows(context, [(1.5, 1, 29.0), (1.5, -1, 29.0)], p.strong_power_w)
    writer.csv("main_fig4_correlations.csv", rows_fig4, CORRELATION_FIELDS)
    writer.csv("main_fig4_distributions.csv", distributions_fig4, _distribution_fields())
    plot_main_multiphonon(
        rows_fig4,
        distributions_fig4,
        writer.figure("main_fig4.png"),
        focus_k=1.5,
        focus_direction=-1,
        xlim=(0.8, 2.2),
        title_left="(c-i) left: 1PB",
        title_right="(c-ii) right: 2PB",
    )
    positive_15 = context.point(k=1.5, direction=1, omega_khz=29.0, power_w=p.strong_power_w)
    negative_15 = context.point(k=1.5, direction=-1, omega_khz=29.0, power_w=p.strong_power_w)
    checks["T005"] = {
        "passed": positive_15["one_photon_blockade"] and negative_15["two_photon_blockade"],
        "metrics": {"positive_g2": positive_15["g2"], "negative_g2": negative_15["g2"], "negative_g3": negative_15["g3"]},
    }


def _generate_supplement_correlations(context: ReproductionContext, writer: ArtifactWriter, checks: dict) -> None:
    p = context.parameters
    rows_s4 = context.sweep(grid_name="supp_fig_s4", directions=[0], omega_khz=0.0, power_w=p.weak_power_w)
    distributions_s4 = _distribution_rows(context, [(1.0, 0, 0.0), (2.0, 0, 0.0)], p.weak_power_w)
    writer.csv("supp_fig_s4_correlations.csv", rows_s4, CORRELATION_FIELDS)
    writer.csv("supp_fig_s4_distributions.csv", distributions_s4, _distribution_fields())
    plot_nonspinning_diagnostics(rows_s4, distributions_s4, writer.figure("supp_fig_s4.png"), probe_ks=[1.0, 2.0], title="Supplement Fig. S4: weak drive")
    s4_k1 = context.point(k=1.0, direction=0, omega_khz=0.0, power_w=p.weak_power_w)
    s4_k2 = context.point(k=2.0, direction=0, omega_khz=0.0, power_w=p.weak_power_w)
    checks["T009"] = {"passed": s4_k1["one_photon_blockade"] and s4_k2["pit_2_to_4"], "metrics": {"g2_k1": s4_k1["g2"], "g2_k2": s4_k2["g2"]}}

    rows_s5 = context.sweep(grid_name="supp_fig_s5", directions=[0], omega_khz=0.0, power_w=p.strong_power_w)
    distributions_s5 = _distribution_rows(context, [(1.0, 0, 0.0), (2.0, 0, 0.0), (3.0, 0, 0.0)], p.strong_power_w)
    writer.csv("supp_fig_s5_correlations.csv", rows_s5, CORRELATION_FIELDS)
    writer.csv("supp_fig_s5_distributions.csv", distributions_s5, _distribution_fields())
    plot_nonspinning_diagnostics(rows_s5, distributions_s5, writer.figure("supp_fig_s5.png"), probe_ks=[1.0, 2.0, 3.0], title="Supplement Fig. S5: strong drive")
    s5_k1 = context.point(k=1.0, direction=0, omega_khz=0.0, power_w=p.strong_power_w)
    s5_k2 = context.point(k=2.0, direction=0, omega_khz=0.0, power_w=p.strong_power_w)
    s5_k3 = context.point(k=3.0, direction=0, omega_khz=0.0, power_w=p.strong_power_w)
    checks["T010"] = {"passed": s5_k1["one_photon_blockade"] and s5_k2["two_photon_blockade"] and s5_k3["pit_2_to_4"], "metrics": {"g2_k1": s5_k1["g2"], "g2_k2": s5_k2["g2"], "g3_k3": s5_k3["g3"]}}

    rows_s6 = context.sweep(grid_name="supp_fig_s6", directions=[0], omega_khz=0.0, power_w=p.weak_power_w)
    writer.csv("supp_fig_s6_analytic_numeric.csv", rows_s6, CORRELATION_FIELDS)
    plot_analytic_numeric(rows_s6, writer.figure("supp_fig_s6.png"))
    numeric_min_g2 = min(rows_s6, key=lambda row: row["g2"])
    numeric_max_g2 = max(rows_s6, key=lambda row: row["g2"])
    numeric_max_g3 = max(rows_s6, key=lambda row: row["g3"])
    checks["T011"] = {
        "passed": abs(numeric_min_g2["k"] - 1.0) <= 0.02 and abs(numeric_max_g2["k"] - 2.0) <= 0.03 and abs(numeric_max_g3["k"] - 3.0) <= 0.03,
        "metrics": {"g2_dip_k": numeric_min_g2["k"], "g2_peak_k": numeric_max_g2["k"], "g3_peak_k": numeric_max_g3["k"]},
    }

    rows_s7: list[dict] = []
    for direction in [-1, 1]:
        for omega in context.settings["rotation_sweep_khz"]:
            rows_s7.extend(
                context.sweep(grid_name="supp_fig_s7", directions=[direction], omega_khz=float(omega), power_w=p.weak_power_w)
            )
    writer.csv("supp_fig_s7_rotation_sweep.csv", rows_s7, CORRELATION_FIELDS)
    plot_rotation_sweep(rows_s7, writer.figure("supp_fig_s7.png"))
    dip_positions: dict[str, float] = {}
    for direction in [-1, 1]:
        for omega in context.settings["rotation_sweep_khz"]:
            selected = [row for row in rows_s7 if row["direction"] == direction and np.isclose(row["omega_khz"], omega)]
            dip_positions[f"{direction}:{omega}"] = min(selected, key=lambda row: row["g2"])["k"]
    checks["T012"] = {
        "passed": dip_positions["-1:45.0"] < dip_positions["-1:0.0"] < dip_positions["1:45.0"],
        "metrics": {"dip_positions": dip_positions},
    }

    rows_s8 = context.sweep(grid_name="supp_fig_s8", directions=[-1, 1], omega_khz=6.6, power_w=p.weak_power_w)
    rows_s8.extend(context.sweep(grid_name="supp_fig_s8", directions=[0], omega_khz=0.0, power_w=p.weak_power_w))
    writer.csv("supp_fig_s8_6p6khz.csv", rows_s8, CORRELATION_FIELDS)
    plot_s8(rows_s8, writer.figure("supp_fig_s8.png"))
    s8_plus = context.point(k=1.5, direction=1, omega_khz=6.6, power_w=p.weak_power_w)
    s8_minus = context.point(k=1.5, direction=-1, omega_khz=6.6, power_w=p.weak_power_w)
    checks["T013"] = {
        "passed": abs(s8_plus["g2"] - 0.39) < 0.03 and abs(s8_minus["g2"] - 2.53) < 0.08,
        "metrics": {"g2_positive": s8_plus["g2"], "g2_negative": s8_minus["g2"], "paper_reported": [0.39, 2.53]},
    }

    rows_s9_58 = context.sweep(grid_name="supp_fig_s9_58khz", directions=[1, -1], omega_khz=58.0, power_w=p.strong_power_w)
    rows_s9_29 = context.sweep(grid_name="supp_fig_s9_29khz", directions=[1, -1], omega_khz=29.0, power_w=p.strong_power_w)
    distributions_s9 = _distribution_rows(
        context,
        [(2.0, 1, 58.0), (2.0, -1, 58.0), (3.0, 1, 58.0), (3.0, -1, 58.0), (1.5, 1, 29.0), (1.5, -1, 29.0), (2.5, 1, 29.0), (2.5, -1, 29.0)],
        p.strong_power_w,
    )
    writer.csv("supp_fig_s9_correlations_58khz.csv", rows_s9_58, CORRELATION_FIELDS)
    writer.csv("supp_fig_s9_correlations_29khz.csv", rows_s9_29, CORRELATION_FIELDS)
    writer.csv("supp_fig_s9_distributions.csv", distributions_s9, _distribution_fields())
    plot_s9(rows_s9_58, rows_s9_29, distributions_s9, writer.figure("supp_fig_s9.png"))
    expected = [
        _classification(context.point(k=2.0, direction=1, omega_khz=58.0, power_w=p.strong_power_w)) == "1PB",
        _classification(context.point(k=2.0, direction=-1, omega_khz=58.0, power_w=p.strong_power_w)) == "PIT",
        _classification(context.point(k=3.0, direction=1, omega_khz=58.0, power_w=p.strong_power_w)) == "2PB",
        _classification(context.point(k=1.5, direction=-1, omega_khz=29.0, power_w=p.strong_power_w)) == "2PB",
    ]
    checks["T014"] = {"passed": all(expected), "metrics": {"classification_checks": expected}}


def _energy_cases(
    context: ReproductionContext,
    specs: list[EnergyCaseSpec],
    *,
    maximum_n: int,
) -> list[dict]:
    cases: list[dict] = []
    for spec in specs:
        if spec.ideal_fizeau_over_u is None:
            energies = fock_energies_over_u(
                context.scales,
                k=spec.k,
                direction=spec.direction,
                omega_khz=spec.omega_khz,
                maximum_n=maximum_n,
            )
            energy_basis = "physical_rotation_frequency"
            signed_fizeau_over_u = fizeau_shift(
                context.scales,
                spec.direction,
                spec.omega_khz,
            ) / context.scales.kerr_u_rad_s
        else:
            energies = fock_energies_from_ratios(
                k=spec.k,
                direction=spec.direction,
                fizeau_over_u=spec.ideal_fizeau_over_u,
                maximum_n=maximum_n,
            )
            energy_basis = "paper_idealized_ratio"
            signed_fizeau_over_u = spec.direction * spec.ideal_fizeau_over_u
        cases.append(
            {
                "title": spec.title,
                "direction": spec.direction,
                "omega_khz": spec.omega_khz,
                "k": spec.k,
                "energies_over_u": energies,
                "resonant_targets": list(spec.resonant_targets),
                "energy_basis": energy_basis,
                "signed_fizeau_over_u": signed_fizeau_over_u,
                "arrow_label": r"$\omega_L$",
                "color": COLORS.get(spec.direction, "#555555"),
            }
        )
    return cases


def _flatten_energy_cases(target_id: str, cases: list[dict]) -> list[dict]:
    return [
        {
            "target_id": target_id,
            "case_title": case["title"],
            "direction": case["direction"],
            "omega_khz": case["omega_khz"],
            "k": case["k"],
            "energy_basis": case["energy_basis"],
            "signed_fizeau_over_u": case["signed_fizeau_over_u"],
            "photon_number": number,
            "energy_over_u": float(energy),
            "resonant_target": number in case["resonant_targets"],
        }
        for case in cases
        for number, energy in enumerate(case["energies_over_u"])
    ]


def _energy_fields() -> list[str]:
    return [
        "target_id",
        "case_title",
        "direction",
        "omega_khz",
        "k",
        "energy_basis",
        "signed_fizeau_over_u",
        "photon_number",
        "energy_over_u",
        "resonant_target",
    ]


def _energy_resonance_metrics(cases: list[dict]) -> dict:
    return {
        case["title"]: {
            "k": case["k"],
            "direction": case["direction"],
            "omega_khz": case["omega_khz"],
            "energy_basis": case["energy_basis"],
            "signed_fizeau_over_u": case["signed_fizeau_over_u"],
            "energies_over_u": [float(value) for value in case["energies_over_u"]],
            "resonant_targets": case["resonant_targets"],
        }
        for case in cases
    }


def _distribution_rows(
    context: ReproductionContext,
    probes: list[tuple[float, int, float]],
    power_w: float,
) -> list[dict]:
    rows: list[dict] = []
    photon_numbers = [int(value) for value in context.settings["distribution_photon_numbers"]]
    for k, direction, omega in probes:
        point = context.point(k=k, direction=direction, omega_khz=omega, power_w=power_w)
        for photon_number in photon_numbers:
            rows.append(
                {
                    "probe_k": k,
                    "direction": direction,
                    "omega_khz": omega,
                    "input_power_w": power_w,
                    "photon_number": photon_number,
                    "probability": float(point["probabilities"][photon_number]),
                    "poisson_probability": float(point["poisson"][photon_number]),
                    "relative_poisson_deviation": float(point["relative_poisson_deviation"][photon_number]),
                    "mean_n": point["mean_n"],
                    "classification": _classification(point),
                }
            )
    return rows


def _distribution_fields() -> list[str]:
    return ["probe_k", "direction", "omega_khz", "input_power_w", "photon_number", "probability", "poisson_probability", "relative_poisson_deviation", "mean_n", "classification"]


def _classification(point: dict) -> str:
    if point["one_photon_blockade"]:
        return "1PB"
    if point["two_photon_blockade"]:
        return "2PB"
    if point["pit_2_to_4"]:
        return "PIT"
    return "unclassified"


def _convergence_check(context: ReproductionContext) -> dict:
    cutoffs = [int(value) for value in context.settings["convergence_cutoffs"]]
    probes = [(1.5, 1, 29.0), (1.5, -1, 29.0), (2.5, 1, 29.0), (2.5, -1, 29.0), (3.0, -1, 58.0)]
    rows: list[dict] = []
    maximum_change = 0.0
    maximum_tail = 0.0
    for k, direction, omega in probes:
        results = [
            context.point(k=k, direction=direction, omega_khz=omega, power_w=context.parameters.strong_power_w, cutoff=cutoff)
            for cutoff in cutoffs
        ]
        for cutoff, result in zip(cutoffs, results, strict=True):
            rows.append({"k": k, "direction": direction, "omega_khz": omega, "cutoff": cutoff, "mean_n": result["mean_n"], "g2": result["g2"], "g3": result["g3"], "g4": result["g4"], "tail_probability": result["tail_probability"]})
            maximum_tail = max(maximum_tail, abs(float(result["tail_probability"])))
        for key in ["mean_n", "g2", "g3", "g4"]:
            denominator = max(abs(float(results[-1][key])), 1e-14)
            maximum_change = max(maximum_change, abs(float(results[-1][key]) - float(results[-2][key])) / denominator)
    return {
        "passed": maximum_change < 1e-7 and maximum_tail < 1e-14,
        "cutoffs": cutoffs,
        "maximum_relative_change_last_two": maximum_change,
        "maximum_tail_probability": maximum_tail,
        "probes": rows,
    }


def _scalar(value: Any) -> Any:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    return _scalar(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
