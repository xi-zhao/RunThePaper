#!/usr/bin/env python3
"""Audit the Supplement Fig. S2 mismatch without using figure pixels.

The check keeps three questions separate:

1. does the finite-ring result converge;
2. does the case Hamiltonian implement the literal printed operator;
3. are the printed Hamiltonian and printed TDVP flow mutually consistent under
   the paper's stated ``S^z+s`` occupation convention.

It reads only the frozen numerical archive and publication text.  Original
figure pixels are not scientific inputs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from scar_tdvp.constrained import constrained_states, full_hamiltonian
from scar_tdvp.tdvp import VariationalManifold, deformed_flow, tdvp_flow


WORKSPACE = Path(__file__).resolve().parents[1]
CASE_ROOT = WORKSPACE.parent
SOURCE = (
    CASE_ROOT
    / "paper-source/Quantum_ManybodyScar_Supplemental_Info_Resubmit_v4.tex"
)
DATA = WORKSPACE / "outputs/data/T_FIGS2.npz"
OUTPUT = WORKSPACE / "outputs/checks/figs2_discrepancy_audit.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _literal_printed_hamiltonian(length: int, deformation: float) -> np.ndarray:
    """Build Supplement Eq. (V) directly in the constrained product basis."""

    states = constrained_states(length, 1)
    index = {state: position for position, state in enumerate(states)}
    matrix = np.zeros((len(states), len(states)), dtype=float)
    for column, state in enumerate(states):
        for site, occupation in enumerate(state):
            if state[(site - 1) % length] or state[(site + 1) % length]:
                continue
            # The paper defines |n> as an eigenstate of S^z+s, hence for
            # s=1/2: S^z=n-1/2.  The printed perturbation carries a plus sign.
            coefficient = 1.0 + deformation * (
                state[(site - 2) % length]
                + state[(site + 2) % length]
                - 1.0
            )
            target = list(state)
            target[site] = 1 - occupation
            matrix[index[tuple(target)], column] += 0.5 * coefficient
    return 0.5 * (matrix + matrix.T)


def main() -> None:
    source_lines = SOURCE.read_text(encoding="utf-8").splitlines()
    source_checks = {
        "occupation_convention": "S^z_1" in source_lines[937]
        and "-\\frac{1}{2}" in source_lines[937],
        "printed_hamiltonian_plus_sign": "H = \\Omega" in source_lines[963]
        and "+ h" in source_lines[963],
        "printed_flow_plus_sign": "+ h" in source_lines[985]
        and "+ h" in source_lines[987],
        "fluctuation_definition": "\\gamma^2" in source_lines[999],
        "printed_minimum_claim": "0.045" in source_lines[1001],
    }

    deformation = 0.05
    states = constrained_states(8, 1)
    literal = _literal_printed_hamiltonian(8, deformation)
    implementation_literal = full_hamiltonian(
        states, 1, deformation=-deformation
    ).toarray()
    literal_operator_max_abs = float(
        np.max(np.abs(literal - implementation_literal))
    )

    manifold = VariationalManifold(12, 0.5)
    angle_pairs = [(-2.0, 1.0), (-1.4, 0.8), (0.3, -1.7)]
    literal_to_plus_flow = []
    literal_to_minus_flow = []
    implemented_to_plus_flow = []
    for even, odd in angle_pairs:
        literal_velocity = manifold.projected_velocity(
            even, odd, deformation=-deformation
        )
        implemented_velocity = manifold.projected_velocity(
            even, odd, deformation=deformation
        )
        plus_flow = np.asarray(
            [
                deformed_flow(even, odd, deformation),
                deformed_flow(odd, even, deformation),
            ]
        )
        minus_flow = np.asarray(
            [
                deformed_flow(even, odd, -deformation),
                deformed_flow(odd, even, -deformation),
            ]
        )
        literal_to_plus_flow.append(
            float(np.max(np.abs(literal_velocity - plus_flow)))
        )
        literal_to_minus_flow.append(
            float(np.max(np.abs(literal_velocity - minus_flow)))
        )
        implemented_to_plus_flow.append(
            float(np.max(np.abs(implemented_velocity - plus_flow)))
        )

    h0_grid = np.linspace(-2.0, 2.0, 41)
    h0_reduction_max_abs = float(
        np.max(
            np.abs(
                deformed_flow(h0_grid, h0_grid[::-1], 0.0)
                - tdvp_flow(h0_grid, h0_grid[::-1], 0.5)
            )
        )
    )

    with np.load(DATA) as archive:
        h_values = np.asarray(archive["h_over_omega"], dtype=float)
        ring_lengths = np.asarray(archive["ring_lengths"], dtype=int)
        errors = np.asarray(archive["integrated_error"], dtype=float)
        fluctuations = np.asarray(
            archive["integrated_fluctuation"], dtype=float
        )
    convergence_max_abs = float(
        max(
            np.max(np.abs(errors[-1] - errors[-2])),
            np.max(np.abs(fluctuations[-1] - fluctuations[-2])),
        )
    )
    error_minimum_h = float(h_values[int(np.argmin(errors[-1]))])
    fluctuation_minimum_h = float(
        h_values[int(np.argmin(fluctuations[-1]))]
    )

    checks = [
        {
            "kind": "independent_implementation",
            "result": "passed" if literal_operator_max_abs < 1e-12 else "failed",
            "statement": (
                "A direct product-basis implementation of the printed "
                "Hamiltonian equals the case implementation evaluated with "
                "the publication-literal sign."
            ),
            "value": literal_operator_max_abs,
            "threshold": 1e-12,
        },
        {
            "kind": "exact_rederivation",
            "result": (
                "passed"
                if max(literal_to_minus_flow) < 1e-3
                and min(literal_to_plus_flow) > 1e-2
                and max(implemented_to_plus_flow) < 1e-3
                else "failed"
            ),
            "statement": (
                "Under the paper's S^z+s occupation convention, the literal "
                "+h Hamiltonian projects to the -h flow, while the printed +h "
                "flow projects from the opposite Hamiltonian sign."
            ),
            "literal_to_printed_plus_flow_max_abs": literal_to_plus_flow,
            "literal_to_opposite_flow_max_abs": literal_to_minus_flow,
            "implemented_to_printed_plus_flow_max_abs": implemented_to_plus_flow,
        },
        {
            "kind": "invariant",
            "result": "passed" if h0_reduction_max_abs < 1e-12 else "failed",
            "statement": "The deformed flow reduces to the undeformed s=1/2 TDVP flow at h=0.",
            "value": h0_reduction_max_abs,
            "threshold": 1e-12,
        },
        {
            "kind": "convergence",
            "result": "passed" if convergence_max_abs < 1e-6 else "failed",
            "statement": "The independently generated S2 arrays converge from the last two finite rings.",
            "value": convergence_max_abs,
            "threshold": 1e-6,
        },
        {
            "kind": "source_trace",
            "result": "passed" if all(source_checks.values()) else "failed",
            "statement": "The publication source pins the occupation convention, +h Hamiltonian, +h flow, gamma-squared integral, and h/Omega approximately 0.045 claim.",
            "source_checks": source_checks,
        },
    ]
    payload = {
        "schema_version": 1,
        "paper_id": "1807.01815",
        "targets": ["T_FIGS2A", "T_FIGS2B"],
        "scientific_input_boundary": {
            "author_code_used": False,
            "author_arrays_used": False,
            "source_pixels_used": False,
            "inputs": [
                "paper-source/Quantum_ManybodyScar_Supplemental_Info_Resubmit_v4.tex",
                "outputs/data/T_FIGS2.npz",
                "src/scar_tdvp/constrained.py",
                "src/scar_tdvp/tdvp.py",
            ],
        },
        "input_hashes": {
            "source": _sha256(SOURCE),
            "generated_data": _sha256(DATA),
        },
        "observed_result": {
            "ring_lengths": ring_lengths.tolist(),
            "convergence_max_abs": convergence_max_abs,
            "generated_error_minimum_h_over_omega": error_minimum_h,
            "generated_fluctuation_minimum_h_over_omega": fluctuation_minimum_h,
            "paper_fluctuation_minimum_h_over_omega": 0.045,
            "paper_claim_reproduced": abs(fluctuation_minimum_h - 0.045) <= 0.011,
        },
        "checks": checks,
        "code_fault_assessment": {
            "status": (
                "not_found_after_checks"
                if all(check["result"] == "passed" for check in checks)
                else "not_excluded"
            ),
            "statement": (
                "Independent operator construction, exact sign rederivation, "
                "h=0 invariant, finite-ring convergence, and source tracing "
                "found no implementation defect that explains the mismatch."
            ),
        },
        "scientific_conclusion": (
            "The generated S2 claim remains different after convergence.  The "
            "publication's literal +h Hamiltonian and printed +h TDVP flow use "
            "opposite signs under its stated occupation convention, so a fresh "
            "claim-level review must adjudicate the discrepancy; no source "
            "pixels are used to force agreement."
        ),
    }
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if not all(check["result"] == "passed" for check in checks):
        raise SystemExit("one or more S2 discrepancy checks failed")


if __name__ == "__main__":
    main()
