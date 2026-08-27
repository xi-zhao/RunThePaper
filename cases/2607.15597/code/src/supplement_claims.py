"""Independent calculations for uncovered supplemental quantitative claims."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from gate_model import (
    GateParameters,
    branch_forces,
    branch_phases,
    concurrence,
    decay_infidelity,
    reduced_spin_state,
    rotated_basis_populations,
)
from ion_chain import axial_modes, mode_trajectory, optimize_toggle_schedule


HBAR = 1.054_571_817e-34
PLANCK = 6.626_070_15e-34
LIGHT_SPEED = 299_792_458.0
VACUUM_PERMITTIVITY = 8.854_187_812_8e-12
POLARIZABILITY_ATOMIC_UNIT = 1.648_777_274_36e-41
BOHR_MAGNETON_OVER_HZ = 13.996_245_55e9


def multimode_spin_dynamics(
    times: Iterable[float], params: GateParameters = GateParameters()
) -> list[dict[str, float]]:
    """Reduced-spin feature model using the independently optimized 10-mode schedule.

    The schedule controls motional overlap.  The matched-force branch phases are
    evaluated from the printed geometric-phase invariant.  This is a runnable
    paper-subset model, not a replacement for the unpublished full open-system
    calculation.
    """

    _positions, frequencies, eigenvectors = axial_modes(10)
    schedule = optimize_toggle_schedule(frequencies, segment_count=25, restarts=4)
    edge_participation = eigenvectors[0, :]
    force = branch_forces(params.coupling_ratio)[:, 0]
    rows: list[dict[str, float]] = []
    for raw_time in times:
        time = float(raw_time)
        if not 0.0 <= time <= 2.0:
            raise ValueError("multimode time must lie in [0, 2]")
        local_time = time % 1.0
        if time > 0.0 and math.isclose(local_time, 0.0, abs_tol=1e-14):
            local_time = 1.0
        trajectory = np.asarray(
            [
                mode_trajectory(np.asarray([local_time]), float(frequency), schedule)[0]
                for frequency in frequencies
            ]
        )
        displacement = (
            force[:, np.newaxis]
            * edge_participation[np.newaxis, :]
            * trajectory[np.newaxis, :]
        )
        phases = branch_phases(time, params)
        state = np.empty((4, 4), dtype=complex)
        for row in range(4):
            for column in range(4):
                delta = displacement[row] - displacement[column]
                overlap = np.exp(-0.5 * np.vdot(delta, delta).real)
                state[row, column] = 0.25 * overlap * np.exp(
                    1j * (phases[row] - phases[column])
                )
        state = 0.5 * (state + state.conj().T)
        populations = rotated_basis_populations(state)
        rows.append(
            {
                "t_over_T": time,
                **populations,
                "concurrence": concurrence(state),
                "trace_error": float(abs(np.trace(state) - 1.0)),
                "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(state))),
                "max_mode_residual": float(np.max(np.abs(displacement))),
            }
        )
    return rows


def table_s3_error_budget(gate_time_us: float = 5.0) -> list[dict[str, object]]:
    """Separate the independently calculable row from publication-only bounds."""

    decay = float(decay_infidelity(gate_time_us, 100.0))
    rows: list[dict[str, object]] = [
        {
            "component": "rydberg_decay",
            "upper_infidelity": decay,
            "provenance": "independent_formula",
        },
        {"component": "thermal_position", "upper_infidelity": 6e-4, "provenance": "paper_bound"},
        {"component": "trap_frequency_mismatch", "upper_infidelity": 1e-5, "provenance": "paper_bound"},
        {"component": "motional_heating", "upper_infidelity": 5e-4, "provenance": "paper_bound"},
        {"component": "magnus_intensity_noise", "upper_infidelity": 2e-4, "provenance": "paper_bound"},
        {"component": "photon_scattering", "upper_infidelity": 1e-4, "provenance": "paper_upper_bound"},
        {"component": "micromotion", "upper_infidelity": 1e-4, "provenance": "paper_bound"},
        {"component": "ac_stark_crosstalk", "upper_infidelity": 1e-5, "provenance": "paper_upper_bound"},
    ]
    total = sum(float(row["upper_infidelity"]) for row in rows)
    rows.append(
        {
            "component": "upper_bound_sum",
            "upper_infidelity": total,
            "provenance": "independent_arithmetic_over_mixed_inputs",
        }
    )
    return rows


def table_s4_toggle_sweep() -> list[dict[str, object]]:
    """Test both the printed table segment counts and the stated 2N+5 rule."""

    paper_rows = {
        1: (5, 80.0, 4.9, 0.975),
        2: (7, 120.0, 4.9, 0.975),
        5: (13, 240.0, 4.8, 0.975),
        10: (17, 320.0, 4.7, 0.974),
    }
    rows: list[dict[str, object]] = []
    for number_of_ions, (paper_segments, overhead_ns, force_time_us, fidelity) in paper_rows.items():
        _positions, frequencies, _eigenvectors = axial_modes(number_of_ions)
        for contract_name, segment_count in (
            ("printed_table", paper_segments),
            ("stated_2N_plus_5", 2 * number_of_ions + 5),
        ):
            schedule = optimize_toggle_schedule(
                frequencies,
                segment_count=segment_count,
                negative_ratio=0.84,
                restarts=2,
            )
            rows.append(
                {
                    "number_of_ions": number_of_ions,
                    "contract": contract_name,
                    "segment_count": segment_count,
                    "max_closure_residual": float(np.max(np.abs(schedule.residuals))),
                    "closure_cost": schedule.cost,
                    "paper_overhead_ns": overhead_ns,
                    "paper_effective_force_time_us": force_time_us,
                    "paper_fidelity": fidelity,
                    "decay_only_fidelity": 1.0
                    - float(decay_infidelity(force_time_us, 100.0)),
                    "source_contract_conflict": paper_segments
                    != 2 * number_of_ions + 5,
                }
            )
    return rows


def table_s6_fidelity_budget() -> list[dict[str, object]]:
    """Recalculate Table S6 totals while retaining reported inequality bounds."""

    inputs = (
        ("doppler_n60", 20.0, 60, 0.013, 0.077, 0.001, 0.002),
        ("eit_n60", 1.0, 60, 0.013, 0.001, 0.001, 0.002),
        ("gsc_n60", 0.1, 60, 0.013, 0.0001, 0.001, 0.002),
        ("eit_n80", 1.0, 80, 0.0052, 0.00026, 0.001, 0.001),
        ("gsc_n80", 0.1, 80, 0.0052, 0.00003, 0.001, 0.001),
    )
    return [
        {
            "regime": label,
            "mean_phonon": mean_phonon,
            "rydberg_n": rydberg_n,
            "decay": decay,
            "anharmonic_upper": anharmonic,
            "technical_lower": technical_lower,
            "technical_upper": technical_upper,
            "fidelity_lower": 1.0 - decay - anharmonic - technical_upper,
            "fidelity_upper": 1.0 - decay - anharmonic - technical_lower,
            "provenance": "independent_arithmetic_over_paper_table_inputs",
        }
        for (
            label,
            mean_phonon,
            rydberg_n,
            decay,
            anharmonic,
            technical_lower,
            technical_upper,
        ) in inputs
    ]


def taylor_anharmonic_gate_fidelity(
    mean_phonons: Iterable[float] = (0.0, 0.1, 1.0, 5.0, 10.0, 20.0),
    *,
    eta: float = 1.88e-3,
    n_fock: int = 120,
    taylor_order: int = 5,
    coupling_ratio: float = GateParameters().coupling_ratio,
) -> list[dict[str, float]]:
    """Propagate the four logical branches with the printed Eq. (S14) model.

    The dimensionless Hamiltonian is expressed in units of the trap angular
    frequency and evolved for one trap period.  The ion Magnus force acts on
    every branch; the C4 Taylor terms act only on the two Rydberg branches.
    The linear control and the five-order model use the same truncated thermal
    state, so numerical truncation is reported separately from anharmonic loss.
    """

    if eta <= 0.0:
        raise ValueError("eta must be positive")
    if n_fock < 8:
        raise ValueError("n_fock must be at least 8")
    if taylor_order not in {2, 3, 4, 5}:
        raise ValueError("taylor_order must be one of 2, 3, 4, 5")

    annihilation = np.diag(np.sqrt(np.arange(1, n_fock, dtype=float)), 1)
    position = annihilation + annihilation.T
    number = np.diag(np.arange(n_fock, dtype=float))
    position_powers = {power: np.linalg.matrix_power(position, power) for power in range(2, 6)}
    coefficients = {
        2: -2.5 * eta * coupling_ratio,
        3: 5.0 * eta**2 * coupling_ratio,
        4: -8.75 * eta**3 * coupling_ratio,
        5: 14.0 * eta**4 * coupling_ratio,
    }
    anharmonic = sum(
        coefficients[power] * position_powers[power]
        for power in range(2, taylor_order + 1)
    )
    ion_forces = branch_forces(coupling_ratio)[:, 0]
    linear_hamiltonians = [number + force * position for force in ion_forces]
    full_hamiltonians = [
        hamiltonian + (anharmonic if branch >= 2 else 0.0)
        for branch, hamiltonian in enumerate(linear_hamiltonians)
    ]
    linear_unitaries = [_one_period_unitary(hamiltonian) for hamiltonian in linear_hamiltonians]
    full_unitaries = [_one_period_unitary(hamiltonian) for hamiltonian in full_hamiltonians]

    rows: list[dict[str, float]] = []
    for raw_mean_phonon in mean_phonons:
        mean_phonon = float(raw_mean_phonon)
        if mean_phonon < 0.0:
            raise ValueError("mean_phonons must be non-negative")
        probabilities, tail = _truncated_thermal_probabilities(mean_phonon, n_fock)
        full_state = _branch_reduced_state(full_unitaries, probabilities)
        linear_state = _branch_reduced_state(linear_unitaries, probabilities)
        eigenvalues, eigenvectors = np.linalg.eigh(linear_state)
        ideal_state = eigenvectors[:, int(np.argmax(eigenvalues))]
        full_fidelity = float(np.real(ideal_state.conj() @ full_state @ ideal_state))
        linear_fidelity = float(np.max(eigenvalues))
        rows.append(
            {
                "mean_phonon": mean_phonon,
                "n_fock": float(n_fock),
                "taylor_order": float(taylor_order),
                "eta": float(eta),
                "full_infidelity": float(max(0.0, 1.0 - full_fidelity)),
                "linear_infidelity": float(max(0.0, 1.0 - linear_fidelity)),
                "thermal_truncation_tail": tail,
                "trace_error": float(abs(np.trace(full_state) - 1.0)),
                "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(full_state))),
            }
        )
    return rows


def _one_period_unitary(hamiltonian: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(hamiltonian)
    return (vectors * np.exp(-2j * math.pi * values)) @ vectors.conj().T


def _truncated_thermal_probabilities(
    mean_phonon: float, n_fock: int
) -> tuple[np.ndarray, float]:
    if mean_phonon == 0.0:
        probabilities = np.zeros(n_fock)
        probabilities[0] = 1.0
        return probabilities, 0.0
    ratio = mean_phonon / (mean_phonon + 1.0)
    probabilities = (1.0 - ratio) * ratio ** np.arange(n_fock, dtype=float)
    tail = float(ratio**n_fock)
    return probabilities / np.sum(probabilities), tail


def _branch_reduced_state(
    unitaries: list[np.ndarray], probabilities: np.ndarray
) -> np.ndarray:
    state = np.empty((4, 4), dtype=complex)
    thermal = np.diag(probabilities)
    for row in range(4):
        for column in range(4):
            state[row, column] = 0.25 * np.trace(
                unitaries[row] @ thermal @ unitaries[column].conj().T
            )
    return 0.5 * (state + state.conj().T)


def magnus_resource_budget(
    waists_um: Iterable[float] = (0.7, 1.0, 1.5),
) -> list[dict[str, float]]:
    """SI-unit reconstruction of Eqs. S8-S10 and the waist scaling."""

    trap_omega = 2.0 * math.pi * 200_000.0
    coupling_omega = trap_omega / (2.0 * math.sqrt(2.0))
    reduced_wavelength = 355e-9 / (2.0 * math.pi)
    zero_point = 12e-9
    polarizability_si = 60.0 * POLARIZABILITY_ATOMIC_UNIT
    rows = []
    for waist_um in waists_um:
        waist = float(waist_um) * 1e-6
        stark_energy = HBAR * coupling_omega * waist**2 / (
            4.0 * reduced_wavelength * zero_point
        )
        intensity = (
            2.0
            * LIGHT_SPEED
            * VACUUM_PERMITTIVITY
            * stark_energy
            / polarizability_si
        )
        power = 0.5 * math.pi * waist**2 * intensity
        rows.append(
            {
                "waist_um": float(waist_um),
                "stark_shift_MHz": stark_energy / PLANCK / 1e6,
                "peak_intensity_W_m2": intensity,
                "beam_power_mW": power * 1e3,
                "power_over_w0_four": power / waist**4,
            }
        )
    return rows


def linear_thermal_invariance(
    mean_phonons: Iterable[float] = (0.0, 0.1, 1.0, 5.0)
) -> list[dict[str, float]]:
    """Check the exact closure-state independence of the linear Hamiltonian."""

    reference = reduced_spin_state(1.0, mean_phonon=0.0)
    rows = []
    for mean_phonon in mean_phonons:
        state = reduced_spin_state(1.0, mean_phonon=float(mean_phonon))
        rows.append(
            {
                "mean_phonon": float(mean_phonon),
                "max_density_matrix_difference": float(np.max(np.abs(state - reference))),
                "trace_error": float(abs(np.trace(state) - 1.0)),
                "minimum_eigenvalue": float(np.min(np.linalg.eigvalsh(state))),
            }
        )
    return rows


def rf_dressing_sweep(
    rabi_MHz: float = 100.0,
    detunings_MHz: Iterable[float] = (-2000.0, -1000.0, 1000.0, 2000.0),
) -> list[dict[str, object]]:
    """Test the dispersive AC-shift sign without inventing missing polarizability data."""

    rows: list[dict[str, object]] = []
    for detuning_MHz in detunings_MHz:
        detuning = float(detuning_MHz)
        if detuning == 0.0:
            raise ValueError("detuning must be nonzero")
        ratio = abs(rabi_MHz / detuning)
        rows.append(
            {
                "rabi_MHz": rabi_MHz,
                "detuning_MHz": detuning,
                "rabi_over_detuning": ratio,
                "dispersive": ratio <= 0.1,
                "ac_shift_MHz": rabi_MHz**2 / (4.0 * detuning),
                "shift_sign": "positive" if detuning > 0 else "negative",
                "absolute_polarizability_status": "blocked_missing_dipole_and_bare_polarizability",
                "printed_equation_dimensional_status": "requires_fresh_review",
            }
        )
    return rows


def circular_field_budget(
    stark_shift_MHz: float = 17.0,
    distance_um: float = 11.7,
    magnetic_noise_microgauss: float = 1.0,
    magnetic_quantum_number: float = 59.0,
    gate_time_us: float = 5.0,
) -> dict[str, float]:
    """Propagate the printed electric and magnetic stability assumptions."""

    separation_sensitivity = 4.0 * stark_shift_MHz / distance_um
    magnetic_noise_tesla = magnetic_noise_microgauss * 1e-10
    zeeman_noise_hz = (
        BOHR_MAGNETON_OVER_HZ * magnetic_quantum_number * magnetic_noise_tesla
    )
    phase_noise = 2.0 * math.pi * zeeman_noise_hz * gate_time_us * 1e-6
    dephasing_upper = 0.5 * phase_noise**2
    return {
        "separation_sensitivity_MHz_per_um": separation_sensitivity,
        "zeeman_noise_hz": zeeman_noise_hz,
        "phase_noise_rad": phase_noise,
        "dephasing_upper": dephasing_upper,
    }


def large_n_participation_scaling(
    ion_counts: Iterable[int] = (2, 3, 5, 10, 20, 40),
) -> tuple[list[dict[str, float]], dict[str, float]]:
    """Evaluate Eq. S25's edge-participation sum and fit its large-N exponent."""

    rows = []
    for raw_count in ion_counts:
        number_of_ions = int(raw_count)
        if number_of_ions < 2:
            raise ValueError("large-N sweep requires at least two ions")
        _positions, frequencies, eigenvectors = axial_modes(number_of_ions)
        participation_sum = float(
            np.sum(np.power(eigenvectors[0, :], 4) / np.square(frequencies))
        )
        rows.append(
            {
                "number_of_ions": float(number_of_ions),
                "participation_sum": participation_sum,
                "N_times_sum": number_of_ions * participation_sum,
            }
        )
    fit_rows = rows[-3:]
    exponent, intercept = np.polyfit(
        np.log([row["number_of_ions"] for row in fit_rows]),
        np.log([row["participation_sum"] for row in fit_rows]),
        1,
    )
    n10 = next(
        row["participation_sum"]
        for row in rows
        if int(row["number_of_ions"]) == 10
    )
    return rows, {
        "large_n_exponent": float(exponent),
        "large_n_prefactor": float(math.exp(intercept)),
        "n10_participation_sum": float(n10),
        "paper_n10_reference": 0.10,
        "n10_relative_difference": float((n10 - 0.10) / 0.10),
    }
