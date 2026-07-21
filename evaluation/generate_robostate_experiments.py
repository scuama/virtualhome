"""Generate the five-group RoboState extension benchmark configs."""

import copy
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
CONFIGS = ROOT / "configs"
CATALOG = ROOT.parent / "doc" / "scene_room_objects_catalog.md"

GROUPS = {
    "G01": (2, ["E1_11", "E1_03", "E1_07", "E1_15", "E1_18", "E1_14", "E1_17"]),
    "G02": (2, ["E1_01", "E1_04", "E1_05", "E1_06", "E1_12", "E1_14", "E1_17"]),
    "G03": (2, ["E1_11", "E1_03", "E1_07", "E1_09", "E1_12", "E1_18", "E1_19"]),
    "G04": (0, ["E1_11", "E1_03", "E1_07", "E1_05", "E1_06", "E1_08", "E1_17"]),
    "G05": (1, ["E1_19", "E1_02", "E1_03", "E1_04", "E1_07", "E1_12", "E1_18"]),
}

SUMMARIES = {
    "G01": "Keep the computer on, move any unorganized book to the sofa, and ensure the mug remains on the coffeetable.",
    "G02": "Maintain the living area by keeping the TV on while nobody watches it, leaving the dishwasher open for drying, and keeping the microwave open for maintenance.",
    "G03": "Keep the computer on, return any unorganized book to the sofa, and make sure the mug stays on the coffeetable.",
    "G04": "Keep the computer on, organize any misplaced book on the sofa, and leave the mug on the coffeetable.",
    "G05": "Keep the microwave on, bring any available apple to the desk, and move any unorganized book to the sofa.",
}

VAGUE = {
    "E1_01": "If nobody is watching the entertainment screen, make sure it is powered on.",
    "E1_02": "If you find some fruit, bring it to the work surface.",
    "E1_03": "If you notice something to read left unorganized, bring it to the main place for sitting.",
    "E1_04": "Leave the dish-cleaning appliance open so it can dry.",
    "E1_05": "Leave the food-heating appliance open for maintenance.",
    "E1_07": "Keep the drinking vessel on the small living-room table.",
    "E1_11": "If the workstation device is off, turn it on.",
    "E1_19": "If the food-heating appliance is off, turn it on.",
}

DYNAMIC = {
    "G01": ("computer", ["OFF"], ["ON"]),
    "G02": ("tv", ["OFF"], ["ON"]),
    "G03": ("computer", ["OFF"], ["ON"]),
    "G04": ("computer", ["OFF"], ["ON"]),
    "G05": ("microwave", ["OFF"], ["ON"]),
}

FIXED_SUBJECTS = {
    "cabinet", "closet", "computer", "dishwasher", "microwave", "radio",
    "stove", "tv", "washingmachine",
}

OPPOSITE_STATES = {
    "ON": "OFF",
    "OFF": "ON",
    "OPEN": "CLOSED",
    "CLOSED": "OPEN",
    "PLUGGED_IN": "PLUGGED_OUT",
    "PLUGGED_OUT": "PLUGGED_IN",
    "CLEAN": "DIRTY",
    "DIRTY": "CLEAN",
}


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
    candidates = scenes.get(int(environment_id), [])
    if not candidates:
        raise ValueError(f"Scene {environment_id} is absent from {CATALOG}")
    return candidates


def bind_condition(condition):
    result = copy.deepcopy(condition)
    mode = str(result.get("mode", "SINGLE")).upper()
    if mode in {"AND", "OR"}:
        result["conditions"] = [
            bind_condition(item) for item in result.get("conditions", [])
        ]
        return result
    if str(result.get("target_class", "ANY")).upper() != "ANY":
        result["target_instance"] = 0
    if result.get("destination_class"):
        result["destination_instance"] = 0
    return result


def bind_relation_override(override):
    result = copy.deepcopy(override)
    if str(result.get("subject", "")).lower() != "character":
        result["subject_instance"] = 0
    return result


def force_initially_unsatisfied(condition):
    """Create an instance-bound inverse for simple state goals."""
    mode = str(condition.get("mode", "SINGLE")).upper()
    if mode in {"AND", "OR"}:
        return [
            override
            for item in condition.get("conditions", [])
            for override in force_initially_unsatisfied(item)
        ]
    required = [str(value).upper() for value in condition.get("states", [])]
    opposites = [OPPOSITE_STATES[value] for value in required if value in OPPOSITE_STATES]
    if not opposites:
        return []
    return [{
        "target_classes": [condition["target_class"]],
        "instance_filter": {"index": int(condition.get("target_instance", 0))},
        "add_states": opposites,
        "remove_states": required,
    }]


def read_source(task_id):
    return json.loads((CONFIGS / "ExRAP" / f"{task_id}.json").read_text())


def dedupe(items):
    result = []
    seen = set()
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(copy.deepcopy(item))
    return result


def build(group_id, scale):
    environment_id, ordered_ids = GROUPS[group_id]
    task_ids = ordered_ids[:scale]
    sources = [(task_id, read_source(task_id)) for task_id in task_ids]
    tasks = [
        {
            "task_id": task_id,
            "instruction": source["goal_instruction"],
            "success_condition": bind_condition(source["success_condition"]),
        }
        for task_id, source in sources
    ]
    states = dedupe([
        {
            **copy.deepcopy(override),
            "instance_filter": copy.deepcopy(
                override.get("instance_filter", {"index": 0})
            ),
        }
        for _, source in sources
        for override in (source.get("initial_states_override") or [])
    ] + [
        override
        for task in tasks
        for override in force_initially_unsatisfied(task["success_condition"])
    ])
    relations = [
        bind_relation_override(override)
        for _, source in sources
        for override in (source.get("initial_relations_override") or [])
        if str(override.get("subject", "")).lower() != "character"
        and str(override.get("subject", "")).lower() not in FIXED_SUBJECTS
    ]
    character = next(
        (
            override
            for _, source in sources
            for override in (source.get("initial_relations_override") or [])
            if str(override.get("subject", "")).lower() == "character"
        ),
        None,
    )
    if character:
        relations.insert(0, bind_relation_override(character))
    conditions = [copy.deepcopy(task["success_condition"]) for task in tasks]
    return {
        "scenario_id": f"E_MULTI_{group_id}_S{scale}",
        "extension_type": "multi",
        "experiment_axis": "scale",
        "group_id": group_id,
        "source_scenarios": task_ids,
        "instruction_scale": scale,
        "instruction_type": "sentence_wise",
        "environment_id": environment_id,
        "grounding_candidates": scene_grounding_candidates(environment_id),
        "goal_instruction": "\n".join(
            f"{index}. {task['instruction']}" for index, task in enumerate(tasks, 1)
        ),
        "tasks": tasks,
        "initial_states_override": states,
        "initial_relations_override": dedupe(relations),
        "success_condition": {"mode": "AND", "conditions": conditions},
        "max_steps": {3: 45, 5: 75, 7: 105}[scale],
    }


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=4, ensure_ascii=False) + "\n")


def main():
    for group_id in GROUPS:
        bases = {}
        for scale in (3, 5, 7):
            config = build(group_id, scale)
            bases[scale] = config
            write(CONFIGS / "multi" / f"{config['scenario_id']}.json", config)

        base = bases[3]
        for instruction_type in ("sentence_wise", "summarized", "vague"):
            config = copy.deepcopy(base)
            config["scenario_id"] = f"E_SEM_{group_id}_S3_{instruction_type}"
            config["extension_type"] = "semantic"
            config["experiment_axis"] = "instruction_type"
            config["instruction_type"] = instruction_type
            if instruction_type == "summarized":
                config["goal_instruction"] = SUMMARIES[group_id]
            elif instruction_type == "vague":
                for task in config["tasks"]:
                    task["instruction"] = VAGUE[task["task_id"]]
                config["goal_instruction"] = "\n".join(
                    f"{index}. {task['instruction']}"
                    for index, task in enumerate(config["tasks"], 1)
                )
            write(CONFIGS / "semantic" / f"{config['scenario_id']}.json", config)

        target, add_states, remove_states = DYNAMIC[group_id]
        for difficulty, interval in (("low", 8), ("medium", 6), ("high", 4)):
            config = copy.deepcopy(base)
            config["scenario_id"] = f"E_DYN_{group_id}_S3_{difficulty}"
            config["extension_type"] = "dynamic"
            config["experiment_axis"] = "non_stationarity"
            config["dynamic_difficulty"] = difficulty
            config["dynamic_events"] = [{
                "event_id": f"disturb_{target}",
                "trigger": {
                    "type": "step_interval",
                    "interval_steps": interval,
                    "start_step": interval,
                },
                "effect": {
                    "type": "set_state",
                    "target": target,
                    "instance_index": 0,
                    "add_states": add_states,
                    "remove_states": remove_states,
                },
            }]
            write(CONFIGS / "dynamic" / f"{config['scenario_id']}.json", config)


if __name__ == "__main__":
    main()
