"""Implementation closure for targets blocked on unpublished paper inputs.

This module proves that every fixed-denominator item has a strict executable
input boundary.  It does not invent an MQDT basis, a QLDPC code/decoder, or a
toggle schedule, and therefore emits blocker artifacts rather than scientific
results when those packages are absent.
"""

from __future__ import annotations

from typing import Any, Callable

from external_input_models import (
    css_monte_carlo_campaign,
    dynamic_polarizability_sweep,
    toggled_hamiltonian_evolution,
)


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "T018": dynamic_polarizability_sweep,
    "T020": css_monte_carlo_campaign,
    "T021": css_monte_carlo_campaign,
    "T022": css_monte_carlo_campaign,
    "T023": css_monte_carlo_campaign,
    "T024": css_monte_carlo_campaign,
    "T027": toggled_hamiltonian_evolution,
}


def build_blocked_artifacts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate the frozen target map and return one honest blocker per target."""

    closure = config.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ValueError("implementation_closure must be an object")
    target_items = closure.get("target_items")
    if not isinstance(target_items, dict) or not target_items:
        raise ValueError("implementation_closure.target_items must be non-empty")
    flattened = [item for items in target_items.values() for item in items]
    if not all(isinstance(item, str) and item for item in flattened):
        raise ValueError("target item ids must be non-empty strings")
    if len(flattened) != len(set(flattened)):
        raise ValueError("each fixed-denominator item must map exactly once")
    if set(target_items) != set(HANDLERS):
        raise ValueError("target map and executable handler map differ")

    contracts = {
        str(row.get("target_id")): row
        for row in config.get("contracts", [])
        if isinstance(row, dict)
    }
    results: dict[str, dict[str, Any]] = {}
    for target_id, item_ids in target_items.items():
        contract = contracts.get(target_id)
        if not isinstance(contract, dict):
            raise ValueError(f"missing input contract for {target_id}")
        required_fields = contract.get("required_fields")
        if (
            contract.get("status") != "runner_ready_input_blocked"
            or not isinstance(required_fields, list)
            or not required_fields
            or not all(isinstance(field, str) and field for field in required_fields)
        ):
            raise ValueError(f"invalid strict input contract for {target_id}")
        results[target_id] = {
            "schema_version": 1,
            "target_id": target_id,
            "item_ids": item_ids,
            "status": "blocked_on_paper_input",
            "scientific_promotion": False,
            "model": contract["model"],
            "implementation": contract["implementation"],
            "required_input_schema": required_fields,
            "runner_entrypoint": [
                "python",
                "scripts/run_external_input_target.py",
                "--target",
                target_id,
                "--input",
                "<reviewed-input-package.json>",
                "--output",
                f"outputs/data/external_inputs/{target_id}.json",
            ],
            "checks": {
                "handler_declared": callable(HANDLERS[target_id]),
                "schema_nonempty": True,
                "no_guessed_values": True,
            },
            "remaining_boundary": (
                "A complete publication-specific scientific input package is "
                "required before the numerical handler may execute."
            ),
        }
    return results
