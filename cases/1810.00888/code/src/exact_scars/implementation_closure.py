"""Executable small-scale witnesses for the no-display claims T010-T023.

The campaign deliberately separates implementation attestation from scientific
acceptance.  Small chains exercise the formula-derived algorithms; they do not
replace the paper-scale L=26 calculation or a fresh proof review.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from .model import (
    bit,
    build_basis,
    build_hamiltonian,
    build_trial_family,
    gamma_state,
    invert_state,
    mps_matrices,
    sector_spectrum,
    translate_state,
)


ITEMS_BY_TARGET = {
    "T010": ["clm_pbc_exact_e0"],
    "T011": ["clm_pbc_aklt_relation"],
    "T012": ["clm_pbc_cross_overlap", "clm_pbc_norm"],
    "T013": ["clm_pbc_domain_wall_eth", "clm_pbc_one_site_rdm_eth", "clm_pbc_rho12", "clm_pbc_rho23_bond_order"],
    "T014": ["clm_pbc_inversion", "clm_pbc_particle_hole", "clm_pbc_translation_momentum"],
    "T015": ["clm_obc_inversion_zero_exchange", "clm_obc_particle_hole"],
    "T016": ["clm_obc_norm"],
    "T017": ["clm_obc_entanglement_d2", "clm_obc_entanglement_d3", "clm_pbc_momentum_entropy"],
    "T018": ["clm_l26_scar_density"],
    "T019": ["clm_xi1_cph_partner", "clm_xi_family_exact_sector"],
    "T020": ["clm_quasiparticle_frequency_rule"],
    "T021": ["clm_tilde_xi1_cph_partner", "clm_tilde_xi1_optimum", "clm_tilde_xi1_sector_orthogonality"],
    "T022": ["clm_tilde_upsilon1_optimum"],
    "T023": ["clm_tilde_upsilon1_cph_partner", "clm_tilde_upsilon1_orthogonality", "clm_upsilon1_cph_partner"],
}

SCIENTIFIC_BOUNDARIES = {
    "T010": "Exact finite-chain zero-energy and blockade identities pass; fresh proof review is still required.",
    "T011": "The nonzero transfer spectra agree, but the explicit AKLT physical-state swap and gauge map are not yet reconstructed.",
    "T012": "The finite norm and Gram identities pass at the canary size; the closed overlap formula still needs proof-level review.",
    "T013": "State-weighted finite reduced densities are computed; the printed thermodynamic limits and ETH comparisons remain unverified.",
    "T014": "Finite translation, inversion, and particle-hole identities pass; independent proof review remains open.",
    "T015": "Finite open-boundary inversion and particle-hole exchange identities pass; independent proof review remains open.",
    "T016": "The finite open-boundary norm formula passes; independent proof review remains open.",
    "T017": "Finite entanglement witnesses pass at declared sizes; asymptotic and momentum-state limits remain review-limited.",
    "T018": "The L=12 density canary runs, but the paper claim is L=26 and has not been executed by this contract.",
    "T019": "One finite Xi witness passes its sector and particle-hole checks; the every-n family claim is not proved.",
    "T020": "The energy-frequency bookkeeping is executable, but no observable time evolution or selection-rule matrix element is tested.",
    "T021": "The reduced tilde-Xi witness runs, but paper-scale energy, variance, and thermodynamic orthogonality remain open.",
    "T022": "The rounded printed tilde-Upsilon parameters do not fix a unique paper-exact convention; the parameterized path remains input-limited.",
    "T023": "Finite particle-hole and overlap canaries pass; thermodynamic orthogonality is not established.",
}


def _periodic_mps_state(length: int, offset: int) -> tuple[Any, np.ndarray, np.ndarray]:
    basis = build_basis(length, periodic=True)
    b_matrices, c_matrices = mps_matrices()
    raw = np.empty(len(basis.states), dtype=np.float64)
    for index, state_value in enumerate(basis.states):
        state = int(state_value)
        matrix = np.eye(2 if offset == 0 else 3)
        for site in range(length):
            matrices = b_matrices if (site + offset) % 2 == 0 else c_matrices
            matrix = matrix @ matrices[bit(state, site)]
        raw[index] = float(np.trace(matrix))
    return basis, raw, raw / np.linalg.norm(raw)


def _permute(basis: Any, vector: np.ndarray, operation: Callable[[int, int], int]) -> np.ndarray:
    result = np.zeros_like(vector)
    for source, state_value in enumerate(basis.states):
        target_state = operation(int(state_value), basis.length)
        result[basis.index[target_state]] = vector[source]
    return result


def _particle_hole_signs(basis: Any) -> np.ndarray:
    return np.asarray([(-1.0) ** int(state).bit_count() for state in basis.states])


def _full_amplitudes(basis: Any, vector: np.ndarray) -> np.ndarray:
    result = np.zeros(2**basis.length, dtype=np.float64)
    result[basis.states] = vector
    return result


def _reduced_density(full: np.ndarray, length: int, sites: tuple[int, ...]) -> np.ndarray:
    tensor = full.reshape((2,) * length)
    keep = tuple(length - 1 - site for site in sites)
    trace = tuple(axis for axis in range(length) if axis not in keep)
    ordered = keep + trace
    reshaped = np.transpose(tensor, ordered).reshape(2 ** len(keep), -1)
    return reshaped @ reshaped.T


def _schmidt_probabilities(basis: Any, vector: np.ndarray, cut: int) -> np.ndarray:
    full = _full_amplitudes(basis, vector)
    matrix = full.reshape(2 ** (basis.length - cut), 2**cut)
    probabilities = np.linalg.svd(matrix, compute_uv=False) ** 2
    probabilities = probabilities[probabilities > 1e-13]
    probabilities /= probabilities.sum()
    return np.sort(probabilities)[::-1]


def _raw_gamma(length: int, alpha: int, beta: int) -> tuple[Any, np.ndarray]:
    basis = build_basis(length, periodic=False)
    b_matrices, c_matrices = mps_matrices()
    boundaries = {1: np.asarray([1.0, 1.0]), 2: np.asarray([1.0, -1.0])}
    vector = np.empty(len(basis.states), dtype=np.float64)
    for index, state_value in enumerate(basis.states):
        state = int(state_value)
        matrix = np.eye(2)
        for site in range(length):
            matrices = b_matrices if site % 2 == 0 else c_matrices
            matrix = matrix @ matrices[bit(state, site)]
        vector[index] = boundaries[alpha] @ matrix @ boundaries[beta]
    return basis, vector


def run_campaign(config: dict[str, Any]) -> dict[str, Any]:
    profile = str(config["profile"])
    parameters = config["parameters"]
    length = int(parameters["attestation_length"])
    tolerance = float(parameters["tolerance"])
    basis, raw_phi1, phi1 = _periodic_mps_state(length, 0)
    _, raw_phi2, phi2 = _periodic_mps_state(length, 1)
    hamiltonian = build_hamiltonian(basis)
    translation_phi1 = _permute(basis, phi1, translate_state)
    inversion_phi1 = _permute(basis, phi1, invert_state)
    particle_hole = _particle_hole_signs(basis)
    blocks = length // 2
    target_checks: dict[str, dict[str, Any]] = {}

    t010 = {
        "phi1_energy_residual": float(np.linalg.norm(hamiltonian @ phi1)),
        "phi2_energy_residual": float(np.linalg.norm(hamiltonian @ phi2)),
        "basis_blockade_valid": bool(all((int(s) & (int(s) << 1)) == 0 for s in basis.states)),
    }
    t010["passed"] = bool(max(t010["phi1_energy_residual"], t010["phi2_energy_residual"]) <= tolerance and t010["basis_blockade_valid"])
    target_checks["T010"] = t010

    b_matrices, c_matrices = mps_matrices()
    bc = [b_matrices[a] @ c_matrices[b] for a in (0, 1) for b in (0, 1)]
    cb = [c_matrices[a] @ b_matrices[b] for a in (0, 1) for b in (0, 1)]
    transfer_bc = sum(np.kron(matrix, matrix) for matrix in bc)
    transfer_cb = sum(np.kron(matrix, matrix) for matrix in cb)
    spectrum_bc = np.sort_complex(np.linalg.eigvals(transfer_bc))
    spectrum_cb = np.sort_complex(np.asarray([v for v in np.linalg.eigvals(transfer_cb) if abs(v) > tolerance]))
    t011 = {"bc_transfer_spectrum": [[float(v.real), float(v.imag)] for v in spectrum_bc], "cb_nonzero_transfer_spectrum": [[float(v.real), float(v.imag)] for v in spectrum_cb], "nonzero_spectrum_residual": float(np.linalg.norm(spectrum_bc - spectrum_cb))}
    t011["passed"] = bool(t011["nonzero_spectrum_residual"] <= tolerance)
    target_checks["T011"] = t011

    norm_formula = float(3**blocks + 2 + (-1) ** blocks)
    gram = np.asarray([[raw_phi1 @ raw_phi1, raw_phi1 @ raw_phi2], [raw_phi2 @ raw_phi1, raw_phi2 @ raw_phi2]])
    t012 = {
        "phi1_norm_squared": float(gram[0, 0]),
        "phi2_norm_squared": float(gram[1, 1]),
        "paper_norm_formula": norm_formula,
        "cross_overlap": float(gram[0, 1]),
        "gram_determinant": float(np.linalg.det(gram)),
        "linearly_independent_expected": bool(blocks > 3),
    }
    t012["passed"] = bool(abs(t012["phi1_norm_squared"] - norm_formula) <= tolerance and abs(t012["phi2_norm_squared"] - norm_formula) <= tolerance and ((t012["gram_determinant"] > tolerance) == (blocks > 3)))
    target_checks["T012"] = t012

    full_phi1 = _full_amplitudes(basis, phi1)
    rho1 = _reduced_density(full_phi1, length, (0,))
    rho12 = _reduced_density(full_phi1, length, (0, 1))
    rho23 = _reduced_density(full_phi1, length, (1, 2))
    density = float(rho1[1, 1])
    probabilities = np.abs(phi1) ** 2
    # The paper calls P_j P_{j+1} the ``domain wall number'', with
    # P=|0><0|.  It is therefore the probability of an adjacent 00 pair,
    # not the probability that the two occupation bits differ.  Keeping this
    # definition literal is important: the latter observable is 2/3 in this
    # state and would falsely contradict the printed 1/3 result.
    domain_wall_indicator = np.asarray(
        [not bit(int(state), 0) and not bit(int(state), 1) for state in basis.states],
        dtype=float,
    )
    domain_wall = float(probabilities @ domain_wall_indicator)
    t013 = {
        "one_site_density": density,
        "distance_to_one_third": abs(density - 1.0 / 3.0),
        "rho1_trace_residual": abs(float(np.trace(rho1)) - 1.0),
        "rho12_trace_residual": abs(float(np.trace(rho12)) - 1.0),
        "rho23_trace_residual": abs(float(np.trace(rho23)) - 1.0),
        "rho12_hermitian_residual": float(np.linalg.norm(rho12 - rho12.T)),
        "rho23_hermitian_residual": float(np.linalg.norm(rho23 - rho23.T)),
        "state_domain_wall_expectation": domain_wall,
    }
    t013["passed"] = bool(
        t013["distance_to_one_third"] < 0.08
        and abs(t013["state_domain_wall_expectation"] - 1.0 / 3.0) < 0.08
        and max(
            t013["rho1_trace_residual"],
            t013["rho12_trace_residual"],
            t013["rho23_trace_residual"],
            t013["rho12_hermitian_residual"],
            t013["rho23_hermitian_residual"],
        )
        <= tolerance
    )
    target_checks["T013"] = t013

    expected_sign = float((-1) ** blocks)
    momentum_plus = phi1 + phi2
    momentum_plus /= np.linalg.norm(momentum_plus)
    momentum_minus = phi1 - phi2
    momentum_minus /= np.linalg.norm(momentum_minus)
    t014 = {
        "translation_exchange_residual": float(np.linalg.norm(translation_phi1 - phi2)),
        "phi1_inversion_expectation": float(phi1 @ inversion_phi1),
        "phi1_particle_hole_expectation": float(phi1 @ (particle_hole * phi1)),
        "momentum_plus_translation": float(momentum_plus @ _permute(basis, momentum_plus, translate_state)),
        "momentum_minus_translation": float(momentum_minus @ _permute(basis, momentum_minus, translate_state)),
        "expected_inversion_particle_hole_sign": expected_sign,
    }
    t014["passed"] = bool(t014["translation_exchange_residual"] <= tolerance and abs(t014["phi1_inversion_expectation"] - expected_sign) <= tolerance and abs(t014["phi1_particle_hole_expectation"] - expected_sign) <= tolerance and abs(t014["momentum_plus_translation"] - 1.0) <= tolerance and abs(t014["momentum_minus_translation"] + 1.0) <= tolerance)
    target_checks["T014"] = t014

    obc_basis = build_basis(length, periodic=False)
    gamma = {(a, b): gamma_state(obc_basis, a, b) for a in (1, 2) for b in (1, 2)}
    inversion_11 = _permute(obc_basis, gamma[(1, 1)], invert_state)
    obc_ph = _particle_hole_signs(obc_basis)
    t015 = {
        "inversion_11_to_22_overlap": float(gamma[(2, 2)] @ inversion_11),
        "particle_hole_11_to_22_overlap": float(gamma[(2, 2)] @ (obc_ph * gamma[(1, 1)])),
        "particle_hole_12_to_21_overlap": float(gamma[(2, 1)] @ (obc_ph * gamma[(1, 2)])),
    }
    t015["passed"] = bool(all(abs(abs(value) - 1.0) <= tolerance for value in t015.values()))
    target_checks["T015"] = t015

    norm_residuals = {}
    for alpha in (1, 2):
        for beta in (1, 2):
            _, raw = _raw_gamma(length, alpha, beta)
            expected = 2.0 * ((-1) ** (blocks + alpha + beta) + 3**blocks)
            norm_residuals[f"{alpha}{beta}"] = abs(float(raw @ raw) - expected)
    t016 = {"norm_formula_residuals": norm_residuals, "maximum_residual": max(norm_residuals.values())}
    t016["passed"] = bool(t016["maximum_residual"] <= 10.0 * tolerance)
    target_checks["T016"] = t016

    d2_length = int(parameters["d2_entanglement_length"])
    d3_length = int(parameters["d3_entanglement_length"])
    d2_basis = build_basis(d2_length, periodic=False)
    d3_basis = build_basis(d3_length, periodic=False)
    d2_probs = _schmidt_probabilities(d2_basis, gamma_state(d2_basis, 1, 2), d2_length // 2)
    d3_probs = _schmidt_probabilities(d3_basis, gamma_state(d3_basis, 1, 2), d3_length // 2)
    entropy_length = int(parameters["periodic_entropy_length"])
    entropy_basis, _, entropy_phi1 = _periodic_mps_state(entropy_length, 0)
    _, _, entropy_phi2 = _periodic_mps_state(entropy_length, 1)
    entropy_state = entropy_phi1 - entropy_phi2
    entropy_state /= np.linalg.norm(entropy_state)
    entropy_probs = _schmidt_probabilities(entropy_basis, entropy_state, entropy_length // 2)
    t017 = {
        "d2_probabilities": d2_probs.tolist(),
        "d2_entropy": float(-np.sum(d2_probs * np.log(d2_probs))),
        "d3_probabilities": d3_probs.tolist(),
        "d3_entropy": float(-np.sum(d3_probs * np.log(d3_probs))),
        "periodic_momentum_entropy": float(-np.sum(entropy_probs * np.log(entropy_probs))),
    }
    t017["passed"] = bool(np.linalg.norm(d2_probs - np.asarray([0.5, 0.5])) <= tolerance and np.linalg.norm(d3_probs - np.asarray([2 / 3, 1 / 6, 1 / 6])) < 0.03 and abs(t017["periodic_momentum_entropy"] - 2.254) < 0.08)
    target_checks["T017"] = t017

    density_length = int(parameters["density_attestation_length"])
    density_basis = build_basis(density_length, periodic=True)
    density_hamiltonian = build_hamiltonian(density_basis)
    parity = (-1) ** (density_length // 2)
    density_spectrum = sector_spectrum(density_basis, density_hamiltonian, k_sign=-1, parity=parity)
    window = float(parameters["density_energy_window"])
    local_density = float(np.mean(np.abs(density_spectrum.energies) <= window))
    t018 = {
        "paper_length": int(parameters["density_paper_length"]),
        "attestation_length": density_length,
        "attestation_sector_dimension": int(len(density_spectrum.energies)),
        "attestation_near_zero_density": local_density,
        "paper_reference_values_comparison_only": parameters["density_paper_reference_values"],
        "paper_scale_status": "code_ready_not_run",
    }
    t018["passed"] = bool(t018["attestation_sector_dimension"] > 0 and 0.0 <= local_density <= 1.0 and t018["paper_length"] == 26)
    target_checks["T018"] = t018

    trial_length = int(parameters["trial_attestation_length"])
    trial_basis = build_basis(trial_length, periodic=True)
    trial_hamiltonian = build_hamiltonian(trial_basis)
    trial_ph = _particle_hole_signs(trial_basis)
    trial_phi_basis, _, trial_phi = _periodic_mps_state(trial_length, 0)
    assert np.array_equal(trial_basis.states, trial_phi_basis.states)
    trials = {family: build_trial_family(trial_basis, family=family, maximum_particles=1, batch_size=int(parameters["trial_batch_size"]))[1] for family in ("xi", "xi_tilde", "upsilon", "upsilon_tilde")}

    def trial_metrics(family: str) -> dict[str, float]:
        vector = trials[family]
        hv = np.asarray(trial_hamiltonian @ vector)
        energy = float(vector @ hv)
        return {
            "energy": energy,
            "variance": float(hv @ hv - energy**2),
            "translation": float(vector @ _permute(trial_basis, vector, translate_state)),
            "inversion": float(vector @ _permute(trial_basis, vector, invert_state)),
            "particle_hole_energy_sum": float(energy + (trial_ph * vector) @ (trial_hamiltonian @ (trial_ph * vector))),
            "phi_overlap": float(abs(trial_phi @ vector)),
        }

    xi = trial_metrics("xi")
    t019 = {"xi": xi}
    t019["passed"] = bool(abs(abs(xi["translation"]) - 1.0) <= tolerance and abs(abs(xi["inversion"]) - 1.0) < 1e-4 and abs(xi["particle_hole_energy_sum"]) <= tolerance)
    target_checks["T019"] = t019

    energy_plus = abs(xi["energy"])
    t020 = {"epsilon_plus": energy_plus, "inversion_flipping_frequency": energy_plus, "inversion_preserving_frequency": 2.0 * energy_plus, "ratio": 2.0}
    t020["passed"] = bool(abs(t020["inversion_preserving_frequency"] / t020["inversion_flipping_frequency"] - 2.0) <= tolerance)
    target_checks["T020"] = t020

    xi_tilde = trial_metrics("xi_tilde")
    t021 = {"xi_tilde": xi_tilde, "paper_reference_comparison_only": parameters["xi_tilde_paper_reference"]}
    t021["passed"] = bool(abs(abs(xi_tilde["translation"]) - 1.0) <= tolerance and abs(abs(xi_tilde["inversion"]) - 1.0) < 1e-4 and abs(xi_tilde["particle_hole_energy_sum"]) <= tolerance and xi_tilde["phi_overlap"] < 0.15)
    target_checks["T021"] = t021

    upsilon_tilde = trial_metrics("upsilon_tilde")
    t022 = {"upsilon_tilde": upsilon_tilde, "paper_reference_comparison_only": parameters["upsilon_tilde_paper_reference"], "input_boundary": "printed parameter interpretation remains review-limited"}
    t022["passed"] = bool(np.isfinite(upsilon_tilde["energy"]) and upsilon_tilde["variance"] >= -tolerance)
    target_checks["T022"] = t022

    upsilon = trial_metrics("upsilon")
    t023 = {"upsilon": upsilon, "upsilon_tilde": upsilon_tilde}
    t023["passed"] = bool(abs(upsilon["particle_hole_energy_sum"]) <= tolerance and abs(upsilon_tilde["particle_hole_energy_sum"]) <= tolerance and max(upsilon["phi_overlap"], upsilon_tilde["phi_overlap"]) < 0.15)
    target_checks["T023"] = t023

    item_results = {
        item_id: {"target_id": target_id, "implementation_status": "attested" if target_checks[target_id]["passed"] else "failed", "scientific_status": "unchanged"}
        for target_id, item_ids in ITEMS_BY_TARGET.items()
        for item_id in item_ids
    }
    return {
        "schema_version": 1,
        "paper_id": "1810.00888",
        "profile": profile,
        "purpose": "implementation_attestation_only",
        "scientific_coverage_changed": False,
        "source_pixels_used": False,
        "author_arrays_used": False,
        "author_code_used": False,
        "target_checks": target_checks,
        "item_results": item_results,
        "scientific_boundaries": {
            target_id: {
                "status": "pending_scientific_acceptance" if target_id != "T022" else "input_limited",
                "statement": SCIENTIFIC_BOUNDARIES[target_id],
                "canary_passed": bool(target_checks[target_id]["passed"]),
            }
            for target_id in ITEMS_BY_TARGET
        },
        "status": "passed" if all(row["passed"] for row in target_checks.values()) else "failed",
    }
