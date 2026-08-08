from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from benchmark_release import (
    ARCHIVE_MD5,
    ARCHIVE_SHA256,
    RANDOM_PANEL_ORDER,
    file_digest,
    validate_archive,
)


RELEASE_PREFIX = "NPUBenchmarkData-release/"
AUTHOR_EVIDENCE_STAGE = "author_data_validated"
INDEPENDENT_EVIDENCE_STAGE = "independent_numerics"
REIMPLEMENTATION_EVIDENCE_STAGE = "independent_reimplementation"
ZERO_GAP_THRESHOLD = 1.0e-6
PIPELINE_GAP_THRESHOLD = 5.0e-4
LAW_TOLERANCE = 1.0e-9

PINNED_REVISIONS = {
    "yao-rs": "a4623570f0d4b9f1e10249ab71ed47a0b7827b22",
    "omeinsum-rs": "c69105303313998733537ff57a23bc7e95349f03",
    "omeco": "193b3bb10256cf9f57bbcb15d492e2964c2b1ba8",
}

FAMILY_ORDER = ("random", "Clifford+T", "QAOA", "VQE")
EXPECTED_FAMILY_COUNTS = {
    "random": 12,
    "Clifford+T": 24,
    "QAOA": 10,
    "VQE": 21,
}
EXPECTED_NEAR_ZERO_COUNTS = {
    "random": 9,
    "Clifford+T": 20,
    "QAOA": 10,
    "VQE": 20,
}
EXPECTED_BELOW_GAP_COUNTS = {
    "random": 11,
    "Clifford+T": 24,
    "QAOA": 10,
    "VQE": 21,
}

RANDOM_DISPLAY_NAMES = {
    "test": "test (5q)",
    "rectangular_4x4_1-16-1_0": "rect 4×4, d16",
    "rochester_53_8_0_pABC": "rochester-53, d8",
    "rectangular_6x6_1-32-1_0": "rect 6×6, d32",
    "bristlecone_48_1-16-1_0": "bristlecone-48, d16",
    "rectangular_6x6_1-24-1_0": "rect 6×6, d24",
    "rectangular_6x6_1-16-1_0": "rect 6×6, d16",
    "bristlecone_70_1-16-1_0": "bristlecone-70, d16",
    "sycamore_53_10_0": "sycamore-53, m=10",
    "rochester_53_12_0_pABC": "rochester-53, d12",
    "bristlecone_70_1-24-1_0": "bristlecone-70, d24",
    "rectangular_8x8_1-24-1_0": "rect 8×8, d24",
}

FAMILY_STYLES = {
    "random": {"color": "#cf4f1c", "marker": "o"},
    "Clifford+T": {"color": "#8d43b5", "marker": "^"},
    "QAOA": {"color": "#1f62b5", "marker": "d"},
    "VQE": {"color": "#0a7d4f", "marker": "s"},
}


class ReproductionDataError(RuntimeError):
    """Raised when numerical evidence violates the reproduction contract."""


@dataclass(frozen=True)
class CostLawPoint:
    circuit: str
    display_name: str
    family: str
    m: float
    r: float
    source_overhead: float
    source_path: str

    @property
    def computed_overhead(self) -> float:
        return 1.0 + 2.0 * self.m + self.r

    @property
    def lower_bound(self) -> float:
        return 1.0 + 2.0 * self.m

    @property
    def upper_bound(self) -> float:
        return 2.0 + self.m

    @property
    def law_residual(self) -> float:
        return abs(self.source_overhead - self.computed_overhead)


@dataclass(frozen=True)
class PipelinePoint:
    circuit: str
    display_name: str
    family: str
    convert_only: float
    polished: float
    full_anneal: float
    released_ratio_max_error: float
    source_path: str

    @property
    def relative_gap(self) -> float:
        return abs(self.convert_only - self.full_anneal) / self.full_anneal

    @property
    def polish_gap(self) -> float:
        return abs(self.polished - self.full_anneal) / self.full_anneal

    @property
    def near_zero(self) -> bool:
        return self.relative_gap <= ZERO_GAP_THRESHOLD

    @property
    def below_pipeline_threshold(self) -> bool:
        return self.relative_gap <= PIPELINE_GAP_THRESHOLD


def _read_json(release: zipfile.ZipFile, member: str) -> Mapping[str, Any]:
    try:
        with release.open(member) as handle:
            return json.load(io.TextIOWrapper(handle, encoding="utf-8"))
    except KeyError as exc:
        raise ReproductionDataError(f"Missing release member: {member}") from exc


def _read_csv(release: zipfile.ZipFile, member: str) -> list[dict[str, str]]:
    try:
        with release.open(member) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", newline="")
            return list(csv.DictReader(text))
    except KeyError as exc:
        raise ReproductionDataError(f"Missing release member: {member}") from exc


def _json_members(release: zipfile.ZipFile, directory: str) -> list[str]:
    prefix = f"{RELEASE_PREFIX}{directory.rstrip('/')}/"
    return sorted(
        name
        for name in release.namelist()
        if name.startswith(prefix)
        and name.endswith(".json")
        and "/._" not in name
    )


def _structured_family(circuit: str) -> str:
    if circuit.startswith("ct_"):
        return "Clifford+T"
    if circuit.startswith("qaoa_"):
        return "QAOA"
    if circuit.startswith("vqe_"):
        return "VQE"
    raise ReproductionDataError(f"Unknown structured circuit family: {circuit}")


def load_cost_law_points(archive_path: Path) -> list[CostLawPoint]:
    points: list[CostLawPoint] = []
    with zipfile.ZipFile(archive_path) as release:
        for directory in ("results/green-sa-v5", "results/green-sa-v5-ext"):
            for member in _json_members(release, directory):
                payload = _read_json(release, member)
                circuit = Path(member).stem
                audit = payload["audit_crosscheck"]
                points.append(
                    CostLawPoint(
                        circuit=circuit,
                        display_name=RANDOM_DISPLAY_NAMES.get(circuit, circuit),
                        family="random",
                        m=float(audit["m"]),
                        r=float(audit["r"]),
                        source_overhead=float(audit["predicted_overhead"]),
                        source_path=member,
                    )
                )

        structured_sources = (
            ("Clifford+T", "clifford-t.csv"),
            ("QAOA", "qaoa.csv"),
            ("VQE", "vqe.csv"),
        )
        for family, filename in structured_sources:
            member = f"{RELEASE_PREFIX}results/structured-v1/{filename}"
            for row in _read_csv(release, member):
                points.append(
                    CostLawPoint(
                        circuit=row["circuit"],
                        display_name=row["circuit"],
                        family=family,
                        m=float(row["m"]),
                        r=float(row["r"]),
                        source_overhead=float(row["predicted_overhead"]),
                        source_path=member,
                    )
                )

    family_rank = {family: index for index, family in enumerate(FAMILY_ORDER)}
    return sorted(points, key=lambda point: (family_rank[point.family], point.circuit))


def _pipeline_point_from_payload(
    circuit: str,
    family: str,
    member: str,
    payload: Mapping[str, Any],
) -> PipelinePoint:
    costs = payload["costs"]
    denominator = float(costs["best_real"])
    if denominator <= 0.0:
        raise ReproductionDataError(f"Non-positive best_real for {circuit}")
    calculated = {
        name: float(costs[name]) / denominator
        for name in ("convert_only", "polished", "full_anneal")
    }
    released = payload.get("ratios_vs_best_real", {})
    ratio_errors = [
        abs(calculated[name] - float(released[name]))
        for name in calculated
        if name in released
    ]
    max_error = max(ratio_errors, default=0.0)
    return PipelinePoint(
        circuit=circuit,
        display_name=RANDOM_DISPLAY_NAMES.get(circuit, circuit),
        family=family,
        convert_only=calculated["convert_only"],
        polished=calculated["polished"],
        full_anneal=calculated["full_anneal"],
        released_ratio_max_error=max_error,
        source_path=member,
    )


def load_pipeline_points(archive_path: Path) -> list[PipelinePoint]:
    points: list[PipelinePoint] = []
    with zipfile.ZipFile(archive_path) as release:
        for directory in ("results/green-sa-v5", "results/green-sa-v5-ext"):
            for member in _json_members(release, directory):
                circuit = Path(member).stem
                points.append(
                    _pipeline_point_from_payload(
                        circuit,
                        "random",
                        member,
                        _read_json(release, member),
                    )
                )
        directory = "results/structured-v1/green-sa"
        for member in _json_members(release, directory):
            circuit = Path(member).stem
            points.append(
                _pipeline_point_from_payload(
                    circuit,
                    _structured_family(circuit),
                    member,
                    _read_json(release, member),
                )
            )

    family_rank = {family: index for index, family in enumerate(FAMILY_ORDER)}
    return sorted(points, key=lambda point: (family_rank[point.family], point.circuit))


def load_independent_points(
    random_study_dir: Path,
    structured_study_dir: Path,
) -> tuple[list[CostLawPoint], list[PipelinePoint], dict[str, Any]]:
    """Load newly computed green-SA studies without reading released results."""

    law_points: list[CostLawPoint] = []
    pipeline_points: list[PipelinePoint] = []
    schedule_mismatches: list[str] = []
    elapsed_seconds = 0.0

    sources = (("random", random_study_dir), ("structured", structured_study_dir))
    for source_kind, study_dir in sources:
        if not study_dir.is_dir():
            raise ReproductionDataError(f"Independent study directory is missing: {study_dir}")
        for path in sorted(study_dir.glob("*.study.json")):
            circuit = path.name.removesuffix(".study.json")
            payload = json.loads(path.read_text(encoding="utf-8"))
            family = "random" if source_kind == "random" else _structured_family(circuit)
            audit = payload["audit_crosscheck"]
            source_path = f"{study_dir.name}/{path.name}"
            law_points.append(
                CostLawPoint(
                    circuit=circuit,
                    display_name=RANDOM_DISPLAY_NAMES.get(circuit, circuit),
                    family=family,
                    m=float(audit["m"]),
                    r=float(audit["r"]),
                    source_overhead=float(audit["predicted_overhead"]),
                    source_path=source_path,
                )
            )
            pipeline_points.append(
                _pipeline_point_from_payload(
                    circuit,
                    family,
                    source_path,
                    payload,
                )
            )

            schedule = payload.get("schedule", {})
            initializer = payload.get("initializer", {})
            schedule_ok = (
                schedule.get("nsteps") == 600_000
                and schedule.get("seeds") == [42, 7, 2026]
                and math.isclose(float(schedule.get("t0", math.nan)), 1.0)
                and math.isclose(float(schedule.get("t1", math.nan)), 0.005)
                and initializer.get("algorithm") == "omeco::TreeSA"
                and initializer.get("profile") == "default"
                and initializer.get("ntrials") == 10
                and initializer.get("niters") == 50
                and initializer.get("seed_base") == 42
                and math.isclose(float(initializer.get("sc_target", math.nan)), 40.0)
            )
            if not schedule_ok:
                schedule_mismatches.append(circuit)
            elapsed_seconds += sum(float(value) for value in payload.get("seconds", {}).values())

    if schedule_mismatches:
        raise ReproductionDataError(
            f"Independent studies do not use the paper schedule: {schedule_mismatches}"
        )
    family_rank = {family: index for index, family in enumerate(FAMILY_ORDER)}
    law_points.sort(key=lambda point: (family_rank[point.family], point.circuit))
    pipeline_points.sort(key=lambda point: (family_rank[point.family], point.circuit))
    info = {
        "kind": INDEPENDENT_EVIDENCE_STAGE,
        "random_study_dir": random_study_dir.name,
        "structured_study_dir": structured_study_dir.name,
        "studies": len(law_points),
        "paper_schedule_verified": True,
        "optimizer_reported_seconds_total": elapsed_seconds,
        "pinned_revisions": PINNED_REVISIONS,
    }
    return law_points, pipeline_points, info


def load_reimplementation_points(
    study_dir: Path,
) -> tuple[list[CostLawPoint], list[PipelinePoint], dict[str, Any]]:
    """Load results produced by the clean-room Python implementation."""

    manifest_path = study_dir / "campaign_manifest.json"
    if not manifest_path.is_file():
        raise ReproductionDataError(f"Missing clean-room campaign manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    input_audit = manifest.get("input_member_audit", {})
    input_members = input_audit.get("members", [])
    allowed_prefixes = tuple(input_audit.get("allowed_prefixes", ()))
    if (
        input_audit.get("author_results_or_plans_read") is not False
        or int(input_audit.get("payloads_read", -1)) != 122
        or len(input_members) != 122
        or not allowed_prefixes
        or any(not str(member).startswith(allowed_prefixes) for member in input_members)
        or any("/results/" in str(member) for member in input_members)
        or any("/experiments/networks/" in str(member) for member in input_members)
    ):
        raise ReproductionDataError("Clean-room input-member audit failed")

    paths = sorted(
        path
        for path in study_dir.glob("*.json")
        if path.name != "campaign_manifest.json"
    )
    if len(paths) != 67:
        raise ReproductionDataError(
            f"Expected 67 independent Python records in {study_dir}, found {len(paths)}"
        )
    law_points: list[CostLawPoint] = []
    pipeline_points: list[PipelinePoint] = []
    configuration_hashes: set[str] = set()
    elapsed_seconds = 0.0
    real_cost_gaps: dict[str, float] = {}
    polish_real_cost_gaps: dict[str, float] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("evidence_stage") != REIMPLEMENTATION_EVIDENCE_STAGE:
            raise ReproductionDataError(f"Unexpected evidence stage in {path}")
        circuit = str(payload["network"]["name"])
        family = str(payload["network"]["family"])
        leaves = int(payload["network"]["leaves"])
        green_leaves = int(payload["network"]["green_leaves"])
        for strategy in ("convert_only", "polished", "full_anneal"):
            stats = payload[strategy]
            expected_merges = max(0, green_leaves - 1)
            if int(stats["merge_nodes"]) != expected_merges:
                raise ReproductionDataError(
                    f"{circuit}/{strategy}: merge count is not n_green-1"
                )
            node_count = sum(
                int(stats[field])
                for field in ("pass_nodes", "ride_nodes", "merge_nodes")
            )
            if node_count != leaves - 1:
                raise ReproductionDataError(
                    f"{circuit}/{strategy}: internal-node count mismatch"
                )
            base = sum(
                int(stats[field])
                for field in ("pass_volume", "ride_volume", "merge_volume")
            )
            real = (
                int(stats["pass_volume"])
                + 2 * int(stats["ride_volume"])
                + 3 * int(stats["merge_volume"])
            )
            if base != int(stats["base_volume"]) or real != int(stats["real_volume"]):
                raise ReproductionDataError(
                    f"{circuit}/{strategy}: integer volume audit failed"
                )
        full = payload["full_anneal"]
        convert = payload["convert_only"]
        polished = payload["polished"]
        source_path = f"{study_dir.name}/{path.name}"
        law_points.append(
            CostLawPoint(
                circuit=circuit,
                display_name=RANDOM_DISPLAY_NAMES.get(circuit, circuit),
                family=family,
                m=float(full["m"]),
                r=float(full["r"]),
                source_overhead=float(full["overhead"]),
                source_path=source_path,
            )
        )
        pipeline_points.append(
            PipelinePoint(
                circuit=circuit,
                display_name=RANDOM_DISPLAY_NAMES.get(circuit, circuit),
                family=family,
                convert_only=float(convert["overhead"]),
                polished=float(polished["overhead"]),
                full_anneal=float(full["overhead"]),
                released_ratio_max_error=0.0,
                source_path=source_path,
            )
        )
        configuration_hashes.add(str(payload["configuration_sha256"]))
        elapsed_seconds += float(payload.get("runtime_seconds", 0.0))
        real_cost_gaps[circuit] = float(payload["pipeline"]["relative_real_cost_gap"])
        polish_real_cost_gaps[circuit] = float(payload["pipeline"]["polish_real_cost_gap"])
    if len(configuration_hashes) != 1:
        raise ReproductionDataError(
            f"Mixed independent configurations in {study_dir}: {sorted(configuration_hashes)}"
        )
    family_rank = {family: index for index, family in enumerate(FAMILY_ORDER)}
    law_points.sort(key=lambda point: (family_rank[point.family], point.circuit))
    pipeline_points.sort(key=lambda point: (family_rank[point.family], point.circuit))
    first = json.loads(paths[0].read_text(encoding="utf-8"))
    configuration_hash = next(iter(configuration_hashes))
    if manifest.get("configuration_sha256") != configuration_hash:
        raise ReproductionDataError("Campaign manifest and records use different configurations")
    info = {
        "kind": REIMPLEMENTATION_EVIDENCE_STAGE,
        "study_dir": study_dir.name,
        "studies": len(paths),
        "configuration": first["configuration"],
        "configuration_sha256": configuration_hash,
        "optimizer_reported_seconds_total": elapsed_seconds,
        "integrity_boundary": first["integrity_boundary"],
        "input_member_audit": {
            "manifest": f"{study_dir.name}/{manifest_path.name}",
            "payloads_read": len(input_members),
            "allowed_prefixes": list(allowed_prefixes),
            "author_results_or_plans_read": False,
        },
        "real_cost_gap_audit": {
            "maximum": max(real_cost_gaps.values()),
            "above_5e-4": sorted(
                circuit for circuit, gap in real_cost_gaps.items() if gap > PIPELINE_GAP_THRESHOLD
            ),
            "per_circuit": real_cost_gaps,
            "polish_per_circuit": polish_real_cost_gaps,
        },
    }
    return law_points, pipeline_points, info


def _counts_by_family(points: Iterable[Any], predicate: Any | None = None) -> dict[str, int]:
    if predicate is None:
        counter = Counter(point.family for point in points)
    else:
        counter = Counter(point.family for point in points if predicate(point))
    return {family: counter.get(family, 0) for family in FAMILY_ORDER}


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ReproductionDataError(f"{label}: expected {expected!r}, got {actual!r}")


def validate_reproduction(
    law_points: Sequence[CostLawPoint],
    pipeline_points: Sequence[PipelinePoint],
    provenance_info: Mapping[str, Any],
    *,
    evidence_stage: str = AUTHOR_EVIDENCE_STAGE,
    integrity_boundary: str | None = None,
) -> dict[str, Any]:
    law_ids = [point.circuit for point in law_points]
    pipeline_ids = [point.circuit for point in pipeline_points]
    _assert_equal(len(law_ids), len(set(law_ids)), "Figure 8 duplicate circuit IDs")
    _assert_equal(len(pipeline_ids), len(set(pipeline_ids)), "Figure 9 duplicate circuit IDs")
    _assert_equal(set(law_ids), set(pipeline_ids), "Figure 8/9 circuit identity set")

    law_family_counts = _counts_by_family(law_points)
    pipeline_family_counts = _counts_by_family(pipeline_points)
    _assert_equal(law_family_counts, EXPECTED_FAMILY_COUNTS, "Figure 8 family counts")
    _assert_equal(pipeline_family_counts, EXPECTED_FAMILY_COUNTS, "Figure 9 family counts")

    max_law_residual = max(point.law_residual for point in law_points)
    if max_law_residual > LAW_TOLERANCE:
        raise ReproductionDataError(
            f"Cost-law residual {max_law_residual:.3e} exceeds {LAW_TOLERANCE:.1e}"
        )
    band_violations = [
        point.circuit
        for point in law_points
        if point.source_overhead < point.lower_bound - LAW_TOLERANCE
        or point.source_overhead > point.upper_bound + LAW_TOLERANCE
        or point.m < -LAW_TOLERANCE
        or point.r < -LAW_TOLERANCE
        or point.m + point.r > 1.0 + LAW_TOLERANCE
    ]
    _assert_equal(band_violations, [], "Figure 8 analytic-band violations")

    max_released_ratio_error = max(
        point.released_ratio_max_error for point in pipeline_points
    )
    if max_released_ratio_error > 1.0e-12:
        raise ReproductionDataError(
            "Released ratio cross-check failed: "
            f"max error {max_released_ratio_error:.3e}"
        )

    near_zero_counts = _counts_by_family(pipeline_points, lambda point: point.near_zero)
    below_gap_counts = _counts_by_family(
        pipeline_points, lambda point: point.below_pipeline_threshold
    )
    outliers = [
        point.circuit
        for point in pipeline_points
        if not point.below_pipeline_threshold
    ]
    test_point = next(point for point in pipeline_points if point.circuit == "test")
    strict_paper_features = evidence_stage != REIMPLEMENTATION_EVIDENCE_STAGE
    if strict_paper_features:
        _assert_equal(near_zero_counts, EXPECTED_NEAR_ZERO_COUNTS, "Figure 9 near-zero counts")
        _assert_equal(
            below_gap_counts,
            EXPECTED_BELOW_GAP_COUNTS,
            "Figure 9 threshold counts",
        )
        _assert_equal(outliers, ["test"], "Figure 9 outlier identity")
        if test_point.polish_gap > 1.0e-12:
            raise ReproductionDataError(
                f"5-qubit polish does not close the gap: {test_point.polish_gap:.3e}"
            )
    paper_feature_match = (
        near_zero_counts == EXPECTED_NEAR_ZERO_COUNTS
        and below_gap_counts == EXPECTED_BELOW_GAP_COUNTS
        and outliers == ["test"]
        and test_point.polish_gap <= PIPELINE_GAP_THRESHOLD
    )

    sycamore = next(
        point for point in law_points if point.circuit == "sycamore_53_10_0"
    )
    yy_point = next(
        point
        for point in law_points
        if point.circuit == "vqe_heisline32_A_l4_yy_s0"
    )

    if integrity_boundary is None:
        if evidence_stage == AUTHOR_EVIDENCE_STAGE:
            integrity_boundary = (
                "Figures are regenerated from author-released numeric records; "
                "this is not an independent optimizer rerun."
            )
        elif evidence_stage == REIMPLEMENTATION_EVIDENCE_STAGE:
            integrity_boundary = (
                "Figures are computed from raw circuits by a clean-room Python cost "
                "model and unrelated generic tree initializer; no author code or plan is used."
            )
        else:
            integrity_boundary = (
                "Figures are regenerated from newly computed paper-parameter optimizer studies."
            )

    return {
        "schema_version": 1,
        "paper_id": "2608.03987",
        "status": "passed" if strict_paper_features or paper_feature_match else "partial",
        "evidence_stage": evidence_stage,
        "integrity_boundary": integrity_boundary,
        "provenance": dict(provenance_info),
        "targets": {
            "T008": {
                "paper_item": "Figure 8",
                "status": "passed",
                "circuits": len(law_points),
                "family_counts": law_family_counts,
                "maximum_law_residual": max_law_residual,
                "law_tolerance": LAW_TOLERANCE,
                "analytic_band_violations": band_violations,
                "sycamore_overhead": sycamore.source_overhead,
                "vqe_yy_point": {
                    "m": yy_point.m,
                    "overhead": yy_point.source_overhead,
                },
            },
            "T009": {
                "paper_item": "Figure 9",
                "status": "passed" if paper_feature_match else "differences_found",
                "circuits": len(pipeline_points),
                "family_counts": pipeline_family_counts,
                "near_zero_threshold": ZERO_GAP_THRESHOLD,
                "near_zero_counts": near_zero_counts,
                "paper_near_zero_counts": EXPECTED_NEAR_ZERO_COUNTS,
                "pipeline_gap_threshold": PIPELINE_GAP_THRESHOLD,
                "below_threshold_counts": below_gap_counts,
                "paper_below_threshold_counts": EXPECTED_BELOW_GAP_COUNTS,
                "outliers": outliers,
                "test_relative_gap": test_point.relative_gap,
                "test_polish_gap": test_point.polish_gap,
                "maximum_released_ratio_error": max_released_ratio_error,
                "real_cost_gap_audit": provenance_info.get("real_cost_gap_audit"),
            },
        },
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_tidy_data(
    law_points: Sequence[CostLawPoint],
    pipeline_points: Sequence[PipelinePoint],
    data_dir: Path,
    *,
    evidence_stage: str,
    filename_suffix: str = "",
) -> list[Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    law_path = data_dir / f"fig8_cost_law{filename_suffix}.csv"
    with law_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=(
                "circuit",
                "display_name",
                "family",
                "m",
                "r",
                "source_overhead",
                "computed_overhead",
                "lower_bound",
                "upper_bound",
                "law_residual",
                "evidence_stage",
                "source_path",
            ),
        )
        writer.writeheader()
        for point in law_points:
            writer.writerow(
                {
                    "circuit": point.circuit,
                    "display_name": point.display_name,
                    "family": point.family,
                    "m": format(point.m, ".17g"),
                    "r": format(point.r, ".17g"),
                    "source_overhead": format(point.source_overhead, ".17g"),
                    "computed_overhead": format(point.computed_overhead, ".17g"),
                    "lower_bound": format(point.lower_bound, ".17g"),
                    "upper_bound": format(point.upper_bound, ".17g"),
                    "law_residual": format(point.law_residual, ".17g"),
                    "evidence_stage": evidence_stage,
                    "source_path": point.source_path,
                }
            )

    pipeline_path = data_dir / f"fig9_pipeline{filename_suffix}.csv"
    with pipeline_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=(
                "circuit",
                "display_name",
                "family",
                "convert_only",
                "polished",
                "full_anneal",
                "relative_gap",
                "polish_gap",
                "near_zero_at_1e-6",
                "below_threshold_at_5e-4",
                "released_ratio_max_error",
                "evidence_stage",
                "source_path",
            ),
        )
        writer.writeheader()
        for point in pipeline_points:
            writer.writerow(
                {
                    "circuit": point.circuit,
                    "display_name": point.display_name,
                    "family": point.family,
                    "convert_only": format(point.convert_only, ".17g"),
                    "polished": format(point.polished, ".17g"),
                    "full_anneal": format(point.full_anneal, ".17g"),
                    "relative_gap": format(point.relative_gap, ".17g"),
                    "polish_gap": format(point.polish_gap, ".17g"),
                    "near_zero_at_1e-6": str(point.near_zero).lower(),
                    "below_threshold_at_5e-4": str(
                        point.below_pipeline_threshold
                    ).lower(),
                    "released_ratio_max_error": format(
                        point.released_ratio_max_error, ".17g"
                    ),
                    "evidence_stage": evidence_stage,
                    "source_path": point.source_path,
                }
            )
    return [law_path, pipeline_path]


def _series_metrics(reference: Sequence[float], generated: Sequence[float]) -> dict[str, float]:
    if len(reference) != len(generated) or not reference:
        raise ReproductionDataError("Cannot compare empty or differently sized series")
    differences = [new - old for old, new in zip(reference, generated, strict=True)]
    mean_reference = sum(reference) / len(reference)
    mean_generated = sum(generated) / len(generated)
    covariance = sum(
        (old - mean_reference) * (new - mean_generated)
        for old, new in zip(reference, generated, strict=True)
    )
    reference_norm = math.sqrt(sum((value - mean_reference) ** 2 for value in reference))
    generated_norm = math.sqrt(sum((value - mean_generated) ** 2 for value in generated))
    pearson = covariance / (reference_norm * generated_norm)
    return {
        "maximum_absolute_difference": max(abs(value) for value in differences),
        "mean_absolute_difference": sum(abs(value) for value in differences) / len(differences),
        "root_mean_square_difference": math.sqrt(
            sum(value * value for value in differences) / len(differences)
        ),
        "pearson_correlation": pearson,
    }


def compare_author_and_independent(
    author_law: Sequence[CostLawPoint],
    author_pipeline: Sequence[PipelinePoint],
    independent_law: Sequence[CostLawPoint],
    independent_pipeline: Sequence[PipelinePoint],
    *,
    require_threshold_agreement: bool = True,
) -> dict[str, Any]:
    author_law_by_id = {point.circuit: point for point in author_law}
    independent_law_by_id = {point.circuit: point for point in independent_law}
    author_pipeline_by_id = {point.circuit: point for point in author_pipeline}
    independent_pipeline_by_id = {point.circuit: point for point in independent_pipeline}
    circuit_ids = sorted(author_law_by_id)
    _assert_equal(
        set(circuit_ids),
        set(independent_law_by_id),
        "Author/independent cost-law circuit set",
    )
    _assert_equal(
        set(author_pipeline_by_id),
        set(independent_pipeline_by_id),
        "Author/independent pipeline circuit set",
    )

    law_metrics = {}
    for field in ("m", "r", "source_overhead"):
        law_metrics[field] = _series_metrics(
            [float(getattr(author_law_by_id[circuit], field)) for circuit in circuit_ids],
            [float(getattr(independent_law_by_id[circuit], field)) for circuit in circuit_ids],
        )
    pipeline_metrics = {}
    for field in ("convert_only", "polished", "full_anneal", "relative_gap"):
        pipeline_metrics[field] = _series_metrics(
            [float(getattr(author_pipeline_by_id[circuit], field)) for circuit in circuit_ids],
            [float(getattr(independent_pipeline_by_id[circuit], field)) for circuit in circuit_ids],
        )

    near_zero_disagreements = [
        circuit
        for circuit in circuit_ids
        if author_pipeline_by_id[circuit].near_zero
        != independent_pipeline_by_id[circuit].near_zero
    ]
    threshold_disagreements = [
        circuit
        for circuit in circuit_ids
        if author_pipeline_by_id[circuit].below_pipeline_threshold
        != independent_pipeline_by_id[circuit].below_pipeline_threshold
    ]
    if threshold_disagreements and require_threshold_agreement:
        raise ReproductionDataError(
            f"Independent rerun changes the paper threshold classification: {threshold_disagreements}"
        )

    return {
        "schema_version": 1,
        "paper_id": "2608.03987",
        "status": "passed" if not threshold_disagreements else "differences_found",
        "comparison": "author_release_vs_clean_room_reimplementation",
        "circuits": len(circuit_ids),
        "interpretation": (
            "The clean-room optimizer uses the same circuits and numerical search-step "
            "budget but a different tree-search algorithm. Figure 8 is an algebraic "
            "cross-check; Figure 9 differences measure optimizer sensitivity."
        ),
        "figure_8": {
            "series_metrics": law_metrics,
            "overhead_correlation": law_metrics["source_overhead"]["pearson_correlation"],
        },
        "figure_9": {
            "series_metrics": pipeline_metrics,
            "near_zero_status_agreement": len(circuit_ids) - len(near_zero_disagreements),
            "near_zero_status_disagreements": near_zero_disagreements,
            "paper_threshold_status_agreement": (
                len(circuit_ids) - len(threshold_disagreements)
            ),
            "paper_threshold_status_disagreements": threshold_disagreements,
        },
    }


def _plot_style() -> dict[str, Any]:
    return {
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 9.0,
        "axes.labelsize": 10.0,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "axes.linewidth": 0.8,
        "svg.fonttype": "none",
        "svg.hashsalt": "realifytn-2608.03987",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
        "savefig.edgecolor": "white",
    }


def render_figure_8(law_points: Sequence[CostLawPoint]) -> Figure:
    with plt.rc_context(_plot_style()):
        figure, axis = plt.subplots(figsize=(304.063 / 72.0, 231.784 / 72.0))
        figure.subplots_adjust(left=0.165, right=0.97, bottom=0.19, top=0.96)

        x = [index / 400.0 for index in range(401)]
        lower = [1.0 + 2.0 * value for value in x]
        upper = [2.0 + value for value in x]
        axis.fill_between(x, lower, upper, color="#eeeeee", zorder=0)
        axis.plot(x, lower, color="#111111", linewidth=1.25, zorder=1)
        axis.plot(
            x,
            upper,
            color="#111111",
            linewidth=1.25,
            linestyle=(0, (3.2, 2.4)),
            zorder=1,
        )

        for family in FAMILY_ORDER:
            family_points = [point for point in law_points if point.family == family]
            style = FAMILY_STYLES[family]
            axis.scatter(
                [point.m for point in family_points],
                [point.source_overhead for point in family_points],
                s=18 if family != "QAOA" else 20,
                marker=style["marker"],
                color=style["color"],
                edgecolors="white",
                linewidths=0.45,
                label=f"{family} ({len(family_points)})",
                zorder=4,
            )

        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.85, 3.08)
        axis.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        axis.set_yticks([1.0, 1.5, 2.0, 2.5, 3.0])
        axis.grid(axis="y", color="#bdbdbd", linewidth=0.45)
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.set_xlabel(r"merge volume fraction $m$")
        axis.set_ylabel("arithmetic overhead vs. real skeleton")
        axis.legend(loc="upper left", frameon=False, borderaxespad=0.0, handlelength=0.9)

        axis.text(
            0.27,
            2.36,
            r"$2+m\quad(r=1-m)$",
            rotation=17,
            rotation_mode="anchor",
            fontsize=9,
            ha="left",
            va="center",
        )
        axis.text(
            0.59,
            2.04,
            r"$1+2m\quad(r=0)$",
            rotation=34,
            rotation_mode="anchor",
            fontsize=9,
            ha="left",
            va="center",
        )
        axis.text(0.985, 3.055, r"$3\times$ ceiling", ha="right", va="bottom", fontsize=9.5)
        return figure


def render_figure_9(pipeline_points: Sequence[PipelinePoint]) -> Figure:
    random_by_id = {
        point.circuit: point
        for point in pipeline_points
        if point.family == "random"
    }
    missing = [circuit for circuit in RANDOM_PANEL_ORDER if circuit not in random_by_id]
    if missing:
        raise ReproductionDataError(f"Missing Figure 9(a) circuits: {missing}")
    ordered_random = [random_by_id[circuit] for circuit in RANDOM_PANEL_ORDER]

    with plt.rc_context(_plot_style()):
        figure = plt.figure(figsize=(337.283 / 72.0, 395.536 / 72.0))
        grid = figure.add_gridspec(
            2,
            1,
            height_ratios=(4.55, 0.95),
            hspace=0.36,
            left=0.34,
            right=0.97,
            bottom=0.08,
            top=0.84,
        )
        top = figure.add_subplot(grid[0])
        bottom = figure.add_subplot(grid[1])

        y_values = list(range(len(ordered_random)))
        convert_color = FAMILY_STYLES["random"]["color"]
        polish_color = FAMILY_STYLES["QAOA"]["color"]
        anneal_color = FAMILY_STYLES["VQE"]["color"]
        top.scatter(
            [point.convert_only for point in ordered_random],
            y_values,
            s=37,
            marker="o",
            facecolors="none",
            edgecolors=convert_color,
            linewidths=1.2,
            zorder=4,
        )
        top.scatter(
            [point.polished for point in ordered_random],
            y_values,
            s=24,
            marker="s",
            color=polish_color,
            linewidths=0.0,
            zorder=5,
        )
        top.scatter(
            [point.full_anneal for point in ordered_random],
            y_values,
            s=37,
            marker="x",
            color=anneal_color,
            linewidths=1.15,
            zorder=6,
        )
        top.set_yticks(y_values)
        top.set_yticklabels([point.display_name for point in ordered_random])
        top.invert_yaxis()
        top.set_xlim(1.9, 3.31)
        top.set_xticks([2.0, 2.4, 2.8, 3.2])
        top.grid(axis="x", color="#c2c2c2", linewidth=0.45)
        top.axvline(3.0, color="#111111", linestyle=(0, (3, 3)), linewidth=0.9)
        top.text(3.04, -0.82, r"$3\times$ ceiling", ha="left", va="bottom", fontsize=9)
        top.set_xlabel("arithmetic overhead vs. real skeleton")
        top.tick_params(axis="y", length=0, pad=8)
        for spine in top.spines.values():
            spine.set_visible(False)

        legend_handles = [
            Line2D(
                [],
                [],
                marker="o",
                linestyle="none",
                markerfacecolor="none",
                markeredgecolor=convert_color,
                markeredgewidth=1.2,
                markersize=6.5,
                label="convert only",
            ),
            Line2D(
                [],
                [],
                marker="s",
                linestyle="none",
                color=polish_color,
                markersize=5.2,
                label="convert + low-T polish",
            ),
            Line2D(
                [],
                [],
                marker="x",
                linestyle="none",
                color=anneal_color,
                markeredgewidth=1.2,
                markersize=6.2,
                label="full green-aware anneal",
            ),
        ]
        # Matplotlib fills a multi-column legend column-first. This ordering
        # keeps convert/polish on the first row and full anneal on the second,
        # matching the source figure's semantic grouping.
        figure.legend(
            handles=[legend_handles[0], legend_handles[2], legend_handles[1]],
            loc="upper center",
            bbox_to_anchor=(0.64, 0.975),
            ncol=2,
            frameon=False,
            columnspacing=1.8,
            handletextpad=0.45,
            borderaxespad=0.0,
        )
        figure.text(0.285, 0.965, "(a)", ha="center", va="top", fontsize=11, fontweight="bold")

        row_points = {
            family: [point for point in pipeline_points if point.family == family]
            for family in FAMILY_ORDER
        }
        for row_index, family in enumerate(FAMILY_ORDER):
            if row_index % 2 == 0:
                bottom.axhspan(row_index - 0.45, row_index + 0.45, color="#f1f1f1", zorder=0)
            else:
                bottom.axhspan(row_index - 0.45, row_index + 0.45, color="#ededed", zorder=0)
            style = FAMILY_STYLES[family]
            near_zero_count = sum(point.near_zero for point in row_points[family])
            bottom.scatter(
                [0.0],
                [row_index],
                s=27,
                marker="o",
                facecolors="none",
                edgecolors=style["color"],
                linewidths=1.0,
                zorder=3,
            )
            bottom.annotate(
                f"({near_zero_count})",
                (0.0, row_index),
                xytext=(11, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=7.2,
                color="#777777",
            )
            nonzero = [point.relative_gap for point in row_points[family] if not point.near_zero]
            if nonzero:
                bottom.scatter(
                    nonzero,
                    [row_index] * len(nonzero),
                    s=13,
                    marker="o",
                    color=style["color"],
                    linewidths=0.0,
                    zorder=4,
                )

        bottom.set_xscale("symlog", linthresh=1.0e-6, linscale=0.55, base=10)
        bottom.set_xlim(-4.0e-7, 0.35)
        bottom.set_xticks([0.0, 1.0e-5, 1.0e-3, 1.0e-1])
        bottom.set_xticklabels(["0", r"$10^{-5}$", r"$10^{-3}$", r"$10^{-1}$"])
        bottom.set_yticks(list(range(len(FAMILY_ORDER))))
        bottom.set_yticklabels(
            [f"{family} ({EXPECTED_FAMILY_COUNTS[family]})" for family in FAMILY_ORDER]
        )
        bottom.invert_yaxis()
        bottom.tick_params(axis="y", length=0, pad=8)
        bottom.set_xlabel("relative pipeline gap", labelpad=1)
        bottom.axvline(
            PIPELINE_GAP_THRESHOLD,
            color="#111111",
            linestyle=(0, (3, 3)),
            linewidth=0.9,
            zorder=2,
        )
        bottom.text(
            PIPELINE_GAP_THRESHOLD,
            -0.67,
            r"$5\times10^{-4}$",
            ha="center",
            va="bottom",
            fontsize=7.7,
        )
        for spine in bottom.spines.values():
            spine.set_visible(False)
        bottom.text(
            -0.105,
            1.27,
            "(b)",
            transform=bottom.transAxes,
            ha="center",
            va="top",
            fontsize=11,
            fontweight="bold",
        )
        return figure


def _save_figure_bundle(
    figure: Figure,
    stem: str,
    figure_dir: Path,
    *,
    evidence_stage: str,
) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    fixed_time = datetime(2026, 8, 7, tzinfo=timezone.utc)
    outputs = {
        "pdf": figure_dir / f"{stem}.pdf",
        "svg": figure_dir / f"{stem}.svg",
        "png": figure_dir / f"{stem}.png",
        "tiff": figure_dir / f"{stem}.tiff",
    }
    # Backend-specific settings such as svg.hashsalt and svg.fonttype are read
    # at save time, after the render function's rc_context has exited.
    with plt.rc_context(_plot_style()):
        figure.savefig(
            outputs["pdf"],
            metadata={
                "Title": stem,
                "Author": "PRAgent reproduction",
                "Subject": f"arXiv:2608.03987 {evidence_stage}",
                "Creator": "matplotlib",
                "Producer": "matplotlib",
                "CreationDate": fixed_time,
                "ModDate": fixed_time,
            },
        )
        figure.savefig(
            outputs["svg"],
            metadata={
                "Title": stem,
                "Creator": "matplotlib",
                "Description": f"arXiv:2608.03987 {evidence_stage}",
                "Date": "2026-08-07",
            },
        )
        # Matplotlib emits trailing spaces inside SVG path data. They are not
        # semantically meaningful and make repository whitespace validation
        # noisy, so canonicalize lines before hashing the artifact.
        svg_text = outputs["svg"].read_text(encoding="utf-8")
        outputs["svg"].write_text(
            "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
            encoding="utf-8",
        )
        figure.savefig(
            outputs["png"],
            dpi=600,
            metadata={"Software": "matplotlib; PRAgent arXiv:2608.03987"},
        )
        figure.savefig(
            outputs["tiff"],
            dpi=600,
            pil_kwargs={"compression": "tiff_lzw"},
        )
    plt.close(figure)
    return list(outputs.values())


def _artifact_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": file_digest(path, "sha256"),
    }


def run_reproduction(
    archive_path: Path,
    output_root: Path,
    *,
    render: bool = True,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    data_dir = output_root / "data"
    figure_dir = output_root / "figures"
    checks_dir = output_root / "checks"

    archive_info = validate_archive(archive_path)
    author_law = load_cost_law_points(archive_path)
    author_pipeline = load_pipeline_points(archive_path)
    author_check = validate_reproduction(
        author_law,
        author_pipeline,
        archive_info,
        evidence_stage=AUTHOR_EVIDENCE_STAGE,
    )

    reimplementation_dir = data_dir / "independent_python_full"
    reimplementation_complete = len(
        [
            path
            for path in reimplementation_dir.glob("*.json")
            if path.name != "campaign_manifest.json"
        ]
    ) == 67
    random_study_dir = data_dir / "independent_random"
    structured_study_dir = data_dir / "independent_structured"
    independent_complete = (
        len(list(random_study_dir.glob("*.study.json"))) == 12
        and len(list(structured_study_dir.glob("*.study.json"))) == 55
    )
    comparison_check: dict[str, Any] | None = None
    if reimplementation_complete:
        primary_law, primary_pipeline, independent_info = load_reimplementation_points(
            reimplementation_dir
        )
        evidence_stage = REIMPLEMENTATION_EVIDENCE_STAGE
        numerical_check = validate_reproduction(
            primary_law,
            primary_pipeline,
            independent_info,
            evidence_stage=evidence_stage,
        )
        comparison_check = compare_author_and_independent(
            author_law,
            author_pipeline,
            primary_law,
            primary_pipeline,
            require_threshold_agreement=False,
        )
        data_files = write_tidy_data(
            author_law,
            author_pipeline,
            data_dir,
            evidence_stage=AUTHOR_EVIDENCE_STAGE,
            filename_suffix="_author_reference",
        )
    elif independent_complete:
        primary_law, primary_pipeline, independent_info = load_independent_points(
            random_study_dir,
            structured_study_dir,
        )
        evidence_stage = INDEPENDENT_EVIDENCE_STAGE
        numerical_check = validate_reproduction(
            primary_law,
            primary_pipeline,
            independent_info,
            evidence_stage=evidence_stage,
        )
        comparison_check = compare_author_and_independent(
            author_law,
            author_pipeline,
            primary_law,
            primary_pipeline,
        )
        data_files = write_tidy_data(
            author_law,
            author_pipeline,
            data_dir,
            evidence_stage=AUTHOR_EVIDENCE_STAGE,
            filename_suffix="_author_reference",
        )
    else:
        primary_law = author_law
        primary_pipeline = author_pipeline
        evidence_stage = AUTHOR_EVIDENCE_STAGE
        numerical_check = author_check
        data_files = []

    data_files.extend(
        write_tidy_data(
            primary_law,
            primary_pipeline,
            data_dir,
            evidence_stage=evidence_stage,
        )
    )
    figure_files: list[Path] = []
    if render:
        figure_files.extend(
            _save_figure_bundle(
                render_figure_8(primary_law),
                "fig8_cost_law",
                figure_dir,
                evidence_stage=evidence_stage,
            )
        )
        figure_files.extend(
            _save_figure_bundle(
                render_figure_9(primary_pipeline),
                "fig9_pipeline",
                figure_dir,
                evidence_stage=evidence_stage,
            )
        )

    _write_json(checks_dir / "author_artifact_integrity.json", archive_info)
    _write_json(checks_dir / "author_data_validation.json", author_check)
    _write_json(checks_dir / "numerical_feature_checks.json", numerical_check)
    if comparison_check is not None:
        _write_json(checks_dir / "source_comparisons.json", comparison_check)
    generated = [*data_files, *figure_files]
    generation_check = {
        "schema_version": 1,
        "paper_id": "2608.03987",
        "status": "passed",
        "evidence_stage": evidence_stage,
        "rendered": render,
        "artifacts": [_artifact_record(path, output_root) for path in generated],
    }
    _write_json(checks_dir / "plot_generation_check.json", generation_check)

    return {
        "status": (
            "passed"
            if numerical_check["status"] == "passed"
            else "completed_with_differences"
        ),
        "paper_id": "2608.03987",
        "evidence_stage": evidence_stage,
        "circuits": len(primary_law),
        "targets": ["T008", "T009"],
        "data_files": [str(path) for path in data_files],
        "figure_files": [str(path) for path in figure_files],
        "check_files": [
            str(checks_dir / "author_artifact_integrity.json"),
            str(checks_dir / "author_data_validation.json"),
            str(checks_dir / "numerical_feature_checks.json"),
            str(checks_dir / "plot_generation_check.json"),
            *(
                [str(checks_dir / "source_comparisons.json")]
                if comparison_check is not None
                else []
            ),
        ],
    }
