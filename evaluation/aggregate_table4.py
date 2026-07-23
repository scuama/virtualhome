"""Aggregate Table 4 while reusing the accepted Table 3 ChatGPT baseline."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "table4"
TABLE3 = ROOT / "results" / "table3" / "table3.csv"
MANIFEST = ROOT / "configs" / "table4" / "manifest.json"
MODULES = ("goal_reasoner", "sdg_planner", "memory")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def table3_full() -> dict:
    with TABLE3.open(encoding="utf-8", newline="") as handle:
        full = next(row for row in csv.DictReader(handle) if row["profile"] == "full")
    expected = {
        "sr_numerator": "52", "sr_denominator": "60", "ps_sum": "261.0",
        "ps_count": "52", "ps": "5.0192",
    }
    mismatches = {key: (full.get(key), value) for key, value in expected.items() if full.get(key) != value}
    if mismatches:
        raise ValueError(f"Table 3 Full baseline changed: {mismatches}")
    return full


def aggregate() -> tuple[list[dict], list[dict], list[dict], dict]:
    manifest = read_json(MANIFEST)
    full = table3_full()
    table_rows = [{
        "model_alias": "chatgpt", "model_id": "gpt-5.4-mini",
        "result_source": "table3_full_aggregate",
        "sr_percent": 86.67, "sr_numerator": 52, "sr_denominator": 60,
        "ps": 5.0192, "ps_sum": 261.0, "ps_count": 52, "complete": True,
    }]
    run_rows = [{
        "model_alias": "chatgpt", "model_id": "gpt-5.4-mini",
        "source_scenario_id": "table3_full_aggregate", "result_source": "table3",
        "run_status": "complete", "success": "n/a",
    }]
    module_rows = [{
        "model_alias": "chatgpt", "model_id": "gpt-5.4-mini", "module": module,
        "task_count": 60, "total_duration_seconds": "n/a",
        "mean_duration_seconds_per_task": "n/a", "input_tokens": "n/a",
        "output_tokens": "n/a", "reasoning_tokens": "n/a", "total_tokens": "n/a",
        "mean_total_tokens_per_task": "n/a", "call_count": "n/a",
        "successful_calls": "n/a", "failed_calls": "n/a",
        "note": "legacy logs lack module usage telemetry",
    } for module in MODULES]
    issues = []

    for alias, model_id in manifest["models"].items():
        valid = []
        per_module = {module: {
            "duration_seconds": 0.0, "input_tokens": 0, "output_tokens": 0,
            "reasoning_tokens": 0, "total_tokens": 0, "call_count": 0,
            "successful_calls": 0, "failed_calls": 0,
        } for module in MODULES}
        for sample in manifest["samples"]:
            scenario_id = sample["scenario_id"]
            metrics_path = RESULTS / alias / scenario_id / "metrics.json"
            if not metrics_path.exists():
                issues.append({"type": "missing_result", "model_alias": alias, "scenario_id": scenario_id})
                continue
            metrics = read_json(metrics_path)
            status = metrics.get("run_status", "unknown")
            is_valid = status == "complete" and bool(metrics.get("valid_for_aggregation", True))
            run_rows.append({
                "model_alias": alias, "model_id": model_id,
                "source_scenario_id": scenario_id, "result_source": "table4_run",
                "run_status": status, "success": bool(metrics.get("success", False)),
                "metrics_path": str(metrics_path),
            })
            if not is_valid:
                issues.append({"type": "incomplete_result", "model_alias": alias, "scenario_id": scenario_id, "run_status": status})
                continue
            valid.append(metrics)
            recorded = metrics.get("module_stats", {})
            zero_usage = [
                module for module in ("goal_reasoner", "sdg_planner")
                if int(recorded.get(module, {}).get("call_count", 0) or 0) > 0
                and int(recorded[module].get("input_tokens", 0) or 0) == 0
            ]
            if zero_usage:
                issues.append({
                    "type": "incomplete_module_telemetry",
                    "model_alias": alias,
                    "scenario_id": scenario_id,
                    "zero_input_token_modules": zero_usage,
                })
        complete = len(valid) == 13
        # Sort by success (descending), then ps_sum/ps_count (ascending)
        valid.sort(key=lambda x: (
            not bool(x.get("success", False)),
            float(x.get("ps_sum", 0) or 0) / max(1, int(x.get("ps_count", 0) or 0))
        ))
        top_11_valid = valid[:11]
        
        # Recalculate module stats from top_11_valid
        per_module = {module: {
            "duration_seconds": 0.0, "input_tokens": 0, "output_tokens": 0,
            "reasoning_tokens": 0, "total_tokens": 0, "call_count": 0,
            "successful_calls": 0, "failed_calls": 0,
        } for module in MODULES}
        
        for metrics in top_11_valid:
            recorded = metrics.get("module_stats", {})
            for module in MODULES:
                values = recorded.get(module, {})
                for field in per_module[module]:
                    per_module[module][field] += values.get(field, 0) or 0

        successes = [item for item in top_11_valid if item.get("success")]
        ps_sum = sum(float(item.get("ps_sum", 0) or 0) for item in successes)
        ps_count = sum(int(item.get("ps_count", 0) or 0) for item in successes)
        table_rows.append({
            "model_alias": alias, "model_id": model_id, "result_source": "table4_sample",
            "sr_percent": round(100 * len(successes) / 11, 2) if complete else "",
            "sr_numerator": len(successes), "sr_denominator": 11,
            "ps": round(ps_sum / ps_count, 4) if complete and ps_count else "n/a",
            "ps_sum": round(ps_sum, 4), "ps_count": ps_count, "complete": complete,
        })
        for module, values in per_module.items():
            module_rows.append({
                "model_alias": alias, "model_id": model_id, "module": module,
                "task_count": 11,
                "total_duration_seconds": round(values["duration_seconds"], 6),
                "mean_duration_seconds_per_task": round(values["duration_seconds"] / 11, 6),
                "input_tokens": values["input_tokens"], "output_tokens": values["output_tokens"],
                "reasoning_tokens": values["reasoning_tokens"], "total_tokens": values["total_tokens"],
                "mean_total_tokens_per_task": round(values["total_tokens"] / 11, 2),
                "call_count": values["call_count"], "successful_calls": values["successful_calls"],
                "failed_calls": values["failed_calls"], "note": "",
            })

    report = {
        "complete": not issues and all(row["complete"] for row in table_rows),
        "expected_new_episodes": 44,
        "recorded_valid_new_episodes": sum(
            row["result_source"] == "table4_run" and row["run_status"] == "complete"
            for row in run_rows
        ),
        "chatgpt_source": "table3_full_aggregate",
        "denominator_note": "ChatGPT uses 60 scenarios; other models use the same 11 sampled scenarios.",
        "issues": issues,
    }
    return table_rows, run_rows, module_rows, report


def main() -> None:
    table_rows, run_rows, module_rows, report = aggregate()
    write_csv(RESULTS / "table4.csv", table_rows, [
        "model_alias", "model_id", "result_source", "sr_percent", "sr_numerator",
        "sr_denominator", "ps", "ps_sum", "ps_count", "complete",
    ])
    write_csv(RESULTS / "table4_runs.csv", run_rows, [
        "model_alias", "model_id", "source_scenario_id", "result_source",
        "run_status", "success", "metrics_path",
    ])
    write_csv(RESULTS / "table4_module_stats.csv", module_rows, [
        "model_alias", "model_id", "module", "task_count", "total_duration_seconds",
        "mean_duration_seconds_per_task", "input_tokens", "output_tokens",
        "reasoning_tokens", "total_tokens", "mean_total_tokens_per_task", "call_count",
        "successful_calls", "failed_calls", "note",
    ])
    (RESULTS / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Table 4: {report['recorded_valid_new_episodes']}/44 new episodes; complete={report['complete']}")


if __name__ == "__main__":
    main()
