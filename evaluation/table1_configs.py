"""Generate the 57 Table 1 VirtualHome experiment configurations.

The checked-in source JSON files are the only task-semantic source of truth.
This generator only binds instances, ports declared initial placements to the
selected scene, and adds Table 1 metadata/budgets.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from typing import Iterable

sys.path.append(str(Path(__file__).resolve().parents[1]))


ROOT = Path(__file__).resolve().parent
CONFIGS = ROOT / "configs"
OUTPUT = CONFIGS / "table1"
CATALOG = ROOT.parent / "doc" / "scene_room_objects_catalog.md"

def scene_grounding_candidates(environment_id):
    """Return every object class listed for one scene in the public catalog."""
    text = CATALOG.read_text(encoding="utf-8")
    sections = re.split(r"^## .*?Scene\s+(\d+)\s*$", text, flags=re.MULTILINE)
    scenes = {}
    for index in range(1, len(sections), 2):
        scene_id = int(sections[index])
        scenes[scene_id] = sorted(set(re.findall(
            r"`([a-z0-9_]+)`\s*\(x\d+\)", sections[index + 1]
        )))
    return scenes.get(int(environment_id), [])

DEFAULT_MANIFEST = OUTPUT / "manifest.json"
DEFAULT_UNITY = (
    ROOT.parent / "virtualhome" / "simulation" / "unity_simulator"
    / "macos_exec.v2.3.0.app" / "Contents" / "MacOS" / "VirtualHome"
)

SCALE_GROUPS = {
    "S-G01": {
        "environment_id": 2,
        "anchor": "G1_01",
        "extras": ["E1_01", "E1_03", "E1_04", "E1_07", "E1_11", "E1_15"],
    },
    "S-G02": {
        "environment_id": 0,
        "anchor": "G1_02",
        "extras": ["E1_11", "E1_03", "E1_17", "E1_07", "E1_01", "E1_15"],
    },
    "S-G03": {
        "environment_id": 0,
        "anchor": "G1_03",
        "extras": ["E1_11", "E1_03", "E1_17", "E1_07", "E1_05", "E1_15"],
    },
    "S-G04": {
        "environment_id": 0,
        "anchor": "G1_04",
        "extras": ["E1_01", "E1_03", "E1_11", "E1_07", "E1_17", "E1_15"],
    },
    "S-G05": {
        "environment_id": 0,
        "anchor": "G1_05",
        "extras": ["E1_01", "E1_03", "E1_11", "E1_15", "E1_17", "E1_02"],
    },
}

INSTRUCTION_SAMPLES = [
    "G1_01", "G1_02", "G1_03", "G1_04", "G1_05", "E1_03", "E1_11"
]

INSTRUCTION_TEXT = {
    "G1_01": {
        "summarized": "If milk is in the fridge, heat one cup of it in the microwave.",
        "vague": "If the chilled dairy drink is in cold storage, heat one cup of it in the food-heating appliance.",
    },
    "G1_02": {
        "summarized": "If an apple is on the table, wash it clean and bring it to me.",
        "vague": "If the fruit is on the kitchen surface, wash it clean and bring it to me.",
    },
    "G1_03": {
        "summarized": "When the TV is on, bring its remote control.",
        "vague": "When the entertainment screen is powered, bring its handheld controller.",
    },
    "G1_04": {
        "summarized": "If the table lamp is on, turn it off.",
        "vague": "If the small bedroom light is on, turn it off.",
    },
    "G1_05": {
        "summarized": "Empty the water from the mug and put the mug in the cabinet.",
        "vague": "Empty the water from the drinking cup and place it in the kitchen storage compartment.",
    },
    "E1_03": {
        "summarized": "Move the misplaced book to the sofa.",
        "vague": "Move the misplaced reading item to the main seat.",
    },
    "E1_11": {
        "summarized": "Turn on the inactive computer.",
        "vague": "Power on the inactive workstation device.",
    },
}

DYNAMIC_SAMPLES = [
    "M1_01", "M1_02", "M1_03", "M1_04", "M1_05", "E1_03", "E1_15"
]

DYNAMIC_TARGETS = {
    "M1_01": "remotecontrol",
    "M1_02": "waterglass",
    "M1_03": "waterglass",
    "M1_04": "pillow",
    "M1_05": "milk",
    "E1_03": "book",
    "E1_15": "folder",
}

DIFFICULTY_TRIGGERS = {"low": 1, "medium": 2, "high": 3}
FIXED_SUBJECTS = {
    "cabinet", "closet", "computer", "dishwasher", "microwave", "radio",
    "stove", "tablelamp", "tv", "washingmachine",
}
ROOM_CLASSES = {"bathroom", "bedroom", "diningroom", "kitchen", "livingroom"}
OPPOSITE_STATES = {
    "ON": "OFF",
    "OFF": "ON",
    "OPEN": "CLOSED",
    "CLOSED": "OPEN",
    "PLUGGED_IN": "PLUGGED_OUT",
    "PLUGGED_OUT": "PLUGGED_IN",
    "CLEAN": "DIRTY",
    "DIRTY": "CLEAN",
    "HOT": "COLD",
    "COLD": "HOT",
    "EMPTY": "FILLED_WATER",
}


def source_path(sample_id: str) -> Path:
    if sample_id.startswith("G"):
        folder = "g_class"
    elif sample_id.startswith("M"):
        folder = "m_class"
    elif sample_id.startswith("E"):
        folder = "exrap"
    else:
        raise ValueError(f"Unsupported source sample: {sample_id}")
    return CONFIGS / "source_tasks" / folder / f"{sample_id}.json"


def read_source(sample_id: str) -> dict:
    return json.loads(source_path(sample_id).read_text(encoding="utf-8"))


def scene_classes(environment_id: int) -> set[str]:
    """Read the generated scene inventory used only for availability checks."""
    text = CATALOG.read_text(encoding="utf-8")
    sections = re.split(r"^## .*?Scene\s+(\d+)\s*$", text, flags=re.MULTILINE)
    scenes = {}
    for index in range(1, len(sections), 2):
        scenes[int(sections[index])] = set(re.findall(
            r"`([a-z0-9_]+)`\s*\(x\d+\)", sections[index + 1]
        ))
    if environment_id not in scenes:
        raise ValueError(f"Scene {environment_id} is missing from {CATALOG}")
    return scenes[environment_id]


def bind_condition(condition: dict, sample_id: str | None = None) -> dict:
    result = copy.deepcopy(condition)
    mode = str(result.get("mode", "SINGLE")).upper()
    if mode in {"AND", "OR"}:
        result["conditions"] = [
            bind_condition(item, sample_id) for item in result.get("conditions", [])
        ]
        return result
    if str(result.get("target_class", "ANY")).upper() != "ANY":
        result["target_instance"] = 0
    if result.get("destination_class"):
        # M1_02's JSON intentionally accepts any pourable filled vessel. Table 1
        # locks evaluation to the waterglass instance disturbed by this sample.
        if sample_id == "M1_02" and result["destination_class"] == "ANY":
            result["destination_class"] = "waterglass"
        result["destination_instance"] = 0
    return result


def bind_state_override(override: dict) -> dict:
    result = copy.deepcopy(override)
    result.setdefault("instance_filter", {"index": 0})
    return result


def bind_relation_override(override: dict) -> dict:
    result = copy.deepcopy(override)
    if str(result.get("subject", "")).lower() != "character":
        result.setdefault("subject_instance", 0)
    if result.get("object"):
        result.setdefault("object_instance", 0)
    return result


def force_initially_unsatisfied(condition: dict) -> list[dict]:
    mode = str(condition.get("mode", "SINGLE")).upper()
    if mode == "AND":
        # It is enough to invalidate every invertible leaf. Relation leaves are
        # made false by the source JSON placements below.
        return [
            override
            for item in condition.get("conditions", [])
            for override in force_initially_unsatisfied(item)
        ]
    if mode == "OR":
        return [
            override
            for item in condition.get("conditions", [])
            for override in force_initially_unsatisfied(item)
        ]
    required = [str(value).upper() for value in condition.get("states", [])]
    opposites = [OPPOSITE_STATES[value] for value in required if value in OPPOSITE_STATES]
    if not opposites or str(condition.get("target_class", "ANY")).upper() == "ANY":
        return []
    return [{
        "target_classes": [condition["target_class"]],
        "instance_filter": {"index": int(condition.get("target_instance", 0))},
        "add_states": opposites,
        "remove_states": required,
    }]


def dedupe(items: Iterable[dict]) -> list[dict]:
    result = []
    seen = set()
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(item))
    return result


def condition_classes(condition: dict) -> set[str]:
    mode = str(condition.get("mode", "SINGLE")).upper()
    if mode in {"AND", "OR"}:
        return set().union(*(
            condition_classes(item) for item in condition.get("conditions", [])
        ))
    classes = {
        str(condition.get("target_class", "")).lower(),
        str(condition.get("destination_class", "")).lower(),
    }
    return {value for value in classes if value and value != "any"}


def task_from_source(sample_id: str, source: dict, instruction: str | None = None) -> dict:
    return {
        "task_id": sample_id,
        "instruction": instruction if instruction is not None else source["goal_instruction"],
        "source_scenario": sample_id,
        "success_condition": bind_condition(source["success_condition"], sample_id),
    }


def source_initialization(sample_id: str, source: dict) -> tuple[list[dict], list[dict]]:
    states = [
        bind_state_override(item)
        for item in (source.get("initial_states_override") or [])
    ]
    relations = [
        bind_relation_override(item)
        for item in (source.get("initial_relations_override") or [])
        if str(item.get("subject", "")).lower() not in FIXED_SUBJECTS
    ]
    states.extend(force_initially_unsatisfied(
        bind_condition(source["success_condition"], sample_id)
    ))
    return dedupe(states), dedupe(relations)


def base_metadata(axis: str, sample_id: str, setting: str) -> dict:
    return {
        "table_id": "table1",
        "experiment_axis": axis,
        "sample_id": sample_id,
        "setting": setting,
        "single_run": True,
    }


def build_scale(group_id: str, scale: int) -> dict:
    group = SCALE_GROUPS[group_id]
    source_ids = [group["anchor"], *group["extras"][: scale - 1]]
    sources = [(sample_id, read_source(sample_id)) for sample_id in source_ids]
    tasks = [task_from_source(sample_id, source) for sample_id, source in sources]

    states = []
    movable_relations = []
    anchor_spawn = None
    for sample_id, source in sources:
        source_states, source_relations = source_initialization(sample_id, source)
        states.extend(source_states)
        for relation in source_relations:
            subject = str(relation.get("subject", "")).lower()
            if subject == "character":
                if sample_id == group["anchor"]:
                    anchor_spawn = relation
                continue
            if subject not in FIXED_SUBJECTS:
                movable_relations.append(relation)

    relations = ([anchor_spawn] if anchor_spawn else []) + movable_relations
    scenario_id = f"T1_SCALE_{group_id.replace('-', '')}_S{scale}"
    return {
        "scenario_id": scenario_id,
        "extension_type": "table1_scale",
        **base_metadata("scale", group_id, f"S{scale}"),
        "source_scenarios": source_ids,
        "instruction_scale": scale,
        "instruction_type": "sentence_wise",
        "environment_id": group["environment_id"],
        "goal_instruction": "\n".join(
            f"{index}. {task['instruction']}" for index, task in enumerate(tasks, 1)
        ),
        "tasks": tasks,
        "initial_states_override": dedupe(states),
        "initial_relations_override": dedupe(relations),
        "success_condition": {
            "mode": "AND",
            "conditions": [copy.deepcopy(task["success_condition"]) for task in tasks],
        },
        "max_steps": {3: 45, 5: 75, 7: 105}[scale],
    }


def build_instruction(sample_id: str, instruction_type: str) -> dict:
    source = read_source(sample_id)
    if instruction_type == "sentence_wise":
        instruction = source["goal_instruction"]
    else:
        instruction = INSTRUCTION_TEXT[sample_id][instruction_type]
    states, relations = source_initialization(sample_id, source)
    task = task_from_source(sample_id, source, instruction)
    scenario_id = f"T1_INST_{sample_id}_{instruction_type}"
    is_preprocessed = instruction_type not in ["vague", "summarized"]
    config_dict = {
        "scenario_id": scenario_id,
        "extension_type": "table1_instruction_type",
        **base_metadata("instruction_type", sample_id, instruction_type),
        "source_scenarios": [sample_id],
        "instruction_type": instruction_type,
        "preprocessed_instruction": is_preprocessed,
        "environment_id": int(source["environment_id"]),
        "goal_instruction": instruction,
        "tasks": [task],
        "initial_states_override": states,
        "initial_relations_override": relations,
        "success_condition": copy.deepcopy(task["success_condition"]),
        "max_steps": 45,
    }
    if not is_preprocessed:
        config_dict["grounding_candidates"] = scene_grounding_candidates(int(source["environment_id"]))
    return config_dict


def build_dynamic(sample_id: str, difficulty: str) -> dict:
    source = read_source(sample_id)
    states, relations = source_initialization(sample_id, source)
    task = task_from_source(sample_id, source)
    target = DYNAMIC_TARGETS[sample_id]
    source_events = copy.deepcopy(source.get("dynamic_events") or [])
    if source_events:
        if len(source_events) != 1:
            raise ValueError(f"{sample_id} must declare exactly one source event")
        event = source_events[0]
    else:
        event = {
            "trigger": {"action": "grab", "target": target},
            "effect": {"type": "hide", "target": target, "duration_steps": 3},
        }
    event["event_id"] = f"hide_{target}"
    event["max_triggers"] = DIFFICULTY_TRIGGERS[difficulty]
    event["trigger"]["type"] = "action"
    event["effect"]["duration_steps"] = 3
    event["effect"]["instance_index"] = 0
    scenario_id = f"T1_DYN_{sample_id}_{difficulty}"
    return {
        "scenario_id": scenario_id,
        "extension_type": "table1_dynamic",
        **base_metadata("dynamic_difficulty", sample_id, difficulty),
        "source_scenarios": [sample_id],
        "dynamic_difficulty": difficulty,
        "dynamic_policy": "action_triggered_disturbance_count",
        "dynamic_target": {"class_name": target, "instance_index": 0},
        "environment_id": int(source["environment_id"]),
        "goal_instruction": source["goal_instruction"],
        "tasks": [task],
        "initial_states_override": states,
        "initial_relations_override": relations,
        "success_condition": copy.deepcopy(task["success_condition"]),
        "dynamic_events": [event],
        "max_steps": 45,
    }


def generate_all() -> list[tuple[Path, dict]]:
    generated = []
    for group_id in SCALE_GROUPS:
        for scale in (3, 5, 7):
            config = build_scale(group_id, scale)
            generated.append((OUTPUT / "scale" / f"{config['scenario_id']}.json", config))
    for sample_id in INSTRUCTION_SAMPLES:
        for instruction_type in ("sentence_wise", "summarized", "vague"):
            config = build_instruction(sample_id, instruction_type)
            generated.append((
                OUTPUT / "instruction_type" / f"{config['scenario_id']}.json",
                config,
            ))
    for sample_id in DYNAMIC_SAMPLES:
        for difficulty in ("low", "medium", "high"):
            config = build_dynamic(sample_id, difficulty)
            generated.append((OUTPUT / "dynamic" / f"{config['scenario_id']}.json", config))
    return generated


def validate(configs: list[tuple[Path, dict]]) -> None:
    if len(configs) != 57:
        raise ValueError(f"Expected 57 configs, generated {len(configs)}")
    scenario_ids = [config["scenario_id"] for _, config in configs]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("Generated scenario IDs are not unique")

    counts = {}
    for _, config in configs:
        axis = config["experiment_axis"]
        counts[axis] = counts.get(axis, 0) + 1
        if config.get("table_id") != "table1" or not config.get("single_run"):
            raise ValueError(f"Invalid Table 1 metadata: {config['scenario_id']}")
        if not config.get("tasks") or not config.get("source_scenarios"):
            raise ValueError(f"Missing tasks/source_scenarios: {config['scenario_id']}")
        available = scene_classes(int(config["environment_id"]))
        required = set()
        for relation in config.get("initial_relations_override", []):
            required.add(str(relation.get("subject", "")).lower())
            required.add(str(relation.get("object", "")).lower())
        required.update(condition_classes(config["success_condition"]))
        if config.get("dynamic_target"):
            required.add(str(config["dynamic_target"]["class_name"]).lower())
        required.discard("")
        required.discard("character")
        required.difference_update(ROOM_CLASSES)
        missing = sorted(required - available)
        if missing:
            raise ValueError(
                f"{config['scenario_id']} references classes absent from scene "
                f"{config['environment_id']}: {missing}"
            )
        for task in config["tasks"]:
            condition_text = json.dumps(task["success_condition"])
            if "target_instance" not in condition_text:
                raise ValueError(f"Unbound task target: {config['scenario_id']}")

    if counts != {"scale": 15, "instruction_type": 21, "dynamic_difficulty": 21}:
        raise ValueError(f"Unexpected axis counts: {counts}")

    for group_id in SCALE_GROUPS:
        group_configs = [
            config for _, config in configs
            if config["experiment_axis"] == "scale" and config["sample_id"] == group_id
        ]
        for config in group_configs:
            expected = int(config["setting"][1:])
            if len(config["tasks"]) != expected:
                raise ValueError(f"Scale mismatch: {config['scenario_id']}")
    for _, config in configs:
        if config["experiment_axis"] == "dynamic_difficulty":
            event = config["dynamic_events"][0]
            if event["effect"]["duration_steps"] != 3:
                raise ValueError(f"Wrong hide duration: {config['scenario_id']}")
            if event["max_triggers"] != DIFFICULTY_TRIGGERS[config["setting"]]:
                raise ValueError(f"Wrong trigger count: {config['scenario_id']}")


def build_manifest(configs: list[tuple[Path, dict]]) -> dict:
    entries = []
    for path, config in configs:
        entries.append({
            "scenario_id": config["scenario_id"],
            "experiment_axis": config["experiment_axis"],
            "sample_id": config["sample_id"],
            "setting": config["setting"],
            "config_path": str(path.relative_to(ROOT)),
            "task_count": len(config["tasks"]),
            "max_steps": config["max_steps"],
        })
    return {
        "table_id": "table1",
        "version": 1,
        "single_run": True,
        "methods": ["robostate", "saycan", "llm_planner", "exrap", "flare"],
        "expected_config_count": 57,
        "expected_episode_count": 285,
        "aggregation": {
            "sr": "sum(final_satisfied_tasks) / sum(tasks)",
            "ps": "mean(first_satisfied_step for finally_satisfied_tasks)",
            "incomplete_is_excluded": True,
            "expected_sample_denominators": {
                "scale": {"S3": 15, "S5": 25, "S7": 35},
                "instruction_type": {
                    "sentence_wise": 7, "summarized": 7, "vague": 7,
                },
                "dynamic_difficulty": {"low": 7, "medium": 7, "high": 7},
            },
        },
        "configs": entries,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def checked_in_configs(manifest_path: Path, targets=None):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    configs = []
    for entry in manifest.get("configs", []):
        scenario_id = entry["scenario_id"]
        if targets and not scenario_id.startswith(tuple(targets)):
            continue
        path = ROOT / entry["config_path"]
        configs.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return configs


def validate_generated_files(manifest_path: Path = DEFAULT_MANIFEST):
    generated = generate_all()
    validate(generated)
    checked_in = checked_in_configs(manifest_path)
    generated_by_id = {config["scenario_id"]: config for _, config in generated}
    checked_in_by_id = {config["scenario_id"]: config for _, config in checked_in}
    if generated_by_id != checked_in_by_id:
        raise ValueError(
            "Checked-in Table 1 configs differ from generator output; "
            "run evaluation/table1_configs.py generate"
        )
    return checked_in


def validate_with_unity(configs, unity_path: Path):
    from evaluation.runtime import TaskProgressTracker, check_success
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
    try:
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
                        f"{config['scenario_id']} cannot resolve dynamic target "
                        f"{target}"
                    )
                properties = {
                    str(value).upper()
                    for value in candidates[index].get("properties", [])
                }
                if "GRABBABLE" not in properties:
                    raise ValueError(
                        f"{config['scenario_id']} dynamic target is not "
                        f"grabbable: {target}"
                    )
            print(f"[OK] {config['scenario_id']}: initialized, step-0 false")
    finally:
        env.close()


def write_generated_configs():
    configs = generate_all()
    validate(configs)
    for path, config in configs:
        write_json(path, config)
    write_json(DEFAULT_MANIFEST, build_manifest(configs))
    return configs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate", help="write the 57 checked-in configs")
    validate_parser = subparsers.add_parser("validate", help="validate Table 1")
    validate_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    validate_parser.add_argument("--unity", action="store_true")
    validate_parser.add_argument("--unity-path", type=Path, default=DEFAULT_UNITY)
    validate_parser.add_argument("--target", nargs="*", default=[])
    args = parser.parse_args()

    if args.command == "generate":
        configs = write_generated_configs()
        print(f"Generated and validated {len(configs)} Table 1 configs")
    else:
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
