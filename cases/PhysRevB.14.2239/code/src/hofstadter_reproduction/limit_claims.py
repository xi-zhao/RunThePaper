"""Finite rational-approximant diagnostics for the paper's limit claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np

from .model import band_edges


@dataclass(frozen=True)
class TargetResult:
    target_id: str
    status: str
    scientific_scale: str
    data: dict[str, Any]
    checks: dict[str, bool]
    boundary: dict[str, Any]

    def payload(self, item_ids: list[str]) -> dict[str, Any]:
        payload = asdict(self)
        payload["item_ids"] = item_ids
        payload["checks_passed"] = all(self.checks.values())
        return payload


def spectral_measure(p: int, q: int) -> float:
    """Lebesgue measure of the finite rational spectrum."""

    return float(sum(high - low for low, high in band_edges(p, q)))


def sampled_hausdorff_distance(
    first: tuple[tuple[float, float], ...],
    second: tuple[tuple[float, float], ...],
    *,
    samples_per_band: int,
) -> float:
    """Deterministic set-distance diagnostic between two interval unions.

    This is deliberately labelled sampled rather than used as a theorem
    oracle.  It is adequate for convergence diagnostics and cannot establish
    the topology of the irrational limit.
    """

    if samples_per_band < 2:
        raise ValueError("samples_per_band must be at least two")

    def samples(bands: tuple[tuple[float, float], ...]) -> np.ndarray:
        return np.concatenate(
            [np.linspace(low, high, samples_per_band) for low, high in bands]
        )

    def directed(points: np.ndarray, bands: tuple[tuple[float, float], ...]) -> float:
        low = np.asarray([row[0] for row in bands], dtype=float)
        high = np.asarray([row[1] for row in bands], dtype=float)
        point_matrix = points[:, None]
        distances = np.maximum(np.maximum(low - point_matrix, point_matrix - high), 0.0)
        return float(np.max(np.min(distances, axis=1)))

    return max(
        directed(samples(first), second),
        directed(samples(second), first),
    )


def run_campaign(config: dict[str, Any], profile_name: str) -> dict[str, dict[str, Any]]:
    if config.get("paper_id") != "PhysRevB.14.2239":
        raise ValueError("configuration paper_id does not match this case")
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        raise ValueError(f"unknown profile: {profile_name}")
    target_items = config.get("target_items")
    runners: dict[str, Callable[[dict[str, Any]], TargetResult]] = {
        "T008": _cantor_limit_diagnostic,
        "T009": _continuity_diagnostic,
    }
    if not isinstance(target_items, dict) or set(target_items) != set(runners):
        raise ValueError("target item map and runner map differ")
    flattened = [item for items in target_items.values() for item in items]
    if len(flattened) != len(set(flattened)):
        raise ValueError("each atomic item must map exactly once")
    profile = profiles[profile_name]
    return {
        target_id: runners[target_id](profile).payload(target_items[target_id])
        for target_id in target_items
    }


def _spectrum_row(p: int, q: int) -> dict[str, Any]:
    bands = band_edges(p, q)
    widths = np.asarray([high - low for low, high in bands], dtype=float)
    return {
        "p": p,
        "q": q,
        "alpha": p / q,
        "band_count": len(bands),
        "spectral_measure": float(np.sum(widths)),
        "maximum_band_width": float(np.max(widths)),
    }


def _cantor_limit_diagnostic(profile: dict[str, Any]) -> TargetResult:
    sequence = [(int(row[0]), int(row[1])) for row in profile["irrational_convergents"]]
    rows = [_spectrum_row(p, q) for p, q in sequence]
    measures = [row["spectral_measure"] for row in rows]
    widths = [row["maximum_band_width"] for row in rows]
    return TargetResult(
        "T008",
        "passed",
        "finite_rational_approximant_diagnostic",
        {"convergents": rows},
        {
            "band_count_equals_denominator": all(row["band_count"] == row["q"] for row in rows),
            "measure_decreases": all(right < left for left, right in zip(measures, measures[1:])),
            "maximum_band_width_decreases": all(right < left for left, right in zip(widths, widths[1:])),
        },
        {
            "implementation_attestation_only": True,
            "scientific_coverage_promotion": False,
            "remaining_scientific_boundary": "Finite convergents support shrinking bands and measure, but cannot prove uncountability, zero measure, or Cantor-set homeomorphism.",
        },
    )


def _continuity_diagnostic(profile: dict[str, Any]) -> TargetResult:
    samples_per_band = int(profile["samples_per_band"])
    convergents = [(int(row[0]), int(row[1])) for row in profile["irrational_convergents"]]
    successive = []
    for first, second in zip(convergents, convergents[1:]):
        distance = sampled_hausdorff_distance(
            band_edges(*first), band_edges(*second), samples_per_band=samples_per_band
        )
        successive.append({"from": list(first), "to": list(second), "sampled_hausdorff": distance})

    rational = tuple(int(value) for value in profile["rational_limit"])
    rational_bands = band_edges(*rational)
    rational_measure = spectral_measure(*rational)
    nearby = []
    for raw in profile["near_rational_sequence"]:
        point = (int(raw[0]), int(raw[1]))
        nearby.append(
            {
                **_spectrum_row(*point),
                "sampled_hausdorff_to_rational": sampled_hausdorff_distance(
                    rational_bands, band_edges(*point), samples_per_band=samples_per_band
                ),
            }
        )
    irrational_distances = [row["sampled_hausdorff"] for row in successive]
    rational_distances = [row["sampled_hausdorff_to_rational"] for row in nearby]
    nearby_measures = [row["spectral_measure"] for row in nearby]
    return TargetResult(
        "T009",
        "passed",
        "finite_rational_approximant_diagnostic",
        {
            "irrational_successive_distances": successive,
            "rational_limit": {"p": rational[0], "q": rational[1], "spectral_measure": rational_measure},
            "near_rational_sequence": nearby,
        },
        {
            "irrational_set_distance_decreases": all(right < left for left, right in zip(irrational_distances, irrational_distances[1:])),
            "near_rational_set_distance_decreases": all(right < left for left, right in zip(rational_distances, rational_distances[1:])),
            "nearby_measure_decreases": all(right < left for left, right in zip(nearby_measures, nearby_measures[1:])),
            "measure_contrast_visible": nearby_measures[-1] < 0.25 * rational_measure,
        },
        {
            "implementation_attestation_only": True,
            "scientific_coverage_promotion": False,
            "remaining_scientific_boundary": "Sampled finite-set convergence and measure contrast are diagnostics, not a proof of the continuity/discontinuity theorem.",
        },
    )
