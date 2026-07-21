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

    def make_row(profile: str, module: str, values: list[dict], expected: int) -> dict:
        successes = [value for value in values if value["success"]]
        ps_values = [
            float(value["completion_step"])
            for value in successes
            if value.get("completion_step") is not None
        ]
        complete = len(values) == expected
        return {
            "table_id": "table3",
            "profile": profile,
            "module": module,
            "method": method,
            "sr": round(len(successes) / expected, 6) if complete else "",
            "sr_percent": round(100 * len(successes) / expected, 2) if complete else "",
            "sr_numerator": len(successes),
            "sr_denominator": expected,
            "ps": round(sum(ps_values) / len(ps_values), 4) if complete and ps_values else "",
            "ps_sum": round(sum(ps_values), 4),
            "ps_count": len(ps_values),
            "GoalAlign": "",
            "SlotID": "",
            "Halluc": "",
            "complete": complete,
        }

    rows.append(make_row("full", "full", full_values, 60))
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
            values.append(value)
            run_rows.append({
                "profile": profile,
                "module": cell["module"],
                "result_source": cell["result_source"],
                **value,
            })
        rows.append(make_row(profile, manifest["profiles"][profile]["module"], values, 20))

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


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline-root", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--method", default="robostate")
    args = parser.parse_args()
    manifest = _read_json(args.manifest)
    rows, run_rows, baseline_rows, report = aggregate(
        manifest, args.baseline_root, args.results_root, args.method
    )
    table_fields = [
        "table_id", "profile", "module", "method", "sr", "sr_percent",
        "sr_numerator", "sr_denominator", "ps", "ps_sum", "ps_count",
        "GoalAlign", "SlotID", "Halluc", "complete",
    ]
    write_csv(args.output_dir / "table3.csv", rows, table_fields)
    write_csv(args.output_dir / "table3_runs.csv", run_rows)
    write_csv(args.output_dir / "baseline_audit.csv", baseline_rows)
    manual_rows = [{
        "profile": row["profile"],
        "module": row["module"],
        "scenario_id": row["scenario_id"],
        "result_source": row["result_source"],
        "success": row["success"],
        "completion_step": row.get("completion_step", ""),
        "log_path": row["evidence_path"],
        "GoalAlign": "",
        "SlotID": "",
        "Halluc": "",
        "review_note": "",
        "reviewed": False,
    } for row in run_rows]
    write_csv(args.output_dir / "table3_manual_review.csv", manual_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Table 3 baseline: {rows[0]['sr_numerator']}/60; "
        f"ablation runs: {report['recorded_runnable_episodes']}/"
        f"{report['expected_runnable_episodes']} recorded"
    )


if __name__ == "__main__":
    main()
