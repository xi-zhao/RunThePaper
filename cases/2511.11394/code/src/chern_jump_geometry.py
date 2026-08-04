"""Two-band geometry and dissipative-flow tools for arXiv:2511.11394.

The module keeps the physical distinction between:

* ``K = integral tr(g)``: the standard integrated quantum metric;
* ``E_D = K / 2``: the paper's Dirichlet energy in flat coordinates;
* ``K_jump(q)``: a calibrated four-direction finite-momentum mismatch.

``K_jump`` is a detector-normalized geometric observable.  It is not an
unqualified total Lindblad jump rate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]
TWO_PI = 2.0 * np.pi


@dataclass(frozen=True)
class GeometryObservables:
    """Brillouin-zone integrated observables for a unit-vector texture."""

    chern: float
    metric_integral: float
    dirichlet_energy: float
    absolute_curvature_integral: float
    finite_difference_chern: float
    opposite_curvature_fraction: float
    max_norm_error: float


def normalize_texture(texture: Array) -> Array:
    """Normalize the final axis of a nonzero vector field."""

    norm = np.linalg.norm(texture, axis=-1, keepdims=True)
    if np.any(norm <= np.finfo(float).tiny):
        raise ValueError("texture contains a zero vector")
    return texture / norm


def momentum_grid(
    size: int,
    offset_fraction: float = 0.0,
) -> tuple[Array, Array, float]:
    """Return a periodic square grid with an optional fractional-cell offset.

    ``offset_fraction=0.5`` is the midpoint grid used for the exact
    extended-Hubbard trajectory.  It avoids placing the bubbling point
    ``(pi, pi)`` exactly on a grid node, where the discrete symmetry would
    artificially pin that spin forever.
    """

    if size < 5:
        raise ValueError("grid size must be at least 5")
    if not 0.0 <= offset_fraction < 1.0:
        raise ValueError("offset_fraction must lie in [0, 1)")
    spacing = TWO_PI / size
    values = -np.pi + (np.arange(size) + offset_fraction) * spacing
    kx, ky = np.meshgrid(values, values, indexing="ij")
    return kx, ky, spacing


def qwz_d_vector(
    size: int,
    mass: float,
    offset_fraction: float = 0.0,
) -> Array:
    """Massive Dirac/QWZ d-vector used in the paper."""

    kx, ky, _ = momentum_grid(size, offset_fraction)
    return np.stack(
        (
            np.sin(kx),
            np.sin(ky),
            mass - np.cos(kx) - np.cos(ky),
        ),
        axis=-1,
    )


def qwz_texture(
    size: int,
    mass: float,
    offset_fraction: float = 0.0,
) -> Array:
    """Lower-band projector texture n=-d/|d|."""

    return normalize_texture(-qwz_d_vector(size, mass, offset_fraction))


def constant_texture(size: int, direction: tuple[float, float, float] = (0.0, 0.0, 1.0)) -> Array:
    """Return a constant normalized negative-control texture."""

    vector = normalize_texture(np.asarray(direction, dtype=float))
    return np.broadcast_to(vector, (size, size, 3)).copy()


def projector_mismatch(texture: Array, shifted_texture: Array) -> Array:
    """Compute tr[P(k)(1-P(k+q))] for two rank-one projectors."""

    if texture.shape != shifted_texture.shape or texture.shape[-1] != 3:
        raise ValueError("textures must have identical (..., 3) shapes")
    mismatch = 0.5 * (1.0 - np.sum(texture * shifted_texture, axis=-1))
    return np.maximum(mismatch, 0.0)


def _fourier_modes(size: int) -> Array:
    spacing = TWO_PI / size
    return TWO_PI * np.fft.fftfreq(size, d=spacing)


def spectral_derivative(texture: Array, axis: int) -> Array:
    """Differentiate a periodic texture spectrally along axis 0 or 1."""

    if axis not in (0, 1):
        raise ValueError("axis must be 0 or 1")
    modes = _fourier_modes(texture.shape[axis])
    shape = [1] * texture.ndim
    shape[axis] = modes.size
    multiplier = 1j * modes.reshape(shape)
    transformed = np.fft.fft(texture, axis=axis)
    derivative = np.fft.ifft(transformed * multiplier, axis=axis)
    return np.real_if_close(derivative, tol=1000).real


def periodic_fourier_shift(texture: Array, shift: float, axis: int) -> Array:
    """Evaluate a periodic grid field at k+shift using a Fourier shift."""

    if axis not in (0, 1):
        raise ValueError("axis must be 0 or 1")
    modes = _fourier_modes(texture.shape[axis])
    shape = [1] * texture.ndim
    shape[axis] = modes.size
    phase = np.exp(1j * modes * shift).reshape(shape)
    shifted = np.fft.ifft(np.fft.fft(texture, axis=axis) * phase, axis=axis)
    return np.real_if_close(shifted, tol=1000).real


def directional_mismatch(texture: Array, q: float, axis: int) -> Array:
    """Symmetric mismatch for displacements +q and -q along one axis."""

    plus = projector_mismatch(texture, periodic_fourier_shift(texture, q, axis))
    minus = projector_mismatch(texture, periodic_fourier_shift(texture, -q, axis))
    return 0.5 * (plus + minus)


def jump_metric_estimator(texture: Array, q: float) -> float:
    """Return the four-direction estimator converging to integral tr(g)."""

    if q <= 0.0:
        raise ValueError("q must be positive")
    average_mismatch = 0.5 * (
        directional_mismatch(texture, q, axis=0)
        + directional_mismatch(texture, q, axis=1)
    )
    dk = TWO_PI / texture.shape[0]
    mismatch_integral = float(np.sum(average_mismatch) * dk * dk)
    return 2.0 * mismatch_integral / (q * q)


def _triangle_solid_angle(a: Array, b: Array, c: Array) -> Array:
    numerator = np.sum(a * np.cross(b, c), axis=-1)
    denominator = (
        1.0
        + np.sum(a * b, axis=-1)
        + np.sum(b * c, axis=-1)
        + np.sum(c * a, axis=-1)
    )
    return 2.0 * np.arctan2(numerator, denominator)


def chern_number_solid_angle(texture: Array) -> float:
    """Gauge-free lattice Chern number in the paper's sign convention."""

    a = texture
    b = np.roll(texture, -1, axis=0)
    c = np.roll(b, -1, axis=1)
    d = np.roll(texture, -1, axis=1)
    oriented_area = _triangle_solid_angle(a, b, c) + _triangle_solid_angle(a, c, d)
    # For A=i<u|du>, P=(1+n.sigma)/2 has Omega=-n.(dn x dn)/2.
    return float(-np.sum(oriented_area) / (4.0 * np.pi))


def local_geometry(texture: Array) -> dict[str, Array]:
    """Return the standard quantum metric and Berry-curvature fields."""

    derivative_x = spectral_derivative(texture, axis=0)
    derivative_y = spectral_derivative(texture, axis=1)
    g_xx = 0.25 * np.sum(derivative_x * derivative_x, axis=-1)
    g_yy = 0.25 * np.sum(derivative_y * derivative_y, axis=-1)
    g_xy = 0.25 * np.sum(derivative_x * derivative_y, axis=-1)
    curvature = -0.5 * np.sum(
        texture * np.cross(derivative_x, derivative_y),
        axis=-1,
    )
    return {
        "g_xx": g_xx,
        "g_yy": g_yy,
        "g_xy": g_xy,
        "metric_trace": g_xx + g_yy,
        "curvature": curvature,
    }


def local_geometry_finite_difference(texture: Array) -> dict[str, Array]:
    """Return geometry using centered periodic finite differences.

    This is the reconstructed finite-mesh convention used for the paper's
    sharp bubbling trajectory.  The spectral version above remains the
    high-accuracy default for smooth static textures.
    """

    spacing = TWO_PI / texture.shape[0]
    derivative_x = (
        np.roll(texture, -1, axis=0) - np.roll(texture, 1, axis=0)
    ) / (2.0 * spacing)
    derivative_y = (
        np.roll(texture, -1, axis=1) - np.roll(texture, 1, axis=1)
    ) / (2.0 * spacing)
    g_xx = 0.25 * np.sum(derivative_x * derivative_x, axis=-1)
    g_yy = 0.25 * np.sum(derivative_y * derivative_y, axis=-1)
    g_xy = 0.25 * np.sum(derivative_x * derivative_y, axis=-1)
    curvature = -0.5 * np.sum(
        texture * np.cross(derivative_x, derivative_y),
        axis=-1,
    )
    return {
        "g_xx": g_xx,
        "g_yy": g_yy,
        "g_xy": g_xy,
        "metric_trace": g_xx + g_yy,
        "curvature": curvature,
    }


def geometry_observables(
    texture: Array,
    derivative_scheme: str = "spectral",
) -> GeometryObservables:
    """Integrate quantum geometry and topology on the periodic grid."""

    if derivative_scheme == "spectral":
        fields = local_geometry(texture)
    elif derivative_scheme == "centered_finite_difference":
        fields = local_geometry_finite_difference(texture)
    else:
        raise ValueError(
            "derivative_scheme must be 'spectral' or "
            "'centered_finite_difference'"
        )
    dk = TWO_PI / texture.shape[0]
    area_element = dk * dk
    metric_integral = float(np.sum(fields["metric_trace"]) * area_element)
    curvature_integral = float(np.sum(fields["curvature"]) * area_element)
    absolute_curvature_integral = float(
        np.sum(np.abs(fields["curvature"])) * area_element
    )
    chern = chern_number_solid_angle(texture)
    expected_sign = np.sign(chern)
    if abs(chern) < 0.5:
        opposite_fraction = 0.0
    else:
        significant = np.abs(fields["curvature"]) > 1e-10
        opposite = significant & (np.sign(fields["curvature"]) != expected_sign)
        opposite_fraction = float(np.count_nonzero(opposite) / np.count_nonzero(significant))
    return GeometryObservables(
        chern=chern,
        metric_integral=metric_integral,
        dirichlet_energy=0.5 * metric_integral,
        absolute_curvature_integral=absolute_curvature_integral,
        finite_difference_chern=curvature_integral / TWO_PI,
        opposite_curvature_fraction=opposite_fraction,
        max_norm_error=float(
            np.max(np.abs(np.linalg.norm(texture, axis=-1) - 1.0))
        ),
    )


def finite_difference_laplacian(texture: Array, spacing: float) -> Array:
    """Second-order periodic Laplacian."""

    return (
        np.roll(texture, -1, axis=0)
        + np.roll(texture, 1, axis=0)
        + np.roll(texture, -1, axis=1)
        + np.roll(texture, 1, axis=1)
        - 4.0 * texture
    ) / (spacing * spacing)


def extended_hubbard_lambda_d(
    onsite_u: float,
    nearest_v: float,
    cutoff_q: float,
) -> float:
    """Return the small-q Dirichlet coupling from Supplemental Eq. (131)."""

    if cutoff_q <= 0.0:
        raise ValueError("cutoff_q must be positive")
    return float(
        (
            (onsite_u + 4.0 * nearest_v) * cutoff_q**4 / 4.0
            - nearest_v * cutoff_q**6 / 6.0
        )
        / (4.0 * np.pi)
    )


def extended_hubbard_convolution(
    texture: Array,
    onsite_u: float,
    nearest_v: float,
    spacing: float,
    grid_offset_fraction: float = 0.0,
) -> Array:
    """Evaluate ``∫dq v(q)n(k-q)`` for Supplemental Eq. (128).

    For ``v(q)=U+2V(cos(q_x)+cos(q_y))`` the circular convolution has only
    five Fourier moments.  Evaluating those moments is algebraically
    identical to a dense periodic convolution but avoids an O(N^4) loop.
    """

    unit_texture = normalize_texture(texture)
    if unit_texture.shape[0] != unit_texture.shape[1]:
        raise ValueError("texture must live on a square momentum grid")
    kx, ky, expected_spacing = momentum_grid(
        unit_texture.shape[0],
        grid_offset_fraction,
    )
    if not np.isclose(spacing, expected_spacing, rtol=0.0, atol=1e-14):
        raise ValueError("spacing does not match the texture grid")

    area_element = spacing * spacing

    def moment(weight: Array) -> Array:
        return np.sum(weight[..., None] * unit_texture, axis=(0, 1)) * area_element

    mean = np.sum(unit_texture, axis=(0, 1)) * area_element
    cos_x = moment(np.cos(kx))
    sin_x = moment(np.sin(kx))
    cos_y = moment(np.cos(ky))
    sin_y = moment(np.sin(ky))
    return (
        onsite_u * mean
        + 2.0
        * nearest_v
        * (
            np.cos(kx)[..., None] * cos_x
            + np.sin(kx)[..., None] * sin_x
            + np.cos(ky)[..., None] * cos_y
            + np.sin(ky)[..., None] * sin_y
        )
    )


def llg_rhs(
    texture: Array,
    d_vector: Array,
    spacing: float,
    gamma: float,
    lambda_d: float,
    lambda_t: float,
) -> Array:
    """Right-hand side of the paper's two-band LLG equation."""

    unit_texture = normalize_texture(texture)
    effective_field = (
        2.0 * lambda_t * d_vector
        - lambda_d * finite_difference_laplacian(unit_texture, spacing)
    ) / (TWO_PI * TWO_PI)
    precession = -np.cross(unit_texture, effective_field)
    damping = gamma * np.cross(
        unit_texture,
        np.cross(unit_texture, effective_field),
    )
    return precession + damping


def exact_extended_hubbard_rhs(
    texture: Array,
    d_vector: Array,
    spacing: float,
    gamma: float,
    onsite_u: float,
    nearest_v: float,
    lambda_t: float,
    grid_offset_fraction: float = 0.0,
) -> Array:
    """Right-hand side of Supplemental Eqs. (127)-(128)."""

    unit_texture = normalize_texture(texture)
    interaction = extended_hubbard_convolution(
        unit_texture,
        onsite_u,
        nearest_v,
        spacing,
        grid_offset_fraction,
    )
    effective_field = (
        2.0 * lambda_t * d_vector - interaction / (np.pi * np.pi)
    ) / (TWO_PI * TWO_PI)
    precession = -np.cross(unit_texture, effective_field)
    damping = gamma * np.cross(
        unit_texture,
        np.cross(unit_texture, effective_field),
    )
    return precession + damping


def _rk4_projected_step(
    texture: Array,
    step: float,
    rhs,
) -> Array:
    """Advance a tangent unit-vector flow and project away roundoff drift."""

    k1 = rhs(texture)
    k2 = rhs(texture + 0.5 * step * k1)
    k3 = rhs(texture + 0.5 * step * k2)
    k4 = rhs(texture + step * k3)
    return normalize_texture(
        texture + step * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
    )


def rk4_step(
    texture: Array,
    step: float,
    d_vector: Array,
    spacing: float,
    gamma: float,
    lambda_d: float,
    lambda_t: float,
) -> Array:
    """One projected fourth-order Runge–Kutta step."""

    def rhs(state: Array) -> Array:
        return llg_rhs(state, d_vector, spacing, gamma, lambda_d, lambda_t)

    return _rk4_projected_step(texture, step, rhs)


def rk4_step_exact_extended_hubbard(
    texture: Array,
    step: float,
    d_vector: Array,
    spacing: float,
    gamma: float,
    onsite_u: float,
    nearest_v: float,
    lambda_t: float,
    grid_offset_fraction: float = 0.0,
) -> Array:
    """Advance the exact extended-Hubbard flow by one RK4 step."""

    def rhs(state: Array) -> Array:
        return exact_extended_hubbard_rhs(
            state,
            d_vector,
            spacing,
            gamma,
            onsite_u,
            nearest_v,
            lambda_t,
            grid_offset_fraction,
        )

    return _rk4_projected_step(texture, step, rhs)


def paper_energy_components(
    texture: Array,
    d_vector: Array,
    lambda_d: float,
    lambda_t: float,
) -> dict[str, float]:
    """Return the energy terms in the main text's internally consistent units."""

    geometry = geometry_observables(texture)
    hopping_energy = float(np.mean(np.sum(d_vector * texture, axis=-1)))
    hopping_component = lambda_t * hopping_energy
    dirichlet_component = (
        2.0 * lambda_d * geometry.dirichlet_energy / (TWO_PI * TWO_PI)
    )
    return {
        "hopping_energy": hopping_energy,
        "hopping_component": hopping_component,
        "dirichlet_component": dirichlet_component,
        "total_energy": hopping_component + dirichlet_component,
    }


def integrate_llg(
    size: int,
    mass: float,
    gamma: float,
    lambda_d: float,
    lambda_t: float,
    time_max: float,
    time_step: float,
    sample_interval: float,
    q_probe: float,
) -> tuple[list[dict[str, float]], Array]:
    """Integrate the paper LLG flow and return diagnostic rows."""

    if time_max <= 0.0 or time_step <= 0.0 or sample_interval <= 0.0:
        raise ValueError("times and steps must be positive")
    d_vector = qwz_d_vector(size, mass)
    texture = normalize_texture(-d_vector)
    _, _, spacing = momentum_grid(size)
    steps = int(round(time_max / time_step))
    sample_steps = max(1, int(round(sample_interval / time_step)))
    rows: list[dict[str, float]] = []

    def record(step_index: int) -> None:
        time = step_index * time_step
        geometry = geometry_observables(texture)
        energies = paper_energy_components(texture, d_vector, lambda_d, lambda_t)
        rows.append(
            {
                "time": float(time),
                "chern": geometry.chern,
                "metric_integral": geometry.metric_integral,
                "dirichlet_energy": geometry.dirichlet_energy,
                "jump_metric_estimator": jump_metric_estimator(texture, q_probe),
                "absolute_curvature_integral": geometry.absolute_curvature_integral,
                "opposite_curvature_fraction": geometry.opposite_curvature_fraction,
                "max_norm_error": geometry.max_norm_error,
                **energies,
            }
        )

    record(0)
    for step_index in range(1, steps + 1):
        texture = rk4_step(
            texture,
            time_step,
            d_vector,
            spacing,
            gamma,
            lambda_d,
            lambda_t,
        )
        if step_index % sample_steps == 0 or step_index == steps:
            record(step_index)
    return rows, texture


def integrate_extended_hubbard_comparison(
    size: int,
    mass: float,
    gamma: float,
    onsite_u: float,
    nearest_v: float,
    lambda_t: float,
    cutoff_q: float,
    time_max: float,
    time_step: float,
    sample_interval: float,
    snapshot_times: tuple[float, ...] = (),
    grid_offset_fraction: float = 0.5,
) -> tuple[list[dict[str, float]], dict[float, dict[str, Array]]]:
    """Integrate exact and small-q flows with identical initial conditions.

    The returned snapshots are keyed by the requested physical times and hold
    independent copies of both textures.  A requested time must lie on the
    integration grid so that target artifacts do not silently interpolate a
    nonlinear trajectory.
    """

    if time_max <= 0.0 or time_step <= 0.0 or sample_interval <= 0.0:
        raise ValueError("times and steps must be positive")
    d_vector = qwz_d_vector(size, mass, grid_offset_fraction)
    exact = normalize_texture(-d_vector)
    approximate = exact.copy()
    _, _, spacing = momentum_grid(size, grid_offset_fraction)
    lambda_d = extended_hubbard_lambda_d(onsite_u, nearest_v, cutoff_q)
    steps = int(round(time_max / time_step))
    if not np.isclose(steps * time_step, time_max, atol=1e-12):
        raise ValueError("time_max must be an integer multiple of time_step")
    sample_steps = max(1, int(round(sample_interval / time_step)))
    snapshot_step_map: dict[int, float] = {}
    for requested in snapshot_times:
        step_index = int(round(requested / time_step))
        if not np.isclose(step_index * time_step, requested, atol=1e-12):
            raise ValueError("snapshot times must lie on the integration grid")
        if step_index < 0 or step_index > steps:
            raise ValueError("snapshot time lies outside the integration range")
        snapshot_step_map[step_index] = float(requested)

    rows: list[dict[str, float]] = []
    snapshots: dict[float, dict[str, Array]] = {}

    def record(step_index: int) -> None:
        exact_geometry = geometry_observables(exact)
        approximate_geometry = geometry_observables(approximate)
        exact_centered = geometry_observables(
            exact,
            derivative_scheme="centered_finite_difference",
        )
        approximate_centered = geometry_observables(
            approximate,
            derivative_scheme="centered_finite_difference",
        )
        rows.append(
            {
                "time": float(step_index * time_step),
                "exact_dirichlet_energy": exact_geometry.dirichlet_energy,
                "small_q_dirichlet_energy": approximate_geometry.dirichlet_energy,
                "exact_chern_solid_angle": exact_geometry.chern,
                "small_q_chern_solid_angle": approximate_geometry.chern,
                "exact_chern_mesh_integral": exact_geometry.finite_difference_chern,
                "small_q_chern_mesh_integral": approximate_geometry.finite_difference_chern,
                "exact_centered_dirichlet_energy": exact_centered.dirichlet_energy,
                "small_q_centered_dirichlet_energy": approximate_centered.dirichlet_energy,
                "exact_centered_chern_mesh_integral": exact_centered.finite_difference_chern,
                "small_q_centered_chern_mesh_integral": approximate_centered.finite_difference_chern,
                "exact_opposite_curvature_fraction": exact_geometry.opposite_curvature_fraction,
                "small_q_opposite_curvature_fraction": approximate_geometry.opposite_curvature_fraction,
                "exact_max_norm_error": exact_geometry.max_norm_error,
                "small_q_max_norm_error": approximate_geometry.max_norm_error,
            }
        )

    if 0 in snapshot_step_map:
        snapshots[snapshot_step_map[0]] = {
            "exact": exact.copy(),
            "small_q": approximate.copy(),
        }
    record(0)
    for step_index in range(1, steps + 1):
        exact = rk4_step_exact_extended_hubbard(
            exact,
            time_step,
            d_vector,
            spacing,
            gamma,
            onsite_u,
            nearest_v,
            lambda_t,
            grid_offset_fraction,
        )
        approximate = rk4_step(
            approximate,
            time_step,
            d_vector,
            spacing,
            gamma,
            lambda_d,
            lambda_t,
        )
        if step_index in snapshot_step_map:
            snapshots[snapshot_step_map[step_index]] = {
                "exact": exact.copy(),
                "small_q": approximate.copy(),
            }
        if step_index % sample_steps == 0 or step_index == steps:
            record(step_index)
    return rows, snapshots


def integrate_exact_extended_hubbard(
    size: int,
    mass: float,
    gamma: float,
    onsite_u: float,
    nearest_v: float,
    lambda_t: float,
    time_max: float,
    time_step: float,
    sample_interval: float,
    grid_offset_fraction: float = 0.5,
) -> list[dict[str, float]]:
    """Integrate only the exact extended-Hubbard flow.

    This is the parameter-sweep path for Supplemental Fig. 6.  It deliberately
    reuses the same exact right-hand side, midpoint momentum grid, projected
    RK4 step, and spectral observables as the main exact-versus-small-q target.
    """

    if time_max <= 0.0 or time_step <= 0.0 or sample_interval <= 0.0:
        raise ValueError("times and steps must be positive")
    d_vector = qwz_d_vector(size, mass, grid_offset_fraction)
    texture = normalize_texture(-d_vector)
    _, _, spacing = momentum_grid(size, grid_offset_fraction)
    steps = int(round(time_max / time_step))
    if not np.isclose(steps * time_step, time_max, atol=1e-12):
        raise ValueError("time_max must be an integer multiple of time_step")
    sample_steps = max(1, int(round(sample_interval / time_step)))
    rows: list[dict[str, float]] = []

    def record(step_index: int) -> None:
        geometry = geometry_observables(texture)
        rows.append(
            {
                "time": float(step_index * time_step),
                "dirichlet_energy": geometry.dirichlet_energy,
                "chern_mesh_integral": geometry.finite_difference_chern,
                "chern_solid_angle": geometry.chern,
                "max_norm_error": geometry.max_norm_error,
            }
        )

    record(0)
    for step_index in range(1, steps + 1):
        texture = rk4_step_exact_extended_hubbard(
            texture,
            time_step,
            d_vector,
            spacing,
            gamma,
            onsite_u,
            nearest_v,
            lambda_t,
            grid_offset_fraction,
        )
        if step_index % sample_steps == 0 or step_index == steps:
            record(step_index)
    return rows
