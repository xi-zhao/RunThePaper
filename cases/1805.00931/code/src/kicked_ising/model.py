"""Formula-derived kicked-Ising and dual-transfer calculations.

This module has no path, image, PDF, or source-archive inputs.  It implements only
the equations declared in EQUATION_CARDS.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import ArpackNoConvergence, LinearOperator, eigs


SELF_DUAL = np.pi / 4.0


@lru_cache(maxsize=None)
def computational_spins(length: int) -> np.ndarray:
    """Return all z-basis configurations, with bit 0 -> +1 and bit 1 -> -1."""

    if length < 1:
        raise ValueError("length must be positive")
    states = np.arange(1 << length, dtype=np.uint64)[:, None]
    bits = (states >> np.arange(length, dtype=np.uint64)) & 1
    return (1 - 2 * bits.astype(np.int8)).astype(np.float64)


@lru_cache(maxsize=None)
def tensor_kick(length: int, b: float = SELF_DUAL) -> np.ndarray:
    """Dense product kick exp(-i b sum_j sigma_x_j)."""

    local = np.array(
        [
            [np.cos(b), -1j * np.sin(b)],
            [-1j * np.sin(b), np.cos(b)],
        ],
        dtype=np.complex128,
    )
    result = local
    for _ in range(length - 1):
        result = np.kron(result, local)
    return result


def floquet_phases(
    length: int,
    fields: np.ndarray | Iterable[float],
    *,
    j_coupling: float = SELF_DUAL,
) -> np.ndarray:
    """Diagonal exp(-i H_I) entries for periodic boundary conditions."""

    field_array = np.asarray(fields, dtype=np.float64)
    if field_array.shape != (length,):
        raise ValueError(f"fields must have shape ({length},)")
    spins = computational_spins(length)
    nearest = np.sum(spins * np.roll(spins, -1, axis=1), axis=1)
    energy = j_coupling * nearest + spins @ field_array
    return np.exp(-1j * energy)


def floquet_matrix(
    length: int,
    fields: np.ndarray | Iterable[float],
    *,
    j_coupling: float = SELF_DUAL,
    b: float = SELF_DUAL,
) -> np.ndarray:
    """Construct U_KI = exp(-i H_K) exp(-i H_I) exactly at finite length."""

    phases = floquet_phases(length, fields, j_coupling=j_coupling)
    return tensor_kick(length, b) * phases[None, :]


def spectral_form_factor(eigenvalues: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Evaluate |sum_n lambda_n**t|^2 for positive integer times."""

    values = np.asarray(eigenvalues, dtype=np.complex128)
    integer_times = np.asarray(times, dtype=np.int64)
    if np.any(integer_times < 1):
        raise ValueError("SFF times must be positive integers")
    traces = np.sum(values[:, None] ** integer_times[None, :], axis=0)
    return np.abs(traces) ** 2


def array_module(name: str) -> Any:
    """Return the requested numerical array module.

    NumPy is the always-available correctness backend.  CuPy is optional and is
    imported only for the paper-scale A100 route; keeping it optional lets the
    same scientific code and tests run on an ordinary CPU installation.
    """

    if name == "numpy":
        return np
    if name == "cupy":
        try:
            import cupy  # type: ignore[import-not-found]
        except ImportError as error:  # pragma: no cover - depends on GPU host
            raise RuntimeError(
                "backend='cupy' requires a CUDA-matched CuPy installation on the run host"
            ) from error
        return cupy
    raise ValueError(f"unsupported array backend: {name}")


def _complex_dtype(module: Any, name: str) -> Any:
    if name == "complex64":
        return module.complex64
    if name == "complex128":
        return module.complex128
    raise ValueError(f"unsupported complex dtype: {name}")


def _as_numpy(value: Any) -> np.ndarray:
    """Copy a NumPy/CuPy value to host NumPy without importing CuPy eagerly."""

    if isinstance(value, np.ndarray):
        return value
    module = type(value).__module__.split(".", maxsplit=1)[0]
    if module == "cupy":  # pragma: no cover - depends on GPU host
        return value.get()
    return np.asarray(value)


def _apply_product_kick_axis_inplace(
    array: Any,
    length: int,
    *,
    axis: int,
    b: float,
    conjugate: bool,
    chunk_size: int,
) -> None:
    """Apply the local kick along one Hilbert-space axis using bounded scratch.

    ``array`` is a two-dimensional NumPy or CuPy array.  Chunking the untouched
    axis prevents a single butterfly from allocating half of a ``4**t`` vector,
    which is the difference between a runnable t=15 transfer action and an
    otherwise hidden extra tens-of-GiB allocation.
    """

    if array.ndim != 2 or array.shape[axis] != 1 << length:
        raise ValueError("kick axis does not match the requested spin-chain length")
    cosine = float(np.cos(b))
    off_diagonal = (1j if conjugate else -1j) * float(np.sin(b))
    dimension = 1 << length
    chunk = max(1, int(chunk_size))

    for bit in range(length):
        step = 1 << bit
        if axis == 0:
            blocks = array.reshape(dimension // (2 * step), 2, step, array.shape[1])
            for start in range(0, array.shape[1], chunk):
                stop = min(start + chunk, array.shape[1])
                lower = blocks[:, 0, :, start:stop].copy()
                upper = blocks[:, 1, :, start:stop]
                blocks[:, 0, :, start:stop] = cosine * lower + off_diagonal * upper
                blocks[:, 1, :, start:stop] = off_diagonal * lower + cosine * upper
        elif axis == 1:
            blocks = array.reshape(array.shape[0], dimension // (2 * step), 2, step)
            for start in range(0, array.shape[0], chunk):
                stop = min(start + chunk, array.shape[0])
                lower = blocks[start:stop, :, 0, :].copy()
                upper = blocks[start:stop, :, 1, :]
                blocks[start:stop, :, 0, :] = cosine * lower + off_diagonal * upper
                blocks[start:stop, :, 1, :] = off_diagonal * lower + cosine * upper
        else:
            raise ValueError("axis must be 0 or 1")


def apply_floquet_states_inplace(
    states: Any,
    fields: np.ndarray | Iterable[float],
    *,
    j_coupling: float = SELF_DUAL,
    b: float = SELF_DUAL,
    backend: str = "numpy",
    dtype: str = "complex128",
    butterfly_chunk_size: int = 1024,
) -> None:
    """Apply one exact finite-chain Floquet period to one or more state vectors.

    This matrix-free ``O(L 2**L)`` action is shared by the paper-scale stochastic
    trace estimator and its small-system exact checks.  It never constructs the
    dense Floquet matrix or diagonalizes it.
    """

    module = array_module(backend)
    if states.ndim == 1:
        matrix = states.reshape(-1, 1)
    elif states.ndim == 2:
        matrix = states
    else:
        raise ValueError("states must be a vector or a column matrix")
    length = int(round(np.log2(matrix.shape[0])))
    if 1 << length != matrix.shape[0]:
        raise ValueError("state dimension must be a power of two")
    expected_dtype = _complex_dtype(module, dtype)
    if matrix.dtype != expected_dtype:
        raise ValueError(f"states must have dtype {dtype}")
    phases = module.asarray(
        floquet_phases(length, fields, j_coupling=j_coupling), dtype=expected_dtype
    )
    matrix *= phases[:, None]
    _apply_product_kick_axis_inplace(
        matrix,
        length,
        axis=0,
        b=b,
        conjugate=False,
        chunk_size=butterfly_chunk_size,
    )


def random_phase_trace_sff(
    fields: np.ndarray | Iterable[float],
    times: np.ndarray,
    *,
    seed: int,
    probe_group_size: int,
    j_coupling: float = SELF_DUAL,
    b: float = SELF_DUAL,
    backend: str = "numpy",
    dtype: str = "complex128",
    butterfly_chunk_size: int = 1024,
    norm_check_interval: int = 100,
) -> tuple[np.ndarray, dict[str, float | int | str]]:
    """Unbiased matrix-free estimator of ``|tr(U**t)|**2``.

    Two statistically independent groups estimate ``tr(U**t)``.  Their real
    cross product is unbiased for the spectral form factor, unlike squaring one
    noisy trace estimate.  Averaging over the paper's 9490 disorder realizations
    then controls both disorder and probe noise without an eigendecomposition.
    """

    integer_times = np.asarray(times, dtype=np.int64)
    if integer_times.ndim != 1 or integer_times.size == 0:
        raise ValueError("times must be a non-empty one-dimensional array")
    if np.any(integer_times < 1) or np.any(np.diff(integer_times) <= 0):
        raise ValueError("times must be strictly increasing positive integers")
    if probe_group_size < 1:
        raise ValueError("probe_group_size must be positive")

    field_array = np.asarray(fields, dtype=np.float64)
    length = field_array.size
    dimension = 1 << length
    module = array_module(backend)
    complex_type = _complex_dtype(module, dtype)
    probe_count = 2 * int(probe_group_size)
    rng = module.random.RandomState(int(seed))
    codes = rng.randint(0, 4, size=(dimension, probe_count))
    phase_lookup = module.asarray([1.0, 1.0j, -1.0, -1.0j], dtype=complex_type)
    initial = phase_lookup[codes]
    states = initial.copy()
    del codes
    initial_norms = module.sum(module.abs(states) ** 2, axis=0)
    estimates = np.empty(integer_times.size, dtype=np.float64)
    maximum_norm_drift = 0.0
    output_index = 0
    wanted = {int(value): index for index, value in enumerate(integer_times)}

    for integer_time in range(1, int(integer_times[-1]) + 1):
        apply_floquet_states_inplace(
            states,
            field_array,
            j_coupling=j_coupling,
            b=b,
            backend=backend,
            dtype=dtype,
            butterfly_chunk_size=butterfly_chunk_size,
        )
        if integer_time in wanted:
            # One batched reduction avoids launching one GPU kernel per probe.
            # The conservative preflight includes separate conjugation and
            # product temporaries even when the GPU backend fuses either step.
            traces = module.sum(module.conj(initial) * states, axis=0)
            first = module.mean(traces[:probe_group_size])
            second = module.mean(traces[probe_group_size:])
            estimates[wanted[integer_time]] = float(
                _as_numpy(module.real(first * module.conj(second)))
            )
            output_index += 1
        if integer_time % max(1, int(norm_check_interval)) == 0 or integer_time == int(
            integer_times[-1]
        ):
            current_norms = module.sum(module.abs(states) ** 2, axis=0)
            drift = module.max(module.abs(current_norms / initial_norms - 1.0))
            maximum_norm_drift = max(maximum_norm_drift, float(_as_numpy(drift)))

    if output_index != integer_times.size:
        raise RuntimeError("not every requested SFF time was evaluated")
    return estimates, {
        "estimator": "independent_random_phase_cross",
        "probe_group_size": int(probe_group_size),
        "probe_count": probe_count,
        "maximum_state_norm_drift": maximum_norm_drift,
    }


def coe_form_factor(times: np.ndarray, dimension: int) -> np.ndarray:
    """Finite-N circular-orthogonal-ensemble form factor."""

    t = np.asarray(times, dtype=np.float64)
    n = float(dimension)
    result = np.empty_like(t)
    below = t <= n
    result[below] = 2.0 * t[below] - t[below] * np.log1p(2.0 * t[below] / n)
    result[~below] = 2.0 * n - t[~below] * np.log(
        (2.0 * t[~below] + n) / (2.0 * t[~below] - n)
    )
    return result


def thermodynamic_sff(times: np.ndarray, spatial_length: int) -> np.ndarray:
    """Unit-circle contribution tr(T**L) from the paper's proved/conjectured counts."""

    output = []
    for time in np.asarray(times, dtype=np.int64):
        integer_time = int(time)
        # Use the closed-form theorem/conjecture for a long time series.  The
        # independent dihedral Gram-rank construction is intentionally reserved for
        # the finite Table-I audit (t=2..17); recomputing a 2t-by-2t Gram matrix at
        # every plot point would turn this O(t) reference curve into O(t^4) work.
        if integer_time == 1:
            plus, minus = 1, 0
        elif integer_time % 2:
            plus, minus = (2 * integer_time - 1 if integer_time <= 5 else 2 * integer_time), 0
        elif integer_time == 2:
            plus, minus = 2, 0
        elif integer_time == 4:
            plus, minus = 7, 0
        elif integer_time == 6:
            plus, minus = 13, 2
        elif integer_time == 8:
            plus, minus = 18, 0
        elif integer_time == 10:
            plus, minus = 22, 2
        else:
            plus, minus = 2 * integer_time + 1, 0
        output.append(float(plus + ((-1) ** spatial_length) * minus))
    return np.asarray(output, dtype=np.float64)


@dataclass(frozen=True)
class TransferOperator:
    """Memory-bounded matrix-free ``(U tensor U*) O_sigma`` operator."""

    time: int
    h_mean: float
    sigma: float
    j_coupling: float = SELF_DUAL
    b: float = SELF_DUAL
    backend: str = "numpy"
    dtype: str = "complex128"
    dephasing_block_rows: int = 64
    butterfly_chunk_size: int = 1024

    def __post_init__(self) -> None:
        if self.time < 2:
            raise ValueError("transfer time must be at least 2")
        if self.sigma < 0:
            raise ValueError("sigma must be non-negative")
        if self.dephasing_block_rows < 1 or self.butterfly_chunk_size < 1:
            raise ValueError("transfer block sizes must be positive")
        module = array_module(self.backend)
        complex_type = _complex_dtype(module, self.dtype)
        spins = computational_spins(self.time)
        magnetization = np.sum(spins, axis=1)
        nearest = np.sum(spins * np.roll(spins, -1, axis=1), axis=1)
        phase = np.exp(-1j * (self.j_coupling * nearest + self.h_mean * magnetization))
        object.__setattr__(self, "module", module)
        object.__setattr__(self, "complex_type", complex_type)
        object.__setattr__(self, "dimension", 1 << self.time)
        object.__setattr__(self, "phase", module.asarray(phase, dtype=complex_type))
        object.__setattr__(
            self, "magnetization", module.asarray(magnetization, dtype=module.float64)
        )

    @property
    def dephasing(self) -> np.ndarray:
        """Explicit small-system dephasing matrix used only by verification tests."""

        if self.dimension > 256:
            raise MemoryError("explicit dephasing is restricted to transfer time <= 8")
        magnetization = _as_numpy(self.magnetization)
        return np.exp(
            -0.5
            * self.sigma**2
            * (magnetization[:, None] - magnetization[None, :]) ** 2
        )

    def matvec(self, vector: Any) -> Any:
        module = self.module
        matrix = module.array(vector, dtype=self.complex_type, copy=True).reshape(
            self.dimension, self.dimension
        )

        # O_sigma depends only on magnetization differences.  Generating it a few
        # rows at a time removes the old O(4**t) real-valued side matrix.
        for start in range(0, self.dimension, self.dephasing_block_rows):
            stop = min(start + self.dephasing_block_rows, self.dimension)
            difference = (
                self.magnetization[start:stop, None] - self.magnetization[None, :]
            )
            matrix[start:stop] *= module.exp(-0.5 * self.sigma**2 * difference**2)

        # U A U^dagger, with U = K D.  Both kick axes use bounded scratch.
        matrix *= self.phase[:, None]
        _apply_product_kick_axis_inplace(
            matrix,
            self.time,
            axis=0,
            b=self.b,
            conjugate=False,
            chunk_size=self.butterfly_chunk_size,
        )
        matrix *= module.conj(self.phase)[None, :]
        _apply_product_kick_axis_inplace(
            matrix,
            self.time,
            axis=1,
            b=self.b,
            conjugate=True,
            chunk_size=self.butterfly_chunk_size,
        )
        return matrix.ravel()

    def as_linear_operator(self) -> LinearOperator:
        if self.backend != "numpy":
            raise ValueError("SciPy LinearOperator is available only for backend='numpy'")
        size = self.dimension**2
        return LinearOperator(
            (size, size),
            matvec=self.matvec,
            dtype=np.dtype(self.dtype),
        )

    def explicit_matrix(self) -> np.ndarray:
        """Build the full superoperator for small-system verification only."""

        if self.backend != "numpy" or self.time > 5:
            raise ValueError("explicit transfer matrices are restricted to NumPy t<=5")
        size = self.dimension**2
        identity = np.eye(size, dtype=np.dtype(self.dtype))
        return np.column_stack([self.matvec(identity[:, index]) for index in range(size)])


def _site_permutation_matrix(mapping: tuple[int, ...]) -> np.ndarray:
    length = len(mapping)
    dimension = 1 << length
    matrix = np.zeros((dimension, dimension), dtype=np.complex128)
    for old_index in range(dimension):
        new_index = 0
        for old_site, new_site in enumerate(mapping):
            if (old_index >> old_site) & 1:
                new_index |= 1 << new_site
        matrix[new_index, old_index] = 1.0
    return matrix


def _compose(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    """Return left after right."""

    return tuple(left[right[index]] for index in range(len(left)))


def _inverse(permutation: tuple[int, ...]) -> tuple[int, ...]:
    result = [0] * len(permutation)
    for source, target in enumerate(permutation):
        result[target] = source
    return tuple(result)


def _cycle_count(permutation: tuple[int, ...]) -> int:
    seen: set[int] = set()
    count = 0
    for start in range(len(permutation)):
        if start in seen:
            continue
        count += 1
        current = start
        while current not in seen:
            seen.add(current)
            current = permutation[current]
    return count


def _dihedral_site_permutations(time: int) -> list[tuple[int, ...]]:
    shift = tuple((index + 1) % time for index in range(time))
    reflection = tuple(time - 1 - index for index in range(time))
    identity = tuple(range(time))
    elements: list[tuple[int, ...]] = []
    power = identity
    for _ in range(time):
        elements.extend((power, _compose(reflection, power)))
        power = _compose(shift, power)
    return elements


def dihedral_gram_rank(time: int) -> int:
    """Rank of {Pi**j, R Pi**j} via permutation-cycle overlaps."""

    elements = _dihedral_site_permutations(time)
    gram = np.asarray(
        [
            [
                2.0 ** _cycle_count(_compose(_inverse(left), right))
                for right in elements
            ]
            for left in elements
        ],
        dtype=np.float64,
    )
    return int(np.linalg.matrix_rank(gram, tol=1e-8))


def transfer_multiplicities(time: int) -> tuple[int, int]:
    """Return (+1, -1) multiplicities from the proved operator inventory."""

    if time < 2:
        # The paper's Table I begins at t=2; t=1 is needed only by the TL plot.
        return 1, 0
    plus = dihedral_gram_rank(time)
    minus = 0
    if time == 6:
        plus += 1
        minus = 2
    elif time in {8, 10}:
        plus += 2
        if time == 10:
            minus = 2
    elif time >= 12 and time % 2 == 0:
        plus += 1
    return plus, minus


def _swap_sites_in_state(
    vector: np.ndarray, length: int, first: int, second: int
) -> np.ndarray:
    output = np.empty_like(vector)
    for old_index in range(1 << length):
        differing = ((old_index >> first) & 1) ^ ((old_index >> second) & 1)
        new_index = old_index ^ (differing << first) ^ (differing << second)
        output[new_index] = vector[old_index]
    return output


def _basis_state(spins: str) -> np.ndarray:
    """Create a z-basis state from a string of 'u' (+z) and 'd' (-z)."""

    index = sum((symbol == "d") << site for site, symbol in enumerate(spins))
    vector = np.zeros(1 << len(spins), dtype=np.complex128)
    vector[index] = 1.0
    return vector


def _even_singlet(time: int) -> np.ndarray:
    if time % 2:
        raise ValueError("the exceptional singlet exists only for even time")
    state = _basis_state("d" * (time // 2) + "u" * (time // 2))
    for site in range(time // 2):
        state = state - _swap_sites_in_state(state, time, site, site + time // 2)
    return state / np.linalg.norm(state)


def _translation_and_reflection(time: int) -> tuple[np.ndarray, np.ndarray]:
    shift = _site_permutation_matrix(tuple((index + 1) % time for index in range(time)))
    reflection = _site_permutation_matrix(tuple(time - 1 - index for index in range(time)))
    return shift, reflection


def _t8_triplet_projector(translation: np.ndarray) -> np.ndarray:
    time = 8
    y_zero = sum(np.linalg.matrix_power(translation, power) for power in range(time)) / time
    raw_plus = (
        _basis_state("uududddd")
        - _basis_state("uudduddd")
        + _basis_state("uudddudd")
        - _basis_state("uuddddud")
    )
    raw_zero = _basis_state("uudududd") - _basis_state("uuddudud")
    raw_minus = (
        _basis_state("dduduuuu")
        - _basis_state("dduuduuu")
        + _basis_state("dduuuduu")
        - _basis_state("dduuuudu")
    )
    triplet = [
        np.sqrt(2.0) * y_zero @ raw_plus,
        2.0 * y_zero @ raw_zero,
        np.sqrt(2.0) * y_zero @ raw_minus,
    ]
    return sum(np.outer(state, state.conj()) for state in triplet)


def _basis_index_permutation(mapping: tuple[int, ...]) -> np.ndarray:
    """Map old computational-basis indices under a site permutation."""

    length = len(mapping)
    old = np.arange(1 << length, dtype=np.uint64)
    new = np.zeros_like(old)
    for old_site, new_site in enumerate(mapping):
        new |= ((old >> np.uint64(old_site)) & np.uint64(1)) << np.uint64(new_site)
    return new.astype(np.int64)


def _total_spin_action(states: np.ndarray, axis: str, time: int) -> np.ndarray:
    """Apply ``M_axis=sum sigma_axis`` to a column matrix of states."""

    matrix = np.asarray(states, dtype=np.complex128)
    indices = np.arange(1 << time, dtype=np.int64)
    if axis == "z":
        bits = (indices[:, None] >> np.arange(time, dtype=np.int64)) & 1
        magnetization = np.sum(1 - 2 * bits, axis=1)
        return magnetization[:, None] * matrix
    output = np.zeros_like(matrix)
    for bit in range(time):
        source = indices ^ (1 << bit)
        if axis == "x":
            output += matrix[source]
        elif axis == "y":
            coefficient = np.where((indices >> bit) & 1, 1j, -1j)
            output += coefficient[:, None] * matrix[source]
        else:
            raise ValueError("spin axis must be x, y, or z")
    return output


@lru_cache(maxsize=1)
def _t10_chi() -> np.ndarray:
    """Reconstruct the exceptional t=10 singlet from its defining symmetries.

    The arXiv source's displayed seed for Eq. (175) repeats and cancels one ket.
    Rather than guessing that typographical term or importing author numerics, we
    independently solve the source-stated conditions: zero momentum, odd
    reflection, total spin zero, and Floquet eigenphase opposite to the generic
    even-time singlet.  The selected one-dimensional eigenspace is therefore
    formula-derived and independently checkable.
    """

    time = 10
    dimension = 1 << time
    shift = tuple((index + 1) % time for index in range(time))
    reflection = tuple(time - 1 - index for index in range(time))
    shift_map = _basis_index_permutation(shift)
    reflection_map = _basis_index_permutation(reflection)

    seen = np.zeros(dimension, dtype=bool)
    orbit_id = np.full(dimension, -1, dtype=np.int64)
    orbits: list[list[int]] = []
    for start in range(dimension):
        if seen[start]:
            continue
        orbit: list[int] = []
        current = start
        while not seen[current]:
            seen[current] = True
            orbit_id[current] = len(orbits)
            orbit.append(current)
            current = int(shift_map[current])
        orbits.append(orbit)

    odd_zero_momentum: list[np.ndarray] = []
    paired: set[int] = set()
    for orbit_index, orbit in enumerate(orbits):
        if orbit_index in paired:
            continue
        reflected_index = int(orbit_id[int(reflection_map[orbit[0]])])
        paired.update((orbit_index, reflected_index))
        if reflected_index == orbit_index:
            continue
        vector = np.zeros(dimension, dtype=np.complex128)
        vector[orbit] = 1.0 / np.sqrt(len(orbit))
        reflected_orbit = orbits[reflected_index]
        vector[reflected_orbit] -= 1.0 / np.sqrt(len(reflected_orbit))
        vector /= np.linalg.norm(vector)
        odd_zero_momentum.append(vector)
    symmetry_basis = np.column_stack(odd_zero_momentum)

    spin_squared = np.zeros(
        (symmetry_basis.shape[1], symmetry_basis.shape[1]), dtype=np.complex128
    )
    for axis in "xyz":
        acted = _total_spin_action(symmetry_basis, axis, time)
        spin_squared += acted.conj().T @ acted
    spin_values, spin_vectors = np.linalg.eigh(spin_squared)
    singlets = symmetry_basis @ spin_vectors[:, spin_values < 1e-8]
    if singlets.shape[1] == 0:
        raise RuntimeError("failed to construct the t=10 singlet sector")

    evolved = singlets.copy()
    apply_floquet_states_inplace(evolved, np.zeros(time, dtype=np.float64))
    reduced_floquet = singlets.conj().T @ evolved
    values, vectors = np.linalg.eig(reduced_floquet)
    generic = _even_singlet(time)
    evolved_generic = generic.copy()
    apply_floquet_states_inplace(evolved_generic, np.zeros(time, dtype=np.float64))
    generic_phase = np.vdot(generic, evolved_generic)
    selected = int(np.argmin(np.abs(values + generic_phase)))
    chi = singlets @ vectors[:, selected]
    chi /= np.linalg.norm(chi)
    evolved_chi = chi.copy()
    apply_floquet_states_inplace(evolved_chi, np.zeros(time, dtype=np.float64))
    residual = float(np.linalg.norm(evolved_chi - values[selected] * chi))
    if residual > 2e-10 or abs(np.vdot(generic, chi)) > 2e-10:
        raise RuntimeError("t=10 exceptional singlet failed its defining identities")
    return chi


@dataclass(frozen=True)
class _OperatorComponent:
    label: str
    permutation: tuple[int, ...] | None = None
    scale: complex = 1.0
    terms: tuple[tuple[complex, np.ndarray, np.ndarray], ...] = ()


def _permutation_component(label: str, permutation: tuple[int, ...]) -> _OperatorComponent:
    dimension = 1 << len(permutation)
    return _OperatorComponent(
        label=label,
        permutation=permutation,
        scale=1.0 / np.sqrt(dimension),
    )


def _low_rank_component(
    label: str, terms: list[tuple[complex, np.ndarray, np.ndarray]]
) -> _OperatorComponent:
    normalized_terms = [
        (complex(weight), np.asarray(left), np.asarray(right))
        for weight, left, right in terms
    ]
    norm_squared = 0.0j
    for left_weight, left_u, left_v in normalized_terms:
        for right_weight, right_u, right_v in normalized_terms:
            norm_squared += (
                np.conj(left_weight)
                * right_weight
                * np.vdot(left_u, right_u)
                * np.vdot(right_v, left_v)
            )
    norm = float(np.sqrt(max(float(np.real(norm_squared)), 0.0)))
    if norm <= 1e-14:
        raise ValueError(f"zero-norm protected operator component: {label}")
    return _OperatorComponent(
        label=label,
        terms=tuple((weight / norm, left, right) for weight, left, right in normalized_terms),
    )


def _component_overlap(left: _OperatorComponent, right: _OperatorComponent) -> complex:
    if left.permutation is not None and right.permutation is not None:
        relative = _compose(_inverse(left.permutation), right.permutation)
        return np.conj(left.scale) * right.scale * 2.0 ** _cycle_count(relative)
    if left.permutation is not None:
        mapping = _basis_index_permutation(left.permutation)
        value = 0.0j
        for weight, vector_u, vector_v in right.terms:
            value += weight * np.sum(vector_u[mapping] * np.conj(vector_v))
        return np.conj(left.scale) * value
    if right.permutation is not None:
        return np.conj(_component_overlap(right, left))
    value = 0.0j
    for left_weight, left_u, left_v in left.terms:
        for right_weight, right_u, right_v in right.terms:
            value += (
                np.conj(left_weight)
                * right_weight
                * np.vdot(left_u, right_u)
                * np.vdot(right_v, left_v)
            )
    return value


class ProtectedOperatorBasis:
    """Implicit protected ``+/-1`` operator span for transfer times through 15.

    Permutation operators are stored as index maps and exceptional operators as
    low-rank factors.  Projection therefore needs ``O(t 4**t)`` arithmetic but
    only ``O(4**t)`` vector storage, rather than materializing a ``4**t by O(t)``
    dense basis.
    """

    def __init__(self, time: int, components: list[_OperatorComponent]) -> None:
        self.time = int(time)
        self.dimension = 1 << self.time
        self.components = tuple(components)
        gram = np.asarray(
            [[_component_overlap(left, right) for right in components] for left in components],
            dtype=np.complex128,
        )
        gram = (gram + gram.conj().T) / 2.0
        self.gram = gram
        self.gram_pseudoinverse = np.linalg.pinv(gram, rcond=1e-11)
        self.rank = int(np.linalg.matrix_rank(gram, tol=1e-9))
        self.shape = (self.dimension**2, self.rank)
        self._backend_cache: dict[tuple[str, str], tuple[list[Any], Any]] = {}

    def _backend_data(self, backend: str, dtype: str) -> tuple[list[Any], Any]:
        cache_key = (backend, dtype)
        if cache_key in self._backend_cache:
            return self._backend_cache[cache_key]
        module = array_module(backend)
        complex_type = _complex_dtype(module, dtype)
        converted: list[Any] = []
        for component in self.components:
            if component.permutation is not None:
                converted.append(
                    (
                        "permutation",
                        module.asarray(
                            _basis_index_permutation(component.permutation), dtype=module.int64
                        ),
                        component.scale,
                    )
                )
            else:
                converted.append(
                    (
                        "low_rank",
                        tuple(
                            (
                                weight,
                                module.asarray(left, dtype=complex_type),
                                module.asarray(right, dtype=complex_type),
                            )
                            for weight, left, right in component.terms
                        ),
                    )
                )
        inverse = module.asarray(self.gram_pseudoinverse, dtype=complex_type)
        self._backend_cache[cache_key] = (converted, inverse)
        return converted, inverse

    def project(
        self,
        vector: Any,
        *,
        copy: bool = True,
        backend: str = "numpy",
        low_rank_block_rows: int = 64,
    ) -> Any:
        """Return the component orthogonal to the protected operator span."""

        module = array_module(backend)
        output = module.array(vector, copy=copy).reshape(self.dimension, self.dimension)
        dtype_name = "complex64" if output.dtype == module.complex64 else "complex128"
        components, inverse = self._backend_data(backend, dtype_name)
        overlaps = module.empty(len(components), dtype=output.dtype)
        columns = module.arange(self.dimension, dtype=module.int64)
        for index, component in enumerate(components):
            if component[0] == "permutation":
                _, mapping, scale = component
                overlaps[index] = module.conj(scale) * module.sum(output[mapping, columns])
            else:
                value = module.asarray(0.0j, dtype=output.dtype)
                for weight, left, right in component[1]:
                    value += module.conj(weight) * module.vdot(left, output @ right)
                overlaps[index] = value
        weights = inverse.astype(output.dtype, copy=False) @ overlaps

        block_rows = max(1, int(low_rank_block_rows))
        for coefficient, component in zip(weights, components, strict=True):
            if component[0] == "permutation":
                _, mapping, scale = component
                output[mapping, columns] -= coefficient * scale
            else:
                for weight, left, right in component[1]:
                    factor = coefficient * weight
                    for start in range(0, self.dimension, block_rows):
                        stop = min(start + block_rows, self.dimension)
                        output[start:stop] -= (
                            factor
                            * left[start:stop, None]
                            * module.conj(right)[None, :]
                        )
        return output.ravel()

    def explicit(self, *, max_elements: int = 8_000_000) -> np.ndarray:
        """Materialize an orthonormal basis only for small verification systems."""

        raw_elements = self.dimension**2 * len(self.components)
        if raw_elements > max_elements:
            raise MemoryError("explicit protected basis exceeds verification memory limit")
        columns: list[np.ndarray] = []
        basis_columns = np.arange(self.dimension)
        for component in self.components:
            matrix = np.zeros((self.dimension, self.dimension), dtype=np.complex128)
            if component.permutation is not None:
                mapping = _basis_index_permutation(component.permutation)
                matrix[mapping, basis_columns] = component.scale
            else:
                for weight, left, right in component.terms:
                    matrix += weight * np.outer(left, right.conj())
            columns.append(matrix.ravel())
        candidate = np.column_stack(columns)
        q_matrix, r_matrix, _ = linalg.qr(
            candidate, mode="economic", pivoting=True, check_finite=False
        )
        diagonal = np.abs(np.diag(r_matrix))
        tolerance = max(candidate.shape) * np.finfo(float).eps * diagonal.max()
        rank = int(np.sum(diagonal > tolerance))
        return q_matrix[:, :rank]


@lru_cache(maxsize=None)
def protected_operator_basis(time: int) -> ProtectedOperatorBasis:
    """Build the complete source-derived protected basis for ``2 <= t <= 15``."""

    if time < 2 or time > 15:
        raise ValueError("protected transfer basis is implemented for 2 <= t <= 15")
    dihedral = _dihedral_site_permutations(time)
    components = [
        _permutation_component(f"dihedral_{index}", permutation)
        for index, permutation in enumerate(dihedral)
    ]

    if time % 2 == 0:
        singlet = _even_singlet(time)
        components.append(_low_rank_component("generic_singlet", [(1.0, singlet, singlet)]))

        if time == 6:
            translation, reflection = _translation_and_reflection(time)
            y_zero = sum(
                np.linalg.matrix_power(translation, power_index)
                for power_index in range(time)
            ) / time
            reflection_odd_zero_momentum = (np.eye(1 << time) - reflection) @ y_zero / 2.0
            values, vectors = np.linalg.eigh(reflection_odd_zero_momentum)
            psi_plus = vectors[:, int(np.argmax(values))]
            psi_plus /= np.linalg.norm(psi_plus)
            components.extend(
                (
                    _low_rank_component("t6_minus_a", [(1.0, psi_plus, singlet)]),
                    _low_rank_component("t6_minus_b", [(1.0, singlet, psi_plus)]),
                )
            )
        elif time == 8:
            translation, _ = _translation_and_reflection(time)
            triplet_projector = _t8_triplet_projector(translation)
            values, vectors = np.linalg.eigh(triplet_projector)
            states = [vectors[:, index] for index in np.flatnonzero(values > 1e-8)]
            components.append(
                _low_rank_component(
                    "t8_triplet_projector", [(1.0, state, state) for state in states]
                )
            )
        elif time == 10:
            chi = _t10_chi()
            components.extend(
                (
                    _low_rank_component("t10_chi_projector", [(1.0, chi, chi)]),
                    _low_rank_component("t10_minus_a", [(1.0, chi, singlet)]),
                    _low_rank_component("t10_minus_b", [(1.0, singlet, chi)]),
                )
            )

    basis = ProtectedOperatorBasis(time, components)
    expected_rank = sum(transfer_multiplicities(time))
    if basis.rank != expected_rank:
        raise RuntimeError(
            f"protected basis rank mismatch at t={time}: {basis.rank} != {expected_rank}"
        )
    return basis


@dataclass
class RestartedArnoldiState:
    """Serializable state between bounded-memory Arnoldi restart cycles."""

    iteration: int
    basis: Any
    eigenvalue: complex = 0.0j
    residual: float = float("inf")
    eigenvalue_change: float = float("inf")
    stable_iterations: int = 0
    history: list[dict[str, float | int]] | None = None


class RestartedArnoldiGapSolver:
    """Projected explicitly restarted Arnoldi solver for paper-scale Figure 3."""

    def __init__(
        self,
        time: int,
        h_mean: float,
        sigma: float,
        *,
        krylov_dimension: int = 6,
        tolerance: float = 3e-5,
        eigenvalue_tolerance: float = 5e-6,
        stable_iterations: int = 2,
        max_iterations: int = 1600,
        seed: int = 264101,
        backend: str = "numpy",
        dtype: str = "complex128",
        dephasing_block_rows: int = 64,
        butterfly_chunk_size: int = 1024,
        projection_block_rows: int = 64,
        memory_limit_gib: float | None = None,
    ) -> None:
        if krylov_dimension < 3:
            raise ValueError("krylov_dimension must be at least three")
        self.time = int(time)
        self.h_mean = float(h_mean)
        self.sigma = float(sigma)
        self.krylov_dimension = int(krylov_dimension)
        self.tolerance = float(tolerance)
        self.eigenvalue_tolerance = float(eigenvalue_tolerance)
        self.required_stable_iterations = int(stable_iterations)
        self.max_iterations = int(max_iterations)
        self.seed = int(seed)
        self.backend = backend
        self.dtype = dtype
        self.projection_block_rows = int(projection_block_rows)
        self.module = array_module(backend)
        self.complex_type = _complex_dtype(self.module, dtype)
        self.protected = protected_operator_basis(time)
        self.transfer = TransferOperator(
            time=time,
            h_mean=h_mean,
            sigma=sigma,
            backend=backend,
            dtype=dtype,
            dephasing_block_rows=dephasing_block_rows,
            butterfly_chunk_size=butterfly_chunk_size,
        )
        self.size = self.transfer.dimension**2
        itemsize = np.dtype(dtype).itemsize
        # Existing restart vector, m+1 Arnoldi vectors, one transfer work vector,
        # and one orthogonalization/Ritz temporary.
        self.estimated_peak_gib = (
            (self.krylov_dimension + 4) * self.size * itemsize / 1024**3
        )
        if memory_limit_gib is not None and self.estimated_peak_gib > memory_limit_gib:
            raise MemoryError(
                f"estimated peak {self.estimated_peak_gib:.2f} GiB exceeds "
                f"configured limit {memory_limit_gib:.2f} GiB"
            )

    def _project(self, vector: Any, *, copy: bool) -> Any:
        return self.protected.project(
            vector,
            copy=copy,
            backend=self.backend,
            low_rank_block_rows=self.projection_block_rows,
        )

    def initialize(self) -> RestartedArnoldiState:
        module = self.module
        rng_seed = (
            self.seed
            + 1009 * self.time
            + int(round(1e6 * self.sigma))
            + int(round(1e3 * self.h_mean))
        )
        rng = module.random.RandomState(rng_seed)
        real_type = module.float32 if self.dtype == "complex64" else module.float64
        real = rng.standard_normal(self.size).astype(real_type, copy=False)
        imaginary = rng.standard_normal(self.size).astype(real_type, copy=False)
        vector = module.empty(self.size, dtype=self.complex_type)
        vector.real = real
        vector.imag = imaginary
        del real, imaginary
        vector = self._project(vector, copy=False)
        vector /= module.linalg.norm(vector)
        return RestartedArnoldiState(iteration=0, basis=vector, history=[])

    def step(self, state: RestartedArnoldiState) -> RestartedArnoldiState:
        module = self.module
        cycle_dimension = min(
            self.krylov_dimension, self.max_iterations - state.iteration
        )
        if cycle_dimension < 1:
            return state
        # Vectors are rows, so every transfer input and active Krylov block is
        # contiguous.  A column-vector layout can make GPU BLAS copy a strided
        # multi-vector transpose, silently adding tens of GiB at t=15.
        basis = module.empty(
            (cycle_dimension + 1, self.size), dtype=self.complex_type
        )
        restart = state.basis.reshape(-1)
        if restart.size != self.size:
            raise ValueError("restart vector has the wrong dimension")
        basis[0] = restart
        hessenberg = np.zeros(
            (cycle_dimension + 1, cycle_dimension), dtype=np.complex128
        )
        effective_dimension = cycle_dimension
        for column in range(cycle_dimension):
            work = self._project(self.transfer.matvec(basis[column]), copy=False)
            # Two-pass modified Gram-Schmidt controls loss of orthogonality in
            # complex64 at the large transfer dimensions.  With vectors stored
            # as rows, conjugating ``work`` in place computes B^H w as
            # conj(B conj(w)); the usual ``B.conj()`` spelling would allocate
            # up to five extra t=15
            # vectors and violate the 80 GiB contract.
            for _ in range(2):
                module.conjugate(work, out=work)
                coefficients = basis[: column + 1] @ work
                module.conjugate(work, out=work)
                coefficients = module.conj(coefficients)
                hessenberg[: column + 1, column] += _as_numpy(coefficients)
                work -= coefficients @ basis[: column + 1]
            beta = float(_as_numpy(module.linalg.norm(work)))
            hessenberg[column + 1, column] = beta
            if beta < 1e-12:
                effective_dimension = column + 1
                break
            basis[column + 1] = work / beta

        reduced = hessenberg[:effective_dimension, :effective_dimension]
        values, vectors = np.linalg.eig(reduced)
        selected = int(np.argmax(np.abs(values)))
        eigenvalue = complex(values[selected])
        host_coefficients = vectors[:, selected]
        residual = float(
            abs(
                hessenberg[effective_dimension, effective_dimension - 1]
                * host_coefficients[-1]
            )
        )
        coefficients = module.asarray(host_coefficients, dtype=self.complex_type)
        restart_vector = coefficients @ basis[:effective_dimension]
        restart_vector = self._project(restart_vector, copy=False)
        restart_vector /= module.linalg.norm(restart_vector)
        change = (
            abs(eigenvalue - state.eigenvalue)
            if state.iteration > 0
            else float("inf")
        )
        stable = (
            state.stable_iterations + 1
            if residual <= self.tolerance and change <= self.eigenvalue_tolerance
            else 0
        )
        history = list(state.history or [])
        history.append(
            {
                "iteration": state.iteration + effective_dimension,
                "leading_modulus": float(abs(eigenvalue)),
                "residual": residual,
                "eigenvalue_change": float(change),
            }
        )
        return RestartedArnoldiState(
            iteration=state.iteration + effective_dimension,
            basis=restart_vector,
            eigenvalue=eigenvalue,
            residual=residual,
            eigenvalue_change=float(change),
            stable_iterations=stable,
            history=history,
        )

    def converged(self, state: RestartedArnoldiState) -> bool:
        return state.stable_iterations >= self.required_stable_iterations

    def result(self, state: RestartedArnoldiState) -> dict[str, Any]:
        leading = float(abs(state.eigenvalue))
        return {
            "gap": float(np.clip(1.0 - leading, 0.0, 1.0)),
            "leading_modulus": leading,
            "residual": float(state.residual),
            "protected_rank": self.protected.rank,
            "converged": self.converged(state),
            "iterations": state.iteration,
            "estimated_peak_gib": self.estimated_peak_gib,
            "history": list(state.history or []),
        }


def spectral_gap(
    time: int,
    h_mean: float,
    sigma: float,
    *,
    arnoldi_k: int = 4,
    tolerance: float = 3e-6,
    max_iterations: int = 1600,
    seed: int = 264101,
    method: str = "arnoldi",
    krylov_dimension: int = 6,
    eigenvalue_tolerance: float = 5e-6,
    backend: str = "numpy",
    dtype: str = "complex128",
    dephasing_block_rows: int = 64,
    butterfly_chunk_size: int = 1024,
    projection_block_rows: int = 64,
    memory_limit_gib: float | None = None,
) -> dict[str, Any]:
    """Compute the largest subunit transfer eigenvalue after analytic deflation."""

    if sigma == 0.0:
        return {
            "gap": 0.0,
            "leading_modulus": 1.0,
            "residual": 0.0,
            "protected_rank": protected_operator_basis(time).rank,
            "converged": True,
            "iterations": 0,
        }

    if method == "restarted_arnoldi":
        solver = RestartedArnoldiGapSolver(
            time,
            h_mean,
            sigma,
            krylov_dimension=krylov_dimension,
            tolerance=tolerance,
            eigenvalue_tolerance=eigenvalue_tolerance,
            max_iterations=max_iterations,
            seed=seed,
            backend=backend,
            dtype=dtype,
            dephasing_block_rows=dephasing_block_rows,
            butterfly_chunk_size=butterfly_chunk_size,
            projection_block_rows=projection_block_rows,
            memory_limit_gib=memory_limit_gib,
        )
        state = solver.initialize()
        while state.iteration < max_iterations and not solver.converged(state):
            state = solver.step(state)
        return solver.result(state)
    if method != "arnoldi":
        raise ValueError(f"unsupported gap solver method: {method}")
    if backend != "numpy":
        raise ValueError("Arnoldi gap solver requires backend='numpy'")

    transfer = TransferOperator(
        time=time,
        h_mean=h_mean,
        sigma=sigma,
        dtype=dtype,
        dephasing_block_rows=dephasing_block_rows,
        butterfly_chunk_size=butterfly_chunk_size,
    )
    protected = protected_operator_basis(time)
    size = transfer.dimension**2

    def project(vector: np.ndarray) -> np.ndarray:
        return protected.project(
            vector,
            copy=True,
            backend="numpy",
            low_rank_block_rows=projection_block_rows,
        )

    def projected_matvec(vector: np.ndarray) -> np.ndarray:
        return project(transfer.matvec(project(vector)))

    operator = LinearOperator(
        (size, size), matvec=projected_matvec, dtype=np.dtype(dtype)
    )
    rng = np.random.default_rng(seed + 1009 * time + int(round(1e6 * sigma)) + int(round(1e3 * h_mean)))
    initial = project(rng.normal(size=size) + 1j * rng.normal(size=size))
    initial /= np.linalg.norm(initial)
    ncv = min(size - 1, max(2 * arnoldi_k + 8, 16))

    converged = True
    try:
        values, vectors = eigs(
            operator,
            k=arnoldi_k,
            which="LM",
            v0=initial,
            tol=tolerance,
            maxiter=max_iterations,
            ncv=ncv,
        )
    except ArpackNoConvergence as error:
        values = error.eigenvalues
        vectors = error.eigenvectors
        converged = False
        if values is None or vectors is None or len(values) == 0:
            raise RuntimeError(
                f"Arnoldi returned no eigenpairs for t={time}, h={h_mean}, sigma={sigma}"
            ) from error

    moduli = np.abs(values)
    index = int(np.argmax(moduli))
    leading = float(moduli[index])
    vector = vectors[:, index]
    residual = float(
        np.linalg.norm(projected_matvec(vector) - values[index] * vector)
        / np.linalg.norm(vector)
    )
    gap = float(np.clip(1.0 - leading, 0.0, 1.0))
    return {
        "gap": gap,
        "leading_modulus": leading,
        "residual": residual,
        "protected_rank": protected.rank,
        "converged": converged,
        "iterations": max_iterations if not converged else -1,
    }


def complete_small_gap(time: int, h_mean: float, sigma: float) -> float:
    """Reference full diagonalization for t<=5 tests."""

    if time > 5:
        raise ValueError("complete transfer diagonalization is restricted to t<=5")
    if sigma == 0.0:
        return 0.0
    values = np.linalg.eigvals(TransferOperator(time, h_mean, sigma).explicit_matrix())
    subunit = np.abs(values)[np.abs(np.abs(values) - 1.0) > 1e-7]
    return float(1.0 - np.max(subunit))
