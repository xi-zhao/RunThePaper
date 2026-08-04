#!/usr/bin/env python3
"""Combine the approved proxy experiments into one agent-facing verdict."""

from __future__ import annotations

import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
CHECKS = WORKSPACE / "outputs" / "checks"
OUTPUT = CHECKS / "proxy_campaign_result.json"


def load_check(name: str) -> dict[str, object]:
    return json.loads((CHECKS / name).read_text(encoding="utf-8"))


def main() -> int:
    routing = load_check("proxy_routing_result.json")
    scaling = load_check("proxy_scaling_result.json")
    sensitivity = load_check("proxy_sensitivity_result.json")

    component_statuses = {
        "routing_fig4_fig5_fig8": routing["status"],
        "scaling_fig6": scaling["status"],
        "sensitivity_fig7": sensitivity["status"],
    }
    completed = all(
        status in {"passed", "passed_with_warnings"}
        for status in component_statuses.values()
    )
    sensitivity_crossings = sensitivity["break_even_crossing"]
    break_even_reproduced = all(sensitivity_crossings.values())

    status = "failed" if not completed else "passed_with_warnings" if not break_even_reproduced else "passed"
    result = {
        "schema_version": 1,
        "status": status,
        "paper_id": "2607.08212",
        "target_scope": "all_locally_feasible_proxy_reproductions",
        "scope": "proxy_model",
        "approval": routing["approval"],
        "components": component_statuses,
        "checks": {
            "all_proxy_components_executed": completed,
            "eight_family_routing_matrix_passed": routing["status"] == "passed",
            "fig6_scaling_proxy_passed": scaling["status"] == "passed",
            "fig7_sensitivity_surface_generated": sensitivity["status"]
            in {"passed", "passed_with_warnings"},
            "fig7_break_even_contours_reproduced": break_even_reproduced,
        },
        "decision": {
            "status": "paper_metric_verdict_pass" if completed else "paper_metric_verdict_stop",
            "next_action": (
                "request_author_artifacts_for_exact_fig4_to_fig8"
                if completed
                else "repair_incomplete_proxy_component"
            ),
            "reason": (
                "All locally feasible proxy experiments have run. The eight-family routing "
                "matrix and Fig. 6 scaling mechanism pass, while Fig. 7 remains partial because "
                "the disclosed toy router does not produce the paper's break-even contours. "
                "Exact curves now require author generators, layouts, route traces, and seeds."
            ),
        },
        "claim_boundary": (
            "This verdict closes only the approved proxy campaign. It does not claim an exact "
            "numerical reproduction of Figs. 4-8. The absent Fig. 7 break-even contours are "
            "retained as a model mismatch rather than tuned away."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
