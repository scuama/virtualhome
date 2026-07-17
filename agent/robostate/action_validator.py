"""Parse, ground, and validate RoboState actions before Unity execution."""

from dataclasses import dataclass
import re
from typing import Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ActionValidation:
    valid: bool
    action: Optional[str] = None
    reason: Optional[str] = None
    repaired: bool = False


class ActionValidator:
    ACTION_PATTERN = re.compile(r"^\s*\[([a-zA-Z_]+)\]\s*(.*?)\s*$")
    OBJECT_PATTERN = re.compile(r"<([^<>]+)>\s*\(\s*(\d+)\s*\)")

    ARITY = {
        "walk": 1,
        "grab": 1,
        "open": 1,
        "close": 1,
        "switchon": 1,
        "switchoff": 1,
        "plugin": 1,
        "plugout": 1,
        "wipe": 1,
        "wash": 1,
        "cut": 1,
        "putin": 2,
        "putback": 2,
        "pour": 2,
    }
    PROTECTED_ACTIONS = {"grab", "switchoff", "plugout"}
    INTERACTION_ACTIONS = {
        "grab", "open", "close", "switchon", "switchoff",
        "plugin", "plugout", "wipe", "wash", "cut",
    }

    def validate(
        self,
        action: str,
        graph: dict,
        protected_classes: Optional[Iterable[str]] = None,
        allow_wait: bool = False,
    ) -> ActionValidation:
        match = self.ACTION_PATTERN.match(str(action or ""))
        if not match:
            return ActionValidation(False, reason="invalid action grammar")

        action_name = match.group(1).lower()
        arguments = match.group(2).strip()
        if action_name == "wait":
            if arguments:
                return ActionValidation(False, reason="wait takes no arguments")
            if allow_wait:
                return ActionValidation(True, "[wait]")
            return ActionValidation(False, reason="wait is not allowed in this state")
        if action_name == "ask":
            if not arguments:
                return ActionValidation(False, reason="ask requires a message")
            return ActionValidation(True, f"[ask] {arguments}")
        if action_name not in self.ARITY:
            return ActionValidation(False, reason=f"unsupported action {action_name}")

        objects = self.OBJECT_PATTERN.findall(arguments)
        remainder = self.OBJECT_PATTERN.sub("", arguments).strip()
        if remainder or len(objects) != self.ARITY[action_name]:
            return ActionValidation(
                False,
                reason=f"{action_name} requires {self.ARITY[action_name]} grounded object(s)",
            )

        id_to_node = {
            int(node["id"]): node
            for node in graph.get("nodes", [])
            if "id" in node
        }
        grounded: List[Tuple[str, int, dict]] = []
        for class_name, object_id_text in objects:
            object_id = int(object_id_text)
            node = id_to_node.get(object_id)
            if node is None:
                return ActionValidation(False, reason=f"unknown object id {object_id}")
            actual_class = str(node.get("class_name", "")).lower()
            if actual_class != class_name.strip().lower():
                return ActionValidation(
                    False,
                    reason=(
                        f"class/id mismatch: {class_name}({object_id}) is "
                        f"{actual_class}({object_id})"
                    ),
                )
            grounded.append((actual_class, object_id, node))

        protected = {str(value).lower() for value in protected_classes or []}
        if action_name in self.PROTECTED_ACTIONS and grounded[0][0] in protected:
            return ActionValidation(
                False,
                reason=f"action would disturb a satisfied task object: {grounded[0][0]}",
            )

        property_error = self._validate_properties(action_name, grounded)
        if property_error:
            return ActionValidation(False, reason=property_error)

        character_ids = {
            int(node["id"])
            for node in graph.get("nodes", [])
            if str(node.get("class_name", "")).lower() == "character"
        }
        close_ids = self._related_ids(graph, character_ids, {"CLOSE"})
        held_ids = self._related_ids(
            graph, character_ids, {"HOLDS", "HOLDS_RH", "HOLDS_LH"}
        )

        if action_name in self.INTERACTION_ACTIONS and grounded[0][1] not in close_ids:
            return self._repair_walk(grounded[0], "interaction target is not close")

        if action_name in {"putin", "putback", "pour"}:
            source, destination = grounded
            if source[1] not in held_ids:
                if source[1] in close_ids:
                    return ActionValidation(
                        True,
                        self._format("grab", [source]),
                        "source must be held first",
                        True,
                    )
                return self._repair_walk(source, "source must be reached and held first")
            if destination[1] not in close_ids:
                return self._repair_walk(destination, "destination is not close")
            if action_name == "putin":
                states = self._upper(destination[2].get("states", []))
                props = self._upper(destination[2].get("properties", []))
                if "CAN_OPEN" in props and "OPEN" not in states:
                    return ActionValidation(
                        True,
                        self._format("open", [destination]),
                        "container must be opened first",
                        True,
                    )

        return ActionValidation(True, self._format(action_name, grounded))

    def _validate_properties(self, action: str, objects: list) -> Optional[str]:
        first_props = self._upper(objects[0][2].get("properties", []))
        if action == "grab" and "GRABBABLE" not in first_props:
            return f"{objects[0][0]} is not GRABBABLE"
        if action in {"open", "close"} and "CAN_OPEN" not in first_props:
            return f"{objects[0][0]} is not openable"
        if action in {"switchon", "switchoff"} and "HAS_SWITCH" not in first_props:
            return f"{objects[0][0]} has no switch"
        if action in {"plugin", "plugout"} and "HAS_PLUG" not in first_props:
            return f"{objects[0][0]} has no plug"
        if action == "cut" and "CUTTABLE" not in first_props:
            return f"{objects[0][0]} is not CUTTABLE"
        if action == "pour" and "POURABLE" not in first_props:
            return f"{objects[0][0]} is not POURABLE"
        if action == "putin":
            dest_props = self._upper(objects[1][2].get("properties", []))
            if not dest_props.intersection({"CONTAINERS", "CONTAINER", "RECIPIENT"}):
                return f"{objects[1][0]} is not a container"
        if action == "putback":
            dest_props = self._upper(objects[1][2].get("properties", []))
            if not dest_props.intersection({"SURFACES", "SURFACE"}):
                return f"{objects[1][0]} is not a surface"
        return None

    def _repair_walk(self, obj: tuple, reason: str) -> ActionValidation:
        return ActionValidation(
            True,
            self._format("walk", [obj]),
            reason,
            True,
        )

    @staticmethod
    def _related_ids(graph: dict, character_ids: Set[int], relations: Set[str]) -> Set[int]:
        related = set()
        for edge in graph.get("edges", []):
            relation = str(
                edge.get("relation_type", edge.get("relation", ""))
            ).upper()
            from_id = int(edge.get("from_id", -1))
            to_id = int(edge.get("to_id", -1))
            if relation not in relations:
                continue
            if from_id in character_ids:
                related.add(to_id)
            if to_id in character_ids:
                related.add(from_id)
        return related

    @staticmethod
    def _upper(values) -> Set[str]:
        return {str(value).upper() for value in values or []}

    @staticmethod
    def _format(action: str, objects: list) -> str:
        args = " ".join(f"<{obj[0]}> ({obj[1]})" for obj in objects)
        return f"[{action}] {args}".strip()
