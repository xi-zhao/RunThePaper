"""Case-local boundary audits for unresolved DQC1 claims."""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np

from .model import (
    analytic_typical_discord,
    dqc1_state,
    haar_unitary,
    negativity,
    realignment_trace_norm,
)
from .symmetric_extension import first_ppt_symmetric_extension


def discord_signature_boundary(parameters: dict[str, Any]) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Reproduce the paper's ``first signature`` scientific conjunction.

    In the paper, ``first signature`` does not assert historical priority or
    an unstated asymptotic protocol.  It denotes positive discord in the
    ``alpha <= 1/2`` regime where the named entanglement tests do not detect
    entanglement.  We check that conjunction on a frozen independent campaign.
    """

    seed = int(parameters["seed_partitions"])
    partition_qubits = [int(value) for value in parameters["partition_qubits"]]
    partition_instances = int(parameters["partition_instances"])
    alpha_values = [float(value) for value in parameters["alpha_values"]]
    alpha_cutoff = float(parameters["alpha_cutoff"])
    rng = np.random.default_rng(seed)

    by_alpha: dict[float, dict[str, object]] = {
        alpha: {
            "alpha": alpha,
            "analytic_discord": float(analytic_typical_discord(alpha)),
            "discord_positive": bool(analytic_typical_discord(alpha) > 0.0),
            "witness_rows": 0,
            "max_negativity": 0.0,
            "max_realignment_trace_norm": 0.0,
        }
        for alpha in alpha_values
        if alpha <= alpha_cutoff
    }

    for qubits in partition_qubits:
        dimensions = (2,) * (qubits + 1)
        register_subsystems = tuple(range(1, qubits + 1))
        groups = [
            (0,) + selected
            for count in range(qubits)
            for selected in itertools.combinations(register_subsystems, count)
        ]
        for _ in range(partition_instances):
            unitary = haar_unitary(2**qubits, rng)
            for alpha, group in itertools.product(by_alpha, groups):
                state = dqc1_state(unitary, alpha)
                negativity_value = negativity(state, dimensions, group)
                realignment_value = realignment_trace_norm(state, dimensions, group)
                row = by_alpha[alpha]
                row["witness_rows"] = int(row["witness_rows"]) + 1
                row["max_negativity"] = max(float(row["max_negativity"]), negativity_value)
                row["max_realignment_trace_norm"] = max(
                    float(row["max_realignment_trace_norm"]),
                    realignment_value,
                )

    rows: list[dict[str, object]] = []
    for alpha in sorted(by_alpha):
        row = by_alpha[alpha]
        row["all_grouped_witnesses_non_detecting"] = bool(
            float(row["max_negativity"]) <= 1.0e-12
            and float(row["max_realignment_trace_norm"]) <= 1.0
        )
        rows.append(row)

    extension_rows: list[dict[str, object]] = []
    extension_spec = parameters.get("symmetric_extension")
    if isinstance(extension_spec, dict) and extension_spec.get("enabled") is True:
        extension_rng = np.random.default_rng(int(extension_spec["seed"]))
        solver = str(extension_spec["solver"])
        for qubits in [int(value) for value in extension_spec["partition_qubits"]]:
            dimensions = (2,) * (qubits + 1)
            register_subsystems = tuple(range(1, qubits + 1))
            groups = [
                (0,) + selected
                for count in range(qubits)
                for selected in itertools.combinations(register_subsystems, count)
            ]
            for instance in range(int(extension_spec["instances"])):
                unitary = haar_unitary(2**qubits, extension_rng)
                for alpha, group in itertools.product(
                    [float(value) for value in extension_spec["alpha_values"]],
                    groups,
                ):
                    state = dqc1_state(unitary, alpha)
                    result = first_ppt_symmetric_extension(
                        state,
                        dimensions,
                        group,
                        solver=solver,
                        tolerance=float(extension_spec["acceptance_tolerance"]),
                        solver_epsilon=float(extension_spec["solver_epsilon"]),
                        max_iterations=int(extension_spec["max_iterations"]),
                    )
                    extension_rows.append(
                        {
                            "qubits": qubits,
                            "instance": instance,
                            "alpha": alpha,
                            "partition": ",".join(str(value) for value in group),
                            **result,
                        }
                    )

    extension_attempted = bool(extension_rows)
    all_extensions_non_detecting = bool(
        extension_rows
        and all(
            bool(row["feasible"]) and bool(row["certificate_passed"])
            for row in extension_rows
        )
    )

    summary = {
        "schema_version": 1,
        "paper_id": "0709.0548",
        "claim_scope": (
            "DQC1 evidence for alpha <= cutoff: positive discord together with "
            "non-detecting grouped PPT, realignment, and first-level PPT "
            "symmetric-extension tests."
        ),
        "paper_claim_interpretation": (
            "The paper's phrase 'first signature' identifies discord as the "
            "nonclassical-correlation signature in the alpha<=1/2 regime where "
            "the named entanglement tests are non-detecting; it is not a claim "
            "about historical priority or an unstated asymptotic protocol."
        ),
        "alpha_cutoff": alpha_cutoff,
        "partition_qubits": partition_qubits,
        "partition_instances": partition_instances,
        "rows": rows,
        "all_rows_support_finite_boundary": all(
            bool(row["discord_positive"]) and bool(row["all_grouped_witnesses_non_detecting"])
            for row in rows
        ),
        "maximum_negativity": max(float(row["max_negativity"]) for row in rows),
        "maximum_realignment_trace_norm": max(
            float(row["max_realignment_trace_norm"]) for row in rows
        ),
        "symmetric_extension_attempted": extension_attempted,
        "symmetric_extension_rows": extension_rows,
        "all_symmetric_extensions_non_detecting": all_extensions_non_detecting,
        "paper_claim_supported": bool(
            all(
                bool(row["discord_positive"])
                and bool(row["all_grouped_witnesses_non_detecting"])
                for row in rows
            )
            and all_extensions_non_detecting
        ),
    }
    return rows, summary


def literature_claim_contract_audit(parameters: dict[str, Any]) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Audit whether cited literature claims are fully specified inside this paper."""

    rows: list[dict[str, object]] = []
    for claim in parameters["claims"]:
        required = [str(value) for value in claim["required_contract_fields"]]
        provided = [str(value) for value in claim["provided_contract_fields"]]
        missing = [field for field in required if field not in provided]
        rows.append(
            {
                "claim_id": str(claim["claim_id"]),
                "source_ref": str(claim["source_ref"]),
                "required_field_count": len(required),
                "provided_field_count": len(provided),
                "missing_field_count": len(missing),
                "internally_specified": not missing,
                "missing_fields": ";".join(missing),
                "root_cause": (
                    "publication_underspecified" if missing else "not_applicable"
                ),
            }
        )

    summary = {
        "schema_version": 1,
        "paper_id": "0709.0548",
        "claim_scope": "Externally cited complexity, speedup, and measure claims.",
        "claims_total": len(rows),
        "internally_specified_claims": sum(
            1 for row in rows if bool(row["internally_specified"])
        ),
        "publication_underspecified_claims": sum(
            1 for row in rows if not bool(row["internally_specified"])
        ),
        "claims": rows,
    }
    return rows, summary
