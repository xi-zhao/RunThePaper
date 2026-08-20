"""Generic clean-room threshold engine for the paper's GF(4)-code proposal.

The article reports tests of unspecified ``n=11`` and ``n=17`` codes.  This
module deliberately does not guess those codes.  It accepts a complete
``[[n,1]]`` stabilizer specification and evaluates T-axis distillation from
Pauli weight enumerators, without author code, source curves, or dense 2**n by
2**n projectors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]

_PAULIS = frozenset("IXYZ")
_PRODUCTS: dict[tuple[str, str], tuple[complex, str]] = {
    ("I", "I"): (1, "I"),
    ("I", "X"): (1, "X"),
    ("I", "Y"): (1, "Y"),
    ("I", "Z"): (1, "Z"),
    ("X", "I"): (1, "X"),
    ("Y", "I"): (1, "Y"),
    ("Z", "I"): (1, "Z"),
    ("X", "X"): (1, "I"),
    ("Y", "Y"): (1, "I"),
    ("Z", "Z"): (1, "I"),
    ("X", "Y"): (1j, "Z"),
    ("Y", "X"): (-1j, "Z"),
    ("Y", "Z"): (1j, "X"),
    ("Z", "Y"): (-1j, "X"),
    ("Z", "X"): (1j, "Y"),
    ("X", "Z"): (-1j, "Y"),
}


@dataclass(frozen=True)
class PauliWord:
    """Hermitian signed Pauli word."""

    phase: complex
    letters: str


@dataclass(frozen=True)
class StabilizerCode:
    """Complete ``[[n,1]]`` stabilizer and logical-Pauli specification."""

    name: str
    n_qubits: int
    stabilizer_generators: tuple[str, ...]
    logical_x: str
    logical_y: str
    logical_z: str

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> "StabilizerCode":
        return cls(
            name=str(payload["name"]),
            n_qubits=int(payload["n_qubits"]),
            stabilizer_generators=tuple(
                str(value) for value in payload["stabilizer_generators"]  # type: ignore[index]
            ),
            logical_x=str(payload["logical_x"]),
            logical_y=str(payload["logical_y"]),
            logical_z=str(payload["logical_z"]),
        )


def _parse_word(value: str, n_qubits: int) -> PauliWord:
    sign = 1
    letters = value.strip().upper()
    if letters[:1] in {"+", "-"}:
        sign = -1 if letters[0] == "-" else 1
        letters = letters[1:]
    if len(letters) != n_qubits or set(letters) - _PAULIS:
        raise ValueError(f"invalid length-{n_qubits} Pauli word: {value!r}")
    return PauliWord(complex(sign), letters)


def multiply(left: PauliWord, right: PauliWord) -> PauliWord:
    """Multiply two Pauli words while retaining the global phase."""

    if len(left.letters) != len(right.letters):
        raise ValueError("Pauli words have different lengths")
    phase = left.phase * right.phase
    output: list[str] = []
    for first, second in zip(left.letters, right.letters, strict=True):
        local_phase, letter = _PRODUCTS[(first, second)]
        phase *= local_phase
        output.append(letter)
    return PauliWord(complex(np.real_if_close(phase)), "".join(output))


def commute(left: PauliWord, right: PauliWord) -> bool:
    """Return whether two Pauli words commute."""

    anti = sum(
        first != "I" and second != "I" and first != second
        for first, second in zip(left.letters, right.letters, strict=True)
    )
    return anti % 2 == 0


def stabilizer_group(code: StabilizerCode) -> tuple[PauliWord, ...]:
    """Enumerate the independent stabilizer group with fail-closed checks."""

    if code.n_qubits < 1:
        raise ValueError("n_qubits must be positive")
    if len(code.stabilizer_generators) != code.n_qubits - 1:
        raise ValueError("an [[n,1]] code requires exactly n-1 generators")
    generators = tuple(
        _parse_word(value, code.n_qubits) for value in code.stabilizer_generators
    )
    for index, left in enumerate(generators):
        if not np.isclose(left.phase.imag, 0.0):
            raise ValueError("stabilizer generators must be Hermitian")
        for right in generators[index + 1 :]:
            if not commute(left, right):
                raise ValueError("stabilizer generators must commute")

    identity = PauliWord(1 + 0j, "I" * code.n_qubits)
    elements = [identity]
    for generator in generators:
        elements += [multiply(element, generator) for element in elements]
    by_letters: dict[str, complex] = {}
    for element in elements:
        if not np.isclose(element.phase.imag, 0.0, atol=1e-12):
            raise ValueError("commuting stabilizers produced a non-Hermitian element")
        previous = by_letters.setdefault(element.letters, element.phase)
        if not np.isclose(previous, element.phase, atol=1e-12):
            raise ValueError("inconsistent stabilizer phases")
    if len(by_letters) != 2 ** (code.n_qubits - 1):
        raise ValueError("stabilizer generators are not independent")
    return tuple(PauliWord(phase, letters) for letters, phase in by_letters.items())


def _logical_words(code: StabilizerCode) -> tuple[PauliWord, PauliWord, PauliWord]:
    logicals = tuple(
        _parse_word(value, code.n_qubits)
        for value in (code.logical_x, code.logical_y, code.logical_z)
    )
    generators = tuple(
        _parse_word(value, code.n_qubits) for value in code.stabilizer_generators
    )
    for logical in logicals:
        if all(letter == "I" for letter in logical.letters):
            raise ValueError("logical Pauli cannot be identity")
        if any(not commute(logical, generator) for generator in generators):
            raise ValueError("logical Pauli must commute with every stabilizer")
    if any(
        commute(left, right)
        for left, right in (
            (logicals[0], logicals[1]),
            (logicals[1], logicals[2]),
            (logicals[2], logicals[0]),
        )
    ):
        raise ValueError("logical X, Y, and Z must anticommute pairwise")
    return logicals  # type: ignore[return-value]


def _signed_weight_enumerator(words: Iterable[PauliWord], n_qubits: int) -> FloatArray:
    coefficients = np.zeros(n_qubits + 1, dtype=float)
    for word in words:
        if not np.isclose(word.phase.imag, 0.0, atol=1e-12):
            raise ValueError("T-axis expectation requires Hermitian Pauli words")
        weight = sum(letter != "I" for letter in word.letters)
        coefficients[weight] += float(word.phase.real)
    return coefficients


def code_weight_enumerators(code: StabilizerCode) -> dict[str, FloatArray]:
    """Return signed stabilizer and logical-coset weight enumerators."""

    group = stabilizer_group(code)
    logical_x, logical_y, logical_z = _logical_words(code)
    return {
        "stabilizer": _signed_weight_enumerator(group, code.n_qubits),
        "logical_x": _signed_weight_enumerator(
            (multiply(item, logical_x) for item in group), code.n_qubits
        ),
        "logical_y": _signed_weight_enumerator(
            (multiply(item, logical_y) for item in group), code.n_qubits
        ),
        "logical_z": _signed_weight_enumerator(
            (multiply(item, logical_z) for item in group), code.n_qubits
        ),
    }


def _evaluate_enumerator(
    coefficients: FloatArray, polarization: FloatArray
) -> FloatArray:
    local = polarization / np.sqrt(3.0)
    powers = np.arange(coefficients.size, dtype=int)
    return np.sum(coefficients * local[..., None] ** powers, axis=-1)


def _evaluate_from_enumerators(
    enumerators: dict[str, FloatArray], n_qubits: int, epsilon: ArrayLike
) -> tuple[float | FloatArray, float | FloatArray]:
    e = np.asarray(epsilon, dtype=float)
    if np.any((e < 0.0) | (e > 0.5)):
        raise ValueError("epsilon must lie in [0, 0.5]")
    polarization = 1.0 - 2.0 * e
    normalization = float(2 ** (n_qubits - 1))
    success = (
        _evaluate_enumerator(enumerators["stabilizer"], polarization) / normalization
    )
    if np.any(success <= 0.0):
        raise ValueError("code has non-positive syndrome probability")
    logical_components = [
        _evaluate_enumerator(enumerators[name], polarization) / normalization / success
        for name in ("logical_x", "logical_y", "logical_z")
    ]
    output_polarization = sum(logical_components) / np.sqrt(3.0)
    output_error = np.clip(0.5 * (1.0 - output_polarization), 0.0, 0.5)
    if np.ndim(epsilon) == 0:
        return float(success), float(output_error)
    return np.asarray(success, dtype=float), np.asarray(output_error, dtype=float)


def evaluate_t_axis_code(
    code: StabilizerCode, epsilon: ArrayLike
) -> tuple[float | FloatArray, float | FloatArray]:
    """Evaluate syndrome success and conditional T-axis output error."""

    return _evaluate_from_enumerators(
        code_weight_enumerators(code), code.n_qubits, epsilon
    )


def interior_threshold(code: StabilizerCode) -> float:
    """Find the first nontrivial fixed point of epsilon_out(epsilon)."""

    enumerators = code_weight_enumerators(code)
    grid = np.linspace(1e-7, 0.5 - 1e-7, 2001)
    _, output = _evaluate_from_enumerators(enumerators, code.n_qubits, grid)
    residual = np.asarray(output) - grid
    brackets = [
        (float(grid[index]), float(grid[index + 1]))
        for index in range(grid.size - 1)
        if residual[index] * residual[index + 1] < 0.0
    ]
    if not brackets:
        raise ValueError("no nontrivial distillation threshold found")
    low, high = brackets[0]
    for _ in range(80):
        middle = 0.5 * (low + high)
        _, output_middle = _evaluate_from_enumerators(
            enumerators, code.n_qubits, middle
        )
        _, output_low = _evaluate_from_enumerators(enumerators, code.n_qubits, low)
        if (float(output_low) - low) * (float(output_middle) - middle) <= 0.0:
            high = middle
        else:
            low = middle
    return 0.5 * (low + high)


def five_qubit_code() -> StabilizerCode:
    """The printed five-qubit code, used as a known-answer validation fixture."""

    # The paper's accepted +T input is the -T eigenstate in the conventional
    # XXXXX/YYYYY/ZZZZZ logical frame.  The odd X/Y permutation below keeps a
    # right-handed Pauli frame while incorporating the decoded Clifford that
    # maps that state back to the output +T axis.
    return StabilizerCode(
        name="printed-five-qubit-code",
        n_qubits=5,
        stabilizer_generators=("XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"),
        logical_x="-YYYYY",
        logical_y="-XXXXX",
        logical_z="-ZZZZZ",
    )
