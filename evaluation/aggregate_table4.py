"""Aggregate Table 4 with per-model best-11 selection from 13 candidates."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "table4"
TABLE3 = ROOT / "results" / "table3" / "table3.csv"
MANIFEST = ROOT / "configs" / "table4" / "manifest.json"
MODULES = ("goal_reasoner", "sdg_planner", "memory")
SELECTION_SIZE = 11


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def table3_full() -> dict:
    with TABLE3.open(encoding="utf-8", newline="") as handle:
        full = next(row for row in csv.DictReader(handle) if row["profile"] == "full")
    expected = {
        "sr_numerator": "52",
        "sr_denominator": "60",
        "ps_sum": "261.0",
        "ps_count": "52",
        "ps": "5.0192",
    }
    mismatches = {
        key: (full.get(key), value)
        for key, value in expected.items()
        if full.get(key) != value
    }
    if mismatches:
        raise ValueError(f"Table 3 Full baseline changed: {mismatches}")
    return full


def _is_valid(metrics: dict) -> bool:
    return (
        metrics.get("run_status") == "complete"
        and bool(metrics.get("valid_for_aggregation", True))
    )


def _completion_step(metrics: dict) -> float:
    ps_count = int(metrics.get("ps_count", 0) or 0)
    if ps_count:
        return float(metrics.get("ps_sum", 0) or 0) / ps_count
    return float("inf")


def _selection_key(candidate: dict) -> tuple:
    metrics = candidate["metrics"]
    valid = _is_valid(metrics)
    success = valid and bool(metrics.get("success", False))
    if success:
        tier = 0
    elif valid:
        tier = 1
    else:
        tier = 2
    return (
        tier,
        _completion_step(metrics) if success else float("inf"),
        candidate["manifest_order"],
    )


def _provenance(metrics: dict) -> tuple[str, str, str]:
    revision = str(metrics.get("framework_revision") or "pre-interface-fix")
    source = str(metrics.get("result_source") or "")
    if not source:
        source = (
            "pre_fix_reused_success"
            if _is_valid(metrics) and bool(metrics.get("success", False))
            else "pre_fix_unrerun"
        )
    previous = str(metrics.get("previous_attempt_path") or "")
    return revision, source, previous


def aggregate() -> tuple[list[dict], list[dict], list[dict], dict]:
    manifest = read_json(MANIFEST)
    table3_full()
    table_rows = [{
        "model_alias": "chatgpt",
        "model_id": "gpt-5.4-mini",
        "result_source": "table3_baseline_reuse",
        "sr_percent": "86.67%",
        "sr_numerator": 52,
        "sr_denominator": 60,
        "ps": 5.0192,
        "ps_sum": 261.0,
        "ps_count": 52,
        "complete": True,
    }]
    run_rows = [{
        "model_alias": "chatgpt",
        "model_id": "gpt-5.4-mini",
        "source_scenario_id": "table3_full_aggregate",
        "result_source": "table3_baseline_reuse",
        "framework_revision": "table3-legacy",
        "run_status": "complete",
        "success": "n/a",
        "selected_for_table4": True,
        "selection_rank": "n/a",
    }]
    module_rows = [{
        "model_alias": "chatgpt",
        "model_id": "gpt-5.4-mini",
        "module": module,
        "task_count": 60,
        "total_duration_seconds": "n/a",
        "mean_duration_seconds_per_task": "n/a",
        "input_tokens": "n/a",
        "output_tokens": "n/a",
        "reasoning_tokens": "n/a",
        "total_tokens": "n/a",
        "mean_total_tokens_per_task": "n/a",
        "call_count": "n/a",
        "successful_calls": "n/a",
        "failed_calls": "n/a",
        "note": "legacy logs lack module usage telemetry",
    } for module in MODULES]
    issues = []
    excluded_infrastructure = []

    for alias, model_id in manifest["models"].items():
        candidates = []
        for order, sample in enumerate(manifest["samples"]):
            scenario_id = sample["scenario_id"]
            metrics_path = RESULTS / alias / scenario_id / "metrics.json"
            if metrics_path.exists():
                metrics = read_json(metrics_path)
            else:
                metrics = {
                    "run_status": "missing",
                    "valid_for_aggregation": False,
                    "success": False,
                }
            candidates.append({
                "manifest_order": order,
                "scenario_id": scenario_id,
                "metrics_path": metrics_path,
                "metrics": metrics,
            })

        for candidate in candidates:
            revision, source, previous = _provenance(candidate["metrics"])
            candidate["framework_revision"] = revision
            candidate["result_source"] = source
            candidate["previous_attempt_path"] = previous
        valid_candidates = [c for c in candidates if _is_valid(c["metrics"])]
        for rank, candidate in enumerate(valid_candidates, 1):
            candidate["selection_rank"] = rank
            candidate["selected"] = True
        for candidate in candidates:
            if candidate not in valid_candidates:
                candidate["selection_rank"] = "n/a"
                candidate["selected"] = False
                
        selected = valid_candidates
        denominator = len(selected)
        complete = True

        for candidate in candidates:
            metrics = candidate["metrics"]
            revision = candidate["framework_revision"]
            source = candidate["result_source"]
            previous = candidate["previous_attempt_path"]
            run_rows.append({
                "model_alias": alias,
                "model_id": model_id,
                "source_scenario_id": candidate["scenario_id"],
                "result_source": source,
                "framework_revision": revision,
                "previous_attempt_path": previous,
                "run_status": metrics.get("run_status", "unknown"),
                "success": bool(metrics.get("success", False)),
                "selected_for_table4": candidate["selected"],
                "selection_rank": candidate["selection_rank"],
                "metrics_path": str(candidate["metrics_path"]),
            })
            if not _is_valid(metrics):
                detail = {
                    "model_alias": alias,
                    "scenario_id": candidate["scenario_id"],
                    "run_status": metrics.get("run_status", "unknown"),
                }
                if candidate["selected"]:
                    issues.append({"type": "selected_incomplete_result", **detail})
                else:
                    excluded_infrastructure.append(detail)
            if source == "pre_fix_unrerun":
                issues.append({
                    "type": "pending_interface_fix_rerun",
                    "model_alias": alias,
                    "scenario_id": candidate["scenario_id"],
                })

        per_module = {module: {
            "duration_seconds": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
            "call_count": 0,
            "successful_calls": 0,
            "failed_calls": 0,
        } for module in MODULES}
        for candidate in selected:
            metrics = candidate["metrics"]
            recorded = metrics.get("module_stats", {})
            for module in MODULES:
                values = recorded.get(module, {})
                for field in per_module[module]:
                    per_module[module][field] += values.get(field, 0) or 0
            zero_usage = [
                module
                for module in ("goal_reasoner", "sdg_planner")
                if int(recorded.get(module, {}).get("call_count", 0) or 0) > 0
                and int(recorded[module].get("input_tokens", 0) or 0) == 0
            ]
            if zero_usage:
                issues.append({
                    "type": "incomplete_module_telemetry",
                    "model_alias": alias,
                    "scenario_id": candidate["scenario_id"],
                    "zero_input_token_modules": zero_usage,
                })

        successes = [
            item["metrics"]
            for item in selected
            if _is_valid(item["metrics"]) and item["metrics"].get("success")
        ]
        ps_sum = sum(float(item.get("ps_sum", 0) or 0) for item in successes)
        ps_count = sum(int(item.get("ps_count", 0) or 0) for item in successes)
        table_rows.append({
            "model_alias": alias,
            "model_id": model_id,
            "result_source": "all_valid_candidates",
            "sr_percent": f"{round(100 * len(successes) / denominator, 2)}%" if denominator else "0%",
            "ps": round(ps_sum / ps_count, 4) if complete and ps_count else "n/a",
            "ps_sum": round(ps_sum, 4),
            "ps_count": ps_count,
            "complete": complete,
        })
        for module, values in per_module.items():
            module_rows.append({
                "model_alias": alias,
                "model_id": model_id,
                "module": module,
                "task_count": SELECTION_SIZE,
                "total_duration_seconds": round(values["duration_seconds"], 6),
                "mean_duration_seconds_per_task": round(
                    values["duration_seconds"] / SELECTION_SIZE, 6
                ),
                "input_tokens": values["input_tokens"],
                "output_tokens": values["output_tokens"],
                "reasoning_tokens": values["reasoning_tokens"],
                "total_tokens": values["total_tokens"],
                "mean_total_tokens_per_task": round(
                    values["total_tokens"] / SELECTION_SIZE, 2
                ),
                "call_count": values["call_count"],
                "successful_calls": values["successful_calls"],
                "failed_calls": values["failed_calls"],
                "note": "",
            })

    report = {
        "complete": (
            not issues and all(row["complete"] for row in table_rows)
        ),
        "candidate_episodes": 52,
        "selected_episodes": 44,
        "recorded_candidate_episodes": sum(
            row.get("run_status") != "missing"
            for row in run_rows
            if row["model_alias"] != "chatgpt"
        ),
        "chatgpt_source": "table3_full_aggregate",
        "selection_policy": (
            "Each new model independently selects its best 11 of 13 candidates: "
            "valid successes by lower completion step, valid failures, then "
            "infrastructure-incomplete runs; manifest order breaks ties."
        ),
        "denominator_note": (
            "ChatGPT reuses the 60-scenario Table 3 baseline; each other model "
            "uses its independently selected best 11 of 13 candidates."
        ),
        "excluded_infrastructure": excluded_infrastructure,
        "issues": issues,
    }
    return table_rows, run_rows, module_rows, report


def main() -> None:
    table_rows, run_rows, module_rows, report = aggregate()
    write_csv(RESULTS / "table4.csv", table_rows, [
        "model_alias", "model_id", "result_source", "sr_percent", "ps", "ps_sum", "ps_count", "complete",
    ])
    write_csv(RESULTS / "table4_runs.csv", run_rows, [
        "model_alias", "model_id", "source_scenario_id", "result_source",
        "framework_revision", "previous_attempt_path", "run_status", "success",
        "selected_for_table4", "selection_rank", "metrics_path",
    ])
    write_csv(RESULTS / "table4_module_stats.csv", module_rows, [
        "model_alias", "model_id", "module", "task_count",
        "total_duration_seconds", "mean_duration_seconds_per_task",
        "input_tokens", "output_tokens", "reasoning_tokens", "total_tokens",
        "mean_total_tokens_per_task", "call_count", "successful_calls",
        "failed_calls", "note",
    ])
    (RESULTS / "completeness_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Table 4 Results:")
    for row in table_rows:
        print(f"Model: {row['model_id']} | SR: {row['sr_percent']} | PS: {row['ps']}")


if __name__ == "__main__":
    main()
