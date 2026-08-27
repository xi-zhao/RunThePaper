from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from atom_path_planner import (
    EdgeScoringGNN,
    assignment_metrics,
    decode_assignment_from_edge_scores,
    decode_assignment_with_modified_auction,
    generate_path_planning_sample,
    predict_edge_scores,
    train_one_sample,
)
from p2wgs_potential import run_reduced_p2wgs_pilot


ITEMS_BY_TARGET = {
    "T001": (
        "F3-A-GNN-MAX",
        "F3-A-HUNGARIAN-MAX",
        "F3-B-GNN-AVERAGE",
        "F3-B-HUNGARIAN-AVERAGE",
    ),
    "T002": (
        "F4-PHASE-ITER3",
        "F4-PHASE-ITER5",
        "F4-PHASE-ITER8",
        "F4-PHASE-ITER10",
        "F4-INTENSITY-ITER3",
        "F4-INTENSITY-ITER5",
        "F4-INTENSITY-ITER8",
        "F4-INTENSITY-ITER10",
    ),
}


def _finite_metrics(metrics: dict[str, float]) -> bool:
    return all(np.isfinite(float(value)) for value in metrics.values())


def _run_gnn_assignment_attestation(config: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(int(config["seed"]))
    device = torch.device("cpu")
    model = EdgeScoringGNN(
        node_dim=4,
        edge_dim=6,
        hidden_dim=int(config["hidden_dim"]),
        message_passes=int(config["message_passes"]),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    losses = []
    for index in range(int(config["train_samples"])):
        sample = generate_path_planning_sample(
            initial_side=int(config["initial_side"]),
            target_side=int(config["target_side"]),
            loading_probability=float(config["loading_probability"]),
            k_neighbors=int(config["k_neighbors"]),
            seed=int(config["seed"]) + index,
            graph_backend=str(config["graph_backend"]),
        )
        losses.append(train_one_sample(model, sample, optimizer, device))

    evaluation_sample = generate_path_planning_sample(
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        loading_probability=float(config["loading_probability"]),
        k_neighbors=int(config["k_neighbors"]),
        seed=int(config["seed"]) + 10_000,
        graph_backend=str(config["graph_backend"]),
    )
    scores = predict_edge_scores(model, evaluation_sample)
    score_hungarian = decode_assignment_from_edge_scores(evaluation_sample, scores)
    modified_auction = decode_assignment_with_modified_auction(evaluation_sample, scores)
    hungarian_metrics = assignment_metrics(evaluation_sample, score_hungarian)
    auction_metrics = assignment_metrics(evaluation_sample, modified_auction)
    unique_hungarian = len(set(int(value) for value in score_hungarian[:, 0]))
    unique_auction = len(set(int(value) for value in modified_auction[:, 0]))
    target_count = int(evaluation_sample.target_count)
    passed = (
        len(losses) == int(config["train_samples"])
        and all(np.isfinite(loss) for loss in losses)
        and scores.shape == (evaluation_sample.edge_index.shape[1],)
        and unique_hungarian == target_count
        and unique_auction == target_count
        and _finite_metrics(hungarian_metrics)
        and _finite_metrics(auction_metrics)
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "training": {
            "steps": len(losses),
            "loss_initial": float(losses[0]),
            "loss_final": float(losses[-1]),
        },
        "evaluation": {
            "atom_count": int(len(evaluation_sample.atom_positions)),
            "target_count": target_count,
            "score_hungarian": hungarian_metrics,
            "modified_auction": auction_metrics,
            "unique_atoms": {
                "score_hungarian": unique_hungarian,
                "modified_auction": unique_auction,
            },
        },
        "paper_target_boundary": config["paper_target_boundary"],
    }


def _run_p2wgs_attestation(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    metrics = run_reduced_p2wgs_pilot(
        output_dir=output_root / "p2wgs",
        grid_size=int(config["grid_size"]),
        initial_side=int(config["initial_side"]),
        target_side=int(config["target_side"]),
        samples=int(config["samples"]),
        frames=int(config["frames"]),
        iterations=[int(value) for value in config["iterations"]],
        sigma=float(config["sigma"]),
        seed=int(config["seed"]),
    )
    iterations = [str(value) for value in config["iterations"]]
    phase = metrics["summary"]["mean_phase_continuity_by_iteration"]
    intensity = metrics["summary"]["mean_intensity_continuity_by_iteration"]
    passed = (
        metrics["status"] == "completed"
        and all(key in phase and np.isfinite(float(phase[key])) for key in iterations)
        and all(key in intensity and np.isfinite(float(intensity[key])) for key in iterations)
    )
    return {
        "status": "passed" if passed else "failed",
        "profile": "reduced_implementation_attestation",
        "paper_scale_executed": False,
        "iteration_counts": [int(value) for value in config["iterations"]],
        "mean_phase_continuity_by_iteration": phase,
        "mean_intensity_continuity_by_iteration": intensity,
        "paper_target_boundary": config["paper_target_boundary"],
        "known_scientific_gap": config["known_scientific_gap"],
    }


def run_campaign(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if config.get("paper_id") != "2604.08669":
        raise ValueError("paper_id must be 2604.08669")
    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    if parameters.get("profile") != "reduced_implementation_attestation":
        raise ValueError("only the frozen reduced implementation-attestation profile is accepted")
    gnn = _run_gnn_assignment_attestation(parameters["gnn_assignment"])
    p2wgs = _run_p2wgs_attestation(parameters["p2wgs"], Path(output_root))
    target_checks = {"T001": gnn, "T002": p2wgs}
    item_results = {
        item_id: {
            "target_id": target_id,
            "implementation_status": "attested" if target_checks[target_id]["status"] == "passed" else "failed",
            "scientific_coverage_changed": False,
        }
        for target_id, items in ITEMS_BY_TARGET.items()
        for item_id in items
    }
    status = "passed" if all(check["status"] == "passed" for check in target_checks.values()) else "failed"
    return {
        "schema_version": 1,
        "paper_id": "2604.08669",
        "status": status,
        "profile": parameters["profile"],
        "fixed_item_denominator": len(item_results),
        "item_results": item_results,
        "target_checks": target_checks,
        "scientific_coverage_changed": False,
        "numerical_input_boundary": {
            "paper_pdf_or_tex_read": False,
            "author_code_or_arrays_read": False,
            "reference_pixels_read": False,
        },
    }
