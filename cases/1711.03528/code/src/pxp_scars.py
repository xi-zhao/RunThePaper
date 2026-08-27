from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.linalg
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass(frozen=True)
class PXPBasis:
    L: int
    periodic: bool
    states: list[int]
    index: dict[int, int]


def fibonacci(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def bit(state: int, site: int) -> int:
    return (state >> site) & 1


def is_allowed_state(state: int, L: int, periodic: bool) -> bool:
    for site in range(L - 1):
        if bit(state, site) and bit(state, site + 1):
            return False
    return not (periodic and L > 1 and bit(state, 0) and bit(state, L - 1))


def build_basis(L: int, periodic: bool = True) -> PXPBasis:
    states = [state for state in range(1 << L) if is_allowed_state(state, L, periodic)]
    return PXPBasis(L=L, periodic=periodic, states=states, index={state: i for i, state in enumerate(states)})


def valid_flip(state: int, L: int, site: int, periodic: bool) -> bool:
    left = (site - 1) % L
    right = (site + 1) % L
    left_ok = True if (not periodic and site == 0) else bit(state, left) == 0
    right_ok = True if (not periodic and site == L - 1) else bit(state, right) == 0
    return left_ok and right_ok


def build_hamiltonian(basis: PXPBasis) -> sp.csr_matrix:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for col, state in enumerate(basis.states):
        for site in range(basis.L):
            if not valid_flip(state, basis.L, site, basis.periodic):
                continue
            target = state ^ (1 << site)
            row = basis.index.get(target)
            if row is None:
                continue
            rows.append(row)
            cols.append(col)
            data.append(1.0)
    dim = len(basis.states)
    return sp.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=float)


def pattern_state(L: int, name: str) -> int:
    if name == "vacuum":
        return 0
    if name == "z2":
        return sum(1 << site for site in range(0, L, 2))
    if name == "z2_shift":
        return sum(1 << site for site in range(1, L, 2))
    if name == "z3":
        return periodic_density_wave_state(L, 3)
    if name == "z4":
        return periodic_density_wave_state(L, 4)
    raise ValueError(f"unknown pattern: {name}")


def periodic_density_wave_state(L: int, period: int) -> int:
    for shift in range(period):
        state = sum(1 << site for site in range(shift, L, period))
        if is_allowed_state(state, L, periodic=True):
            return state
    raise ValueError(f"no legal period-{period} density wave for L={L}")


def basis_vector(basis: PXPBasis, state: int) -> np.ndarray:
    vec = np.zeros(len(basis.states), dtype=complex)
    vec[basis.index[state]] = 1.0
    return vec


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def parity_values(basis: PXPBasis) -> np.ndarray:
    return np.array([(-1) ** (basis.L - state.bit_count()) for state in basis.states], dtype=float)


def nearest_neighbor_zz_values(basis: PXPBasis) -> np.ndarray:
    values = []
    for state in basis.states:
        corr = 0.0
        bonds = basis.L if basis.periodic else basis.L - 1
        for site in range(bonds):
            left = site
            right = (site + 1) % basis.L
            z_left = 1.0 if bit(state, left) else -1.0
            z_right = 1.0 if bit(state, right) else -1.0
            corr += z_left * z_right
        values.append(corr / bonds)
    return np.array(values)


def expectation_diag(psi: np.ndarray, values: np.ndarray) -> float:
    probabilities = np.abs(psi) ** 2
    return float(np.real(np.dot(probabilities, values)))


def entanglement_entropy(psi: np.ndarray, basis: PXPBasis, cut: int | None = None) -> float:
    cut = cut or basis.L // 2
    full = np.zeros(1 << basis.L, dtype=complex)
    for amp, state in zip(psi, basis.states):
        full[state] = amp
    matrix = full.reshape((1 << cut, 1 << (basis.L - cut)))
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    probabilities = np.abs(singular_values) ** 2
    probabilities = probabilities[probabilities > 1e-14]
    return float(-np.sum(probabilities * np.log(probabilities)))


def build_hplus(basis: PXPBasis, reference_state: int) -> sp.csr_matrix:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for col, state in enumerate(basis.states):
        distance = hamming_distance(state, reference_state)
        for site in range(basis.L):
            if not valid_flip(state, basis.L, site, basis.periodic):
                continue
            target = state ^ (1 << site)
            if hamming_distance(target, reference_state) != distance + 1:
                continue
            row = basis.index.get(target)
            if row is None:
                continue
            rows.append(row)
            cols.append(col)
            data.append(1.0)
    dim = len(basis.states)
    return sp.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=float)


def fsa_basis_and_matrix(basis: PXPBasis, hamiltonian: sp.csr_matrix, reference_state: int) -> dict:
    hplus = build_hplus(basis, reference_state)
    hminus = hplus.transpose().tocsr()
    vectors: list[np.ndarray] = [basis_vector(basis, reference_state).real]
    betas: list[float] = []
    backward_errors: list[float] = []

    for _ in range(basis.L):
        proposal = hplus @ vectors[-1]
        beta = float(np.linalg.norm(proposal))
        if beta < 1e-12:
            break
        next_vec = np.asarray(proposal / beta).reshape(-1)
        back = hminus @ next_vec
        backward_error = float(np.linalg.norm(back - beta * vectors[-1]) / max(beta, 1e-12))
        vectors.append(next_vec)
        betas.append(beta)
        backward_errors.append(backward_error)

    matrix = np.zeros((len(vectors), len(vectors)), dtype=float)
    for i, beta in enumerate(betas):
        matrix[i, i + 1] = beta
        matrix[i + 1, i] = beta
    projected = np.vstack(vectors) @ (hamiltonian @ np.vstack(vectors).T)
    return {
        "vectors": np.vstack(vectors),
        "betas": np.array(betas),
        "backward_errors": np.array(backward_errors),
        "matrix": matrix,
        "projected_matrix": np.asarray(projected),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_fig1_graph_data(workspace: Path) -> dict:
    basis = build_basis(6, periodic=True)
    hamiltonian = build_hamiltonian(basis)
    z2 = pattern_state(6, "z2")
    nodes = []
    grouped: dict[int, list[int]] = {}
    for state in basis.states:
        grouped.setdefault(hamming_distance(state, z2), []).append(state)
    for distance, states in grouped.items():
        for offset, state in enumerate(sorted(states)):
            nodes.append(
                {
                    "state": format(state, f"0{basis.L}b"),
                    "integer_state": state,
                    "hamming_distance_from_z2": distance,
                    "x": distance,
                    "y": offset - (len(states) - 1) / 2,
                }
            )

    edges = []
    coo = sp.triu(hamiltonian, k=1).tocoo()
    for row, col in zip(coo.row, coo.col):
        edges.append(
            {
                "source": format(basis.states[col], f"0{basis.L}b"),
                "target": format(basis.states[row], f"0{basis.L}b"),
            }
        )

    write_csv(workspace / "outputs" / "data" / "fig1_graph_nodes.csv", nodes)
    write_csv(workspace / "outputs" / "data" / "fig1_graph_edges.csv", edges)
    return {"nodes": len(nodes), "edges": len(edges), "expected_nodes": fibonacci(5) + fibonacci(7)}


def diagonalize_dense(hamiltonian: sp.csr_matrix) -> tuple[np.ndarray, np.ndarray]:
    return scipy.linalg.eigh(hamiltonian.toarray(), check_finite=False)


def make_dynamics_data(workspace: Path, L: int = 16) -> dict:
    basis = build_basis(L, periodic=True)
    hamiltonian = build_hamiltonian(basis)
    zz_values = nearest_neighbor_zz_values(basis)
    times = np.linspace(0.0, 12.0, 73)
    rows: list[dict] = []
    summary: dict[str, dict] = {}

    for name in ["z2", "z3", "z4", "vacuum"]:
        state = pattern_state(L, name)
        psi0 = basis_vector(basis, state)
        evolved = spla.expm_multiply((-1j) * hamiltonian, psi0, start=times[0], stop=times[-1], num=len(times), endpoint=True)
        entropies = []
        correlations = []
        fidelities = []
        for time, psi in zip(times, evolved):
            entropy = entanglement_entropy(psi, basis)
            correlation = expectation_diag(psi, zz_values)
            fidelity = float(abs(np.vdot(psi0, psi)) ** 2)
            entropies.append(entropy)
            correlations.append(correlation)
            fidelities.append(fidelity)
            rows.append(
                {
                    "initial_state": name,
                    "L": L,
                    "time": time,
                    "entanglement_entropy": entropy,
                    "nearest_neighbor_zz": correlation,
                    "return_probability": fidelity,
                }
            )
        fidelities_array = np.array(fidelities)
        slope = float(np.polyfit(times[:25], entropies[:25], 1)[0])
        peak_times = local_peak_times(times, correlations, min_time=1.0)
        periods = np.diff(peak_times) if len(peak_times) >= 3 else np.array([])
        summary[name] = {
            "entropy_slope_early_time": slope,
            "max_return_after_t1": float(np.max(fidelities_array[times > 1.0])),
            "correlation_peak_times": peak_times.tolist(),
            "correlation_period_mean": float(np.mean(periods)) if len(periods) else None,
        }

    write_csv(workspace / "outputs" / "data" / "fig_ent_dynamics.csv", rows)
    return {"L": L, "times": len(times), "summary": summary}


def local_peak_times(times: np.ndarray, values: list[float], min_time: float) -> np.ndarray:
    arr = np.array(values)
    peaks = []
    for i in range(1, len(arr) - 1):
        if times[i] < min_time:
            continue
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            peaks.append(times[i])
    return np.array(peaks)


def make_special_state_data(workspace: Path, L: int = 16) -> dict:
    basis = build_basis(L, periodic=True)
    hamiltonian = build_hamiltonian(basis)
    energies, eigenvectors = diagonalize_dense(hamiltonian)
    z2_state = pattern_state(L, "z2")
    z2_index = basis.index[z2_state]
    z2_overlaps = np.abs(eigenvectors[z2_index, :]) ** 2
    fsa = fsa_basis_and_matrix(basis, hamiltonian, z2_state)
    fsa_energies, fsa_vectors = scipy.linalg.eigh(fsa["matrix"], check_finite=False)

    scatter_rows = []
    for i, (energy, overlap) in enumerate(zip(energies, z2_overlaps)):
        scatter_rows.append({"eigen_index": i, "L": L, "energy": energy, "z2_overlap": overlap})
    for i, energy in enumerate(fsa_energies):
        scatter_rows.append({"eigen_index": f"fsa_{i}", "L": L, "energy": energy, "z2_overlap": float(abs(fsa_vectors[0, i]) ** 2)})
    write_csv(workspace / "outputs" / "data" / "fig2a_scar_overlaps.csv", scatter_rows)

    selected = select_special_indices(energies, z2_overlaps, fsa_energies)
    basis_overlap_rows = []
    for label, exact_index, fsa_index in selected:
        exact_state = eigenvectors[:, exact_index]
        exact_coeffs = fsa["vectors"] @ exact_state
        fsa_coeffs = fsa_vectors[:, fsa_index]
        for n in range(len(fsa_coeffs)):
            basis_overlap_rows.append(
                {
                    "panel": label,
                    "n": n,
                    "exact_energy": energies[exact_index],
                    "fsa_energy": fsa_energies[fsa_index],
                    "exact_projection": float(abs(exact_coeffs[n]) ** 2),
                    "fsa_projection": float(abs(fsa_coeffs[n]) ** 2),
                }
            )
    write_csv(workspace / "outputs" / "data" / "fig2bc_fsa_basis_overlaps.csv", basis_overlap_rows)

    pr_rows = []
    for L_pr in [10, 12, 14, 16]:
        pr_basis = build_basis(L_pr, periodic=True)
        pr_h = build_hamiltonian(pr_basis)
        pr_energies, pr_vectors = diagonalize_dense(pr_h)
        pr_z2 = pattern_state(L_pr, "z2")
        pr_overlaps = np.abs(pr_vectors[pr_basis.index[pr_z2], :]) ** 2
        pr2 = np.sum(np.abs(pr_vectors) ** 4, axis=0)
        middle = np.abs(pr_energies) < np.quantile(np.abs(pr_energies), 0.67)
        special_count = min(L_pr + 1, len(pr_overlaps))
        special_indices = np.argsort(pr_overlaps)[-special_count:]
        pr_rows.append(
            {
                "L": L_pr,
                "dimension": len(pr_basis.states),
                "average_pr2_middle": float(np.mean(pr2[middle])),
                "special_pr2_average": float(np.mean(pr2[special_indices])),
                "inverse_dimension": 1.0 / len(pr_basis.states),
                "special_to_average_ratio": float(np.mean(pr2[special_indices]) / np.mean(pr2[middle])),
            }
        )
    write_csv(workspace / "outputs" / "data" / "fig2d_participation_ratio.csv", pr_rows)

    high_overlap_indices = np.argsort(z2_overlaps)[-(L + 1) :]
    high_overlap_energies = np.sort(energies[high_overlap_indices])
    central = high_overlap_energies[np.abs(high_overlap_energies) < np.quantile(np.abs(high_overlap_energies), 0.7)]
    spacings = np.diff(central) if len(central) >= 3 else np.diff(high_overlap_energies)
    spacing_mean = float(np.mean(np.abs(spacings))) if len(spacings) else None
    return {
        "L": L,
        "dimension": len(basis.states),
        "max_z2_overlap": float(np.max(z2_overlaps)),
        "median_z2_overlap": float(np.median(z2_overlaps)),
        "scar_overlap_ratio": float(np.max(z2_overlaps) / max(np.median(z2_overlaps), 1e-15)),
        "fsa_dimension": int(fsa["matrix"].shape[0]),
        "fsa_max_backward_error": float(np.max(fsa["backward_errors"])) if len(fsa["backward_errors"]) else 0.0,
        "central_scar_spacing_mean": spacing_mean,
        "selected_panels": [item[0] for item in selected],
    }


def select_special_indices(energies: np.ndarray, overlaps: np.ndarray, fsa_energies: np.ndarray) -> list[tuple[str, int, int]]:
    ground_index = int(np.argmin(energies))
    near_zero_candidates = np.argsort(np.abs(energies))[: max(20, len(energies) // 30)]
    near_zero_index = int(near_zero_candidates[np.argmax(overlaps[near_zero_candidates])])
    ground_fsa = int(np.argmin(np.abs(fsa_energies - energies[ground_index])))
    near_zero_fsa = int(np.argmin(np.abs(fsa_energies - energies[near_zero_index])))
    return [
        ("ground_state", ground_index, ground_fsa),
        ("near_zero_scar", near_zero_index, near_zero_fsa),
    ]


def make_level_statistics_data(workspace: Path, sizes: list[int] | None = None) -> dict:
    sizes = sizes or [12, 14, 16]
    rows = []
    density_rows = []
    summaries = []
    for L in sizes:
        basis = build_basis(L, periodic=True)
        hamiltonian = build_hamiltonian(basis)
        energies = np.sort(scipy.linalg.eigvalsh(hamiltonian.toarray(), check_finite=False))
        energies = energies[np.abs(energies) > 1e-8]
        lo, hi = np.quantile(energies, [0.2, 0.8])
        bulk = energies[(energies >= lo) & (energies <= hi)]
        spacings = np.diff(bulk)
        spacings = spacings[spacings > 1e-8]
        ratios = np.minimum(spacings[:-1], spacings[1:]) / np.maximum(spacings[:-1], spacings[1:])
        r_mean = float(np.mean(ratios)) if len(ratios) else 0.0
        hist, edges = np.histogram(spacings / np.mean(spacings), bins=35, range=(0, 4), density=True)
        for value, left, right in zip(hist, edges[:-1], edges[1:]):
            center = 0.5 * (left + right)
            rows.append({"L": L, "s_over_mean": center, "probability_density": value})
        dens, dens_edges = np.histogram(energies, bins=60, density=True)
        for value, left, right in zip(dens, dens_edges[:-1], dens_edges[1:]):
            density_rows.append({"L": L, "energy": 0.5 * (left + right), "density": value})
        summaries.append({"L": L, "dimension": len(basis.states), "r_mean": r_mean, "bulk_levels": len(bulk)})

    write_csv(workspace / "outputs" / "data" / "fig4_level_spacing_distribution.csv", rows)
    write_csv(workspace / "outputs" / "data" / "fig4_density_of_states.csv", density_rows)
    return {"sizes": summaries}


def make_formula_checks(workspace: Path) -> dict:
    dimension_checks = []
    max_anticommutator = 0.0
    for L in range(4, 13):
        pbc_basis = build_basis(L, periodic=True)
        obc_basis = build_basis(L, periodic=False)
        dimension_checks.append(
            {
                "L": L,
                "pbc_dimension": len(pbc_basis.states),
                "pbc_expected": fibonacci(L - 1) + fibonacci(L + 1),
                "obc_dimension": len(obc_basis.states),
                "obc_expected": fibonacci(L + 2),
            }
        )
        hamiltonian = build_hamiltonian(pbc_basis)
        parity = sp.diags(parity_values(pbc_basis))
        anti = parity @ hamiltonian + hamiltonian @ parity
        if anti.nnz:
            max_anticommutator = max(max_anticommutator, float(np.max(np.abs(anti.data))))

    basis = build_basis(12, periodic=True)
    hamiltonian = build_hamiltonian(basis)
    z2 = pattern_state(12, "z2")
    hplus = build_hplus(basis, z2)
    hminus = hplus.transpose().tocsr()
    hpm_error = float(sp.linalg.norm(hamiltonian - hplus - hminus))
    fsa = fsa_basis_and_matrix(basis, hamiltonian, z2)
    fsa_offdiag_error = float(np.linalg.norm(fsa["projected_matrix"] - fsa["matrix"]))
    dimensions_passed = all(
        item["pbc_dimension"] == item["pbc_expected"] and item["obc_dimension"] == item["obc_expected"]
        for item in dimension_checks
    )
    payload = {
        "status": "passed" if dimensions_passed and max_anticommutator < 1e-12 and hpm_error < 1e-12 else "failed",
        "numeric_closed": [],
        "paper_equations_checked": ["Eq.(1) PXP Hamiltonian", "Eq.(2) Z2 product states", "Eq.(3-5) FSA H+/H- and beta_n"],
        "dimension_checks": dimension_checks,
        "particle_hole_anticommutator_max_abs": max_anticommutator,
        "h_equals_hplus_plus_hminus_frobenius_error": hpm_error,
        "fsa_projected_minus_tridiagonal_norm_L12": fsa_offdiag_error,
        "fsa_max_backward_error_L12": float(np.max(fsa["backward_errors"])),
    }
    write_json(workspace / "outputs" / "checks" / "formula_verification.json", payload)
    return payload


def run_case(workspace: Path) -> None:
    data_dir = workspace / "outputs" / "data"
    checks_dir = workspace / "outputs" / "checks"
    data_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    formula = make_formula_checks(workspace)
    fig1 = make_fig1_graph_data(workspace)
    dynamics = make_dynamics_data(workspace, L=16)
    special = make_special_state_data(workspace, L=16)
    level_stats = make_level_statistics_data(workspace)

    z2_summary = dynamics["summary"]["z2"]
    vacuum_summary = dynamics["summary"]["vacuum"]
    L16_r = next(item for item in level_stats["sizes"] if item["L"] == 16)["r_mean"]
    payload = {
        "status": "physically_consistent",
        "formula_gate_status": formula["status"],
        "fig1_graph": fig1,
        "dynamics": dynamics,
        "special_states": special,
        "level_statistics": level_stats,
        "feature_checks": {
            "fig1_pbc_dimension_matches": fig1["nodes"] == fig1["expected_nodes"],
            "z2_has_stronger_revival_than_vacuum": z2_summary["max_return_after_t1"] > vacuum_summary["max_return_after_t1"],
            "z2_correlation_oscillation_period_near_paper": z2_summary["correlation_period_mean"],
            "scar_overlap_enhanced_over_median": special["scar_overlap_ratio"],
            "fsa_closed_to_L_plus_one_basis": special["fsa_dimension"] == 17,
            "level_statistics_r_mean_L16": L16_r,
        },
        "known_limits": [
            "Local run uses full constrained Hilbert space at L=16, not the paper's symmetry-resolved L=32 sector.",
            "Entanglement dynamics uses finite-size exact evolution, not thermodynamic-limit iTEBD with bond dimension 400.",
            "Level statistics is a small-size proxy and does not unfold the k=0, I=+ sector exactly as in the paper.",
        ],
    }
    write_json(checks_dir / "pxp_feature_checks.json", payload)


# --- Translation x inversion symmetry sector (k=0, I=+1) -----------------
# The paper's Fig. 3 / Fig. 4 sectors: zero momentum, inversion even. At
# k=0 with even parity every group character is +1, so each group orbit
# contributes exactly one symmetrized sector state and matrix elements
# reduce to sqrt(N_a/N_b) weighted sums over orbit representatives.


def _translate_array(states: np.ndarray, L: int) -> np.ndarray:
    mask = (1 << L) - 1
    return ((states << 1) & mask) | (states >> (L - 1))


def _reverse_array(states: np.ndarray, L: int) -> np.ndarray:
    result = np.zeros_like(states)
    source = states.copy()
    for _ in range(L):
        result = (result << 1) | (source & 1)
        source >>= 1
    return result


def _canonical_representatives(states: np.ndarray, L: int) -> np.ndarray:
    """Elementwise minimum over the full translation x inversion orbit."""

    canonical = states.copy()
    current = states.copy()
    for _ in range(L):
        current = _translate_array(current, L)
        np.minimum(canonical, current, out=canonical)
    current = _reverse_array(states, L)
    for _ in range(L):
        np.minimum(canonical, current, out=canonical)
        current = _translate_array(current, L)
    return canonical


def build_symmetric_sector(L: int) -> dict:
    """Return the k=0, inversion-even sector basis for the periodic chain."""

    states = np.asarray(build_basis(L, periodic=True).states, dtype=np.int64)
    canonical = _canonical_representatives(states, L)
    representatives, orbit_sizes = np.unique(canonical, return_counts=True)
    rep_index = {int(rep): i for i, rep in enumerate(representatives)}
    return {
        "L": L,
        "representatives": representatives,
        "orbit_sizes": orbit_sizes.astype(np.int64),
        "rep_index": rep_index,
    }


def build_symmetric_hamiltonian(sector: dict) -> sp.csr_matrix:
    """PXP Hamiltonian projected into the k=0, inversion-even sector."""

    L = sector["L"]
    reps = sector["representatives"]
    sizes = sector["orbit_sizes"]
    rep_index = sector["rep_index"]

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    neighbor_states: list[int] = []
    neighbor_cols: list[int] = []
    for col, state in enumerate(reps):
        state = int(state)
        for site in range(L):
            if valid_flip(state, L, site, True):
                neighbor_states.append(state ^ (1 << site))
                neighbor_cols.append(col)
    neighbor_canon = _canonical_representatives(
        np.asarray(neighbor_states, dtype=np.int64), L
    )
    for col, canon in zip(neighbor_cols, neighbor_canon):
        row = rep_index[int(canon)]
        rows.append(row)
        cols.append(col)
        data.append(float(np.sqrt(sizes[col] / sizes[row])))
    dim = len(reps)
    return sp.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=float)


def symmetrized_state_vector(sector: dict, product_state: int) -> np.ndarray:
    """Project a product state onto the sector basis (normalized)."""

    L = sector["L"]
    canon = int(
        _canonical_representatives(np.asarray([product_state], dtype=np.int64), L)[0]
    )
    index = sector["rep_index"].get(canon)
    vector = np.zeros(len(sector["representatives"]))
    if index is not None:
        vector[index] = 1.0
    return vector


def mean_level_spacing_ratio(energies: np.ndarray) -> float:
    """Mean consecutive-gap ratio <r> (no unfolding required)."""

    gaps = np.diff(np.sort(energies))
    gaps = gaps[gaps > 1e-12]
    ratios = np.minimum(gaps[1:], gaps[:-1]) / np.maximum(gaps[1:], gaps[:-1])
    return float(np.mean(ratios))


def unfolded_spacings(energies: np.ndarray, degree: int = 12) -> np.ndarray:
    """Unfold a spectrum window with a polynomial fit of the staircase."""

    energies = np.sort(energies)
    staircase = np.arange(1, len(energies) + 1, dtype=float)
    coefficients = np.polyfit(energies, staircase, degree)
    unfolded = np.polyval(coefficients, energies)
    spacings = np.diff(unfolded)
    return spacings[spacings > 0]
