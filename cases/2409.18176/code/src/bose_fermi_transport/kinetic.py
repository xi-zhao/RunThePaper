"""Formula-derived l=1 Galerkin solver for the coupled Boltzmann equations.

The solver projects the printed collision equations onto radial hat functions
and integrates the energy-conserving relative angle analytically.  The
resulting collision matrix is symmetric positive semidefinite by construction
and preserves the common momentum mode up to floating-point interpolation
error.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .thermodynamics import HBAR_MEV_PS, EquilibriumState, ModelParameters, bose, fermi


@dataclass(frozen=True)
class GridSpec:
    hole_points: int
    exciton_points: int
    trion_points: int
    hole_max_pf: float
    exciton_max_pf: float
    trion_max_pf: float
    angular_boundary_epsilon: float = 2.0e-4


@dataclass(frozen=True)
class TransportResult:
    sigma_h: complex
    sigma_x: complex
    sigma_t: complex
    collision_momentum_residual: float
    collision_min_eigenvalue: float
    event_count: int
    condition_number: float
    equilibrium: EquilibriumState


def radial_grid(points: int, maximum: float) -> tuple[np.ndarray, np.ndarray]:
    if points < 4 or maximum <= 0.0:
        raise ValueError(
            "radial grid requires at least four points and a positive maximum"
        )
    spacing = maximum / points
    nodes = (np.arange(points, dtype=float) + 0.5) * spacing
    weights = nodes * spacing
    return nodes, weights


def _linear_weights(
    nodes: np.ndarray, value: float
) -> tuple[int, int, float, float] | None:
    if value < nodes[0] or value > nodes[-1]:
        return None
    upper = int(np.searchsorted(nodes, value, side="right"))
    if upper == 0:
        return 0, 0, 1.0, 0.0
    if upper >= len(nodes):
        last = len(nodes) - 1
        return last, last, 1.0, 0.0
    lower = upper - 1
    fraction = float((value - nodes[lower]) / (nodes[upper] - nodes[lower]))
    return lower, upper, 1.0 - fraction, fraction


def on_shell_geometry(
    p: float, k: float, detuning_ratio: float
) -> tuple[float, float, float, float] | None:
    """Return ``(r, cos(phi), cos(psi), cos(phi-psi))`` for h+x->t."""

    if p <= 0.0 or k <= 0.0:
        return None
    cos_phi = (p * p + 0.25 * k * k - 1.5 * detuning_ratio) / (p * k)
    if abs(cos_phi) >= 1.0:
        return None
    r2 = p * p + k * k + 2.0 * p * k * cos_phi
    if r2 <= 0.0:
        return None
    r = float(np.sqrt(r2))
    cos_psi = float((p + k * cos_phi) / r)
    cos_phi_minus_psi = float((k + p * cos_phi) / r)
    return r, float(cos_phi), cos_psi, cos_phi_minus_psi


def _species_distributions(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    hole_nodes: np.ndarray,
    exciton_nodes: np.ndarray,
    trion_nodes: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ef = params.fermi_energy_mev
    hole_energy = ef * hole_nodes**2 - equilibrium.mu_h_mev
    exciton_energy = (
        ef * hole_mass_ratio(params, "x") * exciton_nodes**2 - equilibrium.mu_x_mev
    )
    trion_energy = (
        ef * hole_mass_ratio(params, "t") * trion_nodes**2
        - equilibrium.mu_t_mev
        + equilibrium.detuning_mev
    )
    return (
        fermi(hole_energy, equilibrium.temperature_k),
        bose(exciton_energy, equilibrium.temperature_k),
        fermi(trion_energy, equilibrium.temperature_k),
    )


def hole_mass_ratio(params: ModelParameters, species: str) -> float:
    """Return ``m_h/m_i`` for a species."""

    if species == "h":
        return 1.0
    if species == "x":
        return params.hole_mass_me / params.exciton_mass_me
    if species == "t":
        return params.hole_mass_me / params.trion_mass_me
    raise ValueError(species)


def assemble_operator(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    grid: GridSpec,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray | float | int]]:
    """Assemble mass, collision, and source matrices in inverse-ps units."""

    hp, hw = radial_grid(grid.hole_points, grid.hole_max_pf)
    xp, xw = radial_grid(grid.exciton_points, grid.exciton_max_pf)
    tp, tw = radial_grid(grid.trion_points, grid.trion_max_pf)
    fh, bx, ft = _species_distributions(params, equilibrium, hp, xp, tp)
    sh = fh * (1.0 - fh)
    sx = bx * (1.0 + bx)
    st = ft * (1.0 - ft)

    nh, nx, nt = len(hp), len(xp), len(tp)
    offset_x, offset_t = nh, nh + nx
    size = nh + nx + nt
    mass_diag = np.concatenate((hw * sh, xw * sx, tw * st))
    mass = np.diag(mass_diag)
    collision = np.zeros((size, size), dtype=float)

    coupling_rate = 6.0 * tunnel_mev**2 / (abs(params.trion_binding_mev) * HBAR_MEV_PS)
    detuning_ratio = equilibrium.detuning_mev / params.fermi_energy_mev
    events = 0
    for ih, (p, wp) in enumerate(zip(hp, hw, strict=True)):
        eh = params.fermi_energy_mev * p * p - equilibrium.mu_h_mev
        fh_event = float(fermi(eh, equilibrium.temperature_k))
        for ix, (k, wk) in enumerate(zip(xp, xw, strict=True)):
            geometry = on_shell_geometry(float(p), float(k), detuning_ratio)
            if geometry is None:
                continue
            r, cos_phi, cos_psi, cos_phi_minus_psi = geometry
            sin_phi = float(np.sqrt(max(0.0, 1.0 - cos_phi * cos_phi)))
            if sin_phi <= grid.angular_boundary_epsilon:
                continue
            interpolation = _linear_weights(tp, r)
            if interpolation is None:
                continue
            lower, upper, weight_lower, weight_upper = interpolation
            ex = (
                params.fermi_energy_mev * hole_mass_ratio(params, "x") * k * k
                - equilibrium.mu_x_mev
            )
            et = eh + ex
            bx_event = float(bose(ex, equilibrium.temperature_k))
            ft_event = float(fermi(et, equilibrium.temperature_k))
            equilibrium_weight = fh_event * bx_event * (1.0 - ft_event)
            if not np.isfinite(equilibrium_weight) or equilibrium_weight <= 0.0:
                continue
            jacobian = (2.0 / 3.0) * p * k * sin_phi
            coefficient = coupling_rate * wp * wk * equilibrium_weight / jacobian

            indices = [ih, offset_x + ix, offset_t + lower]
            t_weights = [weight_lower]
            if upper != lower and weight_upper > 0.0:
                indices.append(offset_t + upper)
                t_weights.append(weight_upper)
            cos_vector = [1.0, cos_phi]
            sin_vector = [0.0, sin_phi]
            for weight in t_weights:
                cos_vector.append(-weight * cos_psi)
                sin_psi = np.sign(sin_phi) * np.sqrt(max(0.0, 1.0 - cos_psi * cos_psi))
                cos_vector[-1] = -weight * cos_psi
                sin_vector.append(-weight * sin_psi)

            local = np.outer(cos_vector, cos_vector) + np.outer(sin_vector, sin_vector)
            collision[np.ix_(indices, indices)] += coefficient * local
            events += 1

    velocity = np.concatenate(
        (hp, hole_mass_ratio(params, "x") * xp, hole_mass_ratio(params, "t") * tp)
    )
    source = np.zeros(size, dtype=float)
    source[:nh] = mass_diag[:nh] * hp
    momentum_mode = np.concatenate((hp, xp, tp))
    momentum_norm = max(float(np.linalg.norm(momentum_mode)), 1.0e-30)
    momentum_residual = float(np.linalg.norm(collision @ momentum_mode) / momentum_norm)
    diagnostics: dict[str, np.ndarray | float | int] = {
        "hole_nodes": hp,
        "exciton_nodes": xp,
        "trion_nodes": tp,
        "mass_diag": mass_diag,
        "velocity": velocity,
        "momentum_residual": momentum_residual,
        "event_count": events,
    }
    return mass, collision, source, diagnostics


def solve_transport(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    frequency_mev: float,
    grid: GridSpec,
    relaxation_times_ps: tuple[float, float, float] | None = None,
) -> TransportResult:
    return solve_transport_sweep(
        params,
        equilibrium,
        tunnel_mev,
        np.array([frequency_mev], dtype=float),
        grid,
        relaxation_times_ps,
    )[0]


def solve_transport_sweep(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    frequencies_mev: np.ndarray,
    grid: GridSpec,
    relaxation_times_ps: tuple[float, float, float] | None = None,
) -> list[TransportResult]:
    """Solve several frequencies while reusing one collision operator."""

    mass, collision, source, diagnostics = assemble_operator(
        params, equilibrium, tunnel_mev, grid
    )
    nh, nx = grid.hole_points, grid.exciton_points
    size = mass.shape[0]
    if relaxation_times_ps is None:
        relaxation_times_ps = (params.relaxation_time_ps,) * 3
    rates = np.concatenate(
        (
            np.full(nh, 1.0 / relaxation_times_ps[0]),
            np.full(nx, 1.0 / relaxation_times_ps[1]),
            np.full(grid.trion_points, 1.0 / relaxation_times_ps[2]),
        )
    )
    mass_diag_full = np.diag(mass)
    active_threshold = max(float(np.max(mass_diag_full)) * 1.0e-13, 1.0e-300)
    active = mass_diag_full > active_threshold
    if np.count_nonzero(active) < 4:
        raise RuntimeError("transport grid has fewer than four thermally active modes")
    velocity = np.asarray(diagnostics["velocity"])
    mass_diag = np.asarray(diagnostics["mass_diag"])
    raw_drude = float(
        np.sum(mass_diag[:nh] * velocity[:nh] ** 2) * relaxation_times_ps[0]
    )
    expected_drude = (
        equilibrium.n_h_cm2
        / params.hole_reference_density_cm2
        * relaxation_times_ps[0]
        / params.relaxation_time_ps
    )
    scale = expected_drude / raw_drude
    eigenvalues = np.linalg.eigvalsh(collision)
    results: list[TransportResult] = []
    for frequency_mev in np.asarray(frequencies_mev, dtype=float):
        omega_ps = frequency_mev / HBAR_MEV_PS
        operator = collision.astype(complex) + np.diag(
            mass_diag_full * (rates + 1j * omega_ps)
        )
        reduced_operator = operator[np.ix_(active, active)]
        reduced_solution = np.linalg.solve(
            reduced_operator, source[active].astype(complex)
        )
        solution = np.zeros(size, dtype=complex)
        solution[active] = reduced_solution
        raw = np.array(
            [
                np.dot(mass_diag[:nh] * velocity[:nh], solution[:nh]),
                np.dot(
                    mass_diag[nh : nh + nx] * velocity[nh : nh + nx],
                    solution[nh : nh + nx],
                ),
                np.dot(mass_diag[nh + nx :] * velocity[nh + nx :], solution[nh + nx :]),
            ],
            dtype=complex,
        )
        results.append(
            TransportResult(
                sigma_h=complex(raw[0] * scale),
                sigma_x=complex(raw[1] * scale),
                sigma_t=complex(raw[2] * scale),
                collision_momentum_residual=float(diagnostics["momentum_residual"]),
                collision_min_eigenvalue=float(eigenvalues[0]),
                event_count=int(diagnostics["event_count"]),
                condition_number=float(np.linalg.cond(reduced_operator)),
                equilibrium=equilibrium,
            )
        )
    return results


def hole_scattering_rate(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    hole_momentum_pf: float,
    exciton_points: int = 240,
    exciton_max_pf: float = 4.5,
) -> float:
    """Angular-delta evaluation of Main Eq. (2), returned in ps^-1."""

    nodes, weights = radial_grid(exciton_points, exciton_max_pf)
    coupling_rate = 6.0 * tunnel_mev**2 / (abs(params.trion_binding_mev) * HBAR_MEV_PS)
    rate = 0.0
    for k, weight in zip(nodes, weights, strict=True):
        geometry = on_shell_geometry(
            hole_momentum_pf,
            float(k),
            equilibrium.detuning_mev / params.fermi_energy_mev,
        )
        if geometry is None:
            continue
        r, cos_phi, _, _ = geometry
        sin_phi = np.sqrt(max(0.0, 1.0 - cos_phi * cos_phi))
        if sin_phi < 1.0e-5:
            continue
        ex = (
            params.fermi_energy_mev * hole_mass_ratio(params, "x") * k * k
            - equilibrium.mu_x_mev
        )
        et = (
            params.fermi_energy_mev * hole_mass_ratio(params, "t") * r * r
            - equilibrium.mu_t_mev
            + equilibrium.detuning_mev
        )
        population = float(
            bose(ex, equilibrium.temperature_k) + fermi(et, equilibrium.temperature_k)
        )
        jacobian = (2.0 / 3.0) * hole_momentum_pf * k * sin_phi
        rate += coupling_rate * weight * population / jacobian
    return float(rate)
