"""All-target deterministic campaign for the six numerical figures."""

from __future__ import annotations

import hashlib
import json
import math
import time
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import maximum_filter1d

from .model import (
    band_edges,
    harper_matrix,
    high_precision_band_edges,
    reordered_wavefunction,
    transfer_trace,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rational_fluxes(max_denominator: int, *, upper: float = 1.0) -> list[Fraction]:
    values = {Fraction(0, 1)}
    for q in range(1, max_denominator + 1):
        for p in range(1, q + 1):
            value = Fraction(p, q)
            if float(value) <= upper:
                values.add(value)
    return sorted(values)


def spectrum_segments(
    max_denominator: int, *, upper: float = 1.0
) -> dict[str, np.ndarray]:
    alpha: list[float] = []
    low: list[float] = []
    high: list[float] = []
    numerator: list[int] = []
    denominator: list[int] = []
    band_index: list[int] = []
    for flux in rational_fluxes(max_denominator, upper=upper):
        for index, (edge_low, edge_high) in enumerate(
            band_edges(flux.numerator, flux.denominator)
        ):
            alpha.append(float(flux))
            low.append(edge_low)
            high.append(edge_high)
            numerator.append(flux.numerator)
            denominator.append(flux.denominator)
            band_index.append(index)
    return {
        "alpha": np.asarray(alpha),
        "low": np.asarray(low),
        "high": np.asarray(high),
        "numerator": np.asarray(numerator),
        "denominator": np.asarray(denominator),
        "band_index": np.asarray(band_index),
    }


def high_precision_width_audit(
    spectrum: dict[str, np.ndarray], *, threshold: float = 1e-12
) -> dict[str, Any]:
    """Recompute ill-conditioned band widths without float64 cancellation."""

    widths = spectrum["high"] - spectrum["low"]
    suspicious = np.flatnonzero(widths <= threshold)
    fractions = sorted(
        {
            (int(spectrum["numerator"][row]), int(spectrum["denominator"][row]))
            for row in suspicious
        }
    )
    precise = {
        key: high_precision_band_edges(*key)
        for key in fractions
    }
    rows = []
    for row in suspicious:
        p = int(spectrum["numerator"][row])
        q = int(spectrum["denominator"][row])
        band_index = int(spectrum["band_index"][row])
        low, high = precise[(p, q)][band_index]
        width = Decimal(high) - Decimal(low)
        rows.append(
            {
                "p": p,
                "q": q,
                "band_index": band_index,
                "float64_width": float(widths[row]),
                "low_decimal": low,
                "high_decimal": high,
                "width_decimal": str(width),
                "positive_width": width > 0,
            }
        )
    return {
        "schema_version": 1,
        "selection_threshold": threshold,
        "audited_fraction_count": len(fractions),
        "audited_band_count": len(rows),
        "all_positive": all(row["positive_width"] for row in rows),
        "rows": rows,
    }


def skeleton_segments(pure_max_n: int) -> dict[str, np.ndarray]:
    rows: list[tuple[float, float, float, int, int, int]] = []
    for n in range(2, pure_max_n + 1):
        for p in (1, n - 1):
            for index, (low, high) in enumerate(band_edges(p, n)):
                rows.append((p / n, low, high, p, n, index))
    for n in range(2, (pure_max_n - 1) // 2 + 1):
        q = 2 * n + 1
        for p in (n, n + 1):
            bands = band_edges(p, q)
            index = q // 2
            low, high = bands[index]
            rows.append((p / q, low, high, p, q, index))
    rows.sort()

    connectors: list[tuple[float, float, float, float, str, int, int]] = []

    def connect_sequence(
        points: list[tuple[float, tuple[tuple[float, float], ...], int]],
        edge_selectors: tuple[tuple[int, int, str], ...],
    ) -> None:
        for (alpha0, bands0, n0), (alpha1, bands1, n1) in zip(
            points, points[1:]
        ):
            for band_index, edge_index, family in edge_selectors:
                index0 = band_index if band_index >= 0 else len(bands0) + band_index
                index1 = band_index if band_index >= 0 else len(bands1) + band_index
                connectors.append(
                    (
                        bands0[index0][edge_index],
                        alpha0,
                        bands1[index1][edge_index],
                        alpha1,
                        family,
                        index0,
                        index1,
                    )
                )

    lower_pure = sorted(
        [(1 / n, band_edges(1, n), n) for n in range(2, pure_max_n + 1)]
    )
    upper_pure = sorted(
        [
            ((n - 1) / n, band_edges(n - 1, n), n)
            for n in range(2, pure_max_n + 1)
        ]
    )
    outer_edges = (
        (0, 0, "L_outer_low"),
        (0, 1, "L_outer_high"),
        (-1, 0, "R_outer_low"),
        (-1, 1, "R_outer_high"),
    )
    connect_sequence(lower_pure, outer_edges)
    connect_sequence(upper_pure, outer_edges)

    # The paper's C-chain starts at the *outer* edges of the
    # next-to-outermost pure bands, not at an inferred central band.
    c_pure_edges = ((1, 0, "C_pure_left"), (-2, 1, "C_pure_right"))
    connect_sequence([point for point in lower_pure if point[2] > 2], c_pure_edges)
    connect_sequence([point for point in upper_pure if point[2] > 2], c_pure_edges)

    lower_special = []
    upper_special = []
    for n in range(2, (pure_max_n - 1) // 2 + 1):
        q = 2 * n + 1
        for p, destination in ((n, lower_special), (n + 1, upper_special)):
            bands = band_edges(p, q)
            destination.append((p / q, bands, q))
    special_edges = ((0, 0, "C_special_low"), (0, 1, "C_special_high"))
    # Each tuple contains only the selected centre band so index zero is exact.
    lower_special = [
        (alpha, (bands[len(bands) // 2],), q)
        for alpha, bands, q in sorted(lower_special)
    ]
    upper_special = [
        (alpha, (bands[len(bands) // 2],), q)
        for alpha, bands, q in sorted(upper_special)
    ]
    connect_sequence(lower_special, special_edges)
    connect_sequence(upper_special, special_edges)

    result = {
        "alpha": np.asarray([r[0] for r in rows]),
        "low": np.asarray([r[1] for r in rows]),
        "high": np.asarray([r[2] for r in rows]),
        "numerator": np.asarray([r[3] for r in rows]),
        "denominator": np.asarray([r[4] for r in rows]),
        "band_index": np.asarray([r[5] for r in rows]),
    }
    if connectors:
        result.update(
            {
                "connector_x0": np.asarray([row[0] for row in connectors]),
                "connector_y0": np.asarray([row[1] for row in connectors]),
                "connector_x1": np.asarray([row[2] for row in connectors]),
                "connector_y1": np.asarray([row[3] for row in connectors]),
                "connector_family": np.asarray([row[4] for row in connectors]),
                "connector_band_index0": np.asarray([row[5] for row in connectors]),
                "connector_band_index1": np.asarray([row[6] for row in connectors]),
            }
        )
    return result


def _linear_boundary(
    alpha: float,
    alpha_low: float,
    alpha_high: float,
    value_low: float,
    value_high: float,
) -> float:
    weight = (alpha - alpha_low) / (alpha_high - alpha_low)
    return value_low + weight * (value_high - value_low)


def rectangularized_subcell(
    kind: str, max_denominator: int, *, pure_only: bool | None = None
) -> dict[str, np.ndarray]:
    if pure_only is None:
        pure_only = kind == "C2"
    if kind == "L2":
        alpha_low, alpha_high = 1 / 5, 1 / 4
        low_band = band_edges(1, 5)[0]
        high_band = band_edges(1, 4)[0]

        def local_coordinate(alpha: Fraction) -> Fraction:
            return 1 / alpha - 4

    elif kind == "C2":
        alpha_low, alpha_high = 2 / 5, 3 / 7
        low_band = band_edges(2, 5)[2]
        high_band = band_edges(3, 7)[3]

        def local_coordinate(alpha: Fraction) -> Fraction:
            return alpha / (1 - 2 * alpha) - 2

    else:
        raise ValueError(f"unknown subcell {kind!r}")

    local_alpha: list[float] = []
    normalized_low: list[float] = []
    normalized_high: list[float] = []
    source_alpha: list[float] = []
    source_numerator: list[int] = []
    source_denominator: list[int] = []
    local_numerator: list[int] = []
    local_denominator: list[int] = []
    for flux in rational_fluxes(max_denominator, upper=alpha_high):
        alpha = float(flux)
        if alpha < alpha_low - 1e-14:
            continue
        local = local_coordinate(flux)
        if not 0 <= local <= 1:
            continue
        is_pure = local.numerator == 1 or local.numerator == local.denominator - 1
        if pure_only and not is_pure:
            continue
        left = _linear_boundary(alpha, alpha_low, alpha_high, low_band[0], high_band[0])
        right = _linear_boundary(
            alpha, alpha_low, alpha_high, low_band[1], high_band[1]
        )
        width = right - left
        for edge_low, edge_high in band_edges(flux.numerator, flux.denominator):
            center = 0.5 * (edge_low + edge_high)
            if left - 1e-10 <= center <= right + 1e-10:
                local_alpha.append(float(local))
                normalized_low.append(8.0 * (edge_low - left) / width - 4.0)
                normalized_high.append(8.0 * (edge_high - left) / width - 4.0)
                source_alpha.append(alpha)
                source_numerator.append(flux.numerator)
                source_denominator.append(flux.denominator)
                local_numerator.append(local.numerator)
                local_denominator.append(local.denominator)
    order = np.argsort(local_alpha)
    return {
        "local_alpha": np.asarray(local_alpha)[order],
        "low": np.asarray(normalized_low)[order],
        "high": np.asarray(normalized_high)[order],
        "source_alpha": np.asarray(source_alpha)[order],
        "source_numerator": np.asarray(source_numerator)[order],
        "source_denominator": np.asarray(source_denominator)[order],
        "local_numerator": np.asarray(local_numerator)[order],
        "local_denominator": np.asarray(local_denominator)[order],
        "pure_only": np.asarray(bool(pure_only)),
        "source_interval": np.asarray([alpha_low, alpha_high]),
    }


def _interval_raster(data: dict[str, np.ndarray], pixels: int) -> np.ndarray:
    energy = np.linspace(-4.0, 4.0, pixels)
    raster = np.zeros((pixels, pixels), dtype=bool)
    for alpha, low, high in zip(
        data["local_alpha"], data["low"], data["high"], strict=True
    ):
        row = int(np.clip(round(float(alpha) * (pixels - 1)), 0, pixels - 1))
        start = int(np.searchsorted(energy, max(-4.0, float(low)), side="left"))
        stop = int(np.searchsorted(energy, min(4.0, float(high)), side="right"))
        raster[row, start:stop] = True
    return maximum_filter1d(raster, size=3, axis=0)


def rectangularized_convergence(
    kind: str, cutoffs: list[int], *, pixels: int = 256
) -> dict[str, Any]:
    """Measure stability at fixed observable resolution across q cutoffs."""

    if sorted(set(cutoffs)) != cutoffs or len(cutoffs) < 2:
        raise ValueError("cutoffs must be a strictly increasing sequence")
    records = []
    previous: np.ndarray | None = None
    transitions = []
    for cutoff in cutoffs:
        data = rectangularized_subcell(kind, cutoff)
        raster = _interval_raster(data, pixels)
        records.append(
            {
                "denominator_max": cutoff,
                "interval_count": int(len(data["local_alpha"])),
                "occupied_pixels": int(np.count_nonzero(raster)),
            }
        )
        if previous is not None:
            union = int(np.count_nonzero(previous | raster))
            intersection = int(np.count_nonzero(previous & raster))
            transitions.append(
                {
                    "to_denominator_max": cutoff,
                    "pixel_agreement": float(np.mean(previous == raster)),
                    "jaccard": float(intersection / union) if union else 1.0,
                }
            )
        previous = raster
    return {
        "schema_version": 1,
        "kind": kind,
        "pixels": pixels,
        "records": records,
        "transitions": transitions,
        "final_pixel_agreement": transitions[-1]["pixel_agreement"],
    }


def blurred_quadrant(
    max_denominator: int,
    *,
    field_window: float,
    alpha_pixels: int,
    energy_pixels: int,
) -> dict[str, np.ndarray]:
    alpha_grid = np.linspace(0.0, 0.5, alpha_pixels)
    energy_grid = np.linspace(-4.0, 0.0, energy_pixels)
    occupied = np.zeros((alpha_pixels, energy_pixels), dtype=np.uint8)
    segments = spectrum_segments(max_denominator, upper=0.5)
    for alpha, low, high in zip(
        segments["alpha"], segments["low"], segments["high"], strict=True
    ):
        row = int(np.clip(round(alpha / 0.5 * (alpha_pixels - 1)), 0, alpha_pixels - 1))
        clipped_low = max(float(low), -4.0)
        clipped_high = min(float(high), 0.0)
        if clipped_low > clipped_high:
            continue
        start = int(np.searchsorted(energy_grid, clipped_low, side="left"))
        stop = int(np.searchsorted(energy_grid, clipped_high, side="right"))
        occupied[row, start:stop] = 1
    half_width = field_window / 2.0
    window_rows = max(1, int(round(half_width / 0.5 * (alpha_pixels - 1))))
    blurred = maximum_filter1d(occupied, size=2 * window_rows + 1, axis=0)
    return {
        "alpha": alpha_grid,
        "energy": energy_grid,
        "occupied": occupied,
        "blurred": blurred.astype(np.uint8),
        "field_window": np.asarray(field_window),
        "field_half_width": np.asarray(half_width),
        "half_window_rows": np.asarray(window_rows),
    }


def _save_npz(path: Path, payload: dict[str, np.ndarray]) -> None:
    np.savez_compressed(path, **payload)


def _component_count(row: np.ndarray) -> int:
    padded = np.pad(row.astype(bool), (1, 0))
    return int(np.count_nonzero(np.diff(padded.astype(np.int8)) == 1))


def run_campaign(config_path: Path, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir = output_dir / "data"
    checks_dir = output_dir / "checks"
    data_dir.mkdir(exist_ok=True)
    checks_dir.mkdir(exist_ok=True)

    fig1 = spectrum_segments(int(parameters["fig1"]["denominator_max"]))
    precision_audit = high_precision_width_audit(fig1)
    fig2 = skeleton_segments(int(parameters["fig2"]["pure_max_n"]))
    fig3 = rectangularized_subcell(
        "L2", int(parameters["rectangularized"]["denominator_max"])
    )
    fig4 = rectangularized_subcell(
        "C2", int(parameters["rectangularized"]["denominator_max"]), pure_only=True
    )
    convergence = rectangularized_convergence(
        "L2",
        [int(value) for value in parameters["rectangularized"]["convergence_denominators"]],
        pixels=int(parameters["rectangularized"]["convergence_pixels"]),
    )
    fig5 = blurred_quadrant(
        int(parameters["fig5"]["denominator_max"]),
        field_window=float(parameters["fig5"]["field_window"]),
        alpha_pixels=int(parameters["fig5"]["alpha_pixels"]),
        energy_pixels=int(parameters["fig5"]["energy_pixels"]),
    )
    waves = []
    for item in parameters["fig6"]["fractions"]:
        wave = reordered_wavefunction(int(item["p"]), int(item["q"]))
        wave["printed_energy"] = float(item["printed_energy"])
        waves.append(wave)

    paths = {
        "fig1": data_dir / "fig1_spectrum.npz",
        "fig2": data_dir / "fig2_skeleton.npz",
        "fig3": data_dir / "fig3_l2_rectangularized.npz",
        "fig4": data_dir / "fig4_c2_rectangularized.npz",
        "fig5": data_dir / "fig5_blurred_quadrant.npz",
        "fig6": data_dir / "fig6_wavefunctions.json",
        "precision": checks_dir / "fig1_high_precision_widths.json",
        "convergence": checks_dir / "rectangularized_convergence.json",
    }
    for key, payload in (
        ("fig1", fig1),
        ("fig2", fig2),
        ("fig3", fig3),
        ("fig4", fig4),
        ("fig5", fig5),
    ):
        _save_npz(paths[key], payload)
    serializable_waves = []
    for wave in waves:
        serializable_waves.append(
            {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in wave.items()
            }
        )
    paths["fig6"].write_text(json.dumps({"waves": serializable_waves}, indent=2) + "\n")
    paths["precision"].write_text(json.dumps(precision_audit, indent=2) + "\n")
    paths["convergence"].write_text(json.dumps(convergence, indent=2) + "\n")

    symmetry_residual = 0.0
    for p, q in ((1, 5), (2, 11), (3, 13), (7, 31)):
        left = np.asarray(band_edges(p, q))
        right = np.asarray(band_edges(q - p, q))
        symmetry_residual = max(symmetry_residual, float(np.max(np.abs(left - right))))
    chiral_residual = 0.0
    for p, q in ((1, 5), (2, 11), (3, 13)):
        edges = np.asarray(band_edges(p, q))
        chiral_residual = max(
            chiral_residual, float(np.max(np.abs(edges + edges[::-1, ::-1])))
        )
    edge_trace_residual = 0.0
    for p, q in ((1, 5), (2, 11), (3, 13)):
        for low, high in band_edges(p, q):
            for energy in (low, high):
                edge_trace_residual = max(
                    edge_trace_residual, abs(abs(transfer_trace(energy, p, q)) - 4.0)
                )
    energy_errors = [
        abs(float(wave["energy"]) - float(wave["printed_energy"])) for wave in waves
    ]
    eigen_residuals = []
    for wave in waves:
        p, q = int(wave["p"]), int(wave["q"])
        order = np.asarray(wave["order"], dtype=int)
        amplitudes = np.asarray(wave["amplitude"], dtype=float)
        original = np.empty_like(amplitudes)
        original[order] = amplitudes
        residual = harper_matrix(p, q) @ original - float(wave["energy"]) * original
        eigen_residuals.append(float(np.max(np.abs(residual))))
    component_counts = [_component_count(row) for row in fig5["blurred"]]
    checks = [
        (
            "CHK_BAND_COUNT",
            all(len(band_edges(p, q)) == q for p, q in ((1, 5), (2, 11), (17, 93)))
            and precision_audit["all_positive"],
            0.0,
            0.0,
        ),
        (
            "CHK_POSITIVE_HIGH_PRECISION_WIDTHS",
            bool(precision_audit["all_positive"]),
            float(sum(not row["positive_width"] for row in precision_audit["rows"])),
            0.0,
        ),
        ("CHK_ALPHA_SYMMETRY", symmetry_residual <= 1e-10, symmetry_residual, 1e-10),
        ("CHK_ENERGY_SYMMETRY", chiral_residual <= 1e-10, chiral_residual, 1e-10),
        (
            "CHK_ENERGY_BOUND",
            float(max(fig1["high"])) <= 4.0 + 1e-10
            and float(min(fig1["low"])) >= -4.0 - 1e-10,
            max(
                abs(float(max(fig1["high"])) - 4.0), abs(float(min(fig1["low"])) + 4.0)
            ),
            1e-10,
        ),
        (
            "CHK_TRACE_BAND_EDGES",
            edge_trace_residual <= 1e-7,
            edge_trace_residual,
            1e-7,
        ),
        (
            "CHK_L2_RECTANGULARIZATION",
            len(fig3["local_alpha"]) > 20
            and float(np.min(fig3["local_alpha"])) >= -1e-10
            and float(np.max(fig3["local_alpha"])) <= 1.0 + 1e-10,
            float(len(fig3["local_alpha"])),
            20.0,
        ),
        (
            "CHK_L2_CONVERGENCE",
            float(convergence["final_pixel_agreement"]) >= 0.97,
            float(convergence["final_pixel_agreement"]),
            0.97,
        ),
        (
            "CHK_C2_RECTANGULARIZATION",
            len(fig4["local_alpha"]) > 10
            and float(np.min(fig4["local_alpha"])) >= -1e-10
            and float(np.max(fig4["local_alpha"])) <= 1.0 + 1e-10
            and all(
                int(p) == 1 or int(p) == int(q) - 1
                for p, q in zip(
                    fig4["local_numerator"], fig4["local_denominator"], strict=True
                )
            ),
            float(len(fig4["local_alpha"])),
            10.0,
        ),
        (
            "CHK_BLURRED_BAND_BOUND",
            max(component_counts)
            <= math.floor(1.0 / float(parameters["fig5"]["field_window"])) + 1,
            float(max(component_counts)),
            float(math.floor(1.0 / float(parameters["fig5"]["field_window"])) + 1),
        ),
        (
            "CHK_PRINTED_EIGENVALUES",
            max(energy_errors) <= 1e-4,
            max(energy_errors),
            1e-4,
        ),
        (
            "CHK_WAVEFUNCTION_RESIDUAL",
            max(eigen_residuals) <= 1e-10,
            max(eigen_residuals),
            1e-10,
        ),
        (
            "CHK_WAVEFUNCTION_NORMALIZATION",
            all(
                abs(float(np.max(np.abs(wave["amplitude"]))) - 1.0) <= 1e-12
                for wave in waves
            ),
            0.0,
            1e-12,
        ),
    ]
    target_map = {
        "CHK_BAND_COUNT": ["T001", "T002", "T003", "T004", "T007"],
        "CHK_POSITIVE_HIGH_PRECISION_WIDTHS": ["T001", "T007"],
        "CHK_ALPHA_SYMMETRY": ["T001", "T002", "T007"],
        "CHK_ENERGY_SYMMETRY": ["T001", "T002", "T007"],
        "CHK_ENERGY_BOUND": ["T001", "T005", "T007"],
        "CHK_TRACE_BAND_EDGES": ["T001", "T002", "T003", "T004", "T007"],
        "CHK_L2_RECTANGULARIZATION": ["T003"],
        "CHK_L2_CONVERGENCE": ["T003", "T007"],
        "CHK_C2_RECTANGULARIZATION": ["T004"],
        "CHK_BLURRED_BAND_BOUND": ["T005", "T007"],
        "CHK_PRINTED_EIGENVALUES": ["T006", "T007"],
        "CHK_WAVEFUNCTION_RESIDUAL": ["T006", "T007"],
        "CHK_WAVEFUNCTION_NORMALIZATION": ["T006", "T007"],
    }
    check_rows = [
        {
            "check_id": check_id,
            "passed": bool(passed),
            "value": value,
            "threshold": threshold,
            "target_ids": target_map[check_id],
        }
        for check_id, passed, value, threshold in checks
    ]
    science = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": "passed" if all(row["passed"] for row in check_rows) else "failed",
        "artifact_stage": "paper_exact",
        "checks": check_rows,
    }
    science_path = checks_dir / "science_checks.json"
    science_path.write_text(json.dumps(science, indent=2) + "\n")
    outputs = [*paths.values(), science_path]
    manifest = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "scientific_data_frozen": True,
        "files": [
            {
                "path": str(path.relative_to(output_dir)),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in outputs
        ],
    }
    manifest_path = checks_dir / "generated_data_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    summary = {
        "schema_version": 1,
        "paper_id": config["paper_id"],
        "status": science["status"],
        "duration_seconds": time.perf_counter() - started,
        "targets": ["T001", "T002", "T003", "T004", "T005", "T006", "T007"],
        "fig1_rationals": len(set(zip(fig1["numerator"], fig1["denominator"]))),
        "fig1_bands": len(fig1["alpha"]),
        "fig5_occupancy_fraction": float(np.mean(fig5["blurred"])),
    }
    (checks_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
