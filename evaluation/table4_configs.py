"""Generate the fixed 44-episode Table 4 model-backbone evaluation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "configs" / "source_tasks"
OUTPUT_ROOT = ROOT / "configs" / "table4"

MODELS = {
    "claude": "anthropic/claude-haiku-4.5",
    "gemini": "google/gemini-3.5-flash",
    "llama": "meta-llama/llama-3.1-8b-instruct",
    "qwen": "qwen/qwen3-8b",
}

SAMPLES = [
    "G2_06", "M2_06", "M4_18", "M4_17", "P2_08", 
    "M1_01", "P2_10", "G2_07", "P3_13", "G3_14", 
    "G4_20", "M2_09", "M1_03"
]


def source_path(scenario_id: str) -> Path:
    category_dir = {"G": "g_class", "M": "m_class", "P": "p_class"}[scenario_id[0]]
    return SOURCE_ROOT / category_dir / f"{scenario_id}.json"


def generate_all() -> tuple[list[tuple[Path, dict]], dict]:
    runs = []
    sources = []
    for scenario_id in SAMPLES:
        path = source_path(scenario_id)
        source = json.loads(path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sources.append({
            "scenario_id": scenario_id,
            "subclass": scenario_id.split("_", 1)[0],
            "source_config": str(path.relative_to(ROOT)),
            "source_sha256": digest,
        })
        for alias, model_id in MODELS.items():
            config = copy.deepcopy(source)
            config.update({
                "scenario_id": f"T4_{alias}_{scenario_id}",
                "source_scenario_id": scenario_id,
                "source_config": str(path.relative_to(ROOT)),
                "source_sha256": digest,
                "table_id": "table4",
                "experiment_axis": "model_backbone",
                "sample_id": scenario_id,
                "model_alias": alias,
                "evaluation_model": model_id,
                "provider": "openrouter",
                "single_run": True,
                "max_steps": int(source.get("max_steps", 90 if scenario_id.startswith("P") else 45)),
            })
            runs.append((Path("runs") / alias / f"{scenario_id}.json", config))
    manifest = {
        "table_id": "table4",
        "sampling_seed": 42,
        "sample_replacements": {
            "G2_06": "G2_08: repeated Unity initialization failure",
            "M2_07": "M2_09: repeated Unity initialization failure",
            "P1_01": "P1_03: source task was already satisfied at step 0",
        },
        "chatgpt": {
            "model_id": "gpt-5.4-mini",
            "result_source": "table3_full_aggregate",
        },
        "models": MODELS,
        "samples": sources,
        "runnable_configs": [
            {
                "model_alias": config["model_alias"],
                "model_id": config["evaluation_model"],
                "source_scenario_id": config["source_scenario_id"],
                "config_path": str((Path("configs/table4") / relative).as_posix()),
            }
            for relative, config in runs
        ],
        "expected_runnable_episodes": 52,
    }
    return runs, manifest


def validate(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    if len(runs) != 52 or manifest.get("expected_runnable_episodes") != 52:
        raise ValueError("Table 4 must contain exactly 52 runnable episodes")
    if len(manifest.get("samples", [])) != 13:
        raise ValueError("Table 4 must contain exactly 13 shared samples")
    pairs = {(config["model_alias"], config["source_scenario_id"]) for _, config in runs}
    expected = {(alias, sample) for alias in MODELS for sample in SAMPLES}
    if pairs != expected:
        raise ValueError("Every Table 4 model must use the same 11 samples")
    if len({item["source_sha256"] for item in manifest["samples"]}) != 13:
        raise ValueError("Source hashes must be recorded for all 13 samples")


def write_generated(runs: list[tuple[Path, dict]], manifest: dict) -> None:
    run_root = OUTPUT_ROOT / "runs"
    if run_root.exists():
        shutil.rmtree(run_root)
    for relative, config in runs:
        output = OUTPUT_ROOT / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"), nargs="?", default="generate")
    args = parser.parse_args()
    runs, manifest = generate_all()
    validate(runs, manifest)
    if args.command == "generate":
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        write_generated(runs, manifest)
    print(f"Table 4: {len(runs)} configs; 4 models x {len(SAMPLES)} shared samples")


if __name__ == "__main__":
    main()
