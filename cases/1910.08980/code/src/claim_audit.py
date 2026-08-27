"""Independent finite falsification checks for the paper's analytic claims.

The checks make every claim executable but do not turn finite examples into
proofs.  Each result therefore records its scope limit and awards no scientific
coverage until a fresh proof-level review closes the claim.
"""
from __future__ import annotations

from itertools import product
from math import log, sqrt
from typing import Any

import numpy as np

from src.rqaoa import (
    brute_force_ising_max,
    edge_pairs,
    ising_energy,
    optimize_qaoa1,
    qaoa1_at_gamma,
    run_rqaoa1,
)


def qaoa_corollary_bound(degree: int) -> float:
    if degree < 2:
        raise ValueError("degree must be at least two")
    return float(5.0 / 6.0 + sqrt(degree - 1.0) / (3.0 * degree))


def qaoa_depth_bound(level: int, degree: int, *, regular_bipartite: bool) -> int:
    if level < 1 or degree < 1:
        raise ValueError("level and degree must be positive")
    return level * (degree if regular_bipartite else degree + 1)


def exact_edge_expansion(couplings: np.ndarray) -> float:
    """Return min |boundary(S)|/|S| for nonempty |S|<=n/2."""
    pairs = edge_pairs(np.asarray(couplings, dtype=float))
    n = couplings.shape[0]
    if n > 18:
        raise ValueError("exact expansion audit is limited to 18 vertices")
    best = np.inf
    for mask in range(1, 1 << n):
        size = mask.bit_count()
        if size > n // 2:
            continue
        boundary = sum(bool((mask >> int(u)) & 1) != bool((mask >> int(v)) & 1) for u, v in pairs)
        best = min(best, boundary / size)
    return float(best)


def gauge_transform(couplings: np.ndarray, gauge: np.ndarray) -> np.ndarray:
    gauge = np.asarray(gauge, dtype=np.int64)
    if not set(np.unique(gauge)) <= {-1, 1}:
        raise ValueError("gauge entries must be +/-1")
    return np.asarray(couplings, dtype=float) * np.outer(gauge, gauge)


def cycle_couplings(signs: tuple[int, ...]) -> np.ndarray:
    n = len(signs)
    if n < 3 or not set(signs) <= {-1, 1}:
        raise ValueError("a signed cycle needs at least three +/-1 couplings")
    matrix = np.zeros((n, n), dtype=float)
    for index, sign in enumerate(signs):
        neighbor = (index + 1) % n
        matrix[index, neighbor] += sign
        matrix[neighbor, index] += sign
    return matrix


def theorem3_family(bits: tuple[int, ...]) -> tuple[int, ...]:
    """Return J(s): J_3a=J_(3a+1)=(-1)^s_a and J_(3a+2)=1."""
    signs: list[int] = []
    for bit in bits:
        if bit not in {0, 1}:
            raise ValueError("family bits must be zero or one")
        sign = -1 if bit else 1
        signs.extend((sign, sign, 1))
    return tuple(signs)


def theorem3_local_spins(signs: tuple[int, ...]) -> np.ndarray:
    """Implement Lemma D.1's uniform 1-local rule in the Z basis."""
    bits = [int(signs[v - 1] == -1 and signs[v] == -1) for v in range(len(signs))]
    return np.asarray([1 if bit == 0 else -1 for bit in bits], dtype=np.int64)


def exact_cycle_optimum(signs: tuple[int, ...]) -> int:
    return len(signs) if int(np.prod(signs)) == 1 else len(signs) - 2


def _statevector_correlations(couplings: np.ndarray, beta: float, gamma: float) -> np.ndarray:
    n = couplings.shape[0]
    dimension = 1 << n
    spins = np.empty((dimension, n), dtype=np.int64)
    for state in range(dimension):
        spins[state] = [1 if not state & (1 << qubit) else -1 for qubit in range(n)]
    energies = np.asarray([ising_energy(couplings, row) for row in spins])
    wavefunction = np.exp(1j * gamma * energies) / np.sqrt(dimension)
    cosine, sine = np.cos(beta), 1j * np.sin(beta)
    for qubit in range(n):
        previous = wavefunction
        wavefunction = np.asarray(
            [cosine * previous[state] + sine * previous[state ^ (1 << qubit)] for state in range(dimension)]
        )
    probabilities = np.abs(wavefunction) ** 2
    return np.asarray(
        [np.sum(probabilities * spins[:, u] * spins[:, v]) for u, v in edge_pairs(couplings)]
    )


def _result(passed: bool, value: Any, limit: str) -> dict[str, Any]:
    return {
        "finite_check_passed": bool(passed),
        "value": value,
        "scientific_coverage_awarded": False,
        "scope_limit": limit,
    }


def run_claim_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute one independent, claim-addressed check for all 16 items."""
    finite = config["finite_checks"]
    results: dict[str, dict[str, Any]] = {}

    # Theorem 1: make the expansion/epsilon/depth threshold calculation executable.
    k33 = np.zeros((6, 6), dtype=float)
    for left in range(3):
        for right in range(3, 6):
            k33[left, right] = k33[right, left] = 1.0
    expansion = exact_edge_expansion(k33)
    depth = int(finite["nlts_depth"])
    threshold = int(48**2 * 8**depth)
    epsilon = expansion / 6.0
    results["C-MAIN-T1-NLTS"] = _result(
        expansion > 0 and np.isclose(6.0 * epsilon, expansion) and threshold == 48**2 * 8**depth,
        {"example_graph": "K3,3", "h": expansion, "epsilon_h_over_6": epsilon, "required_n_strictly_above": threshold},
        "This audits the constants and a finite expansion oracle; it is not a proof of the symmetry-protected NLTS theorem.",
    )

    degree = int(finite["corollary_degree"])
    results["C-MAIN-C1-QAOA-BOUND"] = _result(
        0 < qaoa_corollary_bound(degree) < 1,
        {"degree": degree, "ratio_upper_bound": qaoa_corollary_bound(degree)},
        "Formula evaluation does not prove the infinite-family corollary.",
    )
    level = int(finite["depth_level"])
    results["C-APP-A-L1-DEPTH"] = _result(
        qaoa_depth_bound(level, degree, regular_bipartite=True)
        <= qaoa_depth_bound(level, degree, regular_bipartite=False),
        {
            "general_depth": qaoa_depth_bound(level, degree, regular_bipartite=False),
            "regular_bipartite_depth": qaoa_depth_bound(level, degree, regular_bipartite=True),
        },
        "Arithmetic checks the stated edge-colouring bounds; a proof still needs the colouring argument.",
    )
    base = cycle_couplings((1, -1, 1, 1, -1, 1))
    gauged = gauge_transform(base, np.asarray([1, -1, 1, -1, 1, -1]))
    exact_before, exact_after = brute_force_ising_max(base), brute_force_ising_max(gauged)
    qaoa_before, qaoa_after = optimize_qaoa1(base), optimize_qaoa1(gauged)
    results["C-APP-A-L2-GAUGE"] = _result(
        np.isclose(exact_before.energy, exact_after.energy)
        and np.isclose(qaoa_before.expected_energy, qaoa_after.expected_energy, atol=1e-9),
        {"exact_before": exact_before.energy, "exact_after": exact_after.energy, "qaoa_before": qaoa_before.expected_energy, "qaoa_after": qaoa_after.expected_energy},
        "One finite property test does not replace the analytic covariance proof.",
    )

    range_rows = []
    for row in finite["range_pairs"]:
        n, radius = int(row["n"]), int(row["R"])
        bound = (2.0 * radius + 0.5) / (2.0 * radius + 1.0)
        range_rows.append({"n": n, "R": radius, "bound": bound, "divisible": n % (2 * radius + 1) == 0})
    results["C-MAIN-T2-RANGE-BOUND"] = _result(
        all(row["R"] < row["n"] / 4 and 0 < row["bound"] < 1 for row in range_rows),
        range_rows,
        "The executable inequality boundary does not prove the light-cone argument for every symmetric circuit.",
    )
    results["C-MAIN-T2-TIGHTNESS"] = _result(
        any(row["divisible"] for row in range_rows),
        {"exact_tight_rows": [row for row in range_rows if row["divisible"]]},
        "This checks the divisibility/tightness contract; it does not certify the complete circuit construction.",
    )
    ghz_size = 2 * int(finite["ghz_radius"]) + 1
    ghz = np.zeros(1 << ghz_size, dtype=complex)
    ghz[0] = ghz[-1] = 1 / sqrt(2)
    global_x = ghz[::-1]
    results["C-APP-B-L1-GHZ"] = _result(
        np.allclose(global_x, ghz) and np.isclose(np.vdot(ghz, ghz), 1.0),
        {"qubits": ghz_size, "global_x_symmetric": True, "normalization": float(np.vdot(ghz, ghz).real)},
        "The target GHZ state is checked, but circuit range/depth still requires proof-level review.",
    )
    radius = int(finite["ghz_radius"])
    printed_ratio = (2 * radius + 0.5) / (2 * radius + 1)
    n = int(finite["printed_energy_n"])
    results["C-APP-B-L2-PRINTED-ENERGY"] = _result(
        not np.isclose(printed_ratio, n * printed_ratio),
        {"printed_value": printed_ratio, "unnormalized_proof_value": n * printed_ratio, "factor": n},
        "The dimensional inconsistency is a paper-error candidate, not a verdict without fresh independent review.",
    )

    correlation_matrix = np.asarray(finite["correlation_matrix"], dtype=float)
    gamma = float(finite["correlation_gamma"])
    analytic = qaoa1_at_gamma(correlation_matrix, gamma)
    direct = _statevector_correlations(correlation_matrix, analytic.beta, gamma)
    results["C-APP-C-L1-CORRELATION"] = _result(
        np.allclose(analytic.correlations, direct, atol=2e-12),
        {"max_abs_error": float(np.max(np.abs(analytic.correlations - direct))), "edges": len(direct)},
        "A small-system independent statevector check falsifies formula errors but is not a symbolic proof.",
    )
    sizes = [int(value) for value in finite["runtime_sizes"]]
    operation_proxy = [size * size**2 * size for size in sizes]
    slopes = [log(operation_proxy[i + 1] / operation_proxy[i]) / log(sizes[i + 1] / sizes[i]) for i in range(len(sizes) - 1)]
    results["C-APP-C-RUNTIME-O-N4"] = _result(
        all(np.isclose(slope, 4.0) for slope in slopes),
        {"sizes": sizes, "operation_proxy": operation_proxy, "log_slopes": slopes},
        "This checks the loop-count derivation, not wall-clock asymptotics on every backend.",
    )

    family_rows = []
    family_bits = int(finite["theorem3_family_bits"])
    for bits in product((0, 1), repeat=family_bits):
        signs = theorem3_family(bits)
        couplings = cycle_couplings(signs)
        local_energy = ising_energy(couplings, theorem3_local_spins(signs))
        optimum = brute_force_ising_max(couplings).energy
        qaoa = optimize_qaoa1(couplings, gamma_grid_points=129, local_candidates=6)
        rqaoa = run_rqaoa1(couplings, cutoff=3, gamma_grid_points=65, local_candidates=4)
        family_rows.append({"bits": bits, "n": len(signs), "local_energy": local_energy, "optimum": optimum, "qaoa1_ratio": qaoa.expected_energy / optimum, "rqaoa1_ratio": rqaoa.energy / optimum})
    results["C-MAIN-T3-LOCAL"] = _result(
        all(np.isclose(row["local_energy"], row["optimum"]) for row in family_rows),
        family_rows,
        "The complete smallest family is exhaustive; the all-n theorem still needs analytic review.",
    )
    results["C-MAIN-T3-QAOA"] = _result(
        all(row["qaoa1_ratio"] <= 0.5 + 1e-8 for row in family_rows),
        {"p": 1, "bound": 0.5, "max_ratio": max(row["qaoa1_ratio"] for row in family_rows)},
        "Only p=1 and the smallest family are tested; the p/(p+1) theorem is not numerically proven.",
    )
    results["C-MAIN-T3-RQAOA"] = _result(
        all(np.isclose(row["rqaoa1_ratio"], 1.0) for row in family_rows),
        {"min_ratio": min(row["rqaoa1_ratio"] for row in family_rows), "instances": len(family_rows)},
        "The smallest theorem family passes; the general statement still requires proof-level review.",
    )
    results["C-APP-D-L1-PRINTED-ENERGY"] = _result(
        all(np.isclose(row["local_energy"], row["n"]) and not np.isclose(row["local_energy"], 1.0) for row in family_rows),
        {"raw_energies": [row["local_energy"] for row in family_rows], "printed_raw_energy": 1, "normalized_ratio": 1},
        "Finite enumeration supports a missing-normalization-factor hypothesis; fresh review must adjudicate the paper text.",
    )

    ring_rows = []
    for ring_n in range(3, int(finite["exhaustive_ring_n_max"]) + 1):
        for signs in product((-1, 1), repeat=ring_n):
            couplings = cycle_couplings(signs)
            exact = brute_force_ising_max(couplings).energy
            rqaoa = run_rqaoa1(couplings, cutoff=min(3, ring_n), gamma_grid_points=65, local_candidates=4)
            formula = exact_cycle_optimum(signs)
            ring_rows.append({"n": ring_n, "parity": int(np.prod(signs)), "exact": exact, "formula": formula, "rqaoa": rqaoa.energy})
    results["C-APP-D-L2-RQAOA-1D"] = _result(
        all(np.isclose(row["exact"], row["formula"]) and np.isclose(row["rqaoa"], row["exact"]) for row in ring_rows),
        {"instances": len(ring_rows), "n_max": int(finite["exhaustive_ring_n_max"])},
        "Exhaustive finite rings are a falsification suite, not an induction proof.",
    )
    impossible = all(row["optimum"] <= row["n"] for row in family_rows)
    endpoint_rows = [{"n": row["n"], "correct_unfrustrated_max": row["n"], "printed_max": row["n"] + 1} for row in family_rows]
    results["C-APP-D-L2-ENDPOINT-ENERGY"] = _result(
        impossible and all(row["printed_max"] > row["correct_unfrustrated_max"] for row in endpoint_rows),
        endpoint_rows,
        "Term-count and enumeration support an off-by-one hypothesis; fresh review must issue any paper-error verdict.",
    )

    return {
        "schema_version": 1,
        "status": "finite_falsification_suite_executed",
        "items_total": len(results),
        "items_finite_check_passed": sum(row["finite_check_passed"] for row in results.values()),
        "scientific_coverage_awarded": False,
        "results": results,
    }
