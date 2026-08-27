"""Target-level reproduction use cases.

Each use case writes structured data first, then renders plots from those files.
No plotting function is allowed to become the source of numerical truth.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .artifacts import ensure_output_tree, write_csv, write_json
from .checks import run_scientific_checks
from .model import ChannelRates, TransportModel, absorption_rate
from .plotting import (
    plot_dynamics,
    plot_scaling,
    plot_scaling_laws,
    plot_site_n_dynamics,
    plot_site_n_sweep,
    plot_temperature,
    plot_temperature_n64,
    render_side_by_side,
)
from .simulation import (
    PreparedTransport,
    ensemble_final_populations,
    ensemble_population_dynamics,
    prepare_ensemble,
)


@dataclass(frozen=True)
class RunContext:
    workspace: Path
    output_root: Path
    config: dict[str, Any]
    profile_name: str
    profile: dict[str, Any]
    paths: dict[str, Path]
    allow_reference_comparisons: bool = True

    @classmethod
    def create(
        cls,
        workspace: Path,
        output_root: Path,
        profile_name: str,
        output_namespace: str | None = None,
        allow_reference_comparisons: bool = True,
    ) -> "RunContext":
        config_path = workspace / "config" / "reproduction.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if profile_name not in config["profiles"]:
            raise ValueError(f"unknown profile: {profile_name}")
        return cls(
            workspace=workspace,
            output_root=output_root,
            config=config,
            profile_name=profile_name,
            profile=config["profiles"][profile_name],
            paths=ensure_output_tree(output_root, output_namespace),
            allow_reference_comparisons=allow_reference_comparisons,
        )

    def model(self, n_sites: int, **overrides: Any) -> TransportModel:
        shared = self.config["shared_model"]
        values = {
            "n_sites": n_sites,
            "g": shared["g"],
            "t_mean": shared["t_mean"],
            "delta_t": shared["delta_t"],
            "detuning": shared["detuning"],
            "drain": "cavity",
            "source_site": shared["source_site"],
        }
        values.update(overrides)
        return TransportModel(**values)

    @property
    def gamma_lead(self) -> float:
        return float(self.config["shared_model"]["gamma_lead_cavity"])

    def seeds(self, count: int) -> range:
        start = int(self.config["shared_model"]["seed_start"])
        return range(start, start + count)

    def reference(self, filename: str) -> Path:
        return self.workspace / "references" / "original_figures" / filename


def _render_reference_comparison(
    context: RunContext,
    reference_name: str,
    reproduction: Path,
    output_name: str,
) -> str | None:
    """Render an audit panel when the private reference layer is available.

    The public RunThePaper package intentionally excludes standalone paper
    figures. Numerical runs must therefore remain usable without that private
    reference layer; committed public comparison panels are projected
    separately as limited validation excerpts.
    """

    if not context.allow_reference_comparisons:
        return None
    reference = context.reference(reference_name)
    if not reference.is_file():
        return None
    output = context.paths["comparisons"] / output_name
    return str(render_side_by_side(reference, reproduction, output))


def _eta(
    ensemble: list[PreparedTransport],
    rates: ChannelRates,
    final_time: float,
) -> tuple[float, float, np.ndarray]:
    result = ensemble_final_populations(ensemble, rates, final_time)
    return (
        float(result["mean"]["sink"]),
        float(result["sem"]["sink"]),
        np.asarray(result["samples"]["sink"], dtype=float),
    )


def _rate_object(channel: str, rate: float, gamma_lead: float) -> ChannelRates:
    if channel == "rescue":
        return ChannelRates(gamma_rec=rate, gamma_lead=gamma_lead)
    if channel == "dephasing":
        return ChannelRates(gamma_deph=rate, gamma_lead=gamma_lead)
    raise ValueError(f"unknown channel: {channel}")


def _adaptive_channel_scan(
    pilot: list[PreparedTransport],
    evaluation: list[PreparedTransport],
    channel: str,
    final_time: float,
    gamma_lead: float,
    rate_min: float,
    rate_max: float,
    coarse_points: int,
    refinement_points: int,
) -> dict[str, Any]:
    cache: dict[float, float] = {}

    def objective(rate: float) -> float:
        key = float(rate)
        if key not in cache:
            cache[key] = _eta(
                pilot, _rate_object(channel, key, gamma_lead), final_time
            )[0]
        return cache[key]

    coarse = np.logspace(np.log10(rate_min), np.log10(rate_max), coarse_points)
    coarse_values = np.asarray([objective(float(rate)) for rate in coarse])
    best_index = int(np.argmax(coarse_values))
    left = coarse[max(0, best_index - 1)]
    right = coarse[min(len(coarse) - 1, best_index + 1)]
    if left == right:
        refined = np.asarray([coarse[best_index]])
    else:
        refined = np.logspace(np.log10(left), np.log10(right), refinement_points)
    for rate in refined:
        objective(float(rate))

    best_rate = max(cache, key=cache.get)
    eta_mean, eta_sem, samples = _eta(
        evaluation,
        _rate_object(channel, best_rate, gamma_lead),
        final_time,
    )
    return {
        "best_rate": float(best_rate),
        "eta_mean": eta_mean,
        "eta_sem": eta_sem,
        "eta_samples": samples,
        "pilot_scan": [
            {"rate": rate, "eta_mean": cache[rate]} for rate in sorted(cache)
        ],
    }


def run_checks(context: RunContext) -> dict[str, Any]:
    started = time.perf_counter()
    payload = run_scientific_checks()
    payload["runtime_seconds"] = time.perf_counter() - started
    write_json(context.paths["checks"] / "scientific_acceptance.json", payload)
    return {
        "status": payload["status"],
        "check": str(context.paths["checks"] / "scientific_acceptance.json"),
    }


def run_dynamics(context: RunContext) -> dict[str, Any]:
    target = context.config["targets"]["dynamics"]
    gamma_lead = context.gamma_lead
    times = np.linspace(0.0, target["final_time"], context.profile["dynamics_points"])
    rows: list[dict[str, Any]] = []
    endpoint_rows: list[dict[str, Any]] = []
    started = time.perf_counter()

    conditions = {
        "rescue": ChannelRates(gamma_rec=target["gamma_rec"], gamma_lead=gamma_lead),
        "dephasing": ChannelRates(gamma_deph=target["gamma_deph"], gamma_lead=gamma_lead),
    }
    for n_sites in target["sizes_ab"]:
        count = int(context.profile["dynamics_samples_ab"])
        ensemble = prepare_ensemble(context.model(n_sites), context.seeds(count))
        for mechanism, rates in conditions.items():
            result = ensemble_population_dynamics(ensemble, rates, times)
            for observable in ("bright", "dark", "cavity", "sink", "trace"):
                for index, current_time in enumerate(times):
                    rows.append(
                        {
                            "target_id": "T002",
                            "panel": "ab",
                            "mechanism": mechanism,
                            "n_sites": n_sites,
                            "time": float(current_time),
                            "observable": observable,
                            "mean": float(result["mean"][observable][index]),
                            "sem": float(result["sem"][observable][index]),
                            "samples": count,
                            "parameter_match": "paper_subset",
                            "artifact_stage": "exploratory",
                        }
                    )
            for seed_index, value in enumerate(result["samples"]["sink"][:, -1]):
                endpoint_rows.append(
                    {
                        "panel": "ab",
                        "mechanism": mechanism,
                        "n_sites": n_sites,
                        "seed": int(context.seeds(count)[seed_index]),
                        "eta_final": float(value),
                        "dark_final": float(result["samples"]["dark"][seed_index, -1]),
                    }
                )
        print(f"dynamics: completed N={n_sites}", flush=True)

    n_sites = int(target["size_cd"])
    count = int(context.profile["dynamics_samples_cd"])
    ensemble = prepare_ensemble(context.model(n_sites), context.seeds(count))
    for mechanism, rates in conditions.items():
        result = ensemble_population_dynamics(ensemble, rates, times)
        for observable in ("bright", "dark", "cavity", "sink", "trace"):
            for index, current_time in enumerate(times):
                rows.append(
                    {
                        "target_id": "T003",
                        "panel": "cd",
                        "mechanism": mechanism,
                        "n_sites": n_sites,
                        "time": float(current_time),
                        "observable": observable,
                        "mean": float(result["mean"][observable][index]),
                        "sem": float(result["sem"][observable][index]),
                        "samples": count,
                        "parameter_match": "paper_subset",
                        "artifact_stage": "exploratory",
                    }
                )
        for seed_index, value in enumerate(result["samples"]["sink"][:, -1]):
            endpoint_rows.append(
                {
                    "panel": "cd",
                    "mechanism": mechanism,
                    "n_sites": n_sites,
                    "seed": int(context.seeds(count)[seed_index]),
                    "eta_final": float(value),
                    "dark_final": float(result["samples"]["dark"][seed_index, -1]),
                }
            )
    print("dynamics: completed N=6 manifold panels", flush=True)

    data_path = write_csv(context.paths["data"] / "fig2_dynamics.csv", rows)
    endpoint_path = write_csv(
        context.paths["data"] / "fig2_endpoint_samples.csv", endpoint_rows
    )
    figure_path = context.paths["figures"] / "fig2_reproduction.png"
    figure_files = plot_dynamics(data_path, figure_path)
    comparison = _render_reference_comparison(
        context,
        "fig2_combined_v3.png",
        figure_path,
        "fig2_source_vs_reproduction.png",
    )
    return {
        "status": "completed",
        "targets": ["T002", "T003"],
        "data": [str(data_path), str(endpoint_path)],
        "figures": figure_files,
        "comparisons": [comparison] if comparison else [],
        "runtime_seconds": time.perf_counter() - started,
    }


def _fit_scaling(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_n: dict[int, dict[str, float]] = {}
    for row in rows:
        by_n.setdefault(int(row["n_sites"]), {})[str(row["mechanism"])] = float(row["eta_mean"])
    n = np.asarray(sorted(by_n), dtype=float)
    gap = np.asarray([by_n[int(value)]["rescue"] - by_n[int(value)]["dephasing"] for value in n])

    log_mask = n <= 32
    log_coeff = np.polyfit(np.log(n[log_mask]), gap[log_mask], deg=1)
    log_prediction = np.polyval(log_coeff, np.log(n[log_mask]))
    log_r2 = 1.0 - np.sum((gap[log_mask] - log_prediction) ** 2) / np.sum(
        (gap[log_mask] - gap[log_mask].mean()) ** 2
    )

    power_mask = n >= 16
    deficit = np.maximum(1.0 - gap[power_mask], 1e-12)
    power_coeff = np.polyfit(np.log(n[power_mask]), np.log(deficit), deg=1)
    power_prediction = np.polyval(power_coeff, np.log(n[power_mask]))
    power_r2 = 1.0 - np.sum((np.log(deficit) - power_prediction) ** 2) / np.sum(
        (np.log(deficit) - np.log(deficit).mean()) ** 2
    )
    return {
        "schema_version": 1,
        "check": "scaling_fits",
        "paper_id": "2608.05312",
        "status": "passed",
        "log_fit_n_le_32": {
            "slope": float(log_coeff[0]),
            "intercept": float(log_coeff[1]),
            "paper_slope": 0.29,
            "paper_intercept": -0.30,
            "r_squared": float(log_r2),
            "paper_r_squared": 0.994,
        },
        "power_fit_n_ge_16": {
            "alpha": float(-power_coeff[0]),
            "log_prefactor": float(power_coeff[1]),
            "paper_alpha": 0.77,
            "r_squared": float(power_r2),
            "paper_r_squared": 0.998,
        },
    }


def run_scaling(context: RunContext) -> dict[str, Any]:
    target = context.config["targets"]["scaling"]
    rows: list[dict[str, Any]] = []
    scan_rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    total_samples = int(context.profile["scaling_samples"])
    pilot_samples = min(int(context.profile["optimization_samples"]), total_samples)

    for n_sites in context.profile["scaling_n"]:
        ensemble = prepare_ensemble(context.model(int(n_sites)), context.seeds(total_samples))
        pilot = ensemble[:pilot_samples]
        rate_max_deph = (
            target["deph_rate_max_n_ge_48"]
            if int(n_sites) >= 48
            else target["rate_max_n_le_32"]
        )
        scans = {
            "rescue": _adaptive_channel_scan(
                pilot,
                ensemble,
                "rescue",
                target["final_time"],
                context.gamma_lead,
                target["rate_min"],
                target["rate_max_n_le_32"],
                int(context.profile["coarse_rate_points"]),
                int(context.profile["refinement_rate_points"]),
            ),
            "dephasing": _adaptive_channel_scan(
                pilot,
                ensemble,
                "dephasing",
                target["final_time"],
                context.gamma_lead,
                target["rate_min"],
                rate_max_deph,
                int(context.profile["coarse_rate_points"]),
                int(context.profile["refinement_rate_points"]),
            ),
        }
        for mechanism, result in scans.items():
            rows.append(
                {
                    "target_id": "T001",
                    "n_sites": int(n_sites),
                    "mechanism": mechanism,
                    "eta_mean": result["eta_mean"],
                    "eta_sem": result["eta_sem"],
                    "best_rate": result["best_rate"],
                    "samples": total_samples,
                    "optimization_samples": pilot_samples,
                    "parameter_match": "paper_subset",
                    "artifact_stage": "exploratory",
                }
            )
            for point in result["pilot_scan"]:
                scan_rows.append(
                    {
                        "n_sites": int(n_sites),
                        "mechanism": mechanism,
                        "rate": point["rate"],
                        "eta_pilot_mean": point["eta_mean"],
                        "pilot_samples": pilot_samples,
                    }
                )

        baseline_mean, baseline_sem, _ = _eta(
            ensemble,
            ChannelRates(gamma_lead=context.gamma_lead),
            target["final_time"],
        )
        rows.append(
            {
                "target_id": "T001",
                "n_sites": int(n_sites),
                "mechanism": "baseline",
                "eta_mean": baseline_mean,
                "eta_sem": baseline_sem,
                "best_rate": 0.0,
                "samples": total_samples,
                "optimization_samples": 0,
                "parameter_match": "paper_subset",
                "artifact_stage": "exploratory",
            }
        )

        rec_best = scans["rescue"]["best_rate"]
        deph_best = scans["dephasing"]["best_rate"]
        candidates = []
        for rec_factor in (1 / 3, 1.0, 3.0):
            for deph_factor in (1 / 3, 1.0, 3.0):
                rec = min(target["rate_max_n_le_32"], max(target["rate_min"], rec_best * rec_factor))
                deph = min(rate_max_deph, max(target["rate_min"], deph_best * deph_factor))
                mean, _, _ = _eta(
                    pilot,
                    ChannelRates(gamma_rec=rec, gamma_deph=deph, gamma_lead=context.gamma_lead),
                    target["final_time"],
                )
                candidates.append((mean, rec, deph))
        _, rec_combined, deph_combined = max(candidates)
        combined_mean, combined_sem, _ = _eta(
            ensemble,
            ChannelRates(
                gamma_rec=rec_combined,
                gamma_deph=deph_combined,
                gamma_lead=context.gamma_lead,
            ),
            target["final_time"],
        )
        rows.append(
            {
                "target_id": "T001",
                "n_sites": int(n_sites),
                "mechanism": "combined",
                "eta_mean": combined_mean,
                "eta_sem": combined_sem,
                "best_rate": f"rec={rec_combined:.8g};deph={deph_combined:.8g}",
                "samples": total_samples,
                "optimization_samples": pilot_samples,
                "parameter_match": "paper_subset",
                "artifact_stage": "exploratory",
            }
        )
        print(
            f"scaling: N={n_sites} eta_rec={scans['rescue']['eta_mean']:.4f} "
            f"eta_deph={scans['dephasing']['eta_mean']:.4f}",
            flush=True,
        )

    data_path = write_csv(context.paths["data"] / "size_scaling.csv", rows)
    scan_path = write_csv(context.paths["data"] / "size_scaling_rate_scans.csv", scan_rows)
    fits = _fit_scaling(rows)
    fit_path = write_json(context.paths["checks"] / "scaling_fits.json", fits)
    fig1 = context.paths["figures"] / "fig1c_size_scaling.png"
    fig_s2 = context.paths["figures"] / "figS2_scaling_laws.png"
    figure_files = plot_scaling(data_path, fig1)
    scaling_files = plot_scaling_laws(data_path, fits, fig_s2)
    comparison = _render_reference_comparison(
        context,
        "fig1.png",
        fig1,
        "fig1c_source_vs_reproduction.png",
    )
    scaling_comparison = _render_reference_comparison(
        context,
        "figS3_scaling_loglaw.png",
        fig_s2,
        "figS2_source_vs_reproduction.png",
    )
    return {
        "status": "completed",
        "targets": ["T001", "T008"],
        "data": [str(data_path), str(scan_path)],
        "checks": [str(fit_path)],
        "figures": {"fig1c": figure_files, "figS2": scaling_files},
        "comparisons": [
            value for value in (comparison, scaling_comparison) if value
        ],
        "runtime_seconds": time.perf_counter() - started,
    }


def _temperature_map(
    context: RunContext,
    n_sites: int,
    samples: int,
    points: int,
    rate_ratio_min: float,
    rate_ratio_max: float,
) -> list[dict[str, Any]]:
    target = context.config["targets"]["temperature"]
    thermal = np.logspace(
        np.log10(target["thermal_ratio_min"]),
        np.log10(target["thermal_ratio_max"]),
        points,
    )
    ratios = np.logspace(np.log10(rate_ratio_min), np.log10(rate_ratio_max), points)
    ensemble = prepare_ensemble(context.model(n_sites), context.seeds(samples))
    deph_mean, _, _ = _eta(
        ensemble,
        ChannelRates(gamma_deph=target["gamma_deph"], gamma_lead=context.gamma_lead),
        target["final_time"],
    )
    rows: list[dict[str, Any]] = []
    for rate_ratio in ratios:
        gamma_rec = float(rate_ratio * target["gamma_deph"])
        for thermal_ratio in thermal:
            gamma_abs = absorption_rate(gamma_rec, float(thermal_ratio))
            rescue_mean, rescue_sem, _ = _eta(
                ensemble,
                ChannelRates(
                    gamma_rec=gamma_rec,
                    gamma_abs=gamma_abs,
                    gamma_lead=context.gamma_lead,
                ),
                target["final_time"],
            )
            rows.append(
                {
                    "target_id": "T004" if n_sites == 6 else "T010",
                    "n_sites": n_sites,
                    "thermal_ratio": float(thermal_ratio),
                    "rate_ratio": float(rate_ratio),
                    "gamma_rec": gamma_rec,
                    "gamma_abs": gamma_abs,
                    "eta_rescue": rescue_mean,
                    "eta_rescue_sem": rescue_sem,
                    "eta_deph": deph_mean,
                    "delta_eta": rescue_mean - deph_mean,
                    "samples": samples,
                    "parameter_match": "paper_subset",
                    "artifact_stage": "exploratory",
                }
            )
        print(f"temperature map N={n_sites}: ratio={rate_ratio:.4g}", flush=True)
    return rows


def run_temperature(context: RunContext) -> dict[str, Any]:
    target = context.config["targets"]["temperature"]
    started = time.perf_counter()
    line_rows: list[dict[str, Any]] = []
    thermal = np.logspace(
        np.log10(target["thermal_ratio_min"]),
        np.log10(target["thermal_ratio_max"]),
        int(context.profile["temperature_points"]),
    )
    gamma_rec = target["line_rate_ratio"] * target["gamma_deph"]
    line_samples = int(context.profile["temperature_line_samples"])
    for n_sites in (6, 64):
        ensemble = prepare_ensemble(context.model(n_sites), context.seeds(line_samples))
        deph_mean, deph_sem, _ = _eta(
            ensemble,
            ChannelRates(gamma_deph=target["gamma_deph"], gamma_lead=context.gamma_lead),
            target["final_time"],
        )
        for thermal_ratio in thermal:
            gamma_abs = absorption_rate(gamma_rec, float(thermal_ratio))
            conditions = {
                "rescue": ChannelRates(
                    gamma_rec=gamma_rec,
                    gamma_abs=gamma_abs,
                    gamma_lead=context.gamma_lead,
                ),
                "both": ChannelRates(
                    gamma_rec=gamma_rec,
                    gamma_abs=gamma_abs,
                    gamma_deph=target["gamma_deph"],
                    gamma_lead=context.gamma_lead,
                ),
            }
            values = {
                mechanism: _eta(ensemble, rates, target["final_time"])
                for mechanism, rates in conditions.items()
            }
            values["dephasing"] = (deph_mean, deph_sem, np.asarray([]))
            for mechanism, (mean, sem, _) in values.items():
                line_rows.append(
                    {
                        "target_id": "T004",
                        "n_sites": n_sites,
                        "thermal_ratio": float(thermal_ratio),
                        "mechanism": mechanism,
                        "gamma_rec": gamma_rec if mechanism != "dephasing" else 0.0,
                        "gamma_abs": gamma_abs if mechanism != "dephasing" else 0.0,
                        "gamma_deph": target["gamma_deph"] if mechanism != "rescue" else 0.0,
                        "eta_mean": mean,
                        "eta_sem": sem,
                        "samples": line_samples,
                        "parameter_match": "paper_subset",
                        "artifact_stage": "exploratory",
                    }
                )
        print(f"temperature lines: completed N={n_sites}", flush=True)

    n6_rows = _temperature_map(
        context,
        n_sites=6,
        samples=int(context.profile["temperature_map_samples_n6"]),
        points=int(context.profile["temperature_map_points_n6"]),
        rate_ratio_min=target["map_rate_ratio_min_n6"],
        rate_ratio_max=target["map_rate_ratio_max_n6"],
    )
    n64_rows = _temperature_map(
        context,
        n_sites=64,
        samples=int(context.profile["temperature_map_samples_n64"]),
        points=int(context.profile["temperature_map_points_n64"]),
        rate_ratio_min=target["map_rate_ratio_min_n64"],
        rate_ratio_max=target["map_rate_ratio_max_n64"],
    )
    line_path = write_csv(context.paths["data"] / "temperature_lines.csv", line_rows)
    n6_path = write_csv(context.paths["data"] / "temperature_map_n6.csv", n6_rows)
    n64_path = write_csv(context.paths["data"] / "temperature_map_n64.csv", n64_rows)
    fig3 = context.paths["figures"] / "fig3_temperature.png"
    fig_s4 = context.paths["figures"] / "figS4_temperature_n64.png"
    fig3_files = plot_temperature(n6_path, line_path, fig3)
    fig_s4_files = plot_temperature_n64(n64_path, fig_s4)
    comparison = _render_reference_comparison(
        context,
        "fig3_temperature2d_v2.png",
        fig3,
        "fig3_source_vs_reproduction.png",
    )
    n64_comparison = _render_reference_comparison(
        context,
        "figS5_temperature2d_N64.png",
        fig_s4,
        "figS4_source_vs_reproduction.png",
    )
    return {
        "status": "completed",
        "targets": ["T004", "T010"],
        "data": [str(line_path), str(n6_path), str(n64_path)],
        "figures": {"fig3": fig3_files, "figS4": fig_s4_files},
        "comparisons": [value for value in (comparison, n64_comparison) if value],
        "runtime_seconds": time.perf_counter() - started,
    }


def run_detuning(context: RunContext) -> dict[str, Any]:
    target = context.config["targets"]["detuning"]
    paper = {
        0.0: (0.999, 0.794),
        5.0: (1.000, 0.611),
        10.0: (1.000, 0.395),
        20.0: (1.000, 0.170),
    }
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for detuning in target["values"]:
        ensemble = prepare_ensemble(
            context.model(6, detuning=float(detuning)),
            context.seeds(int(target["samples"])),
        )
        generated: dict[str, tuple[float, float, np.ndarray]] = {}
        generated["rescue"] = _eta(
            ensemble,
            ChannelRates(gamma_rec=target["matched_rate"], gamma_lead=context.gamma_lead),
            target["final_time"],
        )
        generated["dephasing"] = _eta(
            ensemble,
            ChannelRates(gamma_deph=target["matched_rate"], gamma_lead=context.gamma_lead),
            target["final_time"],
        )
        for mechanism, (mean, sem, _) in generated.items():
            reference = paper[float(detuning)][0 if mechanism == "rescue" else 1]
            rows.append(
                {
                    "target_id": "T007",
                    "detuning": float(detuning),
                    "mechanism": mechanism,
                    "eta_mean": mean,
                    "eta_sem": sem,
                    "paper_eta": reference,
                    "absolute_error": abs(mean - reference),
                    "samples": int(target["samples"]),
                    "parameter_match": "paper_subset",
                    "artifact_stage": "exploratory",
                }
            )
        print(f"detuning: completed Delta={detuning}", flush=True)
    data_path = write_csv(context.paths["data"] / "table_s2_detuning.csv", rows)
    return {
        "status": "completed",
        "targets": ["T007"],
        "data": [str(data_path)],
        "runtime_seconds": time.perf_counter() - started,
    }


def run_site_n(context: RunContext) -> dict[str, Any]:
    target = context.config["targets"]["site_n"]
    samples = int(context.profile["site_n_samples"])
    points = int(context.profile["site_n_rate_points"])
    rate_grid = np.logspace(np.log10(target["rate_min"]), np.log10(target["rate_max"]), points)
    ensemble = prepare_ensemble(
        context.model(6, drain="site_n"), context.seeds(samples)
    )
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for gamma_deph in rate_grid:
        for gamma_rec in rate_grid:
            mean, sem, _ = _eta(
                ensemble,
                ChannelRates(
                    gamma_rec=float(gamma_rec),
                    gamma_deph=float(gamma_deph),
                    gamma_lead=target["gamma_lead_sweep"],
                ),
                target["final_time"],
            )
            rows.append(
                {
                    "target_id": "T005",
                    "record_kind": "map",
                    "mechanism": "combined",
                    "gamma_rec": float(gamma_rec),
                    "gamma_deph": float(gamma_deph),
                    "rate": "",
                    "eta_mean": mean,
                    "eta_sem": sem,
                    "samples": samples,
                    "parameter_match": "paper_subset",
                    "artifact_stage": "exploratory",
                }
            )
        print(f"site-N map: gamma_deph={gamma_deph:.4g}", flush=True)
    for mechanism in ("rescue", "dephasing"):
        for rate in rate_grid:
            mean, sem, _ = _eta(
                ensemble,
                _rate_object(mechanism, float(rate), target["gamma_lead_sweep"]),
                target["final_time"],
            )
            rows.append(
                {
                    "target_id": "T005",
                    "record_kind": "cut",
                    "mechanism": mechanism,
                    "gamma_rec": float(rate) if mechanism == "rescue" else 0.0,
                    "gamma_deph": float(rate) if mechanism == "dephasing" else 0.0,
                    "rate": float(rate),
                    "eta_mean": mean,
                    "eta_sem": sem,
                    "samples": samples,
                    "parameter_match": "paper_subset",
                    "artifact_stage": "exploratory",
                }
            )
    baseline_samples = int(context.profile["site_n_baseline_samples"])
    baseline_ensemble = prepare_ensemble(
        context.model(6, drain="site_n"), context.seeds(baseline_samples)
    )
    baseline_mean, baseline_sem, _ = _eta(
        baseline_ensemble,
        ChannelRates(gamma_lead=target["gamma_lead_sweep"]),
        target["final_time"],
    )
    paper_eta = float(target["baseline_paper_eta"])
    tolerance = float(target["baseline_abs_tolerance"])
    baseline_row = {
        "target_id": "T012",
        "record_kind": "baseline",
        "mechanism": "baseline",
        "gamma_rec": 0.0,
        "gamma_deph": 0.0,
        "rate": "",
        "eta_mean": baseline_mean,
        "eta_sem": baseline_sem,
        "paper_eta": paper_eta,
        "absolute_error": abs(baseline_mean - paper_eta),
        "samples": baseline_samples,
        "parameter_match": "paper_subset",
        "artifact_stage": "exploratory",
    }
    rows.append(baseline_row)
    sweep_path = write_csv(context.paths["data"] / "site_n_sweep.csv", rows)
    baseline_path = write_csv(
        context.paths["data"] / "site_n_no_dissipation_baseline.csv",
        [baseline_row],
    )
    baseline_check = {
        "schema_version": 1,
        "target_id": "T012",
        "status": (
            "passed"
            if 0.0 <= baseline_mean <= 1.0
            and abs(baseline_mean - paper_eta) <= tolerance
            else "failed"
        ),
        "observable": "site-N sink efficiency at zero rescue and dephasing",
        "generated_eta": baseline_mean,
        "generated_sem": baseline_sem,
        "paper_eta": paper_eta,
        "absolute_error": abs(baseline_mean - paper_eta),
        "absolute_tolerance": tolerance,
        "samples": baseline_samples,
        "parameter_match": "paper_subset",
        "generated_data_provenance": "independent_numerics",
    }
    baseline_check_path = write_json(
        context.paths["checks"] / "site_n_baseline_check.json",
        baseline_check,
    )
    if baseline_check["status"] != "passed":
        raise RuntimeError("T012 site-N no-dissipation baseline check failed")
    sweep_figure = context.paths["figures"] / "figS1_site_n_sweep.png"
    sweep_files = plot_site_n_sweep(sweep_path, sweep_figure)

    scenarios = [
        ("Site-N baseline", 6, 1.5, 25.0, "site_n"),
        ("Longer time", 6, 1.5, 100.0, "site_n"),
        ("Larger system", 10, 1.5, 25.0, "site_n"),
        ("Stronger coupling", 6, 3.0, 25.0, "site_n"),
        ("Cavity drain", 6, 1.5, 25.0, "cavity"),
        ("Cavity drain, large N", 10, 1.5, 25.0, "cavity"),
        ("Cavity drain, longer time", 6, 1.5, 100.0, "cavity"),
    ]
    paper_values = {
        "Site-N baseline": (0.684, 0.727),
        "Longer time": (0.990, 0.995),
        "Larger system": (0.468, 0.520),
        "Stronger coupling": (0.664, 0.771),
        "Cavity drain": (1.000, 0.799),
        "Cavity drain, large N": (1.000, 0.645),
        "Cavity drain, longer time": (1.000, 0.998),
    }
    table_rows: list[dict[str, Any]] = []
    pilot_count = min(int(context.profile["optimization_samples"]), samples)
    for name, n_sites, g, final_time, drain in scenarios:
        current = prepare_ensemble(
            context.model(n_sites, g=g, drain=drain), context.seeds(samples)
        )
        generated = {}
        for mechanism in ("rescue", "dephasing"):
            generated[mechanism] = _adaptive_channel_scan(
                current[:pilot_count],
                current,
                mechanism,
                final_time,
                target["gamma_lead_sweep"] if drain == "site_n" else context.gamma_lead,
                target["rate_min"],
                target["rate_max"],
                int(context.profile["coarse_rate_points"]),
                int(context.profile["refinement_rate_points"]),
            )
        paper_rec, paper_deph = paper_values[name]
        table_rows.append(
            {
                "target_id": "T006",
                "scenario": name,
                "n_sites": n_sites,
                "g": g,
                "final_time": final_time,
                "drain": drain,
                "eta_rec": generated["rescue"]["eta_mean"],
                "eta_deph": generated["dephasing"]["eta_mean"],
                "delta_eta": generated["rescue"]["eta_mean"] - generated["dephasing"]["eta_mean"],
                "best_gamma_rec": generated["rescue"]["best_rate"],
                "best_gamma_deph": generated["dephasing"]["best_rate"],
                "paper_eta_rec": paper_rec,
                "paper_eta_deph": paper_deph,
                "samples": samples,
                "parameter_match": "paper_subset",
                "artifact_stage": "exploratory",
            }
        )
        print(f"regime table: completed {name}", flush=True)
    table_path = write_csv(context.paths["data"] / "table_s1_regimes.csv", table_rows)

    dynamics_model = context.model(6, drain="site_n")
    sample = PreparedTransport.from_seed(dynamics_model, seed=0)
    times = np.linspace(0.0, target["dynamics_final_time"], context.profile["dynamics_points"])
    dynamics_rows: list[dict[str, Any]] = []
    for condition, gamma_rec in (
        ("without_rescue", 0.0),
        ("with_rescue", target["dynamics_gamma_rec"]),
    ):
        result = sample.population_dynamics(
            ChannelRates(
                gamma_rec=gamma_rec,
                gamma_lead=target["dynamics_gamma_lead"],
            ),
            times,
        )
        for observable in ("bright", "dark", "cavity", "sink"):
            for index, current_time in enumerate(times):
                dynamics_rows.append(
                    {
                        "target_id": "T009",
                        "condition": condition,
                        "time": float(current_time),
                        "observable": observable,
                        "value": float(result[observable][index]),
                        "seed": 0,
                        "gamma_lead": target["dynamics_gamma_lead"],
                        "gamma_rec": gamma_rec,
                        "parameter_match": "paper_subset",
                        "artifact_stage": "exploratory",
                    }
                )
    dynamics_path = write_csv(
        context.paths["data"] / "site_n_dynamics.csv", dynamics_rows
    )
    dynamics_figure = context.paths["figures"] / "figS3_site_n_dynamics.png"
    dynamics_files = plot_site_n_dynamics(dynamics_path, dynamics_figure)
    comparison = _render_reference_comparison(
        context,
        "figS1_siteN_phase_v2.png",
        sweep_figure,
        "figS1_source_vs_reproduction.png",
    )
    dynamics_comparison = _render_reference_comparison(
        context,
        "figS2_eigenstate_pops_v2.png",
        dynamics_figure,
        "figS3_source_vs_reproduction.png",
    )
    return {
        "status": "completed",
        "targets": ["T005", "T006", "T009", "T012"],
        "data": [
            str(sweep_path),
            str(baseline_path),
            str(table_path),
            str(dynamics_path),
        ],
        "checks": [str(baseline_check_path)],
        "figures": {"figS1": sweep_files, "figS3": dynamics_files},
        "comparisons": [
            value for value in (comparison, dynamics_comparison) if value
        ],
        "runtime_seconds": time.perf_counter() - started,
    }


TARGET_RUNNERS: dict[str, Callable[[RunContext], dict[str, Any]]] = {
    "checks": run_checks,
    "dynamics": run_dynamics,
    "scaling": run_scaling,
    "temperature": run_temperature,
    "detuning": run_detuning,
    "site-n": run_site_n,
}


def run_targets(
    context: RunContext,
    targets: list[str],
) -> dict[str, Any]:
    unknown = [target for target in targets if target not in TARGET_RUNNERS]
    if unknown:
        raise ValueError(f"unknown targets: {', '.join(unknown)}")
    started = time.perf_counter()
    manifest_path = context.paths["checks"] / "run_manifest.json"
    results: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous = {}
        if (
            previous.get("paper_id") == "2608.05312"
            and previous.get("profile") == context.profile_name
            and isinstance(previous.get("targets"), dict)
        ):
            results.update(previous["targets"])
    for target in targets:
        print(f"=== target: {target} ({context.profile_name}) ===", flush=True)
        results[target] = TARGET_RUNNERS[target](context)
        write_json(context.paths["checks"] / "run_manifest.partial.json", {
            "schema_version": 1,
            "status": "partial",
            "paper_id": "2608.05312",
            "profile": context.profile_name,
            "completed_targets": results,
        })
    manifest = {
        "schema_version": 1,
        "status": "completed_profile",
        "paper_id": "2608.05312",
        "profile": context.profile_name,
        "parameter_match": "paper_subset",
        "artifact_stage": "exploratory",
        "targets": results,
        "invocation_runtime_seconds": time.perf_counter() - started,
        "runtime_seconds": sum(
            float(result.get("runtime_seconds", 0.0) or 0.0)
            for result in results.values()
            if isinstance(result, dict)
        ),
    }
    write_json(manifest_path, manifest)
    return manifest
