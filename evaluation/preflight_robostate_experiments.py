"""Validate the 45 RoboState extension configs before paid agent runs."""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from evaluation.condition_checker import check_success
from evaluation.generate_robostate_experiments import scene_grounding_candidates
from evaluation.test_runner import (
    DynamicEventRuntime,
    apply_overrides,
    ensure_unity_running,
    reset_environment_runtime,
    set_environment_state,
)
from virtualhome.simulation.environment.unity_environment import UnityEnvironment


ROOT = Path(__file__).resolve().parent
CONFIG_ROOT = ROOT / "configs"
CONFIG_DIRS = ("multi", "dynamic", "semantic")
FORBIDDEN_ORDINAL_KEYS = {
    "target_instance", "destination_instance", "subject_instance",
    "object_instance", "instance_index", "instance_filter",
}


class _Logger:
    def info(self, message):
        print(message)


def config_paths():
    return sorted(
        path
        for directory in CONFIG_DIRS
        for path in (CONFIG_ROOT / directory).glob("E_*_G*_*.json")
    )


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate_static(paths=None):
    paths = list(paths or config_paths())
    errors = []
    configs = []
    for path in paths:
        config = json.loads(path.read_text(encoding="utf-8"))
        configs.append((path, config))
        for mapping in _walk(config):
            leaked = FORBIDDEN_ORDINAL_KEYS.intersection(mapping)
            if leaked:
                errors.append(f"{path.name}: hidden ordinal keys {sorted(leaked)}")
        expected_catalog = scene_grounding_candidates(config["environment_id"])
        if config.get("grounding_candidates") != expected_catalog:
            errors.append(f"{path.name}: incomplete grounding catalog")
        for event in config.get("dynamic_events", []):
            effect = event.get("effect", {})
            if effect.get("apply_to") != "all_matching" or not effect.get("match_states"):
                errors.append(f"{path.name}: dynamic event lacks semantic matching")

    axes = Counter(config.get("experiment_axis") for _, config in configs)
    if len(configs) != 45:
        errors.append(f"expected 45 configs, found {len(configs)}")
    if axes != Counter({"scale": 15, "instruction_type": 15, "non_stationarity": 15}):
        errors.append(f"unexpected axis counts: {dict(axes)}")
    if errors:
        raise ValueError("Static preflight failed:\n" + "\n".join(errors))
    return configs


def validate_unity(configs, unity_path):
    def new_environment(force_restart=False):
        ensure_unity_running(unity_path, force_restart=force_restart)
        created = UnityEnvironment(
            num_agents=1,
            observation_types=["partial"],
            executable_args={"file_name": None},
        )
        reset_environment_runtime(created)
        return created

    env = new_environment()
    checked = 0
    try:
        for path, config in configs:
            for attempt in range(2):
                try:
                    env.reset(environment_id=config["environment_id"])
                    reset_environment_runtime(env)
                    apply_overrides(env, config)
                    break
                except Exception:
                    if attempt:
                        raise
                    print(f"[RETRY] {path.stem}: Unity initialization transient")
                    env.close()
                    env = new_environment(force_restart=True)
                    time.sleep(1)
            graph = env.get_graph()
            already_done = [
                task.get("task_id", str(index))
                for index, task in enumerate(config.get("tasks", []), 1)
                if check_success(graph, task.get("success_condition", {}))
            ]
            if already_done:
                raise ValueError(
                    f"{path.name}: task(s) complete at step 0: {already_done}"
                )

            events = config.get("dynamic_events", [])
            if events:
                effect = events[0]["effect"]
                target = str(effect["target"]).lower()
                targets = [
                    node for node in graph.get("nodes", [])
                    if str(node.get("class_name", "")).lower() == target
                ]
                for node in targets:
                    set_environment_state(
                        env,
                        node["id"],
                        effect.get("match_states", []),
                        effect.get("add_states", []),
                    )
                runtime = DynamicEventRuntime(env, events, _Logger())
                start = int(events[0]["trigger"]["start_step"])
                if not runtime.before_step(start):
                    raise ValueError(f"{path.name}: dynamic event changed no target")
                post_event_graph = env.get_graph()
                if any(
                    set(effect.get("match_states", [])).issubset(
                        set(node.get("states", []))
                    )
                    for node in post_event_graph.get("nodes", [])
                    if str(node.get("class_name", "")).lower() == target
                ):
                    raise ValueError(f"{path.name}: dynamic event left completed target")
            checked += 1
            print(f"[OK {checked:02d}/45] {path.stem}")
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", action="store_true", help="also run real Unity checks")
    parser.add_argument(
        "--unity-path",
        default=(
            "/Users/rushy/program/virtualhome/virtualhome/simulation/"
            "unity_simulator/macos_exec.v2.3.0.app/Contents/MacOS/VirtualHome"
        ),
    )
    args = parser.parse_args()
    configs = validate_static()
    print("Static preflight passed: 45 configs")
    if args.unity:
        validate_unity(configs, args.unity_path)
        print("Unity preflight passed: 45 configs")


if __name__ == "__main__":
    main()
