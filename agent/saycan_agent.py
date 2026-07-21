import json
import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .utils.llm_client import LLMClient
from .base_agent import BaseAgent


SAYCAN_AGENT_VERSION = "SAYCAN-VH-v3.3-EXPLORATION-2026-07-17"
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

    # Unity exposes a few graph properties more broadly than the executable
    # action set. These filters keep candidate generation aligned with the
    # actual simulator without encoding task-instance solutions.
    NON_OPENABLE_CATEGORIES = {"FOOD", "DRINKS", "CLOTHES", "DECOR"}
    OPENABLE_CLASS_HINTS = {
        "cabinet", "cupboard", "drawer", "fridge", "refrigerator",
        "microwave", "microwaveoven", "oven", "dishwasher",
        "washingmachine", "dryer", "closet", "door", "box",
        "trashcan", "garbagecan", "coffeemaker",
    }
    ACTIVATION_TASK_TERMS = {
        "heat", "hot", "warm", "cook", "boil", "toast", "bake",
    }
    ROOM_CATEGORIES = {"ROOM", "ROOMS"}
    NAVIGATION_CLASS_HINTS = {
        "door", "doorjamb", "doorframe", "entrance", "hallway",
    }

    def __init__(
        self,
        model_name: str = "gpt-5.4-mini",
        scenario_id: str = "",
    ):
        super().__init__(model_name=model_name, scenario_id=scenario_id)
        self.llm = LLMClient(model_name=model_name)
        self.version = self.VERSION

    # ------------------------------------------------------------------
    # Stepwise Agent Action Selection
    # ------------------------------------------------------------------
    def get_action(
        self,
        obs: dict,
        config: dict,
        env_info: dict = None,
    ) -> str:
        """Select exactly one action without modifying the environment."""
        env_info = env_info or {}

        goal = str(config.get("goal_instruction", "")).strip()
        if not goal:
            raise ValueError(
                "SayCanAgent requires config['goal_instruction']."
            )

        step = int(env_info.get("step", 0))
        action_history = list(env_info.get("action_history", []) or [])
        logger = env_info.get("logger")

        if step == 0:
            self._safe_info(
                logger,
                f"[{self.VERSION}] Starting SayCan-VH episode "
                f"for goal: {goal}",
            )
            self._log_module_output(
                logger=logger,
                module_name="SayCanVersion",
                step=0,
                payload={
                    "version": self.VERSION,
                    "implementation": "SayCan (VirtualHome adaptation)",
                    "interface": "BaseAgent.get_action",
                    "say_score_mode": self.SAY_SCORE_MODE,
                    "can_score_mode": self.CAN_SCORE_MODE,
                    "say_context_mode": config.get(
                        "saycan_say_context_mode",
                        "state_summary",
                    ),
                    "task_semantics_in_can": False,
                },
            )

        graph = self._deduplicate_graph(
            self._extract_graph(obs)
        )

        generated_actions = self._generate_candidate_actions(
            graph=graph,
            goal=goal,
            config=config,
            action_history=action_history,
        )
        if not generated_actions:
            self._safe_error(
                logger,
                "No candidate skills could be generated; returning [wait].",
            )
            return "[wait]"

        # Score physical executability first. Sending only currently executable
        # candidates to the language model prevents an invalid action from
        # receiving a high Say score and also reduces prompt size.
        generated_can_scores = self._score_affordance(
            graph=graph,
            candidate_actions=generated_actions,
            config=config,
        )
        candidate_actions = [
            action for action in generated_actions
            if generated_can_scores.get(action, 0.0) > 0.0
        ]
        if not candidate_actions:
            self._safe_error(
                logger,
                "No executable SayCan candidates remain; returning [wait].",
            )
            return "[wait]"

        can_scores = {
            action: generated_can_scores[action]
            for action in candidate_actions
        }
        say_scores = self._score_with_llm(
            graph=graph,
            candidate_actions=candidate_actions,
            config=config,
            goal=goal,
            action_history=action_history,
            logger=logger,
        )

        combined_scores: Dict[str, float] = {}
        for action in candidate_actions:
            combined_scores[action] = (
                say_scores.get(action, 0.0)
                * can_scores.get(action, 0.0)
                * self._repetition_penalty(
                    action,
                    action_history,
                )
            )

        best_action = self._select_action(
            candidate_actions=candidate_actions,
            say_scores=say_scores,
            can_scores=can_scores,
            combined_scores=combined_scores,
        )

        self._log_scoring(
            logger=logger,
            step=step,
            candidate_actions=candidate_actions,
            say_scores=say_scores,
            can_scores=can_scores,
            combined_scores=combined_scores,
            best_action=best_action,
        )

        self._safe_info(
            logger,
            f"[{self.VERSION}] Step {step}: selected '{best_action}' "
            f"(Say={say_scores.get(best_action, 0.0):.3f}, "
            f"Can={can_scores.get(best_action, 0.0):.3f}, "
            f"Combined={combined_scores.get(best_action, 0.0):.3f})",
        )
        return best_action

    @staticmethod
    def _extract_graph(obs: dict) -> dict:
        if not isinstance(obs, dict):
            return {"nodes": [], "edges": []}
        if "nodes" in obs and "edges" in obs:
            return obs
        graph = obs.get("graph")
        if isinstance(graph, dict):
            return graph
        return {"nodes": [], "edges": []}

    @staticmethod
    def _safe_info(logger, message: str) -> None:
        if logger is not None and hasattr(logger, "info"):
            logger.info(message)

    @staticmethod
    def _safe_error(logger, message: str) -> None:
        if logger is not None and hasattr(logger, "error"):
            logger.error(message)

    def _generate_candidate_actions(
        self,
        graph: dict,
        goal: str,
        config: dict,
        action_history: Sequence[dict],
    ) -> List[str]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        id_to_node = {int(node["id"]): node for node in nodes if "id" in node}
        character = self._get_character(nodes)
        character_id = int(character["id"]) if character else 1

        goal_terms = self._extract_goal_terms(goal)
        compact_goal = self._compact(goal)
        support_classes: Set[str] = set()
        for term in goal_terms:
            support_classes.update(self.SKILL_SUPPORT_CLASSES.get(term, set()))

        selected_ids = self._select_relevant_node_ids(
            graph,
            goal_terms,
            action_history,
        )

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

            # When the explicit target is not visible under partial
            # observation, candidate selection falls back to rooms and
            # navigation landmarks. Walking to them is exploration, not an
            # interaction with an unrelated visible device.
            if self._is_navigation_target(node):
                if (
                    node_id not in held_ids
                    and not self._is_current_room(
                        node_id=node_id,
                        graph=graph,
                        character_id=character_id,
                    )
                ):
                    actions.append(
                        self._format_unary("walk", class_name, node_id)
                    )
                continue

            # Walking is the universal enabling action for object interactions.
            # Do not generate walk-to-self actions for objects already in hand.
            if node_id not in held_ids:
                actions.append(self._format_unary("walk", class_name, node_id))

            if "GRABBABLE" in properties and node_id not in held_ids:
                actions.append(self._format_unary("grab", class_name, node_id))

            if self._is_openable_target(node):
                if "OPEN" not in states:
                    actions.append(self._format_unary("open", class_name, node_id))
                if "CLOSED" not in states:
                    actions.append(self._format_unary("close", class_name, node_id))

            is_goal_target = self._node_matches_terms(node, goal_terms)
            is_support_device = self._compact(class_name) in {
                self._compact(item) for item in support_classes
            }

            if "HAS_SWITCH" in properties:
                if (
                    "ON" not in states
                    and self._should_offer_switch_on(
                        compact_goal=compact_goal,
                        is_goal_target=is_goal_target,
                        is_support_device=is_support_device,
                    )
                ):
                    actions.append(self._format_unary("switchon", class_name, node_id))
                if (
                    "OFF" not in states
                    and self._goal_requests_switch_off(compact_goal)
                    and is_goal_target
                ):
                    actions.append(self._format_unary("switchoff", class_name, node_id))

            if "HAS_PLUG" in properties:
                if (
                    "PLUGGED_IN" not in states
                    and (is_support_device or self._goal_requests_plug_in(compact_goal))
                ):
                    actions.append(self._format_unary("plugin", class_name, node_id))
                if (
                    "PLUGGED_OUT" not in states
                    and self._goal_requests_plug_out(compact_goal)
                    and is_goal_target
                ):
                    actions.append(self._format_unary("plugout", class_name, node_id))

            if ("wash" in compact_goal or "clean" in compact_goal) and "GRABBABLE" in properties:
                actions.append(self._format_unary("wash", class_name, node_id))
            if ("cut" in compact_goal or "slice" in compact_goal) and "CUTTABLE" in properties:
                actions.append(self._format_unary("cut", class_name, node_id))

        held_nodes = [id_to_node[node_id] for node_id in held_ids if node_id in id_to_node]
        containers = [
            node for node in selected_nodes
            if self._is_container_target(node)
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
        if self._last_action_failed(action_history):
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

        actions = list(dict.fromkeys(actions))
        actions.sort(key=lambda action: self._candidate_priority(action, goal, graph), reverse=True)

        max_candidates = max(5, int(config.get("saycan_max_candidates", 28)))
        if len(actions) > max_candidates:
            # Preserve wait and ask actions when truncating.
            special = [
                action for action in actions
                if action == "[wait]"
                or action.lower().startswith("[ask]")
            ]
            regular = [
                action for action in actions
                if action not in special
            ]
            actions = regular[: max_candidates - len(special)] + special

        return actions

    def _select_relevant_node_ids(
        self,
        graph: dict,
        goal_terms: Set[str],
        action_history: Sequence[dict],
    ) -> Set[int]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        id_to_node = {int(node["id"]): node for node in nodes if "id" in node}

        selected_ids: Set[int] = set()
        directly_relevant_ids: Set[int] = set()
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
                directly_relevant_ids.add(node_id)
            elif useful_fixture and class_name in support_classes:
                selected_ids.add(node_id)
                directly_relevant_ids.add(node_id)

        # Keep one-hop spatial parents and children of directly relevant objects.
        # Do not expand from the character node: doing so would pull every CLOSE
        # object in the room into the candidate set (e.g. wall phones and light
        # switches for a television task).
        frontier = set(directly_relevant_ids)
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
        if action_history:
            for object_id in self.ID_PATTERN.findall(
                str(action_history[-1].get("action", ""))
            ):
                if int(object_id) in id_to_node:
                    selected_ids.add(int(object_id))

        character = self._get_character(nodes)
        if character is not None:
            selected_ids.add(int(character["id"]))

        # Under partial observation, absence of the explicit goal target must
        # trigger exploration rather than manipulation of arbitrary visible
        # devices. For example, when a TV is not visible, a wall phone or a
        # light switch must not become a substitute target merely because it is
        # switchable. Rooms and navigation landmarks are generic search skills.
        if not directly_relevant_ids:
            character = self._get_character(nodes)
            character_id = int(character["id"]) if character else 1
            for node in nodes:
                node_id = int(node["id"])
                if not self._is_navigation_target(node):
                    continue
                if self._is_current_room(
                    node_id=node_id,
                    graph=graph,
                    character_id=character_id,
                ):
                    continue
                selected_ids.add(node_id)

        return selected_ids

    # ------------------------------------------------------------------
    # Say score
    # ------------------------------------------------------------------
    def _score_with_llm(
        self,
        graph: dict,
        candidate_actions: Sequence[str],
        config: dict,
        goal: str,
        action_history: Sequence[dict],
        logger=None,
    ) -> Dict[str, float]:
        context_mode = str(
            config.get("saycan_say_context_mode", "state_summary")
        ).lower()
        history_summary = self._build_history_summary(action_history)
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
            "executability. Treat an if/when clause as a condition to check, "
            "not as a state that should be restored. Focus on the requested "
            "effect in the main clause, preserve progress already made, and "
            "avoid irrelevant device controls or action cycles. If the named "
            "target is not visible and the candidates are navigation actions, "
            "prefer the location most likely to reveal the target rather than "
            "acting on an unrelated object. Return valid JSON only."
        )
        user_prompt = f"""
Instruction:
{goal}

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
            self._safe_error(logger, f"LLM scoring failed: {exc}")
            scores = None

        if scores is None:
            self._safe_error(
                logger,
                "Invalid Say response; using generic lexical fallback.",
            )
            return self._heuristic_say_scores(
                candidate_actions=candidate_actions,
                config=config,
                goal=goal,
                action_history=action_history,
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
        goal: str,
        action_history: Sequence[dict],
    ) -> Dict[str, float]:
        """Generic emergency fallback without task-specific action sequences."""
        goal_terms = self._extract_goal_terms(goal)
        scores: Dict[str, float] = {}

        for action in candidate_actions:
            if action == "[wait]":
                scores[action] = 0.25 if self._last_action_failed(action_history) else 0.15
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

            if action_history:
                last_action = str(
                    action_history[-1].get("action", "")
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
                    not self._is_openable_target(primary_node)
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
                    is_container = self._is_container_target(destination)
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
            return "[wait]"

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
            if can_scores.get(action, 0.0) > 0
        ]
        if executable:
            return max(executable, key=lambda action: say_scores.get(action, 0.0))
        return "[wait]"

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

    def _build_history_summary(
        self,
        action_history: Sequence[dict],
        limit: int = 8,
    ) -> str:
        if not action_history:
            return "No previous actions."

        lines = []
        for entry in action_history[-limit:]:
            success = entry.get("success", entry.get("action_success"))
            if success is True:
                status = "success"
            elif success is False:
                status = "failed"
            else:
                status = "unknown"
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

    def _log_module_output(
        self,
        logger,
        module_name: str,
        step: int,
        payload: dict,
    ) -> None:
        if logger is None:
            return
        try:
            logger.log_module_output(
                module_name, step, payload
            )
        except Exception:
            self._safe_info(
                logger,
                json.dumps(payload, ensure_ascii=False),
            )

    def _node_matches_terms(self, node: dict, goal_terms: Set[str]) -> bool:
        compact_name = self._compact(node.get("class_name", ""))
        return any(
            len(term) >= 2
            and (term in compact_name or compact_name in term)
            for term in goal_terms
        )

    def _is_navigation_target(self, node: dict) -> bool:
        category = str(node.get("category", "")).upper()
        compact_name = self._compact(node.get("class_name", ""))
        if category in self.ROOM_CATEGORIES:
            return True
        return any(
            hint in compact_name
            for hint in self.NAVIGATION_CLASS_HINTS
        )

    @staticmethod
    def _is_current_room(
        node_id: int,
        graph: dict,
        character_id: int,
    ) -> bool:
        return any(
            int(edge.get("from_id", -1)) == character_id
            and int(edge.get("to_id", -1)) == node_id
            and str(
                edge.get("relation_type", edge.get("relation", ""))
            ).upper() == "INSIDE"
            for edge in graph.get("edges", [])
        )

    def _is_openable_target(self, node: dict) -> bool:
        properties = self._upper_set(node.get("properties", []))
        if not properties.intersection(self.OPENABLE_PROPERTIES):
            return False

        category = str(node.get("category", "")).upper()
        if category in self.NON_OPENABLE_CATEGORIES:
            return False

        compact_name = self._compact(node.get("class_name", ""))
        has_class_hint = any(
            self._compact(hint) in compact_name
            or compact_name in self._compact(hint)
            for hint in self.OPENABLE_CLASS_HINTS
        )
        return bool(
            properties.intersection(self.CONTAINER_PROPERTIES)
            or has_class_hint
        )

    def _is_container_target(self, node: dict) -> bool:
        properties = self._upper_set(node.get("properties", []))
        return bool(
            properties.intersection(self.CONTAINER_PROPERTIES)
            or self._is_openable_target(node)
        )

    def _should_offer_switch_on(
        self,
        compact_goal: str,
        is_goal_target: bool,
        is_support_device: bool,
    ) -> bool:
        explicit_on = any(
            phrase in compact_goal
            for phrase in (
                "turnon", "turniton", "switchon", "switchiton",
                "poweron", "poweriton", "activate", "start",
            )
        )
        task_needs_activation = any(
            term in compact_goal for term in self.ACTIVATION_TASK_TERMS
        )
        explicit_on = explicit_on or compact_goal.endswith("on")
        return (explicit_on and is_goal_target) or (
            task_needs_activation and is_support_device
        )

    @staticmethod
    def _goal_requests_switch_off(compact_goal: str) -> bool:
        return any(
            phrase in compact_goal
            for phrase in (
                "turnoff", "turnitoff", "switchoff", "switchitoff",
                "poweroff", "poweritoff", "deactivate", "stop",
            )
        )

    @staticmethod
    def _goal_requests_plug_in(compact_goal: str) -> bool:
        return any(
            phrase in compact_goal
            for phrase in ("plugin", "pluggedin", "connectpower")
        )

    @staticmethod
    def _goal_requests_plug_out(compact_goal: str) -> bool:
        return any(
            phrase in compact_goal
            for phrase in ("plugout", "unplug", "disconnectpower")
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

    def _repetition_penalty(
        self,
        action: str,
        action_history: Sequence[dict],
    ) -> float:
        if not action_history:
            return 1.0

        penalty = 1.0
        consecutive_matches = 0
        for entry in reversed(action_history):
            if entry.get("action") != action:
                break
            consecutive_matches += 1
            penalty *= 0.1 if not entry.get("success", False) else 0.35

        recent_actions = [
            str(entry.get("action", ""))
            for entry in action_history[-6:]
        ]

        if consecutive_matches == 0:
            # Penalize a recently failed action even if another action occurred after it.
            for entry in action_history[-3:]:
                success = entry.get("success", entry.get("action_success"))
                if entry.get("action") == action and success is False:
                    penalty *= 0.15
                    break

        # Detect an emerging A-B-A loop. This is task independent and only uses
        # the runner-provided action history.
        if len(recent_actions) >= 2 and action == recent_actions[-2]:
            penalty *= 0.08

        # Detect a sustained A-B-A-B loop and almost completely suppress either
        # member until another skill is attempted.
        if (
            len(recent_actions) >= 4
            and recent_actions[-4] == recent_actions[-2]
            and recent_actions[-3] == recent_actions[-1]
            and action in {recent_actions[-1], recent_actions[-2]}
        ):
            penalty *= 0.02

        return penalty

    @staticmethod
    def _last_action_failed(action_history: Sequence[dict]) -> bool:
        if not action_history:
            return False
        last = action_history[-1]
        success = last.get(
            "success",
            last.get("action_success"),
        )
        return success is False

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

    def _log_scoring(
        self,
        logger,
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
        if logger is None:
            return
        try:
            logger.log_module_output("SayCanScoring", step, payload)
        except Exception:
            self._safe_info(
                logger,
                json.dumps(payload, ensure_ascii=False),
            )

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