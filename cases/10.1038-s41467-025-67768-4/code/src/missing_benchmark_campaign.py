"""Strict implementation campaign for the two unpublished benchmark contracts."""

from __future__ import annotations

from typing import Any, Callable

from missing_benchmark_models import (
    lattice_surgery_zne,
    qldpc_logical_multiplicity,
    required_schema,
)


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "T008": qldpc_logical_multiplicity,
    "T009": lattice_surgery_zne,
}


def build_blocked_artifacts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    closure = config.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ValueError("implementation_closure must be an object")
    target_items = closure.get("target_items")
    if not isinstance(target_items, dict) or set(target_items) != set(HANDLERS):
        raise ValueError("target_items and executable handlers must match")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != 3 or len(flattened) != len(set(flattened)):
        raise ValueError("the three fixed-denominator panels must map exactly once")
    return {
        target_id: {
            "schema_version": 1,
            "target_id": target_id,
            "item_ids": item_ids,
            "status": "blocked_on_paper_input",
            "scientific_promotion": False,
            "required_input_schema": required_schema(target_id),
            "implementation": f"src/missing_benchmark_models.py#{HANDLERS[target_id].__name__}",
            "runner_entrypoint": [
                "python",
                "scripts/run_missing_benchmark_target.py",
                "--target",
                target_id,
                "--input",
                "<reviewed-benchmark-contract.json>",
                "--output",
                f"outputs/data/missing_benchmarks/{target_id}.json",
            ],
            "checks": {
                "handler_declared": callable(HANDLERS[target_id]),
                "schema_nonempty": bool(required_schema(target_id)),
                "no_guessed_values": True,
            },
            "remaining_boundary": (
                "A complete publication-specific circuit, decoder, fault, and sampling contract is required."
            ),
        }
        for target_id, item_ids in target_items.items()
    }
