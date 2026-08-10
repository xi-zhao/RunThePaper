#!/usr/bin/env python3
"""Record formula-level evidence for the unresolved Figure 3 legend discrepancy."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


WORKSPACE = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data_path = WORKSPACE / "outputs/data/fig3_spectrum_numeric.csv"
    reference_path = WORKSPACE / "internal-paper-reference/fig3.png"
    grouped: dict[str, list[float]] = defaultdict(list)
    with data_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[row["sector"]].append(float(row["x"]))
    charges = np.arange(1, 6, dtype=np.float64)
    onsets = np.asarray([min(grouped[str(charge)]) for charge in range(1, 6)])
    slope = float((charges @ onsets) / (charges @ charges))
    residual = onsets - slope * charges
    relative_residual = float(np.max(np.abs(residual)) / slope)
    linearity_tolerance = 0.03
    payload = {
        "schema_version": 1,
        "paper_id": "1711.09418",
        "status": "inconclusive_pending_protocol_v2_review",
        "assessment": "inconclusive",
        "paper_error_candidate_emitted": False,
        "source_figure_sha256": sha256(reference_path),
        "frozen_numeric_data_sha256": sha256(data_path),
        "published_legend_labels": [0, 1, 2, 3, 5, 6],
        "curve_identities_from_equations_and_onsets": [0, 1, 2, 3, 4, 5],
        "numeric_sector_onsets": {str(charge): min(grouped[str(charge)]) for charge in range(6)},
        "onset_linear_fit": {
            "slope": slope,
            "max_relative_residual_to_slope": relative_residual,
            "tolerance": linearity_tolerance,
            "passed": bool(relative_residual < linearity_tolerance),
        },
        "evidence_summary": "Formula-derived sectors 4 and 5 have onsets aligned with the final two visible curves, whereas a sector-6 onset lies beyond x=10. This is a stable label/curve discrepancy, not by itself a paper-error finding.",
        "accepted_reproduction_policy": "Keep the formula-derived 0,...,5 series as an explicit reproduction interpretation and preserve the printed 0,1,2,3,5,6 labels as the strict paper claim. Do not tune numerical arrays from pixels.",
        "missing_before_paper_error_candidate": [
            "fresh inventory-first protocol-v2 independent review",
            "explicit falsification of alternative branch or legend interpretations",
            "quantified strict-reference discrepancy with a justified tolerance",
            "reviewer confirmation that reproduction defects and compute limits are excluded",
        ],
    }
    output = WORKSPACE / "outputs/checks/figure3_legend_audit.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
