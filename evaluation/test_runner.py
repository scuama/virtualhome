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

DEFAULT_CLARIFICATION_REPLY = "nothing to claim"

AGENT_CONFIG_ALLOWLIST = {
    "goal_instruction",
    "grounding_candidates",
    "instruction_type",
    "log_mode",
    "preprocessed_instruction",
    "robostate_task_failure_limit",
    "scheduled_rules",
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

            # Table 1 binds disturbance to one concrete instance. An action on
            # another object of the same class must not consume a trigger.
            target_candidates = sorted(
                [
                    node for node in graph.get("nodes", [])
                    if str(node.get("class_name", "")).lower() == target_class
                ],
                key=lambda node: int(node.get("id", -1)),
            )
            instance_index = int(effect.get("instance_index", 0))
            if (
                instance_index >= len(target_candidates)
                or int(target_candidates[instance_index].get("id", -1)) != target_id
            ):
                continue

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
    return os.path.join(
        base_dir,
        'results',
        'table1',
        str(config['experiment_axis']),
        str(config['setting']),
        method_name,
        str(config['sample_id']),
    )


def write_result_artifacts(
    dest_folder,
    config,
    metrics,
    method_name,
    model_name,
    scenario_log_file=None,
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
            raw_logs_dir = (
                table1_raw_logs_dir if table1_run else standard_raw_logs_dir
            )
            os.makedirs(raw_logs_dir, exist_ok=True)

            if table1_run:
                configured_result_folder = table1_result_folder(
                    base_dir, config, method_name
                )
                recorded_metrics = os.path.join(
                    configured_result_folder, 'metrics.json'
                )
                if not args.force and os.path.exists(recorded_metrics):
                    with open(recorded_metrics, 'r', encoding='utf-8') as metrics_file:
                        prior_metrics = json.load(metrics_file)
                    if prior_metrics.get('run_status') == 'complete':
                        print(f"[SKIP] {scenario_id} — complete Table 1 result exists.")
                        summary["skipped"] += 1
                        continue
            elif not args.force and os.path.exists(
                os.path.join(success_dir, scenario_id)
            ):
                print(f"[SKIP] {scenario_id} — already succeeded.")
                summary["skipped"] += 1
                fail_path = os.path.join(fail_dir, scenario_id)
                if os.path.exists(fail_path):
                    shutil.rmtree(fail_path, ignore_errors=True)
                continue

            print(f"\n==========================================")
            print(f"[RUN] {scenario_id}")

            agent_config = build_agent_config(config)

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
                    "method": method_name,
                    "model": args.model,
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
                        args.model,
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
                    if table1_run:
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
                if table1_run:
                    record_initialization_incomplete(reason)
                else:
                    summary["fail"] += 1
                    summary["failures"].append({"scenario": scenario_id, "reason": reason})
                continue

            # ===================== 根据 method 选择 Agent =====================
            agent_cls = AGENT_REGISTRY[method_name]
            agent = agent_cls(
                model_name=args.model,
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

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)

                from agent.utils.logger import AgentLogger

                logger = AgentLogger(
                    log_mode=config.get("log_mode", "markdown"),
                    scenario_id=scenario_id,
                    log_dir=raw_logs_dir
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
                        
                    intercepted = False
                    action_success = False
                    env_done = False
                    info = {}
                    
                    if action_str.lower().startswith("[ask]"):
                        clarification_reply = config.get(
                            "user_clarification_reply",
                            config.get(
                                "default_clarification_reply",
                                DEFAULT_CLARIFICATION_REPLY,
                            ),
                        )
                        intercepted = True
                        info = {
                            "action_success": True,
                            "action_message": clarification_reply,
                        }
                        logger.info(
                            "💬 CLARIFICATION: answered agent request with "
                            f"{clarification_reply!r}."
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
                    "method": method_name,
                    "model": args.model,
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
                }
            )
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
            else:
                dest_parent = success_dir if success else fail_dir
                dest_folder = os.path.join(dest_parent, scenario_id)
            write_result_artifacts(
                dest_folder,
                config,
                metrics,
                method_name,
                args.model,
                scenario_log_file,
            )

            if run_status != "complete":
                summary["incomplete"] += 1
                summary["failures"].append({
                    "scenario": scenario_id,
                    "reason": reason,
                    "run_status": run_status,
                })
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
