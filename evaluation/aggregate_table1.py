"""Aggregate completed Table 1 runs into table1.csv and completeness_report.json."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "configs" / "table1" / "manifest.json"
DEFAULT_RESULTS = ROOT / "results" / "table1"

AXIS_ORDER = {"scale": 0, "instruction_type": 1, "dynamic_difficulty": 2}
SETTING_ORDER = {
    "S3": 0,
    "S5": 1,
    "S7": 2,
    "sentence_wise": 0,
    "summarized": 1,
    "vague": 2,
    "low": 0,
    "medium": 1,
    "high": 2,
}


def result_path(results_root: Path, entry: dict, method: str) -> Path:
    axis = entry["experiment_axis"]
    if axis == "dynamic_difficulty":
        axis = "dynamic"
    return (
        results_root
        / method
        / axis
        / entry["setting"]
        / entry["sample_id"]
        / "metrics.json"
    )


def expected_task_denominator(entries: list[dict]) -> int:
    return sum(int(entry["task_count"]) for entry in entries)


def aggregate(manifest: dict, results_root: Path, methods: list[str]) -> tuple[list[dict], dict]:
    grouped_entries = {}
    for entry in manifest.get("configs", []):
        key = (entry["experiment_axis"], entry["setting"])
        grouped_entries.setdefault(key, []).append(entry)

    rows = []
    issues = []
    complete_episodes = 0
    expected_episodes = len(manifest.get("configs", [])) * len(methods)

    for (axis, setting), entries in grouped_entries.items():
        for method in methods:
            completed = 0
            total = 0
            ps_sum = 0
            ps_count = 0
            complete_samples = 0
            cell_issues = []
            for entry in entries:
                path = result_path(results_root, entry, method)
                if not path.exists():
                    issue = {
                        "type": "missing",
                        "axis": axis,
                        "setting": setting,
                        "method": method,
                        "sample_id": entry["sample_id"],
                        "metrics_path": str(path),
                    }
                    issues.append(issue)
                    cell_issues.append(issue)
                    continue
                try:
                    metrics = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    issue = {
                        "type": "unreadable",
                        "axis": axis,
                        "setting": setting,
                        "method": method,
                        "sample_id": entry["sample_id"],
                        "metrics_path": str(path),
                        "reason": str(error),
                    }
                    issues.append(issue)
                    cell_issues.append(issue)
                    continue

                reason = metrics.get("reason", "")
                is_agent_failure = any(
                    x in reason for x in ["Agent stagnated", "Agent gave up", "Agent crashed"]
                )

                if not is_agent_failure and (
                    metrics.get("run_status") != "complete"
                    or not metrics.get("valid_for_aggregation", False)
                ):
                    issue = {
                        "type": metrics.get("run_status", "incomplete"),
                        "axis": axis,
                        "setting": setting,
                        "method": method,
                        "sample_id": entry["sample_id"],
                        "metrics_path": str(path),
                        "reason": reason,
                    }
                    issues.append(issue)
                    cell_issues.append(issue)
                    continue

                if metrics.get("scenario_id") != entry["scenario_id"]:
                    issue = {
                        "type": "scenario_mismatch",
                        "axis": axis,
                        "setting": setting,
                        "method": method,
                        "sample_id": entry["sample_id"],
                        "metrics_path": str(path),
                        "expected": entry["scenario_id"],
                        "actual": metrics.get("scenario_id"),
                    }
                    issues.append(issue)
                    cell_issues.append(issue)
                    continue

                complete_samples += 1
                complete_episodes += 1
                completed += int(metrics.get("task_completed", 0))
                total += int(metrics.get("task_total", 0))
                ps_sum += int(metrics.get("ps_sum", 0))
                ps_count += int(metrics.get("ps_count", 0))

            expected_denominator = expected_task_denominator(entries)
            denominator_matches = total == expected_denominator
            if not denominator_matches and not cell_issues:
                issue = {
                    "type": "denominator_mismatch",
                    "axis": axis,
                    "setting": setting,
                    "method": method,
                    "expected_task_denominator": expected_denominator,
                    "actual_task_denominator": total,
                }
                issues.append(issue)
                cell_issues.append(issue)

            rows.append({
                "table_id": "table1",
                "experiment_axis": axis,
                "setting": setting,
                "method": method,
                "sr": round(completed / total, 6) if total else "",
                "sr_percent": round(100 * completed / total, 2) if total else "",
                "sr_numerator": completed,
                "sr_denominator": total,
                "expected_sr_denominator": expected_denominator,
                "ps": round(ps_sum / ps_count, 4) if ps_count else "",
                "ps_sum": ps_sum,
                "ps_count": ps_count,
                "complete_samples": complete_samples,
                "expected_samples": len(entries),
                "complete": not cell_issues and denominator_matches,
            })

    rows.sort(key=lambda row: (
        AXIS_ORDER[row["experiment_axis"]],
        SETTING_ORDER[row["setting"]],
        methods.index(row["method"]),
    ))
    report = {
        "table_id": "table1",
        "complete": not issues and complete_episodes == expected_episodes,
        "methods": methods,
        "expected_configs": len(manifest.get("configs", [])),
        "expected_episodes": expected_episodes,
        "complete_episodes": complete_episodes,
        "missing_or_invalid_episodes": expected_episodes - complete_episodes,
        "complete_cells": sum(1 for row in rows if row["complete"]),
        "expected_cells": len(rows),
        "issues": issues,
    }
    return rows, report


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "table_id", "experiment_axis", "setting", "method", "sr", "sr_percent",
        "sr_numerator", "sr_denominator", "expected_sr_denominator", "ps",
        "ps_sum", "ps_count", "complete_samples", "expected_samples", "complete",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--method", nargs="+", default=None)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    methods = args.method or list(manifest.get("methods", []))
    if not methods:
        raise ValueError("No methods selected for Table 1 aggregation")
    rows, report = aggregate(manifest, args.results_root, methods)
    write_csv(args.output_dir / "table1.csv", rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Table 1 aggregation: {report['complete_episodes']}/"
        f"{report['expected_episodes']} complete episodes; "
        f"{report['complete_cells']}/{report['expected_cells']} complete cells"
    )


if __name__ == "__main__":
    main()
