"""Finite-block certificate for the pure-state communication-rate theorem.

The paper states that preparing many separated copies of a bipartite pure
state costs ``E(psi)`` transmitted qubits per copy.  This module derives the
finite-block optimum without using author code or numerical arrays:

* achievability keeps the largest Schmidt coefficients and transmits the
  resulting compressed subsystem;
* the converse uses the fact that transmitting ``q`` qubits from an initially
  product bipartition can create Schmidt rank at most ``2**q``;
* the Ky Fan bound says that no rank-limited approximation can have more
  fidelity than the sum of the same largest Schmidt coefficients.

Thus the first ``q`` whose rank-limited mass reaches the requested fidelity is
both an achievable cost and a converse lower bound.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from scipy.special import gammaln

from .model import binary_entropy


@dataclass(frozen=True)
class OperationalRateRecord:
    """A finite-block achievability-and-converse certificate."""

    schmidt_probability: float
    copies: int
    allowed_infidelity: float
    entropy_rate: float
    optimal_transmitted_qubits: int
    optimal_rate: float
    rate_minus_entropy: float
    achievable_fidelity: float
    converse_fidelity_with_one_fewer_qubit: float
    cutoff_type: int


def _log_integer(value: int) -> float:
    if value <= 0:
        return -math.inf
    return math.log(value)


def _logaddexp(left: float, right: float) -> float:
    upper = max(left, right)
    lower = min(left, right)
    if upper == math.inf or upper == -math.inf:
        return upper
    return upper + math.log1p(math.exp(lower - upper))


def _candidate_fidelity(
    *,
    qubits: int,
    prefix_rank: int,
    prefix_mass: float,
    cutoff_multiplicity: int,
    cutoff_log_probability: float,
) -> float:
    """Mass of the largest ``2**qubits`` coefficients at a type boundary."""

    rank_budget = 1 << qubits
    if rank_budget <= prefix_rank:
        return prefix_mass
    selected = min(rank_budget - prefix_rank, cutoff_multiplicity)
    partial_mass = math.exp(_log_integer(selected) + cutoff_log_probability)
    return min(1.0, prefix_mass + partial_mass)


def optimal_pure_state_communication(
    schmidt_probability: float,
    copies: int,
    *,
    allowed_infidelity: float,
) -> OperationalRateRecord:
    """Return the exact integer qubit cost at the declared target fidelity.

    The Schmidt probabilities of ``n`` copies are grouped by Hamming type.
    Degeneracies are generated recursively as exact Python integers, so the
    calculation never enumerates ``2**n`` basis strings and never underflows
    individual Schmidt probabilities.
    """

    probability = float(schmidt_probability)
    if not 0.0 < probability < 1.0:
        raise ValueError("schmidt_probability must lie strictly between 0 and 1")
    if copies < 1:
        raise ValueError("copies must be positive")
    if not 0.0 < allowed_infidelity < 1.0:
        raise ValueError("allowed_infidelity must lie strictly between 0 and 1")

    target_fidelity = 1.0 - float(allowed_infidelity)
    entropy = binary_entropy(probability)

    if probability == 0.5:
        qubits = max(0, min(copies, math.ceil(copies + math.log2(target_fidelity))))
        achievable = math.exp2(qubits - copies)
        converse = 0.0 if qubits == 0 else math.exp2(qubits - 1 - copies)
        return OperationalRateRecord(
            schmidt_probability=probability,
            copies=copies,
            allowed_infidelity=allowed_infidelity,
            entropy_rate=entropy,
            optimal_transmitted_qubits=qubits,
            optimal_rate=qubits / copies,
            rate_minus_entropy=qubits / copies - entropy,
            achievable_fidelity=achievable,
            converse_fidelity_with_one_fewer_qubit=converse,
            cutoff_type=0,
        )

    ascending = probability < 0.5
    count = 0 if ascending else copies
    multiplicity = 1
    prefix_rank = 0
    prefix_mass = 0.0
    log_p = math.log(probability)
    log_q = math.log1p(-probability)

    while True:
        log_sequence_probability = count * log_p + (copies - count) * log_q
        log_multiplicity = (
            gammaln(copies + 1.0)
            - gammaln(count + 1.0)
            - gammaln(copies - count + 1.0)
        )
        type_mass = math.exp(log_multiplicity + log_sequence_probability)
        if prefix_mass + type_mass >= target_fidelity - 2.0e-15:
            break

        prefix_mass = math.fsum((prefix_mass, type_mass))
        prefix_rank += multiplicity
        if ascending:
            if count == copies:
                raise RuntimeError("failed to reach target fidelity")
            multiplicity = multiplicity * (copies - count) // (count + 1)
            count += 1
        else:
            if count == 0:
                raise RuntimeError("failed to reach target fidelity")
            multiplicity = multiplicity * count // (copies - count + 1)
            count -= 1

    remaining_mass = max(target_fidelity - prefix_mass, 0.0)
    log_needed_rank = math.log(remaining_mass) - log_sequence_probability
    log_total_rank = _logaddexp(_log_integer(prefix_rank), log_needed_rank)
    qubits = max(0, min(copies, math.ceil(log_total_rank / math.log(2.0))))

    def fidelity(candidate_qubits: int) -> float:
        return _candidate_fidelity(
            qubits=candidate_qubits,
            prefix_rank=prefix_rank,
            prefix_mass=prefix_mass,
            cutoff_multiplicity=multiplicity,
            cutoff_log_probability=log_sequence_probability,
        )

    while qubits < copies and fidelity(qubits) < target_fidelity - 2.0e-13:
        qubits += 1
    while qubits > 0 and fidelity(qubits - 1) >= target_fidelity - 2.0e-13:
        qubits -= 1

    achievable = fidelity(qubits)
    converse = 0.0 if qubits == 0 else fidelity(qubits - 1)
    return OperationalRateRecord(
        schmidt_probability=probability,
        copies=copies,
        allowed_infidelity=allowed_infidelity,
        entropy_rate=entropy,
        optimal_transmitted_qubits=qubits,
        optimal_rate=qubits / copies,
        rate_minus_entropy=qubits / copies - entropy,
        achievable_fidelity=achievable,
        converse_fidelity_with_one_fewer_qubit=converse,
        cutoff_type=count,
    )


def check_operational_rate_records(
    records: list[OperationalRateRecord],
) -> dict[str, object]:
    """Check finite-block optimality and asymptotic convergence by spectrum."""

    if not records:
        raise ValueError("records must not be empty")
    grouped: dict[float, list[OperationalRateRecord]] = {}
    for record in records:
        grouped.setdefault(record.schmidt_probability, []).append(record)

    spectra: dict[str, object] = {}
    all_optimal = True
    all_errors_vanish = True
    all_rates_converge = True
    for probability, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda item: item.copies)
        final = ordered[-1]
        target = 1.0 - final.allowed_infidelity
        finite_block_optimal = bool(
            final.achievable_fidelity >= target - 2.0e-12
            and final.converse_fidelity_with_one_fewer_qubit < target + 2.0e-12
        )
        error_vanishes = final.allowed_infidelity < ordered[0].allowed_infidelity
        rate_converges = abs(final.rate_minus_entropy) <= 0.03
        all_optimal &= finite_block_optimal
        all_errors_vanish &= error_vanishes
        all_rates_converge &= rate_converges
        spectra[f"p={probability:g}"] = {
            "finite_block_optimality": finite_block_optimal,
            "initial_copies": ordered[0].copies,
            "final_copies": final.copies,
            "final_allowed_infidelity": final.allowed_infidelity,
            "final_entropy_rate": final.entropy_rate,
            "final_optimal_rate": final.optimal_rate,
            "final_rate_minus_entropy": final.rate_minus_entropy,
            "final_achievable_fidelity": final.achievable_fidelity,
            "final_converse_fidelity_with_one_fewer_qubit": (
                final.converse_fidelity_with_one_fewer_qubit
            ),
        }

    passed = bool(all_optimal and all_errors_vanish and all_rates_converge)
    return {
        "passed": passed,
        "finite_block_achievability_and_converse_passed": all_optimal,
        "allowed_infidelity_vanishes": all_errors_vanish,
        "rate_converges_to_schmidt_entropy": all_rates_converge,
        "spectra": spectra,
        "proof_boundary": (
            "The executable certificate covers pure-state preparation by "
            "one-way quantum transmission from an initially unentangled cut."
        ),
    }
