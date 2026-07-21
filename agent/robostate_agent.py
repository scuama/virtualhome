"""RoboState agent with observation-driven multi-task control."""

import json
import re
from typing import Optional, Set

from .base_agent import BaseAgent
from .robostate.action_validator import ActionValidator
from .robostate.exploration import RoomFrontierExplorer
from .robostate.goal_reasoner import GoalReasoner
from .robostate.llm_executor import LLMExecutor
from .robostate.loop_detector import LoopDetector
from .robostate.perception_filter import PerceptionFilter
from .robostate.sdg_planner import SDGPlanner
from .robostate.task_manager import MultiTaskManager, TaskState
from .utils.llm_client import LLMClient
from .utils.logger import AgentLogger


class RoboStateAgent(BaseAgent):
    REQUIRED_OBSERVATION = ["partial"]

    def __init__(self, model_name="gpt-4o-mini", scenario_id=""):
        super().__init__(model_name, scenario_id)
        self.llm = LLMClient(model_name=model_name)
        self.scenario_id = scenario_id
        self.logger = None
        self.action_history = []
        self.last_decision = {}
        self._initialized = False

    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        env_info = env_info or {}
        step = int(env_info.get("step", 0))
        goal = str(config.get("goal_instruction", "")).strip()
        if not goal and not config.get("tasks"):
            return "done()"

        self.logger = env_info.get("logger") or self.logger
        if not self.logger:
            self.logger = AgentLogger(
                log_mode=config.get("log_mode", "markdown"),
                scenario_id=self.scenario_id,
            )
        self.action_history = env_info.get("action_history", [])

        if step == 0 or not self._initialized:
            self._initialize_episode(config, goal)

        self._consume_previous_result(step)
        self._handle_clarification()
        memory_graph, effective_graph, _ = self._update_memory(obs, step)
        self.task_manager.update_progress(env_info.get("task_progress"), step)
        self.task_manager.refresh_graph_classes(memory_graph)
        self.explorer.update(obs, step)

        if self.task_manager.all_satisfied():
            return self._return_action(
                step, "done()", None, effective_graph, source="all_tasks_satisfied"
            )

        attempted_tasks: Set[str] = set()

        for _ in range(max(1, len(self.task_manager.tasks))):
            task = self.task_manager.select_task(
                memory_graph, step, exclude=attempted_tasks
            )
            if task is None:
                break
            attempted_tasks.add(task.task_id)

            try:
                self.task_manager.ensure_plan(
                    task, self.goal_reasoner, self.sdg_planner
                )
            except Exception as exc:
                self.logger.error(
                    f"Planning failed for task {task.task_id}: {exc}"
                )
                self.task_manager.defer(
                    task.task_id, step, "intent or SDG generation failed"
                )
                continue

            missing_classes = self.explorer.missing_classes(
                task.required_classes, memory_graph
            )
            if missing_classes:
                explore_action = self.explorer.next_action(step)
                if explore_action:
                    self.logger.info(
                        f"Task {task.task_id} is missing {sorted(missing_classes)}; "
                        "exploring another room."
                    )
                    return self._return_action(
                        step,
                        explore_action,
                        task,
                        effective_graph,
                        source="room_frontier",
                    )
                self.task_manager.defer(
                    task.task_id,
                    step,
                    f"required classes not found: {sorted(missing_classes)}",
                )
                continue

            filtered_graph = (
                self.perception_filter.filter_observations(
                    effective_graph, task.intent or {}, task.sdg
                )
                if task.sdg
                else effective_graph
            )
            candidate, reasoning, focus, satisfied_nodes = (
                self.llm_executor.decide_next_action(
                    filtered_graph,
                    task.intent or {},
                    task.sdg,
                    self.action_history,
                    config.get("scheduled_rules"),
                    allow_ask=not self.clarification_received,
                    task_context=self.task_manager.task_context(),
                )
            )
            candidate = self._normalize_action(candidate)
            allow_wait = self._temporary_rule_active(config, step)

            loop = self.loop_detector.check(candidate, self.action_history)
            if loop.detected:
                self.logger.info(
                    f"LoopDetector rejected {candidate!r}: {loop.reason}."
                )
                self.task_manager.defer(task.task_id, step, loop.reason or "loop")
                continue

            validation = self.action_validator.validate(
                candidate,
                effective_graph,
                protected_classes=(
                    self.task_manager.protected_classes()
                ),
                allow_wait=allow_wait,
            )
            if not validation.valid or not validation.action:
                self.logger.info(
                    f"ActionValidator rejected {candidate!r} for task "
                    f"{task.task_id}: {validation.reason}."
                )
                self.task_manager.defer(
                    task.task_id, step, validation.reason or "invalid action"
                )
                continue

            if validation.repaired:
                self.logger.info(
                    f"ActionValidator replaced {candidate!r} with "
                    f"{validation.action!r}: {validation.reason}."
                )
            return self._return_action(
                step,
                validation.action,
                task,
                filtered_graph,
                focus=focus,
                satisfied_nodes=satisfied_nodes,
                source="llm_executor_repaired" if validation.repaired else "llm_executor",
                reasoning=reasoning,
            )

        # Every runnable task requested an unsafe action or lacked a grounded
        # object. Keep making spatial progress instead of entering a wait loop.
        recovery_action = self.explorer.next_action(step, revisit=True)
        recovery_task = self.task_manager.active_task
        if recovery_action:
            return self._return_action(
                step,
                recovery_action,
                recovery_task,
                effective_graph,
                source="loop_recovery_room_revisit",
            )
        if self._temporary_rule_active(config, step):
            return self._return_action(
                step,
                "[wait]",
                recovery_task,
                effective_graph,
                source="allowed_wait_recovery",
            )

        self.logger.error(
            "RoboState exhausted task switching and room exploration; no safe "
            "grounded action is available."
        )
        return self._return_action(
            step,
            "[wait]",
            recovery_task,
            effective_graph,
            source="no_safe_action",
        )

    def _initialize_episode(self, config: dict, goal: str) -> None:
        self.goal_reasoner = GoalReasoner(self.llm, self.logger)
        self.sdg_planner = SDGPlanner(self.llm, self.logger)
        self.perception_filter = PerceptionFilter(self.llm, self.logger)
        self.llm_executor = LLMExecutor(self.llm, self.logger)
        instruction_overrides = None
        if config.get("instruction_type") == "summarized":
            instruction_overrides = self._decompose_summarized_instruction(
                goal,
                len(config.get("tasks") or []),
            )
        elif config.get("instruction_type") == "vague":
            instruction_overrides = self._ground_vague_instructions(config)
        self.task_manager = MultiTaskManager(
            config,
            logger=self.logger,
            failure_limit=int(config.get("robostate_task_failure_limit", 2)),
            instruction_overrides=instruction_overrides,
        )
        self.explorer = RoomFrontierExplorer(self.logger)
        self.action_validator = ActionValidator()
        self.loop_detector = LoopDetector()
        self.memory_nodes = {}
        self.memory_edges = {}
        self.memory_last_seen = {}
        self._observation_signatures = {}
        self.clarification_received = False
        self._processed_history_steps = set()
        self._processed_clarification_steps = set()
        self._issued_task_by_step = {}
        self.last_decision = {}
        self._initialized = True
        label = goal or " | ".join(
            task.instruction for task in self.task_manager.tasks
        )
        self.logger.info(
            f"Starting RoboState episode with {len(self.task_manager.tasks)} "
            f"task(s): {label}"
        )

    def _decompose_summarized_instruction(
        self, instruction: str, expected_count: int
    ) -> list:
        """Restore a summarized prompt to ordered concrete tasks without evaluator hints."""
        if expected_count < 1:
            raise ValueError("Summarized instruction has no configured task IDs")
        system_prompt = (
            "You decompose summarized embodied household instructions into concrete, "
            "independent tasks. Preserve every condition, object, destination, and state; "
            "resolve pronouns only from the text; never invent information. Return JSON only."
        )
        validation_error = ""
        for attempt in range(2):
            user_prompt = (
                f"Summarized instruction: {instruction!r}\n"
                f"Return exactly {expected_count} tasks in their original order as "
                '{"tasks": ["complete task 1", "complete task 2"]}. '
                "Each item must be a non-empty, distinct, directly executable English instruction."
            )
            if validation_error:
                user_prompt += f"\nPrevious output was invalid: {validation_error}"
            payload = self.llm.generate_json(system_prompt, user_prompt)
            tasks = payload.get("tasks") if isinstance(payload, dict) else None
            if not isinstance(tasks, list):
                validation_error = "the JSON field 'tasks' was not a list"
                continue
            normalized = []
            for item in tasks:
                text = item.get("instruction", "") if isinstance(item, dict) else item
                normalized.append(str(text).strip())
            if len(normalized) != expected_count:
                validation_error = (
                    f"expected {expected_count} tasks but received {len(normalized)}"
                )
                continue
            if any(not item for item in normalized):
                validation_error = "one or more tasks were empty"
                continue
            if len({item.lower() for item in normalized}) != expected_count:
                validation_error = "tasks were not distinct"
                continue
            self.logger.info(
                "Summarized instruction decomposed into: "
                + json.dumps(normalized, ensure_ascii=False)
            )
            return normalized
        raise ValueError(
            f"InstructionDecompositionError: {validation_error or 'invalid output'}"
        )

    def _ground_vague_instructions(self, config: dict) -> list:
        """Ground abstract object descriptions against public scene candidates."""
        source_tasks = [
            str(task.get("instruction", "")).strip()
            for task in config.get("tasks", []) or []
        ]
        candidates = [
            str(value).strip().lower()
            for value in config.get("grounding_candidates", [])
            if str(value).strip()
        ]
        system_prompt = (
            "You ground vague embodied household instructions to concrete VirtualHome "
            "object classes. Rewrite each task independently using the best matching "
            "candidate classes. Preserve conditions, actions, and order; do not add tasks. "
            "Return JSON only."
        )
        validation_error = ""
        for _ in range(2):
            prompt = (
                f"Vague tasks: {json.dumps(source_tasks)}\n"
                f"Available scene object classes: {json.dumps(candidates)}\n"
                f"Return exactly {len(source_tasks)} concrete strings in a 'tasks' list."
            )
            if validation_error:
                prompt += f"\nPrevious output was invalid: {validation_error}"
            payload = self.llm.generate_json(system_prompt, prompt)
            tasks = payload.get("tasks") if isinstance(payload, dict) else None
            grounded = [str(item).strip() for item in tasks] if isinstance(tasks, list) else []
            if len(grounded) != len(source_tasks):
                validation_error = "wrong number of grounded tasks"
                continue
            if any(not item for item in grounded):
                validation_error = "one or more grounded tasks were empty"
                continue
            self.logger.info(
                "Vague instructions grounded into: "
                + json.dumps(grounded, ensure_ascii=False)
            )
            return grounded
        raise ValueError(
            f"InstructionGroundingError: {validation_error or 'invalid output'}"
        )

    def _consume_previous_result(self, step: int) -> None:
        if not self.action_history:
            return
        entry = self.action_history[-1]
        history_step = int(entry.get("step", len(self.action_history) - 1))
        if history_step in self._processed_history_steps:
            return
        self._processed_history_steps.add(history_step)
        task_id = self._issued_task_by_step.get(history_step)
        success = self._coerce_success(entry.get("success", False))
        self.task_manager.record_result(task_id, success, step)
        self.explorer.record_action(
            entry.get("action", ""), success, history_step
        )

    def _handle_clarification(self) -> None:
        if not self.action_history:
            return
        entry = self.action_history[-1]
        history_step = int(entry.get("step", len(self.action_history) - 1))
        if history_step in self._processed_clarification_steps:
            return
        if not str(entry.get("action", "")).lower().startswith("[ask]"):
            return
        if not self._coerce_success(entry.get("success", False)):
            return

        self._processed_clarification_steps.add(history_step)
        self.clarification_received = True
        clarification = str(entry.get("message", "")).strip()
        task_id = self._issued_task_by_step.get(history_step)
        task = self.task_manager.get(task_id) or self.task_manager.active_task
        if not task or not self._meaningful_clarification(clarification):
            self.logger.info(
                "Clarification contained no new task information; continuing "
                "autonomous search."
            )
            return

        rewrite_system = "You rewrite embodied task instructions precisely."
        rewrite_user = (
            f"Original instruction: {task.instruction!r}\n"
            f"User clarification: {clarification!r}\n"
            "Combine them into one complete English instruction. Output only "
            "the instruction."
        )
        rewritten = self.llm.generate_response(
            rewrite_system, rewrite_user
        ).strip()
        if not rewritten:
            rewritten = f"{task.instruction} {clarification}".strip()
        self.task_manager.revise_task(task.task_id, rewritten)

    def _update_memory(self, obs: dict, step: int) -> tuple:
        outgoing = {}
        for edge in obs.get("edges", []):
            outgoing.setdefault(int(edge.get("from_id", -1)), []).append(
                (
                    str(edge.get("relation_type", edge.get("relation", ""))).upper(),
                    int(edge.get("to_id", -1)),
                )
            )
        changed_classes = set()
        visible_ids = set()
        for node in obs.get("nodes", []):
            node_id = int(node["id"])
            signature = (
                tuple(sorted(str(value).upper() for value in node.get("states", []))),
                tuple(sorted(str(value).upper() for value in node.get("properties", []))),
                tuple(sorted(outgoing.get(node_id, []))),
            )
            previous = self._observation_signatures.get(node_id)
            if previous is not None and previous != signature:
                changed_classes.add(str(node.get("class_name", "")).lower())
            self._observation_signatures[node_id] = signature
            self.memory_nodes[node_id] = dict(node)
            self.memory_last_seen[node_id] = int(step)
            self.memory_edges[node_id] = []
            visible_ids.add(node_id)

        for edge in obs.get("edges", []):
            from_id = int(edge.get("from_id", -1))
            if from_id in visible_ids:
                self.memory_edges[from_id].append(dict(edge))

        memory_graph = {
            "nodes": list(self.memory_nodes.values()),
            "edges": [
                edge
                for edges in self.memory_edges.values()
                for edge in edges
            ],
        }
        return memory_graph, memory_graph, changed_classes

    def _return_action(
        self,
        step: int,
        action: str,
        task: Optional[TaskState],
        graph: dict,
        focus: str = "",
        satisfied_nodes=None,
        source: str = "controller",
        reasoning: str = "",
    ) -> str:
        task_id = task.task_id if task else None
        self._issued_task_by_step[int(step)] = task_id
        observed_items = self._get_observed_items(graph)
        self.last_decision = {
            "active_task_id": task_id,
            "task_context": self.task_manager.task_context(),
            "sdg": task.sdg if task else None,
            "observed_items": observed_items,
            "current_node_focus": focus,
            "satisfied_nodes": list(satisfied_nodes or []),
            "source": source,
            "reasoning": reasoning,
        }
        try:
            self.logger.log_module_output(
                "RoboStateMultiTaskController",
                step,
                {
                    "action": action,
                    "active_task_id": task_id,
                    "task_context": self.task_manager.task_context(),
                    "source": source,
                },
            )
        except Exception:
            pass
        return action

    @staticmethod
    def _normalize_action(action: str) -> str:
        value = str(action or "").strip()
        if value.upper() == "WAIT" or value.lower() == "wait()":
            return "[wait]"

        def add_brackets(match):
            class_name = match.group(1).strip()
            return f" <{class_name}> ({match.group(2)})"

        return re.sub(
            r"\s+([A-Za-z0-9_]+)\s*\(\s*(\d+)\s*\)",
            add_brackets,
            value,
        )

    @staticmethod
    def _get_observed_items(graph: dict):
        items = []
        for node in graph.get("nodes", []):
            states = node.get("states", [])
            suffix = f" [{','.join(states)}]" if states else ""
            items.append(
                f"{node.get('class_name', 'object')}({node.get('id')}){suffix}"
            )
        return items

    @staticmethod
    def _temporary_rule_active(config: dict, step: int) -> bool:
        return any(
            int(rule.get("start_step", 0))
            <= step
            <= int(rule.get("end_step", 9999))
            for rule in config.get("scheduled_rules", []) or []
        )

    @staticmethod
    def _meaningful_clarification(message: str) -> bool:
        normalized = " ".join(str(message).strip().lower().split())
        return normalized not in {
            "",
            "none",
            "n/a",
            "no clarification",
            "nothing to claim",
            "nothing to clarify",
        }

    @staticmethod
    def _coerce_success(value) -> bool:
        if isinstance(value, dict):
            return all(bool(item) for item in value.values()) if value else False
        if isinstance(value, (list, tuple)):
            return all(bool(item) for item in value) if value else False
        return bool(value)
