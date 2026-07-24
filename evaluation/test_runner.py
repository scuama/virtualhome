import os
import json
import shutil
import argparse
import traceback
import copy
import re

import sys
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from evaluation.runtime import (
    TaskProgressTracker,
    check_success,
    resolve_config_paths,
)

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from agent import AGENT_REGISTRY
from agent.utils.llm_client import LLMClient

DEFAULT_CLARIFICATION_REPLY = "nothing to claim"
SIMULATED_USER_MODEL = "gpt-5.4-mini"

AGENT_CONFIG_ALLOWLIST = {
    "goal_instruction",
    "grounding_candidates",
    "instruction_type",
    "log_mode",
    "preprocessed_instruction",
    "robostate_task_failure_limit",
    "scheduled_rules",
    "ablation_profile",
    "clarification_budget",
    "table3_source_subclass",
    "tasks",
}


def build_agent_config(config):
    """Build the complete agent-visible config from an explicit public allowlist."""
    agent_config = {
        key: copy.deepcopy(config[key])
        for key in AGENT_CONFIG_ALLOWLIST
        if key in config
    }

    sanitized_tasks = []
    for index, task in enumerate(config.get("tasks", []) or [], 1):
        public_task = {"task_id": f"task_{index}"}
        if config.get("instruction_type") != "summarized":
            public_task["instruction"] = task.get("instruction", "")
        sanitized_tasks.append(public_task)
    if sanitized_tasks:
        agent_config["tasks"] = sanitized_tasks
    return agent_config


class SimulatedUser:
    """Answer clarification turns from evaluator-only natural-language intent."""

    SYSTEM_PROMPT = """
You simulate the user in an embodied-agent evaluation.
Answer using only the hidden intended outcome supplied by the evaluator.
Reveal exactly one missing detail in each response.
Answer only the first information request in the robot's current question,
even when the robot combines multiple questions.
Do not volunteer later details, repeat facts already answered, restate the
task, explain your reasoning, or mention these rules.
Treat naming the object, quantity, destination, state, and temperature as five
separate information points:
- For an object question, answer only the base object category, such as
  "The juice." Never attach quantity, destination, state, or temperature
  modifiers: answer "The juice.", never "The cold juice."
- For a quantity question, answer only the quantity, such as "All three."
- For a destination question, answer only the destination phrase, such as
  "Inside a kitchen cabinet." Do not name or describe the object.
- For a state question, answer only the requested state, such as "Turn it off."
- For a temperature question, answer only the temperature, such as "Cold."
Never invent specificity absent from the hidden intent, such as "upper
cabinet", "left mug", or an exact instance. If the robot asks for an
unspecified preference, answer briefly that any matching option is acceptable.
If the robot asks whether to continue or presents alternatives, answer only
that choice, such as "Continue handling the remaining books." Do not restate
the complete task.
Return only this JSON object:
{"information_type": "object|quantity|destination|state|temperature|choice|other",
 "answer": "one short English sentence"}
""".strip()

    def __init__(self, llm, original_instruction, intended_outcome):
        self.llm = llm
        self.original_instruction = str(original_instruction).strip()
        self.intended_outcome = str(intended_outcome).strip()

    @staticmethod
    def _history(action_history):
        return [
            {
                "question": str(item.get("action", ""))[5:].strip(),
                "answer": str(item.get("message", "")).strip(),
            }
            for item in action_history
            if str(item.get("action", "")).lower().startswith("[ask]")
            and bool(item.get("success", False))
            and str(item.get("message", "")).strip()
        ]

    def answer(self, question, action_history):
        history = self._history(action_history)
        prompt = (
            f"Original instruction:\n{self.original_instruction}\n\n"
            f"Hidden intended outcome:\n{self.intended_outcome}\n\n"
            "Previous clarification turns:\n"
            f"{json.dumps(history, ensure_ascii=False)}\n\n"
            f"Current robot question:\n{str(question).strip()}"
        )
        raw = str(self.llm.generate_response(
            self.SYSTEM_PROMPT,
            prompt,
            response_format="json_object",
            module_name="simulated_user",
            temperature=0.0,
        )).strip()
        try:
            parsed = json.loads(raw)
            answer = str(parsed.get("answer", "")).strip()
        except (json.JSONDecodeError, AttributeError):
            answer = raw
        normalized = re.sub(r"[^a-z0-9]+", " ", answer.lower()).strip()
        previous = {
            re.sub(r"[^a-z0-9]+", " ", item["answer"].lower()).strip()
            for item in history
        }
        if normalized and normalized in previous:
            return "I have no additional preference."
        return answer


def clarification_trace(action_history):
    """Return successful clarification question/answer turns."""
    return [
        {
            "step": int(item.get("step", 0)),
            "question": str(item.get("action", ""))[5:].strip(),
            "answer": str(item.get("message", "")).strip(),
        }
        for item in action_history
        if str(item.get("action", "")).lower().startswith("[ask]")
        and bool(item.get("success", False))
        and str(item.get("message", "")).strip()
    ]


def set_environment_state(env, object_id, add_states=None, remove_states=None):
    """Apply a persistent state overlay through the environment public hook."""
    additions = {str(state).upper() for state in (add_states or [])}
    removals = {str(state).upper() for state in (remove_states or [])}
    if hasattr(env, "set_state_override"):
        env.set_state_override(object_id, additions, removals)
        return

    # Small fake environments used by tests may not implement the Unity hook.
    if not hasattr(env, "custom_states"):
        env.custom_states = {}
    if not hasattr(env, "custom_removed_states"):
        env.custom_removed_states = {}
    stored_additions = env.custom_states.setdefault(int(object_id), set())
    stored_removals = env.custom_removed_states.setdefault(int(object_id), set())
    stored_additions.difference_update(removals)
    stored_additions.update(additions)
    stored_removals.difference_update(additions)
    stored_removals.update(removals)
    env.changed_graph = True


class DynamicEventRuntime:
    """Runner-owned deterministic action- and step-triggered event scheduler."""

    ACTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]")
    OBJECT_PATTERN = re.compile(r"<([^>]+)>\s*\(\s*(\d+)\s*\)")

    def __init__(self, env, configured_events, logger):
        self.env = env
        self.events = copy.deepcopy(configured_events or [])
        self.logger = logger
        self.hidden_until = {}
        self.trace = []
        for index, event in enumerate(self.events):
            event["_runtime_id"] = event.get("event_id", f"event_{index + 1}")
            event["_times_triggered"] = 0
            event["_last_trigger_step"] = None

    @staticmethod
    def _trigger_limit(event):
        value = event.get("max_triggers")
        return int(value) if value is not None else None

    def before_step(self, step):
        """Apply interval state changes before success checking and observation."""
        environment_changed = False
        for event in self.events:
            trigger = event.get("trigger", {})
            effect = event.get("effect", {})
            if str(trigger.get("type", "")).lower() != "step_interval":
                continue
            interval = int(trigger.get("interval_steps", 0))
            start = int(trigger.get("start_step", interval))
            if interval <= 0 or step < start or (step - start) % interval:
                continue
            if event["_last_trigger_step"] == int(step):
                continue
            limit = self._trigger_limit(event)
            if limit is not None and event["_times_triggered"] >= limit:
                continue
            if effect.get("type") != "set_state":
                continue

            target_class = str(effect.get("target", "")).lower()
            graph = self.env.get_graph()
            candidates = [
                node for node in graph.get("nodes", [])
                if str(node.get("class_name", "")).lower() == target_class
            ]
            required_states = {
                str(state).upper() for state in effect.get("match_states", [])
            }
            matching = [
                node for node in candidates
                if required_states.issubset({
                    str(state).upper() for state in node.get("states", [])
                })
            ]
            if not matching:
                # No completed target currently exists, so this interval did
                # not produce an environmental change and is not consumed.
                continue
            if effect.get("apply_to", "all_matching") != "all_matching":
                raise RuntimeError(
                    f"Dynamic event {event['_runtime_id']} has unsupported "
                    f"apply_to={effect.get('apply_to')!r}"
                )
            target_ids = [int(node["id"]) for node in matching]
            for target_id in target_ids:
                set_environment_state(
                    self.env,
                    target_id,
                    effect.get("add_states", []),
                    effect.get("remove_states", []),
                )
            event["_times_triggered"] += 1
            event["_last_trigger_step"] = int(step)
            self.trace.append({
                "step": int(step),
                "event": "set_state",
                "event_id": event["_runtime_id"],
                "object_ids": target_ids,
                "target": target_class,
                "add_states": list(effect.get("add_states", [])),
                "remove_states": list(effect.get("remove_states", [])),
            })
            self.logger.info(
                f"⚡ DYNAMIC EVENT: {target_class}{target_ids} state changed "
                f"at step {step}."
            )
            environment_changed = True
        return environment_changed

    @classmethod
    def parse_action(cls, action_str):
        action_match = cls.ACTION_PATTERN.search(action_str or "")
        action = action_match.group(1).strip().lower() if action_match else ""
        objects = [
            {"class_name": class_name.strip().lower(), "id": int(object_id)}
            for class_name, object_id in cls.OBJECT_PATTERN.findall(action_str or "")
        ]
        return action, objects

    def expire(self, step):
        expired = [
            object_id
            for object_id, visible_at_step in self.hidden_until.items()
            if step >= visible_at_step
        ]
        for object_id in expired:
            visible_at_step = self.hidden_until.pop(object_id)
            if self.env.active_hidden_nodes.get(object_id) == visible_at_step:
                del self.env.active_hidden_nodes[object_id]
                self.env.changed_graph = True
            self.trace.append(
                {
                    "step": int(step),
                    "event": "reappear",
                    "object_id": object_id,
                }
            )
            self.logger.info(
                f"⚡ DYNAMIC EVENT: object {object_id} reappeared at step {step}."
            )

    def before_action(self, step, action_str, graph):
        action, action_objects = self.parse_action(action_str)
        intercepted = False
        message = None

        for event in self.events:
            trigger = event.get("trigger", {})
            effect = event.get("effect", {})
            max_triggers = int(event.get("max_triggers", 1))
            if event["_times_triggered"] >= max_triggers:
                continue
            if str(trigger.get("type", "action")).lower() != "action":
                continue
            if action != str(trigger.get("action", "")).lower():
                continue

            target_class = str(
                trigger.get("target", effect.get("target", ""))
            ).lower()
            target_arg = next(
                (
                    item
                    for item in action_objects
                    if item["class_name"] == target_class
                ),
                None,
            )
            if not target_arg:
                continue

            target_id = target_arg["id"]
            if target_id in self.hidden_until:
                continue

            # Relaxed behavior: The disturbance affects whichever valid target
            # the agent tries to interact with. This aligns with the relaxed
            # success conditions in check_success().
            pass

            required_state = trigger.get("target_state")
            if required_state:
                target_node = next(
                    (
                        node
                        for node in graph.get("nodes", [])
                        if int(node.get("id", -1)) == target_id
                    ),
                    None,
                )
                states = {
                    str(state).upper()
                    for state in (target_node or {}).get("states", [])
                }
                if str(required_state).upper() not in states:
                    continue

            if effect.get("type") != "hide":
                continue

            duration = int(effect.get("duration_steps", 2))
            # The triggering action is step t. The object is hidden for the
            # complete decisions t+1..t+duration and restored before t+duration+1.
            visible_at_step = int(step) + duration + 1
            self.env.active_hidden_nodes[target_id] = visible_at_step
            self.hidden_until[target_id] = visible_at_step
            self.env.changed_graph = True
            event["_times_triggered"] += 1
            intercepted = True
            message = "temporary_unavailable: target disappeared; wait or search and retry"
            self.trace.append(
                {
                    "step": int(step),
                    "event": "hide",
                    "event_id": event["_runtime_id"],
                    "object_id": target_id,
                    "duration_steps": duration,
                    "trigger_index": event["_times_triggered"],
                    "max_triggers": max_triggers,
                    "visible_at_step": visible_at_step,
                }
            )
            self.logger.info(
                "⚡ DYNAMIC EVENT: "
                f"{target_class}({target_id}) hidden for {duration} full steps "
                f"({event['_times_triggered']}/{max_triggers}); "
                f"returns before step {visible_at_step}."
            )
            break

        if not intercepted:
            hidden_target = next(
                (
                    item
                    for item in action_objects
                    if item["id"] in self.env.active_hidden_nodes
                ),
                None,
            )
            if hidden_target:
                intercepted = True
                message = "temporary_unavailable: target is temporarily hidden"

        info = (
            {
                "action_success": False,
                "action_message": message,
                "error_type": "temporary_unavailable",
                "temporary": True,
            }
            if intercepted
            else {}
        )
        return intercepted, info

    def event_counts(self):
        return {
            event["_runtime_id"]: {
                "times_triggered": event["_times_triggered"],
                "max_triggers": self._trigger_limit(event),
            }
            for event in self.events
        }


def reset_environment_runtime(env):
    """Remove scenario-specific monkey patches and transient event state."""
    if hasattr(env, "_test_runner_base_get_graph"):
        env.get_graph = env._test_runner_base_get_graph
    else:
        env._test_runner_base_get_graph = env.get_graph

    env.active_hidden_nodes = {}
    env.active_teleports = {}
    env.dynamic_events = []
    env.scheduled_rules = []
    env.current_step = 0


def table1_result_folder(base_dir, config, method_name):
    """Return the non-overlapping Table 1 result location."""
    axis = str(config.get('experiment_axis', 'unknown'))
    if axis == 'dynamic_difficulty':
        axis = 'dynamic'
    return os.path.join(
        base_dir, 'results', 'table1', method_name, axis,
        str(config.get('setting', 'unknown')),
        str(config.get('sample_id', 'unknown'))
    )

def table2_result_folder(base_dir, config, method_name):
    """Return the non-overlapping Table 2 result location."""
    axis = str(config.get('experiment_axis', 'unknown'))
    if axis == 'dynamic_difficulty':
        axis = 'non_stationarity'
        
    setting = str(config.get('setting', 'unknown'))
    if setting == 'unknown':
        if axis == 'non_stationarity':
            setting = str(config.get('dynamic_difficulty', 'unknown'))
        elif axis == 'scale':
            scale_val = config.get('instruction_scale', 'unknown')
            setting = f"S{scale_val}" if scale_val != 'unknown' else 'unknown'
        elif axis == 'instruction_type':
            setting = str(config.get('instruction_type', 'unknown'))
            
    return os.path.join(
        base_dir, 'results', 'table2', method_name, axis,
        setting,
        str(config.get('task_id', config.get('scenario_id', 'unknown')))
    )

def table3_result_folder(base_dir, config, method_name):
    """Return the non-overlapping Table 3 ablation result location."""
    return os.path.join(
        base_dir, 'results', 'table3', method_name, 'runs',
        str(config.get('ablation_profile', 'unknown')),
        str(config.get('source_scenario_id', config.get('scenario_id', 'unknown')))
    )


def table4_result_folder(base_dir, config, method_name):
    """Return the non-overlapping Table 4 model/scenario result location."""
    return os.path.join(
        base_dir, 'results', 'table4',
        str(config.get('model_alias', 'unknown')),
        str(config.get('source_scenario_id', config.get('scenario_id', 'unknown'))),
    )


def table5_result_folder(base_dir, config, method_name):
    """Return the Table 5 scenario/budget result location."""
    return os.path.join(
        base_dir, 'results', 'table5', method_name,
        str(config.get('source_scenario_id', config.get('sample_id', 'unknown'))),
        f"B{int(config.get('clarification_budget', 0))}",
    )


def source_tasks_result_folder(base_dir, config, method_name, config_path):
    """Return the result location for standard source tasks."""
    # config_path typically looks like: .../configs/source_tasks/<subclass>/E1_07.json
    path_parts = str(config_path).split(os.sep)
    subclass = 'unknown'
    if 'source_tasks' in path_parts:
        st_index = path_parts.index('source_tasks')
        if st_index + 1 < len(path_parts):
            subclass = path_parts[st_index + 1]
    
    return os.path.join(
        base_dir, 'results', 'source_tasks', method_name, subclass,
        str(config.get('scenario_id', 'unknown'))
    )


def write_result_artifacts(
    dest_folder,
    config,
    metrics,
    method_name,
    model_name,
    scenario_log_file=None,
    llm_calls_file=None,
):
    os.makedirs(dest_folder, exist_ok=True)
    recorded_config = copy.deepcopy(config)
    recorded_config['evaluation_method'] = method_name
    recorded_config['evaluation_model'] = model_name
    recorded_config['execution_time_seconds'] = metrics.get(
        'execution_time_seconds', 0
    )
    with open(os.path.join(dest_folder, 'config.json'), 'w', encoding='utf-8') as cf:
        json.dump(recorded_config, cf, indent=4, ensure_ascii=False)
    with open(os.path.join(dest_folder, 'metrics.json'), 'w', encoding='utf-8') as mf:
        json.dump(metrics, mf, indent=4, ensure_ascii=False)
    if scenario_log_file and os.path.exists(scenario_log_file):
        shutil.copy(
            scenario_log_file,
            os.path.join(dest_folder, f"run_{config['scenario_id']}.md"),
        )
    if llm_calls_file and os.path.exists(llm_calls_file):
        shutil.copy(llm_calls_file, os.path.join(dest_folder, 'llm_calls.jsonl'))


def apply_overrides(env, config, debug=False):
    """
    Apply persistent state overlays and physical relation initialization.
    """
    from agent.utils.graph_utils import find_node, find_all

    def _already_has_relation(graph, s_node, rel, obj_node):
        return any(e for e in graph['edges'] if e['from_id'] == s_node['id'] and e['relation_type'] == rel and e['to_id'] == obj_node['id'])

    def execute(action_str):
        obs, reward, done, info = env.step({0: action_str})
        success = info.get('action_success', False)
        return success, info.get('action_message', '')

    def destination_candidates(graph, class_name, in_room=None):
        candidates = sorted(
            find_all(graph, class_name),
            key=lambda node: int(node.get('id', -1)),
        )
        if not in_room:
            return candidates
        room_ids = {
            node['id']
            for node in graph['nodes']
            if node['class_name'].lower() == in_room.lower()
        }
        inside_ids = {
            edge['from_id']
            for edge in graph['edges']
            if edge['relation_type'] == 'INSIDE'
            and edge['to_id'] in room_ids
        }
        return [node for node in candidates if node['id'] in inside_ids]

    def conflicting_relation_subject_ids(graph, subject_class):
        """Find visible subjects that already satisfy a configured task goal."""
        ids = set()

        def visit(condition):
            if str(condition.get('mode', 'SINGLE')).upper() in {'AND', 'OR'}:
                for child in condition.get('conditions', []):
                    visit(child)
                return
            if str(condition.get('target_class', '')).lower() != subject_class:
                return
            relations = {
                value.strip().upper()
                for value in str(condition.get('relation') or '').split('|')
                if value.strip()
            }
            destination = str(condition.get('destination_class', '')).lower()
            if not relations or not destination:
                return
            destination_ids = {
                node['id'] for node in graph.get('nodes', [])
                if str(node.get('class_name', '')).lower() == destination
            }
            ids.update(
                edge['from_id'] for edge in graph.get('edges', [])
                if str(edge.get('relation_type', '')).upper() in relations
                and edge.get('to_id') in destination_ids
            )

        for task in config.get('tasks', []):
            visit(task.get('success_condition', {}))
        return ids

    # 1. 状态覆盖
    state_overrides = config.get('initial_states_override', [])
    graph = env.get_graph()
    for override in state_overrides:
        target_ids = []
        for class_name in override.get('target_classes', []):
            candidates = sorted(
                [
                    node for node in graph.get('nodes', [])
                    if str(node.get('class_name', '')).lower()
                    == str(class_name).lower()
                ],
                key=lambda node: int(node.get('id', -1)),
            )
            in_room = override.get('in_room')
            if in_room:
                room_ids = {
                    node['id'] for node in graph.get('nodes', [])
                    if str(node.get('class_name', '')).lower()
                    == str(in_room).lower()
                }
                inside_ids = {
                    edge['from_id'] for edge in graph.get('edges', [])
                    if edge.get('relation_type') == 'INSIDE'
                    and edge.get('to_id') in room_ids
                }
                candidates = [
                    node for node in candidates if node['id'] in inside_ids
                ]
            instance_filter = override.get('instance_filter')
            if instance_filter and 'index' in instance_filter:
                index = int(instance_filter['index'])
                candidates = candidates[index:index + 1]
            target_ids.extend(node['id'] for node in candidates)
        for target_id in target_ids:
            set_environment_state(
                env,
                target_id,
                override.get('add_states', []),
                override.get('remove_states', []),
            )

    # 2. 关系覆盖 (位置)
    graph = env.get_graph()
    relation_overrides = config.get('initial_relations_override', [])
    # Initialization actions move the real character. Always restore the
    # configured character spawn after all object placements are complete.
    ordered_relations = [
        ro for ro in relation_overrides
        if str(ro.get('subject', '')).lower() != 'character'
    ] + [
        ro for ro in relation_overrides
        if str(ro.get('subject', '')).lower() == 'character'
    ]
    for ro in ordered_relations:
        subj   = ro['subject'].lower()
        count  = ro.get('count', 1)
        
        subj_nodes = sorted(
            find_all(graph, subj),
            key=lambda node: int(node.get('id', -1)),
        )
        subject_instance = ro.get('subject_instance')
        conflicting_ids = conflicting_relation_subject_ids(graph, subj)

        # Explicitly bound benchmark tasks keep every non-target scene instance.
        if subject_instance is not None:
            start = int(subject_instance)
            subj_nodes = subj_nodes[start:start + count]
        else:
            conflicting = [
                node for node in subj_nodes if node['id'] in conflicting_ids
            ]
            remaining = [
                node for node in subj_nodes if node['id'] not in conflicting_ids
            ]
            # Move every already-satisfying subject out of the goal relation;
            # otherwise move only the configured count. No instance is hidden.
            subj_nodes = conflicting + remaining[
                :max(0, int(count) - len(conflicting))
            ]
            count = len(subj_nodes)

        # 验证必需物品是否充足
        if len(subj_nodes) < count:
            raise RuntimeError(f"Scene initialization failed: Requested {count} '{subj}', but only {len(subj_nodes)} exist in the scene. Please change to a different room/scene that contains enough '{subj}'.")
        
        # 如果没有指定 object，只调整数量不移动位置
        if 'object' not in ro:
            continue
            
        rel    = ro.get('relation', 'ON').upper()
        obj    = ro['object'].lower()
        in_room = ro.get('in_room')

        # 角色初始位置特殊处理
        if subj == 'character':
            obj_node = find_node(graph, obj)
            if obj_node:
                execute(f'[walk] <{obj}> ({obj_node["id"]})')
            graph = env.get_graph()
            continue

        obj_nodes = destination_candidates(graph, obj, in_room)
        object_instance = ro.get('object_instance')
        if object_instance is not None:
            index = int(object_instance)
            obj_nodes = obj_nodes[index:index + 1]
        if not obj_nodes:
            raise RuntimeError(
                f"Scene initialization failed: No destination '{obj}' "
                f"matched in_room={in_room!r}."
            )

        # Use real Unity actions so the configured graph and Unity physics stay
        # aligned. Some scenes contain multiple surfaces of the same class and
        # only a subset accept a given object, so try each matching instance.
        for s_node in subj_nodes[:count]:
            if s_node['id'] not in conflicting_ids and any(
                _already_has_relation(graph, s_node, rel, obj_node)
                for obj_node in obj_nodes
            ):
                continue

            walked, walk_message = execute(
                f'[walk] <{subj}> ({s_node["id"]})'
            )
            grabbed, grab_message = execute(
                f'[grab] <{subj}> ({s_node["id"]})'
            )
            if not (walked and grabbed):
                raise RuntimeError(
                    f"Scene initialization failed while grabbing "
                    f"{subj}({s_node['id']}): "
                    f"walk={walked} {walk_message!r}, "
                    f"grab={grabbed} {grab_message!r}."
                )

            placed = False
            placement_errors = []
            for obj_node in obj_nodes:
                walked_to_dest, dest_message = execute(
                    f'[walk] <{obj}> ({obj_node["id"]})'
                )
                if not walked_to_dest:
                    placement_errors.append(
                        f"{obj_node['id']}: walk failed {dest_message!r}"
                    )
                    continue

                if rel == 'INSIDE':
                    # Opening an already-open container may report failure;
                    # placement itself is the authoritative check.
                    execute(f'[open] <{obj}> ({obj_node["id"]})')
                    placed, place_message = execute(
                        f'[putin] <{subj}> ({s_node["id"]}) '
                        f'<{obj}> ({obj_node["id"]})'
                    )
                else:
                    placed, place_message = execute(
                        f'[putback] <{subj}> ({s_node["id"]}) '
                        f'<{obj}> ({obj_node["id"]})'
                    )

                if placed:
                    break
                placement_errors.append(
                    f"{obj_node['id']}: placement failed {place_message!r}"
                )

            if not placed:
                raise RuntimeError(
                    f"Scene initialization failed while placing "
                    f"{subj}({s_node['id']}) {rel} {obj}: "
                    + "; ".join(placement_errors)
                )

            graph = env.get_graph()
            if not _already_has_relation(graph, s_node, rel, obj_node):
                raise RuntimeError(
                    f"Scene initialization verification failed: "
                    f"{subj}({s_node['id']}) is not {rel} "
                    f"{obj}({obj_node['id']})."
                )

    return True
def ensure_unity_running(unity_path, force_restart=False):
    import socket
    import time
    import subprocess
    
    def is_port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect(('127.0.0.1', port))
                return True
            except:
                return False

    if not force_restart and is_port_open(8080):
        return

    print("[INFO] Starting/Restarting Unity Simulator...")
    subprocess.run(["pkill", "-9", "-f", "VirtualHome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    cmd = [unity_path, "-batchmode", "-http-port=8080"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for _ in range(30):
        if is_port_open(8080):
            time.sleep(2)  # Give Unity extra time to fully init its HTTP server
            print("[INFO] Unity Simulator started successfully.")
            return
        time.sleep(1)
    
    raise RuntimeError("Failed to start Unity simulator on port 8080 after 30 seconds.")


def main():
    parser = argparse.ArgumentParser(description='VirtualHome E2E Test Runner')
    parser.add_argument(
        'config_paths',
        nargs='+',
        help='One or more config JSON files or directories (searched recursively).',
    )
    # ===================== 新增 --method 参数 =====================
    parser.add_argument(
        '--method',
        nargs='+',
        default=['robostate'],
        choices=list(AGENT_REGISTRY.keys()),
        help='Methods to evaluate: ' + ', '.join(AGENT_REGISTRY.keys())
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-5.4-mini',
        help='Shared LLM backbone used by all methods'
    )
    # (Timeout is dynamically calculated as max_steps * 5, --timeout argument removed)
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-run even if scenario already succeeded'
    )
    parser.add_argument(
        '--untested-only',
        action='store_true',
        help='Skip all scenarios that already have a complete result (even if they failed)'
    )
    parser.add_argument(
        '--retry-sr-lt',
        type=float,
        default=None,
        help='Retry completed scenarios with success rate <= this value (e.g. 0.5)'
    )
    parser.add_argument(
        '--unity-path',
        type=str,
        default='/Users/rushy/program/virtualhome/virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app/Contents/MacOS/VirtualHome',
        help='Path to Unity executable'
    )
    parser.add_argument('--daemon', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    config_inputs = [
        os.path.abspath(os.path.expanduser(path)) for path in args.config_paths
    ]
    try:
        all_configs = resolve_config_paths(config_inputs)
    except ValueError as exc:
        parser.error(str(exc))

    log_path = os.path.join(base_dir, 'test_runner.log')
    if not args.daemon:
        import subprocess
        cmd = [sys.executable, __file__]
        cmd.extend(config_inputs)
        cmd.append("--daemon")
        # 传递 method 参数到子进程
        cmd.append("--method")
        cmd.extend(args.method)
        cmd.extend(["--model", args.model])
        cmd.extend(["--unity-path", args.unity_path])
        if args.force:
            cmd.append("--force")
        if args.untested_only:
            cmd.append("--untested-only")
        if args.retry_sr_lt is not None:
            cmd.extend(["--retry-sr-lt", str(args.retry_sr_lt)])
        
        env = os.environ.copy()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
            cwd=project_root,
        )
        print(f"[INFO] Task started in background.")
        print(f"[INFO] Evaluating methods: {', '.join(args.method)}")
        print(f"[INFO] Monitor logs via: tail -f {log_path}")
        sys.exit(0)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Logger(log_path)
    sys.stderr = sys.stdout

    # Init engine
    ensure_unity_running(args.unity_path)
    try:
        env = UnityEnvironment(
            num_agents=1,
            observation_types=['partial'],
            executable_args={'file_name': None}
        )
    except Exception as initial_engine_error:
        print(
            f"[WARN] Unity port was open but the engine health check failed: "
            f"{initial_engine_error}. Restarting Unity..."
        )
        ensure_unity_running(args.unity_path, force_restart=True)
        env = UnityEnvironment(
            num_agents=1,
            observation_types=['partial'],
            executable_args={'file_name': None}
        )
    reset_environment_runtime(env)

    for method_name in args.method:
        results_dir = os.path.join(base_dir, 'results', method_name)
        success_dir = os.path.join(results_dir, 'success')
        fail_dir = os.path.join(results_dir, 'fail')
        standard_raw_logs_dir = os.path.join(results_dir, 'raw')
        table1_raw_logs_dir = os.path.join(
            base_dir, 'results', 'table1', '_raw', method_name
        )
        table4_raw_logs_root = os.path.join(
            base_dir, 'results', 'table4', '_raw'
        )
        table5_raw_logs_dir = os.path.join(
            base_dir, 'results', 'table5', '_raw', method_name
        )
        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(fail_dir, exist_ok=True)
        
        

        summary = {
            "method": method_name,
            "model": args.model,
            "total": len(all_configs),
            "skipped": 0,
            "success": 0,
            "fail": 0,
            "incomplete": 0,
            "failures": [],
            "extension_metrics": []
        }

        print(
            f"[INFO] Method={method_name} | "
            f"Model={args.model} | "
            f"Timeout=Dynamic (max_steps * 5)s"
        )

        for scenario_id, config_path, _config_metadata in all_configs:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            table1_run = config.get('table_id') == 'table1'
            table2_run = config.get('table_id') == 'table2'
            table3_run = config.get('table_id') == 'table3'
            table4_run = config.get('table_id') == 'table4'
            table5_run = config.get('table_id') == 'table5'
            if table1_run:
                raw_logs_dir = table1_raw_logs_dir
            elif table4_run:
                raw_logs_dir = os.path.join(
                    table4_raw_logs_root, str(config.get('model_alias', 'unknown'))
                )
            elif table5_run:
                raw_logs_dir = table5_raw_logs_dir
            else:
                raw_logs_dir = standard_raw_logs_dir
            os.makedirs(raw_logs_dir, exist_ok=True)

            if table1_run:
                configured_result_folder = table1_result_folder(
                    base_dir, config, method_name
                )
            elif table2_run:
                configured_result_folder = table2_result_folder(
                    base_dir, config, method_name
                )
            elif table3_run:
                configured_result_folder = table3_result_folder(
                    base_dir, config, method_name
                )
            elif table4_run:
                configured_result_folder = table4_result_folder(
                    base_dir, config, method_name
                )
            elif table5_run:
                configured_result_folder = table5_result_folder(
                    base_dir, config, method_name
                )
            else:
                configured_result_folder = source_tasks_result_folder(
                    base_dir, config, method_name, config_path
                )

            recorded_metrics = os.path.join(
                configured_result_folder, 'metrics.json'
            )
            if not args.force and os.path.exists(recorded_metrics):
                with open(recorded_metrics, 'r', encoding='utf-8') as metrics_file:
                    try:
                        prior_metrics = json.load(metrics_file)
                    except Exception:
                        prior_metrics = {}
                if prior_metrics.get('run_status') == 'complete':
                    sr = prior_metrics.get('sr', 0.0)
                    if (
                        table4_run
                        and prior_metrics.get("result_source") == "post_fix_rerun"
                        and prior_metrics.get("framework_revision")
                        == config.get("framework_revision")
                    ):
                        print(
                            f"[SKIP] {scenario_id} — interface-fix result "
                            "already recorded."
                        )
                        summary["skipped"] += 1
                        continue
                    
                    if getattr(args, 'untested_only', False):
                        print(f"[SKIP] {scenario_id} — previous run complete, skipped due to --untested-only.")
                        summary["skipped"] += 1
                        continue
                        
                    retry_threshold = getattr(args, 'retry_sr_lt', None)
                    if retry_threshold is not None:
                        if sr <= retry_threshold:
                            print(f"[RE-RUN] {scenario_id} — previous run SR={sr} <= {retry_threshold}.")
                            # Fall through to re-run
                        else:
                            print(f"[SKIP] {scenario_id} — already succeeded with SR={sr} > {retry_threshold}.")
                            summary["skipped"] += 1
                            continue
                    else:
                        print(f"[SKIP] {scenario_id} — already has a complete run (SR={sr}).")
                        summary["skipped"] += 1
                        continue

            print(f"\n==========================================")
            print(f"[RUN] {scenario_id}")

            agent_config = build_agent_config(config)
            configured_model = str(config.get("evaluation_model", args.model))

            env_id = config.get('environment_id', 0)

            def record_initialization_incomplete(reason):
                metrics = TaskProgressTracker(config).as_metrics()
                metrics.update({
                    "scenario_id": scenario_id,
                    "table_id": config.get("table_id"),
                    "experiment_axis": config.get("experiment_axis"),
                    "sample_id": config.get("sample_id"),
                    "setting": config.get("setting"),
                    "extension_type": config.get("extension_type"),
                    "framework_revision": config.get("framework_revision"),
                    "result_source": config.get("result_source"),
                    "previous_attempt_path": config.get("previous_attempt_path"),
                    "method": method_name,
                    "model": configured_model,
                    "success": False,
                    "run_status": "incomplete",
                    "valid_for_aggregation": False,
                    "reason": reason,
                    "steps_executed": 0,
                    "execution_time_seconds": 0,
                    "dynamic_event_counts": {},
                    "dynamic_event_trace": [],
                })
                summary["extension_metrics"].append(metrics)
                summary["incomplete"] += 1
                summary["failures"].append({
                    "scenario": scenario_id,
                    "reason": reason,
                    "run_status": "incomplete",
                })
                if table1_run:
                    write_result_artifacts(
                        table1_result_folder(base_dir, config, method_name),
                        config,
                        metrics,
                        method_name,
                        configured_model,
                    )
                elif table3_run:
                    write_result_artifacts(
                        table3_result_folder(base_dir, config, method_name),
                        config,
                        metrics,
                        method_name,
                        configured_model,
                    )
                elif table4_run:
                    write_result_artifacts(
                        table4_result_folder(base_dir, config, method_name),
                        config,
                        metrics,
                        method_name,
                        config.get("evaluation_model", args.model),
                    )
                elif table5_run:
                    write_result_artifacts(
                        table5_result_folder(base_dir, config, method_name),
                        config,
                        metrics,
                        method_name,
                        configured_model,
                    )

            old_stdout = sys.stdout
            # sys.stdout = open(os.devnull, 'w') # Commented out to see intermediate logs

            try:
                reset_environment_runtime(env)
                env.reset(environment_id=env_id)
            except Exception as e:
                print(f"[WARN] Engine Reset Failed: {e}. Attempting to restart Unity engine...")
                try:
                    ensure_unity_running(args.unity_path, force_restart=True)
                    env = UnityEnvironment(
                        num_agents=1,
                        observation_types=['partial'],
                        executable_args={'file_name': None}
                    )
                    reset_environment_runtime(env)
                    env.reset(environment_id=env_id)
                except Exception as e2:
                    sys.stdout = old_stdout
                    reason = f"Engine Reset Failed twice: {e2}"
                    print(f"  {reason}")
                    if table1_run or table3_run or table4_run or table5_run:
                        record_initialization_incomplete(reason)
                    else:
                        summary["fail"] += 1
                        summary["failures"].append({"scenario": scenario_id, "reason": reason})
                    continue

            try:
                apply_overrides(env, config, debug=False)
            except Exception as e:
                # sys.stdout.close()
                sys.stdout = old_stdout
                reason = f"Initialization Failed: {e}"
                print(f"  {reason}")
                if table1_run or table3_run or table4_run or table5_run:
                    record_initialization_incomplete(reason)
                else:
                    summary["fail"] += 1
                    summary["failures"].append({"scenario": scenario_id, "reason": reason})
                continue

            if table4_run:
                # Table 4 exposes only the class-name catalog requested by the
                # model-interface experiment. IDs, states, relations, and
                # evaluator success conditions remain private.
                initialized_graph = env.get_graph()
                agent_config["grounding_candidates"] = sorted({
                    str(node.get("class_name", "")).strip().lower()
                    for node in initialized_graph.get("nodes", [])
                    if str(node.get("class_name", "")).strip()
                    and str(node.get("category", "")) != "Rooms"
                    and str(node.get("class_name", "")).lower() != "character"
                })

            # ===================== 根据 method 选择 Agent =====================
            agent_cls = AGENT_REGISTRY[method_name]
            agent = agent_cls(
                model_name=configured_model,
                scenario_id=(
                    "evaluation_episode"
                    if method_name == "robostate"
                    else scenario_id
                )
            )
            # ================================================================

            # Prevent a failed run from copying a stale log produced by
            # another method or an earlier execution of the same scenario.
            scenario_log_file = os.path.join(
                raw_logs_dir,
                f"run_{scenario_id}.md"
            )
            if os.path.exists(scenario_log_file):
                os.remove(scenario_log_file)

            max_steps = int(config.get("max_steps", 15))
            timeout_seconds = max_steps * 5
            
            dynamic_events = config.get("dynamic_events", [])
            dynamic_delay_allowance = sum(
                e.get("effect", {}).get("duration_steps", 0) * e.get("max_triggers", 1)
                for e in dynamic_events
            )
            # Base stagnation limit of 15, plus any potential delays from dynamic traps
            stagnation_limit = min(15 + dynamic_delay_allowance, max_steps)

            class TimeoutException(Exception):
                pass

            def timeout_handler(signum, frame):
                raise TimeoutException(
                    f"Episode timed out after {timeout_seconds} seconds"
                )

            import time
            start_time = time.time()
            step_count = 0
            success = False
            reason = "Max steps reached"
            run_status = "complete"
            task_tracker = None
            dynamic_runtime = None
            ask_policy_satisfied_step = None
            logger = None
            simulated_user = None

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)

                from agent.utils.logger import AgentLogger

                logger = AgentLogger(
                    log_mode=config.get("log_mode", "markdown"),
                    scenario_id=scenario_id,
                    log_dir=raw_logs_dir
                )
                if config.get("simulated_user_intent"):
                    simulated_user_llm = LLMClient(
                        model_name=SIMULATED_USER_MODEL
                    )
                    simulated_user_llm.set_telemetry_logger(logger)
                    simulated_user = SimulatedUser(
                        simulated_user_llm,
                        config.get("goal_instruction", ""),
                        config["simulated_user_intent"],
                    )

                success_condition = config.get("success_condition", {})
                failure_condition = config.get("failure_condition")

                # Adapt the observation types for the unity environment
                env.observation_types = getattr(agent, "REQUIRED_OBSERVATION", ["partial"])

                task_tracker = TaskProgressTracker(config)
                dynamic_runtime = DynamicEventRuntime(
                    env,
                    config.get("dynamic_events", []),
                    logger,
                )
                # UnityEnvironment has a legacy dynamic-event implementation
                # with different countdown semantics. The runner is the sole
                # owner for these deterministic extension events.
                env.dynamic_events = []
                action_history = list(config.get("prior_action_history", []))
                
                consecutive_waits = 0
                last_task_completion_step = 0
                last_satisfied_count = 0

                while step_count < max_steps:
                    dynamic_runtime.before_step(step_count)
                    dynamic_runtime.expire(step_count)
                    graph = env.get_graph()
                    task_tracker.update(
                        graph,
                        step_count,
                        check_success,
                        logger,
                    )
                    
                    current_satisfied_count = sum(1 for t in task_tracker.tasks if t["currently_satisfied"])
                    if current_satisfied_count > last_satisfied_count:
                        last_satisfied_count = current_satisfied_count
                        last_task_completion_step = step_count
                    elif step_count - last_task_completion_step >= stagnation_limit:
                        success = False
                        reason = f"Agent stagnated ({stagnation_limit} steps without progress)"
                        break

                    if step_count == 0:
                        initially_satisfied = [
                            task["task_id"]
                            for task in task_tracker.tasks
                            if task["currently_satisfied"]
                        ]
                        if initially_satisfied:
                            success = False
                            reason = (
                                "Invalid benchmark: task(s) already satisfied at "
                                f"step 0: {initially_satisfied}"
                            )
                            run_status = "invalid"
                            break

                    if check_success(graph, success_condition):
                        if config.get("require_ask_to_pass", False):
                            has_asked = any(entry.get('action', '').lower().startswith('[ask]') for entry in action_history)
                            if not has_asked:
                                success = False
                                reason = "Failed: Did not ask for clarification"
                                break
                                
                        success = True
                        reason = "Goal Reached"
                        break

                    if failure_condition:
                        start_step = int(failure_condition.get("start_step", 0))
                        end_step = int(failure_condition.get("end_step", 999999))
                        if start_step <= step_count <= end_step and check_success(graph, failure_condition):
                            success = False
                            reason = "Failure condition met (Constraint Violated)"
                            break

                    obs = env.get_observations()[0]
                    if isinstance(obs, list) and len(obs) == 1:
                        obs = obs[0]

                    env_info = {
                        "step": step_count,
                        "logger": logger,
                        "action_history": action_history,
                        "task_progress": task_tracker.as_agent_info(),
                    }

                    try:
                        action_str = agent.get_action(obs, agent_config, env_info)
                    except Exception as e:
                        success = False
                        reason = f"Agent generation crashed: {e}"
                        run_status = "incomplete"
                        break

                    if action_str == "done()":
                        success = False
                        reason = "Agent terminated early without reaching goal"
                        break
                        
                    if action_str == "[wait]":
                        consecutive_waits += 1
                        if consecutive_waits >= 5:
                            success = False
                            reason = "Agent gave up (5 consecutive waits)"
                            break
                    else:
                        consecutive_waits = 0
                        
                    intercepted = False
                    action_success = False
                    env_done = False
                    info = {}
                    
                    if action_str.lower().startswith("[ask]"):
                        intercepted = True
                        used = len(clarification_trace(action_history))
                        budget = max(
                            0, int(config.get("clarification_budget", 1))
                        )
                        if used >= budget:
                            info = {
                                "action_success": False,
                                "action_message": (
                                    "Clarification budget exhausted."
                                ),
                                "error_type": "clarification_budget_exhausted",
                            }
                            logger.info(
                                "💬 CLARIFICATION: rejected request because "
                                f"budget {budget} is exhausted."
                            )
                        else:
                            if simulated_user is not None:
                                clarification_reply = simulated_user.answer(
                                    action_str[5:].strip(),
                                    action_history,
                                )
                            else:
                                clarification_reply = config.get(
                                    "user_clarification_reply",
                                    config.get(
                                        "default_clarification_reply",
                                        DEFAULT_CLARIFICATION_REPLY,
                                    ),
                                )
                            clarification_reply = str(
                                clarification_reply
                            ).strip()
                            if clarification_reply:
                                info = {
                                    "action_success": True,
                                    "action_message": clarification_reply,
                                }
                                logger.info(
                                    "💬 CLARIFICATION: answered agent request "
                                    f"with {clarification_reply!r}."
                                )
                            else:
                                info = {
                                    "action_success": False,
                                    "action_message": (
                                        "Simulated user returned no answer."
                                    ),
                                    "error_type": "empty_clarification_reply",
                                }
                                logger.info(
                                    "💬 CLARIFICATION: simulated user returned "
                                    "an empty answer; budget was not consumed."
                                )

                    if not intercepted:
                        intercepted, event_info = dynamic_runtime.before_action(
                            step_count,
                            action_str,
                            graph,
                        )
                        if intercepted:
                            info = event_info

                    if not intercepted:
                        _, _, env_done, info = env.step({0: action_str})
                    
                    action_success = info.get("action_success", False) if info else False

                    history_entry = {
                        "step": step_count,
                        "action": action_str,
                        "success": action_success,
                    }
                    if info and info.get("action_message"):
                        history_entry["message" if action_success else "error"] = info["action_message"]
                    if info and info.get("error_type"):
                        history_entry["error_type"] = info["error_type"]
                        history_entry["temporary"] = bool(info.get("temporary"))
                    action_history.append(history_entry)

                    # Refresh evaluator truth immediately so the step log and
                    # the next agent call see the action's resulting state.
                    try:
                        task_tracker.update(
                            env.get_graph(),
                            step_count + 1,
                            check_success,
                            logger,
                        )
                    except Exception as progress_error:
                        logger.error(
                            f"Task progress refresh failed: {progress_error}"
                        )

                    try:
                        # Write markdown step
                        decision = getattr(agent, "last_decision", {}) or {}
                        logger.write_step(
                            step_count,
                            action_str,
                            decision.get("sdg"),
                            decision.get("observed_items", []),
                            decision.get("current_node_focus"),
                            decision.get("satisfied_nodes"),
                            action_success=action_success,
                            action_message=(
                                info.get("action_message") if info else None
                            ),
                            task_progress=task_tracker.as_log_info(),
                            active_task_id=decision.get("active_task_id"),
                            decision_source=decision.get("source"),
                        )
                    except Exception:
                        pass

                    if (
                        action_str.lower().startswith("[ask]")
                        and str(config.get("on_ask_policy", "")).upper() == "SUCCESS"
                    ):
                        ask_policy_satisfied_step = step_count
                        success = True
                        reason = "Clarification/impossibility correctly requested"
                        break

                    if env_done:
                        success = False
                        reason = "Environment terminated unexpectedly"
                        run_status = "incomplete"
                        break

                    step_count += 1

                # Final verification if loop finished
                if not success and step_count == max_steps:
                    dynamic_runtime.expire(step_count)
                    graph = env.get_graph()
                    task_tracker.update(
                        graph,
                        step_count,
                        check_success,
                        logger,
                    )
                    if check_success(graph, success_condition):
                        if config.get("require_ask_to_pass", False):
                            has_asked = any(entry.get('action', '').lower().startswith('[ask]') for entry in action_history)
                            if not has_asked:
                                success = False
                                reason = "Failed: Did not ask for clarification"
                            else:
                                success = True
                                reason = "Goal Reached at last step"
                        else:
                            success = True
                            reason = "Goal Reached at last step"

                signal.alarm(0)
            except TimeoutException as e:
                success = False
                reason = str(e)
                run_status = "incomplete"
            except Exception as e:
                signal.alarm(0)
                success = False
                reason = f"Exception: {e}"
                run_status = "incomplete"
            finally:
                # sys.stdout.close()
                sys.stdout = old_stdout

            execution_time = time.time() - start_time

            if task_tracker is None:
                task_tracker = TaskProgressTracker(config)
            metrics = task_tracker.as_metrics()
            if ask_policy_satisfied_step is not None and success:
                metrics.update({
                    "task_completed": 1,
                    "task_total": 1,
                    "sr": 1.0,
                    "ps": float(ask_policy_satisfied_step),
                    "ps_sum": int(ask_policy_satisfied_step),
                    "ps_count": 1,
                    "mean_completion_step": float(ask_policy_satisfied_step),
                    "tasks": [{
                        "task_id": config.get("scenario_id", "task_1"),
                        "currently_satisfied": True,
                        "ever_satisfied": True,
                        "first_satisfied_step": int(ask_policy_satisfied_step),
                        "completed": True,
                        "completion_step": int(ask_policy_satisfied_step),
                        "completion_evidence": "on_ask_policy",
                    }],
                })
            if len(task_tracker.tasks) > 1 and success and metrics["sr"] < 1.0:
                success = False
                reason = "Not all multi-task success conditions were completed"
            event_counts = (
                dynamic_runtime.event_counts()
                if dynamic_runtime is not None
                else {}
            )
            missing_dynamic_events = [
                event_id
                for event_id, counts in event_counts.items()
                if counts.get("max_triggers") is not None
                and counts.get("times_triggered") != counts.get("max_triggers")
            ]
            if success and missing_dynamic_events:
                success = False
                run_status = "invalid"
                reason = (
                    "Invalid benchmark: success before configured dynamic "
                    f"events completed: {missing_dynamic_events}"
                )
            metrics.update(
                {
                    "scenario_id": scenario_id,
                    "table_id": config.get("table_id"),
                    "experiment_axis": config.get("experiment_axis"),
                    "sample_id": config.get("sample_id"),
                    "setting": config.get("setting"),
                    "extension_type": config.get("extension_type"),
                    "ablation_profile": config.get("ablation_profile"),
                    "source_scenario_id": config.get("source_scenario_id"),
                    "framework_revision": config.get("framework_revision"),
                    "result_source": config.get("result_source"),
                    "previous_attempt_path": config.get("previous_attempt_path"),
                    "method": method_name,
                    "model": configured_model,
                    "success": bool(success),
                    "run_status": run_status,
                    "valid_for_aggregation": run_status == "complete",
                    "reason": reason,
                    "steps_executed": step_count,
                    "execution_time_seconds": round(execution_time, 2),
                    "dynamic_event_counts": event_counts,
                    "dynamic_event_trace": (
                        copy.deepcopy(dynamic_runtime.trace)
                        if dynamic_runtime is not None
                        else []
                    ),
                    "clarification_budget": max(
                        0, int(config.get("clarification_budget", 1))
                    ),
                    "clarification_count": len(
                        clarification_trace(action_history)
                    ),
                    "clarification_trace": clarification_trace(action_history),
                    "simulated_user_model": (
                        SIMULATED_USER_MODEL if simulated_user is not None else None
                    ),
                }
            )
            metrics["module_stats"] = logger.module_stats() if logger else {}
            summary["extension_metrics"].append(metrics)

            print(f"  Result: {'✅ SUCCESS' if success else '❌ FAILED'} — {reason}")
            print(f"  Time: {execution_time:.2f} seconds")
            print(
                f"  Metrics: SR={metrics['sr']:.4f} | "
                f"PS={metrics['ps'] if metrics['ps'] is not None else 'n/a'} | "
                f"Tasks={metrics['task_completed']}/{metrics['task_total']}"
            )

            if table1_run:
                dest_folder = table1_result_folder(base_dir, config, method_name)
            elif table2_run:
                dest_folder = table2_result_folder(base_dir, config, method_name)
            elif table3_run:
                dest_folder = table3_result_folder(base_dir, config, method_name)
            elif table4_run:
                dest_folder = table4_result_folder(base_dir, config, method_name)
            elif table5_run:
                dest_folder = table5_result_folder(base_dir, config, method_name)
            else:
                dest_folder = source_tasks_result_folder(base_dir, config, method_name, config_path)
            write_result_artifacts(
                dest_folder,
                config,
                metrics,
                method_name,
                configured_model,
                scenario_log_file,
                logger.llm_calls_file if logger else None,
            )

            if run_status != "complete":
                summary["incomplete"] += 1
                summary["failures"].append({
                    "scenario": scenario_id,
                    "reason": reason,
                    "run_status": run_status,
                })
                print(f"[WARN] Run was {run_status} ({reason}). Proactively restarting Unity...")
                try:
                    ensure_unity_running(args.unity_path, force_restart=True)
                    env = UnityEnvironment(num_agents=1, observation_types=['partial'], executable_args={'file_name': None})
                except Exception as ex:
                    print(f"[ERROR] Proactive restart failed: {ex}")
            elif success:
                summary["success"] += 1
                if not table1_run:
                    fail_path = os.path.join(fail_dir, scenario_id)
                    if os.path.exists(fail_path):
                        shutil.rmtree(fail_path, ignore_errors=True)
            else:
                summary["fail"] += 1
                summary["failures"].append({"scenario": scenario_id, "reason": reason})

        print(f"\n\n==========================================")
        print(
            f"Testing Complete! "
            f"Method={summary['method']} | "
            f"Model={summary['model']}"
        )
        print(
            f"Total: {summary['total']} | "
            f"Skipped: {summary['skipped']} | "
            f"✅ Success: {summary['success']} | "
            f"❌ Fail: {summary['fail']} | "
            f"Incomplete/invalid: {summary['incomplete']}"
        )
        if summary["extension_metrics"]:
            measured = [
                item for item in summary["extension_metrics"]
                if item.get("valid_for_aggregation", True)
            ]
            task_total = sum(item["task_total"] for item in measured)
            task_completed = sum(item["task_completed"] for item in measured)
            ps_sum = sum(item.get("ps_sum", 0) for item in measured)
            ps_count = sum(item.get("ps_count", 0) for item in measured)
            summary["aggregate_task_completed"] = task_completed
            summary["aggregate_task_total"] = task_total
            summary["aggregate_ps_count"] = ps_count
            summary["aggregate_sr"] = (
                round(task_completed / task_total, 4) if task_total else None
            )
            summary["aggregate_ps"] = (
                round(ps_sum / ps_count, 4) if ps_count else None
            )
            print(
                f"Aggregate: SR={summary['aggregate_sr']} | "
                f"PS={summary['aggregate_ps']}"
            )

        if config.get("table_id") == "table4":
            summary_path = os.path.join(
                base_dir,
                "results",
                "table4",
                f"summary_run_{method_name}_{config.get('model_alias', 'mixed')}.json",
            )
        elif config.get("table_id") == "table5":
            summary_path = os.path.join(
                base_dir,
                "results",
                "table5",
                f"summary_run_{method_name}.json",
            )
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        else:
            summary_path = os.path.join(
                results_dir,
                f"summary_run_{method_name}.json",
            )
        with open(summary_path, 'w', encoding='utf-8') as summary_file:
            json.dump(summary, summary_file, indent=4, ensure_ascii=False)

    if hasattr(sys.stdout, 'log') and not sys.stdout.log.closed:
        sys.stdout.log.close()
    sys.stdout = original_stdout
    sys.stderr = original_stderr

if __name__ == '__main__':
    main()
