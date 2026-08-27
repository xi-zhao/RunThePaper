#!/usr/bin/env python3
"""Generate the formula-derived far-detuned total-resistivity target."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from bose_fermi_transport.far_detuned import (  # noqa: E402
    asymptotic_far_detuned_resistivity,
    check_far_detuned_resistivity,
)


def run(config_path: Path, workspace: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parameters = config["parameters"]
    temperatures = np.linspace(
        float(parameters["temperature_min_k"]),
        float(parameters["temperature_max_k"]),
        int(parameters["temperature_points"]),
    )
    phonon = parameters["phonon"]
    result = asymptotic_far_detuned_resistivity(
        temperatures,
        background_over_rho0=float(parameters["background_over_rho0"]),
        bloch_gruneisen_k=float(phonon["bloch_gruneisen_k"]),
        high_temperature_slope_per_k=float(
            phonon["high_temperature_slope_per_k"]
        ),
        crossover_power=float(phonon["crossover_power"]),
    )
    checks = check_far_detuned_resistivity(result)
    checks.update(
        {
            "schema_version": 1,
            "paper_id": "2409.18176",
            "target_id": "T011",
            "parameter_match": "proxy_model",
            "scientific_interpretation": (
                "The far-detuned many-body term vanishes, leaving the Drude "
                "background plus the declared acoustic-phonon proxy."
            ),
            "remaining_gap": (
                "The paper delegates the absolute acoustic-phonon calibration "
                "to external references, so the curve is not paper-exact."
            ),
            "source_boundary": {
                "author_code_used": False,
                "author_numeric_arrays_used": False,
                "source_pixels_used_as_numeric_input": False,
            },
        }
    )

    data_path = workspace / "outputs/data/T011_far_detuned_total_resistivity.csv"
    figure_path = workspace / "outputs/figures/T011_main_fig3_inset_far_detuned.png"
    check_path = workspace / "outputs/checks/T011_far_detuned_total_resistivity.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.parent.mkdir(parents=True, exist_ok=True)

    with data_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "temperature_k",
                "detuning_regime",
                "background_over_rho0",
                "many_body_over_rho0",
                "phonon_over_rho0",
                "total_over_rho0",
            ],
        )
        writer.writeheader()
        for index, temperature in enumerate(result.temperature_k):
            writer.writerow(
                {
                    "temperature_k": float(temperature),
                    "detuning_regime": "Delta/Delta_star -> infinity",
                    "background_over_rho0": float(
                        result.background_over_rho0[index]
                    ),
                    "many_body_over_rho0": float(
                        result.many_body_over_rho0[index]
                    ),
                    "phonon_over_rho0": float(result.phonon_over_rho0[index]),
                    "total_over_rho0": float(result.total_over_rho0[index]),
                }
            )

    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.plot(
        result.temperature_k,
        result.total_over_rho0,
        color="#707782",
        linestyle="-.",
        linewidth=1.7,
        label=r"$\Delta/\Delta_\star\to\infty$",
    )
    ax.set(
        xlabel="temperature (K)",
        ylabel=r"$(\rho_0^h+\rho_{ph}^h)/\rho_0^h$",
        title="Far-detuned total resistivity",
    )
    ax.tick_params(direction="in", top=True, right=True)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    check_path.write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not checks["passed"]:
        raise RuntimeError("T011 scientific checks failed")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/t011_far_detuned.json")
    args = parser.parse_args()
    config_path = (WORKSPACE / args.config).resolve()
    if WORKSPACE not in config_path.parents:
        raise ValueError("config must remain inside workspace")
    checks = run(config_path, WORKSPACE)
    print(json.dumps({"passed": checks["passed"], "target_id": "T011"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
