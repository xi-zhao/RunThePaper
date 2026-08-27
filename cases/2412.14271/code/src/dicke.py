"""Formula-driven solvers for the dissipative two-photon Dicke model.

No paper image, author array, or author program is accepted as an input.  The
module implements the printed Hamiltonian, Lindblad jumps, mean-field/cumulant
equations, stability matrices, and an independent quantum-trajectory route.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import optimize, sparse
from scipy.sparse import linalg as sparse_linalg


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def critical_coupling(omega_c: float = 1.0, kappa1: float = 0.4) -> float:
    return float(np.sqrt(kappa1**2 + 4 * omega_c**2) / 4)


def one_photon_branches(
    lambdas: ArrayLike,
    *,
    omega_c: float = 1.0,
    omega_a: float = 2.0,
    kappa1: float = 0.4,
) -> dict[str, FloatArray | float]:
    coupling = np.asarray(lambdas, dtype=float)
    threshold = critical_coupling(omega_c, kappa1)
    exists = coupling > threshold
    jx = np.full_like(coupling, np.nan)
    jy = np.full_like(coupling, np.nan)
    jz = np.full_like(coupling, np.nan)
    photons = np.full_like(coupling, np.nan)
    x_moment = np.full_like(coupling, np.nan)
    y_moment_imag = np.full_like(coupling, np.nan)
    jx[exists] = threshold / coupling[exists]
    jy[exists] = 0
    jz[exists] = -np.sqrt(1 - (threshold / coupling[exists]) ** 2)
    photons[exists] = -(omega_a / omega_c) * jx[exists] ** 2 / jz[exists]
    x_moment[exists] = (omega_a / coupling[exists]) * jx[exists] / jz[exists]
    # Y is purely imaginary; store Im(Y), since the physical plot uses real spin
    # and photon number only.
    y_moment_imag[exists] = kappa1 * x_moment[exists] / (2 * omega_c)
    return {
        "lambda": coupling,
        "lambda_c": threshold,
        "normal_photons": np.zeros_like(coupling),
        "normal_jx": np.zeros_like(coupling),
        "normal_jz": -np.ones_like(coupling),
        "super_photons": photons,
        "super_jx_positive": jx,
        "super_jx_negative": -jx,
        "super_jy": jy,
        "super_jz": jz,
        "super_X": x_moment,
        "super_ImY": y_moment_imag,
    }


def one_photon_jacobian(
    coupling: float,
    state: Sequence[complex],
    *,
    omega_c: float = 1.0,
    omega_a: float = 2.0,
    kappa1: float = 0.4,
) -> ComplexArray:
    """Printed 6x6 Bogoliubov matrix in (X,Y,n,Jx,Jy,Jz)."""
    x_moment, y_moment, photons, jx, jy, jz = state
    return np.array(
        [
            [-kappa1, -2j * omega_c, 0, 0, 0, 0],
            [-2j * omega_c, -kappa1, -8j * coupling * jx, -8j * coupling * photons, 0, 0],
            [0, 2j * coupling * jx, -kappa1, 2j * coupling * y_moment, 0, 0],
            [0, 0, 0, 0, -2 * omega_a, 0],
            [-2 * coupling * jz, 0, 0, 2 * omega_a, 0, -2 * coupling * x_moment],
            [2 * coupling * jy, 0, 0, 0, 2 * coupling * x_moment, 0],
        ],
        dtype=np.complex128,
    )


def one_photon_stability_scan(
    lambdas: ArrayLike,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
) -> dict[str, ComplexArray | FloatArray]:
    coupling = np.asarray(lambdas, dtype=float)
    branches = one_photon_branches(
        coupling, omega_c=omega_c, omega_a=omega_a, kappa1=kappa1
    )
    normal = np.empty((coupling.size, 6), dtype=np.complex128)
    superradiant = np.full((coupling.size, 6), np.nan + 1j * np.nan, dtype=np.complex128)
    for index, value in enumerate(coupling):
        normal[index] = np.linalg.eigvals(
            one_photon_jacobian(
                value,
                [0, 0, 0, 0, 0, -1],
                omega_c=omega_c,
                omega_a=omega_a,
                kappa1=kappa1,
            )
        )
        if np.isfinite(branches["super_photons"][index]):
            x_moment = branches["super_X"][index]
            y_moment = 1j * branches["super_ImY"][index]
            state = [
                x_moment,
                y_moment,
                branches["super_photons"][index],
                branches["super_jx_positive"][index],
                0,
                branches["super_jz"][index],
            ]
            superradiant[index] = np.linalg.eigvals(
                one_photon_jacobian(
                    value,
                    state,
                    omega_c=omega_c,
                    omega_a=omega_a,
                    kappa1=kappa1,
                )
            )
    return {"lambda": coupling, "normal": normal, "superradiant": superradiant}


def cumulant_rhs_complex(
    variables: ArrayLike,
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
    kappa2: float = 0.2,
) -> ComplexArray:
    """Printed second-order cumulant EOM with conjugates independent.

    Ordering is (a, adag, a2, adag2, n, Jx, Jy, Jz).  Treating conjugates as
    independent is exactly the Bogoliubov linearization convention used in the
    supplement.
    """
    a, adag, a2, adag2, photons, jx, jy, jz = np.asarray(variables, dtype=np.complex128)
    return np.array(
        [
            -(kappa1 / 2 + 1j * omega_c) * a
            - 2j * coupling * jx * adag
            - kappa2 * (2 * photons * a + a2 * adag - 2 * a**2 * adag),
            -(kappa1 / 2 - 1j * omega_c) * adag
            + 2j * coupling * jx * a
            - kappa2 * (2 * photons * adag + adag2 * a - 2 * adag**2 * a),
            -(kappa1 + 2j * omega_c) * a2
            - 4j * coupling * jx * photons
            - 2 * kappa2 * (3 * photons * a2 - 2 * adag * a**3),
            -(kappa1 - 2j * omega_c) * adag2
            + 4j * coupling * jx * photons
            - 2 * kappa2 * (3 * photons * adag2 - 2 * a * adag**3),
            2j * coupling * jx * (a2 - adag2)
            - kappa1 * photons
            - kappa2 * (4 * photons**2 - 4 * adag**2 * a**2 + 2 * adag2 * a2),
            -2 * omega_a * jy,
            2 * omega_a * jx - 2 * coupling * jz * (a2 + adag2),
            2 * coupling * jy * (a2 + adag2),
        ],
        dtype=np.complex128,
    )


def cumulant_rhs_real(
    variables: ArrayLike,
    coupling: float,
    **parameters: float,
) -> FloatArray:
    """Printed cumulant EOM restricted to the physical real-variable space.

    The coordinates are ``(Re(a), Im(a), Re(a2), Im(a2), n, Jx, Jy, Jz)``.
    This representation enforces the photon conjugacy relations and the
    reality of the number and spin moments before linearization.
    """
    x, y, u, v, photons, jx, jy, jz = np.asarray(variables, dtype=float)
    state = np.array(
        [
            complex(x, y),
            complex(x, -y),
            complex(u, v),
            complex(u, -v),
            photons,
            jx,
            jy,
            jz,
        ],
        dtype=np.complex128,
    )
    result = cumulant_rhs_complex(state, coupling, **parameters)
    return np.array(
        [
            result[0].real,
            result[0].imag,
            result[2].real,
            result[2].imag,
            result[4].real,
            result[5].real,
            result[6].real,
            result[7].real,
        ],
        dtype=float,
    )


def physical_cumulant_state(reduced: ArrayLike) -> ComplexArray:
    """Map (Re a, Im a, Re a2, Im a2, n, theta) to the 8-variable state."""
    x, y, u, v, photons, theta = np.asarray(reduced, dtype=float)
    a = complex(x, y)
    a2 = complex(u, v)
    return np.array(
        [a, a.conjugate(), a2, a2.conjugate(), photons, np.sin(theta), 0, -np.cos(theta)],
        dtype=np.complex128,
    )


def cumulant_reduced_residual(
    reduced: ArrayLike,
    coupling: float,
    **parameters: float,
) -> FloatArray:
    result = cumulant_rhs_complex(physical_cumulant_state(reduced), coupling, **parameters)
    return np.array(
        [result[0].real, result[0].imag, result[2].real, result[2].imag, result[4].real, result[6].real]
    )


def cumulant_jacobian(
    state: ArrayLike,
    coupling: float,
    *,
    step: float = 1e-6,
    **parameters: float,
) -> ComplexArray:
    point = np.asarray(state, dtype=np.complex128)
    basis = np.eye(8, dtype=np.complex128)
    columns = [
        (
            cumulant_rhs_complex(point + step * basis[index], coupling, **parameters)
            - cumulant_rhs_complex(point - step * basis[index], coupling, **parameters)
        )
        / (2 * step)
        for index in range(8)
    ]
    return np.column_stack(columns)


def cumulant_real_jacobian(
    state: ArrayLike,
    coupling: float,
    *,
    step: float = 1e-6,
    **parameters: float,
) -> FloatArray:
    """Finite-difference Jacobian on the physical eight-real-variable space."""
    point = np.asarray(state, dtype=float)
    basis = np.eye(8, dtype=float)
    columns = [
        (
            cumulant_rhs_real(point + step * basis[index], coupling, **parameters)
            - cumulant_rhs_real(point - step * basis[index], coupling, **parameters)
        )
        / (2 * step)
        for index in range(8)
    ]
    return np.column_stack(columns)


def stability_max_real(state: ArrayLike, coupling: float, **parameters: float) -> tuple[float, ComplexArray]:
    eigenvalues = np.linalg.eigvals(cumulant_jacobian(state, coupling, **parameters))
    # Spin length is conserved, so the unconstrained 8-variable Jacobian has a
    # neutral mode.  Finite-difference/root tolerances move that mode by about
    # 1e-6; it must not be misclassified as a physical instability.
    nonzero = eigenvalues[np.abs(eigenvalues) > 1e-5]
    return float(np.max(nonzero.real, initial=-np.inf)), eigenvalues


def _deduplicate_reduced(solutions: list[FloatArray], candidate: FloatArray, tolerance: float = 1e-5) -> None:
    # Distinct branches in this model have distinct photon numbers. Numerical
    # root solving can leave tiny O(1e-3) first moments on an exact a=0 branch;
    # photon-number deduplication prevents reporting those as new physics.
    if not any(abs(existing[4] - candidate[4]) < max(tolerance, 1e-4) for existing in solutions):
        solutions.append(candidate)


def find_cumulant_solutions(
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
    kappa2: float = 0.2,
    extra_seeds: Iterable[ArrayLike] = (),
) -> list[dict[str, object]]:
    """Find physical fixed points without source-data seeding."""
    parameters = dict(omega_c=omega_c, omega_a=omega_a, kappa1=kappa1, kappa2=kappa2)
    seeds: list[ArrayLike] = list(extra_seeds)
    for photons in (0.05, 0.2, 0.6, 1.2, 2.5, 5.0, 9.0, 13.0):
        amplitude = np.sqrt(photons)
        for phase in (np.pi / 12, np.pi / 4, 5 * np.pi / 12, 3 * np.pi / 4):
            a = amplitude * np.exp(1j * phase)
            seeds.append([a.real, a.imag, (a**2).real, (a**2).imag, photons, 1.0])
    # Zero-first-moment seeds are required for the squeezed branches.
    for photons in (0.1, 0.4, 1.0, 2.0, 4.0, 8.0):
        seeds.extend(
            ([0, 0, photons / 2, photons, photons, 0.7], [0, 0, -photons / 2, -photons, photons, -0.7])
        )

    solutions: list[FloatArray] = []
    for raw_seed in seeds:
        seed = np.asarray(raw_seed, dtype=float)
        seed[4] = max(seed[4], 0)
        result = optimize.least_squares(
            cumulant_reduced_residual,
            seed,
            args=(coupling,),
            kwargs=parameters,
            bounds=(
                np.array([-20, -20, -40, -40, 0, -np.pi]),
                np.array([20, 20, 40, 40, 40, np.pi]),
            ),
            xtol=1e-11,
            ftol=1e-11,
            gtol=1e-11,
            max_nfev=2500,
        )
        if np.linalg.norm(result.fun) > 1e-7:
            continue
        candidate = result.x
        if candidate[4] < 1e-6:
            continue
        a_abs2 = candidate[0] ** 2 + candidate[1] ** 2
        a2_abs2 = candidate[2] ** 2 + candidate[3] ** 2
        # Basic bosonic covariance positivity checks.
        if candidate[4] + 1e-5 < a_abs2:
            continue
        if candidate[4] * (candidate[4] + 1) + 1e-5 < a2_abs2:
            continue
        _deduplicate_reduced(solutions, candidate)

    records: list[dict[str, object]] = []
    for reduced in sorted(solutions, key=lambda item: item[4]):
        state = physical_cumulant_state(reduced)
        max_real, eigenvalues = stability_max_real(state, coupling, **parameters)
        records.append(
            {
                "reduced": reduced,
                "state": state,
                "photons": float(reduced[4]),
                "alpha_abs": float(abs(state[0])),
                "a2_abs": float(abs(state[2])),
                "residual": float(np.linalg.norm(cumulant_reduced_residual(reduced, coupling, **parameters))),
                "max_real_eigenvalue": max_real,
                "eigenvalues": eigenvalues,
                "stable": bool(max_real <= 1e-7),
            }
        )
    return records


def cumulant_branch_scan(
    lambdas: ArrayLike,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
    kappa2: float = 0.2,
) -> dict[str, FloatArray | ComplexArray]:
    coupling = np.asarray(lambdas, dtype=float)
    coherent_high = np.full_like(coupling, np.nan)
    coherent_low = np.full_like(coupling, np.nan)
    squeezed_high = np.full_like(coupling, np.nan)
    squeezed_low = np.full_like(coupling, np.nan)
    coherent_high_stability = np.full_like(coupling, np.nan)
    coherent_low_stability = np.full_like(coupling, np.nan)
    squeezed_high_stability = np.full_like(coupling, np.nan)
    squeezed_low_stability = np.full_like(coupling, np.nan)
    previous: list[FloatArray] = []

    for index, value in enumerate(coupling):
        solutions = find_cumulant_solutions(
            float(value),
            omega_c=omega_c,
            omega_a=omega_a,
            kappa1=kappa1,
            kappa2=kappa2,
            extra_seeds=previous,
        )
        previous = [np.asarray(record["reduced"], dtype=float) for record in solutions]
        coherent = [record for record in solutions if record["alpha_abs"] > 1e-2]
        squeezed = [record for record in solutions if record["alpha_abs"] <= 1e-2]
        if coherent:
            coherent.sort(key=lambda record: record["photons"])
            coherent_low[index] = float(coherent[0]["photons"])
            coherent_low_stability[index] = float(coherent[0]["max_real_eigenvalue"])
            coherent_high[index] = float(coherent[-1]["photons"])
            coherent_high_stability[index] = float(coherent[-1]["max_real_eigenvalue"])
        if squeezed:
            squeezed.sort(key=lambda record: record["photons"])
            squeezed_low[index] = float(squeezed[0]["photons"])
            squeezed_low_stability[index] = float(squeezed[0]["max_real_eigenvalue"])
            squeezed_high[index] = float(squeezed[-1]["photons"])
            squeezed_high_stability[index] = float(squeezed[-1]["max_real_eigenvalue"])
    return {
        "lambda": coupling,
        "normal": np.zeros_like(coupling),
        "coherent_high": coherent_high,
        "coherent_low": coherent_low,
        "squeezed_high": squeezed_high,
        "squeezed_low": squeezed_low,
        "coherent_high_max_real": coherent_high_stability,
        "coherent_low_max_real": coherent_low_stability,
        "squeezed_high_max_real": squeezed_high_stability,
        "squeezed_low_max_real": squeezed_low_stability,
    }


@dataclass(frozen=True)
class QuantumModel:
    hamiltonian: object
    collapse_operators: tuple[object, ...]
    photon_annihilation: object
    photon_number: object
    spin_z: object


def operators(
    system_size: int,
    photon_cutoff: int,
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
    kappa2: float = 0.2,
) -> QuantumModel:
    import qutip as qt

    photon = qt.tensor(qt.destroy(photon_cutoff), qt.qeye(system_size + 1))
    photon_identity = qt.qeye(photon_cutoff)
    jx = qt.tensor(photon_identity, 2 * qt.jmat(system_size / 2, "x"))
    jz = qt.tensor(photon_identity, 2 * qt.jmat(system_size / 2, "z"))
    number = photon.dag() * photon
    hamiltonian = (
        omega_c * number
        + omega_a * jz / 2
        + coupling * jx * (photon.dag() ** 2 + photon**2) / system_size
    )
    collapse: list[object] = []
    if kappa1 > 0:
        collapse.append(np.sqrt(kappa1) * photon)
    if kappa2 > 0:
        collapse.append(np.sqrt(kappa2 / system_size) * photon**2)
    return QuantumModel(hamiltonian, tuple(collapse), photon, number, jz)


def _random_initial_ket(system_size: int, photon_cutoff: int, seed: int):
    import qutip as qt

    # A dense Haar-random ket is an unbiased pure-state sample whose ensemble
    # average is the infinite-temperature density matrix described in the SM.
    return qt.rand_ket([photon_cutoff, system_size + 1], seed=seed)


def trajectory_density(
    system_size: int,
    photon_cutoff: int,
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.4,
    kappa2: float = 0.2,
    final_time: float = 45.0,
    trajectories: int = 30,
    seed: int = 1701,
    initial_fock: int | None = None,
) -> dict[str, object]:
    """Independent Monte-Carlo unraveling with reproducible run-level seeds."""
    import qutip as qt

    model = operators(
        system_size,
        photon_cutoff,
        coupling,
        omega_c=omega_c,
        omega_a=omega_a,
        kappa1=kappa1,
        kappa2=kappa2,
    )
    if initial_fock is None:
        initial = _random_initial_ket(system_size, photon_cutoff, seed)
    else:
        if not 0 <= initial_fock < photon_cutoff:
            raise ValueError("initial_fock must lie inside the photon cutoff")
        initial = qt.tensor(qt.fock(photon_cutoff, initial_fock), qt.basis(system_size + 1, system_size))
    result = qt.mcsolve(
        model.hamiltonian,
        initial,
        [0.0, final_time],
        list(model.collapse_operators),
        ntraj=trajectories,
        seeds=seed + 1009,
        options={
            "store_final_state": True,
            "keep_runs_results": True,
            "progress_bar": "",
            "method": "vern9",
            "nsteps": 20000,
            "atol": 1e-7,
            "rtol": 1e-6,
            "norm_steps": 100,
            "norm_tol": 5e-2,
            "norm_t_tol": 1e-4,
        },
    )
    photon_states = [state.ptrace(0) for state in result.runs_final_states]
    spin_z_runs = np.asarray(
        [float(np.real(qt.expect(model.spin_z, state))) / system_size for state in result.runs_final_states]
    )
    cumulative: dict[int, object] = {}
    cumulative_spin_z: dict[int, float] = {}
    for count in sorted(
        set([min(4, trajectories), min(10, trajectories), min(trajectories, 30), trajectories])
    ):
        cumulative[count] = sum(photon_states[:count]) / count
        cumulative_spin_z[count] = float(np.mean(spin_z_runs[:count]))
    rho_photon = cumulative[trajectories]
    distribution = np.real(np.diag(rho_photon.full()))
    distribution = np.maximum(distribution, 0)
    distribution /= distribution.sum()
    photons = np.arange(photon_cutoff, dtype=float)
    return {
        "rho_photon": rho_photon,
        "fock_distribution": distribution,
        "photon_mean": float(distribution @ photons),
        "photon_tail": float(distribution[max(0, photon_cutoff - 5) :].sum()),
        "spin_z_mean": float(np.mean(spin_z_runs)),
        "spin_z_runs": spin_z_runs,
        "trace_error": float(abs(rho_photon.tr() - 1)),
        "cumulative_rho_photon": cumulative,
        "cumulative_spin_z": cumulative_spin_z,
        "trajectory_count": trajectories,
        "final_time": final_time,
        "seed": seed,
    }


def wigner_distribution(rho_photon: object, coordinates: ArrayLike) -> FloatArray:
    import qutip as qt

    axis = np.asarray(coordinates, dtype=float)
    return np.asarray(qt.wigner(rho_photon, axis, axis, method="clenshaw"), dtype=float)


def liouvillian_near_zero_eigenvalues(
    system_size: int,
    photon_cutoff: int,
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 1.0,
    kappa1: float = 0.0,
    kappa2: float = 0.05,
    count: int = 8,
) -> ComplexArray:
    import qutip as qt

    model = operators(
        system_size,
        photon_cutoff,
        coupling,
        omega_c=omega_c,
        omega_a=omega_a,
        kappa1=kappa1,
        kappa2=kappa2,
    )
    liouvillian = qt.liouvillian(model.hamiltonian, list(model.collapse_operators))
    matrix = liouvillian.data.as_scipy().tocsr()
    # The target is specifically the kernel and its nearest decay modes.
    # Shift-invert around a tiny nonzero shift avoids the singular factor at
    # exactly zero and is orders of magnitude faster than searching the full
    # complex plane for the largest real parts.
    eigenvalues = sparse_linalg.eigs(
        matrix,
        k=count,
        sigma=1e-8,
        which="LM",
        return_eigenvectors=False,
    )
    order = np.argsort(np.abs(eigenvalues))
    return np.asarray(eigenvalues[order], dtype=np.complex128)


def parity_leakage(distribution: ArrayLike, parity: int) -> float:
    probability = np.asarray(distribution, dtype=float)
    indices = np.arange(probability.size)
    return float(probability[indices % 2 != parity].sum())


def one_photon_steady_state_ed(
    system_size: int,
    photon_cutoff: int,
    coupling: float,
    *,
    omega_c: float = 1.0,
    omega_a: float = 2.0,
    kappa1: float = 0.4,
) -> dict[str, object]:
    """Solve the printed one-photon Lindblad model by sparse exact diagonalization.

    This implementation deliberately does not depend on QuTiP, paper arrays,
    author code, or figure pixels.  It constructs the Hamiltonian and
    Liouvillian directly from the printed operators, replaces one Liouvillian
    row with the trace constraint, and solves the resulting sparse linear
    system.  The method is general at the paper cutoffs, while its memory cost
    remains explicit through the returned Liouvillian dimension and sparsity.
    """
    if system_size < 1:
        raise ValueError("system_size must be positive")
    if photon_cutoff < 3:
        raise ValueError("photon_cutoff must be at least 3")
    if kappa1 <= 0:
        raise ValueError("one-photon steady state requires kappa1 > 0")

    spin_dimension = system_size + 1
    photon = sparse.diags(
        np.sqrt(np.arange(1, photon_cutoff, dtype=float)),
        offsets=1,
        shape=(photon_cutoff, photon_cutoff),
        format="csr",
        dtype=np.complex128,
    )
    photon_identity = sparse.identity(photon_cutoff, format="csr", dtype=np.complex128)
    spin_identity = sparse.identity(spin_dimension, format="csr", dtype=np.complex128)
    spin_z_values = np.arange(system_size, -system_size - 1, -2, dtype=float)
    spin_z = sparse.diags(spin_z_values, format="csr", dtype=np.complex128)
    upper = np.sqrt(
        np.arange(1, spin_dimension, dtype=float)
        * np.arange(system_size, 0, -1, dtype=float)
    )
    spin_x = sparse.diags([upper, upper], offsets=[-1, 1], shape=(spin_dimension, spin_dimension), format="csr")

    photon_full = sparse.kron(photon, spin_identity, format="csr")
    number_full = photon_full.getH() @ photon_full
    spin_z_full = sparse.kron(photon_identity, spin_z, format="csr")
    spin_x_full = sparse.kron(photon_identity, spin_x, format="csr")
    pair_field = photon_full.getH() @ photon_full.getH() + photon_full @ photon_full
    hamiltonian = (
        float(omega_c) * number_full
        + 0.5 * float(omega_a) * spin_z_full
        + float(coupling) * (spin_x_full @ pair_field) / float(system_size)
    ).tocsr()
    collapse = np.sqrt(float(kappa1)) * photon_full
    liouvillian = _lindblad_liouvillian(hamiltonian, (collapse,))
    hilbert_dimension = hamiltonian.shape[0]
    trace_row = np.zeros(hilbert_dimension * hilbert_dimension, dtype=np.complex128)
    trace_row[np.arange(hilbert_dimension) * (hilbert_dimension + 1)] = 1.0
    constrained = liouvillian.tolil(copy=True)
    constrained[0, :] = trace_row
    rhs = np.zeros(hilbert_dimension * hilbert_dimension, dtype=np.complex128)
    rhs[0] = 1.0
    density_vector = sparse_linalg.spsolve(constrained.tocsc(), rhs)
    density = np.asarray(density_vector, dtype=np.complex128).reshape(
        (hilbert_dimension, hilbert_dimension), order="F"
    )
    density = 0.5 * (density + density.conj().T)
    density /= np.trace(density)

    physical_vector = density.reshape(-1, order="F")
    residual = float(np.linalg.norm(liouvillian @ physical_vector))
    trace_error = float(abs(np.trace(density) - 1.0))
    hermiticity_error = float(np.linalg.norm(density - density.conj().T))
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(density)).real)
    tensor_density = density.reshape(
        photon_cutoff,
        spin_dimension,
        photon_cutoff,
        spin_dimension,
    )
    photon_density = np.einsum("psqs->pq", tensor_density)
    distribution = np.real(np.diag(photon_density))
    distribution = np.maximum(distribution, 0.0)
    distribution /= distribution.sum()
    occupations = np.arange(photon_cutoff, dtype=float)
    photon_mean = float(distribution @ occupations)
    spin_z_mean = float(np.real(np.trace(density @ spin_z_full.toarray())) / system_size)
    tail_start = max(0, photon_cutoff - 5)
    return {
        "system_size": int(system_size),
        "photon_cutoff": int(photon_cutoff),
        "coupling": float(coupling),
        "photon_mean": photon_mean,
        "spin_z_mean": spin_z_mean,
        "fock_distribution": distribution,
        "photon_tail": float(distribution[tail_start:].sum()),
        "trace_error": trace_error,
        "hermiticity_error": hermiticity_error,
        "minimum_density_eigenvalue": minimum_eigenvalue,
        "liouvillian_residual": residual,
        "hilbert_dimension": int(hilbert_dimension),
        "liouvillian_dimension": int(liouvillian.shape[0]),
        "liouvillian_nnz": int(liouvillian.nnz),
    }


def _lindblad_liouvillian(
    hamiltonian: sparse.spmatrix,
    collapse_operators: Sequence[sparse.spmatrix],
) -> sparse.csr_matrix:
    dimension = int(hamiltonian.shape[0])
    identity = sparse.identity(dimension, format="csr", dtype=np.complex128)
    result = -1j * (
        sparse.kron(identity, hamiltonian, format="csr")
        - sparse.kron(hamiltonian.transpose(), identity, format="csr")
    )
    for collapse in collapse_operators:
        rate = (collapse.getH() @ collapse).tocsr()
        result = result + sparse.kron(collapse.conjugate(), collapse, format="csr")
        result = result - 0.5 * sparse.kron(identity, rate, format="csr")
        result = result - 0.5 * sparse.kron(rate.transpose(), identity, format="csr")
    return result.tocsr()
