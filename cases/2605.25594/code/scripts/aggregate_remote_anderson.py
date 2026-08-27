#!/usr/bin/env python3
"""Aggregate remote A100 Anderson campaign JSONL into per-(L, W) summaries.

Reads outputs/data/remote/results_L*.jsonl (one row per
(L, W, sample) from anderson_remote_driver.py) and writes
outputs/data/remote_campaign_summary.csv with disorder-averaged
gap ratio, IPR, and fidelity-susceptibility metrics per mu, plus a check
JSON with transition-feature gates per system size.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REMOTE_DIR = ROOT / "outputs/data/remote"
SUMMARY_CSV = ROOT / "outputs/data/remote_campaign_summary.csv"
CHECK_PATH = ROOT / "outputs/checks/remote_campaign_summary.json"

GOE_R = 0.5307
POISSON_R = 0.3863
PAPER_WC = 16.5


def main() -> int:
    rows = []
    for path in sorted(REMOTE_DIR.glob("results_L*.jsonl")):
        for line in path.open():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not rows:
        raise SystemExit("no remote result rows found")

    by_lw = defaultdict(list)
    for row in rows:
        by_lw[(row["L"], row["W"])].append(row)

    mu_keys = sorted(rows[0]["susceptibility"].keys(), key=float)
    summary_rows = []
    for (L, W), group in sorted(by_lw.items()):
        entry = {
            "L": L,
            "W": W,
            "samples": len(group),
            "gap_ratio_mean": float(np.mean([g["spacing"]["gap_ratio"] for g in group])),
            "gap_ratio_sem": float(np.std([g["spacing"]["gap_ratio"] for g in group]) / np.sqrt(len(group))),
            "ipr_mean": float(np.mean([g["ipr"] for g in group])),
            "omega_av_mean": float(np.mean([g["spacing"]["omega_av"] for g in group])),
        }
        for mu in mu_keys:
            log_values = [np.log(g["susceptibility"][mu]["tilde_chi_typ_r"] + 1e-300) for g in group]
            entry[f"tilde_chi_typ_r_mu{mu}"] = float(np.exp(np.mean(log_values)))
        summary_rows.append(entry)

    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)

    sizes = {}
    for L in sorted({r["L"] for r in summary_rows}):
        subset = sorted((r for r in summary_rows if r["L"] == L), key=lambda r: r["W"])
        w_values = [r["W"] for r in subset]
        r_values = [r["gap_ratio_mean"] for r in subset]
        crossing = None
        midpoint = 0.5 * (GOE_R + POISSON_R)
        for (w1, r1), (w2, r2) in zip(zip(w_values, r_values), list(zip(w_values, r_values))[1:]):
            if (r1 - midpoint) * (r2 - midpoint) <= 0:
                crossing = w1 + (w2 - w1) * (r1 - midpoint) / (r1 - r2)
                break
        chi_key = f"tilde_chi_typ_r_mu{mu_keys[2]}"
        peak_w = max(subset, key=lambda r: r[chi_key])["W"]
        sizes[str(L)] = {
            "w_grid": w_values,
            "goe_end_r": r_values[0],
            "poisson_end_r": r_values[-1],
            "gap_ratio_midpoint_crossing_W": crossing,
            "chi_peak_W": peak_w,
            "gates": {
                "goe_end_matches": abs(r_values[0] - GOE_R) < 0.01,
                "poisson_end_matches": abs(r_values[-1] - POISSON_R) < 0.01,
                "crossing_near_paper_wc": crossing is not None and abs(crossing - PAPER_WC) < 2.5,
                "chi_peak_below_wc": peak_w < PAPER_WC,
            },
        }

    check = {
        "status": "passed"
        if all(all(v["gates"].values()) for v in sizes.values())
        else "partial",
        "source": "remote_a100_campaign",
        "paper_wc": PAPER_WC,
        "sizes": sizes,
        "rows_total": len(rows),
        "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
    }
    CHECK_PATH.write_text(json.dumps(check, indent=2) + "\n")
    print(json.dumps({"status": check["status"], "sizes": {k: v["gates"] for k, v in sizes.items()},
                      "crossings": {k: v["gap_ratio_midpoint_crossing_W"] for k, v in sizes.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
