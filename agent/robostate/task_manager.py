"""Deterministic multi-task state and scheduling for RoboState."""

from dataclasses import dataclass, field
import re
from typing import Iterable, List, Optional, Set


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


NON_ENVIRONMENT_CLASSES = {
    "agent",
    "robot",
    "character",
    "human",
    "person",
    "people",
    "nobody",
    "someone",
    "user",
    "self",
    "hand",
    "hands",
    "left_hand",
    "right_hand",
}


@dataclass
class TaskState:
    task_id: str
    instruction: str
    order: int
    status: str = "pending"
    currently_satisfied: bool = False
    intent: Optional[dict] = None
    sdg: Optional[dict] = None
    required_classes: Set[str] = field(default_factory=set)
    failure_count: int = 0
    cooldown_until: int = 0
    first_activated_step: Optional[int] = None
    last_activated_step: Optional[int] = None


class MultiTaskManager:
    """Own task state while using evaluator booleans for task completion."""

    def __init__(
        self,
        config: dict,
        logger=None,
        failure_limit: int = 2,
        instruction_overrides: Optional[List[str]] = None,
        fixed_order: bool = False,
    ):
        configured_tasks = config.get("tasks") or []
        if configured_tasks:
            task_specs = configured_tasks
        else:
            task_specs = [
                {
                    "task_id": config.get("scenario_id", "task_1"),
                    "instruction": config.get("goal_instruction", ""),
                }
            ]

        self.tasks: List[TaskState] = []
        seen_ids = set()
        for index, spec in enumerate(task_specs):
            task_id = str(spec.get("task_id") or f"task_{index + 1}")
            if task_id in seen_ids:
                task_id = f"{task_id}_{index + 1}"
            seen_ids.add(task_id)
            instruction = (
                str(instruction_overrides[index]).strip()
                if instruction_overrides and index < len(instruction_overrides)
                else str(spec.get("instruction") or "").strip()
            )
            if not instruction and len(task_specs) == 1:
                instruction = str(config.get("goal_instruction", "")).strip()
            self.tasks.append(TaskState(task_id, instruction, index))

        self.logger = logger
        self.failure_limit = max(1, int(failure_limit))
        self.active_task_id: Optional[str] = None
        self.fixed_order = bool(fixed_order)
        self.scene_classes = {
            str(value).strip().lower().replace(" ", "_")
            for value in config.get("grounding_candidates", []) or []
            if str(value).strip()
        }

    @property
    def active_task(self) -> Optional[TaskState]:
        return self.get(self.active_task_id) if self.active_task_id else None

    def get(self, task_id: Optional[str]) -> Optional[TaskState]:
        return next((task for task in self.tasks if task.task_id == task_id), None)

    def update_progress(self, progress: Optional[Iterable[dict]], step: int) -> None:
        """Consume only public task IDs and their evaluator completion booleans."""
        if progress is None:
            return
        progress_by_id = {
            str(item.get("task_id")): bool(item.get("currently_satisfied", False))
            for item in progress
            if item.get("task_id") is not None
        }
        for task in self.tasks:
            if task.task_id not in progress_by_id:
                continue
            was_satisfied = task.currently_satisfied
            task.currently_satisfied = progress_by_id[task.task_id]
            if task.currently_satisfied:
                task.status = "satisfied"
                task.failure_count = 0
                task.cooldown_until = 0
                if self.active_task_id == task.task_id:
                    self.active_task_id = None
            elif was_satisfied:
                task.status = "pending"
                task.cooldown_until = 0
                self._log(f"Task {task.task_id} regressed at step {step}; reopening it.")

    def select_task(
        self,
        graph: dict,
        step: int,
        exclude: Optional[Set[str]] = None,
        force_switch: bool = False,
    ) -> Optional[TaskState]:
        excluded = exclude or set()
        active = self.active_task
        if (
            active
            and not force_switch
            and active.task_id not in excluded
            and not active.currently_satisfied
            and active.cooldown_until <= step
        ):
            return active

        if active and active.status == "active":
            active.status = "pending"
        self.active_task_id = None

        candidates = [
            task
            for task in self.tasks
            if not task.currently_satisfied
            and task.task_id not in excluded
            and task.cooldown_until <= step
        ]
        if not candidates:
            return None

        graph_classes = {
            str(node.get("class_name", "")).lower()
            for node in graph.get("nodes", [])
            if str(node.get("category", "")) != "Rooms"
        }
        compact_graph_classes = {_compact(value) for value in graph_classes}

        def score(task: TaskState):
            compact_instruction = _compact(task.instruction)
            mentioned_visible = sum(
                1
                for class_name in graph_classes
                if _compact(class_name) and _compact(class_name) in compact_instruction
            )
            planned_visible = sum(
                1
                for class_name in task.required_classes
                if _compact(class_name) in compact_graph_classes
            )
            # Prefer grounded tasks, then fewer failures, then stable config order.
            return (mentioned_visible + planned_visible, -task.failure_count, -task.order)

        selected = (
            min(candidates, key=lambda task: task.order)
            if self.fixed_order
            else max(candidates, key=score)
        )
        selected.status = "active"
        selected.last_activated_step = int(step)
        if selected.first_activated_step is None:
            selected.first_activated_step = int(step)
        self.active_task_id = selected.task_id
        self._log(f"Active task at step {step}: {selected.task_id}")
        return selected

    def ensure_plan(self, task: TaskState, goal_reasoner, sdg_planner) -> None:
        if task.intent is None:
            task.intent = goal_reasoner.extract_intent(task.instruction)
        if task.sdg is None:
            task.sdg = sdg_planner.generate_sdg(task.instruction)
        self._extract_required_classes(task)

    def refresh_graph_classes(self, graph: dict) -> None:
        """Learn exact scene classes mentioned by each instruction without conditions."""
        graph_classes = {
            str(node.get("class_name", "")).lower()
            for node in graph.get("nodes", [])
            if str(node.get("category", "")) != "Rooms"
            and str(node.get("class_name", "")).lower() != "character"
        }
        for task in self.tasks:
            compact_instruction = _compact(task.instruction)
            for class_name in graph_classes:
                if _compact(class_name) in compact_instruction:
                    task.required_classes.add(class_name)

    def revise_task(self, task_id: str, instruction: str) -> None:
        task = self.get(task_id)
        if not task or not instruction.strip():
            return
        task.instruction = instruction.strip()
        task.intent = None
        task.sdg = None
        task.required_classes.clear()
        task.failure_count = 0
        task.cooldown_until = 0
        if not task.currently_satisfied:
            task.status = "pending"
        self._log(f"Revised task {task.task_id} after clarification.")

    def record_result(self, task_id: Optional[str], success: bool, step: int) -> None:
        task = self.get(task_id)
        if not task or task.currently_satisfied:
            return
        if success:
            task.failure_count = 0
            return
        task.failure_count += 1
        if task.failure_count >= self.failure_limit:
            self.defer(task.task_id, step, "repeated action failures")

    def defer(self, task_id: str, step: int, reason: str = "recovery") -> None:
        task = self.get(task_id)
        if not task or task.currently_satisfied:
            return
        task.status = "pending"
        task.cooldown_until = max(task.cooldown_until, int(step) + 1)
        if self.active_task_id == task_id:
            self.active_task_id = None
        self._log(f"Deferred task {task_id} at step {step}: {reason}.")

    def task_context(self) -> dict:
        return {
            "active_task_id": self.active_task_id,
            "pending_task_ids": [
                task.task_id
                for task in self.tasks
                if not task.currently_satisfied and task.task_id != self.active_task_id
            ],
            "satisfied_task_ids": [
                task.task_id for task in self.tasks if task.currently_satisfied
            ],
        }

    def protected_classes(self) -> Set[str]:
        protected = set()
        for task in self.tasks:
            if task.currently_satisfied:
                protected.update(task.required_classes)
        return protected

    def all_satisfied(self) -> bool:
        return bool(self.tasks) and all(task.currently_satisfied for task in self.tasks)

    def _extract_required_classes(self, task: TaskState) -> None:
        if not isinstance(task.sdg, dict):
            return
        for node in task.sdg.get("nodes", []):
            for key in ("object", "target"):
                value = str(node.get(key, "")).strip().lower()
                if not value or value.startswith("?"):
                    continue
                # Quantity variables such as apple_1 still refer to class apple.
                value = re.sub(r"_\d+$", "", value)
                if value.replace(" ", "_") in NON_ENVIRONMENT_CLASSES:
                    continue
                normalized = value.replace(" ", "_")
                if self.scene_classes and normalized not in self.scene_classes:
                    continue
                if re.fullmatch(r"[a-z][a-z0-9_ -]*", value):
                    task.required_classes.add(normalized)

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.info(f"MultiTaskManager: {message}")
