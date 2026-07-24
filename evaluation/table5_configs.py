"""Generate the 9-scenario x 4-budget RoboState Table 5 matrix."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "configs" / "source_tasks" / "g_class"
TABLE5_ROOT = ROOT / "configs" / "table5"
NEW_SOURCE_ROOT = TABLE5_ROOT / "sources"
RUN_ROOT = TABLE5_ROOT / "runs"

BUDGETS = (0, 1, 2, 3)
LEGACY_SCENARIOS = ("G2_06", "G2_07", "G2_08", "G2_09", "G2_10")
NEW_SCENARIOS = ("T5_G2_11", "T5_G2_12", "T5_G2_13", "T5_G2_14")
SCENARIOS = (*LEGACY_SCENARIOS, *NEW_SCENARIOS)

LEGACY_INTENTS = {
    "G2_06": "Turn on the table lamp on the coffee table.",
    "G2_07": "Put the mug from the kitchen table inside a kitchen cabinet.",
    "G2_08": "Bring me the hot milk from the kitchen table.",
    "G2_09": "Put all three books from the living-room floor on the living-room desk.",
    "G2_10": "Turn off the stove.",
}

# Only unchanged one-turn results are candidates. The aggregator still checks
# for one successful ask and a FINISH marker before reusing either log.
LEGACY_B1_CANDIDATES = {
    "G2_07": "results/robostate/raw/run_G2_07.md",
    "G2_10": "results/robostate/raw/run_G2_10.md",
}


def source_path(source_id: str) -> Path:
    if source_id in LEGACY_SCENARIOS:
        return SOURCE_ROOT / f"{source_id}.json"
    return NEW_SOURCE_ROOT / f"{source_id}.json"


def _read_source(source_id: str) -> tuple[Path, dict]:
    path = source_path(source_id)
    source = json.loads(path.read_text(encoding="utf-8"))
    if source_id in LEGACY_INTENTS:
        source["simulated_user_intent"] = LEGACY_INTENTS[source_id]
        source.pop("user_clarification_reply", None)
        source.pop("require_ask_to_pass", None)
        source["max_steps"] = max(45, int(source.get("max_steps", 45)))
    if source_id == "G2_08":
        for index, override in enumerate(
            source.get("initial_states_override", [])
        ):
            override.pop("target_index", None)
            override["instance_filter"] = {"index": index}
            if "HOT" in override.get("add_states", []):
                override["remove_states"] = ["COLD"]
            elif "COLD" in override.get("add_states", []):
                override["remove_states"] = ["HOT"]
    if source_id == "G2_09":
        source["success_condition"]["min_count"] = 3
        source["max_steps"] = 60
    if source_id == "G2_06":
        # Table lamps are fixed scene fixtures and cannot be grabbed for a
        # relation override. Start beside the existing bedroom lamp instead.
        source["initial_relations_override"] = [{
            "subject": "character",
            "relation": "INSIDE",
            "object": "bedroom",
        }]
    return path, source


def generate_all() -> tuple[list[tuple[Path, dict]], dict]:
    runs = []
    sources = []
    for source_id in SCENARIOS:
        path, source = _read_source(source_id)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sources.append({
            "source_scenario_id": source_id,
            "source_config": str(path.relative_to(ROOT)),
            "source_sha256": digest,
            "simulated_user_intent": source["simulated_user_intent"],
        })
        for budget in BUDGETS:
            config = copy.deepcopy(source)
            run_prefix = source_id if source_id.startswith("T5_") else f"T5_{source_id}"
            config.update({
                "scenario_id": f"{run_prefix}_B{budget}",
                "source_scenario_id": source_id,
                "source_config": str(path.relative_to(ROOT)),
                "source_sha256": digest,
                "table_id": "table5",
                "experiment_axis": "clarification_budget",
                "sample_id": source_id,
                "setting": f"B{budget}",
                "clarification_budget": budget,
                "evaluation_model": "gpt-5.4-mini",
                "framework_revision": "table5-structured-atomic-sim-user-v2",
                "single_run": True,
            })
            relative = Path(f"B{budget}") / f"{source_id}.json"
            runs.append((relative, config))

    manifest = {
        "table_id": "table5",
        "framework_revision": "table5-structured-atomic-sim-user-v2",
        "method": "robostate",
        "evaluation_model": "gpt-5.4-mini",
        "simulated_user_model": "gpt-5.4-mini",
        "budgets": list(BUDGETS),
        "scenarios": sources,
        "expected_runnable_episodes": len(SCENARIOS) * len(BUDGETS),
        "legacy_b1_candidates": LEGACY_B1_CANDIDATES,
        "runnable_configs": [
            {
                "scenario_id": config["scenario_id"],
                "source_scenario_id": config["source_scenario_id"],
                "clarification_budget": config["clarification_budget"],
                "config_path": str(
                    (Path("configs/table5/runs") / relative).as_posix()
                ),
            }
            for relative, config in runs
        ],
    }
    return runs, manifest


def validate(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    if len(runs) != 36:
        raise ValueError(f"Table 5 must contain 36 configs, found {len(runs)}")
    pairs = {
        (config["source_scenario_id"], config["clarification_budget"])
        for _, config in runs
    }
    if pairs != {(scenario, budget) for scenario in SCENARIOS for budget in BUDGETS}:
        raise ValueError("Every Table 5 scenario must have budgets 0, 1, 2, and 3")
    if any("simulated_user_intent" not in config for _, config in runs):
        raise ValueError("Every Table 5 config needs simulated_user_intent")
    if manifest.get("expected_runnable_episodes") != 36:
        raise ValueError("Table 5 manifest denominator must be 36")


def write_generated(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    if RUN_ROOT.exists():
        shutil.rmtree(RUN_ROOT)
    for relative, config in runs:
        output = RUN_ROOT / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    (TABLE5_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("generate", "validate"), nargs="?", default="generate"
    )
    args = parser.parse_args()
    runs, manifest = generate_all()
    validate(runs, manifest)
    if args.command == "generate":
        write_generated(runs, manifest)
    print("Table 5: 36 configs; 9 scenarios x 4 clarification budgets")


if __name__ == "__main__":
    main()
