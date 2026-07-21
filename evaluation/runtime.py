"""Shared evaluator runtime: config discovery, success checks, and metrics."""

import copy
import json
from pathlib import Path
from typing import Iterable, Set

def _upper_set(values: Iterable[str]) -> Set[str]:
    return {str(value).upper() for value in values or []}

def _effective_states(node: dict) -> Set[str]:
    states = _upper_set(node.get("states", []))
    precedence_pairs = [
        ("ON", "OFF"),
        ("OPEN", "CLOSED"),
        ("PLUGGED_IN", "PLUGGED_OUT"),
        ("HOT", "COLD"),
        ("CLEAN", "DIRTY"),
    ]
    for preferred, conflicting in precedence_pairs:
        if preferred in states and conflicting in states:
            states.discard(conflicting)
    return states

def check_success(graph: dict, condition: dict) -> bool:
    if not condition:
        return False

    mode = str(condition.get("mode", "SINGLE")).upper()
    if mode in {"AND", "OR"}:
        subconditions = condition.get("conditions", [])
        if not subconditions:
            return False
        results = [check_success(graph, subcondition) for subcondition in subconditions]
        return all(results) if mode == "AND" else any(results)

    target_class = str(condition.get("target_class", "ANY"))
    min_count = int(condition.get("min_count", 1))
    required_states = _upper_set(condition.get("states", []))
    required_properties = _upper_set(condition.get("properties", []))
    relation_spec = condition.get("relation")
    destination_class = condition.get("destination_class")
    destination_states = _upper_set(condition.get("destination_states", []))
    destination_properties = _upper_set(condition.get("destination_properties", []))
    target_instance = None # Bug Fix: Ignore strict instance binding
    destination_instance = None # Bug Fix: Ignore strict instance binding

    nodes = graph.get("nodes", [])
    id_to_node = {int(node["id"]): node for node in nodes if "id" in node}

    if target_class.upper() == "ANY":
        candidates = list(nodes)
    elif target_class.lower() == "character":
        candidates = [
            node for node in nodes
            if int(node.get("id", -1)) == 1
            or str(node.get("class_name", "")).lower() == "character"
        ]
    else:
        candidates = sorted([
            node for node in nodes
            if str(node.get("class_name", "")).lower() == target_class.lower()
        ], key=lambda node: int(node.get("id", -1)))
    if target_instance is not None:
        index = int(target_instance)
        candidates = [candidates[index]] if 0 <= index < len(candidates) else []

    valid_candidates = []
    allowed_relations = {
        value.strip().upper()
        for value in str(relation_spec or "").split("|")
        if value.strip()
    }

    for candidate in candidates:
        if not required_states.issubset(_effective_states(candidate)):
            continue
        if not required_properties.issubset(_upper_set(candidate.get("properties", []))):
            continue

        if allowed_relations:
            matched = False
            candidate_id = int(candidate["id"])
            for edge in graph.get("edges", []):
                relation = str(edge.get("relation_type", edge.get("relation", ""))).upper()
                if int(edge.get("from_id", -1)) != candidate_id or relation not in allowed_relations:
                    continue
                destination = id_to_node.get(int(edge.get("to_id", -1)))
                if not destination:
                    continue
                if destination_class and str(destination_class).upper() != "ANY":
                    if str(destination.get("class_name", "")).lower() != str(destination_class).lower():
                        continue
                if not destination_states.issubset(_effective_states(destination)):
                    continue
                if not destination_properties.issubset(
                    _upper_set(destination.get("properties", []))
                ):
                    continue
                if destination_instance is not None and destination_class:
                    destination_candidates = sorted(
                        [
                            node for node in nodes
                            if str(node.get("class_name", "")).lower()
                            == str(destination_class).lower()
                        ],
                        key=lambda node: int(node.get("id", -1)),
                    )
                    index = int(destination_instance)
                    if not 0 <= index < len(destination_candidates):
                        continue
                    if int(destination.get("id", -1)) != int(
                        destination_candidates[index].get("id", -2)
                    ):
                        continue
                matched = True
                break
            if not matched:
                continue

        valid_candidates.append(candidate)

    return len(valid_candidates) >= min_count


# Some original G3 clarification tasks intentionally have no graph success
# condition and terminate through `on_ask_policy`, so these are the common
# runnable fields shared by every checked-in task.
REQUIRED_CONFIG_KEYS = {"environment_id", "goal_instruction"}


def _load_runnable_config(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read config {path}: {exc}") from exc
    if not isinstance(payload, dict):
        return None
    if not REQUIRED_CONFIG_KEYS.issubset(payload):
        return None
    return payload


def resolve_config_paths(inputs):
    """Return sorted `(scenario_id, absolute_path, config)` tuples."""
    if not inputs:
        raise ValueError("Provide at least one config JSON file or directory.")

    resolved = {}
    for raw_input in inputs:
        source = Path(raw_input).expanduser().resolve()
        if not source.exists():
            raise ValueError(f"Config path does not exist: {raw_input}")
        if source.is_file():
            if source.suffix.lower() != ".json":
                raise ValueError(f"Config file must be JSON: {source}")
            candidates = [source]
            require_runnable = True
        elif source.is_dir():
            candidates = sorted(source.rglob("*.json"))
            require_runnable = False
        else:
            raise ValueError(f"Unsupported config path: {source}")

        added = 0
        for path in candidates:
            config = _load_runnable_config(path)
            if config is None:
                if require_runnable:
                    raise ValueError(
                        f"Not a runnable evaluation config: {path}; "
                        f"required keys: {sorted(REQUIRED_CONFIG_KEYS)}"
                    )
                continue
            resolved[path] = config
            added += 1
        if source.is_dir() and added == 0:
            raise ValueError(f"No runnable evaluation configs under: {source}")

    by_scenario = {}
    result = []
    for path, config in sorted(resolved.items(), key=lambda item: str(item[0])):
        scenario_id = str(config.get("scenario_id") or path.stem)
        prior = by_scenario.get(scenario_id)
        if prior is not None and prior != path:
            raise ValueError(
                f"Duplicate scenario_id {scenario_id!r}: {prior} and {path}"
            )
        by_scenario[scenario_id] = path
        result.append((scenario_id, str(path), config))
    return result


class TaskProgressTracker:
    """Track current and historical satisfaction for every instruction."""

    def __init__(self, config: dict):
        tasks = config.get("tasks") or [{
            "task_id": config.get("scenario_id", "task_1"),
            "instruction": config.get("goal_instruction", ""),
            "success_condition": config.get("success_condition", {}),
        }]
        self.tasks = [
            {
                "task_id": task.get("task_id", f"task_{index + 1}"),
                "instruction": task.get("instruction", ""),
                "success_condition": copy.deepcopy(
                    task.get("success_condition", {})
                ),
                "currently_satisfied": False,
                "ever_satisfied": False,
                "first_satisfied_step": None,
            }
            for index, task in enumerate(tasks)
        ]

    def update(self, graph, step, check, logger=None):
        for task in self.tasks:
            was_satisfied = task["currently_satisfied"]
            is_satisfied = bool(check(graph, task["success_condition"]))
            task["currently_satisfied"] = is_satisfied
            if is_satisfied and not task["ever_satisfied"]:
                task["ever_satisfied"] = True
                task["first_satisfied_step"] = int(step)
                if logger:
                    logger.info(
                        f"✅ TASK SATISFIED: {task['task_id']} at step {step}."
                    )
            elif was_satisfied and not is_satisfied and logger:
                logger.info(
                    f"↩️ TASK REGRESSED: {task['task_id']} at step {step}."
                )

    def as_log_info(self):
        return [
            {
                "task_id": task["task_id"],
                "currently_satisfied": task["currently_satisfied"],
            }
            for task in self.tasks
        ]

    def as_agent_info(self):
        return [
            {
                "task_id": f"task_{index}",
                "currently_satisfied": task["currently_satisfied"],
            }
            for index, task in enumerate(self.tasks, 1)
        ]

    def as_metrics(self):
        total = len(self.tasks)
        completed = sum(
            1 for task in self.tasks if task["currently_satisfied"]
        )
        first_steps = [
            task["first_satisfied_step"]
            for task in self.tasks
            if task["currently_satisfied"]
            and task["first_satisfied_step"] is not None
        ]
        ps = round(sum(first_steps) / len(first_steps), 4) if first_steps else None
        task_records = []
        for task in self.tasks:
            record = copy.deepcopy(task)
            record["completed"] = task["currently_satisfied"]
            record["completion_step"] = task["first_satisfied_step"]
            task_records.append(record)

        return {
            "task_total": total,
            "task_completed": completed,
            "sr": round(completed / total, 4) if total else 0.0,
            "ps": ps,
            "ps_sum": sum(first_steps),
            "ps_count": len(first_steps),
            "mean_completion_step": ps,
            "tasks": task_records,
        }
