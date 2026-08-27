"""Caption-exact target selection for generated rheology results.

The simulation grid and the figure contract are different objects: a campaign
may generate many conditions, while a paper panel names a small exact subset.
This module is the single place that binds those two layers.
"""

from __future__ import annotations

from typing import Any


REQUIRED_TARGET_SELECTORS: dict[str, tuple[str, ...]] = {
    "T005": ("p0", "activity"),
    "T006": ("p0", "activity", "shear_rates"),
    "T007": ("p0", "activity", "shear_rates"),
    "T008": ("p0", "activity", "shear_rates"),
    "T009": ("p0", "activity", "shear_rates"),
    "T012": ("p0", "activity"),
    "T013": ("p0", "activity"),
    "T014": ("p0", "activity"),
    "T015": ("p0", "activity"),
}


def validate_target_selectors(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selectors = config.get("target_selectors")
    if not isinstance(selectors, dict):
        raise ValueError("target_selectors must be an object")
    for target_id, required_fields in REQUIRED_TARGET_SELECTORS.items():
        selector = selectors.get(target_id)
        if not isinstance(selector, dict):
            raise ValueError(f"target selector {target_id} is required")
        missing = [field for field in required_fields if field not in selector]
        if missing:
            raise ValueError(f"target selector {target_id} misses {missing}")
        float(selector["p0"])
        float(selector["activity"])
        if "shear_rates" in required_fields:
            rates = selector["shear_rates"]
            if not isinstance(rates, list) or not rates:
                raise ValueError(f"target selector {target_id} needs shear_rates")
            if any(float(rate) <= 0.0 for rate in rates):
                raise ValueError(f"target selector {target_id} rates must be positive")
    return selectors


def select_curve(
    curves: list[dict[str, Any]],
    selector: dict[str, Any],
    *,
    strict: bool,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Select the exact caption curve, with reduced-profile fallback only."""

    p0 = float(selector["p0"])
    activity = float(selector["activity"])
    exact = [
        curve
        for curve in curves
        if abs(float(curve["p0"]) - p0) <= tolerance
        and abs(float(curve["activity"]) - activity) <= tolerance
    ]
    if exact:
        return exact[0]
    if strict:
        raise ValueError(
            f"caption-exact curve is missing: p0={p0}, activity={activity}"
        )
    if not curves:
        raise ValueError("cannot select a curve from an empty campaign")
    return min(
        curves,
        key=lambda curve: abs(float(curve["p0"]) - p0)
        + abs(float(curve["activity"]) - activity),
    )


def select_condition_results(
    results: list[dict[str, Any]],
    selector: dict[str, Any],
    *,
    strict: bool,
    tolerance: float = 1e-12,
) -> list[dict[str, Any]]:
    """Select one generated condition for every caption-declared shear rate."""

    p0 = float(selector["p0"])
    activity = float(selector["activity"])
    requested = [float(value) for value in selector["shear_rates"]]
    base = [
        item
        for item in results
        if abs(float(item["condition"].p0) - p0) <= tolerance
        and abs(float(item["condition"].activity) - activity) <= tolerance
    ]
    exact: list[dict[str, Any]] = []
    for rate in requested:
        match = next(
            (
                item
                for item in base
                if abs(float(item["condition"].shear_rate) - rate) <= tolerance
            ),
            None,
        )
        if match is None:
            if strict:
                raise ValueError(
                    "caption-exact condition is missing: "
                    f"p0={p0}, activity={activity}, shear_rate={rate}"
                )
            exact = []
            break
        exact.append(match)
    if exact:
        return exact

    if not base:
        if strict:
            raise ValueError(
                f"caption condition family is missing: p0={p0}, activity={activity}"
            )
        base = sorted(
            results,
            key=lambda item: abs(float(item["condition"].p0) - p0)
            + abs(float(item["condition"].activity) - activity),
        )
        if base:
            nearest_p0 = float(base[0]["condition"].p0)
            nearest_activity = float(base[0]["condition"].activity)
            base = [
                item
                for item in base
                if abs(float(item["condition"].p0) - nearest_p0) <= tolerance
                and abs(float(item["condition"].activity) - nearest_activity)
                <= tolerance
            ]
    remaining = list(base)
    selected: list[dict[str, Any]] = []
    for rate in requested:
        if not remaining:
            break
        item = min(
            remaining,
            key=lambda row: abs(float(row["condition"].shear_rate) - rate),
        )
        selected.append(item)
        remaining.remove(item)
    return selected
