import json
import re
from ..utils.llm_client import LLMClient
from .prompt_templates import SDG_SYSTEM_PROMPT, SDG_USER_PROMPT
from .ablation import get_ablation_policy
from .class_resolver import (
    STATE_MODIFIERS,
    instruction_scene_classes,
    resolve_scene_class,
)

class SDGPlanner:
    NODE_TYPES = {"state", "relation"}
    STATE_VALUES = {
        "BROKEN", "CLEAN", "CLOSED", "COLD", "DIRTY", "EMPTY",
        "FILLED", "FILLED_WATER", "FILLED_JUICE", "HELD", "HOT", "OFF", "ON",
        "OPEN", "PLUGGED_IN", "SLICED", "UNPLUGGED",
    }
    RELATIONS = {
        "CLOSE", "HELD", "HOLDS", "HOLDS_LH", "HOLDS_RH", "INSIDE", "ON",
    }
    NON_SCENE_REFERENTS = {"agent", "character", "robot", "self", "user"}

    def __init__(self, llm_client: LLMClient, logger, ablation_profile="full"):
        self.llm = llm_client
        self.logger = logger
        self.current_sdg = None
        self.policy = get_ablation_policy(ablation_profile)

    def generate_sdg(self, goal_description: str, scene_classes=None) -> dict:
        scene_classes = sorted({
            str(value).strip().lower()
            for value in (scene_classes or [])
            if str(value).strip()
        })
        if not self.policy.stg_planning:
            return {"planning_ablation": "no_stg_planning"}
        if not self.policy.stg_construction:
            checklist = self.llm.generate_json(
                system_prompt=(
                    "Turn the embodied household instruction into a short, ordered, flat "
                    "action checklist. Do not create graph nodes, dependencies, or edges. "
                    "Return JSON as {\"checklist\": [\"step\"]}."
                ),
                user_prompt=f"Task: {goal_description}",
                module_name="sdg_planner",
            )
            result = {
                "planning_ablation": "flat_checklist",
                "checklist": list(checklist.get("checklist", [])),
            }
            self.current_sdg = result
            return result
        validation_errors = []
        for attempt in range(2):
            user_prompt = SDG_USER_PROMPT.format(
                goal_description=goal_description
            )
            user_prompt += (
                "\nObserved scene class catalog (use these exact names for every "
                f"concrete object): {json.dumps(scene_classes)}"
                "\nAllowed node types: State, Relation."
                f"\nAllowed state values: {json.dumps(sorted(self.STATE_VALUES))}; "
                "FILLED_<LIQUID> is also allowed."
                f"\nAllowed relations: {json.dumps(sorted(self.RELATIONS))}."
            )
            if validation_errors:
                user_prompt += (
                    "\nYour previous SDG was rejected. Correct every error and return "
                    "the complete SDG again:\n- "
                    + "\n- ".join(validation_errors)
                )
            sdg_data = self.llm.generate_json(
                system_prompt=SDG_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                module_name="sdg_planner",
            )
            canonical, validation_errors = self.validate_sdg(
                sdg_data, goal_description, scene_classes
            )
            if canonical is not None:
                self.current_sdg = canonical
                if self.logger:
                    self.logger.log_info(
                        f"Generated SDG with {len(canonical.get('nodes', []))} "
                        f"nodes after {attempt + 1} attempt(s)."
                    )
                return canonical
            if self.logger:
                self.logger.log_error(
                    "SDG semantic validation failed: "
                    + "; ".join(validation_errors)
                )
        return None

    @classmethod
    def validate_sdg(cls, payload, instruction, scene_classes):
        errors = []
        if not isinstance(payload, dict):
            return None, ["top-level output must be an object"]
        nodes = payload.get("nodes")
        edges = payload.get("edges")
        if not isinstance(nodes, list) or not nodes:
            errors.append("nodes must be a non-empty list")
            nodes = []
        if not isinstance(edges, list):
            errors.append("edges must be a list")
            edges = []

        canonical_nodes = []
        node_ids = []
        semantic_signatures = set()
        mentioned_classes = set()
        for index, raw_node in enumerate(nodes):
            if not isinstance(raw_node, dict):
                errors.append(f"node {index} must be an object")
                continue
            node = dict(raw_node)
            node_id = str(node.get("id", "")).strip()
            node_type = str(node.get("type", "")).strip().lower()
            if not node_id:
                errors.append(f"node {index} has no id")
            elif node_id in node_ids:
                errors.append(f"duplicate node id {node_id}")
            node_ids.append(node_id)
            if node_type not in cls.NODE_TYPES:
                errors.append(f"node {node_id or index} has unsupported type {node_type!r}")

            for key in ("object", "target"):
                value = str(node.get(key, "")).strip()
                if not value or value.startswith("?"):
                    continue
                if value.lower() in cls.NON_SCENE_REFERENTS:
                    node[key] = value.lower()
                    continue
                suffix = ""
                suffix_match = re.search(r"(_\d+)$", value)
                if suffix_match:
                    suffix = suffix_match.group(1)
                resolved = resolve_scene_class(value, scene_classes)
                if not resolved:
                    errors.append(
                        f"node {node_id or index} {key} {value!r} does not "
                        "resolve uniquely to the scene class catalog"
                    )
                    continue
                mentioned_classes.add(resolved)
                modifiers = [
                    token.upper()
                    for token in re.split(r"[^a-z0-9]+", value.lower())
                    if token in STATE_MODIFIERS
                ]
                node[key] = resolved + suffix
                if modifiers:
                    node["descriptive_states"] = sorted(set(
                        node.get("descriptive_states", []) + modifiers
                    ))

            value = str(node.get("value", "")).strip().upper()
            relation = str(node.get("relation", "")).strip().upper()
            if node_type == "state":
                if not value:
                    errors.append(f"state node {node_id or index} has no value")
                elif value not in cls.STATE_VALUES and not value.startswith("FILLED_"):
                    errors.append(
                        f"state node {node_id or index} has unsupported value {value!r}"
                    )
                node["value"] = value
            if node_type == "relation":
                relation = relation or value
                if relation not in cls.RELATIONS:
                    errors.append(
                        f"relation node {node_id or index} has unsupported relation "
                        f"{relation!r}"
                    )
                node["relation"] = relation

            signature = (
                node_type,
                str(node.get("object", "")).lower(),
                str(node.get("target", "")).lower(),
                str(node.get("value", "")).upper(),
                str(node.get("relation", "")).upper(),
            )
            if signature in semantic_signatures:
                errors.append(f"duplicate semantic node {node_id or index}")
            semantic_signatures.add(signature)
            canonical_nodes.append(node)

        known_ids = set(node_ids)
        adjacency = {node_id: [] for node_id in known_ids}
        canonical_edges = []
        for index, raw_edge in enumerate(edges):
            if not isinstance(raw_edge, dict):
                errors.append(f"edge {index} must be an object")
                continue
            edge = dict(raw_edge)
            source = str(edge.get("from", "")).strip()
            target = str(edge.get("to", "")).strip()
            if source not in known_ids or target not in known_ids:
                errors.append(
                    f"edge {index} references unknown node {source!r}->{target!r}"
                )
            else:
                adjacency[source].append(target)
            canonical_edges.append(edge)

        visiting = set()
        visited = set()

        def has_cycle(node_id):
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            if any(has_cycle(target) for target in adjacency.get(node_id, [])):
                return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        if any(has_cycle(node_id) for node_id in known_ids):
            errors.append("dependency graph contains a cycle")

        required_explicit = instruction_scene_classes(
            instruction, scene_classes
        )
        missing_explicit = sorted(required_explicit - mentioned_classes)
        if missing_explicit:
            errors.append(
                "SDG dropped instruction class(es): " + ", ".join(missing_explicit)
            )

        if errors:
            return None, errors
        canonical = dict(payload)
        canonical["nodes"] = canonical_nodes
        canonical["edges"] = canonical_edges
        return canonical, []
