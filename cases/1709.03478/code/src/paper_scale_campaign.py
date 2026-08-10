from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

from .reproduce_spme import (
    clear_basis_cache,
    cloud_observables,
    continuum_tridiagonal,
    dephased_expectation,
    lowest_band,
    prepare_cdw,
    prepare_center_third_eigenstates,
    prepare_gaussian_cloud,
    primary_basis,
    primary_hopping,
    site_density,
    spectral_expectation,
    threshold_crossing,
)


class CampaignConfigError(ValueError):
    """Raised when a paper-scale deck is structurally or scientifically incomplete."""


@dataclass(frozen=True)
class CampaignTask:
    task_id: str
    profile: str
    target_ids: tuple[str, ...]
    kind: str
    parameters: dict[str, Any]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignConfigError(message)


def derived_tube_nodes(
    geometry: dict[str, Any], order_y: int, order_z: int
) -> list[dict[str, float | str]]:
    """Return a deterministic atom-weighted Gaussian-beam depth quadrature.

    The atom density is modeled as exp[-2(y^2/w_y^2+z^2/w_z^2)] and the
    lattice depth as exp[-2(y^2+z^2)/w_b^2].  With u=sqrt(2)y/w_y and
    v=sqrt(2)z/w_z, product Gauss-Hermite quadrature directly averages the
    nonlinear observable O[f(u,v)].  Even orders permit four-quadrant symmetry
    to be merged without approximation.  This remains a paper-derived proxy
    because the paper does not state the width convention or release its
    discrete per-tube population table.
    """

    beam = float(geometry["lattice_beam_waist_um"])
    width_y = float(geometry["cloud_width_y_um"])
    width_z = float(geometry["cloud_width_z_um"])
    _require(
        beam > 0.0 and width_y > 0.0 and width_z > 0.0,
        "tube geometry widths must be positive",
    )
    _require(
        order_y >= 2 and order_y % 2 == 0 and order_z >= 2 and order_z % 2 == 0,
        "tube quadrature orders must be positive even integers",
    )
    y_nodes, y_weights = np.polynomial.hermite.hermgauss(order_y)
    z_nodes, z_weights = np.polynomial.hermite.hermgauss(order_z)
    positive_y = [
        (float(node), float(weight))
        for node, weight in zip(y_nodes, y_weights)
        if node > 0.0
    ]
    positive_z = [
        (float(node), float(weight))
        for node, weight in zip(z_nodes, z_weights)
        if node > 0.0
    ]
    nodes: list[dict[str, float | str]] = []
    for y_index, (node_y, weight_y) in enumerate(positive_y, start=1):
        for z_index, (node_z, weight_z) in enumerate(positive_z, start=1):
            factor = math.exp(
                -(((width_y * node_y) / beam) ** 2) - ((width_z * node_z) / beam) ** 2
            )
            nodes.append(
                {
                    "node_id": f"hermite_y{y_index:02d}_z{z_index:02d}",
                    "hermite_node_y": node_y,
                    "hermite_node_z": node_z,
                    "depth_factor": factor,
                    "weight": 4.0 * weight_y * weight_z / math.pi,
                }
            )
    return nodes


def load_campaign_config(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CampaignConfigError(
            f"cannot read campaign JSON {path}: {error}"
        ) from error
    validate_campaign_config(payload)
    return payload


def validate_campaign_config(payload: dict[str, Any]) -> None:
    _require(isinstance(payload, dict), "campaign config must be a JSON object")
    _require(
        payload.get("schema_version") == 2,
        "paper-scale campaign schema_version must be 2",
    )
    _require(payload.get("paper_id") == "1709.03478", "paper_id must be 1709.03478")
    _require(
        payload.get("status") in {"paper_scale_ready", "smoke"},
        "status must be paper_scale_ready or smoke",
    )
    parameters = payload.get("parameters")
    campaign = payload.get("campaign")
    _require(isinstance(parameters, dict), "top-level parameters object is required")
    _require(isinstance(campaign, dict), "top-level campaign object is required")
    for key in (
        "paper_id",
        "artifact_stage",
        "model",
        "alpha",
        "paper_wavelengths_nm",
        "paper_times_tau",
        "main_trace",
        "phase_sweep",
        "supplement_trace",
        "solver",
    ):
        _require(key in parameters, f"parameters.{key} is required")

    wavelengths = parameters["paper_wavelengths_nm"]
    alpha = float(parameters["alpha"])
    ratio = float(wavelengths["primary"]) / float(wavelengths["detuning"])
    _require(
        abs(alpha - ratio) <= 1e-9, "alpha must equal the declared wavelength ratio"
    )

    sweep = parameters["phase_sweep"]
    specs = sweep.get("specs")
    _require(
        isinstance(specs, list) and specs, "parameters.phase_sweep.specs is required"
    )
    declared_vp = [float(row["vp"]) for row in specs]
    _require(
        declared_vp == [3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "detuning specs must cover Vp=3..8 in order",
    )
    for row in specs:
        _require(
            int(row["points"]) >= 2, "every detuning spec needs at least two points"
        )
        _require(
            float(row["vd_stop"]) > float(row["vd_start"]) >= 0.0,
            "invalid detuning scan interval",
        )
        _require(
            str(row.get("basis") or "").strip() != "",
            "every detuning spec needs a scientific basis",
        )
    phases = sweep.get("phases_rad")
    _require(
        isinstance(phases, list) and len(phases) >= 1,
        "phase_sweep.phases_rad cannot be empty",
    )
    nodes = sweep.get("tube_nodes")
    _require(
        isinstance(nodes, list) and len(nodes) >= 1,
        "phase_sweep.tube_nodes cannot be empty",
    )
    node_ids = [str(row.get("node_id") or "") for row in nodes]
    _require(
        all(node_ids) and len(set(node_ids)) == len(node_ids),
        "tube node ids must be unique and non-empty",
    )
    weights = np.asarray([float(row["weight"]) for row in nodes], dtype=float)
    factors = np.asarray([float(row["depth_factor"]) for row in nodes], dtype=float)
    _require(np.all(weights > 0.0), "tube weights must be positive")
    _require(abs(float(weights.sum()) - 1.0) <= 1e-10, "tube weights must sum to one")
    _require(
        np.all((factors > 0.0) & (factors <= 1.0)),
        "tube depth factors must lie in (0,1]",
    )

    quadrature = sweep.get("tube_quadrature")
    _require(isinstance(quadrature, dict), "phase_sweep.tube_quadrature is required")
    if payload.get("status") == "paper_scale_ready":
        _require(len(phases) == 6, "paper-scale sweep requires six phase nodes")
        _require(
            np.allclose(
                np.asarray(phases, dtype=float),
                np.arange(6) * (2.0 * math.pi / 6.0),
                atol=1e-14,
                rtol=0.0,
            ),
            "paper-scale phase nodes must be the declared uniform six-point rule",
        )
        _require(len(nodes) == 8, "paper-scale sweep requires eight tube nodes")
        production_orders = quadrature["production_orders"]
        expected_nodes = derived_tube_nodes(
            quadrature["geometry"],
            int(production_orders["y"]),
            int(production_orders["z"]),
        )
        for declared, expected in zip(nodes, expected_nodes):
            _require(
                declared["node_id"] == expected["node_id"],
                "tube node ordering differs from declared quadrature",
            )
            _require(
                abs(float(declared["weight"]) - float(expected["weight"])) <= 1e-12,
                "tube node weight is stale",
            )
            _require(
                abs(float(declared["depth_factor"]) - float(expected["depth_factor"]))
                <= 1e-12,
                "tube depth factor is stale",
            )
        _require(
            int(parameters["main_trace"]["sites"]) == 738,
            "main paper-scale theory uses L=738",
        )
        _require(
            int(parameters["phase_sweep"]["sites"]) == 738,
            "phase diagram paper-scale theory uses L=738",
        )
        _require(
            int(parameters["supplement_trace"]["sites"]) == 369,
            "Supplement S1 requires its stated L=369",
        )
        _require(
            float(parameters["supplement_trace"]["gaussian_fwhm_sites"]) == 123.0,
            "Supplement S1 requires FWHM=123 sites",
        )

    profiles = campaign.get("profiles")
    _require(isinstance(profiles, dict) and profiles, "campaign.profiles is required")
    production = [
        name for name, row in profiles.items() if row.get("role") == "production"
    ]
    _require(
        len(production) == 1, "campaign must declare exactly one production profile"
    )
    for profile_name, profile in profiles.items():
        role = profile.get("role")
        overrides = profile.get("overrides", {})
        if role == "phase_convergence":
            expected_phases = np.arange(12) * (2.0 * math.pi / 12.0)
            for section in ("main_trace", "phase_sweep", "supplement_trace"):
                declared = overrides.get(section, {}).get("phases_rad")
                _require(
                    isinstance(declared, list)
                    and np.allclose(
                        np.asarray(declared, dtype=float),
                        expected_phases,
                        atol=1e-14,
                        rtol=0.0,
                    ),
                    f"{profile_name} must use the uniform twelve-point phase rule in {section}",
                )
        if role == "tube_convergence":
            declared_nodes = overrides.get("phase_sweep", {}).get("tube_nodes")
            reference_orders = quadrature["convergence_orders"]
            expected_nodes = derived_tube_nodes(
                quadrature["geometry"],
                int(reference_orders["y"]),
                int(reference_orders["z"]),
            )
            _require(
                isinstance(declared_nodes, list)
                and len(declared_nodes) == len(expected_nodes),
                f"{profile_name} has the wrong tube-node count",
            )
            for declared, expected in zip(declared_nodes, expected_nodes):
                _require(
                    declared["node_id"] == expected["node_id"],
                    f"{profile_name} tube node ordering is stale",
                )
                _require(
                    abs(float(declared["weight"]) - float(expected["weight"])) <= 1e-12,
                    f"{profile_name} tube weight is stale",
                )
                _require(
                    abs(
                        float(declared["depth_factor"])
                        - float(expected["depth_factor"])
                    )
                    <= 1e-12,
                    f"{profile_name} depth factor is stale",
                )
    output_roots = campaign.get("output_roots")
    _require(isinstance(output_roots, dict), "campaign.output_roots is required")
    for name in ("state", "data", "figures"):
        value = output_roots.get(name)
        _require(
            isinstance(value, str) and value.strip() != "",
            f"campaign.output_roots.{name} is required",
        )
        if payload.get("status") == "paper_scale_ready":
            expected_prefix = {
                "state": "outputs/checks/",
                "data": "outputs/data/",
                "figures": "outputs/figures/",
            }[name]
            _require(
                Path(value).is_absolute() or value.startswith(expected_prefix),
                f"campaign.output_roots.{name} must start with {expected_prefix} or be an explicit scratch path",
            )
    _require(isinstance(campaign.get("machine"), dict), "campaign.machine is required")
    _require(
        isinstance(campaign.get("acceptance"), dict), "campaign.acceptance is required"
    )
    _require(
        isinstance(campaign.get("crosschecks"), dict),
        "campaign.crosschecks is required",
    )


def _merge_section(
    parameters: dict[str, Any], section: str, override: dict[str, Any]
) -> None:
    target = parameters.get(section)
    if not isinstance(target, dict):
        raise CampaignConfigError(
            f"cannot override unknown parameter section: {section}"
        )
    target.update(deepcopy(override))


def parameters_for_profile(
    payload: dict[str, Any], profile_name: str
) -> tuple[dict[str, Any], set[str]]:
    profile = payload["campaign"]["profiles"].get(profile_name)
    if not isinstance(profile, dict):
        raise CampaignConfigError(f"unknown profile: {profile_name}")
    parameters = deepcopy(payload["parameters"])
    for section, override in profile.get("overrides", {}).items():
        _require(
            isinstance(override, dict), f"profile override {section} must be an object"
        )
        _merge_section(parameters, section, override)
    targets = set(profile.get("targets") or ["T002", "T003", "T004", "T005", "T006"])
    sweep = parameters["phase_sweep"]
    _require(
        bool(sweep.get("phases_rad")), f"profile {profile_name} has no phase nodes"
    )
    nodes = sweep.get("tube_nodes")
    _require(
        isinstance(nodes, list) and nodes, f"profile {profile_name} has no tube nodes"
    )
    _require(
        abs(sum(float(row["weight"]) for row in nodes) - 1.0) <= 1e-10,
        f"profile {profile_name} tube weights do not sum to one",
    )
    return parameters, targets


def _new_task(
    profile: str, target_ids: Iterable[str], kind: str, parameters: dict[str, Any]
) -> CampaignTask:
    identity = {
        "profile": profile,
        "target_ids": list(target_ids),
        "kind": kind,
        "parameters": parameters,
    }
    task_id = f"{'-'.join(identity['target_ids']).lower()}__{kind}__{_fingerprint(identity)[:16]}"
    return CampaignTask(
        task_id, profile, tuple(identity["target_ids"]), kind, parameters
    )


def _linspace(spec: dict[str, Any]) -> list[float]:
    return np.linspace(
        float(spec["vd_start"]), float(spec["vd_stop"]), int(spec["points"])
    ).tolist()


def build_tasks(
    payload: dict[str, Any], profile_names: Iterable[str] | None = None
) -> list[CampaignTask]:
    validate_campaign_config(payload)
    names = list(profile_names or payload["campaign"]["profiles"].keys())
    tasks: list[CampaignTask] = []
    for profile_name in names:
        parameters, targets = parameters_for_profile(payload, profile_name)
        alpha = float(parameters["alpha"])
        solver = parameters["solver"]
        if "T002" in targets:
            spec = parameters["main_trace"]
            for phase_index, phi in enumerate(map(float, spec["phases_rad"])):
                tasks.append(
                    _new_task(
                        profile_name,
                        ["T002"],
                        "main_trace_phase",
                        {
                            "sites": int(spec["sites"]),
                            "grid_points_per_site": int(spec["grid_points_per_site"]),
                            "vp": float(spec["vp"]),
                            "vd_values": list(map(float, spec["vd_values"])),
                            "times_tau": np.linspace(
                                float(spec["time_tau"]["start"]),
                                float(spec["time_tau"]["stop"]),
                                int(spec["time_tau"]["points"]),
                            ).tolist(),
                            "phase_index": phase_index,
                            "phi": phi,
                            "alpha": alpha,
                            "solver": solver,
                        },
                    )
                )

        if targets.intersection({"T003", "T004"}):
            spec = parameters["phase_sweep"]
            node_rows = [
                {
                    "node_id": "central",
                    "depth_factor": 1.0,
                    "weight": 0.0,
                    "central": True,
                }
            ]
            node_rows.extend({**row, "central": False} for row in spec["tube_nodes"])
            for detuning_spec in spec["specs"]:
                for node in node_rows:
                    for phase_index, phi in enumerate(map(float, spec["phases_rad"])):
                        tasks.append(
                            _new_task(
                                profile_name,
                                ["T003", "T004"],
                                "stationary_sweep_phase",
                                {
                                    "sites": int(spec["sites"]),
                                    "grid_points_per_site": int(
                                        spec["grid_points_per_site"]
                                    ),
                                    "vp": float(detuning_spec["vp"]),
                                    "vd_values": _linspace(detuning_spec),
                                    "node_id": node["node_id"],
                                    "depth_factor": float(node["depth_factor"]),
                                    "tube_weight": float(node["weight"]),
                                    "central": bool(node["central"]),
                                    "phase_index": phase_index,
                                    "phi": phi,
                                    "alpha": alpha,
                                    "solver": solver,
                                    "threshold": float(spec["threshold"]),
                                    "imbalance_time_tau": float(
                                        parameters["paper_times_tau"][
                                            "numerical_imbalance"
                                        ]
                                    ),
                                    "edge_time_tau": float(
                                        parameters["paper_times_tau"]["edge_density"]
                                    ),
                                },
                            )
                        )

        if "T005" in targets:
            spec = parameters["supplement_trace"]
            times = np.linspace(
                float(spec["time_tau"]["start"]),
                float(spec["time_tau"]["stop"]),
                int(spec["time_tau"]["points"]),
            ).tolist()
            for trap in map(float, spec["trap_edge_recoil"]):
                for vd in map(float, spec["vd_values"]):
                    for phase_index, phi in enumerate(map(float, spec["phases_rad"])):
                        tasks.append(
                            _new_task(
                                profile_name,
                                ["T005"],
                                "supplement_trace_phase",
                                {
                                    "sites": int(spec["sites"]),
                                    "grid_points_per_site": int(
                                        spec["grid_points_per_site"]
                                    ),
                                    "vp": float(spec["vp"]),
                                    "vd": vd,
                                    "trap_edge_recoil": trap,
                                    "gaussian_fwhm_sites": float(
                                        spec["gaussian_fwhm_sites"]
                                    ),
                                    "times_tau": times,
                                    "phase_index": phase_index,
                                    "phi": phi,
                                    "alpha": alpha,
                                    "solver": solver,
                                },
                            )
                        )

        if "T006" in targets:
            spec = parameters["phase_sweep"]
            detuning_spec = next(
                row for row in spec["specs"] if float(row["vp"]) == 4.0
            )
            node_rows = [
                {
                    "node_id": "central",
                    "depth_factor": 1.0,
                    "weight": 0.0,
                    "central": True,
                }
            ]
            node_rows.extend({**row, "central": False} for row in spec["tube_nodes"])
            for node in node_rows:
                for phase_index, phi in enumerate(map(float, spec["phases_rad"])):
                    tasks.append(
                        _new_task(
                            profile_name,
                            ["T006"],
                            "finite_time_sweep_phase",
                            {
                                "sites": int(spec["sites"]),
                                "grid_points_per_site": int(
                                    spec["grid_points_per_site"]
                                ),
                                "vp": 4.0,
                                "vd_values": _linspace(detuning_spec),
                                "node_id": node["node_id"],
                                "depth_factor": float(node["depth_factor"]),
                                "tube_weight": float(node["weight"]),
                                "central": bool(node["central"]),
                                "phase_index": phase_index,
                                "phi": phi,
                                "alpha": alpha,
                                "solver": solver,
                                "time_tau": float(
                                    parameters["paper_times_tau"]["numerical_imbalance"]
                                ),
                            },
                        )
                    )
    return tasks


def _orthogonality_error(vectors: np.ndarray) -> float:
    return float(np.max(np.abs(vectors.T @ vectors - np.eye(vectors.shape[1]))))


def _simulate_paper_scalar(
    *,
    sites: int,
    points_per_site: int,
    vp: float,
    vd: float,
    alpha: float,
    phi: float,
    imbalance_time_tau: float,
    edge_time_tau: float,
    phase_hopping: float | None,
    solver: dict[str, Any],
    dephased: bool,
) -> dict[str, float]:
    """Evaluate I and D using the paper's distinct CDW/center-box preparations."""

    basis = primary_basis(
        sites,
        points_per_site,
        vp,
        alpha,
        int(solver["primary_bloch_harmonics"]),
        int(solver["primary_bloch_points"]),
    )
    _, eigenvalues, eigenvectors = lowest_band(
        sites, points_per_site, vp, vd, alpha, phi
    )
    overlap = eigenvectors.T @ basis.wannier
    cdw_density, imbalance_operator = prepare_cdw(overlap)
    center_density, center_operator, center_sites = prepare_center_third_eigenstates(
        sites=sites,
        points_per_site=points_per_site,
        vp=vp,
        vd=vd,
        alpha=alpha,
        phi=phi,
        final_eigenvectors=eigenvectors,
    )
    hopping = basis.hopping if phase_hopping is None else phase_hopping
    if dephased:
        imbalance = dephased_expectation(imbalance_operator, cdw_density)
        center_probability = dephased_expectation(center_operator, center_density)
    else:
        imbalance = spectral_expectation(
            eigenvalues, imbalance_operator, cdw_density, imbalance_time_tau, hopping
        )
        center_probability = spectral_expectation(
            eigenvalues, center_operator, center_density, edge_time_tau, hopping
        )
    center_probability_0 = spectral_expectation(
        eigenvalues, center_operator, center_density, 0.0, hopping
    )
    return {
        "imbalance": imbalance,
        "edge_density": 1.0 - center_probability / center_probability_0,
        "projection_cdw": float(np.trace(cdw_density).real / math.ceil(sites / 2)),
        "projection_center": float(np.trace(center_density).real / center_sites),
        "orthogonality_error": _orthogonality_error(eigenvectors),
    }


def execute_task(task: CampaignTask) -> dict[str, Any]:
    p = task.parameters
    solver = p["solver"]
    started = time.monotonic()
    diagnostics: list[dict[str, float]] = []
    rows: list[dict[str, Any]] = []
    try:
        if task.kind == "main_trace_phase":
            basis = primary_basis(
                p["sites"],
                p["grid_points_per_site"],
                p["vp"],
                p["alpha"],
                int(solver["primary_bloch_harmonics"]),
                int(solver["primary_bloch_points"]),
            )
            for vd in p["vd_values"]:
                _, eigenvalues, eigenvectors = lowest_band(
                    p["sites"],
                    p["grid_points_per_site"],
                    p["vp"],
                    vd,
                    p["alpha"],
                    p["phi"],
                )
                density, center, center_sites = prepare_center_third_eigenstates(
                    sites=p["sites"],
                    points_per_site=p["grid_points_per_site"],
                    vp=p["vp"],
                    vd=vd,
                    alpha=p["alpha"],
                    phi=p["phi"],
                    final_eigenvectors=eigenvectors,
                )
                initial = spectral_expectation(
                    eigenvalues, center, density, 0.0, basis.hopping
                )
                diagnostics.append(
                    {
                        "orthogonality_error": _orthogonality_error(eigenvectors),
                        "projection_fraction": float(
                            np.trace(density).real / center_sites
                        ),
                    }
                )
                for time_tau in p["times_tau"]:
                    retained = spectral_expectation(
                        eigenvalues, center, density, time_tau, basis.hopping
                    )
                    rows.append(
                        {
                            "vd_recoil": vd,
                            "time_tau": time_tau,
                            "edge_density": 1.0 - retained / initial,
                        }
                    )

        elif task.kind == "stationary_sweep_phase":
            central_hopping = primary_hopping(
                p["vp"],
                int(solver["primary_bloch_harmonics"]),
                int(solver["primary_bloch_points"]),
            )
            for vd in p["vd_values"]:
                result = _simulate_paper_scalar(
                    sites=p["sites"],
                    points_per_site=p["grid_points_per_site"],
                    vp=p["vp"] * p["depth_factor"],
                    vd=vd * p["depth_factor"],
                    alpha=p["alpha"],
                    phi=p["phi"],
                    imbalance_time_tau=p["imbalance_time_tau"],
                    edge_time_tau=p["edge_time_tau"],
                    phase_hopping=central_hopping,
                    solver=solver,
                    dephased=True,
                )
                diagnostics.append(
                    {
                        "orthogonality_error": result["orthogonality_error"],
                        "projection_fraction": min(
                            result["projection_cdw"], result["projection_center"]
                        ),
                    }
                )
                rows.append(
                    {
                        "vd_recoil": vd,
                        "imbalance": result["imbalance"],
                        "edge_density": result["edge_density"],
                    }
                )

        elif task.kind == "supplement_trace_phase":
            basis = primary_basis(
                p["sites"],
                p["grid_points_per_site"],
                p["vp"],
                p["alpha"],
                int(solver["primary_bloch_harmonics"]),
                int(solver["primary_bloch_points"]),
            )
            _, eigenvalues, eigenvectors = lowest_band(
                p["sites"],
                p["grid_points_per_site"],
                p["vp"],
                p["vd"],
                p["alpha"],
                p["phi"],
                p["trap_edge_recoil"],
            )
            overlap = eigenvectors.T @ basis.wannier
            density = prepare_gaussian_cloud(overlap, p["gaussian_fwhm_sites"])
            center_start = p["sites"] // 3
            center_slice = slice(center_start, p["sites"] - center_start)
            diagnostics.append(
                {
                    "orthogonality_error": _orthogonality_error(eigenvectors),
                    "projection_fraction": float(
                        np.trace(density).real
                        / np.sum(
                            np.exp(
                                -4.0
                                * math.log(2.0)
                                * (
                                    (np.arange(p["sites"]) - (p["sites"] - 1.0) / 2.0)
                                    / p["gaussian_fwhm_sites"]
                                )
                                ** 2
                            )
                        )
                    ),
                }
            )
            for time_tau in p["times_tau"]:
                observables = cloud_observables(
                    site_density(
                        eigenvalues, overlap, density, time_tau, basis.hopping
                    ),
                    center_slice,
                )
                rows.append({"time_tau": time_tau, **observables})

        elif task.kind == "finite_time_sweep_phase":
            central_hopping = primary_hopping(
                p["vp"],
                int(solver["primary_bloch_harmonics"]),
                int(solver["primary_bloch_points"]),
            )
            for vd in p["vd_values"]:
                result = _simulate_paper_scalar(
                    sites=p["sites"],
                    points_per_site=p["grid_points_per_site"],
                    vp=p["vp"] * p["depth_factor"],
                    vd=vd * p["depth_factor"],
                    alpha=p["alpha"],
                    phi=p["phi"],
                    imbalance_time_tau=p["time_tau"],
                    edge_time_tau=p["time_tau"],
                    phase_hopping=central_hopping,
                    solver=solver,
                    dephased=False,
                )
                diagnostics.append(
                    {
                        "orthogonality_error": result["orthogonality_error"],
                        "projection_fraction": min(
                            result["projection_cdw"], result["projection_center"]
                        ),
                    }
                )
                rows.append(
                    {
                        "vd_recoil": vd,
                        "imbalance": result["imbalance"],
                        "edge_density": result["edge_density"],
                    }
                )
        else:
            raise ValueError(f"unknown campaign task kind: {task.kind}")
    finally:
        clear_basis_cache()

    return {
        "rows": rows,
        "diagnostics": {
            "max_orthogonality_error": max(
                row["orthogonality_error"] for row in diagnostics
            ),
            "min_projection_fraction": min(
                row["projection_fraction"] for row in diagnostics
            ),
        },
        "duration_seconds": round(time.monotonic() - started, 6),
    }


def _output_root(payload: dict[str, Any], workspace_root: Path, kind: str) -> Path:
    configured = Path(payload["campaign"]["output_roots"][kind])
    return configured if configured.is_absolute() else workspace_root / configured


def _campaign_root(payload: dict[str, Any], workspace_root: Path) -> Path:
    return _output_root(payload, workspace_root, "state")


def _checkpoint_path(root: Path, task: CampaignTask) -> Path:
    return root / "checkpoints" / task.profile / f"{task.task_id}.json"


def _checkpoint_valid(path: Path, config_hash: str, task: CampaignTask) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    expected_task = json.loads(_canonical_json(asdict(task)))
    return (
        payload.get("status") == "complete"
        and payload.get("config_hash") == config_hash
        and payload.get("task") == expected_task
    )


def prepare_campaign(
    payload: dict[str, Any],
    workspace_root: Path,
    profile_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    tasks = build_tasks(payload, profile_names)
    root = _campaign_root(payload, workspace_root)
    counts: dict[str, int] = defaultdict(int)
    for task in tasks:
        counts[task.profile] += 1
    manifest = {
        "schema_version": 2,
        "paper_id": payload["paper_id"],
        "status": "prepared",
        "config_hash": _fingerprint(payload),
        "output_roots": {
            name: str(_output_root(payload, workspace_root, name))
            for name in ("state", "data", "figures")
        },
        "profiles": dict(sorted(counts.items())),
        "task_count": len(tasks),
        "checkpoint_unit": "one phase-resolved parameter block",
        "machine": payload["campaign"]["machine"],
        "reference_assets_read": False,
        "author_code_or_arrays_used": False,
    }
    _atomic_json(root / "campaign_manifest.json", manifest)
    return manifest


def run_campaign(
    payload: dict[str, Any],
    workspace_root: Path,
    *,
    profile_names: Iterable[str] | None = None,
    resume: bool = True,
    max_tasks: int | None = None,
    shard_index: int = 0,
    shard_count: int = 1,
) -> dict[str, Any]:
    _require(
        shard_count >= 1 and 0 <= shard_index < shard_count, "invalid shard index/count"
    )
    manifest = prepare_campaign(payload, workspace_root, profile_names)
    tasks = build_tasks(payload, profile_names)
    root = _campaign_root(payload, workspace_root)
    config_hash = manifest["config_hash"]
    selected = [
        task
        for task in tasks
        if int(_fingerprint(task.task_id)[:16], 16) % shard_count == shard_index
    ]
    completed = skipped = executed = 0
    started = time.monotonic()
    for task in selected:
        checkpoint = _checkpoint_path(root, task)
        if resume and _checkpoint_valid(checkpoint, config_hash, task):
            skipped += 1
            completed += 1
            continue
        if max_tasks is not None and executed >= max_tasks:
            break
        result = execute_task(task)
        _atomic_json(
            checkpoint,
            {
                "schema_version": 1,
                "status": "complete",
                "config_hash": config_hash,
                "task": asdict(task),
                "result": result,
            },
        )
        executed += 1
        completed += 1
    summary = {
        "schema_version": 1,
        "status": "complete" if completed == len(selected) else "partial",
        "config_hash": config_hash,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "selected_tasks": len(selected),
        "completed_tasks_this_invocation": completed,
        "executed_tasks": executed,
        "resumed_tasks": skipped,
        "duration_seconds": round(time.monotonic() - started, 6),
    }
    _atomic_json(
        root
        / "checks"
        / "shards"
        / f"shard-{shard_index:05d}-of-{shard_count:05d}.json",
        summary,
    )
    return summary


def _load_results(
    payload: dict[str, Any], workspace_root: Path, profile: str
) -> tuple[list[tuple[CampaignTask, dict[str, Any]]], list[str]]:
    root = _campaign_root(payload, workspace_root)
    config_hash = _fingerprint(payload)
    completed: list[tuple[CampaignTask, dict[str, Any]]] = []
    missing: list[str] = []
    for task in build_tasks(payload, [profile]):
        checkpoint = _checkpoint_path(root, task)
        if not _checkpoint_valid(checkpoint, config_hash, task):
            missing.append(task.task_id)
            continue
        stored = json.loads(checkpoint.read_text(encoding="utf-8"))
        completed.append((task, stored["result"]))
    return completed, missing


def _mean_std(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return float(np.mean(array)), float(np.std(array))


def _tables_for_profile(
    payload: dict[str, Any], workspace_root: Path, profile: str
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    completed, missing = _load_results(payload, workspace_root, profile)
    parameters, targets = parameters_for_profile(payload, profile)
    by_kind: dict[str, list[tuple[CampaignTask, dict[str, Any]]]] = defaultdict(list)
    for task, result in completed:
        by_kind[task.kind].append((task, result))
    tables: dict[str, list[dict[str, Any]]] = {}

    if "T002" in targets and not any("t002" in item for item in missing):
        grouped: dict[tuple[float, float], list[float]] = defaultdict(list)
        for task, result in by_kind["main_trace_phase"]:
            for row in result["rows"]:
                grouped[(row["vd_recoil"], row["time_tau"])].append(row["edge_density"])
        rows = []
        for (vd, time_tau), values in sorted(grouped.items()):
            mean, std = _mean_std(values)
            rows.append(
                {
                    "target_id": "T002",
                    "vp_recoil": float(parameters["main_trace"]["vp"]),
                    "vd_recoil": vd,
                    "time_tau": time_tau,
                    "edge_density_mean": mean,
                    "edge_density_phase_std": std,
                    "sites": int(parameters["main_trace"]["sites"]),
                    "grid_points_per_site": int(
                        parameters["main_trace"]["grid_points_per_site"]
                    ),
                    "phase_samples": len(values),
                    "parameter_match": "paper_scale_method_match",
                }
            )
        tables["T002"] = rows

    if targets.intersection({"T003", "T004"}) and not any(
        "t003-t004" in item for item in missing
    ):
        phase_node: dict[
            tuple[float, float, float, str], tuple[float, float, float, bool]
        ] = {}
        for task, result in by_kind["stationary_sweep_phase"]:
            p = task.parameters
            for row in result["rows"]:
                phase_node[(p["vp"], row["vd_recoil"], p["phi"], p["node_id"])] = (
                    row["imbalance"],
                    row["edge_density"],
                    p["tube_weight"],
                    p["central"],
                )
        pairs = sorted({(key[0], key[1]) for key in phase_node})
        rows = []
        for vp, vd in pairs:
            phases = sorted(
                {key[2] for key in phase_node if key[0] == vp and key[1] == vd}
            )
            central_i, central_d, tube_i, tube_d = [], [], [], []
            for phi in phases:
                values = [
                    (node, *value)
                    for (vp_key, vd_key, phi_key, node), value in phase_node.items()
                    if vp_key == vp and vd_key == vd and phi_key == phi
                ]
                central = next(value for value in values if value[4])
                tube = [value for value in values if not value[4]]
                central_i.append(central[1])
                central_d.append(central[2])
                tube_i.append(sum(value[3] * value[1] for value in tube))
                tube_d.append(sum(value[3] * value[2] for value in tube))
            for averaging, i_values, d_values in (
                ("central", central_i, central_d),
                ("tube_proxy", tube_i, tube_d),
            ):
                i_mean, i_std = _mean_std(i_values)
                d_mean, d_std = _mean_std(d_values)
                rows.append(
                    {
                        "target_ids": "T003;T004",
                        "vp_recoil": vp,
                        "vd_recoil": vd,
                        "averaging": averaging,
                        "imbalance": i_mean,
                        "edge_density": d_mean,
                        "imbalance_phase_std": i_std,
                        "edge_density_phase_std": d_std,
                        "sites": int(parameters["phase_sweep"]["sites"]),
                        "grid_points_per_site": int(
                            parameters["phase_sweep"]["grid_points_per_site"]
                        ),
                        "phase_samples": len(phases),
                        "tube_nodes": (
                            0
                            if averaging == "central"
                            else len(parameters["phase_sweep"]["tube_nodes"])
                        ),
                        "evaluation": "stationary_diagonal_ensemble",
                        "parameter_match": (
                            "paper_scale_method_match"
                            if averaging == "central"
                            else "paper_scale_method_proxy"
                        ),
                    }
                )
        tables["T003"] = rows
        boundary_rows = []
        for vp in sorted({row["vp_recoil"] for row in rows}):
            for averaging in ("central", "tube_proxy"):
                subset = sorted(
                    (
                        row
                        for row in rows
                        if row["vp_recoil"] == vp and row["averaging"] == averaging
                    ),
                    key=lambda row: row["vd_recoil"],
                )
                x = np.asarray([row["vd_recoil"] for row in subset])
                imbalance = np.asarray([row["imbalance"] for row in subset])
                edge = np.asarray([row["edge_density"] for row in subset])
                threshold = float(parameters["phase_sweep"]["threshold"])
                lower = threshold_crossing(x, imbalance, threshold, "up")
                upper = threshold_crossing(x, edge, threshold, "down")
                boundary_rows.append(
                    {
                        "target_id": "T004",
                        "vp_recoil": vp,
                        "averaging": averaging,
                        "v_imbalance_recoil": lower,
                        "v_edge_recoil": upper,
                        "intermediate_width_recoil": (
                            None if lower is None or upper is None else upper - lower
                        ),
                        "threshold": threshold,
                        "parameter_match": (
                            "paper_scale_method_match"
                            if averaging == "central"
                            else "paper_scale_method_proxy"
                        ),
                    }
                )
        tables["T004"] = boundary_rows

    if "T005" in targets and not any("t005" in item for item in missing):
        grouped: dict[tuple[float, float, float], list[dict[str, float]]] = defaultdict(
            list
        )
        for task, result in by_kind["supplement_trace_phase"]:
            for row in result["rows"]:
                grouped[
                    (
                        task.parameters["trap_edge_recoil"],
                        task.parameters["vd"],
                        row["time_tau"],
                    )
                ].append(row)
        rows = []
        for (trap, vd, time_tau), values in sorted(grouped.items()):
            fwhm, fwhm_std = _mean_std([row["fwhm_sites"] for row in values])
            rms, rms_std = _mean_std([row["rms_sites"] for row in values])
            edge, edge_std = _mean_std([row["edge_density"] for row in values])
            rows.append(
                {
                    "target_id": "T005",
                    "trap_edge_recoil": trap,
                    "vp_recoil": float(parameters["supplement_trace"]["vp"]),
                    "vd_recoil": vd,
                    "time_tau": time_tau,
                    "fwhm_sites": fwhm,
                    "fwhm_phase_std": fwhm_std,
                    "edge_density": edge,
                    "edge_density_phase_std": edge_std,
                    "rms_sites": rms,
                    "rms_phase_std": rms_std,
                    "sites": int(parameters["supplement_trace"]["sites"]),
                    "phase_samples": len(values),
                    "parameter_match": "paper_exact_stated_parameters",
                }
            )
        tables["T005"] = rows

    if "T006" in targets and not any("t006" in item for item in missing):
        phase_node: dict[tuple[float, float, str], tuple[float, float, float, bool]] = (
            {}
        )
        for task, result in by_kind["finite_time_sweep_phase"]:
            p = task.parameters
            for row in result["rows"]:
                phase_node[(row["vd_recoil"], p["phi"], p["node_id"])] = (
                    row["imbalance"],
                    row["edge_density"],
                    p["tube_weight"],
                    p["central"],
                )
        rows = []
        for vd in sorted({key[0] for key in phase_node}):
            phases = sorted({key[1] for key in phase_node if key[0] == vd})
            central_i, central_d, tube_i, tube_d = [], [], [], []
            for phi in phases:
                values = [
                    (node, *value)
                    for (vd_key, phi_key, node), value in phase_node.items()
                    if vd_key == vd and phi_key == phi
                ]
                central = next(value for value in values if value[4])
                tube = [value for value in values if not value[4]]
                central_i.append(central[1])
                central_d.append(central[2])
                tube_i.append(sum(value[3] * value[1] for value in tube))
                tube_d.append(sum(value[3] * value[2] for value in tube))
            for averaging, i_values, d_values in (
                ("central", central_i, central_d),
                ("tube_proxy", tube_i, tube_d),
            ):
                i_mean, i_std = _mean_std(i_values)
                d_mean, d_std = _mean_std(d_values)
                rows.append(
                    {
                        "target_id": "T006",
                        "vp_recoil": 4.0,
                        "vd_recoil": vd,
                        "averaging": averaging,
                        "imbalance_3000tau": i_mean,
                        "edge_density_3000tau": d_mean,
                        "imbalance_phase_std": i_std,
                        "edge_density_phase_std": d_std,
                        "sites": int(parameters["phase_sweep"]["sites"]),
                        "phase_samples": len(phases),
                        "parameter_match": (
                            "paper_scale_method_match"
                            if averaging == "central"
                            else "paper_scale_method_proxy"
                        ),
                    }
                )
        tables["T006"] = rows
    return tables, missing


def _acceptance(
    tables: dict[str, list[dict[str, Any]]], payload: dict[str, Any]
) -> dict[str, Any]:
    tolerance = float(payload["campaign"]["acceptance"]["width_trend_tolerance_recoil"])
    checks: dict[str, dict[str, bool]] = {}
    t2 = tables.get("T002", [])
    if t2:
        final_time = max(row["time_tau"] for row in t2)
        final = {
            row["vd_recoil"]: row["edge_density_mean"]
            for row in t2
            if row["time_tau"] == final_time
        }
        checks["T002"] = {
            "values_bounded": all(
                -1e-10 <= row["edge_density_mean"] <= 1.0 + 1e-10 for row in t2
            ),
            "final_ordering": final.get(0.0, -math.inf)
            > final.get(0.57, math.inf)
            > final.get(1.04, math.inf),
        }
    t3 = tables.get("T003", [])
    if t3:
        target_checks = {
            "values_bounded": all(
                -0.02 <= row["imbalance"] <= 1.02
                and -0.02 <= row["edge_density"] <= 1.02
                for row in t3
            )
        }
        for vp in (4.0, 6.0, 8.0):
            rows = sorted(
                (
                    row
                    for row in t3
                    if row["vp_recoil"] == vp and row["averaging"] == "central"
                ),
                key=lambda row: row["vd_recoil"],
            )
            target_checks[f"vp{vp:g}_imbalance_rises"] = (
                bool(rows) and rows[-1]["imbalance"] > rows[0]["imbalance"]
            )
            target_checks[f"vp{vp:g}_edge_falls"] = (
                bool(rows) and rows[-1]["edge_density"] < rows[0]["edge_density"]
            )
        checks["T003"] = target_checks
    t4 = tables.get("T004", [])
    if t4:
        central = sorted(
            (row for row in t4 if row["averaging"] == "central"),
            key=lambda row: row["vp_recoil"],
        )
        widths = [row["intermediate_width_recoil"] for row in central]
        checks["T004"] = {
            "all_six_central_boundaries_resolved": len(widths) == 6
            and all(value is not None for value in widths),
            "all_widths_nonnegative": all(
                value is not None and value >= -1e-9 for value in widths
            ),
            "width_nonincreasing_with_vp": (
                all(
                    right <= left + tolerance for left, right in zip(widths, widths[1:])
                )
                if all(value is not None for value in widths)
                else False
            ),
        }
    t5 = tables.get("T005", [])
    if t5:
        target_checks = {
            "values_bounded": all(
                -1e-10 <= row["edge_density"] <= 1.0 + 1e-10
                and row["rms_sites"] >= 0.0
                and row["fwhm_sites"] >= 0.0
                for row in t5
            )
        }
        final_time = max(row["time_tau"] for row in t5)
        for trap in sorted({row["trap_edge_recoil"] for row in t5}):
            final = {
                row["vd_recoil"]: row
                for row in t5
                if row["trap_edge_recoil"] == trap and row["time_tau"] == final_time
            }
            target_checks[f"trap_{trap:g}_edge_order"] = (
                final[0.0]["edge_density"]
                > final[0.57]["edge_density"]
                > final[1.04]["edge_density"]
            )
            target_checks[f"trap_{trap:g}_rms_order"] = (
                final[0.0]["rms_sites"]
                > final[0.57]["rms_sites"]
                > final[1.04]["rms_sites"]
            )
        checks["T005"] = target_checks
    t6 = tables.get("T006", [])
    if t6:
        target_checks = {}
        for averaging in ("central", "tube_proxy"):
            rows = sorted(
                (row for row in t6 if row["averaging"] == averaging),
                key=lambda row: row["vd_recoil"],
            )
            target_checks[f"{averaging}_imbalance_rises"] = (
                bool(rows)
                and rows[-1]["imbalance_3000tau"] > rows[0]["imbalance_3000tau"]
            )
            target_checks[f"{averaging}_edge_falls"] = (
                bool(rows)
                and rows[-1]["edge_density_3000tau"] < rows[0]["edge_density_3000tau"]
            )
        checks["T006"] = target_checks
    target_status = {
        target: "passed" if values and all(values.values()) else "failed"
        for target, values in checks.items()
    }
    return {
        "schema_version": 1,
        "status": (
            "passed"
            if len(target_status) == 5
            and all(value == "passed" for value in target_status.values())
            else "failed"
        ),
        "targets": target_status,
        "checks": checks,
    }


def _comparison_key(row: dict[str, Any], fields: list[str]) -> tuple[Any, ...]:
    return tuple(
        round(value, 12) if isinstance(value, float) else value
        for value in (row[field] for field in fields)
    )


def _compare_tables(
    production: list[dict[str, Any]],
    reference: list[dict[str, Any]],
    keys: list[str],
    values: list[str],
    tolerance: float,
) -> dict[str, Any]:
    reference_by_key = {_comparison_key(row, keys): row for row in reference}
    differences: list[float] = []
    unresolved = missing = 0
    for row in production:
        other = reference_by_key.get(_comparison_key(row, keys))
        if other is None:
            missing += 1
            continue
        for field in values:
            left, right = row.get(field), other.get(field)
            if (
                left is None
                or right is None
                or not math.isfinite(float(left))
                or not math.isfinite(float(right))
            ):
                unresolved += 1
            else:
                differences.append(abs(float(left) - float(right)))
    maximum = max(differences, default=None)
    return {
        "status": (
            "passed"
            if missing == 0
            and unresolved == 0
            and maximum is not None
            and maximum <= tolerance
            else "failed"
        ),
        "max_absolute_difference": maximum,
        "tolerance": tolerance,
        "missing_rows": missing,
        "unresolved_values": unresolved,
        "values_compared": len(differences),
    }


def convergence_report(
    payload: dict[str, Any],
    workspace_root: Path,
    production_tables: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    profile_rows = payload["campaign"]["profiles"]
    references = [
        (name, row)
        for name, row in profile_rows.items()
        if row.get("role")
        in {
            "grid_convergence",
            "size_convergence",
            "phase_convergence",
            "tube_convergence",
        }
    ]
    table_specs = {
        "T002": (["vd_recoil", "time_tau"], ["edge_density_mean"]),
        "T003": (
            ["vp_recoil", "vd_recoil", "averaging"],
            ["imbalance", "edge_density"],
        ),
        "T004": (
            ["vp_recoil", "averaging"],
            ["v_imbalance_recoil", "v_edge_recoil", "intermediate_width_recoil"],
        ),
        "T005": (
            ["trap_edge_recoil", "vd_recoil", "time_tau"],
            ["fwhm_sites", "edge_density", "rms_sites"],
        ),
        "T006": (
            ["vd_recoil", "averaging"],
            ["imbalance_3000tau", "edge_density_3000tau"],
        ),
    }
    checks: dict[str, Any] = {}
    for name, profile in references:
        tables, missing = _tables_for_profile(payload, workspace_root, name)
        profile_checks: dict[str, Any] = {
            "missing_checkpoint_count": len(missing),
            "targets": {},
        }
        for target in profile.get("targets") or table_specs:
            if target not in production_tables or target not in tables:
                profile_checks["targets"][target] = {"status": "incomplete"}
                continue
            keys, values = table_specs[target]
            tolerance = float(
                payload["campaign"]["convergence_tolerances_absolute"][target]
            )
            profile_checks["targets"][target] = _compare_tables(
                production_tables[target], tables[target], keys, values, tolerance
            )
        profile_checks["status"] = (
            "passed"
            if profile_checks["missing_checkpoint_count"] == 0
            and profile_checks["targets"]
            and all(
                row["status"] == "passed" for row in profile_checks["targets"].values()
            )
            else "incomplete_or_failed"
        )
        checks[name] = profile_checks
    return {
        "schema_version": 2,
        "protocol": "paper-review-v2-convergence",
        "status": (
            "passed"
            if checks and all(row["status"] == "passed" for row in checks.values())
            else "incomplete_or_failed"
        ),
        "profiles": checks,
    }


def _alternative_scalar(
    probe: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, float]:
    solver = parameters["solver"]
    sites = int(parameters["phase_sweep"]["sites"])
    points_per_site = int(parameters["phase_sweep"]["grid_points_per_site"])
    vp = float(probe["vp"])
    vd = float(probe["vd"])
    factor = float(probe["depth_factor"])
    phi = float(probe["phi"])
    _, diagonal, off = continuum_tridiagonal(
        sites,
        points_per_site,
        vp * factor,
        vd * factor,
        float(parameters["alpha"]),
        phi,
    )
    matrix = diags((off, diagonal, off), (-1, 0, 1), format="csr")
    count = len(diagonal)
    eigenvalues, eigenvectors = eigsh(
        matrix,
        k=sites,
        which="SA",
        tol=float(solver["alternative_solver_tolerance"]),
        maxiter=int(solver["alternative_solver_maxiter"]),
        ncv=min(count - 1, max(2 * sites + 1, 40)),
    )
    order = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    basis = primary_basis(
        sites,
        points_per_site,
        vp * factor,
        float(parameters["alpha"]),
        int(solver["primary_bloch_harmonics"]),
        int(solver["primary_bloch_points"]),
    )
    overlap = eigenvectors.T @ basis.wannier
    cdw_density, imbalance_operator = prepare_cdw(overlap)
    center_density, center_operator, _ = prepare_center_third_eigenstates(
        sites=sites,
        points_per_site=points_per_site,
        vp=vp * factor,
        vd=vd * factor,
        alpha=float(parameters["alpha"]),
        phi=phi,
        final_eigenvectors=eigenvectors,
    )
    imbalance = dephased_expectation(imbalance_operator, cdw_density)
    center0 = spectral_expectation(
        eigenvalues, center_operator, center_density, 0.0, basis.hopping
    )
    center = dephased_expectation(center_operator, center_density)
    clear_basis_cache()
    return {
        "imbalance": imbalance,
        "edge_density": 1.0 - center / center0,
        "orthogonality_error": _orthogonality_error(eigenvectors),
    }


def run_crosschecks(payload: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    production = next(
        name
        for name, row in payload["campaign"]["profiles"].items()
        if row.get("role") == "production"
    )
    parameters, _ = parameters_for_profile(payload, production)
    completed, missing = _load_results(payload, workspace_root, production)
    thresholds = payload["campaign"]["crosschecks"]
    if missing:
        report = {
            "schema_version": 2,
            "protocol": "paper-review-v2-independent-crosschecks",
            "status": "incomplete",
            "distinct_methods": [],
            "normalization_check": {
                "method": "normalization_check",
                "status": "not_run",
                "missing_checkpoint_count": len(missing),
            },
            "alternative_implementation": {"status": "not_run", "probes": []},
            "reason": "Production checkpoints are incomplete; expensive cross-checks are not executed early.",
        }
        _atomic_json(
            _campaign_root(payload, workspace_root) / "checks" / "crosschecks.json",
            report,
        )
        return report
    max_orthogonality = max(
        (result["diagnostics"]["max_orthogonality_error"] for _, result in completed),
        default=math.inf,
    )
    min_projection = min(
        (result["diagnostics"]["min_projection_fraction"] for _, result in completed),
        default=-math.inf,
    )
    normalization = {
        "method": "normalization_check",
        "status": (
            "passed"
            if not missing
            and max_orthogonality <= float(thresholds["max_orthogonality_error"])
            and min_projection >= float(thresholds["min_projection_fraction"])
            else "incomplete_or_failed"
        ),
        "max_orthogonality_error": max_orthogonality,
        "min_projection_fraction": min_projection,
        "missing_checkpoint_count": len(missing),
    }
    alternative_rows = []
    for probe in thresholds["alternative_solver_probes"]:
        main = _simulate_paper_scalar(
            sites=int(parameters["phase_sweep"]["sites"]),
            points_per_site=int(parameters["phase_sweep"]["grid_points_per_site"]),
            vp=float(probe["vp"]) * float(probe["depth_factor"]),
            vd=float(probe["vd"]) * float(probe["depth_factor"]),
            alpha=float(parameters["alpha"]),
            phi=float(probe["phi"]),
            imbalance_time_tau=float(
                parameters["paper_times_tau"]["numerical_imbalance"]
            ),
            edge_time_tau=float(parameters["paper_times_tau"]["edge_density"]),
            phase_hopping=primary_hopping(
                float(probe["vp"]),
                int(parameters["solver"]["primary_bloch_harmonics"]),
                int(parameters["solver"]["primary_bloch_points"]),
            ),
            solver=parameters["solver"],
            dephased=True,
        )
        alternative = _alternative_scalar(probe, parameters)
        clear_basis_cache()
        delta_i = abs(main["imbalance"] - alternative["imbalance"])
        delta_d = abs(main["edge_density"] - alternative["edge_density"])
        alternative_rows.append(
            {
                "probe_id": probe["probe_id"],
                "method": "alternative_implementation",
                "main": {
                    "imbalance": main["imbalance"],
                    "edge_density": main["edge_density"],
                },
                "alternative_sparse_arpack": alternative,
                "absolute_difference": {"imbalance": delta_i, "edge_density": delta_d},
                "status": (
                    "passed"
                    if max(delta_i, delta_d)
                    <= float(thresholds["alternative_solver_tolerance_absolute"])
                    else "failed"
                ),
            }
        )
    alternative_status = (
        "passed"
        if alternative_rows
        and all(row["status"] == "passed" for row in alternative_rows)
        else "failed"
    )
    report = {
        "schema_version": 2,
        "protocol": "paper-review-v2-independent-crosschecks",
        "status": (
            "passed"
            if normalization["status"] == "passed" and alternative_status == "passed"
            else "incomplete_or_failed"
        ),
        "distinct_methods": ["normalization_check", "alternative_implementation"],
        "normalization_check": normalization,
        "alternative_implementation": {
            "status": alternative_status,
            "probes": alternative_rows,
        },
        "independence_note": "The alternative probe rebuilds the Hamiltonian as sparse CSR and uses ARPACK eigsh; preparation/observable definitions are shared and disclosed, so a fresh reviewer must still judge independence.",
    }
    _atomic_json(
        _campaign_root(payload, workspace_root) / "checks" / "crosschecks.json", report
    )
    return report


def _plot_tables(tables: dict[str, list[dict[str, Any]]], figures: Path) -> None:
    figures.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    for vd in sorted({row["vd_recoil"] for row in tables["T002"]}):
        rows = [row for row in tables["T002"] if row["vd_recoil"] == vd]
        ax.plot(
            [row["time_tau"] for row in rows],
            [row["edge_density_mean"] for row in rows],
            label=f"Vd={vd:g}",
        )
    ax.set(
        xlabel="time (tau)", ylabel="edge density", title="Paper-scale Fig. 2(b) theory"
    )
    ax.legend(frameon=False)
    fig.savefig(figures / "t002_fig2b_edge_density.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.8), constrained_layout=True)
    for ax, vp in zip(axes, (4.0, 6.0, 8.0)):
        for averaging, style in (("central", "--"), ("tube_proxy", "-")):
            rows = sorted(
                (
                    row
                    for row in tables["T003"]
                    if row["vp_recoil"] == vp and row["averaging"] == averaging
                ),
                key=lambda row: row["vd_recoil"],
            )
            ax.plot(
                [row["vd_recoil"] for row in rows],
                [row["imbalance"] for row in rows],
                style,
                color="#3366cc",
            )
            ax.plot(
                [row["vd_recoil"] for row in rows],
                [row["edge_density"] for row in rows],
                style,
                color="#d65f00",
            )
        ax.set(title=f"Vp={vp:g}", xlabel="Vd")
    axes[0].set_ylabel("I, D")
    fig.savefig(figures / "t003_fig3_theory_sweeps.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 4.4), constrained_layout=True)
    for averaging, style in (("central", "--"), ("tube_proxy", "-")):
        rows = sorted(
            (row for row in tables["T004"] if row["averaging"] == averaging),
            key=lambda row: row["vp_recoil"],
        )
        ax.plot(
            [row["vp_recoil"] for row in rows],
            [row["v_imbalance_recoil"] for row in rows],
            style,
            marker="o",
            color="#3366cc",
        )
        ax.plot(
            [row["vp_recoil"] for row in rows],
            [row["v_edge_recoil"] for row in rows],
            style,
            marker="s",
            color="#d65f00",
        )
    ax.set(xlabel="Vp", ylabel="Vd boundary", title="Paper-scale Fig. 4 theory")
    fig.savefig(figures / "t004_fig4_phase_boundaries.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(12.0, 6.6), constrained_layout=True)
    for row_index, trap in enumerate(
        sorted({row["trap_edge_recoil"] for row in tables["T005"]})
    ):
        for vd in sorted({row["vd_recoil"] for row in tables["T005"]}):
            rows = sorted(
                (
                    row
                    for row in tables["T005"]
                    if row["trap_edge_recoil"] == trap and row["vd_recoil"] == vd
                ),
                key=lambda row: row["time_tau"],
            )
            axes[row_index, 0].plot(
                [row["time_tau"] for row in rows], [row["fwhm_sites"] for row in rows]
            )
            axes[row_index, 1].plot(
                [row["time_tau"] for row in rows], [row["edge_density"] for row in rows]
            )
            axes[row_index, 2].plot(
                [row["time_tau"] for row in rows], [row["rms_sites"] for row in rows]
            )
    fig.savefig(figures / "t005_supp_s1_observables.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    for averaging, style in (("central", "--"), ("tube_proxy", "-")):
        rows = sorted(
            (row for row in tables["T006"] if row["averaging"] == averaging),
            key=lambda row: row["vd_recoil"],
        )
        ax.plot(
            [row["vd_recoil"] for row in rows],
            [row["imbalance_3000tau"] for row in rows],
            style,
            color="#3366cc",
        )
        ax.plot(
            [row["vd_recoil"] for row in rows],
            [row["edge_density_3000tau"] for row in rows],
            style,
            color="#d65f00",
        )
    ax.set(xlabel="Vd", ylabel="I, D", title="Paper-scale Supplement S2 theory")
    fig.savefig(figures / "t006_supp_s2_finite_time.png", dpi=180)
    plt.close(fig)


def aggregate_campaign(payload: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    root = _campaign_root(payload, workspace_root)
    production = next(
        name
        for name, row in payload["campaign"]["profiles"].items()
        if row.get("role") == "production"
    )
    tables, missing = _tables_for_profile(payload, workspace_root, production)
    protocol_path = root / "checks" / "protocol_v2_assessment.json"
    if missing or set(tables) != {"T002", "T003", "T004", "T005", "T006"}:
        result = {
            "schema_version": 2,
            "status": "incomplete",
            "paper_assessment": "inconclusive",
            "reason": "Production checkpoints are incomplete; no scientific adjudication is permitted.",
            "missing_checkpoint_count": len(missing),
            "targets_available": sorted(tables),
        }
        _atomic_json(protocol_path, result)
        return result

    data_root = _output_root(payload, workspace_root, "data")
    data_paths = {
        "T002": data_root / "t002_fig2b_edge_density.csv",
        "T003": data_root / "t003_fig3_theory_sweeps.csv",
        "T004": data_root / "t004_fig4_phase_boundaries.csv",
        "T005": data_root / "t005_supp_s1_observables.csv",
        "T006": data_root / "t006_supp_s2_finite_time.csv",
    }
    for target, path in data_paths.items():
        _write_csv(path, tables[target])
    acceptance = _acceptance(tables, payload)
    _atomic_json(root / "checks" / "acceptance.json", acceptance)
    convergence = convergence_report(payload, workspace_root, tables)
    _atomic_json(root / "checks" / "convergence.json", convergence)
    crosscheck_path = root / "checks" / "crosschecks.json"
    crosschecks = (
        json.loads(crosscheck_path.read_text(encoding="utf-8"))
        if crosscheck_path.is_file()
        else {"status": "not_run", "distinct_methods": []}
    )
    freeze = {
        "schema_version": 1,
        "status": "frozen_before_reference_comparison",
        "reference_assets_read": False,
        "data_files": [
            {"path": _display_path(path, workspace_root), "sha256": _sha256(path)}
            for path in data_paths.values()
        ],
    }
    _atomic_json(root / "checks" / "data_freeze.json", freeze)
    _plot_tables(tables, _output_root(payload, workspace_root, "figures"))

    if crosschecks.get("status") == "incomplete_or_failed":
        paper_assessment, reason = (
            "reproduction_defect",
            "A solver invariant or independent solver cross-check failed; attribute the mismatch to the reproduction until repaired.",
        )
    else:
        paper_assessment = "inconclusive"
        if (
            acceptance["status"] != "passed"
            and convergence["status"] == "passed"
            and crosschecks.get("status") == "passed"
        ):
            reason = "A stable discrepancy is retained, but no fresh protocol-v2 reviewer has falsified a precise paper claim and documented the gap."
        elif (
            acceptance["status"] == "passed"
            and convergence["status"] == "passed"
            and crosschecks.get("status") == "passed"
        ):
            reason = "Evidence is ready for a fresh protocol-v2 review; a reproducer cannot self-award paper_supported."
        else:
            reason = "Convergence and/or dual independent cross-check evidence is incomplete."
    candidate_requirements = {
        "frozen_independent_data": True,
        "convergence_passed": convergence["status"] == "passed",
        "two_distinct_crosscheck_methods_passed": crosschecks.get("status") == "passed"
        and len(set(crosschecks.get("distinct_methods", []))) >= 2,
        "strong_crosscheck_present": "alternative_implementation"
        in crosschecks.get("distinct_methods", []),
        "explicit_paper_claim_falsified": False,
        "complete_discrepancy_record": False,
        "fresh_context_review_passed": False,
    }
    result = {
        "schema_version": 2,
        "status": (
            "evidence_ready"
            if convergence["status"] == "passed"
            and crosschecks.get("status") == "passed"
            else "evidence_incomplete"
        ),
        "paper_assessment": paper_assessment,
        "reason": reason,
        "acceptance_status": acceptance["status"],
        "convergence_status": convergence["status"],
        "crosscheck_status": crosschecks.get("status"),
        "paper_error_candidate_requirements": candidate_requirements,
        "paper_error_candidate_eligible": all(candidate_requirements.values()),
        "reference_assets_read": False,
        "author_code_or_arrays_used": False,
    }
    _atomic_json(protocol_path, result)
    return result


def make_smoke_payload(
    payload: dict[str, Any], output_root: str | None = None
) -> dict[str, Any]:
    smoke = deepcopy(payload)
    smoke["status"] = "smoke"
    p = smoke["parameters"]
    phases = [0.0]
    p["main_trace"].update(
        {
            "sites": 15,
            "grid_points_per_site": 3,
            "phases_rad": phases,
            "time_tau": {"start": 0.0, "stop": 3.0, "points": 3},
        }
    )
    p["phase_sweep"].update(
        {"sites": 15, "grid_points_per_site": 3, "phases_rad": phases}
    )
    for row in p["phase_sweep"]["specs"]:
        row["points"] = 3
    nodes = deepcopy(p["phase_sweep"]["tube_nodes"][:2])
    total = sum(float(row["weight"]) for row in nodes)
    for row in nodes:
        row["weight"] = float(row["weight"]) / total
    p["phase_sweep"]["tube_nodes"] = nodes
    p["supplement_trace"].update(
        {
            "sites": 15,
            "grid_points_per_site": 3,
            "phases_rad": phases,
            "gaussian_fwhm_sites": 5.0,
            "time_tau": {"start": 0.0, "stop": 3.0, "points": 3},
        }
    )
    p["solver"].update(
        {
            "primary_bloch_harmonics": 5,
            "primary_bloch_points": 51,
            "alternative_solver_maxiter": 10000,
        }
    )
    production_name = next(
        name
        for name, row in smoke["campaign"]["profiles"].items()
        if row.get("role") == "production"
    )
    smoke["campaign"]["profiles"] = {
        production_name: {
            "role": "production",
            "targets": ["T002", "T003", "T004", "T005", "T006"],
            "overrides": {},
        }
    }
    if output_root:
        base = Path(output_root)
        smoke["campaign"]["output_roots"] = {
            "state": str(base / "state"),
            "data": str(base / "data"),
            "figures": str(base / "figures"),
        }
    else:
        smoke["campaign"]["output_roots"] = {
            "state": "outputs/checks/paper_scale_smoke",
            "data": "outputs/data/paper_scale_smoke",
            "figures": "outputs/figures/paper_scale_smoke",
        }
    validate_campaign_config(smoke)
    return smoke
