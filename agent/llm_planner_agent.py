import ast
import importlib.util
import json
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .utils.logger import AgentLogger
from .utils.llm_client import LLMClient
from .base_agent import BaseAgent


LLM_PLANNER_VERSION = "LLM-PLANNER-VH-OFFICIAL-HLP-v1.0-2026-07-16"


@dataclass(frozen=True)
class HighLevelSkill:
    action: str
    obj: Optional[str] = None
    target: Optional[str] = None

    def as_tuple(self) -> Tuple[str, ...]:
        if self.target:
            return (self.action, self.obj or "", self.target)
        if self.obj:
            return (self.action, self.obj)
        return (self.action,)

    def __str__(self) -> str:
        return " ".join(self.as_tuple())


@dataclass
class SkillExecutionResult:
    success: bool
    primitive_actions: List[str]
    consumed_steps: int
    message: str = ""


class OfficialHLPAdapter:
    """Wrap the official OSU LLM-Planner high-level prompt generator."""

    def __init__(
        self,
        llm_client: LLMClient,
        project_root: Path,
        logger: AgentLogger,
        knn_k: int = 9,
        embedding_model: str = "paraphrase-MiniLM-L6-v2",
        debug: bool = False,
    ):
        self.llm = llm_client
        self.logger = logger
        self.knn_k = knn_k
        self.embedding_model = embedding_model
        self.debug = debug

        configured_root = os.environ.get("LLM_PLANNER_ROOT", "").strip()
        if configured_root:
            self.official_root = Path(configured_root).expanduser().resolve()
        else:
            self.official_root = (
                project_root / "third_party" / "LLM-Planner"
            ).resolve()

        self.hlp_file = self.official_root / "hlp" / "hlp_planner.py"
        self.knn_file = self.official_root / "hlp" / "knn_set.pkl"
        self._generator = None

    def validate_setup(self) -> None:
        missing = [
            str(path)
            for path in (self.hlp_file, self.knn_file)
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Official LLM-Planner HLP files are missing:\n- "
                + "\n- ".join(missing)
                + "\nClone OSU-NLP-Group/LLM-Planner into "
                  "third_party/LLM-Planner or set LLM_PLANNER_ROOT."
            )

    def load(self) -> None:
        if self._generator is not None:
            return

        self.validate_setup()

        spec = importlib.util.spec_from_file_location(
            "osu_llm_planner_hlp",
            str(self.hlp_file),
        )
        if spec is None or spec.loader is None:
            raise ImportError(
                f"Cannot import official HLP file: {self.hlp_file}"
            )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self._generator = module.LLM_HLP_Generator(
            knn_data_path=str(self.knn_file),
            emb_model_name=self.embedding_model,
            debug=self.debug,
        )

    def generate(
        self,
        instruction: str,
        visible_objects: Sequence[str],
        completed_plans: Sequence[Tuple[str, ...]],
        prompt_seed: int,
    ) -> Tuple[List[HighLevelSkill], dict]:
        self.load()

        # Official generate_prompt randomly selects a split point in each
        # demonstration. Seeding keeps evaluation runs reproducible.
        random.seed(prompt_seed)

        task = {
            "task_instr": [instruction],
            "step_instr": [],
            "vis_objs": sorted(set(visible_objects)),
            "completed_plans": list(completed_plans),
        }

        prompt = self._generator.generate_prompt(
            task,
            k=self.knn_k,
            removeNav=False,
            naturalFormat=False,
            includeLow=False,
        )

        system_prompt = (
            "Complete the supplied official LLM-Planner prompt. "
            "Output only the remaining high-level plan as a comma-separated "
            "sequence. Use only these actions: OpenObject, CloseObject, "
            "PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, "
            "SliceObject, Navigation. Example output: "
            "Navigation fridge, OpenObject fridge, PickupObject milk. "
            "Do not output explanations, markdown, numbering, primitive "
            "VirtualHome actions, JSON, done, or FINISH."
        )

        raw_output = self.llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=prompt,
            response_format="text",
        )

        plan = parse_high_level_plan(raw_output)

        metadata = {
            "official_hlp_file": str(self.hlp_file),
            "official_knn_file": str(self.knn_file),
            "knn_k": self.knn_k,
            "embedding_model": self.embedding_model,
            "visible_objects": list(task["vis_objs"]),
            "completed_plans": [
                list(item) for item in completed_plans
            ],
            "prompt": prompt,
            "raw_output": raw_output,
            "parsed_plan": [
                list(skill.as_tuple()) for skill in plan
            ],
        }
        return plan, metadata


class VirtualHomeHLPExecutor:
    """Map official high-level actions to VirtualHome primitive actions.

    This class performs only grounding and low-level execution. It may walk
    to an interaction target, but it does not invent missing high-level
    subgoals such as opening a closed container before PutObject.
    """

    CLASS_ALIASES = {
        "refrigerator": "fridge",
        "television": "tv",
        "remote": "remotecontrol",
        "remotecontroller": "remotecontrol",
        "remote_control": "remotecontrol",
        "microwaveoven": "microwave",
        "counter": "countertop",
        "counter_top": "countertop",
        "couch": "sofa",
        "trashcan": "garbagecan",
        "garbage": "garbagecan",
    }

    OPENABLE_PROPERTIES = {"OPENABLE", "CAN_OPEN"}
    CONTAINER_PROPERTIES = {"CONTAINER", "CONTAINERS"}
    SURFACE_PROPERTIES = {"SURFACE", "SITTABLE"}

    def __init__(self, logger: AgentLogger):
        self.logger = logger

    def execute(
        self,
        graph: dict,
        skill: HighLevelSkill,
    ) -> SkillExecutionResult:
        action = skill.action

        if action == "Navigation":
            node = self.resolve_object(skill.obj, graph)
            if not node:
                return self._failure(
                    f"Navigation target not found: {skill.obj}"
                )
            if int(node["id"]) in get_held_ids(graph):
                return SkillExecutionResult(
                    success=True,
                    primitive_actions=[],
                    consumed_steps=0,
                    message="Target is already held.",
                )
            if is_character_close_to(graph, int(node["id"])):
                return SkillExecutionResult(
                    success=True,
                    primitive_actions=[],
                    consumed_steps=0,
                    message="Target is already close.",
                )
            return self._run_primitives(
                [format_unary("walk", node)],
            )

        unary_mapping = {
            "OpenObject": "open",
            "CloseObject": "close",
            "PickupObject": "grab",
            "ToggleObjectOn": "switchon",
            "ToggleObjectOff": "switchoff",
            "SliceObject": "cut",
        }

        if action in unary_mapping:
            node = self.resolve_object(
                skill.obj,
                graph,
                prefer_held=(action == "SliceObject"),
            )
            if not node:
                return self._failure(
                    f"{action} target not found: {skill.obj}"
                )

            primitives: List[str] = []
            if not is_character_close_to(graph, int(node["id"])):
                primitives.append(format_unary("walk", node))
            primitives.append(format_unary(unary_mapping[action], node))

            return self._run_primitives(
                primitives,
            )

        if action == "PutObject":
            source = self.resolve_object(
                skill.obj,
                graph,
                prefer_held=True,
            )
            target = self.resolve_object(skill.target, graph)

            if not source or not target:
                return self._failure(
                    "PutObject grounding failed: "
                    f"object={skill.obj}, target={skill.target}"
                )

            held_ids = get_held_ids(graph)
            if int(source["id"]) not in held_ids:
                return self._failure(
                    f"PutObject source is not held: "
                    f"{source['class_name']}({source['id']})"
                )

            target_props = upper_set(target.get("properties", []))
            target_states = effective_states(target)

            primitives = []
            if not is_character_close_to(graph, int(target["id"])):
                primitives.append(format_unary("walk", target))

            if target_props.intersection(self.CONTAINER_PROPERTIES):
                if (
                    target_props.intersection(self.OPENABLE_PROPERTIES)
                    and "OPEN" not in target_states
                ):
                    return self._failure(
                        f"PutObject target is closed: "
                        f"{target['class_name']}({target['id']})"
                    )
                primitives.append(
                    format_binary("putin", source, target)
                )
            elif target_props.intersection(self.SURFACE_PROPERTIES):
                primitives.append(
                    format_binary("putback", source, target)
                )
            elif target_props.intersection(self.OPENABLE_PROPERTIES):
                if "OPEN" not in target_states:
                    return self._failure(
                        f"PutObject target is closed: "
                        f"{target['class_name']}({target['id']})"
                    )
                primitives.append(
                    format_binary("putin", source, target)
                )
            else:
                return self._failure(
                    f"PutObject target is neither container nor surface: "
                    f"{target['class_name']}({target['id']})"
                )

            return self._run_primitives(
                primitives,
            )

        return self._failure(
            f"Unsupported high-level action: {action}"
        )

    def resolve_object(
        self,
        requested_name: Optional[str],
        graph: dict,
        prefer_held: bool = False,
    ) -> Optional[dict]:
        if not requested_name:
            return None

        requested = normalize_name(requested_name)
        requested = self.CLASS_ALIASES.get(requested, requested)

        nodes = [
            node
            for node in graph.get("nodes", [])
            if str(node.get("class_name", "")).lower()
            != "character"
            and str(node.get("category", "")) != "Rooms"
        ]

        exact = [
            node
            for node in nodes
            if normalize_name(node.get("class_name", ""))
            == requested
        ]

        if not exact:
            exact = [
                node
                for node in nodes
                if (
                    requested
                    in normalize_name(node.get("class_name", ""))
                    or normalize_name(node.get("class_name", ""))
                    in requested
                )
            ]

        if not exact:
            return None

        held_ids = get_held_ids(graph)
        close_ids = get_close_ids(graph)

        def rank(node: dict) -> Tuple[int, int, int]:
            node_id = int(node.get("id", -1))
            return (
                1 if prefer_held and node_id in held_ids else 0,
                1 if node_id in close_ids else 0,
                -node_id,
            )

        return max(exact, key=rank)

    def _run_primitives(
        self,
        primitives: Sequence[str],
    ) -> SkillExecutionResult:
        if not primitives:
            return SkillExecutionResult(
                success=True,
                primitive_actions=[],
                consumed_steps=0,
                message="No primitives to execute.",
            )

        return SkillExecutionResult(
            success=True,
            primitive_actions=list(primitives),
            consumed_steps=len(primitives),
            message="",
        )

    @staticmethod
    def _failure(message: str) -> SkillExecutionResult:
        return SkillExecutionResult(
            success=False,
            primitive_actions=[],
            consumed_steps=0,
            message=message,
        )
class LLMPlannerAgent(BaseAgent):
    VERSION = LLM_PLANNER_VERSION

    REQUIRED_OBSERVATION = ["partial"]

    def __init__(
        self,
        model_name: str = "gpt-5.4-mini",
        scenario_id: str = "",
    ):
        self.llm = LLMClient(model_name=model_name)
        self.scenario_id = scenario_id
        self.logger = None

        # agent/llm_planner_agent.py -> project root
        self.project_root = Path(__file__).resolve().parents[1]

        self.action_history: List[dict] = []
        self.completed_plans: List[Tuple[str, ...]] = []
        self.visible_objects: Set[str] = set()
        self.current_plan: List[HighLevelSkill] = []
        self.primitive_queue: List[str] = []
        
        self.hlp = None
        self.executor = None
        self.replan_count = 0
        self.replan_reason = "initial planning"

    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        goal = str(config.get("goal_instruction", "")).strip()
        if not goal:
            return "done()"

        env_info = env_info or {}
        step = env_info.get("step", 0)
        self.logger = env_info.get("logger") or self.logger
        self.action_history = env_info.get("action_history", [])

        if step == 0:
            self.logger.info(f"[{self.VERSION}] Starting LLM-Planner-VH episode for goal: {goal}")
            self.completed_plans = []
            self.visible_objects = set()
            self.current_plan = []
            self.primitive_queue = []
            self.replan_count = 0
            self.replan_reason = "initial planning"
            
            knn_k = int(config.get("llm_planner_knn_k", 9))
            embedding_model = str(config.get("llm_planner_embedding_model", "paraphrase-MiniLM-L6-v2"))
            
            self.hlp = OfficialHLPAdapter(
                llm_client=self.llm,
                project_root=self.project_root,
                logger=self.logger,
                knn_k=knn_k,
                embedding_model=embedding_model,
                debug=bool(config.get("llm_planner_debug_prompt", False)),
            )
            self.executor = VirtualHomeHLPExecutor(self.logger)
            
            self._log_module(
                "LLMPlannerVersion",
                {
                    "version": self.VERSION,
                    "planner_core": "official OSU HLP prompt generator and kNN",
                    "controller": "VirtualHome grounding and primitive executor",
                    "knn_k": knn_k,
                    "embedding_model": embedding_model,
                },
            )
            try:
                self.hlp.validate_setup()
            except Exception as exc:
                self.logger.error(str(exc))
                return "done()"

        self._update_visible_objects(obs)
        full_graph = deduplicate_graph(obs)

        # If previous action failed, clear primitive queue and current plan
        if step > 0 and self.action_history and not self.action_history[-1].get("success", True):
            self.primitive_queue = []
            self.current_plan = []
            self.replan_reason = f"previous action failed: {self.action_history[-1].get('action', '')}"

        if self.primitive_queue:
            return self.primitive_queue.pop(0)

        max_replans = int(config.get("llm_planner_max_replans", 15))
        prompt_seed = int(config.get("llm_planner_prompt_seed", 0))

        while not self.current_plan:
            if self.replan_count >= max_replans:
                self.logger.error("❌ FAILED: maximum replanning attempts reached.")
                return "done()"

            try:
                plan, metadata = self.hlp.generate(
                    instruction=goal,
                    visible_objects=sorted(self.visible_objects),
                    completed_plans=self.completed_plans,
                    prompt_seed=(prompt_seed + self.replan_count),
                )
            except Exception as exc:
                self.logger.error(f"Official HLP generation failed: {exc}")
                return "done()"

            self.replan_count += 1
            metadata["replan_count"] = self.replan_count
            metadata["reason"] = self.replan_reason
            self._log_module("LLMPlannerHLP", metadata)

            if not plan:
                self.logger.error("LLM returned no parseable high-level plan.")
                return "done()"

            self.current_plan = list(plan)
            self.logger.info(
                f"[{self.VERSION}] Generated HLP #{self.replan_count}: {[str(skill) for skill in self.current_plan]}"
            )

        skill = self.current_plan.pop(0)
        self.logger.info(f"[{self.VERSION}] Executing HLP: {skill}")

        result = self.executor.execute(
            graph=full_graph,
            skill=skill,
        )

        if result.consumed_steps == 0:
            if result.success:
                self.completed_plans.append(skill.as_tuple())
                self.logger.info(f"HLP already satisfied: {skill}")
                return "wait()"
            
            self.logger.info(f"HLP failed before execution: {skill}. {result.message}. Replanning.")
            self.current_plan = []
            self.replan_reason = f"high-level skill failed: {skill}; reason: {result.message}"
            return "wait()"

        if result.success:
            self.completed_plans.append(skill.as_tuple())
            self.replan_reason = "continue after completed high-level skills"
        else:
            self.logger.info(f"HLP execution failed: {skill}. {result.message}. Replanning.")
            self.current_plan = []
            self.replan_reason = f"high-level skill failed: {skill}; environment feedback: {result.message}"

        self.primitive_queue = result.primitive_actions
        
        if self.primitive_queue:
            return self.primitive_queue.pop(0)
            
        return "wait()"

    def _update_visible_objects(self, obs: dict) -> None:
        for node in obs.get("nodes", []):
            if str(node.get("category", "")) == "Rooms":
                continue

            class_name = str(
                node.get("class_name", "")
            ).strip().lower()

            if class_name and class_name != "character":
                self.visible_objects.add(class_name)


    def _log_module(
        self,
        module_name: str,
        payload: dict,
    ) -> None:
        try:
            self.logger.log_module_output(
                module_name,
                0,
                payload,
            )
        except Exception:
            pass

    def _write_step(
        self,
        step: int,
        action: str,
        graph: dict,
    ) -> None:
        items = observed_items(graph)

        try:
            self.logger.write_step(
                step,
                action,
                None,
                items,
            )
            return
        except Exception:
            pass

        log_file = getattr(
            self.logger,
            "log_file",
            None,
        )
        if not log_file:
            return

        try:
            with open(
                log_file,
                "a",
                encoding="utf-8",
            ) as file:
                file.write(f"\n## Step {step}\n")
                file.write(
                    f"- **Action**: `{action}`\n"
                )
                file.write(
                    f"- **Observed Items ({len(items)})**: "
                    f"{', '.join(items[:20])}\n"
                )
        except Exception:
            pass


OFFICIAL_ACTIONS = (
    "ToggleObjectOff",
    "ToggleObjectOn",
    "PickupObject",
    "CloseObject",
    "OpenObject",
    "SliceObject",
    "PutObject",
    "Navigation",
)


def parse_high_level_plan(
    text: str,
) -> List[HighLevelSkill]:
    if not text:
        return []

    cleaned = str(text).strip()
    cleaned = re.sub(
        r"```(?:json|text)?",
        "",
        cleaned,
    )
    cleaned = cleaned.replace("```", "")

    # Tuple-form output, e.g. ('Navigation', 'Fridge').
    tuple_matches = re.findall(
        r"\([^()]+\)",
        cleaned,
    )
    tuple_skills: List[HighLevelSkill] = []

    for match in tuple_matches:
        try:
            value = ast.literal_eval(match)
        except Exception:
            continue

        if isinstance(value, tuple):
            skill = skill_from_sequence(value)
            if skill:
                tuple_skills.append(skill)

    if tuple_skills:
        return deduplicate_consecutive_skills(
            tuple_skills
        )

    # JSON is accepted as a robustness fallback.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            raw_plan = parsed.get("plan", [])
            skills: List[HighLevelSkill] = []

            if isinstance(raw_plan, list):
                for item in raw_plan:
                    if isinstance(item, dict):
                        action = canonical_action(
                            item.get("action", "")
                        )
                        if not action:
                            continue

                        skills.append(
                            HighLevelSkill(
                                action=action,
                                obj=clean_object_name(
                                    item.get("object")
                                    or item.get("obj")
                                ),
                                target=clean_object_name(
                                    item.get("target")
                                    or item.get("location")
                                ),
                            )
                        )
                    elif isinstance(
                        item,
                        (list, tuple),
                    ):
                        skill = skill_from_sequence(
                            item
                        )
                        if skill:
                            skills.append(skill)
                    elif isinstance(item, str):
                        skills.extend(
                            parse_high_level_plan(item)
                        )

            if skills:
                return deduplicate_consecutive_skills(
                    skills
                )
    except Exception:
        pass

    action_pattern = re.compile(
        r"(?i)\b("
        + "|".join(OFFICIAL_ACTIONS)
        + r")\b"
    )
    matches = list(
        action_pattern.finditer(cleaned)
    )

    skills = []

    for index, match in enumerate(matches):
        action = canonical_action(
            match.group(1)
        )
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(cleaned)
        )

        argument_text = cleaned[start:end]
        argument_text = re.sub(
            r"^[\s,:;\-\.\d\)\(]+",
            "",
            argument_text,
        )
        argument_text = re.split(
            r"[\n,;.]",
            argument_text,
            maxsplit=1,
        )[0]

        words = [
            clean_object_name(token)
            for token in re.findall(
                r"[A-Za-z0-9_]+",
                argument_text,
            )
        ]
        words = [word for word in words if word]

        if action == "PutObject":
            if len(words) >= 2:
                skills.append(
                    HighLevelSkill(
                        action,
                        words[0],
                        words[1],
                    )
                )
        elif words:
            skills.append(
                HighLevelSkill(
                    action,
                    words[0],
                )
            )

    return deduplicate_consecutive_skills(
        skills
    )


def skill_from_sequence(
    value: Sequence,
) -> Optional[HighLevelSkill]:
    if not value:
        return None

    action = canonical_action(value[0])
    if not action:
        return None

    obj = (
        clean_object_name(value[1])
        if len(value) > 1
        else None
    )
    target = (
        clean_object_name(value[2])
        if len(value) > 2
        else None
    )

    return HighLevelSkill(
        action,
        obj,
        target,
    )


def canonical_action(value: object) -> str:
    normalized = re.sub(
        r"[^a-z]",
        "",
        str(value).lower(),
    )

    for action in OFFICIAL_ACTIONS:
        candidate = re.sub(
            r"[^a-z]",
            "",
            action.lower(),
        )
        if candidate == normalized:
            return action

    return ""


def clean_object_name(
    value: object,
) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    text = text.strip(
        "[](){}'\"`.,:;"
    )
    text = re.sub(
        r"^(the|a|an)\s+",
        "",
        text,
        flags=re.I,
    )
    return text.lower() or None


def deduplicate_consecutive_skills(
    skills: Sequence[HighLevelSkill],
) -> List[HighLevelSkill]:
    output: List[HighLevelSkill] = []

    for skill in skills:
        if not output or skill != output[-1]:
            output.append(skill)

    return output


def normalize_name(value: object) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower(),
    )


def format_unary(
    action: str,
    node: dict,
) -> str:
    return (
        f"[{action}] "
        f"<{node.get('class_name', 'object')}> "
        f"({node.get('id')})"
    )


def format_binary(
    action: str,
    first: dict,
    second: dict,
) -> str:
    return (
        f"[{action}] "
        f"<{first.get('class_name', 'object')}> "
        f"({first.get('id')}) "
        f"<{second.get('class_name', 'object')}> "
        f"({second.get('id')})"
    )


def deduplicate_graph(graph: dict) -> dict:
    node_map: Dict[int, dict] = {}

    for raw_node in graph.get("nodes", []):
        if "id" not in raw_node:
            continue

        node_id = int(raw_node["id"])
        node = dict(raw_node)

        if node_id not in node_map:
            node_map[node_id] = node
            continue

        existing = node_map[node_id]
        existing["states"] = sorted(
            upper_set(
                existing.get("states", [])
            ).union(
                upper_set(
                    node.get("states", [])
                )
            )
        )
        existing["properties"] = sorted(
            upper_set(
                existing.get("properties", [])
            ).union(
                upper_set(
                    node.get("properties", [])
                )
            )
        )

    edge_map: Dict[
        Tuple[int, str, int],
        dict,
    ] = {}

    for raw_edge in graph.get("edges", []):
        relation = str(
            raw_edge.get(
                "relation_type",
                raw_edge.get("relation", ""),
            )
        ).upper()

        key = (
            int(raw_edge.get("from_id", -1)),
            relation,
            int(raw_edge.get("to_id", -1)),
        )

        if key not in edge_map:
            edge = dict(raw_edge)
            edge["relation_type"] = relation
            edge_map[key] = edge

    return {
        "nodes": list(node_map.values()),
        "edges": list(edge_map.values()),
    }


def get_character_id(graph: dict) -> int:
    for node in graph.get("nodes", []):
        if (
            int(node.get("id", -1)) == 1
            or str(
                node.get("class_name", "")
            ).lower()
            == "character"
        ):
            return int(node.get("id", 1))

    return 1


def get_held_ids(graph: dict) -> Set[int]:
    character_id = get_character_id(graph)

    return {
        int(edge.get("to_id", -1))
        for edge in graph.get("edges", [])
        if int(edge.get("from_id", -1))
        == character_id
        and str(
            edge.get("relation_type", "")
        ).upper().startswith("HOLDS")
    }


def get_close_ids(graph: dict) -> Set[int]:
    character_id = get_character_id(graph)

    return {
        int(edge.get("to_id", -1))
        for edge in graph.get("edges", [])
        if int(edge.get("from_id", -1))
        == character_id
        and str(
            edge.get("relation_type", "")
        ).upper()
        == "CLOSE"
    }


def is_character_close_to(
    graph: dict,
    object_id: int,
) -> bool:
    return object_id in get_close_ids(graph)


def upper_set(
    values: Iterable[object],
) -> Set[str]:
    return {
        str(value).upper()
        for value in values
    }


def effective_states(node: dict) -> Set[str]:
    states = upper_set(
        node.get("states", [])
    )

    if "ON" in states:
        states.discard("OFF")
    if "OPEN" in states:
        states.discard("CLOSED")
    if "HOT" in states:
        states.discard("COLD")
    if "CLEAN" in states:
        states.discard("DIRTY")
    if "PLUGGED_IN" in states:
        states.discard("PLUGGED_OUT")

    return states


def coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return all(
            bool(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return all(
            bool(item)
            for item in value
        )
    return bool(value)


def observed_items(graph: dict) -> List[str]:
    items = []

    for node in graph.get("nodes", []):
        states = node.get("states", [])
        state_text = (
            f" [{','.join(str(item) for item in states)}]"
            if states
            else ""
        )

        items.append(
            f"{node.get('class_name', 'object')}"
            f"({node.get('id', -1)})"
            f"{state_text}"
        )

    return items

