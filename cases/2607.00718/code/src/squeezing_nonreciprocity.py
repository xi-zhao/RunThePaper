"""Analytic core for arXiv:2607.00718.

The paper's numerical figures are driven by a small set of closed expressions:

* the squeezing-dependent nonreciprocal coupling;
* the three steady-state battery energies;
* their coupling derivatives; and
* the normal and anomalous forward scattering channels.

Keeping these expressions in one module makes the physical conventions shared
across the main-text and supplemental targets.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.sparse.linalg import expm_multiply


BatteryCase = Literal["a", "b", "c"]
FloatArray = NDArray[np.float64]


def _as_float_array(value: ArrayLike) -> FloatArray:
    return np.asarray(value, dtype=float)


def effective_enhancement(
    r_a: ArrayLike,
    r_b: ArrayLike,
    delta_theta: ArrayLike,
) -> FloatArray:
    """Return ``G = |J_eff/(2J)|`` from main-text Eq. (4)."""

    r_a_array = _as_float_array(r_a)
    r_b_array = _as_float_array(r_b)
    phase_array = _as_float_array(delta_theta)
    amplitude = (
        np.cosh(r_a_array) * np.cosh(r_b_array)
        - np.exp(1j * phase_array) * np.sinh(r_a_array) * np.sinh(r_b_array)
    )
    return np.asarray(np.abs(amplitude), dtype=float)


def steady_state_energy_nonsqueezed(
    coupling: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return the nonsqueezed steady-state battery energy ``E^ss``."""

    coupling_array = _as_float_array(coupling)
    decay = 2.0 * coupling_array + kappa
    return np.asarray(64.0 * coupling_array**2 * drive**2 / decay**4, dtype=float)


def steady_state_energy(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return ``E_i^ss`` for battery cases (a), (b), or (c)."""

    coupling_array = _as_float_array(coupling)
    squeezing_array = _as_float_array(squeezing)
    decay = 2.0 * coupling_array + kappa
    occupation = np.sinh(squeezing_array) ** 2
    baseline = steady_state_energy_nonsqueezed(coupling_array, kappa, drive)

    if case == "a":
        squeezing_term = 8.0 * coupling_array**2 * kappa * occupation / decay**3
    elif case == "b":
        squeezing_term = (
            2.0
            * coupling_array
            * (4.0 * coupling_array**2 + kappa**2)
            * occupation
            / decay**3
        )
    elif case == "c":
        squeezing_term = 2.0 * coupling_array * occupation / decay
    else:
        raise ValueError(f"unknown battery case: {case}")

    return np.asarray(baseline + squeezing_term, dtype=float)


def steady_state_energy_enhancement(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return the dimensionless enhancement ``E_i^ss / E^ss``.

    Keeping the normalization next to the closed energy expression prevents a
    plotted curve from silently switching between absolute energy and
    enhancement-factor semantics.
    """

    baseline = steady_state_energy_nonsqueezed(coupling, kappa, drive)
    if np.any(baseline == 0.0):
        raise ValueError("steady-state enhancement is undefined at zero baseline")
    return np.asarray(
        steady_state_energy(case, coupling, squeezing, kappa, drive) / baseline,
        dtype=float,
    )


def steady_state_energy_derivative(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return the supplement's closed ``partial E_i^ss / partial J``."""

    coupling_array = _as_float_array(coupling)
    squeezing_array = _as_float_array(squeezing)
    decay = 2.0 * coupling_array + kappa
    occupation = np.sinh(squeezing_array) ** 2

    if case == "a":
        numerator = 16.0 * coupling_array * (
            8.0 * drive**2 * (kappa - 2.0 * coupling_array)
            + kappa * (kappa - coupling_array) * decay * occupation
        )
    elif case == "b":
        numerator = (
            128.0 * coupling_array * drive**2 * (kappa - 2.0 * coupling_array)
            + 2.0
            * kappa
            * decay
            * (12.0 * coupling_array**2 - 4.0 * coupling_array * kappa + kappa**2)
            * occupation
        )
    elif case == "c":
        numerator = 2.0 * (
            64.0 * coupling_array * drive**2 * (kappa - 2.0 * coupling_array)
            + kappa * decay**3 * occupation
        )
    else:
        raise ValueError(f"unknown battery case: {case}")

    return np.asarray(numerator / decay**5, dtype=float)


def normal_channel_strength_squared(
    r_a: ArrayLike,
    r_b: ArrayLike,
    delta_theta: ArrayLike,
) -> FloatArray:
    """Squared normal forward-channel amplitude in supplemental Eq. (S34)."""

    r_a_array = _as_float_array(r_a)
    r_b_array = _as_float_array(r_b)
    phase_array = _as_float_array(delta_theta)
    value = (
        2.0
        + np.cosh(2.0 * (r_a_array - r_b_array))
        + np.cosh(2.0 * (r_a_array + r_b_array))
        - 2.0
        * np.cos(phase_array)
        * np.sinh(2.0 * r_a_array)
        * np.sinh(2.0 * r_b_array)
    ) / 4.0
    return np.asarray(value, dtype=float)


def anomalous_channel_strength_squared(
    r_a: ArrayLike,
    r_b: ArrayLike,
    delta_theta: ArrayLike,
) -> FloatArray:
    """Squared anomalous forward-channel amplitude in supplemental Eq. (S34)."""

    r_a_array = _as_float_array(r_a)
    r_b_array = _as_float_array(r_b)
    phase_array = _as_float_array(delta_theta)
    value = (
        np.sinh(r_a_array) ** 2 * np.cosh(r_b_array) ** 2
        + np.cosh(r_a_array) ** 2 * np.sinh(r_b_array) ** 2
        - 0.5
        * np.cos(phase_array)
        * np.sinh(2.0 * r_a_array)
        * np.sinh(2.0 * r_b_array)
    )
    return np.asarray(value, dtype=float)


def forward_transmission(
    omega: ArrayLike,
    omega_s: ArrayLike,
    r_a: float,
    r_b: float,
    delta_theta: float,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    collective_decay: float,
) -> FloatArray:
    """Return the general forward power transmission ``T_ba``.

    This is the two-channel expression at the end of the Supplemental
    Material.  ``Lambda_h = kappa_h + collective_decay`` assumes
    ``|p_h| = 1``, as in the plotted figure.
    """

    omega_array = _as_float_array(omega)
    squeezed_frequency = _as_float_array(omega_s)
    lambda_a = kappa_a + collective_decay
    lambda_b = kappa_b + collective_decay
    shifted = 2.0 * omega_array + squeezed_frequency
    conjugate_shifted = -2.0 * omega_array + squeezed_frequency
    prefactor = 64.0 * coupling**2 * kappa_a * kappa_b
    normal = normal_channel_strength_squared(r_a, r_b, delta_theta)
    anomalous = anomalous_channel_strength_squared(r_a, r_b, delta_theta)

    value = prefactor / (lambda_b**2 + shifted**2) * (
        normal / (lambda_a**2 + shifted**2)
        + anomalous / (lambda_a**2 + conjugate_shifted**2)
    )
    return np.asarray(value, dtype=float)


def forward_transmission_zero_squeezed_frequency(
    omega: ArrayLike,
    r_a: float,
    r_b: float,
    delta_theta: float,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    collective_decay: float,
) -> FloatArray:
    """Return the main-text ``omega_s = 0`` transmission formula."""

    omega_array = _as_float_array(omega)
    lambda_a = kappa_a + collective_decay
    lambda_b = kappa_b + collective_decay
    squeeze_factor = (
        np.cosh(2.0 * r_a) * np.cosh(2.0 * r_b)
        - np.cos(delta_theta) * np.sinh(2.0 * r_a) * np.sinh(2.0 * r_b)
    )
    numerator = 64.0 * coupling**2 * kappa_a * kappa_b * squeeze_factor
    denominator = (lambda_a**2 + 4.0 * omega_array**2) * (
        lambda_b**2 + 4.0 * omega_array**2
    )
    return np.asarray(numerator / denominator, dtype=float)


def optimal_transmission_coupling(kappa_a: float, kappa_b: float) -> float:
    """Return ``J'_op = sqrt(kappa_a kappa_b) / 2``."""

    return float(np.sqrt(kappa_a * kappa_b) / 2.0)


def gaussian_invariant(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return the single-mode Gaussian invariant ``mathcal J_i``.

    This is the closed expression printed in Supplemental Sec. V after
    setting ``Lambda_a = Lambda_b = 2 J + kappa``.  The result determines the
    passive-state energy and therefore the steady-state ergotropy.
    """

    coupling_array = _as_float_array(coupling)
    squeezing_array = _as_float_array(squeezing)
    decay = 2.0 * coupling_array + kappa
    cosh_r = np.cosh(squeezing_array)
    sinh_r = np.sinh(squeezing_array)

    if case == "a":
        first = (
            (8.0 * (1.0 - 1.0j) * drive**2 + (2.0 * coupling_array - decay) * decay)
            * cosh_r
            - 8.0 * (1.0 - 1.0j) * drive**2 * sinh_r
        )
        second = (
            (-8.0 * (1.0 + 1.0j) * drive**2 - (2.0 * coupling_array - decay) * decay)
            * cosh_r
            + 8.0 * (1.0 + 1.0j) * drive**2 * sinh_r
        )
        centered = (
            -8.0 * coupling_array**2 * decay
            + decay**3
            + 8.0
            * coupling_array**2
            * (decay * np.cosh(2.0 * squeezing_array) - 4.0 * coupling_array * sinh_r**2)
        )
        value = (
            256.0
            * coupling_array**4
            * sinh_r**2
            * first
            * second
            / decay**8
            + centered**2 / decay**6
        )
    elif case == "b":
        normal = (
            (2.0 * coupling_array - decay) * (8.0 * coupling_array**2 + decay**2)
            - 2.0
            * coupling_array
            * (8.0 * coupling_array**2 - 4.0 * coupling_array * decay + decay**2)
            * np.cosh(2.0 * squeezing_array)
        )
        anomalous = (
            64.0 * coupling_array * drive**2 * (1.0 - cosh_r)
            + (
                2.0 * decay**3
                + 16.0 * coupling_array**2 * decay
                - 8.0 * coupling_array * decay**2
            )
            * np.sinh(2.0 * squeezing_array)
        )
        value = (decay**2 * normal**2 - coupling_array**2 * anomalous**2) / decay**8
    elif case == "c":
        polynomial = 8.0 * coupling_array**2 - 4.0 * coupling_array * decay + decay**2
        quartic = (
            -32.0 * coupling_array**4
            + 16.0 * coupling_array**3 * decay
            - decay**4
            + 16.0
            * coupling_array**3
            * (2.0 * coupling_array - decay)
            * np.cosh(4.0 * squeezing_array)
        )
        value = (
            4.0
            * coupling_array
            * decay**4
            * (decay - 2.0 * coupling_array)
            * np.cosh(2.0 * squeezing_array)
            - polynomial * quartic
        ) / decay**6
    else:
        raise ValueError(f"unknown battery case: {case}")

    real_value = np.real_if_close(value, tol=1000)
    real_array = np.asarray(np.real(real_value), dtype=float)
    return np.maximum(real_array, 0.0)


def passive_state_energy(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return ``(sqrt(mathcal J_i) - 1) / 2`` in units of ``omega_b``."""

    invariant = gaussian_invariant(case, coupling, squeezing, kappa, drive)
    energy = (np.sqrt(invariant) - 1.0) / 2.0
    return np.maximum(np.asarray(energy, dtype=float), 0.0)


def steady_state_ergotropy(
    case: BatteryCase,
    coupling: ArrayLike,
    squeezing: ArrayLike,
    kappa: float,
    drive: float,
) -> FloatArray:
    """Return steady-state ergotropy from total minus passive energy."""

    total = steady_state_energy(case, coupling, squeezing, kappa, drive)
    passive = passive_state_energy(case, coupling, squeezing, kappa, drive)
    return np.maximum(np.asarray(total - passive, dtype=float), 0.0)


def closed_charger_squeezed_energy_dynamics(
    times: ArrayLike,
    coupling: float,
    lambda_a: float,
    lambda_b: float,
    drive: float,
    squeezing: float,
) -> FloatArray:
    """Return the published zero-detuning case-(a) battery energy.

    This is Supplemental Sec. IV's closed expression for ``E_a(t)`` after
    analytically combining its exponential prefactor with every term in the
    braces.  The scaled form avoids exponentially large intermediates.  The
    printed expression contains a removable pole at ``lambda_a == lambda_b``;
    the deposited Fig. 2 data evaluates it with a ``1e-7`` rate offset, which
    callers must pass explicitly rather than hiding here.
    """

    time_array = _as_float_array(times).reshape(-1)
    if np.any(time_array < 0.0) or np.any(np.diff(time_array) < 0.0):
        raise ValueError("times must be nonnegative and monotonically increasing")

    if abs(lambda_a - lambda_b) <= np.finfo(float).eps * max(
        abs(lambda_a), abs(lambda_b)
    ):
        raise ValueError(
            "the published closed expression requires an explicit "
            "lambda_a/lambda_b regularizer"
        )

    with localcontext() as context:
        context.prec = 50
        j = Decimal(str(coupling))
        la = Decimal(str(lambda_a))
        lb = Decimal(str(lambda_b))
        epsilon = Decimal(str(drive))
        r = Decimal(str(squeezing))
        two = Decimal(2)
        four = Decimal(4)
        eight = Decimal(8)
        lambda_minus = la - lb
        lambda_plus = la + lb
        exp_minus_two_r = (-two * r).exp()
        one_plus_exp_four_r = Decimal(1) + (four * r).exp()
        denominator = la**2 * lb**2 * lambda_minus**2 * lambda_plus
        prefactor = -four * j**2 / denominator
        values: list[float] = []
        for time_value in time_array:
            time = Decimal(str(float(time_value)))
            exp_minus_la = (-la * time).exp()
            exp_minus_lb = (-lb * time).exp()
            exp_minus_half_la = (-la * time / two).exp()
            exp_minus_half_lb = (-lb * time / two).exp()
            exp_minus_half_sum = (-lambda_plus * time / two).exp()
            scaled_braces = (
                one_plus_exp_four_r
                * (two * j - la)
                * (
                    la * lb * lambda_minus**2 * exp_minus_two_r
                    + four
                    * la**2
                    * lb**2
                    * exp_minus_two_r
                    * exp_minus_half_sum
                )
                + Decimal(32)
                * epsilon**2
                * lambda_plus
                * lambda_minus
                * (la * exp_minus_half_lb - lb * exp_minus_half_la)
                + la
                * lb
                * lambda_plus
                * one_plus_exp_four_r
                * (la - two * j)
                * (
                    la * exp_minus_two_r * exp_minus_lb
                    + lb * exp_minus_two_r * exp_minus_la
                )
                - two
                * lb**2
                * lambda_plus
                * (eight * epsilon**2 - two * j * la + la**2)
                * exp_minus_la
                - two
                * la**2
                * lambda_plus
                * (eight * epsilon**2 - two * j * lb + la * lb)
                * exp_minus_lb
                + eight
                * la
                * lb
                * (
                    four * epsilon**2 * lambda_plus
                    - two * j * la * lb
                    + la**2 * lb
                )
                * exp_minus_half_sum
                - two
                * lambda_minus**2
                * (
                    eight * epsilon**2 * lambda_plus
                    + two * j * la * lb
                    - la**2 * lb
                )
            )
            values.append(float(prefactor * scaled_braces))

    result = np.asarray(values, dtype=float)
    result[np.abs(result) < 1e-12] = 0.0
    return np.maximum(result, 0.0)


def gaussian_battery_energy_dynamics(
    case: Literal["baseline", "a", "b", "c"],
    times: ArrayLike,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    drive: float,
    squeezing: float,
    omega_s: float = 0.0,
    charger_phase: float = np.pi,
    reservoir_phase: float = np.pi,
) -> FloatArray:
    """Propagate the closed affine first/second-moment system.

    The state contains the two first moments and the six independent Gaussian
    second moments together with their conjugates.  The affine generator is
    exponentiated directly, avoiding a Hilbert-space cutoff and keeping the
    time-domain targets tied to Supplemental Eq. (S18) and the general moment
    equations preceding it.  ``omega_s`` is the charger-mode detuning between
    squeezed mode ``a_s`` and the unsqueezed battery mode ``b``; it therefore
    enters only moments containing ``a_s``.
    """

    time_array = _as_float_array(times).reshape(-1)
    if time_array.size == 0:
        return np.asarray([], dtype=float)
    if np.any(time_array < 0.0) or np.any(np.diff(time_array) < 0.0):
        raise ValueError("times must be nonnegative and monotonically increasing")
    if time_array.size > 2:
        steps = np.diff(time_array)
        if not np.allclose(steps, steps[0], rtol=1e-10, atol=1e-13):
            raise ValueError("gaussian propagation currently requires an evenly spaced time grid")

    if case == "baseline":
        charger_squeezing = 0.0
        reservoir_squeezing = 0.0
    elif case == "a":
        charger_squeezing = squeezing
        reservoir_squeezing = 0.0
    elif case == "b":
        charger_squeezing = 0.0
        reservoir_squeezing = squeezing
    elif case == "c":
        charger_squeezing = squeezing
        reservoir_squeezing = squeezing
    else:
        raise ValueError(f"unknown battery dynamics case: {case}")

    generator = _gaussian_affine_generator(
        coupling=coupling,
        kappa_a=kappa_a,
        kappa_b=kappa_b,
        drive=drive,
        charger_squeezing=charger_squeezing,
        reservoir_squeezing=reservoir_squeezing,
        omega_s=omega_s,
        charger_phase=charger_phase,
        reservoir_phase=reservoir_phase,
    )
    initial = np.zeros(generator.shape[0], dtype=complex)
    initial[-1] = 1.0
    if time_array.size == 1:
        if time_array[0] == 0.0:
            states = initial[np.newaxis, :]
        else:
            states = expm_multiply(generator * time_array[0], initial)[np.newaxis, :]
    else:
        states = expm_multiply(
            generator,
            initial,
            start=float(time_array[0]),
            stop=float(time_array[-1]),
            num=int(time_array.size),
            endpoint=True,
            traceA=np.trace(generator),
        )
    energy = np.asarray(np.real(states[:, 13]), dtype=float)
    energy[np.abs(energy) < 1e-13] = 0.0
    return np.maximum(energy, 0.0)


def gaussian_master_equation_energy_dynamics(
    case: Literal["baseline", "a", "b", "c"],
    times: ArrayLike,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    drive: float,
    squeezing: float,
    omega_s: float = 0.0,
    charger_phase: float = 0.0,
    reservoir_phase: float = 0.0,
    coherent_phase: float = np.pi / 2.0,
) -> FloatArray:
    """Propagate the paper's quadratic master equation in Gaussian form.

    The quadrature state ``(q_a, p_a, q_b, p_b)`` is advanced through its
    first moments and covariance matrix.  Local loss uses ordinary vacuum
    collapse operators, while the pure squeezed common reservoir is represented
    by its equivalent Bogoliubov collapse operator.  This keeps the anomalous
    reservoir correlations required at finite ``omega_s`` without a
    Hilbert-space cutoff.
    """

    time_array = _as_float_array(times).reshape(-1)
    if time_array.size == 0:
        return np.asarray([], dtype=float)
    if np.any(time_array < 0.0) or np.any(np.diff(time_array) < 0.0):
        raise ValueError("times must be nonnegative and monotonically increasing")
    if time_array.size > 2:
        steps = np.diff(time_array)
        if not np.allclose(steps, steps[0], rtol=1e-10, atol=1e-13):
            raise ValueError("Gaussian propagation requires an evenly spaced time grid")

    if case == "baseline":
        charger_squeezing = 0.0
        reservoir_squeezing = 0.0
    elif case == "a":
        charger_squeezing = squeezing
        reservoir_squeezing = 0.0
    elif case == "b":
        charger_squeezing = 0.0
        reservoir_squeezing = squeezing
    elif case == "c":
        charger_squeezing = squeezing
        reservoir_squeezing = squeezing
    else:
        raise ValueError(f"unknown battery dynamics case: {case}")

    drift, diffusion, forcing = _quadrature_master_equation(
        coupling=coupling,
        kappa_a=kappa_a,
        kappa_b=kappa_b,
        drive=drive,
        charger_squeezing=charger_squeezing,
        reservoir_squeezing=reservoir_squeezing,
        omega_s=omega_s,
        charger_phase=charger_phase,
        reservoir_phase=reservoir_phase,
        coherent_phase=coherent_phase,
    )
    state_size = 20

    def derivative(state: FloatArray) -> FloatArray:
        mean = state[:4]
        covariance = state[4:].reshape(4, 4)
        mean_derivative = drift @ mean + forcing
        covariance_derivative = (
            drift @ covariance + covariance @ drift.T + diffusion
        )
        return np.concatenate((mean_derivative, covariance_derivative.reshape(-1)))

    zero = np.zeros(state_size, dtype=float)
    constant = derivative(zero)
    linear = np.empty((state_size, state_size), dtype=float)
    for column in range(state_size):
        basis = np.zeros(state_size, dtype=float)
        basis[column] = 1.0
        linear[:, column] = derivative(basis) - constant
    generator = np.zeros((state_size + 1, state_size + 1), dtype=float)
    generator[:state_size, :state_size] = linear
    generator[:state_size, -1] = constant

    initial = np.zeros(state_size + 1, dtype=float)
    initial[4:20] = (0.5 * np.eye(4)).reshape(-1)
    initial[-1] = 1.0
    if time_array.size == 1:
        if time_array[0] == 0.0:
            states = initial[np.newaxis, :]
        else:
            states = expm_multiply(generator * time_array[0], initial)[np.newaxis, :]
    else:
        states = expm_multiply(
            generator,
            initial,
            start=float(time_array[0]),
            stop=float(time_array[-1]),
            num=int(time_array.size),
            endpoint=True,
            traceA=np.trace(generator),
        )

    means_b = states[:, 2:4]
    covariance_b_trace = states[:, 14] + states[:, 19]
    energy = (
        covariance_b_trace + np.sum(means_b**2, axis=1) - 1.0
    ) / 2.0
    energy[np.abs(energy) < 1e-12] = 0.0
    return np.maximum(np.asarray(energy, dtype=float), 0.0)


def _quadrature_master_equation(
    *,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    drive: float,
    charger_squeezing: float,
    reservoir_squeezing: float,
    omega_s: float,
    charger_phase: float,
    reservoir_phase: float,
    coherent_phase: float,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    inverse_sqrt_two = 1.0 / np.sqrt(2.0)
    annihilation_a = inverse_sqrt_two * np.asarray([1.0, 1.0j, 0.0, 0.0])
    annihilation_b = inverse_sqrt_two * np.asarray([0.0, 0.0, 1.0, 1.0j])
    creation_a = np.conj(annihilation_a)
    creation_b = np.conj(annihilation_b)

    hamiltonian = np.zeros((4, 4), dtype=complex)

    def add_product(
        coefficient: complex,
        left: NDArray[np.complex128],
        right: NDArray[np.complex128],
    ) -> None:
        nonlocal hamiltonian
        hamiltonian += coefficient * (
            np.outer(left, right) + np.outer(right, left)
        )

    add_product(omega_s, creation_a, annihilation_a)
    cosh_a = np.cosh(charger_squeezing)
    sinh_a = np.sinh(charger_squeezing)
    squeezed_creation_a = (
        cosh_a * creation_a
        - np.exp(1.0j * charger_phase) * sinh_a * annihilation_a
    )
    squeezed_annihilation_a = np.conj(squeezed_creation_a)
    forward_coefficient = coupling * np.exp(1.0j * coherent_phase)
    add_product(forward_coefficient, squeezed_creation_a, annihilation_b)
    add_product(
        np.conj(forward_coefficient),
        creation_b,
        squeezed_annihilation_a,
    )
    hamiltonian_real = np.asarray(
        np.real_if_close(hamiltonian, tol=1000),
        dtype=float,
    )

    drive_coefficient = drive * (
        cosh_a - np.exp(1.0j * charger_phase) * sinh_a
    )
    forcing_hamiltonian = np.asarray(
        np.real_if_close(
            drive_coefficient * annihilation_a
            + np.conj(drive_coefficient) * creation_a,
            tol=1000,
        ),
        dtype=float,
    )

    collapse_rows = [
        np.sqrt(kappa_a) * annihilation_a,
        np.sqrt(kappa_b) * annihilation_b,
    ]
    collective_annihilation = squeezed_annihilation_a + annihilation_b
    collective_creation = np.conj(collective_annihilation)
    squeezed_collective = np.sqrt(2.0 * coupling) * (
        np.cosh(reservoir_squeezing) * collective_annihilation
        - np.exp(1.0j * reservoir_phase)
        * np.sinh(reservoir_squeezing)
        * collective_creation
    )
    collapse_rows.append(squeezed_collective)
    collapse_matrix = np.vstack(collapse_rows)
    damping_matrix = collapse_matrix.conj().T @ collapse_matrix
    symplectic = np.asarray(
        [
            [0.0, 1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0, 0.0],
        ]
    )
    drift = symplectic @ (hamiltonian_real + np.imag(damping_matrix))
    diffusion = symplectic @ np.real(damping_matrix) @ symplectic.T
    forcing = symplectic @ forcing_hamiltonian
    return (
        np.asarray(drift, dtype=float),
        np.asarray(diffusion, dtype=float),
        np.asarray(forcing, dtype=float),
    )


def _gaussian_affine_generator(
    *,
    coupling: float,
    kappa_a: float,
    kappa_b: float,
    drive: float,
    charger_squeezing: float,
    reservoir_squeezing: float,
    omega_s: float,
    charger_phase: float,
    reservoir_phase: float,
) -> NDArray[np.complex128]:
    state_size = 14

    def derivative(state: NDArray[np.complex128]) -> NDArray[np.complex128]:
        (
            alpha,
            alpha_bar,
            beta,
            beta_bar,
            occupation_a,
            anomalous_ab,
            anomalous_ab_bar,
            coherence_ab,
            coherence_ab_bar,
            anomalous_a,
            anomalous_a_bar,
            anomalous_b,
            anomalous_b_bar,
            occupation_b,
        ) = state
        gamma = 2.0 * coupling
        decay_a = gamma + kappa_a
        decay_b = gamma + kappa_b
        mean_decay = (decay_a + decay_b) / 2.0
        sinh_a = np.sinh(charger_squeezing)
        cosh_a = np.cosh(charger_squeezing)
        sinh_c = np.sinh(reservoir_squeezing)
        cosh_c = np.cosh(reservoir_squeezing)
        phase_a_minus = np.exp(-1.0j * charger_phase)
        phase_a_plus = np.conj(phase_a_minus)
        phase_c_plus = np.exp(1.0j * reservoir_phase)
        drive_term = -1.0j * drive * (
            cosh_a - phase_a_minus * sinh_a
        )

        noise_occupation_a = gamma * (
            2.0
            * np.cos(charger_phase + reservoir_phase)
            * sinh_a
            * cosh_a
            * sinh_c
            * cosh_c
            + sinh_a**2 * cosh_c**2
            + cosh_a**2 * sinh_c**2
        )
        noise_anomalous_ab = (
            coupling * phase_a_minus * sinh_a
            + 0.5
            * gamma
            * phase_a_minus
            * sinh_a
            * np.cosh(2.0 * reservoir_squeezing)
            + 0.5
            * gamma
            * phase_c_plus
            * cosh_a
            * np.sinh(2.0 * reservoir_squeezing)
        )
        noise_coherence_ab = gamma * (
            np.exp(1.0j * (charger_phase + reservoir_phase))
            * sinh_a
            * sinh_c
            * cosh_c
            + cosh_a * sinh_c**2
        )
        noise_anomalous_a = gamma * (
            np.exp(-1.0j * (2.0 * charger_phase + reservoir_phase))
            * sinh_a**2
            * sinh_c
            * cosh_c
            + phase_c_plus * cosh_a**2 * sinh_c * cosh_c
            + phase_a_minus
            * sinh_a
            * cosh_a
            * np.cosh(2.0 * reservoir_squeezing)
        )
        noise_anomalous_b = gamma * phase_c_plus * sinh_c * cosh_c
        noise_occupation_b = gamma * sinh_c**2

        result = np.zeros(state_size, dtype=complex)
        result[0] = -(decay_a + 1.0j * omega_s) * alpha / 2.0 + drive_term
        result[1] = -(decay_a - 1.0j * omega_s) * alpha_bar / 2.0 + np.conj(drive_term)
        result[2] = (
            -decay_b * beta / 2.0
            + 2.0 * coupling * phase_a_minus * sinh_a * alpha_bar
            - 2.0 * coupling * cosh_a * alpha
        )
        result[3] = (
            -decay_b * beta_bar / 2.0
            + 2.0 * coupling * phase_a_plus * sinh_a * alpha
            - 2.0 * coupling * cosh_a * alpha_bar
        )
        result[4] = (
            -decay_a * occupation_a
            + np.conj(drive_term) * alpha
            + drive_term * alpha_bar
            + noise_occupation_a
        )
        result[5] = (
            -(mean_decay + 1.0j * omega_s) * anomalous_ab
            + 2.0 * coupling * phase_a_minus * sinh_a * occupation_a
            - 2.0 * coupling * cosh_a * anomalous_a
            + drive_term * beta
            + noise_anomalous_ab
        )
        result[6] = (
            -(mean_decay - 1.0j * omega_s) * anomalous_ab_bar
            + 2.0 * coupling * phase_a_plus * sinh_a * occupation_a
            - 2.0 * coupling * cosh_a * anomalous_a_bar
            + np.conj(drive_term) * beta_bar
            + np.conj(noise_anomalous_ab)
        )
        result[7] = (
            -(mean_decay - 1.0j * omega_s) * coherence_ab
            + 2.0 * coupling * phase_a_minus * sinh_a * anomalous_a_bar
            - 2.0 * coupling * cosh_a * occupation_a
            + np.conj(drive_term) * beta
            + noise_coherence_ab
        )
        result[8] = (
            -(mean_decay + 1.0j * omega_s) * coherence_ab_bar
            + 2.0 * coupling * phase_a_plus * sinh_a * anomalous_a
            - 2.0 * coupling * cosh_a * occupation_a
            + drive_term * beta_bar
            + np.conj(noise_coherence_ab)
        )
        result[9] = (
            -(decay_a + 2.0j * omega_s) * anomalous_a
            + 2.0 * drive_term * alpha
            + noise_anomalous_a
        )
        result[10] = (
            -(decay_a - 2.0j * omega_s) * anomalous_a_bar
            + 2.0 * np.conj(drive_term) * alpha_bar
            + np.conj(noise_anomalous_a)
        )
        result[11] = (
            -decay_b * anomalous_b
            + 4.0 * coupling * phase_a_minus * sinh_a * coherence_ab
            - 4.0 * coupling * cosh_a * anomalous_ab
            + noise_anomalous_b
        )
        result[12] = (
            -decay_b * anomalous_b_bar
            + 4.0 * coupling * phase_a_plus * sinh_a * coherence_ab_bar
            - 4.0 * coupling * cosh_a * anomalous_ab_bar
            + np.conj(noise_anomalous_b)
        )
        result[13] = (
            -decay_b * occupation_b
            + 2.0
            * coupling
            * sinh_a
            * (
                phase_a_plus * anomalous_ab
                + phase_a_minus * anomalous_ab_bar
            )
            - 2.0 * coupling * cosh_a * (coherence_ab + coherence_ab_bar)
            + noise_occupation_b
        )
        return result

    zero = np.zeros(state_size, dtype=complex)
    constant = derivative(zero)
    linear = np.empty((state_size, state_size), dtype=complex)
    for column in range(state_size):
        basis = np.zeros(state_size, dtype=complex)
        basis[column] = 1.0
        linear[:, column] = derivative(basis) - constant

    augmented = np.zeros((state_size + 1, state_size + 1), dtype=complex)
    augmented[:state_size, :state_size] = linear
    augmented[:state_size, -1] = constant
    return augmented
