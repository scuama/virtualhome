import re
from typing import Set, Dict, Iterable

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
    target_instance = condition.get("target_instance")
    destination_instance = condition.get("destination_instance")

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
