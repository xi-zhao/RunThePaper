#!/usr/bin/env python3
"""Evaluate the (001)/(110) surface-energy pair or fail closed on missing inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "src"))

from nio_dmft.observables import surface_energy  # noqa: E402


REQUIRED_FIELDS = (
    "slab_energy_ev",
    "formula_units",
    "bulk_energy_ev_per_formula",
    "surface_area_angstrom2",
    "equivalent_surfaces",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    orientations = config["parameters"]["orientations"]
    missing = {
        orientation: [name for name in REQUIRED_FIELDS if values.get(name) is None]
        for orientation, values in orientations.items()
    }
    missing = {key: value for key, value in missing.items() if value}
    results: dict[str, float] = {}
    if not missing:
        for orientation, values in orientations.items():
            results[orientation] = surface_energy(
                float(values["slab_energy_ev"]),
                formula_units=int(values["formula_units"]),
                bulk_energy_ev_per_formula=float(values["bulk_energy_ev_per_formula"]),
                surface_area_angstrom2=float(values["surface_area_angstrom2"]),
                equivalent_surfaces=int(values["equivalent_surfaces"]),
            )
    payload = {
        "schema_version": 1,
        "paper_id": "2101.12558",
        "target_id": "T019",
        "status": "generated" if results else "blocked_publication_underspecified",
        "missing_inputs": missing,
        "surface_energy_mev_per_angstrom2": results,
        "orientation_ordering_001_lower": (
            results["001"] < results["110"] if len(results) == 2 else None
        ),
        "required_input_provenance": (
            "independently generated full-precision converged slab and matched bulk "
            "energies; printed final surface energies are comparison-only"
        ),
        "scientific_boundary": {
            "source_pixels_used": False,
            "author_code_used": False,
            "author_numeric_arrays_used": False,
            "printed_surface_energies_used_as_operands": False,
        },
    }
    output = (WORKSPACE / args.output_root).resolve() / "checks" / "T019_surface_energy_pair.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
