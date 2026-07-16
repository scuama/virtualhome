import json
import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .utils.logger import AgentLogger
from .utils.llm_client import LLMClient
from .base_agent import BaseAgent


SAYCAN_AGENT_VERSION = "SAYCAN-VH-v3.0-2026-07-16"
__version__ = SAYCAN_AGENT_VERSION


class SayCanAgent(BaseAgent):
    """SayCan adapted to the project's VirtualHome environment.

    The language model provides a semantic relevance score (Say), while
    graph-based precondition checks provide an executability score (Can).
    The selected action maximizes Say * Can.

    This implementation intentionally does not use GoalReasoner, SDGPlanner,
    PerceptionFilter, LTM, or any learned memory module, so it remains a clean
    no-memory planning baseline.
    """

    VERSION = SAYCAN_AGENT_VERSION

    ACTION_PATTERN = re.compile(r"\[(\w+)\]")
    ID_PATTERN = re.compile(r"\(\s*(\d+)\s*\)")

    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "bring", "by", "do",
        "for", "from", "here", "if", "in", "into", "is", "it", "of", "on",
        "or", "please", "some", "that", "the", "there", "this", "to", "with",
        "you", "your",
    }

    ACTION_WORDS = {
        "ask", "bring", "close", "cut", "get", "go", "grab", "heat", "move",
        "open", "place", "plug", "pour", "put", "switch", "take", "turn",
        "unplug", "wait", "walk", "wash",
    }

    # Generic VirtualHome prerequisites for skills whose support object
    # may be omitted from the instruction. These are environment semantics,
    # not task-instance plans or success-condition shortcuts.
    SKILL_SUPPORT_CLASSES = {
        "heat": {"microwave", "oven", "stove", "toaster", "kettle"},
        "hot": {"microwave", "oven", "stove", "toaster", "kettle"},
        "wash": {"sink", "dishwasher"},
        "clean": {"sink", "dishwasher"},
        "cut": {"knife", "cuttingboard"},
        "slice": {"knife", "cuttingboard"},
        "pour": {"sink", "cup", "glass", "bowl"},
    }

    SAY_SCORE_MODE = "explicit_candidate_relevance"
    CAN_SCORE_MODE = "symbolic_task_independent_affordance"

    CONTAINER_PROPERTIES = {"CONTAINER", "CONTAINERS"}
    SURFACE_PROPERTIES = {"SURFACE"}
    OPENABLE_PROPERTIES = {"OPENABLE", "CAN_OPEN"}

    def __init__(self, model_name: str = "gpt-5.4-mini", scenario_id: str = ""):
        self.llm = LLMClient(model_name=model_name)
        self.scenario_id = scenario_id
        self.logger = AgentLogger(log_mode="markdown", scenario_id=scenario_id)
        self.action_history: List[dict] = []
        self.goal = ""
        self.version = self.VERSION

    # ------------------------------------------------------------------
    # Episode loop
    # ------------------------------------------------------------------
    def run_episode(self, env, config: dict) -> Tuple[bool, str]:
        self.goal = str(config.get("goal_instruction", "")).strip()
        if not self.goal:
            return False, "No goal instruction provided"

        self.logger = AgentLogger(
            log_mode=config.get("log_mode", "markdown"),
            scenario_id=self.scenario_id,
        )
        self.action_history = list(config.get("prior_action_history", []))
        max_steps = int(config.get("max_steps", 15))
        success_condition = config.get("success_condition", {})
        failure_condition = config.get("failure_condition")

        self.logger.info(
            f"[{self.VERSION}] Starting SayCan-VH episode for goal: {self.goal}"
        )
        self._log_module_output(
            "SayCanVersion",
            0,
            {
                "version": self.VERSION,
                "implementation": "SayCan (VirtualHome adaptation)",
                "say_score_mode": self.SAY_SCORE_MODE,
                "can_score_mode": self.CAN_SCORE_MODE,
                "say_context_mode": config.get(
                    "saycan_say_context_mode", "state_summary"
                ),
                "task_semantics_in_can": False,
                "source_file": __file__,
            },
        )

        for step in range(max_steps):
            graph = self._deduplicate_graph(env.get_graph())

            if self._check_success(graph, success_condition):
                if not self._ask_requirement_met(config):
                    self.logger.error(
                        "Goal reached, but clarification was required."
                    )
                    return False, "Failed: Did not ask for clarification"
                self.logger.info("✅ SUCCESS! Goal condition met.")
                self._write_step_log(
                    step,
                    "FINISH (Goal Reached)",
                    self._observed_items(graph),
                )
                return True, "Goal Reached"

            if (
                failure_condition
                and self._condition_is_active(failure_condition, step)
                and self._check_success(graph, failure_condition)
            ):
                self.logger.error("❌ FAILED: Failure condition met.")
                return False, "Failure condition met (Constraint Violated)"

            candidate_actions = self._generate_candidate_actions(
                graph=graph,
                goal=self.goal,
                config=config,
            )
            if not candidate_actions:
                self.logger.error("No candidate skills could be generated.")
                return False, "No candidate actions"

            say_scores = self._score_with_llm(
                graph=graph,
                candidate_actions=candidate_actions,
                config=config,
            )
            can_scores = self._score_affordance(
                graph=graph,
                candidate_actions=candidate_actions,
                config=config,
            )

            combined_scores: Dict[str, float] = {}
            for action in candidate_actions:
                combined_scores[action] = (
                    say_scores.get(action, 0.0)
                    * can_scores.get(action, 0.0)
                    * self._repetition_penalty(action)
                )

            best_action = self._select_action(
                candidate_actions=candidate_actions,
                say_scores=say_scores,
                can_scores=can_scores,
                combined_scores=combined_scores,
            )

            self._log_scoring(
                step=step,
                candidate_actions=candidate_actions,
                say_scores=say_scores,
                can_scores=can_scores,
                combined_scores=combined_scores,
                best_action=best_action,
            )

            if best_action == "done()":
                self.logger.error(
                    "Agent selected done(), but the goal is not satisfied."
                )
                self._write_step_log(
                    step, "done()", self._observed_items(graph)
                )
                return False, "Terminated before goal"

            self.logger.info(
                f"[{self.VERSION}] Step {step}: selected '{best_action}' "
                f"(Say={say_scores.get(best_action, 0.0):.3f}, "
                f"Can={can_scores.get(best_action, 0.0):.3f}, "
                f"Combined={combined_scores.get(best_action, 0.0):.3f})"
            )

            if best_action.lower().startswith("[ask]"):
                ask_result = self._handle_ask(
                    best_action, step, graph, config
                )
                if ask_result is not None:
                    return ask_result
                continue

            try:
                _, _, done, info = env.step({0: best_action})
                info = info or {}
                success = self._coerce_action_success(
                    info.get("action_success", False)
                )
                message = str(info.get("action_message", ""))
            except Exception as exc:
                done = False
                success = False
                message = f"Environment exception: {exc}"
                self.logger.error(message)

            history_entry = {
                "step": step,
                "action": best_action,
                "success": success,
                "reasoning": (
                    f"Say={say_scores.get(best_action, 0.0):.3f}; "
                    f"Can={can_scores.get(best_action, 0.0):.3f}; "
                    f"Combined={combined_scores.get(best_action, 0.0):.3f}"
                ),
            }
            if message:
                history_entry["message" if success else "error"] = message
            self.action_history.append(history_entry)

            if not success:
                self.logger.info(f"Action failed: {best_action}. {message}")

            post_graph = self._deduplicate_graph(env.get_graph())
            self._write_step_log(
                step, best_action, self._observed_items(post_graph)
            )

            if (
                failure_condition
                and self._condition_is_active(failure_condition, step)
                and self._check_success(post_graph, failure_condition)
            ):
                self.logger.error("❌ FAILED: Failure condition met.")
                return False, "Failure condition met (Constraint Violated)"

            if self._check_success(post_graph, success_condition):
                if not self._ask_requirement_met(config):
                    self.logger.error(
                        "Goal reached, but clarification was required."
                    )
                    return False, "Failed: Did not ask for clarification"
                self.logger.info("✅ SUCCESS! Goal condition met.")
                return True, "Goal Reached"

            if done:
                self.logger.error(
                    "Environment terminated before the goal was reached."
                )
                return False, "Environment terminated"

        self.logger.error("❌ FAILED: Max steps reached.")
        return False, "Max steps reached"

    def _generate_candidate_actions(
        self,
        graph: dict,
        goal: str,
        config: dict,
    ) -> List[str]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        id_to_node = {int(node["id"]): node for node in nodes if "id" in node}
        character = self._get_character(nodes)
        character_id = int(character["id"]) if character else 1

        goal_terms = self._extract_goal_terms(goal)
        selected_ids = self._select_relevant_node_ids(graph, goal_terms)

        selected_nodes = [
            id_to_node[node_id]
            for node_id in sorted(selected_ids)
            if node_id in id_to_node
        ]

        held_ids = {
            int(edge["to_id"])
            for edge in edges
            if int(edge.get("from_id", -1)) == character_id
            and str(edge.get("relation_type", "")).upper().startswith("HOLDS")
        }

        actions: List[str] = []

        for node in selected_nodes:
            node_id = int(node["id"])
            if node_id == character_id:
                continue

            class_name = node.get("class_name", "object")
            category = str(node.get("category", ""))
            properties = self._upper_set(node.get("properties", []))
            states = self._effective_states(node)

            # Walking is the universal enabling action for object interactions.
            # Do not generate walk-to-self actions for objects already in hand.
            if category != "Rooms" and node_id not in held_ids:
                actions.append(self._format_unary("walk", class_name, node_id))

            if "GRABBABLE" in properties and node_id not in held_ids:
                actions.append(self._format_unary("grab", class_name, node_id))

            if properties & self.OPENABLE_PROPERTIES:
                if "OPEN" not in states:
                    actions.append(self._format_unary("open", class_name, node_id))
                if "CLOSED" not in states:
                    actions.append(self._format_unary("close", class_name, node_id))

            if "HAS_SWITCH" in properties:
                if "ON" not in states:
                    actions.append(self._format_unary("switchon", class_name, node_id))
                if "OFF" not in states:
                    actions.append(self._format_unary("switchoff", class_name, node_id))

            if "HAS_PLUG" in properties:
                if "PLUGGED_IN" not in states:
                    actions.append(self._format_unary("plugin", class_name, node_id))
                if "PLUGGED_OUT" not in states:
                    actions.append(self._format_unary("plugout", class_name, node_id))

            compact_goal = self._compact(goal)
            if ("wash" in compact_goal or "clean" in compact_goal) and "GRABBABLE" in properties:
                actions.append(self._format_unary("wash", class_name, node_id))
            if ("cut" in compact_goal or "slice" in compact_goal) and "CUTTABLE" in properties:
                actions.append(self._format_unary("cut", class_name, node_id))

        held_nodes = [id_to_node[node_id] for node_id in held_ids if node_id in id_to_node]
        containers = [
            node for node in selected_nodes
            if self._upper_set(node.get("properties", []))
            & (self.CONTAINER_PROPERTIES | self.OPENABLE_PROPERTIES)
        ]
        surfaces = [
            node for node in selected_nodes
            if self._upper_set(node.get("properties", [])) & self.SURFACE_PROPERTIES
        ]

        for held in held_nodes:
            held_id = int(held["id"])
            held_class = held.get("class_name", "object")

            for container in containers:
                container_id = int(container["id"])
                if container_id == held_id:
                    continue
                actions.append(
                    self._format_binary(
                        "putin",
                        held_class,
                        held_id,
                        container.get("class_name", "container"),
                        container_id,
                    )
                )

            for surface in surfaces:
                surface_id = int(surface["id"])
                if surface_id == held_id:
                    continue
                actions.append(
                    self._format_binary(
                        "putback",
                        held_class,
                        held_id,
                        surface.get("class_name", "surface"),
                        surface_id,
                    )
                )

            if "pour" in self._compact(goal):
                for destination in selected_nodes:
                    destination_id = int(destination["id"])
                    if destination_id == held_id:
                        continue
                    dest_properties = self._upper_set(destination.get("properties", []))
                    if "POURABLE" in dest_properties or destination.get("class_name", "").lower() == "sink":
                        actions.append(
                            self._format_binary(
                                "pour",
                                held_class,
                                held_id,
                                destination.get("class_name", "object"),
                                destination_id,
                            )
                        )

        # WAIT is an environment skill for temporary-event scenarios.
        if (
            config.get("dynamic_events")
            or config.get("scheduled_rules")
            or self._last_action_failed()
        ):
            actions.append("[wait]")

        # ASK is available only when the benchmark permits or requires it.
        if (
            config.get("allow_ask", False)
            or config.get("require_ask_to_pass", False)
            or "user_clarification_reply" in config
            or str(config.get("on_ask_policy", "")).upper() == "SUCCESS"
        ):
            actions.append(
                "[ask] Could you clarify the target object or location?"
            )

        # done() allows the language model to express intentional termination,
        # but run_episode only accepts it when success has already been verified.
        actions.append("done()")

        actions = list(dict.fromkeys(actions))
        actions.sort(key=lambda action: self._candidate_priority(action, goal, graph), reverse=True)

        max_candidates = max(5, int(config.get("saycan_max_candidates", 40)))
        if len(actions) > max_candidates:
            # Preserve done() and wait when truncating.
            special = [
                action for action in actions
                if action == "done()"
                or action == "[wait]"
                or action.lower().startswith("[ask]")
            ]
            regular = [
                action for action in actions
                if action not in special
            ]
            actions = regular[: max_candidates - len(special)] + special

        return actions

    def _select_relevant_node_ids(self, graph: dict, goal_terms: Set[str]) -> Set[int]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        id_to_node = {int(node["id"]): node for node in nodes if "id" in node}

        selected_ids: Set[int] = set()
        support_classes: Set[str] = set()
        for term in goal_terms:
            support_classes.update(self.SKILL_SUPPORT_CLASSES.get(term, set()))

        for node in nodes:
            node_id = int(node["id"])
            class_name = str(node.get("class_name", "")).lower()
            compact_name = self._compact(class_name)
            properties = self._upper_set(node.get("properties", []))

            direct_match = any(
                term in compact_name or compact_name in term
                for term in goal_terms
                if len(term) >= 3
            )
            support_match = class_name in support_classes or compact_name in {
                self._compact(item) for item in support_classes
            }
            useful_fixture = bool(
                properties
                & (
                    self.CONTAINER_PROPERTIES
                    | self.SURFACE_PROPERTIES
                    | self.OPENABLE_PROPERTIES
                    | {"HAS_SWITCH", "HAS_PLUG"}
                )
            )

            if direct_match or support_match:
                selected_ids.add(node_id)
            elif useful_fixture and class_name in support_classes:
                selected_ids.add(node_id)

            if class_name == "character":
                selected_ids.add(node_id)

        # Keep one-hop spatial parents and children of directly relevant objects.
        frontier = set(selected_ids)
        for edge in edges:
            relation = str(edge.get("relation_type", edge.get("relation", ""))).upper()
            from_id = int(edge.get("from_id", -1))
            to_id = int(edge.get("to_id", -1))
            if relation not in {"ON", "INSIDE", "CLOSE", "HOLDS_RH", "HOLDS_LH", "HOLDS"}:
                continue
            if from_id in frontier and to_id in id_to_node:
                selected_ids.add(to_id)
            if to_id in frontier and from_id in id_to_node:
                selected_ids.add(from_id)

        # A failed target must remain available even if it is not explicit in the goal.
        if self.action_history:
            for object_id in self.ID_PATTERN.findall(self.action_history[-1].get("action", "")):
                if int(object_id) in id_to_node:
                    selected_ids.add(int(object_id))

        # Safe fallback: retain interactive nodes rather than the entire scene clutter.
        if len(selected_ids) <= 1:
            for node in nodes:
                properties = self._upper_set(node.get("properties", []))
                if properties & {
                    "GRABBABLE", "HAS_SWITCH", "HAS_PLUG", "OPENABLE", "CAN_OPEN",
                    "CONTAINER", "CONTAINERS", "SURFACE",
                }:
                    selected_ids.add(int(node["id"]))

        return selected_ids

    # ------------------------------------------------------------------
    # Say score
    # ------------------------------------------------------------------
    def _score_with_llm(
        self,
        graph: dict,
        candidate_actions: Sequence[str],
        config: dict,
    ) -> Dict[str, float]:
        context_mode = str(
            config.get("saycan_say_context_mode", "state_summary")
        ).lower()
        history_summary = self._build_history_summary()
        active_rules = self._active_rules(config)

        if context_mode == "instruction_only":
            scene_section = (
                "Environment executability is handled only by the Can component."
            )
        else:
            scene_section = self._build_scene_summary(
                graph, candidate_actions
            )

        indexed_actions = "\n".join(
            f"{index}. {action}"
            for index, action in enumerate(candidate_actions)
        )

        system_prompt = (
            "You are the Say component of a SayCan planner. Score how useful "
            "each candidate skill is as the immediate next step for completing "
            "the instruction. A separate Can component evaluates physical "
            "executability. Prefer coherent progress, respect conditional "
            "instructions and active rules, and avoid repeating failed skills. "
            "Return valid JSON only."
        )
        user_prompt = f"""
Instruction:
{self.goal}

Candidate-local environment context:
{scene_section}

Previously selected skills and feedback:
{history_summary}

Active rules:
{active_rules}

Candidate skills:
{indexed_actions}

Return exactly this JSON schema:
{{"scores": [0, 0, ...]}}
The array must contain exactly {len(candidate_actions)} numbers in candidate
order. Every score must be between 0 and 100.
""".strip()

        try:
            response = self.llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format="json_object",
            )
            scores = self._parse_llm_scores(
                response, len(candidate_actions)
            )
        except Exception as exc:
            self.logger.error(f"LLM scoring failed: {exc}")
            scores = None

        if scores is None:
            self.logger.error(
                "Invalid Say response; using generic lexical fallback."
            )
            return self._heuristic_say_scores(
                candidate_actions, config
            )

        return {
            action: max(0.0, min(1.0, float(score) / 100.0))
            for action, score in zip(candidate_actions, scores)
        }

    def _parse_llm_scores(self, response: str, expected_count: int) -> Optional[List[float]]:
        if not response:
            return None

        try:
            payload = json.loads(response)
            values = payload.get("scores")
            if isinstance(values, list) and len(values) == expected_count:
                return [float(value) for value in values]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        # Defensive fallback for a model that ignored JSON mode.
        numbers = re.findall(r"-?\d+(?:\.\d+)?", response)
        if len(numbers) == expected_count:
            return [float(value) for value in numbers]
        return None

    def _heuristic_say_scores(
        self,
        candidate_actions: Sequence[str],
        config: dict,
    ) -> Dict[str, float]:
        """Generic emergency fallback without task-specific action sequences."""
        goal_terms = self._extract_goal_terms(self.goal)
        scores: Dict[str, float] = {}

        for action in candidate_actions:
            if action == "done()":
                scores[action] = 0.0
                continue
            if action == "[wait]":
                scores[action] = 0.25 if (
                    config.get("dynamic_events")
                    or config.get("scheduled_rules")
                    or self._last_action_failed()
                ) else 0.02
                continue
            if action.lower().startswith("[ask]"):
                scores[action] = 0.55 if (
                    config.get("require_ask_to_pass", False)
                    or "user_clarification_reply" in config
                ) else 0.08
                continue

            compact_action = self._compact(action)
            overlap = sum(
                1 for term in goal_terms if term in compact_action
            )
            score = 0.12 + min(0.66, 0.22 * overlap)

            if self.action_history:
                last_action = str(
                    self.action_history[-1].get("action", "")
                )
                if action == last_action:
                    score *= 0.35

            scores[action] = min(1.0, score)

        return scores

    def _score_affordance(
        self,
        graph: dict,
        candidate_actions: Sequence[str],
        config: dict,
    ) -> Dict[str, float]:
        """Compute task-independent physical executability from the graph."""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        id_to_node = {
            int(node["id"]): node
            for node in nodes
            if "id" in node
        }
        character = self._get_character(nodes)
        character_id = int(character["id"]) if character else 1

        close_ids = {
            int(edge["to_id"])
            for edge in edges
            if int(edge.get("from_id", -1)) == character_id
            and str(edge.get("relation_type", "")).upper() == "CLOSE"
        }
        held_ids = {
            int(edge["to_id"])
            for edge in edges
            if int(edge.get("from_id", -1)) == character_id
            and str(edge.get("relation_type", "")).upper().startswith("HOLDS")
        }

        scores: Dict[str, float] = {}
        for action in candidate_actions:
            action_name = self._action_name(action)
            ids = [
                int(value)
                for value in self.ID_PATTERN.findall(action)
            ]

            if action == "done()":
                scores[action] = 0.0
                continue
            if action == "[wait]" or action.lower().startswith("[ask]"):
                scores[action] = 1.0
                continue
            if (
                not action_name
                or not ids
                or any(node_id not in id_to_node for node_id in ids)
            ):
                scores[action] = 0.0
                continue

            primary_id = ids[0]
            primary_node = id_to_node[primary_id]
            primary_properties = self._upper_set(
                primary_node.get("properties", [])
            )
            primary_states = self._effective_states(primary_node)

            if "BROKEN" in primary_states and action_name != "walk":
                scores[action] = 0.0
                continue

            if action_name in {"walk", "walktowards"}:
                scores[action] = 0.0 if primary_id in held_ids else 1.0
                continue

            if action_name == "grab":
                blocked = self._inside_closed_container(
                    primary_id, graph, id_to_node
                )
                scores[action] = 1.0 if (
                    "GRABBABLE" in primary_properties
                    and primary_id not in held_ids
                    and primary_id in close_ids
                    and not blocked
                ) else 0.0
                continue

            if action_name in {"open", "close"}:
                if (
                    not primary_properties.intersection(
                        self.OPENABLE_PROPERTIES
                    )
                    or primary_id not in close_ids
                ):
                    scores[action] = 0.0
                elif action_name == "open":
                    scores[action] = 0.0 if "OPEN" in primary_states else 1.0
                else:
                    scores[action] = 0.0 if "CLOSED" in primary_states else 1.0
                continue

            if action_name in {"switchon", "switchoff"}:
                if (
                    "HAS_SWITCH" not in primary_properties
                    or primary_id not in close_ids
                ):
                    scores[action] = 0.0
                elif action_name == "switchon":
                    if "ON" in primary_states:
                        scores[action] = 0.0
                    elif (
                        primary_properties.intersection(
                            self.OPENABLE_PROPERTIES
                        )
                        and "OPEN" in primary_states
                    ):
                        scores[action] = 0.0
                    else:
                        scores[action] = 1.0
                else:
                    scores[action] = 0.0 if "OFF" in primary_states else 1.0
                continue

            if action_name in {"plugin", "plugout"}:
                if (
                    "HAS_PLUG" not in primary_properties
                    or primary_id not in close_ids
                ):
                    scores[action] = 0.0
                elif action_name == "plugin":
                    scores[action] = (
                        0.0 if "PLUGGED_IN" in primary_states else 1.0
                    )
                else:
                    scores[action] = (
                        0.0 if "PLUGGED_OUT" in primary_states else 1.0
                    )
                continue

            if action_name in {"putin", "putback"} and len(ids) >= 2:
                source_id, destination_id = ids[0], ids[1]
                destination = id_to_node[destination_id]
                destination_properties = self._upper_set(
                    destination.get("properties", [])
                )
                destination_states = self._effective_states(destination)

                if (
                    source_id not in held_ids
                    or destination_id not in close_ids
                ):
                    scores[action] = 0.0
                elif action_name == "putin":
                    is_container = bool(
                        destination_properties.intersection(
                            self.CONTAINER_PROPERTIES
                            | self.OPENABLE_PROPERTIES
                        )
                    )
                    if not is_container:
                        scores[action] = 0.0
                    elif (
                        destination_properties.intersection(
                            self.OPENABLE_PROPERTIES
                        )
                        and "OPEN" not in destination_states
                    ):
                        scores[action] = 0.0
                    else:
                        scores[action] = 1.0
                else:
                    scores[action] = 1.0 if (
                        destination_properties.intersection(
                            self.SURFACE_PROPERTIES
                        )
                    ) else 0.0
                continue

            if action_name == "wash":
                near_sink = any(
                    destination_id in close_ids
                    and str(
                        id_to_node.get(destination_id, {}).get(
                            "class_name", ""
                        )
                    ).lower() in {"sink", "dishwasher"}
                    for destination_id in close_ids
                )
                scores[action] = 1.0 if (
                    primary_id in held_ids and near_sink
                ) else 0.0
                continue

            if action_name == "cut":
                holding_knife = any(
                    "knife" in str(
                        id_to_node.get(object_id, {}).get(
                            "class_name", ""
                        )
                    ).lower()
                    for object_id in held_ids
                )
                target_close = (
                    primary_id in close_ids or primary_id in held_ids
                )
                scores[action] = 1.0 if (
                    holding_knife and target_close
                ) else 0.0
                continue

            if action_name == "pour" and len(ids) >= 2:
                source_id, destination_id = ids[0], ids[1]
                scores[action] = 1.0 if (
                    source_id in held_ids
                    and destination_id in close_ids
                ) else 0.0
                continue

            scores[action] = 0.0

        return scores

    def _select_action(
        self,
        candidate_actions: Sequence[str],
        say_scores: Dict[str, float],
        can_scores: Dict[str, float],
        combined_scores: Dict[str, float],
    ) -> str:
        if not candidate_actions:
            return "done()"

        max_combined = max(combined_scores.values(), default=0.0)
        if max_combined > 0:
            return max(
                candidate_actions,
                key=lambda action: (
                    combined_scores.get(action, 0.0),
                    can_scores.get(action, 0.0),
                    say_scores.get(action, 0.0),
                    -candidate_actions.index(action),
                ),
            )

        executable = [
            action for action in candidate_actions
            if can_scores.get(action, 0.0) > 0 and action != "done()"
        ]
        if executable:
            return max(executable, key=lambda action: say_scores.get(action, 0.0))
        return "done()"

    # ------------------------------------------------------------------
    # Prompt and graph helpers
    # ------------------------------------------------------------------
    def _build_scene_summary(self, graph: dict, candidate_actions: Sequence[str]) -> str:
        referenced_ids = {
            int(value)
            for action in candidate_actions
            for value in self.ID_PATTERN.findall(action)
        }
        id_to_node = {
            int(node["id"]): node
            for node in graph.get("nodes", [])
            if "id" in node
        }

        lines: List[str] = []
        for node_id in sorted(referenced_ids):
            node = id_to_node.get(node_id)
            if not node:
                continue
            properties = sorted(self._upper_set(node.get("properties", [])))
            states = sorted(self._effective_states(node))
            lines.append(
                f"- {node.get('class_name', 'object')}({node_id}): "
                f"states={states}, properties={properties}"
            )

        for edge in graph.get("edges", []):
            from_id = int(edge.get("from_id", -1))
            to_id = int(edge.get("to_id", -1))
            if from_id not in referenced_ids and to_id not in referenced_ids:
                continue
            from_node = id_to_node.get(from_id)
            to_node = id_to_node.get(to_id)
            if not from_node or not to_node:
                continue
            relation = edge.get("relation_type", edge.get("relation", ""))
            lines.append(
                f"- {from_node.get('class_name')}({from_id}) "
                f"--{relation}--> {to_node.get('class_name')}({to_id})"
            )

        return "\n".join(lines[:120]) if lines else "No relevant graph facts available."

    def _build_history_summary(self, limit: int = 8) -> str:
        if not self.action_history:
            return "No previous actions."

        lines = []
        for entry in self.action_history[-limit:]:
            status = "success" if entry.get("success") else "failed"
            detail = entry.get("error") or entry.get("message") or ""
            line = f"- {entry.get('action', '')}: {status}"
            if detail:
                line += f" ({detail})"
            lines.append(line)
        return "\n".join(lines)

    def _active_rules(self, config: dict) -> str:
        rules = config.get("scheduled_rules", []) or []
        if not rules:
            return "No active rules provided."
        return "\n".join(f"- {rule.get('rule_text', str(rule))}" for rule in rules)

    def _candidate_priority(self, action: str, goal: str, graph: dict) -> float:
        if action == "done()":
            return -100.0
        if action == "[wait]":
            return -50.0
        if action.lower().startswith("[ask]"):
            return -40.0

        priority = 0.0
        compact_action = self._compact(action)
        goal_terms = self._extract_goal_terms(goal)
        for term in goal_terms:
            if term in compact_action:
                priority += 10.0

        action_name = self._action_name(action)
        action_bonus = {
            "grab": 5.0,
            "putin": 4.5,
            "putback": 4.0,
            "switchon": 3.5,
            "open": 3.0,
            "close": 2.5,
            "walk": 2.0,
            "wash": 5.0,
            "cut": 5.0,
            "pour": 5.0,
        }
        priority += action_bonus.get(action_name, 0.0)

        # Stable tie-breaker independent of Python hash randomization.
        ids = [int(value) for value in self.ID_PATTERN.findall(action)]
        if ids:
            priority -= ids[0] * 1e-6
        return priority

    def _extract_goal_terms(self, goal: str) -> Set[str]:
        words = re.findall(r"[A-Za-z0-9_]+", goal.lower())
        terms = {
            self._compact(word)
            for word in words
            if word not in self.STOPWORDS
            and word not in self.ACTION_WORDS
            and len(self._compact(word)) >= 3
        }

        compact_goal = self._compact(goal)
        phrase_aliases = {
            "remotecontrol": {"remote", "control", "remotecontrol"},
            "television": {"tv", "television"},
            "microwaveoven": {"microwave"},
        }
        for phrase, aliases in phrase_aliases.items():
            if phrase in compact_goal or any(alias in compact_goal for alias in aliases):
                terms.update(aliases)

        # Preserve task verbs that imply support objects.
        for keyword in self.SKILL_SUPPORT_CLASSES:
            if keyword in compact_goal:
                terms.add(keyword)
        return terms

    def _handle_ask(
        self,
        action: str,
        step: int,
        graph: dict,
        config: dict,
    ) -> Optional[Tuple[bool, str]]:
        self.action_history.append(
            {
                "step": step,
                "action": action,
                "success": True,
                "reasoning": "Selected as a clarification skill.",
            }
        )
        self._write_step_log(
            step, action, self._observed_items(graph)
        )

        if "user_clarification_reply" in config:
            clarification = str(
                config.pop("user_clarification_reply")
            ).strip()
            if clarification:
                self.goal = (
                    f"{self.goal} User clarification: {clarification}"
                )
                self.action_history.append(
                    {
                        "step": step + 0.5,
                        "action": f"[USER_REPLY] {clarification}",
                        "success": True,
                        "reasoning": "User clarified the instruction.",
                    }
                )
                self.logger.info(
                    f"User clarification received: {clarification}"
                )
            return None

        if str(config.get("on_ask_policy", "FAIL")).upper() == "SUCCESS":
            self.logger.info(
                "✅ SUCCESS: clarification request satisfied the policy."
            )
            return True, "Goal Reached (Help Asked)"

        self.logger.error(
            "❌ FAILED: clarification was requested but is not permitted."
        )
        return False, "Agent requested help, which is not permitted"

    def _ask_requirement_met(self, config: dict) -> bool:
        if not config.get("require_ask_to_pass", False):
            return True
        return any(
            str(entry.get("action", "")).lower().startswith("[ask]")
            for entry in self.action_history
        )

    @staticmethod
    def _condition_is_active(
        condition: dict,
        current_step: int,
    ) -> bool:
        return (
            int(condition.get("start_step", 0))
            <= current_step
            <= int(condition.get("end_step", 999999))
        )

    def _log_module_output(
        self,
        module_name: str,
        step: int,
        payload: dict,
    ) -> None:
        try:
            self.logger.log_module_output(
                module_name, step, payload
            )
        except Exception:
            self.logger.info(
                json.dumps(payload, ensure_ascii=False)
            )

    def _inside_closed_container(
        self,
        object_id: int,
        graph: dict,
        id_to_node: Dict[int, dict],
    ) -> bool:
        for edge in graph.get("edges", []):
            if int(edge.get("from_id", -1)) != object_id:
                continue
            relation = str(edge.get("relation_type", edge.get("relation", ""))).upper()
            if relation != "INSIDE":
                continue
            container = id_to_node.get(int(edge.get("to_id", -1)))
            if not container:
                continue
            properties = self._upper_set(container.get("properties", []))
            states = self._effective_states(container)
            if properties & self.OPENABLE_PROPERTIES and "OPEN" not in states:
                return True
        return False

    def _repetition_penalty(self, action: str) -> float:
        if not self.action_history:
            return 1.0

        penalty = 1.0
        consecutive_matches = 0
        for entry in reversed(self.action_history):
            if entry.get("action") != action:
                break
            consecutive_matches += 1
            penalty *= 0.1 if not entry.get("success", False) else 0.35

        if consecutive_matches == 0:
            # Penalize a recently failed action even if another action occurred after it.
            for entry in self.action_history[-3:]:
                if entry.get("action") == action and not entry.get("success", False):
                    penalty *= 0.25
                    break
        return penalty

    def _last_action_failed(self) -> bool:
        return bool(self.action_history and not self.action_history[-1].get("success", False))

    def _effective_states(self, node: dict) -> Set[str]:
        """Return states without mutating the environment graph.

        The project's initialization wrapper may add ON without removing OFF.
        We retain ON as the effective state in that specific conflict because an
        explicit override is intended to make the appliance active. Similar
        deterministic handling is used for other mutually exclusive pairs.
        """
        states = self._upper_set(node.get("states", []))
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

    def _deduplicate_graph(self, graph: dict) -> dict:
        nodes_by_id: Dict[int, dict] = {}
        for node in graph.get("nodes", []):
            if "id" not in node:
                continue
            node_id = int(node["id"])
            if node_id not in nodes_by_id:
                nodes_by_id[node_id] = dict(node)
                continue

            existing = nodes_by_id[node_id]
            existing["states"] = sorted(
                self._upper_set(existing.get("states", []))
                | self._upper_set(node.get("states", []))
            )
            existing["properties"] = sorted(
                self._upper_set(existing.get("properties", []))
                | self._upper_set(node.get("properties", []))
            )

        edge_keys = set()
        edges = []
        for edge in graph.get("edges", []):
            key = (
                int(edge.get("from_id", -1)),
                str(edge.get("relation_type", edge.get("relation", ""))).upper(),
                int(edge.get("to_id", -1)),
            )
            if key in edge_keys:
                continue
            edge_keys.add(key)
            normalized = dict(edge)
            normalized["relation_type"] = key[1]
            edges.append(normalized)

        return {"nodes": list(nodes_by_id.values()), "edges": edges}

    def _check_success(self, graph: dict, condition: dict) -> bool:
        if not condition:
            return False

        mode = str(condition.get("mode", "SINGLE")).upper()
        if mode in {"AND", "OR"}:
            subconditions = condition.get("conditions", [])
            if not subconditions:
                return False
            results = [self._check_success(graph, subcondition) for subcondition in subconditions]
            return all(results) if mode == "AND" else any(results)

        target_class = str(condition.get("target_class", "ANY"))
        min_count = int(condition.get("min_count", 1))
        required_states = self._upper_set(condition.get("states", []))
        required_properties = self._upper_set(condition.get("properties", []))
        relation_spec = condition.get("relation")
        destination_class = condition.get("destination_class")
        destination_states = self._upper_set(condition.get("destination_states", []))
        destination_properties = self._upper_set(condition.get("destination_properties", []))

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
            candidates = [
                node for node in nodes
                if str(node.get("class_name", "")).lower() == target_class.lower()
            ]

        valid_candidates = []
        allowed_relations = {
            value.strip().upper()
            for value in str(relation_spec or "").split("|")
            if value.strip()
        }

        for candidate in candidates:
            if not required_states.issubset(self._effective_states(candidate)):
                continue
            if not required_properties.issubset(self._upper_set(candidate.get("properties", []))):
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
                    if not destination_states.issubset(self._effective_states(destination)):
                        continue
                    if not destination_properties.issubset(
                        self._upper_set(destination.get("properties", []))
                    ):
                        continue
                    matched = True
                    break
                if not matched:
                    continue

            valid_candidates.append(candidate)

        return len(valid_candidates) >= min_count

    def _write_step_log(
        self,
        step: int,
        action: str,
        observed_items: Sequence[str],
    ) -> None:
        """Write a step even when a project logger has an older signature."""
        try:
            self.logger.write_step(step, action, None, list(observed_items))
            return
        except Exception as exc:
            self.logger.error(f"Markdown step logging failed: {exc}")

        # Last-resort fallback for the current AgentLogger implementation.
        log_file = getattr(self.logger, "log_file", None)
        if not log_file:
            return
        try:
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(f"## Step {step}\n")
                handle.write(f"- **Action**: `{action}`\n")
                preview = ", ".join(list(observed_items)[:15])
                suffix = "..." if len(observed_items) > 15 else ""
                handle.write(
                    f"- **Observed Items ({len(observed_items)})**: "
                    f"{preview}{suffix}\n\n"
                )
        except Exception as exc:
            self.logger.error(f"Fallback markdown logging failed: {exc}")

    def _log_scoring(
        self,
        step: int,
        candidate_actions: Sequence[str],
        say_scores: Dict[str, float],
        can_scores: Dict[str, float],
        combined_scores: Dict[str, float],
        best_action: str,
    ) -> None:
        ranked = sorted(
            candidate_actions,
            key=lambda action: combined_scores.get(action, 0.0),
            reverse=True,
        )
        payload = {
            "selected_action": best_action,
            "top_candidates": [
                {
                    "action": action,
                    "say": round(say_scores.get(action, 0.0), 4),
                    "can": round(can_scores.get(action, 0.0), 4),
                    "combined": round(combined_scores.get(action, 0.0), 4),
                }
                for action in ranked[:10]
            ],
        }
        try:
            self.logger.log_module_output("SayCanScoring", step, payload)
        except Exception:
            self.logger.info(json.dumps(payload, ensure_ascii=False))

    @staticmethod
    def _observed_items(graph: dict) -> List[str]:
        items = []
        seen = set()
        for node in graph.get("nodes", []):
            node_id = int(node.get("id", -1))
            if node_id in seen:
                continue
            seen.add(node_id)
            states = node.get("states", [])
            state_suffix = f" [{','.join(states)}]" if states else ""
            items.append(f"{node.get('class_name', 'object')}({node_id}){state_suffix}")
        return items

    @staticmethod
    def _coerce_action_success(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, dict):
            return all(bool(item) for item in value.values()) if value else False
        if isinstance(value, (list, tuple)):
            return all(bool(item) for item in value) if value else False
        return bool(value)

    @staticmethod
    def _get_character(nodes: Iterable[dict]) -> Optional[dict]:
        return next(
            (
                node for node in nodes
                if str(node.get("class_name", "")).lower() == "character"
            ),
            None,
        )

    @classmethod
    def _action_name(cls, action: str) -> str:
        match = cls.ACTION_PATTERN.search(action)
        return match.group(1).lower() if match else ""

    @staticmethod
    def _format_unary(action: str, class_name: str, object_id: int) -> str:
        return f"[{action}] <{class_name}> ({object_id})"

    @staticmethod
    def _format_binary(
        action: str,
        source_class: str,
        source_id: int,
        destination_class: str,
        destination_id: int,
    ) -> str:
        return (
            f"[{action}] <{source_class}> ({source_id}) "
            f"<{destination_class}> ({destination_id})"
        )

    @staticmethod
    def _upper_set(values: Iterable[str]) -> Set[str]:
        return {str(value).upper() for value in values or []}

    @staticmethod
    def _compact(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).lower())