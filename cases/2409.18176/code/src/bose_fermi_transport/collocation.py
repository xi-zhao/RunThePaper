"""Direct radial collocation of Supplement Eqs. (17)-(19).

This lane keeps the paper's population-deviation variables ``phi_i`` rather
than the entropy-variable Galerkin form in :mod:`kinetic`.  It is the primary
feature renderer; the symmetric Galerkin lane remains an independent
positivity and momentum-conservation cross-check.
"""

from __future__ import annotations

import numpy as np

from .kinetic import (
    GridSpec,
    TransportResult,
    _linear_weights,
    hole_mass_ratio,
    on_shell_geometry,
    radial_grid,
)
from .thermodynamics import (
    HBAR_MEV_PS,
    KB_MEV_PER_K,
    EquilibriumState,
    ModelParameters,
    bose,
    fermi,
)


def _add_interpolated(
    matrix: np.ndarray,
    row: int,
    offset: int,
    interpolation: tuple[int, int, float, float],
    value: float,
) -> None:
    lower, upper, weight_lower, weight_upper = interpolation
    matrix[row, offset + lower] += value * weight_lower
    if upper != lower:
        matrix[row, offset + upper] += value * weight_upper


def assemble_collocation_operator(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    grid: GridSpec,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray | float | int]]:
    hp, hw = radial_grid(grid.hole_points, grid.hole_max_pf)
    xp, xw = radial_grid(grid.exciton_points, grid.exciton_max_pf)
    tp, tw = radial_grid(grid.trion_points, grid.trion_max_pf)
    nh, nx, nt = len(hp), len(xp), len(tp)
    offset_x, offset_t = nh, nh + nx
    size = nh + nx + nt
    collision = np.zeros((size, size), dtype=float)
    source = np.zeros(size, dtype=float)
    ef = params.fermi_energy_mev
    beta = 1.0 / (KB_MEV_PER_K * equilibrium.temperature_k)
    hole_energy = ef * hp**2 - equilibrium.mu_h_mev
    exciton_energy = ef * hole_mass_ratio(params, "x") * xp**2 - equilibrium.mu_x_mev
    trion_energy = (
        ef * hole_mass_ratio(params, "t") * tp**2
        - equilibrium.mu_t_mev
        + equilibrium.detuning_mev
    )
    fh_nodes = fermi(hole_energy, equilibrium.temperature_k)
    bx_nodes = bose(exciton_energy, equilibrium.temperature_k)
    ft_nodes = fermi(trion_energy, equilibrium.temperature_k)
    source[:nh] = beta * hp * fh_nodes * (1.0 - fh_nodes)
    coupling_rate = 6.0 * tunnel_mev**2 / (abs(params.trion_binding_mev) * HBAR_MEV_PS)
    detuning_ratio = equilibrium.detuning_mev / ef
    events_hx = 0

    for ih, (p, wp) in enumerate(zip(hp, hw, strict=True)):
        fh = float(fh_nodes[ih])
        for ix, (k, wk) in enumerate(zip(xp, xw, strict=True)):
            geometry = on_shell_geometry(float(p), float(k), detuning_ratio)
            if geometry is None:
                continue
            r, cos_phi, cos_psi, cos_phi_minus_psi = geometry
            sin_phi = float(np.sqrt(max(0.0, 1.0 - cos_phi * cos_phi)))
            if sin_phi <= grid.angular_boundary_epsilon:
                continue
            interpolation_t = _linear_weights(tp, r)
            if interpolation_t is None:
                continue
            bx = float(bx_nodes[ix])
            et = (
                ef * hole_mass_ratio(params, "t") * r * r
                - equilibrium.mu_t_mev
                + equilibrium.detuning_mev
            )
            ft = float(fermi(et, equilibrium.temperature_k))
            a_x = ft - fh
            a_t = bx - fh + 1.0
            a_h = ft + bx
            jacobian = (2.0 / 3.0) * p * k * sin_phi

            coefficient_h = coupling_rate * wk / jacobian
            collision[ih, ih] += coefficient_h * a_h
            collision[ih, offset_x + ix] -= coefficient_h * a_x * cos_phi
            _add_interpolated(
                collision,
                ih,
                offset_t,
                interpolation_t,
                -coefficient_h * a_t * cos_psi,
            )

            row_x = offset_x + ix
            coefficient_x = coupling_rate * wp / jacobian
            collision[row_x, row_x] -= coefficient_x * a_x
            collision[row_x, ih] += coefficient_x * a_h * cos_phi
            _add_interpolated(
                collision,
                row_x,
                offset_t,
                interpolation_t,
                -coefficient_x * a_t * cos_phi_minus_psi,
            )
            events_hx += 1

    events_t = 0
    for it, (r, _wr) in enumerate(zip(tp, tw, strict=True)):
        ft = float(ft_nodes[it])
        row_t = offset_t + it
        for ix, (k, wk) in enumerate(zip(xp, xw, strict=True)):
            p2 = detuning_ratio + r * r / 3.0 - 0.5 * k * k
            if p2 <= 0.0:
                continue
            p = float(np.sqrt(p2))
            interpolation_h = _linear_weights(hp, p)
            if interpolation_h is None or r <= 0.0 or k <= 0.0:
                continue
            cos_theta_k = float((r * r + k * k - p * p) / (2.0 * r * k))
            if abs(cos_theta_k) >= 1.0:
                continue
            sin_theta = float(np.sqrt(max(0.0, 1.0 - cos_theta_k * cos_theta_k)))
            if sin_theta <= grid.angular_boundary_epsilon:
                continue
            cos_theta_h = float((r - k * cos_theta_k) / p)
            eh = ef * p * p - equilibrium.mu_h_mev
            fh = float(fermi(eh, equilibrium.temperature_k))
            bx = float(bx_nodes[ix])
            b_x = fh - ft
            b_t = bx - fh + 1.0
            b_h = bx + ft
            jacobian = 2.0 * r * k * sin_theta
            coefficient_t = coupling_rate * wk / jacobian
            collision[row_t, row_t] += coefficient_t * b_t
            collision[row_t, offset_x + ix] -= coefficient_t * b_x * cos_theta_k
            _add_interpolated(
                collision,
                row_t,
                0,
                interpolation_h,
                -coefficient_t * b_h * cos_theta_h,
            )
            events_t += 1

    common_drift = np.concatenate(
        (
            beta * fh_nodes * (1.0 - fh_nodes) * hp,
            beta * bx_nodes * (1.0 + bx_nodes) * xp,
            beta * ft_nodes * (1.0 - ft_nodes) * tp,
        )
    )
    drift_norm = max(float(np.linalg.norm(common_drift)), 1.0e-30)
    diagnostics: dict[str, np.ndarray | float | int] = {
        "hole_nodes": hp,
        "hole_weights": hw,
        "exciton_nodes": xp,
        "exciton_weights": xw,
        "trion_nodes": tp,
        "trion_weights": tw,
        "common_drift_residual": float(
            np.linalg.norm(collision @ common_drift) / drift_norm
        ),
        "events_hx": events_hx,
        "events_t": events_t,
        "fh_nodes": fh_nodes,
    }
    return collision, source, diagnostics


def solve_collocation_sweep(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    frequencies_mev: np.ndarray,
    grid: GridSpec,
    relaxation_times_ps: tuple[float, float, float] | None = None,
) -> list[TransportResult]:
    collision, source, diagnostics = assemble_collocation_operator(
        params, equilibrium, tunnel_mev, grid
    )
    nh, nx, nt = grid.hole_points, grid.exciton_points, grid.trion_points
    if relaxation_times_ps is None:
        relaxation_times_ps = (params.relaxation_time_ps,) * 3
    rates = np.concatenate(
        (
            np.full(nh, 1.0 / relaxation_times_ps[0]),
            np.full(nx, 1.0 / relaxation_times_ps[1]),
            np.full(nt, 1.0 / relaxation_times_ps[2]),
        )
    )
    hp = np.asarray(diagnostics["hole_nodes"])
    hw = np.asarray(diagnostics["hole_weights"])
    xp = np.asarray(diagnostics["exciton_nodes"])
    xw = np.asarray(diagnostics["exciton_weights"])
    tp = np.asarray(diagnostics["trion_nodes"])
    tw = np.asarray(diagnostics["trion_weights"])
    velocity = np.concatenate(
        (hp, hole_mass_ratio(params, "x") * xp, hole_mass_ratio(params, "t") * tp)
    )
    current_weights = np.concatenate((hw, xw, tw)) * velocity
    beta = 1.0 / (KB_MEV_PER_K * equilibrium.temperature_k)
    fh = np.asarray(diagnostics["fh_nodes"])
    raw_drude = float(
        np.sum(hw * hp * (relaxation_times_ps[0] * beta * hp * fh * (1.0 - fh)))
    )
    expected_drude = (
        equilibrium.n_h_cm2
        / params.hole_reference_density_cm2
        * relaxation_times_ps[0]
        / params.relaxation_time_ps
    )
    scale = expected_drude / raw_drude
    results: list[TransportResult] = []
    for frequency in np.asarray(frequencies_mev, dtype=float):
        operator = collision.astype(complex) + np.diag(
            rates + 1j * frequency / HBAR_MEV_PS
        )
        solution = np.linalg.solve(operator, source.astype(complex))
        raw = np.array(
            [
                np.dot(current_weights[:nh], solution[:nh]),
                np.dot(current_weights[nh : nh + nx], solution[nh : nh + nx]),
                np.dot(current_weights[nh + nx :], solution[nh + nx :]),
            ]
        )
        real_eigenvalues = np.linalg.eigvals(collision).real
        results.append(
            TransportResult(
                sigma_h=complex(raw[0] * scale),
                sigma_x=complex(raw[1] * scale),
                sigma_t=complex(raw[2] * scale),
                collision_momentum_residual=float(diagnostics["common_drift_residual"]),
                collision_min_eigenvalue=float(np.min(real_eigenvalues)),
                event_count=int(diagnostics["events_hx"])
                + int(diagnostics["events_t"]),
                condition_number=float(np.linalg.cond(operator)),
                equilibrium=equilibrium,
            )
        )
    return results


def solve_collocation(
    params: ModelParameters,
    equilibrium: EquilibriumState,
    tunnel_mev: float,
    frequency_mev: float,
    grid: GridSpec,
    relaxation_times_ps: tuple[float, float, float] | None = None,
) -> TransportResult:
    return solve_collocation_sweep(
        params,
        equilibrium,
        tunnel_mev,
        np.array([frequency_mev]),
        grid,
        relaxation_times_ps,
    )[0]
