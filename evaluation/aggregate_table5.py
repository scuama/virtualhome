"""Aggregate the RoboState Table 5 clarification-budget experiment."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "configs" / "table5" / "manifest.json"
RESULTS = ROOT / "results" / "table5" / "robostate"
OUTPUT = ROOT / "results" / "table5"

ASK_RE = re.compile(r"^\s*-\s+\*\*Action\*\*:\s+`\[ask\]", re.MULTILINE)
FINISH_RE = re.compile(r"FINISH \(Goal Reached\)")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_record(source_id: str, manifest: dict):
    relative = manifest.get("legacy_b1_candidates", {}).get(source_id)
    if not relative:
        return None
    path = ROOT / relative
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    asks = len(ASK_RE.findall(text))
    if asks != 1 or not FINISH_RE.search(text):
        return None
    return {
        "source_scenario_id": source_id,
        "clarification_budget": 1,
        "success": True,
        "run_status": "complete",
        "valid_for_aggregation": True,
        "clarification_count": 1,
        "result_source": "legacy_b1_log",
        "evidence_path": str(path),
    }


def _result_record(source_id: str, budget: int):
    path = RESULTS / source_id / f"B{budget}" / "metrics.json"
    if not path.exists():
        return None
    try:
        metrics = _read_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return {
        "source_scenario_id": source_id,
        "clarification_budget": budget,
        "success": bool(metrics.get("success", False)),
        "run_status": metrics.get("run_status", "unknown"),
        "valid_for_aggregation": bool(
            metrics.get("valid_for_aggregation", False)
        ),
        "clarification_count": int(metrics.get("clarification_count", 0)),
        "result_source": "table5_metrics",
        "evidence_path": str(path),
    }


def aggregate(manifest: dict | None = None):
    manifest = manifest or _read_json(MANIFEST_PATH)
    scenarios = [
        item["source_scenario_id"] for item in manifest["scenarios"]
    ]
    run_rows = []
    issues = []
    by_budget = {int(value): [] for value in manifest["budgets"]}

    for source_id in scenarios:
        for budget in manifest["budgets"]:
            budget = int(budget)
            record = _result_record(source_id, budget)
            if record is None and budget == 1:
                record = _legacy_record(source_id, manifest)
            if record is None:
                issues.append({
                    "type": "missing_result",
                    "source_scenario_id": source_id,
                    "clarification_budget": budget,
                })
                run_rows.append({
                    "source_scenario_id": source_id,
                    "clarification_budget": budget,
                    "run_status": "missing",
                    "success": "",
                    "clarification_count": "",
                    "result_source": "",
                    "evidence_path": "",
                })
                continue
            run_rows.append(record)
            if (
                record["run_status"] == "complete"
                and record["valid_for_aggregation"]
            ):
                by_budget[budget].append(record)
            else:
                issues.append({
                    "type": "invalid_result",
                    "source_scenario_id": source_id,
                    "clarification_budget": budget,
                    "run_status": record["run_status"],
                })

    rows = []
    baseline_sr = None
    for budget in sorted(by_budget):
        values = by_budget[budget]
        complete = len(values) == len(scenarios)
        successes = sum(int(item["success"]) for item in values)
        clarification_total = sum(
            item["clarification_count"] for item in values
        )
        sr = successes / len(scenarios) if complete else None
        clar_cost = clarification_total / len(scenarios) if complete else None
        if budget == 0 and complete:
            baseline_sr = sr
        delta_per_clarification = None
        if (
            complete
            and baseline_sr is not None
            and budget > 0
            and clar_cost
        ):
            delta_per_clarification = (
                100.0 * (sr - baseline_sr) / clar_cost
            )
        rows.append({
            "budget": budget,
            "sr": round(sr, 6) if sr is not None else "",
            "sr_percent": round(100 * sr, 2) if sr is not None else "",
            "sr_numerator": successes,
            "sr_denominator": len(scenarios),
            "ClarCost": round(clar_cost, 4) if clar_cost is not None else "",
            "clarification_total": clarification_total,
            "delta_sr_per_clarification": (
                round(delta_per_clarification, 4)
                if delta_per_clarification is not None
                else "n/a"
            ),
            "complete": complete,
        })

    report = {
        "table_id": "table5",
        "expected_cells": len(scenarios) * len(manifest["budgets"]),
        "recorded_complete_cells": sum(len(value) for value in by_budget.values()),
        "complete": not issues and all(row["complete"] for row in rows),
        "issues": issues,
    }
    return rows, run_rows, report


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=OUTPUT,
        help="Directory for table5.csv, table5_runs.csv, and completeness report",
    )
    args = parser.parse_args()
    rows, run_rows, report = aggregate()
    args.output.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output / "table5.csv", rows)
    _write_csv(args.output / "table5_runs.csv", run_rows)
    (args.output / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Table 5: {report['recorded_complete_cells']}/"
        f"{report['expected_cells']} complete cells"
    )


if __name__ == "__main__":
    main()
