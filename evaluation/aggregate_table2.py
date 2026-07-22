import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple

DEFAULT_RESULTS = Path("evaluation/results/table2")
DEFAULT_CONFIGS = Path("evaluation/configs/table2")

AXIS_ORDER = {
    "non_stationarity": 0,
    "scale": 1,
    "instruction_type": 2,
}
SETTING_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "S3": 0,
    "S5": 1,
    "S7": 2,
    "sentence_wise": 0,
    "summarized": 1,
    "vague": 2,
}


def result_path(results_root: Path, entry: dict, method: str) -> Path:
    return (
        results_root
        / method
        / entry["experiment_axis"]
        / str(entry["setting"])
        / entry["sample_id"]
        / "metrics.json"
    )


def expected_task_denominator(entries: List[Dict]) -> int:
    return sum(int(entry["task_count"]) for entry in entries)


def build_manifest_entries(configs_root: Path) -> List[Dict]:
    entries: List[Dict] = []
    for path in configs_root.rglob("*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                config = json.load(f)
            axis = config["experiment_axis"]
            if axis == "non_stationarity":
                setting = config["dynamic_difficulty"]
            elif axis == "scale":
                setting = f"S{config['instruction_scale']}"
            elif axis == "instruction_type":
                setting = config["instruction_type"]
            else:
                continue

            # In Table 2, sample_id might just be the scenario_id but split by something?
            # Actually test_runner saves to result_root / method / axis / setting / sample_id / metrics.json
            # Let's just assume sample_id is the scenario_id stem
            sample_id = path.stem
            # Wait, test_runner uses sample_id = config['scenario_id'].split('_')[1] or something?
            # Let's check how test_runner generates paths.
            
            entries.append({
                "scenario_id": config["scenario_id"],
                "experiment_axis": axis,
                "setting": setting,
                "sample_id": sample_id,
                "task_count": len(config.get("tasks", [])),
                "config_path": str(path)
            })
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return entries


def aggregate(configs_root: Path, results_root: Path, methods: List[str]) -> Tuple[List[Dict], Dict]:
    entries_list = build_manifest_entries(configs_root)
    grouped_entries = {}
    for entry in entries_list:
        key = (entry["experiment_axis"], entry["setting"])
        grouped_entries.setdefault(key, []).append(entry)

    rows = []
    issues = []
    complete_episodes = 0
    expected_episodes = len(entries_list) * len(methods)

    for (axis, setting), entries in grouped_entries.items():
        for method in methods:
            completed = 0
            total = 0
            ps_sum = 0
            ps_count = 0
            complete_samples = 0
            cell_issues = []
            for entry in entries:
                # Need to use glob since test_runner might create slightly different sample_id dirs?
                # Actually test_runner might just save to: evaluation/results/table2/{method}/{axis}/{setting}/{scenario_id}/metrics.json
                # Wait, test_runner output path logic:
                # sample_id = config.get("sample_id") or config["scenario_id"]
                # result_dir = root / method / axis / setting / sample_id
                # Let's assume sample_id = scenario_id for Table 2 if sample_id is missing from config
                
                path = results_root / method / axis / str(setting) / entry["scenario_id"] / "metrics.json"
                if not path.exists():
                    issue = {
                        "type": "missing",
                        "axis": axis,
                        "setting": setting,
                        "method": method,
                        "sample_id": entry["scenario_id"],
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
                        "sample_id": entry["scenario_id"],
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
                        "sample_id": entry["scenario_id"],
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
                        "sample_id": entry["scenario_id"],
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
                "table_id": "table2",
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
        "table_id": "table2",
        "complete": not issues and complete_episodes == expected_episodes,
        "methods": methods,
        "expected_configs": len(entries_list),
        "expected_episodes": expected_episodes,
        "complete_episodes": complete_episodes,
        "missing_or_invalid_episodes": expected_episodes - complete_episodes,
        "complete_cells": sum(1 for row in rows if row["complete"]),
        "expected_cells": len(rows),
        "issues": issues,
    }
    return rows, report


def write_csv(path: Path, rows: List[Dict]) -> None:
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
    parser = argparse.ArgumentParser(description="Aggregate Table 2 Results")
    parser.add_argument("--configs-root", type=Path, default=DEFAULT_CONFIGS)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--method", nargs="+", default=["robostate"])
    args = parser.parse_args()

    methods = args.method
    rows, report = aggregate(args.configs_root, args.results_root, methods)
    write_csv(args.output_dir / "table2.csv", rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Table 2 aggregation: {report['complete_episodes']}/"
        f"{report['expected_episodes']} complete episodes; "
        f"{report['complete_cells']}/{report['expected_cells']} complete cells"
    )


if __name__ == "__main__":
    main()
