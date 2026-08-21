#!/usr/bin/env python3
"""Run all independent numerical checks for Wootters's two-qubit formula."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from wootters.model import (  # noqa: E402
    SPIN_FLIP,
    average_concurrence,
    average_entanglement,
    bell_diagonal_state,
    bell_state,
    caratheodory_ensemble_bound,
    concurrence,
    concurrence_spectrum,
    entanglement_from_concurrence,
    hjw_decomposition,
    hjw_isometry_from_decomposition,
    magic_basis,
    optimal_decomposition,
    partial_transpose_b,
    pure_concurrence,
    pure_entanglement,
    random_density_matrix,
    random_isometry,
    spin_flip_state,
    tilde_orthogonal_decomposition,
    typical_subspace_record,
    werner_state,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def random_unitary_2(rng: np.random.Generator) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2)))
    phases = np.diag(r)
    return q @ np.diag(np.where(abs(phases) > 0, phases.conj() / abs(phases), 1.0))


def random_unitary_4(rng: np.random.Generator) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4)))
    phases = np.diag(r)
    return q @ np.diag(np.where(abs(phases) > 0, phases.conj() / abs(phases), 1.0))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    started = time.perf_counter()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    p, limits = config["parameters"], config["acceptance"]
    rng = np.random.default_rng(int(p["random_seed"]))
    root = Path(args.output_root)
    data = root / "data"
    checks_dir = root / "checks"
    data.mkdir(parents=True, exist_ok=True)

    pure_errors = []
    for _ in range(int(p["pure_state_samples"])):
        state = rng.normal(size=4) + 1j * rng.normal(size=4)
        state /= np.linalg.norm(state)
        c = pure_concurrence(state)
        pure_errors.append(
            abs(pure_entanglement(state) - entanglement_from_concurrence(c))
        )

    mixed_rows = []
    lower_bound_violation = 0.0
    reconstruction_error = 0.0
    spectrum_error = 0.0
    local_unitary_error = 0.0
    for sample in range(int(p["mixed_state_samples"])):
        rho = random_density_matrix(rng)
        c = concurrence(rho)
        direct_values = np.linalg.eigvals(rho @ SPIN_FLIP @ rho.conj() @ SPIN_FLIP)
        direct_lambdas = np.sort(np.sqrt(np.clip(direct_values.real, 0.0, None)))[::-1]
        spectrum_error = max(
            spectrum_error,
            float(np.max(np.abs(concurrence_spectrum(rho) - direct_lambdas))),
        )
        u, v = random_unitary_2(rng), random_unitary_2(rng)
        local = np.kron(u, v)
        local_unitary_error = max(
            local_unitary_error, abs(concurrence(local @ rho @ local.conj().T) - c)
        )
        best_average = np.inf
        for _ in range(int(p["decompositions_per_state"])):
            iso = random_isometry(rng, 4, 4)
            states = hjw_decomposition(rho, iso)
            reconstruction_error = max(
                reconstruction_error,
                float(np.linalg.norm(states @ states.conj().T - rho)),
            )
            avg = average_concurrence(states)
            best_average = min(best_average, avg)
            lower_bound_violation = max(lower_bound_violation, c - avg)
        mixed_rows.append(
            {
                "sample": sample,
                "concurrence": c,
                "entanglement": entanglement_from_concurrence(c),
                "best_random_decomposition_average_concurrence": best_average,
                "lower_bound_gap": best_average - c,
            }
        )

    basis = magic_basis()
    magic_basis_error = float(np.linalg.norm(basis.conj().T @ basis - np.eye(4)))
    for _ in range(int(p["pure_state_samples"])):
        coefficients = rng.normal(size=4) + 1j * rng.normal(size=4)
        magic_basis_error = max(
            magic_basis_error,
            float(
                np.linalg.norm(
                    spin_flip_state(basis @ coefficients) - basis @ coefficients.conj()
                )
            ),
        )

    optimal_rows = []
    max_takagi_residual = 0.0
    max_optimal_reconstruction_error = 0.0
    max_optimal_concurrence_gap = 0.0
    max_optimal_entanglement_gap = 0.0
    max_hjw_converse_error = 0.0
    max_zero_phase_closure_error = 0.0
    max_equal_entanglement_spread = 0.0
    branch_counts = {"positive_concurrence": 0, "zero_concurrence": 0}
    optimal_inputs = []
    for rank in range(1, 5):
        for sample in range(int(p["optimal_samples_per_rank"])):
            optimal_inputs.append(
                (f"random_rank_{rank}_{sample}", rank, random_density_matrix(rng, rank))
            )
    for value in p["zero_branch_werner_p"]:
        optimal_inputs.append((f"werner_{value}", 4, werner_state(float(value))))

    for sample_id, rank, rho in optimal_inputs:
        tilde_states, lambdas = tilde_orthogonal_decomposition(rho)
        tilde_matrix = tilde_states.conj().T @ SPIN_FLIP @ tilde_states.conj()
        max_takagi_residual = max(
            max_takagi_residual,
            float(np.linalg.norm(tilde_matrix - np.diag(lambdas))),
        )
        states, diagnostics = optimal_decomposition(rho)
        component_entanglements = [
            pure_entanglement(states[:, index])
            for index in range(states.shape[1])
            if float(np.vdot(states[:, index], states[:, index]).real) > 1.0e-15
        ]
        entanglement_spread = float(
            max(component_entanglements) - min(component_entanglements)
        )
        max_equal_entanglement_spread = max(
            max_equal_entanglement_spread, entanglement_spread
        )
        isometry = hjw_isometry_from_decomposition(rho, states)
        converse_error = float(
            np.linalg.norm(hjw_decomposition(rho, isometry) - states)
        )
        max_hjw_converse_error = max(max_hjw_converse_error, converse_error)
        max_optimal_reconstruction_error = max(
            max_optimal_reconstruction_error, float(diagnostics["reconstruction_error"])
        )
        max_optimal_concurrence_gap = max(
            max_optimal_concurrence_gap, float(diagnostics["concurrence_gap"])
        )
        max_optimal_entanglement_gap = max(
            max_optimal_entanglement_gap, float(diagnostics["entanglement_gap"])
        )
        if diagnostics["branch"] == "zero_concurrence":
            max_zero_phase_closure_error = max(
                max_zero_phase_closure_error, float(diagnostics["phase_closure_error"])
            )
        branch_counts[str(diagnostics["branch"])] += 1
        optimal_rows.append(
            {
                "sample_id": sample_id,
                "rank": rank,
                "branch": diagnostics["branch"],
                "concurrence": concurrence(rho),
                "ensemble_average_concurrence": average_concurrence(states),
                "ensemble_average_entanglement": average_entanglement(states),
                "reconstruction_error": diagnostics["reconstruction_error"],
                "concurrence_gap": diagnostics["concurrence_gap"],
                "entanglement_gap": diagnostics["entanglement_gap"],
                "hjw_converse_error": converse_error,
                "phase_closure_error": diagnostics.get("phase_closure_error", 0.0),
                "component_entanglement_spread": entanglement_spread,
            }
        )

    bell_rows = []
    max_bell_reconstruction_error = 0.0
    max_bell_concurrence_gap = 0.0
    max_bell_entanglement_gap = 0.0
    bell_cases = [
        (
            "named_positive_degenerate",
            np.asarray(p["named_degenerate_bell_probabilities"], dtype=float),
        )
    ]
    denominator = int(p["bell_simplex_denominator"])
    for first in range(denominator + 1):
        for second in range(denominator - first + 1):
            for third in range(denominator - first - second + 1):
                fourth = denominator - first - second - third
                bell_cases.append(
                    (
                        f"simplex_{first}_{second}_{third}_{fourth}",
                        np.array([first, second, third, fourth], dtype=float)
                        / denominator,
                    )
                )
    for sample_id, probabilities in bell_cases:
        rho = bell_diagonal_state(probabilities)
        states, diagnostics = optimal_decomposition(rho)
        max_bell_reconstruction_error = max(
            max_bell_reconstruction_error,
            float(diagnostics["reconstruction_error"]),
        )
        max_bell_concurrence_gap = max(
            max_bell_concurrence_gap, float(diagnostics["concurrence_gap"])
        )
        max_bell_entanglement_gap = max(
            max_bell_entanglement_gap, float(diagnostics["entanglement_gap"])
        )
        bell_rows.append(
            {
                "sample_id": sample_id,
                "p_phi_plus": probabilities[0],
                "p_phi_minus": probabilities[1],
                "p_psi_plus": probabilities[2],
                "p_psi_minus": probabilities[3],
                "concurrence": concurrence(rho),
                "ensemble_average_concurrence": average_concurrence(states),
                "ensemble_average_entanglement": average_entanglement(states),
                "reconstruction_error": diagnostics["reconstruction_error"],
                "concurrence_gap": diagnostics["concurrence_gap"],
                "entanglement_gap": diagnostics["entanglement_gap"],
            }
        )

    # Conditioning campaign motivated by the universal quantifier in the
    # constructive proof.  These are physical density matrices, not arbitrary
    # symmetric test matrices: two eigenvalue families straddle exact rank
    # deficiency and a third family is an explicit convex mixture of product
    # states.  Every input receives a reproducible byte fingerprint.
    conditioning_rows = []
    conditioning_failures = 0
    conditioning_max_reconstruction = 0.0
    conditioning_max_concurrence_gap = 0.0
    conditioning_max_entanglement_gap = 0.0
    conditioning_max_takagi_residual = 0.0
    conditioning_rng = np.random.default_rng(int(p["conditioning_seed"]))
    conditioning_families = {
        "near_rank_3": np.array([1.0 - 2e-12, 1e-12, 1e-12, 0.0]),
        "near_full_rank": np.array([1.0 - 3e-12, 1e-12, 1e-12, 1e-12]),
    }
    for family, eigenvalues in conditioning_families.items():
        for sample in range(int(p["conditioning_samples_per_family"])):
            vectors = random_unitary_4(conditioning_rng)
            rho = (vectors * eigenvalues) @ vectors.conj().T
            fingerprint = hashlib.sha256(
                np.ascontiguousarray(rho).view(np.uint8)
            ).hexdigest()
            try:
                tilde_states, lambdas = tilde_orthogonal_decomposition(rho)
                residual = float(
                    np.linalg.norm(
                        tilde_states.conj().T
                        @ SPIN_FLIP
                        @ tilde_states.conj()
                        - np.diag(lambdas)
                    )
                )
                states, diagnostics = optimal_decomposition(rho)
                reconstruction = float(diagnostics["reconstruction_error"])
                concurrence_gap = float(diagnostics["concurrence_gap"])
                entanglement_gap = float(diagnostics["entanglement_gap"])
                error = ""
            except Exception as exception:  # recorded evidence, then gate fails
                conditioning_failures += 1
                residual = reconstruction = concurrence_gap = entanglement_gap = float(
                    "nan"
                )
                error = f"{type(exception).__name__}: {exception}"
            if not error:
                conditioning_max_takagi_residual = max(
                    conditioning_max_takagi_residual, residual
                )
                conditioning_max_reconstruction = max(
                    conditioning_max_reconstruction, reconstruction
                )
                conditioning_max_concurrence_gap = max(
                    conditioning_max_concurrence_gap, concurrence_gap
                )
                conditioning_max_entanglement_gap = max(
                    conditioning_max_entanglement_gap, entanglement_gap
                )
            conditioning_rows.append(
                {
                    "family": family,
                    "sample": sample,
                    "rho_sha256": fingerprint,
                    "concurrence": concurrence(rho),
                    "takagi_residual": residual,
                    "reconstruction_error": reconstruction,
                    "concurrence_gap": concurrence_gap,
                    "entanglement_gap": entanglement_gap,
                    "error": error,
                }
            )

    near_product_weights = np.array([1.0 - 3e-12, 1e-12, 1e-12, 1e-12])
    for sample in range(int(p["conditioning_separable_samples"])):
        products = []
        for _ in range(4):
            left = conditioning_rng.normal(size=2) + 1j * conditioning_rng.normal(
                size=2
            )
            right = conditioning_rng.normal(size=2) + 1j * conditioning_rng.normal(
                size=2
            )
            products.append(
                np.kron(
                    left / np.linalg.norm(left), right / np.linalg.norm(right)
                )
            )
        rho = sum(
            weight * np.outer(state, state.conj())
            for weight, state in zip(near_product_weights, products, strict=True)
        )
        fingerprint = hashlib.sha256(
            np.ascontiguousarray(rho).view(np.uint8)
        ).hexdigest()
        try:
            tilde_states, lambdas = tilde_orthogonal_decomposition(rho)
            residual = float(
                np.linalg.norm(
                    tilde_states.conj().T
                    @ SPIN_FLIP
                    @ tilde_states.conj()
                    - np.diag(lambdas)
                )
            )
            states, diagnostics = optimal_decomposition(rho)
            reconstruction = float(diagnostics["reconstruction_error"])
            concurrence_gap = float(diagnostics["concurrence_gap"])
            entanglement_gap = float(diagnostics["entanglement_gap"])
            error = ""
        except Exception as exception:  # recorded evidence, then gate fails
            conditioning_failures += 1
            residual = reconstruction = concurrence_gap = entanglement_gap = float(
                "nan"
            )
            error = f"{type(exception).__name__}: {exception}"
        if not error:
            conditioning_max_takagi_residual = max(
                conditioning_max_takagi_residual, residual
            )
            conditioning_max_reconstruction = max(
                conditioning_max_reconstruction, reconstruction
            )
            conditioning_max_concurrence_gap = max(
                conditioning_max_concurrence_gap, concurrence_gap
            )
            conditioning_max_entanglement_gap = max(
                conditioning_max_entanglement_gap, entanglement_gap
            )
        conditioning_rows.append(
            {
                "family": "near_rank_product_mixture",
                "sample": sample,
                "rho_sha256": fingerprint,
                "concurrence": concurrence(rho),
                "takagi_residual": residual,
                "reconstruction_error": reconstruction,
                "concurrence_gap": concurrence_gap,
                "entanglement_gap": entanglement_gap,
                "error": error,
            }
        )

    separable_max = 0.0
    ppt_min = 1.0
    for _ in range(int(p["separable_state_samples"])):
        rho = np.zeros((4, 4), dtype=complex)
        weights = rng.dirichlet(np.ones(6))
        for weight in weights:
            left = rng.normal(size=2) + 1j * rng.normal(size=2)
            right = rng.normal(size=2) + 1j * rng.normal(size=2)
            state = np.kron(left / np.linalg.norm(left), right / np.linalg.norm(right))
            rho += weight * np.outer(state, state.conj())
        separable_max = max(separable_max, concurrence(rho))
        ppt_min = min(
            ppt_min, float(np.min(np.linalg.eigvalsh(partial_transpose_b(rho))).real)
        )

    werner_rows = []
    werner_error = 0.0
    for value in np.linspace(0.0, 1.0, int(p["werner_grid_points"])):
        numeric = concurrence(werner_state(float(value)))
        analytic = max(0.0, (3.0 * float(value) - 1.0) / 2.0)
        werner_error = max(werner_error, abs(numeric - analytic))
        werner_rows.append(
            {
                "p": value,
                "numeric_concurrence": numeric,
                "analytic_concurrence": analytic,
                "entanglement": entanglement_from_concurrence(numeric),
            }
        )

    singlet = bell_state("psi_minus")
    product = np.array([0, 1, 0, 0], dtype=complex)
    endpoint_error = max(
        abs(pure_concurrence(singlet) - 1.0),
        pure_concurrence(product),
        abs(pure_entanglement(singlet) - 1.0),
        pure_entanglement(product),
    )

    protocol_rows = []
    tolerance_exponent = float(p["typical_tolerance_exponent"])
    for probability in p["typical_schmidt_probabilities"]:
        for copies in p["typical_copy_counts"]:
            protocol_rows.append(
                typical_subspace_record(
                    float(probability),
                    int(copies),
                    information_tolerance=float(copies) ** (-tolerance_exponent),
                )
            )
    final_copies = max(int(value) for value in p["typical_copy_counts"])
    final_protocol_rows = [
        row for row in protocol_rows if int(row["copies"]) == final_copies
    ]
    rank_two_rows = [row for row in optimal_rows if int(row["rank"]) <= 2]
    historical_rows = [
        {
            "claim": "rank_at_most_two_formula_campaign",
            "value": max(
                float(row["concurrence_gap"]) for row in rank_two_rows
            ),
            "reference": 0.0,
            "absolute_error": max(
                float(row["concurrence_gap"]) for row in rank_two_rows
            ),
            "cases": len(rank_two_rows),
            "scope_boundary": "The numerical formula is checked; the historical attribution to Ref. 9 remains source-unavailable.",
        },
        {
            "claim": "equal_entanglement_optimal_components",
            "value": max_equal_entanglement_spread,
            "reference": 0.0,
            "absolute_error": max_equal_entanglement_spread,
            "cases": len(optimal_rows),
            "scope_boundary": "The construction is checked; the unpublished Uhlmann attribution remains source-unavailable.",
        },
        {
            "claim": "caratheodory_pure_state_bound",
            "value": caratheodory_ensemble_bound(4),
            "reference": 16.0,
            "absolute_error": 0.0,
            "cases": 1,
            "scope_boundary": "The d^2 convex-hull bound is independently derived; the cited prior source is not bundled.",
        },
    ]

    for path, fields, rows in [
        (data / "random_mixed_states.csv", list(mixed_rows[0]), mixed_rows),
        (data / "optimal_decompositions.csv", list(optimal_rows[0]), optimal_rows),
        (data / "bell_diagonal_adversarial.csv", list(bell_rows[0]), bell_rows),
        (
            data / "ill_conditioned_physical_states.csv",
            list(conditioning_rows[0]),
            conditioning_rows,
        ),
        (data / "werner_family.csv", list(werner_rows[0]), werner_rows),
        (
            data / "pure_state_protocol_rates.csv",
            list(protocol_rows[0]),
            protocol_rows,
        ),
        (
            data / "historical_claim_checks.csv",
            list(historical_rows[0]),
            historical_rows,
        ),
    ]:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    assertions = {
        "pure_entropy_identity": max(pure_errors)
        <= limits["pure_entropy_identity_error_max"],
        "magic_basis_spin_flip_equivalence": magic_basis_error
        <= limits["magic_basis_error_max"],
        "rho_rhotilde_spectrum_equivalence": spectrum_error
        <= limits["spectrum_equivalence_error_max"],
        "local_unitary_invariance": local_unitary_error
        <= limits["local_unitary_invariance_error_max"],
        "hjw_reconstruction": reconstruction_error
        <= limits["decomposition_reconstruction_error_max"],
        "all_decompositions_obey_lower_bound": lower_bound_violation
        <= limits["concurrence_lower_bound_violation_max"],
        "takagi_tilde_orthogonality": max_takagi_residual
        <= limits["takagi_residual_max"],
        "constructive_optimal_reconstruction": max_optimal_reconstruction_error
        <= limits["decomposition_reconstruction_error_max"],
        "constructive_optimal_concurrence": max_optimal_concurrence_gap
        <= limits["optimal_concurrence_gap_max"],
        "constructive_optimal_entanglement": max_optimal_entanglement_gap
        <= limits["optimal_entanglement_gap_max"],
        "bell_diagonal_adversarial_reconstruction": max_bell_reconstruction_error
        <= limits["decomposition_reconstruction_error_max"],
        "bell_diagonal_adversarial_concurrence": max_bell_concurrence_gap
        <= limits["optimal_concurrence_gap_max"],
        "bell_diagonal_adversarial_entanglement": max_bell_entanglement_gap
        <= limits["optimal_entanglement_gap_max"],
        "ill_conditioned_physical_states_execute": conditioning_failures == 0,
        "ill_conditioned_takagi_orthogonality": conditioning_max_takagi_residual
        <= limits["takagi_residual_max"],
        "ill_conditioned_optimal_reconstruction": conditioning_max_reconstruction
        <= limits["decomposition_reconstruction_error_max"],
        "ill_conditioned_optimal_concurrence": conditioning_max_concurrence_gap
        <= limits["optimal_concurrence_gap_max"],
        "ill_conditioned_optimal_entanglement": conditioning_max_entanglement_gap
        <= limits["optimal_entanglement_gap_max"],
        "hjw_converse_isometry": max_hjw_converse_error
        <= limits["hjw_converse_error_max"],
        "positive_and_zero_branches_exercised": branch_counts["positive_concurrence"]
        >= limits["branch_samples_min"]
        and branch_counts["zero_concurrence"] >= limits["branch_samples_min"],
        "zero_branch_phase_polygon_closes": max_zero_phase_closure_error
        <= limits["zero_phase_closure_error_max"],
        "separable_mixtures_have_zero_concurrence": separable_max
        <= limits["separable_concurrence_max"],
        "werner_closed_form": werner_error <= limits["werner_formula_error_max"],
        "printed_endpoints": endpoint_error
        <= limits["pure_entropy_identity_error_max"],
        "separable_states_are_ppt": ppt_min >= -1e-12,
        "pure_state_typical_mass_converges": min(
            float(row["typical_probability_mass"]) for row in final_protocol_rows
        )
        >= limits["typical_final_probability_mass_min"],
        "pure_state_typical_rate_converges": max(
            abs(float(row["rate_minus_entropy"])) for row in final_protocol_rows
        )
        <= limits["typical_final_rate_error_max"],
        "rank_two_formula_campaign": historical_rows[0]["absolute_error"]
        <= limits["optimal_concurrence_gap_max"],
        "equal_entanglement_components": max_equal_entanglement_spread
        <= limits["optimal_entanglement_gap_max"],
        "caratheodory_bound_is_sixteen": caratheodory_ensemble_bound(4) == 16,
    }
    metrics = {
        "max_pure_entropy_identity_error": max(pure_errors),
        "max_magic_basis_spin_flip_error": magic_basis_error,
        "max_rho_rhotilde_spectrum_error": spectrum_error,
        "max_local_unitary_invariance_error": local_unitary_error,
        "max_hjw_reconstruction_error": reconstruction_error,
        "max_lower_bound_violation": lower_bound_violation,
        "max_takagi_residual": max_takagi_residual,
        "max_optimal_reconstruction_error": max_optimal_reconstruction_error,
        "max_optimal_concurrence_gap": max_optimal_concurrence_gap,
        "max_optimal_entanglement_gap": max_optimal_entanglement_gap,
        "bell_diagonal_adversarial_cases": len(bell_rows),
        "max_bell_diagonal_reconstruction_error": max_bell_reconstruction_error,
        "max_bell_diagonal_concurrence_gap": max_bell_concurrence_gap,
        "max_bell_diagonal_entanglement_gap": max_bell_entanglement_gap,
        "ill_conditioned_cases": len(conditioning_rows),
        "ill_conditioned_failures": conditioning_failures,
        "ill_conditioned_max_takagi_residual": conditioning_max_takagi_residual,
        "ill_conditioned_max_reconstruction_error": conditioning_max_reconstruction,
        "ill_conditioned_max_concurrence_gap": conditioning_max_concurrence_gap,
        "ill_conditioned_max_entanglement_gap": conditioning_max_entanglement_gap,
        "max_hjw_converse_error": max_hjw_converse_error,
        "max_zero_phase_closure_error": max_zero_phase_closure_error,
        "positive_branch_samples": branch_counts["positive_concurrence"],
        "zero_branch_samples": branch_counts["zero_concurrence"],
        "max_separable_concurrence": separable_max,
        "minimum_separable_partial_transpose_eigenvalue": ppt_min,
        "max_werner_formula_error": werner_error,
        "endpoint_error": endpoint_error,
        "typical_final_probability_mass_min": min(
            float(row["typical_probability_mass"]) for row in final_protocol_rows
        ),
        "typical_final_rate_error_max": max(
            abs(float(row["rate_minus_entropy"])) for row in final_protocol_rows
        ),
        "max_equal_component_entanglement_spread": max_equal_entanglement_spread,
        "rank_two_formula_cases": len(rank_two_rows),
        "caratheodory_ensemble_bound": caratheodory_ensemble_bound(4),
    }
    status = "passed" if all(assertions.values()) else "failed"
    target_assertions = {
        "T001": [
            "pure_entropy_identity",
            "magic_basis_spin_flip_equivalence",
            "printed_endpoints",
        ],
        "T002": ["rho_rhotilde_spectrum_equivalence", "local_unitary_invariance"],
        "T003": ["werner_closed_form", "printed_endpoints"],
        "T004": [
            "hjw_reconstruction",
            "hjw_converse_isometry",
            "takagi_tilde_orthogonality",
        ],
        "T005": [
            "all_decompositions_obey_lower_bound",
            "constructive_optimal_reconstruction",
            "constructive_optimal_concurrence",
            "constructive_optimal_entanglement",
            "bell_diagonal_adversarial_reconstruction",
            "bell_diagonal_adversarial_concurrence",
            "bell_diagonal_adversarial_entanglement",
            "ill_conditioned_physical_states_execute",
            "ill_conditioned_takagi_orthogonality",
            "ill_conditioned_optimal_reconstruction",
            "ill_conditioned_optimal_concurrence",
            "ill_conditioned_optimal_entanglement",
        ],
        "T006": [
            "positive_and_zero_branches_exercised",
            "zero_branch_phase_polygon_closes",
            "separable_mixtures_have_zero_concurrence",
            "separable_states_are_ppt",
        ],
        "T007": [
            "pure_state_typical_mass_converges",
            "pure_state_typical_rate_converges",
        ],
        "T008": ["rank_two_formula_campaign"],
        "T009": ["equal_entanglement_components"],
        "T010": ["caratheodory_bound_is_sixteen"],
    }
    science = {
        "schema_version": 2,
        "paper_id": "quant-ph-9709029",
        "status": status,
        "assertions": assertions,
        "metrics": metrics,
        "target_results": {
            target_id: {
                "status": (
                    "passed" if all(assertions[name] for name in names) else "failed"
                ),
                "assertion_ids": names,
            }
            for target_id, names in target_assertions.items()
        },
    }
    write_json(checks_dir / "science_checks.json", science)
    produced = [
        data / "random_mixed_states.csv",
        data / "optimal_decompositions.csv",
        data / "bell_diagonal_adversarial.csv",
        data / "ill_conditioned_physical_states.csv",
        data / "werner_family.csv",
        data / "pure_state_protocol_rates.csv",
        data / "historical_claim_checks.csv",
        checks_dir / "science_checks.json",
    ]
    write_json(
        checks_dir / "generated_data_manifest.json",
        {
            "schema_version": 1,
            "paper_id": "quant-ph-9709029",
            "generated_data_provenance": "independent_numerics",
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "files": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path in produced
            ],
        },
    )
    write_json(
        checks_dir / "run_summary.json",
        {
            "schema_version": 1,
            "paper_id": "quant-ph-9709029",
            "status": status,
            "runtime_seconds": time.perf_counter() - started,
            "targets": [f"T{i:03d}" for i in range(1, 11)],
            "paper_parameters_executed": True,
            "artifact_stage": "final_reproduction",
        },
    )
    print(json.dumps({"status": status, **metrics}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
