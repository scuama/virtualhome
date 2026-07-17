"""Deterministic room-frontier exploration for partial observations."""

import re
from typing import Dict, Iterable, Optional, Set


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


class RoomFrontierExplorer:
    WALK_ROOM_PATTERN = re.compile(
        r"^\s*\[walk\]\s*<([^>]+)>\s*\(\s*(\d+)\s*\)\s*$",
        re.IGNORECASE,
    )

    def __init__(self, logger=None):
        self.logger = logger
        self.rooms: Dict[int, dict] = {}
        self.visited_room_ids: Set[int] = set()
        self.attempted_room_ids: Set[int] = set()
        self.current_room_id: Optional[int] = None
        self.last_visit_step: Dict[int, int] = {}

    def update(self, graph: dict, step: int) -> None:
        nodes = graph.get("nodes", [])
        for node in nodes:
            if str(node.get("category", "")) == "Rooms":
                self.rooms[int(node["id"])] = node

        character_ids = {
            int(node["id"])
            for node in nodes
            if str(node.get("class_name", "")).lower() == "character"
        }
        room_ids = set(self.rooms)
        for edge in graph.get("edges", []):
            relation = str(
                edge.get("relation_type", edge.get("relation", ""))
            ).upper()
            from_id = int(edge.get("from_id", -1))
            to_id = int(edge.get("to_id", -1))
            if relation == "INSIDE" and from_id in character_ids and to_id in room_ids:
                self._mark_visited(to_id, step)
                break

    def record_action(self, action: str, success: bool, step: int) -> None:
        match = self.WALK_ROOM_PATTERN.match(str(action or ""))
        if not match:
            return
        room_id = int(match.group(2))
        if room_id not in self.rooms:
            return
        self.attempted_room_ids.add(room_id)
        if success:
            self._mark_visited(room_id, step)

    def missing_classes(self, required_classes: Iterable[str], graph: dict) -> Set[str]:
        present = {
            _compact(node.get("class_name", ""))
            for node in graph.get("nodes", [])
        }
        return {
            str(class_name).lower()
            for class_name in required_classes
            if _compact(class_name) not in present
        }

    def relevant_hidden_ids(
        self,
        required_classes: Iterable[str],
        hidden_nodes,
        memory_graph: dict,
    ) -> Set[int]:
        hidden_ids = {
            int(node_id) for node_id in (hidden_nodes or {})
        }
        required = {_compact(value) for value in required_classes}
        return {
            int(node["id"])
            for node in memory_graph.get("nodes", [])
            if int(node.get("id", -1)) in hidden_ids
            and _compact(node.get("class_name", "")) in required
        }

    def next_action(self, step: int, revisit: bool = False) -> Optional[str]:
        if not self.rooms:
            return None

        frontier = [
            room
            for room_id, room in sorted(self.rooms.items())
            if room_id != self.current_room_id
            and room_id not in self.visited_room_ids
            and room_id not in self.attempted_room_ids
        ]
        if not frontier and revisit:
            frontier = [
                room
                for room_id, room in self.rooms.items()
                if room_id != self.current_room_id
            ]
            frontier.sort(
                key=lambda room: (
                    self.last_visit_step.get(int(room["id"]), -1),
                    int(room["id"]),
                )
            )
        if not frontier:
            return None

        room = frontier[0]
        room_id = int(room["id"])
        self.attempted_room_ids.add(room_id)
        action = f"[walk] <{room['class_name']}> ({room_id})"
        if self.logger:
            mode = "revisit" if revisit else "frontier"
            self.logger.info(
                f"RoomFrontierExplorer: {mode} action at step {step}: {action}"
            )
        return action

    def _mark_visited(self, room_id: int, step: int) -> None:
        self.current_room_id = int(room_id)
        self.visited_room_ids.add(int(room_id))
        self.attempted_room_ids.add(int(room_id))
        self.last_visit_step[int(room_id)] = int(step)
