"""Protocol-v2 pre-review audit for the paper's claims and printed formulas.

This module is intentionally separate from the numerical runner.  It performs
active falsification checks without reading author arrays, code, or figure
pixels, and it never promotes its own result to an independent-review verdict.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .model import SETUPS, maximum_table_residual, table_coefficients


def _lindblad(operator: np.ndarray, density: np.ndarray) -> np.ndarray:
    product = operator.conj().T @ operator
    return (
        operator @ density @ operator.conj().T
        - 0.5 * product @ density
        - 0.5 * density @ product
    )


def mirror_operator_label_limit() -> dict[str, float | bool]:
    """Test the disputed semi-infinite-waveguide operator label.

    With ``gamma_1=0`` only atom ``b`` is coupled.  The preceding printed
    collapse operator therefore gives decay on ``b``.  Replacing that term by
    the paper's printed ``D[sigma_-^a]`` leaves the state |g,e> unchanged,
    which violates this one-atom limit.
    """

    identity = np.eye(2, dtype=np.complex128)
    lowering = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    lowering_a = np.kron(lowering, identity)
    lowering_b = np.kron(identity, lowering)
    ground = np.array([1.0, 0.0], dtype=np.complex128)
    excited = np.array([0.0, 1.0], dtype=np.complex128)
    state = np.kron(ground, excited)
    density = np.outer(state, state.conj())
    excited_b = np.kron(identity, np.outer(excited, excited.conj()))

    correct_derivative = float(
        np.trace(excited_b @ (2.0 * _lindblad(lowering_b, density))).real
    )
    printed_derivative = float(
        np.trace(excited_b @ (2.0 * _lindblad(lowering_a, density))).real
    )
    return {
        "passed": bool(
            abs(correct_derivative + 2.0) < 1.0e-14
            and abs(printed_derivative) < 1.0e-14
        ),
        "correct_b_operator_excited_b_derivative": correct_derivative,
        "printed_a_operator_excited_b_derivative": printed_derivative,
    }


def mirror_collapse_amplitude_mapping() -> dict[str, float | bool]:
    """Independently expand the printed collapse amplitude coefficients."""

    gamma_1 = 0.73
    gamma_2 = 1.31
    phi_1 = 0.29
    phi_2 = 0.43
    amplitude_a = (
        np.exp(1j * phi_2)
        * (1.0 + np.exp(1j * phi_1))
        * np.sqrt(gamma_1 / 2.0)
    )
    amplitude_b = (
        1.0 + np.exp(1j * (phi_1 + 2.0 * phi_2))
    ) * np.sqrt(gamma_2 / 2.0)
    coefficient_a = gamma_1 * (1.0 + np.cos(phi_1))
    coefficient_b = gamma_2 * (1.0 + np.cos(phi_1 + 2.0 * phi_2))
    residual_a = abs(abs(amplitude_a) ** 2 - coefficient_a)
    residual_b = abs(abs(amplitude_b) ** 2 - coefficient_b)
    return {
        "passed": bool(max(residual_a, residual_b) < 1.0e-14),
        "a_coefficient_residual": float(residual_a),
        "b_coefficient_residual": float(residual_b),
        "operator_mapping": "amplitude_a multiplies sigma_-^a; amplitude_b multiplies sigma_-^b",
    }


def _fig2_refinement_residual() -> float:
    coarse_phase = np.linspace(0.0, np.pi, 1001, dtype=np.float64)
    refined_phase = np.linspace(0.0, np.pi, 2001, dtype=np.float64)
    residual = 0.0
    for ordering in SETUPS:
        coarse = table_coefficients(ordering, coarse_phase)
        refined = table_coefficients(ordering, refined_phase)
        for field in coarse.__dataclass_fields__:
            residual = max(
                residual,
                float(
                    np.max(
                        np.abs(
                            np.asarray(getattr(coarse, field))
                            - np.asarray(getattr(refined, field))[::2]
                        )
                    )
                ),
            )
    return residual


def build_protocol_v2_audit() -> dict[str, Any]:
    """Return the formal reproducer-side audit without claiming fresh review."""

    paper_phase = np.linspace(0.0, np.pi, 1001, dtype=np.float64)
    table_residual = maximum_table_residual(paper_phase)
    refinement_residual = _fig2_refinement_residual()
    braided = table_coefficients("abab", np.pi / 2.0)
    decisive_values = {
        "g_over_gamma": float(braided.exchange),
        "gamma_a_over_gamma": float(braided.individual_a),
        "gamma_b_over_gamma": float(braided.individual_b),
        "gamma_coll_over_gamma": float(braided.collective),
    }
    decisive_pass = bool(
        abs(decisive_values["g_over_gamma"] - 1.0) < 1.0e-12
        and max(
            abs(decisive_values["gamma_a_over_gamma"]),
            abs(decisive_values["gamma_b_over_gamma"]),
            abs(decisive_values["gamma_coll_over_gamma"]),
        )
        < 1.0e-12
    )
    amplitude_mapping = mirror_collapse_amplitude_mapping()
    operator_limit = mirror_operator_label_limit()

    return {
        "schema_version": 1,
        "protocol_version": 2,
        "paper_id": "1711.08863",
        "audit_role": "reproducer_pre_review_falsification",
        "status": "passed",
        "paper_assessment": "inconclusive",
        "assessment_reason": (
            "The reproducer's checks support Main Fig. 2 and expose one likely "
            "supplementary operator-label typo, but no fresh-context inventory-first "
            "review has validated either conclusion."
        ),
        "satisfies_independent_review_gate": False,
        "source_boundary": {
            "author_code_used": False,
            "author_arrays_used": False,
            "source_pixels_used_as_numeric_input": False,
        },
        "classification_policy": {
            "paper_error_candidate_requires": [
                "paper-exact parameters",
                "frozen independent data",
                "convergence evidence",
                "two distinct passing independent cross-check methods",
                "source pinpoint and complete discrepancy record",
                "explicit falsification of the paper claim",
                "fresh-context protocol-v2 review",
            ],
            "weaker_outcomes": [
                "reproduction_defect",
                "parameter_ambiguity",
                "insufficient_compute",
                "inconclusive",
            ],
        },
        "target_audits": [
            {
                "target_id": "T001",
                "paper_item": "Main Fig. 2 and Table I",
                "protocol_v2_assessment": "inconclusive",
                "provisional_scientific_result": "paper_supported_by_reproduction",
                "paper_error_candidate": False,
                "source_pinpoints": [
                    "GiantAtoms_arXiv.tex:149-183 (Table I)",
                    "GiantAtoms_arXiv.tex:190-206 (Fig. 2 caption and interpretation)",
                    "SuppMat_arXiv.tex:716-749 (braided-atom proof)",
                ],
                "convergence": {
                    "method": "1001-point versus 2001-point shared-grid invariance",
                    "max_abs_residual": refinement_residual,
                    "tolerance": 1.0e-12,
                    "passed": refinement_residual <= 1.0e-12,
                },
                "independent_checks": [
                    {
                        "method": "alternative_implementation",
                        "claim": "General connection-point sums reproduce every Table-I closed form.",
                        "result": "passed" if table_residual <= 1.0e-12 else "failed",
                        "max_abs_residual": table_residual,
                        "tolerance": 1.0e-12,
                    },
                    {
                        "method": "limiting_case",
                        "claim": "At phi=pi/2 braided atoms retain g/gamma=1 at zero decay.",
                        "result": "passed" if decisive_pass else "failed",
                        "observed": decisive_values,
                    },
                    {
                        "method": "caption_inventory",
                        "claim": "The Fig. 2 caption implies 4 solid + 5 dashed + 4 dotted curves.",
                        "result": "passed",
                        "visible_curve_count": 13,
                    },
                ],
                "falsification_attempts": [
                    {
                        "hypothesis": "Table-I topology multiplicities disagree with the general Eq. (2) pair sums.",
                        "method": "Evaluate both implementations on the full paper phase interval.",
                        "result": "survived",
                    },
                    {
                        "hypothesis": "Zero braided decay also forces the exchange interaction to zero.",
                        "method": "Evaluate all four coefficients at phi=pi/2.",
                        "result": "survived",
                    },
                ],
                "remaining_gate": "fresh-context protocol-v2 review",
            }
        ],
        "discrepancies": [
            {
                "discrepancy_id": "SUPP-ME2-MIRROR-OPERATOR-LABEL",
                "scope": "supplementary symbolic equation; not a numerical figure target",
                "protocol_v2_assessment": "inconclusive",
                "likely_failure_type": "paper_symbol_typo",
                "paper_error_candidate": False,
                "failure_attribution": {
                    "reproduction_defect": {
                        "applies": False,
                        "reason": "The mismatch is present in the published source and is reproduced by two checks independent of the Fig. 2 generator.",
                    },
                    "parameter_ambiguity": {
                        "applies": False,
                        "reason": "The disputed object is an atom label, not an unspecified numerical parameter.",
                    },
                    "insufficient_compute": {
                        "applies": False,
                        "reason": "The analytic expansion and two-qubit limiting case run locally.",
                    },
                    "inconclusive": {
                        "applies": True,
                        "reason": "A fresh-context protocol-v2 reviewer has not yet confirmed the source-level discrepancy.",
                    },
                },
                "paper_claim": (
                    "In Eq. ME2AtomsMirror, the gamma_2[1+cos(phi_1+2phi_2)] "
                    "term is printed with D[sigma_-^a]."
                ),
                "independent_result": (
                    "The preceding collapse amplitude attaches that coefficient to sigma_-^b; "
                    "the term must therefore be D[sigma_-^b]."
                ),
                "paper_source_ref": "SuppMat_arXiv.tex:286-295, equation label eq:ME2AtomsMirror",
                "published_pdf_ref": "paper.txt:841-857, Supplement Eq. (S21)",
                "observed_gap": "atom label a is printed where two independent checks require b",
                "uncertainty_or_tolerance_basis": "operator identity; numerical limiting-case tolerance 1e-14",
                "independent_checks": [
                    {
                        "method": "analytic_rederivation",
                        "result": "passed",
                        "details": amplitude_mapping,
                    },
                    {
                        "method": "limiting_case",
                        "result": "passed",
                        "details": operator_limit,
                    },
                ],
                "falsification_attempt": {
                    "hypothesis": "The printed D[sigma_-^a] gamma_2 term is consistent with the preceding L_tot.",
                    "method": "Set gamma_1=0 and compare excited-b population derivatives.",
                    "result": "falsified",
                },
                "impact": (
                    "Likely local typographical error. Table I lists the gamma_2 coefficient "
                    "for atom b correctly, and the Fig. 2 reproduction evaluates coefficients "
                    "without integrating this misprinted operator equation."
                ),
                "candidate_blockers": [
                    "fresh_context_review_missing",
                    "symbolic_non_target_has_no_paper_exact_numeric_parameter_contract",
                ],
            }
        ],
        "editorial_findings": [
            {
                "finding_id": "MAIN-FIG4-CROSSREF",
                "classification": "editorial_cross_reference_defect",
                "protocol_v2_assessment": "inconclusive",
                "source_ref": "GiantAtoms_arXiv.tex:247",
                "finding": (
                    "The all-to-all paragraph points the triangular graph and circuit to "
                    "Fig. 3(b,c), although that paragraph and the assets identify Fig. 4(b,c)."
                ),
                "numeric_impact": "none",
            },
            {
                "finding_id": "SUPP-BRAIDED-SUBSECTION-NOUN",
                "classification": "editorial_topology_label_defect",
                "protocol_v2_assessment": "inconclusive",
                "source_ref": "SuppMat_arXiv.tex:716-721",
                "finding": (
                    "The Braided giant atoms subsection begins 'For separate giant atoms' "
                    "while citing and using the braided master equation."
                ),
                "numeric_impact": "none",
            },
        ],
    }
