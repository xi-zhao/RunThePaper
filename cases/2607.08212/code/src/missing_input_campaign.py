"""Executable implementation contracts for the unpublished Fig. 3/9 inputs."""

from __future__ import annotations

from typing import Any, Callable

from paper_input_models import (
    build_zx_backend_request,
    compile_three_sat_package,
    required_schema,
)


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "FIG3A_ZAP": compile_three_sat_package,
    "FIG3C_NATIVE": compile_three_sat_package,
    "ZX_EXTRACTOR_INPUT_GAP": build_zx_backend_request,
}


def build_blocked_artifacts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    closure = config.get("implementation_closure")
    if not isinstance(closure, dict):
        raise ValueError("implementation_closure must be an object")
    target_items = closure.get("target_items")
    if not isinstance(target_items, dict) or set(target_items) != set(HANDLERS):
        raise ValueError("target_items and executable handlers must match")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != 4 or len(flattened) != len(set(flattened)):
        raise ValueError("the four fixed-denominator items must each map exactly once")
    results = {}
    for target_id, item_ids in target_items.items():
        results[target_id] = {
            "schema_version": 1,
            "target_id": target_id,
            "item_ids": item_ids,
            "status": "blocked_on_paper_input",
            "scientific_promotion": False,
            "required_input_schema": required_schema(target_id),
            "implementation": f"src/paper_input_models.py#{HANDLERS[target_id].__name__}",
            "runner_entrypoint": [
                "python",
                "scripts/run_paper_input_target.py",
                "--target",
                target_id,
                "--input",
                "<reviewed-paper-input-package.json>",
                "--output",
                f"outputs/data/paper_inputs/{target_id}.json",
            ],
            "checks": {
                "handler_declared": callable(HANDLERS[target_id]),
                "schema_nonempty": bool(required_schema(target_id)),
                "no_guessed_values": True,
            },
            "remaining_boundary": (
                "A complete citable source-instance package is required before the target may produce "
                "paper-specific scientific data."
            ),
        }
    return results
