"""Multi-orbital interaction, CT-HYB contract, and impurity adapter.

The production adapter imports the public TRIQS/cthyb package only at
execution time. Validation and deck generation remain deterministic on
machines without that dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


class SolverUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ImpurityResult:
    green_iw: np.ndarray
    self_energy_iw: np.ndarray
    density_matrix: np.ndarray
    spin_correlation_tau: np.ndarray
    average_sign: float


def density_density_kanamori_matrix(
    n_orbitals: int,
    *,
    u: float,
    j: float,
) -> np.ndarray:
    """Return U_(a sigma,b sigma') for density-density Slater-Kanamori."""

    if n_orbitals < 1 or u <= 0.0 or j < 0.0 or u < 3.0 * j:
        raise ValueError("invalid Slater-Kanamori parameters")
    n_flavors = 2 * n_orbitals
    matrix = np.zeros((n_flavors, n_flavors), dtype=float)
    for flavor_a in range(n_flavors):
        orbital_a, spin_a = divmod(flavor_a, 2)
        for flavor_b in range(n_flavors):
            orbital_b, spin_b = divmod(flavor_b, 2)
            if flavor_a == flavor_b:
                continue
            if orbital_a == orbital_b:
                matrix[flavor_a, flavor_b] = u
            elif spin_a == spin_b:
                matrix[flavor_a, flavor_b] = u - 3.0 * j
            else:
                matrix[flavor_a, flavor_b] = u - 2.0 * j
    return matrix


def validate_solver_contract(contract: dict[str, Any]) -> None:
    required = {
        "beta_ev_inverse",
        "u_ev",
        "j_ev",
        "n_orbitals",
        "n_iw",
        "n_tau",
        "warmup_cycles",
        "measurement_cycles",
        "cycle_length",
        "random_seed",
        "spin_correlation_orbitals",
    }
    missing = sorted(required - set(contract))
    if missing:
        raise ValueError(f"missing CT-HYB fields: {missing}")
    if float(contract["beta_ev_inverse"]) <= 0.0:
        raise ValueError("beta must be positive")
    density_density_kanamori_matrix(
        int(contract["n_orbitals"]),
        u=float(contract["u_ev"]),
        j=float(contract["j_ev"]),
    )
    for name in (
        "n_iw",
        "n_tau",
        "warmup_cycles",
        "measurement_cycles",
        "cycle_length",
        "independent_chains",
    ):
        if int(contract[name]) <= 0:
            raise ValueError(f"{name} must be positive")
    correlation_orbitals = contract["spin_correlation_orbitals"]
    if (
        not isinstance(correlation_orbitals, list)
        or not correlation_orbitals
        or len(set(correlation_orbitals)) != len(correlation_orbitals)
        or any(
            not isinstance(index, int) or not 0 <= index < int(contract["n_orbitals"])
            for index in correlation_orbitals
        )
    ):
        raise ValueError("spin-correlation orbitals must be unique valid d indices")


def solve_impurity_triqs(
    weiss_iw: np.ndarray,
    contract: dict[str, Any],
) -> ImpurityResult:
    """Execute one public TRIQS/cthyb impurity solve.

    The adapter sets the Weiss field, builds the density-density interaction,
    samples G(tau) and the requested orbital moment correlators, averages
    independent chains, and evaluates Sigma by Dyson. The complete slab loop
    calls this once per inequivalent Ni layer with disjoint deterministic seeds.
    """

    validate_solver_contract(contract)
    try:
        from triqs.gf import GfImFreq  # type: ignore
        from triqs.operators import n  # type: ignore
        from triqs_cthyb import Solver  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional HPC dependency
        raise SolverUnavailable("public TRIQS/cthyb is not installed") from exc

    beta = float(contract["beta_ev_inverse"])
    n_orbitals = int(contract["n_orbitals"])
    n_flavors = 2 * n_orbitals
    values = np.asarray(weiss_iw, dtype=np.complex128)
    if values.ndim != 3 or values.shape[1:] != (n_flavors, n_flavors):
        raise ValueError("Weiss field must have shape (n_iw, 2*n_orb, 2*n_orb)")
    gf_struct = [("loc", n_flavors)]

    def configured_solver() -> Any:
        solver = Solver(
            beta=beta,
            gf_struct=gf_struct,
            n_iw=int(contract["n_iw"]),
            n_tau=int(contract["n_tau"]),
        )
        g0 = GfImFreq(
            beta=beta,
            target_shape=(n_flavors, n_flavors),
            n_points=int(contract["n_iw"]),
        )
        if g0.data.shape != values.shape:
            raise ValueError(
                "TRIQS frequency layout differs from the serialized Weiss field"
            )
        g0.data[:] = values
        solver.G0_iw["loc"] << g0
        return solver

    interaction = density_density_kanamori_matrix(
        n_orbitals,
        u=float(contract["u_ev"]),
        j=float(contract["j_ev"]),
    )
    h_int = 0
    for flavor_a in range(n_flavors):
        for flavor_b in range(flavor_a + 1, n_flavors):
            h_int += (
                float(interaction[flavor_a, flavor_b])
                * n("loc", flavor_a)
                * n("loc", flavor_b)
            )
    chi_chains = []
    signs = []
    green_chains = []
    density_chains = []
    for chain_index in range(int(contract["independent_chains"])):
        chi_rows = []
        for measurement_index, orbital in enumerate(
            contract["spin_correlation_orbitals"]
        ):
            solver = configured_solver()
            magnetic_moment = n("loc", 2 * orbital) - n("loc", 2 * orbital + 1)
            solver.solve(
                h_int=h_int,
                n_warmup_cycles=int(contract["warmup_cycles"]),
                n_cycles=int(contract["measurement_cycles"]),
                length_cycle=int(contract["cycle_length"]),
                random_seed=(
                    int(contract["random_seed"])
                    + 15485863 * chain_index
                    + 130363 * measurement_index
                ),
                measure_G_tau=True,
                measure_O_tau=(magnetic_moment, magnetic_moment),
                measure_O_tau_min_ins=int(
                    contract.get("spin_correlation_min_insertions", 100)
                ),
            )
            chi = np.asarray(solver.O_tau.data).real.squeeze()
            if chi.shape != (int(contract["n_tau"]),):
                raise ValueError("TRIQS O_tau layout violates the chi(tau) contract")
            chi_rows.append(chi)
            signs.append(float(getattr(solver, "average_sign", 1.0)))
            if measurement_index == 0:
                green_chains.append(np.asarray(solver.G_iw["loc"].data))
                density_chains.append(np.asarray(solver.G_iw["loc"].density()))
        chi_chains.append(np.stack(chi_rows))
    green = np.mean(green_chains, axis=0)
    density = np.mean(density_chains, axis=0)
    sigma = np.linalg.inv(values) - np.linalg.inv(green)
    chi_tau = np.mean(chi_chains, axis=0)
    average_sign = min(signs)
    return ImpurityResult(green, sigma, density, chi_tau, average_sign)
