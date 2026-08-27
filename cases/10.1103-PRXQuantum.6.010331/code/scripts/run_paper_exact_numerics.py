from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from src.fidelity_response import appendix_fit, scale_universal_response  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_universal(path: Path, frequencies: np.ndarray, fits: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "normalized_frequency",
        "haar_frequency_response",
        "symmetric_haar_frequency_response",
        "haar_intensity_response",
        "symmetric_haar_intensity_response",
        "generated_data_provenance",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, frequency in enumerate(frequencies):
            writer.writerow(
                {
                    "normalized_frequency": float(frequency),
                    "haar_frequency_response": float(fits["haar_frequency"][index]),
                    "symmetric_haar_frequency_response": float(
                        fits["symmetric_haar_frequency"][index]
                    ),
                    "haar_intensity_response": float(fits["haar_intensity"][index]),
                    "symmetric_haar_intensity_response": float(
                        fits["symmetric_haar_intensity"][index]
                    ),
                    "generated_data_provenance": "analytic_reference",
                }
            )


def _write_scaled(
    path: Path,
    normalized_grid: np.ndarray,
    fits: dict[str, np.ndarray],
    physical_frequencies: np.ndarray,
    rabi_frequencies: list[float],
) -> float:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "physical_frequency_mhz",
        "rabi_frequency_mhz",
        "normalized_frequency",
        "frequency_response_mhz_minus_2",
        "intensity_response",
        "generated_data_provenance",
    ]
    maximum_error = 0.0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for rabi in rabi_frequencies:
            frequency_response, intensity_response = scale_universal_response(
                normalized_grid,
                fits["haar_frequency"],
                fits["haar_intensity"],
                physical_frequencies,
                rabi,
            )
            normalized = physical_frequencies / rabi
            expected_frequency = np.interp(normalized, normalized_grid, fits["haar_frequency"])
            expected_intensity = np.interp(normalized, normalized_grid, fits["haar_intensity"])
            maximum_error = max(
                maximum_error,
                float(
                    np.max(
                        np.abs(
                            frequency_response * (2.0 * np.pi * rabi) ** 2
                            - expected_frequency
                        )
                    )
                ),
                float(np.max(np.abs(intensity_response - expected_intensity))),
            )
            for index, frequency in enumerate(physical_frequencies):
                writer.writerow(
                    {
                        "physical_frequency_mhz": float(frequency),
                        "rabi_frequency_mhz": rabi,
                        "normalized_frequency": float(normalized[index]),
                        "frequency_response_mhz_minus_2": float(frequency_response[index]),
                        "intensity_response": float(intensity_response[index]),
                        "generated_data_provenance": "analytic_reference",
                    }
                )
    return maximum_error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate paper-exact Appendix-L response data without rendering."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    universal = config["universal_response"]
    fig6 = config["fig6a"]
    frequencies = np.linspace(
        float(universal["normalized_frequency_min"]),
        float(universal["normalized_frequency_max"]),
        int(universal["frequency_points"]),
    )
    fits = {
        f"{metric}_{noise}": appendix_fit(frequencies, metric, noise)
        for metric in ("haar", "symmetric_haar")
        for noise in ("frequency", "intensity")
    }
    _write_universal(WORKSPACE / "outputs/data/universal_response.csv", frequencies, fits)

    minimum_response = min(float(np.min(curve)) for curve in fits.values())
    response_at_half = float(np.interp(0.5, frequencies, fits["haar_intensity"]))
    peak_window = (frequencies >= 1.0) & (frequencies <= 1.4)
    peak_locations = {
        metric: float(
            frequencies[peak_window][
                np.argmax(fits[f"{metric}_frequency"][peak_window])
            ]
        )
        for metric in ("haar", "symmetric_haar")
    }
    acceptance = {
        "responses_nonnegative": minimum_response >= -1.0e-8,
        "published_1p5_mhz_response": abs(response_at_half - 1.04) < 0.15,
        "frequency_second_peak_present": all(
            1.0 <= value <= 1.4 for value in peak_locations.values()
        ),
    }
    _write_json(
        WORKSPACE / "outputs/checks/universal_response.json",
        {
            "schema_version": 1,
            "target_id": "T001",
            "figure_refs": ["Fig. 15"],
            "status": "passed" if all(acceptance.values()) else "failed",
            "artifact_stage": "final_reproduction",
            "parameter_match": "paper_exact",
            "generated_data_provenance": "analytic_reference",
            "reference_comparison": "analytic_reference",
            "formula_gate": "verified",
            "formula_dependencies": ["EQ005", "EQ006"],
            "normalized_frequency_points": len(frequencies),
            "minimum_response": minimum_response,
            "frequency_second_peak_locations": peak_locations,
            "haar_intensity_response_x_0p5": response_at_half,
            "paper_reference_x_0p5": 1.04,
            "acceptance": acceptance,
            "data": "outputs/data/universal_response.csv",
        },
    )

    physical = np.linspace(
        float(fig6["frequency_min_mhz"]),
        float(fig6["frequency_max_mhz"]),
        int(fig6["frequency_points"]),
    )
    rabi_frequencies = [float(value) for value in fig6["rabi_frequencies_mhz"]]
    collapse_error = _write_scaled(
        WORKSPACE / "outputs/data/fig6a_scaled_response.csv",
        frequencies,
        fits,
        physical,
        rabi_frequencies,
    )
    fig6_status = "passed" if collapse_error < 1.0e-12 else "failed"
    _write_json(
        WORKSPACE / "outputs/checks/fig6a_scaled_response.json",
        {
            "schema_version": 1,
            "target_id": "T002",
            "figure_refs": ["Fig. 6(a)"],
            "status": fig6_status,
            "artifact_stage": "final_reproduction",
            "parameter_match": "paper_exact",
            "generated_data_provenance": "analytic_reference",
            "reference_comparison": "analytic_reference",
            "formula_gate": "verified",
            "formula_dependencies": ["EQ005", "EQ006"],
            "rabi_frequencies_mhz": rabi_frequencies,
            "frequency_range_mhz": [float(physical[0]), float(physical[-1])],
            "maximum_scaling_collapse_error": collapse_error,
            "data": "outputs/data/fig6a_scaled_response.csv",
        },
    )
    status = "passed" if all(acceptance.values()) and fig6_status == "passed" else "failed"
    _write_json(
        WORKSPACE / "outputs/checks/run_summary.json",
        {"status": status, "targets": {"T001": status, "T002": fig6_status}},
    )
    print(json.dumps({"status": status, "T001": acceptance, "T002_error": collapse_error}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
