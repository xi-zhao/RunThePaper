"""Independent Eq. (3) simulator for the EV20 Rydberg-qudit paper.

The module keeps the scientific object explicit:

graph -> weighted proper colorings -> atom coordinates -> one laser channel per
Rydberg level -> sparse time-dependent Hamiltonian -> coloring probabilities.

It intentionally does not adapt the model to a qubit/MIS simulator.  The local
Hilbert space has one preparation state ``|g>`` plus ``k`` distinct Rydberg
levels, so a faithful backend needs local dimension ``k + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import expm_multiply


TWO_PI = 2.0 * math.pi
DEFAULT_SAMPLE_COUNT = 300


@dataclass(frozen=True)
class AnnealingSchedule:
    """The source-bound normalized controls in equations (5) and (6)."""

    ramp_on_end_us: float = 0.4
    detuning_sweep_end_us: float = 8.0
    duration_us: float = 8.4

    def normalized(self, time_us: float) -> tuple[float, float]:
        """Return ``(omega_tilde, delta_tilde)`` at one physical time."""

        if not 0.0 <= time_us <= self.duration_us:
            raise ValueError("time must lie inside the annealing interval")
        ti = self.ramp_on_end_us
        tf = self.detuning_sweep_end_us
        if time_us <= ti:
            omega = time_us / ti
        elif time_us <= tf:
            omega = 1.0
        else:
            omega = (self.duration_us - time_us) / (self.duration_us - tf)

        if time_us <= ti:
            detuning = -1.0
        elif time_us <= tf:
            midpoint = 0.5 * (ti + tf)
            width = tf - ti
            detuning = 8.0 * (time_us - midpoint) ** 3 / width**3
        else:
            detuning = 1.0
        return float(omega), float(detuning)

    def times(self, sample_count: int = DEFAULT_SAMPLE_COUNT) -> np.ndarray:
        if sample_count < 2:
            raise ValueError("sample_count must be at least two")
        return np.linspace(0.0, self.duration_us, sample_count, dtype=float)


@dataclass(frozen=True)
class RydbergLevelProfile:
    """One source-bound set of Rydberg levels and global laser channels."""

    profile_id: str
    principal_quantum_numbers: tuple[int, ...]
    c6_intra_2pi_ghz_um6: tuple[float, ...]
    c6_inter_2pi_ghz_um6: tuple[tuple[float, ...], ...]
    omega_max_over_2pi_mhz: tuple[float, ...]
    detuning_max_over_2pi_mhz: tuple[float, ...]

    def __post_init__(self) -> None:
        count = len(self.principal_quantum_numbers)
        if count < 2:
            raise ValueError("a qudit profile requires at least two Rydberg levels")
        if any(
            len(values) != count
            for values in (
                self.c6_intra_2pi_ghz_um6,
                self.c6_inter_2pi_ghz_um6,
                self.omega_max_over_2pi_mhz,
                self.detuning_max_over_2pi_mhz,
            )
        ):
            raise ValueError("all profile arrays must match the Rydberg level count")
        if any(len(row) != count for row in self.c6_inter_2pi_ghz_um6):
            raise ValueError("inter-level C6 must be a square matrix")
        matrix = np.asarray(self.c6_inter_2pi_ghz_um6, dtype=float)
        if not np.allclose(matrix, matrix.T, atol=0.0, rtol=0.0):
            raise ValueError("inter-level C6 matrix must be symmetric")
        if not np.allclose(np.diag(matrix), 0.0, atol=0.0, rtol=0.0):
            raise ValueError("inter-level C6 diagonal must be zero")

    @property
    def rydberg_level_count(self) -> int:
        return len(self.principal_quantum_numbers)

    @property
    def local_dimension(self) -> int:
        return self.rydberg_level_count + 1

    @property
    def omega_max_rad_per_us(self) -> np.ndarray:
        return TWO_PI * np.asarray(self.omega_max_over_2pi_mhz, dtype=float)

    @property
    def detuning_max_rad_per_us(self) -> np.ndarray:
        return TWO_PI * np.asarray(self.detuning_max_over_2pi_mhz, dtype=float)

    @property
    def c6_intra_rad_per_us_um6(self) -> np.ndarray:
        return TWO_PI * 1000.0 * np.asarray(
            self.c6_intra_2pi_ghz_um6,
            dtype=float,
        )

    @property
    def c6_inter_rad_per_us_um6(self) -> np.ndarray:
        return TWO_PI * 1000.0 * np.asarray(
            self.c6_inter_2pi_ghz_um6,
            dtype=float,
        )


def _symmetric_c6_matrix(
    count: int,
    values: dict[tuple[int, int], float],
) -> tuple[tuple[float, ...], ...]:
    matrix = np.zeros((count, count), dtype=float)
    for (left, right), value in values.items():
        matrix[left - 1, right - 1] = value
        matrix[right - 1, left - 1] = value
    return tuple(tuple(float(value) for value in row) for row in matrix)


PROFILE_K2_65_70 = RydbergLevelProfile(
    profile_id="EV20-K2-65-70",
    principal_quantum_numbers=(65, 70),
    c6_intra_2pi_ghz_um6=(360.7, 862.7),
    c6_inter_2pi_ghz_um6=_symmetric_c6_matrix(2, {(1, 2): -94.1}),
    omega_max_over_2pi_mhz=(3.0, 7.0),
    detuning_max_over_2pi_mhz=(8.0, 19.0),
)

PROFILE_K3_65_70_75 = RydbergLevelProfile(
    profile_id="EV20-K3-65-70-75",
    principal_quantum_numbers=(65, 70, 75),
    c6_intra_2pi_ghz_um6=(360.7, 862.7, 1984.5),
    c6_inter_2pi_ghz_um6=_symmetric_c6_matrix(
        3,
        {(1, 2): -94.1, (1, 3): -35.0, (2, 3): -226.7},
    ),
    omega_max_over_2pi_mhz=(1.0, 2.0, 5.0),
    detuning_max_over_2pi_mhz=(5.0, 10.0, 15.0),
)

PROFILE_K4_61_66_72_78 = RydbergLevelProfile(
    profile_id="EV20-K4-61-66-72-78",
    principal_quantum_numbers=(61, 66, 72, 78),
    c6_intra_2pi_ghz_um6=(169.2, 431.4, 1203.7, 3091.1),
    c6_inter_2pi_ghz_um6=_symmetric_c6_matrix(
        4,
        {
            (1, 2): -35.3,
            (1, 3): -12.1,
            (1, 4): -25.3,
            (2, 3): -76.8,
            (2, 4): -36.9,
            (3, 4): -234.1,
        },
    ),
    omega_max_over_2pi_mhz=(1.0, 2.0, 5.0, 8.0),
    detuning_max_over_2pi_mhz=(3.0, 10.0, 15.0, 25.0),
)

PROFILE_K3_WHEEL_60_65_75 = RydbergLevelProfile(
    profile_id="EV20-K3-WHEEL-60-65-75",
    principal_quantum_numbers=(60, 65, 75),
    c6_intra_2pi_ghz_um6=(138.9, 360.7, 1948.4),
    c6_inter_2pi_ghz_um6=_symmetric_c6_matrix(
        3,
        {(1, 2): -28.5, (1, 3): -8.0, (2, 3): -34.9},
    ),
    omega_max_over_2pi_mhz=(2.0, 3.0, 5.0),
    detuning_max_over_2pi_mhz=(2.5, 10.0, 15.0),
)


@dataclass(frozen=True)
class PaperGraph:
    graph_id: str
    chromatic_number: int
    normalized_coordinates: tuple[tuple[float, float, float], ...]
    edges: tuple[tuple[int, int], ...]
    lattice_spacing_um_by_k: tuple[tuple[int, float], ...]

    @property
    def atom_count(self) -> int:
        return len(self.normalized_coordinates)

    def lattice_spacing_um(self, rydberg_level_count: int) -> float:
        spacings = dict(self.lattice_spacing_um_by_k)
        try:
            return float(spacings[rydberg_level_count])
        except KeyError as exc:
            raise ValueError(
                f"graph {self.graph_id} has no k={rydberg_level_count} source spacing"
            ) from exc

    def coordinates_um(self, rydberg_level_count: int) -> np.ndarray:
        return self.lattice_spacing_um(rydberg_level_count) * np.asarray(
            self.normalized_coordinates,
            dtype=float,
        )


def _distance_edges(
    coordinates: tuple[tuple[float, float, float], ...],
    threshold: float = 1.001,
) -> tuple[tuple[int, int], ...]:
    values = np.asarray(coordinates, dtype=float)
    return tuple(
        (left, right)
        for left in range(len(values))
        for right in range(left + 1, len(values))
        if float(np.linalg.norm(values[left] - values[right])) <= threshold
    )


SQRT3 = math.sqrt(3.0)
_NORMALIZED_COORDINATES: dict[str, tuple[tuple[float, float, float], ...]] = {
    "A": ((0.0, 0.0, 0.0), (0.5, SQRT3 / 2.0, 0.0), (1.0, 0.0, 0.0)),
    "B": ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    "C": (
        (0.0, 0.0, 0.0),
        (0.5, SQRT3 / 2.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.5, -SQRT3 / 2.0, 0.0),
    ),
    "D": (
        (0.0, 0.0, 0.0),
        (0.5, SQRT3 / 2.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.5, SQRT3 / 2.0, 0.0),
        (2.0, 0.0, 0.0),
    ),
    "E": (
        (-1.0, 0.0, 0.0),
        (-0.5, SQRT3 / 2.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.5, SQRT3 / 2.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, SQRT3, 0.0),
    ),
    "F": (
        (-1.0, 0.0, 0.0),
        (-0.5, SQRT3 / 2.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.5, SQRT3 / 2.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.5, SQRT3 / 2.0, 0.0),
    ),
    "G": (
        (0.0, 1.0, 0.0),
        (SQRT3 / 2.0, -0.5, 0.0),
        (-SQRT3 / 2.0, -0.5, 0.0),
        (0.0, 0.0, 0.0),
    ),
    "H": ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    # Table 1 writes the tetrahedron as (0,0,0),(-a,0,a),... while table 2
    # calls its reported value the physical lattice spacing.  Scaling the
    # printed coordinate pattern by 1/sqrt(2) makes every physical edge equal
    # to that table-2 spacing and is required by the quoted blockade radii.
    "I": tuple(
        tuple(value / math.sqrt(2.0) for value in coordinate)
        for coordinate in (
            (0.0, 0.0, 0.0),
            (-1.0, 0.0, 1.0),
            (0.0, 1.0, 1.0),
            (-1.0, 1.0, 0.0),
        )
    ),
    "J": (
        (0.0, 0.0, 0.0),
        *tuple(
            (
                math.sin(math.radians(72.0 * index)),
                math.cos(math.radians(72.0 * index)),
                0.0,
            )
            for index in range(1, 6)
        ),
    ),
}


def _complete_edges(atom_count: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (left, right)
        for left in range(atom_count)
        for right in range(left + 1, atom_count)
    )


def _wheel_edges() -> tuple[tuple[int, int], ...]:
    outer = tuple(range(1, 6))
    spokes = tuple((0, vertex) for vertex in outer)
    cycle = tuple((outer[index], outer[(index + 1) % len(outer)]) for index in range(5))
    return tuple(sorted((*spokes, *cycle)))


PAPER_GRAPHS: dict[str, PaperGraph] = {}
for _graph_id in "ABCDEF":
    _coordinates = _NORMALIZED_COORDINATES[_graph_id]
    PAPER_GRAPHS[_graph_id] = PaperGraph(
        graph_id=_graph_id,
        chromatic_number=2 if _graph_id == "B" else 3,
        normalized_coordinates=_coordinates,
        edges=_distance_edges(_coordinates),
        lattice_spacing_um_by_k=(
            (2, {"A": 5.26, "B": 5.26, "C": 4.99, "D": 5.26, "E": 4.91, "F": 5.26}[_graph_id]),
            (3, {"A": 6.33, "B": 6.41, "C": 6.75, "D": 6.75, "E": 6.75, "F": 6.75}[_graph_id]),
        ),
    )

for _graph_id in "GHI":
    _coordinates = _NORMALIZED_COORDINATES[_graph_id]
    PAPER_GRAPHS[_graph_id] = PaperGraph(
        graph_id=_graph_id,
        chromatic_number=4,
        normalized_coordinates=_coordinates,
        edges=_complete_edges(4),
        lattice_spacing_um_by_k=(
            (3, {"G": 3.37, "H": 4.45, "I": 5.61}[_graph_id]),
            (4, {"G": 2.97, "H": 3.83, "I": 5.90}[_graph_id]),
        ),
    )

PAPER_GRAPHS["J"] = PaperGraph(
    graph_id="J",
    chromatic_number=4,
    normalized_coordinates=_NORMALIZED_COORDINATES["J"],
    edges=_wheel_edges(),
    lattice_spacing_um_by_k=((3, 4.10),),
)


@dataclass(frozen=True)
class QuditAnnealingProgram:
    graph: PaperGraph
    profile: RydbergLevelProfile
    schedule: AnnealingSchedule
    ground_state_is_color: bool

    @property
    def basis_state_count(self) -> int:
        return self.profile.local_dimension**self.graph.atom_count

    @property
    def pasqal_qubit_backend_status(self) -> str:
        return "not_applicable_multilevel_hilbert_space"

    def control_at_time(self, time_us: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        omega_scale, detuning_scale = self.schedule.normalized(time_us)
        return (
            omega_scale * self.profile.omega_max_rad_per_us,
            detuning_scale * self.profile.detuning_max_rad_per_us,
            np.zeros(self.profile.rydberg_level_count, dtype=float),
        )


def compile_paper_program(
    graph_id: str,
    rydberg_level_count: int,
) -> QuditAnnealingProgram:
    """Compile one table-1/table-2 graph into the published global controls."""

    try:
        graph = PAPER_GRAPHS[graph_id.upper()]
    except KeyError as exc:
        raise ValueError(f"unknown EV20 graph: {graph_id}") from exc
    if graph.graph_id == "J":
        if rydberg_level_count != 3:
            raise ValueError("graph J is source-bound only for the k=3 wheel profile")
        profile = PROFILE_K3_WHEEL_60_65_75
    else:
        profiles = {
            2: PROFILE_K2_65_70,
            3: PROFILE_K3_65_70_75,
            4: PROFILE_K4_61_66_72_78,
        }
        try:
            profile = profiles[rydberg_level_count]
        except KeyError as exc:
            raise ValueError("only the paper's k=2, k=3 and k=4 profiles are available") from exc
    graph.lattice_spacing_um(rydberg_level_count)
    return QuditAnnealingProgram(
        graph=graph,
        profile=profile,
        schedule=AnnealingSchedule(),
        ground_state_is_color=rydberg_level_count < graph.chromatic_number,
    )


def enumerate_basis(program: QuditAnnealingProgram) -> np.ndarray:
    """Enumerate lexicographic local states ``g,r1,...,rk``."""

    dimension = program.profile.local_dimension
    atom_count = program.graph.atom_count
    count = dimension**atom_count
    indices = np.arange(count, dtype=np.int64)[:, None]
    powers = dimension ** np.arange(atom_count - 1, -1, -1, dtype=np.int64)
    return ((indices // powers) % dimension).astype(np.int8)


def target_coloring_indices(
    program: QuditAnnealingProgram,
    basis: np.ndarray | None = None,
    final_diagonal_energy: np.ndarray | None = None,
) -> np.ndarray:
    """Return the lowest-energy proper colorings for the declared encoding.

    For the robust main protocol, ``|g>`` is preparation-only and every vertex
    must occupy a Rydberg color.  Appendix-B ``k=chi-1`` programs allow ``|g>``
    as a candidate color, but still require adjacent vertices to differ.
    """

    if basis is None:
        basis = enumerate_basis(program)
    allowed = np.ones(len(basis), dtype=bool)
    if not program.ground_state_is_color:
        allowed &= np.all(basis > 0, axis=1)
    for left, right in program.graph.edges:
        allowed &= basis[:, left] != basis[:, right]
    if final_diagonal_energy is None:
        excitation_counts = np.stack(
            [
                (basis == level).sum(axis=1)
                for level in range(1, program.profile.rydberg_level_count + 1)
            ],
            axis=1,
        ).astype(float)
        final_diagonal_energy = (
            _interaction_energies(program, basis)
            - excitation_counts @ program.profile.detuning_max_rad_per_us
        )
    energies = np.asarray(final_diagonal_energy, dtype=float).copy()
    energies[~allowed] = np.inf
    best = float(np.min(energies))
    if not math.isfinite(best):
        raise ValueError("the requested color profile has no proper coloring")
    return np.flatnonzero(np.isclose(energies, best, atol=1e-9, rtol=0.0))


def proper_coloring_indices(
    program: QuditAnnealingProgram,
    basis: np.ndarray | None = None,
) -> np.ndarray:
    """Return every mathematically valid coloring in the declared color space."""

    if basis is None:
        basis = enumerate_basis(program)
    allowed = np.ones(len(basis), dtype=bool)
    if not program.ground_state_is_color:
        allowed &= np.all(basis > 0, axis=1)
    for left, right in program.graph.edges:
        allowed &= basis[:, left] != basis[:, right]
    return np.flatnonzero(allowed)


def paper_figure_target_indices(
    program: QuditAnnealingProgram,
    basis: np.ndarray,
    final_diagonal_energy: np.ndarray,
) -> np.ndarray:
    """Resolve the source figure's declared ground-state solution subset.

    Figure 5(h) explicitly isolates one dominant Z2 pair for graph F.  Those
    two basis configurations are a target definition from the paper, not a
    value inferred from the released probabilities.  Other panels use the
    lowest-energy proper-coloring subset of the printed Hamiltonian.
    """

    if (
        program.graph.graph_id == "F"
        and program.profile.profile_id == PROFILE_K3_65_70_75.profile_id
    ):
        declared = {
            (2, 3, 1, 2, 3, 1),
            (1, 3, 2, 1, 3, 2),
        }
        indices = np.asarray(
            [index for index, state in enumerate(basis) if tuple(state) in declared],
            dtype=np.int64,
        )
        if len(indices) != 2:
            raise RuntimeError("failed to resolve the Figure-5 graph-F Z2 pair")
        return indices
    return target_coloring_indices(
        program,
        basis,
        final_diagonal_energy=final_diagonal_energy,
    )


@dataclass(frozen=True)
class _Operators:
    drive_by_level: tuple[sparse.csr_matrix, ...]
    excitation_count_by_level: np.ndarray
    interaction_energy_rad_per_us: np.ndarray


def _interaction_energies(
    program: QuditAnnealingProgram,
    basis: np.ndarray,
) -> np.ndarray:
    atom_count = program.graph.atom_count
    basis_count = len(basis)
    interactions = np.zeros(basis_count, dtype=float)
    coordinates = program.graph.coordinates_um(program.profile.rydberg_level_count)
    intra = program.profile.c6_intra_rad_per_us_um6
    inter = program.profile.c6_inter_rad_per_us_um6
    for left in range(atom_count):
        for right in range(left + 1, atom_count):
            distance = float(np.linalg.norm(coordinates[left] - coordinates[right]))
            left_states = basis[:, left]
            right_states = basis[:, right]
            occupied = np.flatnonzero((left_states > 0) & (right_states > 0))
            same = occupied[left_states[occupied] == right_states[occupied]]
            different = occupied[left_states[occupied] != right_states[occupied]]
            interactions[same] += intra[left_states[same] - 1] / distance**6
            interactions[different] += (
                inter[left_states[different] - 1, right_states[different] - 1]
                / distance**6
            )
    return interactions


def _operators(program: QuditAnnealingProgram, basis: np.ndarray) -> _Operators:
    dimension = program.profile.local_dimension
    atom_count = program.graph.atom_count
    basis_count = len(basis)
    powers = dimension ** np.arange(atom_count - 1, -1, -1, dtype=np.int64)
    drives: list[sparse.csr_matrix] = []
    for level in range(1, program.profile.rydberg_level_count + 1):
        rows: list[int] = []
        columns: list[int] = []
        for site, power in enumerate(powers):
            ground_indices = np.flatnonzero(basis[:, site] == 0)
            excited_indices = ground_indices + level * int(power)
            rows.extend(ground_indices.tolist())
            columns.extend(excited_indices.tolist())
            rows.extend(excited_indices.tolist())
            columns.extend(ground_indices.tolist())
        drives.append(
            sparse.csr_matrix(
                (np.ones(len(rows), dtype=float), (rows, columns)),
                shape=(basis_count, basis_count),
            )
        )

    excitation_counts = np.stack(
        [
            (basis == level).sum(axis=1)
            for level in range(1, program.profile.rydberg_level_count + 1)
        ],
        axis=1,
    ).astype(float)
    return _Operators(
        drive_by_level=tuple(drives),
        excitation_count_by_level=excitation_counts,
        interaction_energy_rad_per_us=_interaction_energies(program, basis),
    )


@dataclass(frozen=True)
class QuditSimulationResult:
    graph_id: str
    profile_id: str
    times_us: np.ndarray
    target_probability: np.ndarray
    final_probabilities: np.ndarray
    target_indices: np.ndarray
    proper_coloring_indices: np.ndarray
    basis: np.ndarray
    final_norm_error: float
    propagation_scheme: str = "left_endpoint_piecewise_constant_sparse_expm"

    @property
    def final_target_probability(self) -> float:
        return float(self.target_probability[-1])

    @property
    def most_likely_state_index(self) -> int:
        return int(np.argmax(self.final_probabilities))

    @property
    def most_likely_local_states(self) -> tuple[int, ...]:
        return tuple(int(value) for value in self.basis[self.most_likely_state_index])


def simulate_program(
    program: QuditAnnealingProgram,
    *,
    times_us: Iterable[float] | np.ndarray | None = None,
) -> QuditSimulationResult:
    """Evolve Eq. (3) with one sparse matrix exponential per source time step."""

    times = (
        program.schedule.times()
        if times_us is None
        else np.asarray(tuple(times_us), dtype=float)
    )
    if times.ndim != 1 or len(times) < 2:
        raise ValueError("times must be a one-dimensional sequence")
    if not np.isclose(times[0], 0.0) or not np.isclose(times[-1], program.schedule.duration_us):
        raise ValueError("times must span the full source annealing interval")
    if np.any(np.diff(times) <= 0.0):
        raise ValueError("times must be strictly increasing")

    basis = enumerate_basis(program)
    operators = _operators(program, basis)
    final_diagonal_energy = (
        operators.interaction_energy_rad_per_us
        - operators.excitation_count_by_level
        @ program.profile.detuning_max_rad_per_us
    )
    targets = paper_figure_target_indices(
        program,
        basis,
        final_diagonal_energy,
    )
    proper_colorings = proper_coloring_indices(program, basis)
    state = np.zeros(len(basis), dtype=np.complex128)
    state[0] = 1.0 + 0.0j
    target_probabilities = [float(np.sum(np.abs(state[targets]) ** 2))]

    for index in range(1, len(times)):
        duration = float(times[index] - times[index - 1])
        omega, detuning, _phase = program.control_at_time(float(times[index - 1]))
        diagonal = (
            operators.interaction_energy_rad_per_us
            - operators.excitation_count_by_level @ detuning
        )
        hamiltonian = sparse.diags(diagonal, format="csr")
        for level_index, drive in enumerate(operators.drive_by_level):
            hamiltonian = hamiltonian + 0.5 * omega[level_index] * drive
        state = expm_multiply((-1j * duration) * hamiltonian, state)
        target_probabilities.append(float(np.sum(np.abs(state[targets]) ** 2)))

    raw_norm = float(np.vdot(state, state).real)
    if not math.isfinite(raw_norm) or raw_norm <= 0.0:
        raise RuntimeError("qudit evolution produced an invalid state norm")
    state /= math.sqrt(raw_norm)
    probabilities = np.abs(state) ** 2
    return QuditSimulationResult(
        graph_id=program.graph.graph_id,
        profile_id=program.profile.profile_id,
        times_us=times,
        target_probability=np.asarray(target_probabilities, dtype=float),
        final_probabilities=probabilities,
        target_indices=targets,
        proper_coloring_indices=proper_colorings,
        basis=basis,
        final_norm_error=abs(raw_norm - 1.0),
    )


def hardware_control_rows(
    program: QuditAnnealingProgram,
    times_us: Iterable[float] = (0.0, 0.4, 4.2, 8.0, 8.4),
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for time_us in times_us:
        omega, detuning, phase = program.control_at_time(float(time_us))
        for level_index, principal_n in enumerate(program.profile.principal_quantum_numbers):
            rows.append(
                {
                    "graph_id": program.graph.graph_id,
                    "profile_id": program.profile.profile_id,
                    "time_us": float(time_us),
                    "channel_index": level_index + 1,
                    "rydberg_state": f"{principal_n}S1/2,mj=1/2",
                    "omega_rad_per_us": float(omega[level_index]),
                    "omega_over_2pi_mhz": float(omega[level_index] / TWO_PI),
                    "detuning_rad_per_us": float(detuning[level_index]),
                    "detuning_over_2pi_mhz": float(detuning[level_index] / TWO_PI),
                    "phase_rad": float(phase[level_index]),
                }
            )
    return rows


def atom_coordinate_rows(
    program: QuditAnnealingProgram,
) -> list[dict[str, float | int | str]]:
    coordinates = program.graph.coordinates_um(program.profile.rydberg_level_count)
    return [
        {
            "graph_id": program.graph.graph_id,
            "atom_index": index,
            "x_um": float(coordinate[0]),
            "y_um": float(coordinate[1]),
            "z_um": float(coordinate[2]),
        }
        for index, coordinate in enumerate(coordinates)
    ]
