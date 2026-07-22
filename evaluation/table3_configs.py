"""Generate the minimal Table 3 ablation run set and reuse manifest."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "configs" / "source_tasks"
OUTPUT_ROOT = ROOT / "configs" / "table3"

PROFILE_SPECS = {
    "without_goal_reasoning": {"module": "goal", "category": "G", "rerun": ["G1", "G2", "G3", "G4"]},
    "without_intention": {"module": "goal", "category": "G", "rerun": ["G3", "G4"]},
    "without_parameter_binding": {"module": "goal", "category": "G", "rerun": ["G2"]},
    "without_memory": {"module": "memory", "category": "M", "rerun": ["M1", "M2", "M3", "M4"]},
    "without_memory_structure": {"module": "memory", "category": "M", "rerun": ["M2"]},
    "without_state_alignment": {"module": "memory", "category": "M", "rerun": ["M3"]},
    "without_stg_planning": {"module": "stg", "category": "P", "rerun": ["P1", "P2", "P3", "P4"]},
    "without_stg_construction": {"module": "stg", "category": "P", "rerun": ["P1", "P2"]},
    "without_path_merging": {"module": "stg", "category": "P", "rerun": ["P3", "P4"]},
}

# 5 randomly selected tasks per category (seed=42) for cross-category ablation testing
CROSS_CATEGORY_SAMPLES = {
    'G': ['G1_04', 'G1_01', 'G2_09', 'G2_08', 'G4_17'],
    'M': ['M1_05', 'M1_04', 'M4_18', 'M1_03', 'M3_14'],
    'P': ['P1_02', 'P1_01', 'P1_03', 'P2_07', 'P2_08'],
}

CATEGORY_DIR = {"G": "g_class", "M": "m_class", "P": "p_class"}


def source_records(category: str) -> list[tuple[str, Path, dict]]:
    records = []
    for path in sorted((SOURCE_ROOT / CATEGORY_DIR[category]).glob("*.json")):
        config = json.loads(path.read_text(encoding="utf-8"))
        records.append((path.stem, path, config))
    return records


def subclass_of(scenario_id: str) -> str:
    return scenario_id.split("_", 1)[0]


def build_run_config(profile: str, source_id: str, path: Path, source: dict) -> dict:
    spec = PROFILE_SPECS[profile]
    config = copy.deepcopy(source)
    config.update({
        "scenario_id": f"T3_{profile}_{source_id}",
        "source_scenario_id": source_id,
        "table_id": "table3",
        "experiment_axis": "ablation",
        "ablation_profile": profile,
        "ablation_module": spec["module"],
        "table3_source_subclass": subclass_of(source_id),
        "source_config": str(path.relative_to(ROOT)),
        "single_run": True,
        "max_steps": int(source.get("max_steps", 90 if spec["category"] == "P" else 45)),
    })
    if (
        subclass_of(source_id) == "G2"
        and profile in {"without_goal_reasoning", "without_parameter_binding"}
    ):
        config.pop("require_ask_to_pass", None)
    return config


def generate_all() -> tuple[list[tuple[Path, dict]], dict]:
    runs = []
    cells = []
    baseline = []
    all_sources = {category: source_records(category) for category in "GMP"}
    for category, records in all_sources.items():
        for source_id, path, _ in records:
            baseline.append({
                "scenario_id": source_id,
                "category": category,
                "subclass": subclass_of(source_id),
                "source_config": str(path.relative_to(ROOT)),
            })

    for profile, spec in PROFILE_SPECS.items():
        for category, records in all_sources.items():
            for source_id, path, source in records:
                is_target_category = category == spec["category"]
                
                # Determine if this scenario should be re-run as an ablation
                rerun = False
                if is_target_category:
                    rerun = subclass_of(source_id) in spec["rerun"]
                else:
                    # For cross-category testing, run if it is in the fixed sampling list
                    rerun = source_id in CROSS_CATEGORY_SAMPLES[category]
                
                # The cells are populated for all 60 tasks for every profile
                cells.append({
                    "profile": profile,
                    "module": spec["module"],
                    "category": category,
                    "scenario_id": source_id,
                    "subclass": subclass_of(source_id),
                    "result_source": "ablation" if rerun else "baseline",
                })
                
                if rerun:
                    relative = Path(profile) / f"{source_id}.json"
                    runs.append((relative, build_run_config(profile, source_id, path, source)))

    manifest = {
        "table_id": "table3",
        "methods": ["robostate"],
        "baseline": baseline,
        "profiles": {
            profile: {
                "module": spec["module"],
                "category": spec["category"],
                "rerun_subclasses": sorted(spec["rerun"]),
            }
            for profile, spec in PROFILE_SPECS.items()
        },
        "runnable_configs": [
            {
                "profile": config["ablation_profile"],
                "scenario_id": config["scenario_id"],
                "source_scenario_id": config["source_scenario_id"],
                "config_path": str((Path("configs/table3/runs") / relative)),
            }
            for relative, config in runs
        ],
        "cells": cells,
        "expected_runnable_episodes": len(runs),
        "expected_cell_contributions": len(cells),
    }
    return runs, manifest


def validate(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    # Original 105 runs + (9 profiles * 10 cross-category runs) = 195 runs
    if len(runs) != 195:
        raise ValueError(f"Expected 195 runnable Table 3 configs, found {len(runs)}")
    # Now all profiles have all 60 tasks in the manifest
    if len(manifest["cells"]) != 540:
        raise ValueError(f"Table 3 must contain 9 profiles x 60 contributions, found {len(manifest['cells'])}")
    if len(manifest["baseline"]) != 60:
        raise ValueError("Table 3 baseline must contain exactly 60 source scenarios")
    counts = {}
    for _, config in runs:
        profile = config["ablation_profile"]
        counts[profile] = counts.get(profile, 0) + 1
        if config.get("table_id") != "table3" or not config.get("single_run"):
            raise ValueError(f"Invalid Table 3 metadata for {config['scenario_id']}")
    expected = {
        "without_goal_reasoning": 30,
        "without_intention": 20,
        "without_parameter_binding": 15,
        "without_memory": 30,
        "without_memory_structure": 15,
        "without_state_alignment": 15,
        "without_stg_planning": 30,
        "without_stg_construction": 20,
        "without_path_merging": 20,
    }
    if counts != expected:
        raise ValueError(f"Invalid profile distribution: {counts}")


def write_generated(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    run_root = OUTPUT_ROOT / "runs"
    if run_root.exists():
        shutil.rmtree(run_root)
    for relative, config in runs:
        output = run_root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"), nargs="?", default="generate")
    args = parser.parse_args()
    runs, manifest = generate_all()
    validate(runs, manifest)
    if args.command == "generate":
        write_generated(runs, manifest)
    print(
        f"Table 3: {len(runs)} runnable configs; "
        f"{len(manifest['cells'])} row contributions; 60 reused baseline samples"
    )


if __name__ == "__main__":
    main()
