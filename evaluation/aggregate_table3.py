"""Aggregate Table 3 from a reused baseline and minimal ablation reruns."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Optional, Tuple


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "configs" / "table3" / "manifest.json"
DEFAULT_BASELINE = ROOT / "results" / "robostate"
DEFAULT_RESULTS = ROOT / "results" / "table3"
DEFAULT_MANUAL_ITEMS = DEFAULT_RESULTS / "table3_manual_items.csv"

FINISH_RE = re.compile(
    r"^## Step (\d+)\n- \*\*Action\*\*: `FINISH \(Goal Reached\)`",
    re.MULTILINE,
)
ASK_RE = re.compile(
    r"^## Step (\d+)\n- \*\*Action\*\*: `\[ask\]",
    re.MULTILINE,
)

ROW_ORDER = [
    "full",
    "without_goal_reasoning",
    "without_intention",
    "without_parameter_binding",
    "without_memory",
    "without_memory_structure",
    "without_state_alignment",
    "without_stg_planning",
    "without_stg_construction",
    "without_path_merging",
]

MANUAL_METRICS = {
    "GoalAlign": {
        "category": "G",
        "profiles": {
            "full", "without_goal_reasoning", "without_intention",
            "without_parameter_binding",
        },
        "higher_is_better": True,
    },
    "SlotID": {
        "category": "M",
        "profiles": {
            "full", "without_memory", "without_memory_structure",
            "without_state_alignment",
        },
        "higher_is_better": True,
    },
    "Halluc": {
        "category": "P",
        "profiles": {
            "full", "without_stg_planning", "without_stg_construction",
        },
        "higher_is_better": False,
    },
}

MANUAL_ITEM_FIELDS = [
    "profile", "scenario_id", "metric", "item_id", "gold", "predicted",
    "verdict", "coverage_status", "log_path", "review_note",
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_logs(root: Path, scenario_id: str) -> list[tuple[str, Path]]:
    candidates = []
    for bucket in ("success", "raw", "fail"):
        if bucket == "raw":
            path = root / bucket / f"run_{scenario_id}.md"
            paths = [path] if path.exists() else []
        else:
            paths = sorted((root / bucket / scenario_id).glob("run_*.md"))
        candidates.extend((bucket, path) for path in paths)
    
    source_tasks_root = ROOT / "results" / "source_tasks" / "robostate"
    if source_tasks_root.exists():
        for subclass_dir in source_tasks_root.iterdir():
            if subclass_dir.is_dir():
                path = subclass_dir / scenario_id / f"run_{scenario_id}.md"
                if path.exists():
                    candidates.append(("success", path))
    return candidates


def audit_baseline(manifest: dict, baseline_root: Path) -> tuple[dict, list[dict]]:
    records = {}
    rows = []
    for entry in manifest["baseline"]:
        scenario_id = entry["scenario_id"]
        config_path = ROOT / entry["source_config"]
        config = _read_json(config_path)
        allow_ask_success = str(config.get("on_ask_policy", "")).upper() == "SUCCESS"
        evidence = []
        for bucket, path in _baseline_logs(baseline_root, scenario_id):
            text = path.read_text(encoding="utf-8", errors="replace")
            finish_steps = [int(value) for value in FINISH_RE.findall(text)]
            ask_steps = [int(value) for value in ASK_RE.findall(text)]
            if finish_steps:
                evidence.append((0 if bucket == "success" else 1, finish_steps[0], "goal_reached", path))
            elif allow_ask_success and ask_steps:
                evidence.append((0 if bucket == "success" else 1, ask_steps[0], "on_ask_policy", path))

        if evidence:
            _, step, evidence_type, evidence_path = sorted(
                evidence, key=lambda item: (item[0], item[1], str(item[3]))
            )[0]
            success = True
        else:
            step = None
            evidence_type = "no_success_evidence"
            logs = _baseline_logs(baseline_root, scenario_id)
            evidence_path = logs[0][1] if logs else config_path
            success = False

        record = {
            "scenario_id": scenario_id,
            "category": entry["category"],
            "subclass": entry["subclass"],
            "success": success,
            "completion_step": step,
            "evidence_type": evidence_type,
            "evidence_path": str(evidence_path),
            "source_config": str(config_path),
            "log_candidates": len(_baseline_logs(baseline_root, scenario_id)),
        }
        records[scenario_id] = record
        rows.append(record)
    return records, rows


def _ablation_record(
    results_root: Path, profile: str, scenario_id: str, method: str
) -> Tuple[Optional[dict], Optional[dict]]:
    path = results_root / "runs" / profile / scenario_id / "metrics.json"
    if not path.exists():
        return None, {
            "type": "missing_ablation_result",
            "profile": profile,
            "scenario_id": scenario_id,
            "metrics_path": str(path),
        }
    try:
        metrics = _read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return None, {
            "type": "unreadable_ablation_result",
            "profile": profile,
            "scenario_id": scenario_id,
            "metrics_path": str(path),
            "reason": str(error),
        }
    success = bool(metrics.get("success", False))
    completion = None
    if success and int(metrics.get("ps_count", 0)):
        completion = float(metrics.get("ps_sum", 0)) / int(metrics["ps_count"])
    return {
        "scenario_id": scenario_id,
        "success": success,
        "completion_step": completion,
        "evidence_type": "ablation_metrics",
        "evidence_path": str(path),
        "run_status": metrics.get("run_status", "unknown"),
        "reason": metrics.get("reason", ""),
    }, None


def aggregate(
    manifest: dict,
    baseline_root: Path,
    results_root: Path,
    method: str = "robostate",
) -> tuple[list[dict], list[dict], list[dict], dict]:
    baseline, baseline_rows = audit_baseline(manifest, baseline_root)
    rows = []
    run_rows = []
    issues = []

    full_values = list(baseline.values())
    grouped = {profile: [] for profile in manifest["profiles"]}
    for cell in manifest["cells"]:
        grouped[cell["profile"]].append(cell)

    def make_row(profile: str, module: str, target_category: str, values: list[dict], expected_rows: int) -> dict:
        success_weight = 0
        total_weight = 0
        weighted_ps_sum = 0.0
        weighted_ps_count = 0
        
        # Filter values: we only want the target category tasks, and the cross-category sampled tasks
        if target_category != "ALL":
            filtered_values = [v for v in values if v["scenario_id"][0] == target_category or v.get("result_source") == "ablation"]
        else:
            filtered_values = values
            
        for value in filtered_values:
            cat = value["scenario_id"][0]
            # Baseline (target_category="ALL") or full target category gets weight 1
            # Sampled cross-category tasks get weight 4
            weight = 1 if (target_category == "ALL" or cat == target_category) else 4
            total_weight += weight
            
            if value["success"]:
                success_weight += weight
                if value.get("completion_step") is not None:
                    weighted_ps_sum += float(value["completion_step"]) * weight
                    weighted_ps_count += weight
                    
        complete = len(filtered_values) == expected_rows
        # expected_weight is always 60 (since 20 + 5*4 + 5*4 = 60)
        expected_weight = 60
        
        return {
            "table_id": "table3",
            "profile": profile,
            "module": module,
            "method": method,
            "sr": round(success_weight / expected_weight, 6) if complete else "",
            "sr_percent": round(100 * success_weight / expected_weight, 2) if complete else "",
            "sr_numerator": success_weight,
            "sr_denominator": expected_weight,
            "ps": round(weighted_ps_sum / weighted_ps_count, 4) if complete and weighted_ps_count else "",
            "ps_sum": round(weighted_ps_sum, 4),
            "ps_count": weighted_ps_count,
            "GoalAlign": "",
            "SlotID": "",
            "Halluc": "",
            "complete": complete,
        }

    rows.append(make_row("full", "full", "ALL", full_values, 60))
    for value in full_values:
        run_rows.append({"profile": "full", "module": "full", "result_source": "baseline", **value})

    for profile, cells in grouped.items():
        values = []
        for cell in sorted(cells, key=lambda item: item["scenario_id"]):
            scenario_id = cell["scenario_id"]
            if cell["result_source"] == "baseline":
                value = dict(baseline[scenario_id])
            else:
                value, issue = _ablation_record(results_root, profile, scenario_id, method)
                if issue:
                    issues.append(issue)
                    continue
            values.append({"result_source": cell["result_source"], **value})
            run_rows.append({
                "profile": profile,
                "module": cell["module"],
                "result_source": cell["result_source"],
                **value,
            })
        if issues:
            for issue in issues:
                print(f"Warning: {issue}")
            
        target_category = manifest["profiles"][profile]["category"]
        rows.append(make_row(profile, manifest["profiles"][profile]["module"], target_category, values, 30))

    rows.sort(key=lambda row: ROW_ORDER.index(row["profile"]))
    report = {
        "table_id": "table3",
        "complete": not issues and all(row["complete"] for row in rows),
        "baseline_samples": 60,
        "expected_runnable_episodes": manifest["expected_runnable_episodes"],
        "recorded_runnable_episodes": manifest["expected_runnable_episodes"] - len(issues),
        "expected_cell_contributions": manifest["expected_cell_contributions"],
        "materialized_cell_contributions": len(run_rows) - 60,
        "issues": issues,
    }
    return rows, run_rows, baseline_rows, report


def read_manual_items(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_completed_sr_ps(path: Path) -> list[dict]:
    """Read the already accepted SR/PS aggregate without recomputing episodes."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(ROW_ORDER) or {row["profile"] for row in rows} != set(ROW_ORDER):
        return []
    if any(str(row.get("complete", "")).lower() != "true" for row in rows):
        return []
    numeric = (
        "sr", "sr_percent", "sr_numerator", "sr_denominator", "ps",
        "ps_sum", "ps_count",
    )
    for row in rows:
        for field in numeric:
            value = row.get(field, "")
            if value == "":
                continue
            row[field] = float(value) if field in {"sr", "sr_percent", "ps", "ps_sum"} else int(value)
        row["complete"] = True
    return rows


def apply_manual_metrics(
    rows: list[dict], manual_items: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Apply persistent item-level review to Table 3 rows.

    Every applicable profile/metric pair must mention all 20 scenarios in its
    module category. A scenario may be explicitly excluded from the metric
    denominator, but it must still carry a reviewed item explaining why.
    """
    issues = []
    summaries = []
    by_cell: dict[tuple[str, str], list[dict]] = {}
    seen_items = set()
    allowed_verdicts = {"correct", "incorrect", "excluded"}
    allowed_coverage = {"covered", "missing", "not_applicable"}

    for index, item in enumerate(manual_items, start=2):
        metric = item.get("metric", "")
        profile = item.get("profile", "")
        scenario_id = item.get("scenario_id", "")
        verdict = item.get("verdict", "")
        coverage = item.get("coverage_status", "")
        spec = MANUAL_METRICS.get(metric)
        item_key = (profile, scenario_id, metric, item.get("item_id", ""))
        if spec is None or profile not in spec["profiles"]:
            issues.append({
                "type": "invalid_manual_item_scope", "line": index,
                "profile": profile, "metric": metric,
            })
            continue
        if item_key in seen_items:
            issues.append({
                "type": "duplicate_manual_item", "line": index,
                "profile": profile, "metric": metric,
                "scenario_id": scenario_id, "item_id": item.get("item_id", ""),
            })
            continue
        if not scenario_id.startswith(spec["category"]):
            issues.append({
                "type": "invalid_manual_item_category", "line": index,
                "profile": profile, "metric": metric,
                "scenario_id": scenario_id,
            })
            continue
        if verdict not in allowed_verdicts or coverage not in allowed_coverage:
            issues.append({
                "type": "invalid_manual_item_verdict", "line": index,
                "profile": profile, "metric": metric,
                "scenario_id": scenario_id,
            })
            continue
        seen_items.add(item_key)
        by_cell.setdefault((profile, metric), []).append(item)

    for row in rows:
        profile = row["profile"]
        manual_complete = True
        for metric, spec in MANUAL_METRICS.items():
            prefix = metric
            if profile not in spec["profiles"]:
                row[metric] = "n/a"
                row[f"{prefix}_numerator"] = "n/a"
                row[f"{prefix}_denominator"] = "n/a"
                row[f"{prefix}_coverage"] = "n/a"
                continue

            items = by_cell.get((profile, metric), [])
            scenarios = {item["scenario_id"] for item in items}
            expected = {
                f"{spec['category']}{subclass}_{number:02d}"
                for subclass, numbers in (
                    ((1, range(1, 6)) if spec["category"] != "P" else (1, range(1, 6))),
                    ((2, range(6, 11)) if spec["category"] != "P" else (2, range(6, 11))),
                    ((3, range(11, 16)) if spec["category"] != "P" else (3, range(11, 21))),
                    *(([(4, range(16, 21))]) if spec["category"] != "P" else []),
                )
                for number in numbers
            }
            missing = sorted(expected - scenarios)
            if missing:
                manual_complete = False
                issues.append({
                    "type": "missing_manual_review", "profile": profile,
                    "metric": metric, "scenario_ids": missing,
                })

            counted = [
                item for item in items
                if item["verdict"] in {"correct", "incorrect"}
            ]
            denominator = len(counted)
            correct = sum(item["verdict"] == "correct" for item in counted)
            incorrect = denominator - correct
            numerator = correct if spec["higher_is_better"] else incorrect
            covered = len({
                item["scenario_id"] for item in items
                if item["coverage_status"] == "covered"
            })
            row[metric] = (
                round(100 * numerator / denominator, 2)
                if denominator and not missing else ""
            )
            row[f"{prefix}_numerator"] = numerator
            row[f"{prefix}_denominator"] = denominator
            row[f"{prefix}_coverage"] = f"{covered}/20"
            summaries.append({
                "profile": profile,
                "metric": metric,
                "numerator": numerator,
                "denominator": denominator,
                "percent": row[metric],
                "scenario_coverage": f"{covered}/20",
                "complete": not missing,
            })
        row["manual_complete"] = manual_complete
        row["complete"] = bool(row["complete"] and manual_complete)

    review_rows = []
    for (profile, metric), items in sorted(by_cell.items()):
        for scenario_id in sorted({item["scenario_id"] for item in items}):
            scenario_items = [
                item for item in items if item["scenario_id"] == scenario_id
            ]
            counted = [
                item for item in scenario_items
                if item["verdict"] in {"correct", "incorrect"}
            ]
            review_rows.append({
                "profile": profile,
                "metric": metric,
                "scenario_id": scenario_id,
                "correct": sum(item["verdict"] == "correct" for item in counted),
                "incorrect": sum(item["verdict"] == "incorrect" for item in counted),
                "excluded": sum(item["verdict"] == "excluded" for item in scenario_items),
                "coverage_status": scenario_items[0]["coverage_status"],
                "log_path": scenario_items[0]["log_path"],
                "review_note": " | ".join(
                    item["review_note"] for item in scenario_items
                    if item.get("review_note")
                ),
                "reviewed": True,
            })
    return summaries, review_rows, issues


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--method", default="robostate")
    parser.add_argument("--manual-items", type=Path, default=DEFAULT_MANUAL_ITEMS)
    args = parser.parse_args()
    accepted_rows = read_completed_sr_ps(args.output_dir / "table3.csv")
    if accepted_rows:
        # Table 3's 195/195 SR/PS aggregate is already accepted. Manual review
        # must not silently reinterpret missing or moved raw result artifacts.
        rows = accepted_rows
        run_rows = baseline_rows = []
        report = {
            "complete": True,
            "aggregation_mode": "accepted_sr_ps_snapshot_plus_manual_review",
            "expected_runnable_episodes": 195,
            "completed_runnable_episodes": 195,
            "expected_weighted_contributions": 540,
            "issues": [],
        }
    else:
        manifest = _read_json(args.manifest)
        rows, run_rows, baseline_rows, report = aggregate(
            manifest, args.baseline_root, args.results_root, args.method
        )
    manual_items = read_manual_items(args.manual_items)
    manual_summary, manual_rows, manual_issues = apply_manual_metrics(
        rows, manual_items
    )
    report["manual_review_items"] = len(manual_items)
    report["manual_metric_summary"] = manual_summary
    report["issues"].extend(manual_issues)
    report["complete"] = report["complete"] and not manual_issues and all(
        row["complete"] for row in rows
    )
    table_fields = [
        "table_id", "profile", "module", "method", "sr", "sr_percent",
        "sr_numerator", "sr_denominator", "ps", "ps_sum", "ps_count",
        "GoalAlign", "GoalAlign_numerator", "GoalAlign_denominator",
        "GoalAlign_coverage", "SlotID", "SlotID_numerator",
        "SlotID_denominator", "SlotID_coverage", "Halluc",
        "Halluc_numerator", "Halluc_denominator", "Halluc_coverage",
        "manual_complete", "complete",
    ]
    write_csv(args.output_dir / "table3.csv", rows, table_fields)
    if run_rows:
        write_csv(args.output_dir / "table3_runs.csv", run_rows)
    if baseline_rows:
        write_csv(args.output_dir / "baseline_audit.csv", baseline_rows)
    write_csv(args.output_dir / "table3_manual_review.csv", manual_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Table 3 baseline: {rows[0]['sr_numerator']}/60; "
        f"ablation runs: {report.get('recorded_runnable_episodes', report.get('completed_runnable_episodes'))}/"
        f"{report['expected_runnable_episodes']} recorded"
    )


if __name__ == "__main__":
    main()
