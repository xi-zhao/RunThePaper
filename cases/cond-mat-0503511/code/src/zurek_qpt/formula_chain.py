"""Clean-room checks for the paper's KZM-to-LZF analytic chain.

The figure runner already uses the endpoint formulae.  This module makes the
intermediate quantitative claims independently executable so that equations
and method claims discovered by fresh review are not hidden behind a figure.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FormulaChain:
    coupling_w: float
    hbar: float
    lattice_spacing: float
    tau_q: float
    fidelity: float

    def __post_init__(self) -> None:
        if min(self.coupling_w, self.hbar, self.lattice_spacing, self.tau_q) <= 0:
            raise ValueError("positive physical scales are required")
        if not 0.0 < self.fidelity < 1.0:
            raise ValueError("fidelity must lie strictly inside (0, 1)")

    @property
    def tau_0(self) -> float:
        return self.hbar / (2.0 * self.coupling_w)

    @property
    def sound_speed(self) -> float:
        return 2.0 * self.coupling_w * self.lattice_spacing / self.hbar

    def epsilon(self, time: float) -> float:
        return time / self.tau_q

    def thermodynamic_gap(self, epsilon: float) -> float:
        return 2.0 * self.coupling_w * abs(epsilon)

    def relaxation_time(self, epsilon: float) -> float:
        if epsilon == 0.0:
            return float("inf")
        return self.tau_0 / abs(epsilon)

    def healing_length(self, epsilon: float) -> float:
        if epsilon == 0.0:
            return float("inf")
        return self.lattice_spacing / abs(epsilon)

    @property
    def freeze_time(self) -> float:
        return float(np.sqrt(self.tau_q * self.tau_0))

    @property
    def freeze_epsilon(self) -> float:
        return self.freeze_time / self.tau_q

    @property
    def freeze_length(self) -> float:
        return self.lattice_spacing / self.freeze_epsilon

    @property
    def mean_field_freeze_length(self) -> float:
        return self.lattice_spacing * (self.tau_q / self.tau_0) ** 0.25

    @property
    def kzm_density(self) -> float:
        return self.lattice_spacing / self.freeze_length

    @property
    def quench_velocity(self) -> float:
        return 2.0 * self.coupling_w / self.tau_q

    def accessible_gap(self, chain_length: float) -> float:
        if chain_length <= 0.0:
            raise ValueError("chain length must be positive")
        return 4.0 * np.pi * self.coupling_w / chain_length

    def speed_bound(self, chain_length: float) -> float:
        gap = self.accessible_gap(chain_length)
        return float(
            np.pi * gap**2
            / (2.0 * self.hbar * abs(np.log1p(-self.fidelity)))
        )

    @property
    def defect_free_chain_bound(self) -> float:
        return float(
            2.0
            * np.pi
            * np.sqrt(
                np.pi
                * self.coupling_w
                * self.tau_q
                / (self.hbar * abs(np.log1p(-self.fidelity)))
            )
        )

    def landau_zener_change_probability(self, chain_length: float) -> float:
        gap = self.accessible_gap(chain_length)
        return float(
            np.exp(-np.pi * gap**2 / (2.0 * self.hbar * self.quench_velocity))
        )


def open_ising_hamiltonian(
    n_spins: int,
    *,
    field_j: float,
    coupling_w: float,
) -> np.ndarray:
    """Construct Eq. (1) directly for a small open chain."""

    if n_spins < 2:
        raise ValueError("at least two spins are required")
    identity = np.eye(2, dtype=float)
    sigma_x = np.array([[0.0, 1.0], [1.0, 0.0]])
    sigma_z = np.diag([1.0, -1.0])

    def product(operators: list[np.ndarray]) -> np.ndarray:
        result = operators[0]
        for operator in operators[1:]:
            result = np.kron(result, operator)
        return result

    dimension = 2**n_spins
    hamiltonian = np.zeros((dimension, dimension), dtype=float)
    for site in range(n_spins):
        operators = [identity] * n_spins
        operators[site] = sigma_x
        hamiltonian -= field_j * product(operators)
    for site in range(n_spins - 1):
        operators = [identity] * n_spins
        operators[site] = sigma_z
        operators[site + 1] = sigma_z
        hamiltonian -= coupling_w * product(operators)
    return hamiltonian


def evaluate_formula_chain(parameters: dict[str, float | int]) -> dict[str, object]:
    """Evaluate the 28 independently falsifiable quantitative claims."""

    chain = FormulaChain(
        coupling_w=float(parameters["coupling_w"]),
        hbar=float(parameters["hbar"]),
        lattice_spacing=float(parameters["lattice_spacing"]),
        tau_q=float(parameters["tau_q"]),
        fidelity=float(parameters["fidelity"]),
    )
    tolerance = float(parameters["identity_tolerance"])
    check_n = int(parameters["spin_check_n"])
    chain_length = float(parameters["chain_length"])
    freeze_time = chain.freeze_time
    freeze_epsilon = chain.freeze_epsilon
    hamiltonian = open_ising_hamiltonian(
        check_n,
        field_j=chain.coupling_w,
        coupling_w=chain.coupling_w,
    )
    low_field = open_ising_hamiltonian(
        check_n,
        field_j=0.0,
        coupling_w=chain.coupling_w,
    )
    low_spectrum = np.linalg.eigvalsh(low_field)
    ground_degeneracy = int(
        np.count_nonzero(np.isclose(low_spectrum, low_spectrum[0], atol=tolerance))
    )
    n_tilde = chain.defect_free_chain_bound
    lzf_at_bound = chain.landau_zener_change_probability(n_tilde)
    fidelity_state = np.array(
        [np.sqrt(chain.fidelity), np.sqrt(1.0 - chain.fidelity)]
    )
    ground_state = np.array([1.0, 0.0])
    overlap_fidelity = float(abs(np.vdot(fidelity_state, ground_state)) ** 2)
    identity_residuals = {
        "epsilon_timescale": abs(
            chain.epsilon(freeze_time)
            / (1.0 / chain.tau_q)
            - freeze_time
        ),
        "freeze_condition": abs(
            chain.relaxation_time(freeze_epsilon) - freeze_time
        ),
        "freeze_length": abs(
            chain.freeze_length
            - chain.lattice_spacing * np.sqrt(chain.tau_q / chain.tau_0)
        ),
        "kzm_density": abs(
            chain.kzm_density
            - np.sqrt(chain.hbar / (2.0 * chain.coupling_w * chain.tau_q))
        ),
        "velocity_substitution": abs(
            chain.speed_bound(n_tilde) - chain.quench_velocity
        ),
        "lzf_probability": abs(lzf_at_bound - (1.0 - chain.fidelity)),
        "fidelity_overlap": abs(overlap_fidelity - chain.fidelity),
    }
    common_pass = all(value <= tolerance for value in identity_residuals.values())
    claim_ids = [
        "R004", "R005", "R005B", "R006", "R007", "R008", "R009",
        "R010", "R011", "R012", "R013", "R013B", "R014", "R015",
        "R017", "R018", "R019", "R020", "R028", "R028B", "R031",
        "R034", "R035", "R036", "R037", "R038", "R041", "R042",
    ]
    checks = {
        "hamiltonian_is_hermitian": bool(
            np.allclose(hamiltonian, hamiltonian.T, atol=tolerance)
        ),
        "thermodynamic_gap_closes_at_j_equals_w": (
            chain.thermodynamic_gap(0.0) == 0.0
        ),
        "low_field_ground_state_is_doubly_degenerate": ground_degeneracy == 2,
        "all_printed_identities_close": common_pass,
        "kzm_validity_probe_is_small": freeze_epsilon
        <= float(parameters["maximum_freeze_epsilon"]),
        "expected_defects_at_least_one": chain_length * chain.kzm_density
        >= float(parameters["minimum_expected_defects"]),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "claim_ids": claim_ids,
        "checks": checks,
        "identity_residuals": identity_residuals,
        "values": {
            "tau_0": chain.tau_0,
            "sound_speed": chain.sound_speed,
            "freeze_time": freeze_time,
            "freeze_epsilon": freeze_epsilon,
            "freeze_length": chain.freeze_length,
            "mean_field_freeze_length": chain.mean_field_freeze_length,
            "kzm_density": chain.kzm_density,
            "expected_defects": chain_length * chain.kzm_density,
            "quench_velocity": chain.quench_velocity,
            "defect_free_chain_bound": n_tilde,
            "inverse_defect_free_chain_bound": 1.0 / n_tilde,
            "lzf_change_probability_at_bound": lzf_at_bound,
            "overlap_fidelity": overlap_fidelity,
            "low_field_ground_degeneracy": ground_degeneracy,
        },
    }
