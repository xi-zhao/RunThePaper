#!/usr/bin/env python3
"""Run independent Fig. 2(d) and Supplement S2/S4-S7 numerical targets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from src.geometry_adaptive import (
    build_obc_hamiltonian,
    model_eq11,
    model_eq15,
    spectral_density_from_potential,
)
from src.supplemental_campaign import (
    amoeba_potential_grid,
    biorthogonal_first_order_disorder,
    directional_winding_rows,
    geometry_adaptive_density_grid,
    geometry_sites,
    independent_fig2d_rows,
    model_s17,
    model_s27,
    normalized_state_width,
    s17_amoeba_residual_surface,
    s17_exact_potential_grid,
    s17_separable_spectrum,
    s24_bloch_spectrum,
    s24_hamiltonian,
    s24_state_profiles,
    s24_winding,
    s5_geometry_result,
)

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("T004", "T005", "T006", "T007", "T008", "T009")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    os.replace(temporary, path)


def run_t004(profile: dict[str, object], output: Path) -> list[Path]:
    rows: list[dict[str, object]] = []
    for region in profile["fig2d_regions"]:
        real_axis = np.linspace(*region["real_range"], int(region["points_per_axis"]))
        imag_axis = np.linspace(*region["imag_range"], int(region["points_per_axis"]))
        probes = np.asarray(
            [
                complex(float(real), float(imaginary))
                for imaginary in imag_axis
                for real in real_axis
            ]
        )
        region_rows = independent_fig2d_rows(
            profile["fig2d_geometries"],
            probes,
            momentum_samples=int(profile["momentum_samples"]),
            tolerance=float(profile["minimizer_tolerance"]),
        )
        for row in region_rows:
            row["region"] = str(region["label"])
            row["region_parameter_provenance"] = str(region["provenance"])
        rows.extend(region_rows)
    path = output / "data" / "T004_fig2d_independent.json"
    _json(path, rows)
    return [path]


def run_t005(profile: dict[str, object], output: Path) -> list[Path]:
    grid = profile["s2_grid"]
    real_axis = np.linspace(*grid["real_range"], int(grid["points"]))
    imag_axis = np.linspace(*grid["imag_range"], int(grid["points"]))
    exact_potential = s17_exact_potential_grid(
        real_axis,
        imag_axis,
        quadrature_points=int(profile["s2_quadrature_points"]),
    )
    exact_density = spectral_density_from_potential(
        exact_potential,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imag_axis[1] - imag_axis[0]),
    )
    amoeba = amoeba_potential_grid(
        real_axis,
        imag_axis,
        model_s17(),
        momentum_samples=int(profile["amoeba_momentum_samples"]),
        tolerance=float(profile["amoeba_tolerance"]),
    )
    amoeba_density = spectral_density_from_potential(
        amoeba,
        real_step=float(real_axis[1] - real_axis[0]),
        imaginary_step=float(imag_axis[1] - imag_axis[0]),
    )
    deformation = np.linspace(
        *profile["s2_deformation_range"], int(profile["s2_deformation_points"])
    )
    arrays = {
        "real_axis": real_axis,
        "imag_axis": imag_axis,
        "spectrum": s17_separable_spectrum(int(profile["s2_length"])),
        "exact_potential": exact_potential,
        "exact_density": exact_density,
        "amoeba_potential": amoeba,
        "amoeba_density": amoeba_density,
        "deformation_axis": deformation,
        "E1_residual": s17_amoeba_residual_surface(
            2.2 + 0.03j,
            deformation,
            momentum_samples=int(profile["s2_amoeba_surface_momentum_samples"]),
        ),
        "E2_residual": s17_amoeba_residual_surface(
            6.0 - 0.3j,
            deformation,
            momentum_samples=int(profile["s2_amoeba_surface_momentum_samples"]),
        ),
    }
    path = output / "data" / "T005_supplement_s2.npz"
    _npz(path, arrays)
    return [path]


def run_t006(profile: dict[str, object], output: Path) -> list[Path]:
    arrays: dict[str, np.ndarray] = {}
    for length in profile["s4_lengths"]:
        arrays[f"obc_L{length}"] = np.linalg.eigvals(
            s24_hamiltonian(int(length)).toarray()
        )
    momentum, pbc = s24_bloch_spectrum(int(profile["s4_momentum_points"]))
    arrays["pbc_momentum"] = momentum
    arrays["pbc_energies"] = pbc
    profiles = s24_state_profiles(int(profile["s4_profile_length"]))
    for key, value in profiles.items():
        arrays[key] = np.asarray(value)
    for name, energy in (
        ("left_wing", -2.0 + 0.0j),
        ("center", 0.0 + 0.0j),
        ("right_wing", 3.5 + 0.0j),
    ):
        arrays[f"winding_{name}"] = np.asarray(s24_winding(energy))
    path = output / "data" / "T006_supplement_s4.npz"
    _npz(path, arrays)
    return [path]


def run_t007(profile: dict[str, object], output: Path) -> list[Path]:
    paths: list[Path] = []
    density_grid = profile["s5_density_grid"]
    real_axis = np.linspace(*density_grid["real_range"], int(density_grid["points"]))
    imag_axis = np.linspace(*density_grid["imag_range"], int(density_grid["points"]))
    for geometry in profile["s5_geometries"]:
        label = str(geometry["label"])
        values, arrays = s5_geometry_result(
            geometry,
            backend=str(profile["s5_backend"]),
            target_energies=[complex(*pair) for pair in profile["s5_target_energies"]],
        )
        arrays["spectrum"] = values
        arrays["density_real_axis"] = real_axis
        arrays["density_imag_axis"] = imag_axis
        potential, density = geometry_adaptive_density_grid(
            real_axis,
            imag_axis,
            model_s27(),
            basis=str(geometry["basis"]),
            momentum_samples=int(profile["s5_density_momentum_samples"]),
            tolerance=float(profile["s5_density_tolerance"]),
        )
        arrays["theory_potential"] = potential
        arrays["theory_density"] = density
        if str(geometry["basis"]) == "square":
            widths = []
            for length in profile["s5_scaling_lengths"]:
                sites = geometry_sites({"kind": "square", "length": int(length)})
                row = []
                for target in [
                    complex(*pair) for pair in profile["s5_target_energies"]
                ]:
                    state = s5_geometry_result(
                        {"kind": "square", "length": int(length)},
                        backend=(
                            "numpy_dense"
                            if int(length)
                            <= int(profile["s5_scaling_dense_max_length"])
                            else "spectrum_skipped"
                        ),
                        target_energies=[target],
                    )[1]
                    row.append(
                        normalized_state_width(
                            np.asarray(sites),
                            state["state_0_density"],
                            basis="x",
                        )
                    )
                widths.append(row)
            arrays["scaling_lengths"] = np.asarray(
                profile["s5_scaling_lengths"], dtype=np.int64
            )
            arrays["scaling_widths"] = np.asarray(widths, dtype=np.float64)
        path = output / "data" / f"T007_supplement_s5_{label}.npz"
        _npz(path, arrays)
        paths.append(path)
    return paths


def run_t008(profile: dict[str, object], output: Path) -> list[Path]:
    payload = {
        "normal_square_y": directional_winding_rows(
            model_eq11(),
            basis="square_y",
            transverse_points=int(profile["s6_transverse_points"]),
            path_points=int(profile["s6_path_points"]),
        ),
        "critical_diagonal": directional_winding_rows(
            model_eq15(),
            basis="diagonal_1m1",
            transverse_points=int(profile["s6_transverse_points"]),
            path_points=int(profile["s6_path_points"]),
        ),
    }
    path = output / "data" / "T008_supplement_s6.json"
    _json(path, payload)
    return [path]


def run_t009(profile: dict[str, object], output: Path) -> list[Path]:
    random = np.random.default_rng(int(profile["s7_seed"]))
    payload: dict[str, object] = {
        "observable_semantics": profile["s7_observable_semantics"],
        "conditions": [],
    }
    for family in profile["s7_families"]:
        sites = geometry_sites(family["geometry"])
        hoppings = model_eq11() if family["model"] == "eq11" else model_eq15()
        matrix = build_obc_hamiltonian(sites, hoppings)
        labels = [
            (float(delta), realization)
            for delta in profile["s7_deltas"]
            for realization in range(int(profile["s7_realizations"]))
        ]
        vectors = [random.uniform(0.0, delta, len(sites)) for delta, _ in labels]
        shifts = biorthogonal_first_order_disorder(matrix, vectors)
        for row, (delta, realization) in zip(shifts, labels, strict=True):
            row["disorder_strength"] = delta
            row["realization"] = realization
        payload["conditions"].append(
            {"label": family["label"], "site_count": len(sites), "shifts": shifts}
        )
    path = output / "data" / "T009_supplement_s7.json"
    _json(path, payload)
    return [path]


RUNNERS = {
    "T004": run_t004,
    "T005": run_t005,
    "T006": run_t006,
    "T007": run_t007,
    "T008": run_t008,
    "T009": run_t009,
}


def _target_checkpoint(
    target: str,
    output: Path,
    *,
    config_sha256: str,
    implementation_sha256: str,
    paths: list[Path] | None = None,
) -> list[Path] | None:
    checkpoint = output / "checkpoints" / f"{target}.json"
    if paths is not None:
        _json(
            checkpoint,
            {
                "schema_version": 1,
                "target_id": target,
                "config_sha256": config_sha256,
                "implementation_sha256": implementation_sha256,
                "outputs": {
                    str(path.relative_to(ROOT)): _sha256(path) for path in paths
                },
            },
        )
        return paths
    if not checkpoint.exists():
        return None
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    if (
        payload.get("config_sha256") != config_sha256
        or payload.get("implementation_sha256") != implementation_sha256
    ):
        return None
    restored = [ROOT / relative for relative in payload.get("outputs", {})]
    if not restored or any(not path.is_file() for path in restored):
        return None
    if any(
        _sha256(path) != payload["outputs"][str(path.relative_to(ROOT))]
        for path in restored
    ):
        return None
    return restored


def _target_acceptance(output: Path, selected: tuple[str, ...]) -> dict[str, object]:
    """Evaluate invariants that do not depend on the source figure pixels."""

    results: dict[str, object] = {}
    if "T004" in selected:
        rows = json.loads((output / "data" / "T004_fig2d_independent.json").read_text())
        families: dict[str, list[tuple[int, float]]] = {}
        for label in sorted({str(row["size_label"]) for row in rows}):
            selected_rows = [row for row in rows if row["size_label"] == label]
            families.setdefault(str(selected_rows[0]["geometry"]), []).append(
                (
                    int(selected_rows[0]["site_count"]),
                    float(
                        np.mean([row["absolute_difference"] for row in selected_rows])
                    ),
                )
            )
        convergence = {
            family: sorted(values)[-1][1] <= sorted(values)[0][1]
            for family, values in families.items()
        }
        results["T004"] = {
            "status": "passed" if all(convergence.values()) else "failed",
            "checks": {"largest_size_not_worse_than_smallest": convergence},
            "means_by_site_count": {
                family: sorted(values) for family, values in families.items()
            },
        }
    if "T005" in selected:
        with np.load(output / "data" / "T005_supplement_s2.npz") as arrays:
            correlation = float(
                np.corrcoef(
                    arrays["exact_density"].ravel(), arrays["amoeba_density"].ravel()
                )[0, 1]
            )
            finite = bool(all(np.isfinite(arrays[key]).all() for key in arrays.files))
        results["T005"] = {
            "status": "passed" if finite and correlation > 0.8 else "failed",
            "checks": {
                "all_arrays_finite": finite,
                "exact_vs_amoeba_density_correlation": correlation,
            },
        }
    if "T006" in selected:
        with np.load(output / "data" / "T006_supplement_s4.npz") as arrays:
            normalized = {
                key: float(abs(np.sum(arrays[key]) - 1.0)) < 1e-10
                for key in arrays.files
                if key.endswith("_density")
            }
            windings = {
                key: int(arrays[key])
                for key in arrays.files
                if key.startswith("winding_")
            }
        passed = (
            all(normalized.values())
            and windings.get("winding_center") == 0
            and any(
                value != 0 for key, value in windings.items() if key != "winding_center"
            )
        )
        results["T006"] = {
            "status": "passed" if passed else "failed",
            "checks": {
                "densities_normalized": normalized,
                "representative_windings": windings,
            },
        }
    if "T007" in selected:
        residuals: dict[str, float] = {}
        normalized: dict[str, bool] = {}
        for path in sorted((output / "data").glob("T007_supplement_s5_*.npz")):
            with np.load(path) as arrays:
                for key in arrays.files:
                    name = f"{path.stem}:{key}"
                    if key.endswith("_residual"):
                        residuals[name] = float(arrays[key])
                    elif key.startswith("state_") and key.endswith("_density"):
                        normalized[name] = float(abs(np.sum(arrays[key]) - 1.0)) < 1e-10
        passed = (
            bool(residuals)
            and max(residuals.values()) < 1e-7
            and all(normalized.values())
        )
        results["T007"] = {
            "status": "passed" if passed else "failed",
            "checks": {
                "eigenstate_residuals": residuals,
                "densities_normalized": normalized,
            },
        }
    if "T008" in selected:
        payload = json.loads((output / "data" / "T008_supplement_s6.json").read_text())
        normal = {int(row["winding"]) for row in payload["normal_square_y"]}
        critical = {int(row["winding"]) for row in payload["critical_diagonal"]}
        passed = not any(value < 0 for value in normal) and {-1, 1}.issubset(critical)
        results["T008"] = {
            "status": "passed" if passed else "failed",
            "checks": {
                "normal_winding_values": sorted(normal),
                "critical_winding_values": sorted(critical),
            },
        }
    if "T009" in selected:
        payload = json.loads((output / "data" / "T009_supplement_s7.json").read_text())
        zero_rows = [
            row
            for condition in payload["conditions"]
            for row in condition["shifts"]
            if row["disorder_strength"] == 0.0
        ]
        nonzero_rows = [
            row
            for condition in payload["conditions"]
            for row in condition["shifts"]
            if row["disorder_strength"] > 0.0
        ]
        zero_exact = all(row["mean_shift_magnitude"] == 0.0 for row in zero_rows)
        response_positive = bool(nonzero_rows) and all(
            row["mean_shift_magnitude"] > 0.0 for row in nonzero_rows
        )
        results["T009"] = {
            "status": "passed" if zero_exact and response_positive else "failed",
            "checks": {
                "zero_disorder_zero_shift": zero_exact,
                "positive_disorder_nonzero_shift": response_positive,
                "ambiguous_positive_scalar_conventions_both_emitted": True,
            },
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", choices=("smoke", "paper"), default="paper")
    parser.add_argument("--targets", default=",".join(TARGETS))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    config_path = (ROOT / arguments.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    profile = config["profiles"][arguments.profile]
    selected = tuple(
        item.strip() for item in arguments.targets.split(",") if item.strip()
    )
    if not selected or any(item not in TARGETS for item in selected):
        raise ValueError(f"targets must be a non-empty subset of {TARGETS}")
    output = (ROOT / arguments.output_root).resolve()
    manifest_path = output / "manifest.json"
    config_digest = _sha256(config_path)
    implementation_digest = _sha256(ROOT / "src" / "supplemental_campaign.py")
    if arguments.resume and manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        if prior.get("config_sha256") == config_digest and prior.get(
            "selected_targets"
        ) == list(selected):
            print(json.dumps({"status": "resumed", "manifest": str(manifest_path)}))
            return 0

    outputs: list[Path] = []
    for target in selected:
        restored = (
            _target_checkpoint(
                target,
                output,
                config_sha256=config_digest,
                implementation_sha256=implementation_digest,
            )
            if arguments.resume
            else None
        )
        if restored is not None:
            outputs.extend(restored)
            continue
        generated = RUNNERS[target](profile, output)
        outputs.extend(generated)
        _target_checkpoint(
            target,
            output,
            config_sha256=config_digest,
            implementation_sha256=implementation_digest,
            paths=generated,
        )
    target_results = _target_acceptance(output, selected)
    checks = {
        "status": (
            "passed"
            if all(row["status"] == "passed" for row in target_results.values())
            else "failed"
        ),
        "profile": arguments.profile,
        "paper_parameters_executed": arguments.profile == "paper",
        "selected_targets": list(selected),
        "author_code_or_arrays_used": False,
        "source_pixels_used_as_numerical_input": False,
        "paper_review_notes": {
            "T009": "Eq. S29 does not specify whether the plotted positive scalar is |mean Delta E| or mean |Delta E|; both are emitted and the discrepancy remains inconclusive.",
            "T007": "The eigenstate-selection energies in S5(a,b) are not printed and remain explicit reconstruction inputs.",
        },
        "target_results": target_results,
    }
    check_path = output / "checks" / "science.json"
    _json(check_path, checks)
    outputs.append(check_path)
    if checks["status"] != "passed":
        raise RuntimeError("one or more scientific acceptance checks failed")
    manifest = {
        "schema_version": 1,
        "profile": arguments.profile,
        "config_sha256": config_digest,
        "implementation_sha256": implementation_digest,
        "selected_targets": list(selected),
        "numerical_input_policy": {
            "author_code": "forbidden",
            "author_arrays": "forbidden",
            "paper_pixels": "forbidden",
            "digitized_curves": "forbidden",
        },
        "outputs": {
            str(path.relative_to(ROOT)): {
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in outputs
        },
    }
    _json(manifest_path, manifest)
    print(json.dumps({"status": "passed", "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    normalized_state_width,
