"""Paper-scale scientific runner primitives for arXiv:2605.25594.

The paper's numerical figures all descend from one expensive object: a full
single-particle eigensystem of the three-dimensional Anderson Hamiltonian.
This module makes that shared object explicit and derives bounded sufficient
statistics for every figure without retaining source images, digitized curves,
or author numerical arrays.

The production campaign is deliberately separated into deterministic work
units.  A work unit owns one ``(family, L, W, disorder realization)`` and may
serve several paper figures and perturbation operators.  Its JSON checkpoint
is enough to render the declared targets after aggregation; eigenvectors are
discarded after the statistics have been reduced.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from scipy import sparse

from anderson_sensitivity import (
    central_indices,
    inverse_participation_ratio,
    nearest_neighbor_pairs,
    spacing_stats,
    sublattice_next_neighbor_pairs,
)

ANDERSON_TARGET_IDS = (
    "T001",
    "T002",
    "T003",
    "T004",
    "T005",
    "T006",
    "T007",
    "T008",
    "T010",
    "T011",
    "T012",
    "T013",
    "T014",
    "T015",
    "T016",
    "T017",
    "T018",
    "T019",
    "T020",
    "T021",
    "T022",
    "T023",
    "T024",
)


@dataclass(frozen=True)
class WorkUnit:
    index: int
    family: str
    target_ids: tuple[str, ...]
    L: int
    W: float
    sample: int
    operators: tuple[str, ...]
    boundary_disorder: bool
    full_spectrum_spacing: bool
    collect_spectral: bool
    collect_distribution: bool
    collect_perturbation: bool

    @property
    def key(self) -> str:
        disorder = f"{self.W:.8g}".replace("-", "m").replace(".", "p")
        return f"{self.family}_L{self.L:02d}_W{disorder}_s{self.sample:03d}"


def canonical_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _samples_for_size(family: dict[str, Any], L: int) -> int:
    if "sample_count" in family:
        return int(family["sample_count"])
    policy = family.get("samples_by_size")
    if not isinstance(policy, dict):
        raise ValueError(f"{family.get('family_id')}: no sample-count policy")
    threshold = int(policy["threshold_L"])
    return int(policy["at_or_below"] if L <= threshold else policy["above"])


def _disorder_values(family: dict[str, Any], L: int) -> list[float]:
    if "w_values" in family:
        values = [float(value) for value in family["w_values"]]
    elif "w_sqrt_v_values" in family:
        values = [float(value) / math.sqrt(L**3) for value in family["w_sqrt_v_values"]]
    else:
        raise ValueError(f"{family.get('family_id')}: no disorder grid")
    if not values or len(set(values)) != len(values):
        raise ValueError(f"{family.get('family_id')}: empty or duplicate disorder grid")
    return values


def build_work_units(config: dict[str, Any]) -> list[WorkUnit]:
    """Expand the immutable campaign config into deterministic work units."""

    families = config.get("families")
    if not isinstance(families, list) or not families:
        raise ValueError("paper-scale config requires a non-empty families list")
    units: list[WorkUnit] = []
    seen_family_ids: set[str] = set()
    covered_targets: set[str] = set()
    for family in families:
        family_id = str(family["family_id"])
        if family_id in seen_family_ids:
            raise ValueError(f"duplicate family_id: {family_id}")
        seen_family_ids.add(family_id)
        target_ids = tuple(str(value) for value in family["target_ids"])
        unknown = sorted(set(target_ids) - set(ANDERSON_TARGET_IDS))
        if unknown:
            raise ValueError(f"{family_id}: unknown target ids {unknown}")
        covered_targets.update(target_ids)
        operators = tuple(str(value) for value in family.get("operators", []))
        if not operators and not bool(family.get("full_spectrum_spacing")):
            raise ValueError(f"{family_id}: no operator or spacing observable")
        if set(operators) - {"T_s", "T", "n"}:
            raise ValueError(f"{family_id}: unsupported operator set {operators}")
        for L in [int(value) for value in family["sizes"]]:
            if L < 2:
                raise ValueError(f"{family_id}: invalid L={L}")
            sample_count = _samples_for_size(family, L)
            if sample_count <= 0:
                raise ValueError(f"{family_id}: invalid sample count")
            for W in _disorder_values(family, L):
                for sample in range(sample_count):
                    units.append(
                        WorkUnit(
                            index=len(units),
                            family=family_id,
                            target_ids=target_ids,
                            L=L,
                            W=W,
                            sample=sample,
                            operators=operators,
                            boundary_disorder=bool(
                                family.get("boundary_disorder", False)
                            ),
                            full_spectrum_spacing=bool(
                                family.get("full_spectrum_spacing", False)
                            ),
                            collect_spectral=bool(
                                family.get("collect_spectral", False)
                            ),
                            collect_distribution=bool(
                                family.get("collect_distribution", False)
                            ),
                            collect_perturbation=bool(
                                family.get("collect_perturbation", False)
                            ),
                        )
                    )
    missing = sorted(set(ANDERSON_TARGET_IDS) - covered_targets)
    if missing:
        raise ValueError(f"paper-scale campaign does not cover targets {missing}")
    return units


def describe_campaign(config: dict[str, Any]) -> dict[str, Any]:
    units = build_work_units(config)
    return {
        "paper_id": config["paper_id"],
        "work_unit_count": len(units),
        "family_count": len({unit.family for unit in units}),
        "target_ids": list(ANDERSON_TARGET_IDS),
        "size_values": sorted({unit.L for unit in units}),
        "operator_values": sorted({name for unit in units for name in unit.operators}),
        "full_eigensystems": len(units),
        "checkpoint_resume": True,
        "generated_data_provenance": "independent_numerics",
        "paper_pdf_or_tex_read_by_runner": False,
        "author_code_or_arrays_read_by_runner": False,
        "reference_pixels_read_by_runner": False,
    }


def work_unit_seed(seed_base: int, unit: WorkUnit) -> int:
    """Stable stream assignment independent of worker/shard scheduling."""

    material = f"{seed_base}:{unit.key}".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") % (2**63 - 1)


def anderson_hamiltonian_sparse(
    L: int,
    W: float,
    rng: np.random.Generator,
    *,
    boundary_disorder: bool,
    boundary_disorder_halfwidth: float,
) -> sparse.csr_matrix:
    size = L**3
    pairs = nearest_neighbor_pairs(L)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for i, j in pairs:
        rows.extend((i, j))
        cols.extend((j, i))
        data.extend((-1.0, -1.0))
    onsite = rng.uniform(-W / 2.0, W / 2.0, size=size)
    if boundary_disorder:
        # The paper applies this term only to calculations involving T_s.
        from anderson_sensitivity import is_boundary

        edge_noise = rng.uniform(
            -boundary_disorder_halfwidth, boundary_disorder_halfwidth, size=size
        )
        onsite += np.asarray(
            [
                edge_noise[index] if is_boundary(index, L) else 0.0
                for index in range(size)
            ]
        )
    rows.extend(range(size))
    cols.extend(range(size))
    data.extend(float(value) for value in onsite)
    return sparse.csr_matrix((data, (rows, cols)), shape=(size, size))


def randomized_site_values(L: int, largest_L: int, seed: int) -> np.ndarray:
    """One frozen largest-lattice configuration, cropped for smaller cubes.

    The paper states that one random ``r_i`` configuration generated for the
    largest size is reused in every calculation, but it does not publish the
    configuration or the smaller-size indexing rule.  Cropping the same cubic
    field is therefore an explicit reconstruction, not a paper-exact hidden
    parameter.
    """

    if L > largest_L:
        raise ValueError("L cannot exceed the frozen randomized-operator lattice")
    rng = np.random.default_rng(seed)
    field = rng.random((largest_L, largest_L, largest_L))
    values = field[:L, :L, :L].reshape(-1)
    return values - float(np.mean(values))


def operator_matrix(
    name: str, L: int, largest_L: int, operator_seed: int
) -> sparse.csr_matrix:
    size = L**3
    if name == "T":
        pairs = nearest_neighbor_pairs(L)
        rows = [index for i, j in pairs for index in (i, j)]
        cols = [index for i, j in pairs for index in (j, i)]
        return sparse.csr_matrix(
            (np.full(len(rows), -1.0), (rows, cols)), shape=(size, size)
        )
    if name == "T_s":
        pairs = sublattice_next_neighbor_pairs(L)
        rows = [index for i, j, _ in pairs for index in (i, j)]
        cols = [index for i, j, _ in pairs for index in (j, i)]
        data = [value for _, _, value in pairs for value in (value, value)]
        return sparse.csr_matrix((data, (rows, cols)), shape=(size, size))
    if name == "n":
        return sparse.diags(
            randomized_site_values(L, largest_L, operator_seed), format="csr"
        )
    raise ValueError(f"unsupported operator: {name}")


def full_spacing_payload(
    eigenvalues: np.ndarray, zero_frequency_tolerance: float
) -> dict[str, float]:
    gaps = np.diff(eigenvalues)
    gaps = gaps[gaps > zero_frequency_tolerance]
    ratios = np.minimum(gaps[1:], gaps[:-1]) / np.maximum(gaps[1:], gaps[:-1])
    return {
        "omega_average": float(np.mean(gaps)),
        "omega_typical": float(np.exp(np.mean(np.log(gaps)))),
        "gap_ratio_average": float(np.mean(ratios)),
        "level_count": int(len(eigenvalues)),
    }


def localized_perturbation_payload(
    L: int,
    W: float,
    mu_values: Iterable[float],
    operator_name: str,
    *,
    disorder_seed: int,
    largest_L: int,
    operator_seed: int,
) -> dict[str, Any]:
    """Zeroth/lowest-order localized baselines printed below Main Fig. 10.

    These baselines are generated from the printed disorder law and operator
    definitions.  They do not use a fitted ordinate from the paper.
    """

    rng = np.random.default_rng(disorder_seed)
    onsite = rng.uniform(-W / 2.0, W / 2.0, size=L**3)
    random_site = randomized_site_values(L, largest_L, operator_seed)
    if operator_name == "T_s":
        pairs = [
            (i, j, weight * weight)
            for i, j, weight in sublattice_next_neighbor_pairs(L)
        ]
    elif operator_name == "n":
        pairs = [
            (i, j, float((random_site[i] - random_site[j]) ** 2))
            for i, j in nearest_neighbor_pairs(L)
        ]
    else:
        raise ValueError(
            "localized perturbation baseline is defined only for T_s and n"
        )

    output: dict[str, Any] = {}
    for mu in mu_values:
        state_values = np.zeros(L**3, dtype=float)
        for i, j, numerator in pairs:
            difference = float(onsite[i] - onsite[j])
            if operator_name == "T_s":
                contribution = (
                    numerator * (difference / (difference * difference + mu * mu)) ** 2
                )
            else:
                contribution = numerator / (difference * difference + mu * mu) ** 2
            state_values[i] += contribution
            state_values[j] += contribution
        output[f"{mu:.16g}"] = {
            "chi_typ_r": float(np.exp(np.mean(np.log(state_values + 1e-300)))),
            "chi_average_r": float(np.mean(state_values)),
        }
    return output


def _mu_values(config: dict[str, Any], eigenvalues: np.ndarray) -> list[float]:
    indices = central_indices(eigenvalues, float(config["central_fraction"]))
    omega_average = spacing_stats(eigenvalues, indices)["omega_av"]
    values = [float(value) for value in config["mu_values"]]
    values.append(2.0 * math.log(len(eigenvalues)) * omega_average)
    return sorted(set(values))


def operator_statistics(
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    operator: sparse.csr_matrix,
    config: dict[str, Any],
    *,
    collect_spectral: bool,
    collect_distribution: bool,
) -> dict[str, Any]:
    """Reduce one operator/eigensystem pair to figure-sufficient statistics."""

    indices = central_indices(eigenvalues, float(config["central_fraction"]))
    mu_values = _mu_values(config, eigenvalues)
    transformed_all = operator @ eigenvectors
    block_size = int(config["selected_state_block_size"])
    chi_unregularized: list[np.ndarray] = []
    chi_regularized: dict[float, list[np.ndarray]] = {mu: [] for mu in mu_values}
    spectral_edges = np.asarray(config["spectral_bin_edges"], dtype=float)
    spectral_weight = np.zeros(len(spectral_edges) - 1, dtype=float)
    spectral_count = np.zeros(len(spectral_edges) - 1, dtype=np.int64)

    for start in range(0, len(indices), block_size):
        selected = indices[start : start + block_size]
        matrix = eigenvectors[:, selected].T @ transformed_all
        abs_o2 = np.abs(matrix) ** 2
        omega = eigenvalues[selected, None] - eigenvalues[None, :]
        mask = np.abs(omega) > float(config["zero_frequency_tolerance"])
        kernel = np.zeros_like(omega)
        kernel[mask] = 1.0 / omega[mask] ** 2
        chi_unregularized.append(np.sum(kernel * abs_o2, axis=1))
        for mu in mu_values:
            regularized = omega**2 / (omega**2 + mu**2) ** 2
            chi_regularized[mu].append(np.sum(regularized * abs_o2, axis=1))
        if collect_spectral:
            absolute_omega = np.abs(omega[mask])
            weights, _ = np.histogram(
                absolute_omega, bins=spectral_edges, weights=abs_o2[mask]
            )
            counts, _ = np.histogram(absolute_omega, bins=spectral_edges)
            spectral_weight += weights
            spectral_count += counts

    del transformed_all
    chi = np.concatenate(chi_unregularized)
    local_spacing = spacing_stats(eigenvalues, indices)
    susceptibility: dict[str, Any] = {
        "unregularized": {
            "chi_typ": float(np.exp(np.mean(np.log(chi + 1e-300)))),
            "chi_average": float(np.mean(chi)),
            "tilde_chi_typ": float(
                local_spacing["omega_typ"] * np.exp(np.mean(np.log(chi + 1e-300))),
            ),
        },
        "regularized": {},
    }
    for mu, chunks in chi_regularized.items():
        values = np.concatenate(chunks)
        typical = float(np.exp(np.mean(np.log(values + 1e-300))))
        average = float(np.mean(values))
        susceptibility["regularized"][f"{mu:.16g}"] = {
            "chi_typ_r": typical,
            "chi_average_r": average,
            "tilde_chi_typ_r": float(mu * typical),
            "tilde_chi_average_r": float(mu * average),
            "average_over_typical": float(average / typical),
        }

    payload: dict[str, Any] = {
        "selected_state_count": int(len(indices)),
        "spacing": local_spacing,
        "susceptibility": susceptibility,
    }
    if collect_spectral:
        means = np.divide(
            len(eigenvalues) * spectral_weight,
            spectral_count,
            out=np.full_like(spectral_weight, np.nan),
            where=spectral_count > 0,
        )
        payload["spectral"] = {
            "bin_edges": spectral_edges.tolist(),
            "mean_weight": [
                None if not np.isfinite(value) else float(value) for value in means
            ],
            "counts": spectral_count.tolist(),
        }
    if collect_distribution:
        log_edges = np.asarray(config["log10_chi_bin_edges"], dtype=float)
        counts, _ = np.histogram(np.log10(chi + 1e-300), bins=log_edges)
        payload["chi_distribution"] = {
            "log10_bin_edges": log_edges.tolist(),
            "counts": counts.tolist(),
            "underflow": int(np.count_nonzero(np.log10(chi + 1e-300) < log_edges[0])),
            "overflow": int(np.count_nonzero(np.log10(chi + 1e-300) >= log_edges[-1])),
        }
    return payload


def run_unit_numerics(
    unit: WorkUnit,
    config: dict[str, Any],
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
) -> dict[str, Any]:
    """Derive every requested observable after an eigensystem is generated."""

    result: dict[str, Any] = {
        "central_ipr": inverse_participation_ratio(
            eigenvectors,
            central_indices(eigenvalues, float(config["central_fraction"])),
        ),
        "operators": {},
    }
    if unit.full_spectrum_spacing:
        result["full_spectrum_spacing"] = full_spacing_payload(
            eigenvalues, float(config["zero_frequency_tolerance"])
        )
    for name in unit.operators:
        result["operators"][name] = operator_statistics(
            eigenvalues,
            eigenvectors,
            operator_matrix(
                name, unit.L, int(config["largest_L"]), int(config["operator_seed"])
            ),
            config,
            collect_spectral=unit.collect_spectral,
            collect_distribution=unit.collect_distribution and name == "T_s",
        )
        if unit.collect_perturbation and name in {"T_s", "n"}:
            result["operators"][name]["localized_perturbation"] = (
                localized_perturbation_payload(
                    unit.L,
                    unit.W,
                    _mu_values(config, eigenvalues),
                    name,
                    disorder_seed=work_unit_seed(int(config["seed_base"]) + 97, unit),
                    largest_L=int(config["largest_L"]),
                    operator_seed=int(config["operator_seed"]),
                )
            )
    return result


def aggregate_target_index(
    records: Iterable[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any]:
    """Fail closed on missing work units and index immutable target inputs."""

    rows = list(records)
    by_key = {str(row["work_unit_key"]): row for row in rows}
    expected = build_work_units(config)
    missing = [unit.key for unit in expected if unit.key not in by_key]
    duplicate_count = len(rows) - len(by_key)
    target_records: dict[str, list[str]] = {
        target_id: [] for target_id in ANDERSON_TARGET_IDS
    }
    for unit in expected:
        if unit.key not in by_key:
            continue
        for target_id in unit.target_ids:
            target_records[target_id].append(unit.key)
    return {
        "status": "passed" if not missing and duplicate_count == 0 else "incomplete",
        "expected_work_units": len(expected),
        "completed_work_units": len(by_key),
        "duplicate_work_units": duplicate_count,
        "missing_work_units": missing,
        "target_records": target_records,
        "all_targets_have_data": all(target_records.values()),
    }
