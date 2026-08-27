"""Low-cost, clean-room implementation campaign for the RMP target surface.

The campaign proves that every declared target has an executable scientific
path.  It deliberately does not promote reduced calculations to paper-scale
evidence.  The only non-computing result is T030, whose COMSOL input boundary
is emitted as a machine-readable blocked artifact.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np
from scipy import linalg

from .completion_repairs import small_matrix_multilevel_shift_check
from .cqed_reproduction import (
    annihilation,
    black_box_kerr,
    discretized_bath_hamiltonians,
    jc_analytic_energies,
    jc_block,
    lindblad_rhs,
    longitudinal_analytic_energy,
    longitudinal_block,
    passive_one_port_response,
    thermal_oscillator_evolution,
    transmon_coupling,
    transmon_coupling_via_alpha,
    transmon_dispersive_energy,
    transmon_dispersive_shifts,
)
from .full_rmp_reproduction import (
    binomial_code_metrics,
    bloch_excited_population,
    cat_state_coefficients,
    cpw_transmission,
    dispersive_pointer_trajectory,
    dispersive_steady_response,
    drag_pi_pulse,
    duffing_cavity_pull,
    fock_state_wigner,
    linear_cqed_response,
    one_excitation_dynamics,
    photon_number_split_spectrum,
    squeezed_quadrature_variance,
    squeezed_vacuum_wigner,
    thermal_jc_spectrum,
    transmon_eigensystem,
    transmon_phase_wavefunctions,
)


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    status: str
    scientific_scale: str
    data: dict[str, Any]
    checks: dict[str, bool]
    boundary: dict[str, Any] | None = None

    def as_json(self, item_ids: list[str]) -> dict[str, Any]:
        payload = asdict(self)
        payload["item_ids"] = item_ids
        payload["checks_passed"] = all(self.checks.values())
        return _json_safe(payload)


def run_campaign(config: dict[str, Any], profile_name: str) -> dict[str, dict[str, Any]]:
    """Run one reduced implementation proof per target in the frozen item map."""

    if config.get("paper_id") != "2005.12667":
        raise ValueError("configuration paper_id does not match this case")
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise ValueError(f"unknown profile: {profile_name}")
    profile = profiles[profile_name]
    target_items = config.get("target_items")
    if not isinstance(target_items, dict) or not target_items:
        raise ValueError("target_items must be a non-empty object")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != len(set(flattened)):
        raise ValueError("each atomic item must belong to exactly one target")

    runners: dict[str, Callable[[dict[str, Any], dict[str, Any]], TargetResult]] = {
        "T001": _t001_jaynes_cummings,
        "T002": _t002_dispersive,
        "T003": _t003_quantization_claims,
        "T004": _t004_open_system_claims,
        "T005": _t005_cpw,
        "T006": _t006_transmon_states,
        "T007": _t007_charge_dispersion,
        "T008": _t008_pointer_states,
        "T009": _t009_cavity_response,
        "T010": _t010_coupling_regimes,
        "T011": _t011_vacuum_rabi,
        "T012": _t012_avoided_crossing,
        "T013": _t013_bloch_spectroscopy,
        "T014": _t014_ac_stark,
        "T015": _t015_drive_mapped_pull,
        "T016": _t016_two_vs_three_level,
        "T017": _t017_error_code,
        "T018": _t018_cat_wigner,
        "T019": _t019_fock_wigner,
        "T020": _t020_squeezing,
        "T030": _t030_comsol_boundary,
        "T032": _t032_three_mode_spectrum,
        "T042": _t042_master_equation,
    }
    unknown = sorted(set(target_items) - set(runners))
    if unknown:
        raise ValueError(f"no campaign runner for targets: {unknown}")
    paper_parameters = config.get("paper_parameters", {})
    return {
        target_id: runners[target_id](profile, paper_parameters).as_json(items)
        for target_id, items in target_items.items()
    }


def _t001_jaynes_cummings(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    coupling = float(profile["coupling"])
    detunings = np.linspace(-1.0, 1.0, int(profile["grid_points"]))
    residuals = []
    branches = []
    for detuning in detunings:
        matrix = jc_block(1, 1.0, 1.0 + detuning, coupling)
        exact = np.linalg.eigvalsh(matrix)
        analytic = np.asarray(jc_analytic_energies(1, 1.0, 1.0 + detuning, coupling))
        residuals.append(float(np.max(np.abs(exact - analytic))))
        branches.append([float(detuning), *exact.tolist()])
    return TargetResult("T001", "passed", "reduced_scale", {"branches": branches}, {"analytic_diagonalization": max(residuals) < 1e-12})


def _t002_dispersive(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    coupling = float(profile["dispersive_coupling"])
    detuning = float(profile["dispersive_detuning"])
    anharmonicity = float(profile["anharmonicity"])
    lamb, chi = transmon_dispersive_shifts(2, coupling, detuning, anharmonicity)
    rows = [
        {
            "level": level,
            "photon": photon,
            "energy": transmon_dispersive_energy(level, photon, 5.0, 5.0 + detuning, anharmonicity, lamb, chi),
        }
        for level in range(3)
        for photon in range(3)
    ]
    finite = all(np.isfinite(row["energy"]) for row in rows)
    return TargetResult("T002", "passed", "reduced_scale", {"energies": rows, "lamb": lamb, "chi": chi}, {"finite_spectrum": finite, "nonzero_cavity_pull": bool(np.max(np.abs(chi)) > 0)})


def _t003_quantization_claims(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    coupling_a = transmon_coupling(7.0, 0.08, 50.0, 50.0)
    coupling_b = transmon_coupling_via_alpha(7.0, 0.08, 50.0, 50.0)
    black_box = black_box_kerr([5.0, 7.0], [0.08, 0.12], 20.0)
    block = longitudinal_block(10, 5.0, 6.0, 0.12, 1)
    exact = np.linalg.eigvalsh(block)[:3]
    analytic = np.asarray([longitudinal_analytic_energy(n, 5.0, 6.0, 0.12, 1) for n in range(3)])
    small_matrix = small_matrix_multilevel_shift_check()
    checks = {
        "coupling_forms_agree": abs(coupling_a - coupling_b) < 1e-12,
        "kerr_matrix_symmetric": bool(np.allclose(black_box.chi, black_box.chi.T)),
        "longitudinal_square_completion": float(np.max(np.abs(exact - analytic))) < 2e-10,
        "multilevel_small_matrix_finite": bool(np.isfinite(small_matrix["max_spacing_error"])),
    }
    return TargetResult("T003", "passed", "analytic_check", {"coupling_residual": abs(coupling_a - coupling_b), "small_matrix": small_matrix}, checks)


def _t004_open_system_claims(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    matrices = discretized_bath_hamiltonians()
    detuning = np.linspace(-2.0, 2.0, int(profile["grid_points"]))
    _, reflected = passive_one_port_response(detuning, 1.0)
    states = thermal_oscillator_evolution(4, 1.0, 0.2, 0.1, 1, np.linspace(0.0, 2.0, 9))
    traces = np.trace(states, axis1=1, axis2=2)
    minimum_eigenvalue = min(float(np.min(np.linalg.eigvalsh((rho + rho.conj().T) / 2.0))) for rho in states)
    literal = matrices["eq67_arxiv_literal"]
    published = matrices["eq67_published_correction"]
    checks = {
        "thermal_trace": float(np.max(np.abs(traces - 1.0))) < 1e-9,
        "thermal_positivity": minimum_eigenvalue > -1e-9,
        "passive_unit_modulus": float(np.max(np.abs(np.abs(reflected) - 1.0))) < 1e-12,
        "published_rwa_hermitian": bool(np.allclose(published, published.conj().T)),
        "arxiv_sign_difference_exposed": not bool(np.allclose(literal, literal.conj().T)),
    }
    return TargetResult("T004", "passed", "analytic_check", {"minimum_density_eigenvalue": minimum_eigenvalue}, checks)


def _t005_cpw(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    frequency = np.linspace(1.0, 31.0, 3001)
    response = cpw_transmission(frequency, 10.0, 400.0, 3)
    peak_errors = []
    for center in (10.0, 20.0, 30.0):
        mask = np.abs(frequency - center) <= 0.2
        peak_errors.append(abs(float(frequency[mask][np.argmax(response[mask])]) - center))
    return TargetResult("T005", "passed", "paper_subset", {"frequency": frequency, "response": response}, {"harmonic_peaks": max(peak_errors) < 0.02})


def _t006_transmon_states(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    cutoff = int(profile["charge_cutoff"])
    energies, vectors = transmon_eigensystem(cutoff, 1.0, 50.0, 0.0)
    phase = np.linspace(-np.pi, np.pi, int(profile["grid_points"]))
    wavefunctions = transmon_phase_wavefunctions(vectors, phase, 3)
    norms = np.trapezoid(np.abs(wavefunctions) ** 2, phase, axis=0)
    return TargetResult("T006", "passed", "reduced_scale", {"phase": phase, "energies": energies[:3], "probabilities": np.abs(wavefunctions) ** 2}, {"wavefunction_normalization": float(np.max(np.abs(norms - 1.0))) < 2e-5, "negative_anharmonicity": bool((energies[2] - energies[1]) < (energies[1] - energies[0]))})


def _t007_charge_dispersion(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    cutoff = int(profile["charge_cutoff"])
    offset = np.linspace(-0.5, 0.5, int(profile["grid_points"]))
    ratios = paper["fig6_ej_over_ec"]
    data: dict[str, Any] = {}
    dispersions = []
    for ratio in ratios:
        branches = np.asarray([transmon_eigensystem(cutoff, 1.0, float(ratio), value)[0][:3] for value in offset])
        branches -= branches[:, :1]
        data[str(ratio)] = branches
        dispersions.append(float(np.ptp(branches[:, 1])))
    return TargetResult("T007", "passed", "reduced_scale", {"offset_charge": offset, "branches": data}, {"charge_periodicity": all(np.allclose(values[0], values[-1], atol=1e-9) for values in data.values()), "dispersion_suppression": dispersions[-1] < dispersions[0]})


def _t008_pointer_states(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    time = np.linspace(0.0, 20.0, int(profile["time_points"]))
    results = {}
    steady_errors = []
    for ratio in (0.2, 1.0, 10.0):
        chi = 0.5 * ratio
        drive = np.sqrt(chi**2 + 0.25)
        ground, excited = dispersive_pointer_trajectory(time, 1.0, chi, drive)
        results[str(ratio)] = {"ground": ground, "excited": excited}
        steady_errors.extend([abs(abs(ground[-1]) ** 2 - 1.0), abs(abs(excited[-1]) ** 2 - 1.0)])
    return TargetResult("T008", "passed", "reduced_scale", {"time": time, "trajectories": results}, {"steady_pointer_norm": max(steady_errors) < 2e-3})


def _t009_cavity_response(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    detuning = np.linspace(-4.0, 4.0, int(profile["grid_points"]))
    ground, excited = dispersive_steady_response(detuning, 1.0, 1.0)
    return TargetResult("T009", "passed", "reduced_scale", {"detuning": detuning, "ground": ground, "excited": excited}, {"finite": bool(np.all(np.isfinite(ground)) and np.all(np.isfinite(excited))), "state_exchange_amplitude_symmetry": bool(np.allclose(np.abs(ground), np.abs(excited[::-1])))})


def _t010_coupling_regimes(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    time = np.linspace(0.0, 12.0, int(profile["time_points"]))
    qubit, cavity = one_excitation_dynamics(time, 1.0, 0.2, 0.1, "qubit")
    detuning = np.linspace(-2.0, 2.0, int(profile["grid_points"]))
    spectrum = thermal_jc_spectrum(detuning, 1.0, 0.08, 0.35, 4)
    return TargetResult("T010", "passed", "reduced_scale", {"time": time, "qubit_population": qubit, "cavity_population": cavity, "detuning": detuning, "thermal_spectrum": spectrum}, {"probabilities_nonnegative": bool(np.min(qubit) >= 0 and np.min(cavity) >= 0), "loss_contract": bool(np.max(qubit + cavity) <= 1.0 + 1e-10), "spectrum_normalized": abs(float(np.max(spectrum)) - 1.0) < 1e-12})


def _t011_vacuum_rabi(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    detuning = np.linspace(-1.5, 1.5, int(profile["spectrum_points"]))
    power = np.abs(linear_cqed_response(detuning, 0.0, 1.0, 0.02, 0.01)) ** 2
    left = float(detuning[detuning < 0][np.argmax(power[detuning < 0])])
    right = float(detuning[detuning > 0][np.argmax(power[detuning > 0])])
    return TargetResult("T011", "passed", "paper_subset", {"detuning": detuning, "power": power}, {"doublet_split": abs((right - left) - 2.0) < 0.03})


def _t012_avoided_crossing(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    probe = np.linspace(-1.5, 1.5, int(profile["grid_points"]))
    qubit = np.linspace(-1.0, 1.0, max(11, int(profile["grid_points"]) // 2))
    response = np.asarray([np.abs(linear_cqed_response(probe, offset, 0.5, 0.02, 0.01)) ** 2 for offset in qubit])
    resonant = response[int(np.argmin(np.abs(qubit)))]
    left = float(probe[probe < 0][np.argmax(resonant[probe < 0])])
    right = float(probe[probe > 0][np.argmax(resonant[probe > 0])])
    return TargetResult("T012", "passed", "reduced_scale", {"probe_detuning": probe, "qubit_cavity_detuning": qubit, "power": response}, {"finite_map": bool(np.all(np.isfinite(response))), "resonance_split_visible": abs((right - left) - 1.0) < 0.08})


def _t013_bloch_spectroscopy(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    detuning = np.linspace(-2.0, 2.0, int(profile["spectrum_points"]))
    curves = {str(rabi): bloch_excited_population(detuning, rabi, 0.1, 0.15) for rabi in (0.1, 0.5, 1.0)}
    return TargetResult("T013", "passed", "reduced_scale", {"detuning": detuning, "population": curves}, {"population_bound": all(float(np.max(curve)) < 0.5 for curve in curves.values()), "power_broadening": _support_width(curves["1.0"]) > _support_width(curves["0.1"])})


def _t014_ac_stark(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    """Recreate both Fig. 25 caption parameter families.

    The former canary used arbitrary mean photon numbers and therefore could
    not test the published drive-amplitude contract.  Here the mean
    occupations are derived from the caption's drive conditions; source
    pixels are not used.
    """

    parameters = paper["fig25"]
    points = int(profile["spectrum_points"])
    weak_detuning = np.linspace(-2.0, 5.0, points)
    weak_spectra: dict[str, Any] = {}
    weak_mean_photons: dict[str, float] = {}
    for epsilon in parameters["weak_drive_amplitudes_MHz"]:
        mean = float(epsilon) ** 2 / (
            float(parameters["weak_drive_detuning_from_pulled_resonance_MHz"]) ** 2
            + (float(parameters["kappa_MHz"]) / 2.0) ** 2
        )
        weak_mean_photons[str(epsilon)] = mean
        weak_spectra[str(epsilon)] = photon_number_split_spectrum(
            weak_detuning,
            float(parameters["weak_chi_MHz"]),
            float(parameters["rabi_MHz"]),
            float(parameters["gamma1_MHz"]),
            float(parameters["gamma_phi_MHz"]),
            float(parameters["kappa_MHz"]),
            mean,
            40,
        )

    strong_detuning = np.linspace(-12.0, 72.0, points)
    strong_mean = float(parameters["strong_drive_amplitude_MHz"]) ** 2 / (
        float(parameters["strong_drive_detuning_from_pulled_resonance_MHz"]) ** 2
        + (float(parameters["kappa_MHz"]) / 2.0) ** 2
    )
    strong_spectrum = photon_number_split_spectrum(
        strong_detuning,
        float(parameters["strong_chi_MHz"]),
        float(parameters["rabi_MHz"]),
        float(parameters["gamma1_MHz"]),
        float(parameters["gamma_phi_MHz"]),
        float(parameters["kappa_MHz"]),
        strong_mean,
        20,
    )
    arrays = [*weak_spectra.values(), strong_spectrum]
    checks = {
        "caption_parameters_consumed": bool(
            np.isclose(strong_mean, 4.0)
            and list(weak_mean_photons) == ["0.0", "0.2", "0.4"]
        ),
        "finite_nonnegative_spectra": all(
            bool(np.all(np.isfinite(curve)) and np.min(curve) >= 0.0)
            for curve in arrays
        ),
        "weak_drive_occupation_monotone": bool(
            np.all(np.diff(list(weak_mean_photons.values())) > 0.0)
        ),
    }
    return TargetResult(
        "T014",
        "passed",
        "paper_subset",
        {
            "weak_panel": {
                "detuning_MHz": weak_detuning,
                "mean_photons_by_epsilon_MHz": weak_mean_photons,
                "spectra": weak_spectra,
            },
            "strong_panel": {
                "detuning_MHz": strong_detuning,
                "mean_photons": strong_mean,
                "spectrum": strong_spectrum,
            },
        },
        checks,
    )


def _t015_drive_mapped_pull(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    maximum = int(profile["pull_maximum_photon"])
    dimensions = [int(value) for value in profile["pull_transmon_dimensions"]]
    curves: dict[str, Any] = {}
    checks: dict[str, bool] = {}
    for dimension in dimensions:
        pulls = duffing_cavity_pull(maximum + 2, dimension, paper["omega_r_GHz"], paper["omega_01_GHz"], paper["coupling_GHz"], paper["anharmonicity_GHz"], maximum)
        branches = {str(level): values for level, values in pulls.items()}
        curves[str(dimension)] = branches
        checks[f"dimension_{dimension}_finite"] = all(np.all(np.isfinite(values)) for values in branches.values())
    checks["photon_axis_complete"] = maximum >= 2
    return TargetResult(
        "T015",
        "passed",
        "parameterized_model",
        {
            "photon_number": np.arange(maximum + 1, dtype=float),
            "effective_frequency": curves,
            "paper_drive_axis_boundary": {
                "status": "input_required",
                "required_inputs": [
                    "figure-specific cavity linewidth",
                    "measurement-drive frequency or detuning",
                    "steady-state drive-to-photon response convention",
                ],
                "source_trace": "paper-source/CircuitQED_RMP.tex:1690-1696",
            },
        },
        checks,
    )


def _t016_two_vs_three_level(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    times = np.linspace(float(profile["minimum_gate_time"]), float(profile["maximum_gate_time"]), int(profile["gate_time_points"]))
    anharmonicity = 2.0 * np.pi * float(paper["anharmonicity_GHz"])
    two_level_error = []
    three_level_gaussian_error = []
    three_level_drag_error = []
    three_level_gaussian_leakage = []
    three_level_drag_leakage = []
    norm_errors = []
    for gate_time in times:
        ideal = drag_pi_pulse(
            float(gate_time), anharmonicity, False, dimension=2
        )
        gaussian = drag_pi_pulse(
            float(gate_time), anharmonicity, False, dimension=3
        )
        drag = drag_pi_pulse(
            float(gate_time), anharmonicity, True, dimension=3
        )
        two_level_error.append(1.0 - ideal.target_population)
        three_level_gaussian_error.append(1.0 - gaussian.target_population)
        three_level_drag_error.append(1.0 - drag.target_population)
        three_level_gaussian_leakage.append(gaussian.leakage)
        three_level_drag_leakage.append(drag.leakage)
        norm_errors.extend([ideal.norm_error, gaussian.norm_error, drag.norm_error])
    checks = {
        "two_and_three_level_models_executed": bool(
            np.max(np.abs(np.asarray(three_level_gaussian_error) - two_level_error))
            > 1e-7
        ),
        "drag_branch_executed": bool(
            np.max(np.abs(np.asarray(three_level_drag_error) - three_level_gaussian_error))
            > 1e-7
        ),
        "all_branches_norm_preserving": max(norm_errors) < 5e-8,
    }
    return TargetResult(
        "T016",
        "passed",
        "parameterized_model",
        {
            "gate_time": times,
            "two_level_gaussian_error": two_level_error,
            "three_level_gaussian_error": three_level_gaussian_error,
            "three_level_drag_error": three_level_drag_error,
            "three_level_gaussian_leakage": three_level_gaussian_leakage,
            "three_level_drag_leakage": three_level_drag_leakage,
            "paper_parameter_boundary": {
                "status": "input_required",
                "required_inputs": [
                    "Chow et al. pulse-width schedule",
                    "decoherence model and fitted rates",
                    "randomized-benchmarking error map",
                ],
                "source_trace": "paper-source/CircuitQED_RMP.tex:1752-1760",
            },
        },
        checks,
    )


def _t017_error_code(_: dict[str, Any], __: dict[str, Any]) -> TargetResult:
    metrics = binomial_code_metrics()
    return TargetResult("T017", "passed", "analytic_check", metrics, {"knill_laflamme": max(metrics["identity_residual"], metrics["equal_loss_residual"], metrics["logical_loss_residual"]) < 1e-12})


def _t018_cat_wigner(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    grid = np.linspace(-5.0, 5.0, int(profile["wigner_points"]))
    states = {"two": cat_state_coefficients(2.0, int(profile["fock_dimension"]), 2), "four": cat_state_coefficients(2.0, int(profile["fock_dimension"]), 4)}
    wigners = {key: fock_state_wigner(state, grid, grid) for key, state in states.items()}
    return TargetResult("T018", "passed", "reduced_scale", {"grid": grid, "wigner": wigners}, {"negative_interference": all(float(np.min(value)) < -0.01 for value in wigners.values())})


def _t019_fock_wigner(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    grid = np.linspace(-4.0, 4.0, int(profile["wigner_points"]))
    dimension = max(7, int(profile["fock_dimension"]))
    state = np.zeros(dimension, dtype=np.complex128)
    state[[0, 3, 6]] = np.exp(1j * np.asarray([0.0, np.pi / 4.0, np.pi / 2.0])) / np.sqrt(3.0)
    wigner = fock_state_wigner(state, grid, grid)
    return TargetResult("T019", "passed", "reduced_scale", {"grid": grid, "wigner": wigner}, {"state_normalized": abs(float(np.vdot(state, state).real) - 1.0) < 1e-12, "finite_wigner": bool(np.all(np.isfinite(wigner)))})


def _t020_squeezing(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    grid = np.linspace(-4.0, 4.0, int(profile["wigner_points"]))
    phase = np.linspace(0.0, 2.0 * np.pi, int(profile["grid_points"]))
    wigner = squeezed_vacuum_wigner(grid, grid, 0.75, np.pi / 2.0)
    variance = {str(r): squeezed_quadrature_variance(phase, r, np.pi) for r in (0.5, 1.0, 1.5)}
    return TargetResult("T020", "passed", "reduced_scale", {"grid": grid, "wigner": wigner, "phase": phase, "variance": variance}, {"minimum_uncertainty": all(abs(float(np.min(v) * np.max(v)) - 0.25) < 5e-3 for v in variance.values())})


def _t030_comsol_boundary(_: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    missing = paper["comsol_required_inputs"]
    return TargetResult(
        "T030",
        "blocked_input",
        "input_schema_only",
        {"mode_labels": ["TE110", "TE210", "TE120", "TE220"]},
        {"schema_complete": len(missing) >= 5},
        boundary={
            "blocker": "indispensable_input_unavailable",
            "required_fields": missing,
            "prohibited_substitutions": ["source pixels", "digitized field arrays", "guessed COMSOL project"],
            "resume_condition": "Provide an independently specified geometry/material/boundary/port/mesh project.",
        },
    )


def _t032_three_mode_spectrum(profile: dict[str, Any], paper: dict[str, Any]) -> TargetResult:
    dimensions = tuple(int(value) for value in profile["fig30_dimensions"])
    sweep = np.linspace(float(profile["fig30_sweep"][0]), float(profile["fig30_sweep"][1]), int(profile["fig30_sweep_points"]))
    spectra = []
    conservation = []
    for omega_2 in sweep:
        hamiltonian, total_number = _three_mode_hamiltonian(
            dimensions,
            paper["omega_q1_GHz"],
            float(omega_2),
            paper["omega_r_GHz"],
            paper["anharmonicity_1_GHz"],
            paper["anharmonicity_2_GHz"],
            paper["g1_GHz"],
            paper["g2_GHz"],
        )
        eigenvalues, eigenvectors = linalg.eigh(hamiltonian)
        number_expectation = np.real(np.sum(np.conjugate(eigenvectors) * (total_number @ eigenvectors), axis=0))
        conservation.append(float(np.linalg.norm(hamiltonian @ total_number - total_number @ hamiltonian)))
        spectra.append({
            "omega_q2_GHz": float(omega_2),
            "one_excitation": eigenvalues[np.abs(number_expectation - 1.0) < 1e-7].tolist(),
            "two_excitation": eigenvalues[np.abs(number_expectation - 2.0) < 1e-7].tolist(),
        })
    return TargetResult("T032", "passed", "reduced_scale", {"dimensions": dimensions, "spectra": spectra}, {"number_conserved": max(conservation) < 1e-10, "both_manifolds_present": all(row["one_excitation"] and row["two_excitation"] for row in spectra)})


def _t042_master_equation(profile: dict[str, Any], _: dict[str, Any]) -> TargetResult:
    detuning = np.linspace(-1.5, 1.5, int(profile["spectrum_points"]))
    curves: dict[str, Any] = {}
    maximum_population_residual = 0.0
    maximum_phase_residual = 0.0
    maximum_width_residual = 0.0
    trace_residual = 0.0
    gamma1 = 0.1
    gamma_phi = 0.1
    gamma2 = 0.5 * gamma1 + gamma_phi
    for rabi in (0.1, 0.5, 1.0):
        numerical_population = []
        for delta in detuning:
            rho = _two_level_steady_state(
                float(delta), rabi, gamma1, gamma_phi
            )
            numerical_population.append(float(rho[1, 1].real))
            trace_residual = max(trace_residual, abs(complex(np.trace(rho)) - 1.0))
        numerical = np.asarray(numerical_population)
        analytic = bloch_excited_population(
            detuning, rabi, gamma1, gamma2
        )
        # Fig. 24 defines the readout phase from <sigma_z>, not from the
        # off-diagonal density-matrix phase.  The caption fixes 2 chi/kappa=1.
        phase_numeric = np.arctan(2.0 * numerical - 1.0)
        phase_analytic = np.arctan(2.0 * analytic - 1.0)
        width_numeric = _fwhm(detuning, numerical)
        width_analytic = 2.0 * np.sqrt(
            gamma2**2 + rabi**2 * gamma2 / gamma1
        )
        maximum_population_residual = max(
            maximum_population_residual,
            float(np.max(np.abs(numerical - analytic))),
        )
        maximum_phase_residual = max(
            maximum_phase_residual,
            float(np.max(np.abs(phase_numeric - phase_analytic))),
        )
        maximum_width_residual = max(
            maximum_width_residual,
            abs(width_numeric - width_analytic),
        )
        curves[str(rabi)] = {
            "population_numeric": numerical_population,
            "population_analytic": analytic,
            "readout_phase_numeric": phase_numeric,
            "readout_phase_analytic": phase_analytic,
            "fwhm_numeric": width_numeric,
            "fwhm_analytic": width_analytic,
        }
    return TargetResult(
        "T042",
        "passed",
        "paper_subset",
        {"detuning": detuning, "curves": curves},
        {
            "steady_state_trace": trace_residual < 1e-10,
            "numeric_analytic_population": maximum_population_residual < 5e-8,
            "numeric_analytic_phase": maximum_phase_residual < 5e-8,
            "numeric_analytic_fwhm": maximum_width_residual < 0.03,
        },
    )


def _fwhm(axis: np.ndarray, values: np.ndarray) -> float:
    half_maximum = 0.5 * float(np.max(values))
    selected = np.flatnonzero(values >= half_maximum)
    if len(selected) < 2:
        raise ValueError("spectrum grid does not resolve the FWHM")
    return float(axis[selected[-1]] - axis[selected[0]])


def _three_mode_hamiltonian(
    dimensions: tuple[int, int, int],
    omega_1: float,
    omega_2: float,
    omega_r: float,
    alpha_1: float,
    alpha_2: float,
    g_1: float,
    g_2: float,
) -> tuple[np.ndarray, np.ndarray]:
    d1, d2, dr = dimensions
    identity_1, identity_2, identity_r = np.eye(d1), np.eye(d2), np.eye(dr)
    b1 = np.kron(np.kron(annihilation(d1), identity_2), identity_r)
    b2 = np.kron(np.kron(identity_1, annihilation(d2)), identity_r)
    cavity = np.kron(np.kron(identity_1, identity_2), annihilation(dr))
    n1, n2, nr = b1.conj().T @ b1, b2.conj().T @ b2, cavity.conj().T @ cavity
    hamiltonian = (
        omega_1 * n1
        + omega_2 * n2
        + omega_r * nr
        - 0.5 * alpha_1 * (b1.conj().T @ b1.conj().T @ b1 @ b1)
        - 0.5 * alpha_2 * (b2.conj().T @ b2.conj().T @ b2 @ b2)
        + g_1 * (b1.conj().T @ cavity + b1 @ cavity.conj().T)
        + g_2 * (b2.conj().T @ cavity + b2 @ cavity.conj().T)
    )
    return np.asarray(hamiltonian), np.asarray(n1 + n2 + nr)


def _two_level_steady_state(detuning: float, rabi: float, gamma1: float, gamma_phi: float) -> np.ndarray:
    lowering = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    number = lowering.conj().T @ lowering
    hamiltonian = detuning * number + 0.5 * rabi * (lowering + lowering.conj().T)
    collapse = [np.sqrt(gamma1) * lowering, np.sqrt(gamma_phi / 2.0) * np.diag([1.0, -1.0])]
    generator = np.column_stack(
        [
            lindblad_rhs(
                np.eye(4, dtype=np.complex128)[:, index].reshape(2, 2),
                hamiltonian,
                collapse,
            ).reshape(-1)
            for index in range(4)
        ]
    )
    system = generator.copy()
    rhs = np.zeros(4, dtype=np.complex128)
    system[-1] = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128)
    rhs[-1] = 1.0
    rho = np.linalg.solve(system, rhs).reshape(2, 2)
    return (rho + rho.conj().T) / 2.0


def _support_width(values: np.ndarray) -> int:
    array = np.asarray(values, dtype=float)
    return int(np.count_nonzero(array >= 0.5 * float(np.max(array))))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        if np.iscomplexobj(value):
            return {"real": value.real.tolist(), "imag": value.imag.tolist()}
        return value.tolist()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, np.generic):
        return value.item()
    return value
