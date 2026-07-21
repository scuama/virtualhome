"""Validate checked-in Table 1 configs, optionally against live Unity scenes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from evaluation.condition_checker import check_success
from evaluation.generate_table1_experiments import generate_all, validate
from evaluation.task_progress import TaskProgressTracker


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "configs" / "table1" / "manifest.json"
DEFAULT_UNITY = (
    ROOT.parent
    / "virtualhome"
    / "simulation"
    / "unity_simulator"
    / "macos_exec.v2.3.0.app"
    / "Contents"
    / "MacOS"
    / "VirtualHome"
)


def checked_in_configs(manifest_path: Path, targets: list[str]) -> list[tuple[Path, dict]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    configs = []
    for entry in manifest.get("configs", []):
        scenario_id = entry["scenario_id"]
        if targets and not scenario_id.startswith(tuple(targets)):
            continue
        path = ROOT / entry["config_path"]
        configs.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return configs


def validate_generated_files(manifest_path: Path) -> None:
    generated = generate_all()
    validate(generated)
    checked_in = checked_in_configs(manifest_path, [])
    generated_by_id = {config["scenario_id"]: config for _, config in generated}
    checked_in_by_id = {config["scenario_id"]: config for _, config in checked_in}
    if generated_by_id != checked_in_by_id:
        raise ValueError(
            "Checked-in Table 1 configs differ from generator output; "
            "run evaluation/generate_table1_experiments.py"
        )


def validate_with_unity(
    configs: list[tuple[Path, dict]], unity_path: Path
) -> None:
    from evaluation.test_runner import (
        apply_overrides,
        ensure_unity_running,
        reset_environment_runtime,
    )
    from virtualhome.simulation.environment.unity_environment import UnityEnvironment

    ensure_unity_running(str(unity_path))
    env = UnityEnvironment(
        num_agents=1,
        observation_types=["partial"],
        executable_args={"file_name": None},
    )
    for _, config in configs:
        reset_environment_runtime(env)
        env.reset(environment_id=int(config["environment_id"]))
        apply_overrides(env, config, debug=False)
        graph = env.get_graph()
        tracker = TaskProgressTracker(config)
        tracker.update(graph, 0, check_success)
        initially_satisfied = [
            task["task_id"] for task in tracker.tasks
            if task["currently_satisfied"]
        ]
        if initially_satisfied:
            raise ValueError(
                f"{config['scenario_id']} is satisfied at step 0: "
                f"{initially_satisfied}"
            )

        if config.get("experiment_axis") == "dynamic_difficulty":
            target = config["dynamic_target"]
            candidates = sorted(
                [
                    node for node in graph.get("nodes", [])
                    if str(node.get("class_name", "")).lower()
                    == target["class_name"]
                ],
                key=lambda node: int(node.get("id", -1)),
            )
            index = int(target["instance_index"])
            if index >= len(candidates):
                raise ValueError(
                    f"{config['scenario_id']} cannot resolve dynamic target {target}"
                )
            properties = {
                str(value).upper() for value in candidates[index].get("properties", [])
            }
            if "GRABBABLE" not in properties:
                raise ValueError(
                    f"{config['scenario_id']} dynamic target is not grabbable: "
                    f"{target}"
                )
        print(f"[OK] {config['scenario_id']}: initialized, step-0 false")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--unity", action="store_true")
    parser.add_argument("--unity-path", type=Path, default=DEFAULT_UNITY)
    parser.add_argument("--target", nargs="*", default=[])
    args = parser.parse_args()

    validate_generated_files(args.manifest)
    configs = checked_in_configs(args.manifest, args.target)
    if args.unity:
        validate_with_unity(configs, args.unity_path)
    print(
        f"Validated Table 1 files; selected={len(configs)}, "
        f"unity={'yes' if args.unity else 'no'}"
    )


if __name__ == "__main__":
    main()
