import os
import json
import glob
import shutil
import argparse
import traceback
import copy
import re

import sys
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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


class TaskProgressTracker:
    """Tracks per-instruction completion without changing success semantics."""

    def __init__(self, config):
        configured_tasks = config.get("tasks") or []
        if configured_tasks:
            tasks = configured_tasks
        else:
            tasks = [
                {
                    "task_id": config.get("scenario_id", "task_1"),
                    "instruction": config.get("goal_instruction", ""),
                    "success_condition": config.get("success_condition", {}),
                }
            ]

        self.tasks = [
            {
                "task_id": task.get("task_id", f"task_{index + 1}"),
                "instruction": task.get("instruction", ""),
                "success_condition": copy.deepcopy(task.get("success_condition", {})),
                "completed": False,
                "completion_step": None,
            }
            for index, task in enumerate(tasks)
        ]

    def update(self, graph, step, check_success, logger=None):
        for task in self.tasks:
            if task["completed"]:
                continue
            if check_success(graph, task["success_condition"]):
                task["completed"] = True
                task["completion_step"] = int(step)
                if logger:
                    logger.info(
                        f"✅ TASK COMPLETED: {task['task_id']} at step {step}."
                    )

    def as_metrics(self):
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task["completed"])
        completion_steps = [
            task["completion_step"]
            for task in self.tasks
            if task["completion_step"] is not None
        ]
        mean_completion_step = (
            round(sum(completion_steps) / len(completion_steps), 4)
            if completion_steps
            else None
        )
        return {
            "task_total": total,
            "task_completed": completed,
            # SR is strict episode success; PS exposes partial task progress.
            "sr": 1.0 if total and completed == total else 0.0,
            "ps": round(completed / total, 4) if total else 0.0,
            "mean_completion_step": mean_completion_step,
            "tasks": copy.deepcopy(self.tasks),
        }


class DynamicEventRuntime:
    """Runner-owned deterministic action-triggered event scheduler."""

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
            message = (
                "动作失败：目标物品突然消失了，请等待其重新出现后重试。"
            )
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
                message = "动作失败：目标物品当前不可见，请等待或重新规划。"

        info = {"action_message": message} if intercepted else {}
        return intercepted, info

    def event_counts(self):
        return {
            event["_runtime_id"]: {
                "times_triggered": event["_times_triggered"],
                "max_triggers": int(event.get("max_triggers", 1)),
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


def apply_overrides(env, config, debug=False):
    """
    Applies scenario overrides using monkey-patching for states and physical actions for relations.
    """
    def _install_state_patch(env, overrides, debug):
        original = env.get_graph
        # Map to store which IDs get which overrides so they don't shift
        # Key: override index, Value: list of node IDs assigned to this override
        locked_assignments = {}
        
        def patched(*args, **kwargs):
            graph = original(*args, **kwargs)
            
            for ov_idx, ov in enumerate(overrides):
                rm, add = ov.get('remove_states', []), ov.get('add_states', [])
                add_props = ov.get('add_properties', [])
                i_filter = ov.get('instance_filter')
                in_room  = ov.get('in_room')
                
                # If we haven't locked IDs for this override yet, do it now
                if ov_idx not in locked_assignments:
                    assigned_ids = []
                    for cls in ov.get('target_classes', []):
                        candidates = [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]
                        if in_room:
                            room_ids  = {n['id'] for n in graph['nodes'] if n['class_name'].lower() == in_room.lower()}
                            inside_ids = {e['from_id'] for e in graph['edges'] if e['relation_type']=='INSIDE' and e['to_id'] in room_ids}
                            candidates = [n for n in candidates if n['id'] in inside_ids]
                        if i_filter and 'index' in i_filter:
                            idx = i_filter['index']
                            candidates = [candidates[idx]] if idx < len(candidates) else []
                        assigned_ids.extend([n['id'] for n in candidates])
                    locked_assignments[ov_idx] = assigned_ids
                
                # Apply patches to the locked IDs
                target_ids = locked_assignments[ov_idx]
                for node in graph['nodes']:
                    if node['id'] in target_ids:
                        # Initial overrides establish the episode's starting
                        # state. Once a real/mock action records a custom state
                        # for this node, that action must take precedence.
                        custom_states = getattr(env, 'custom_states', {}) or {}
                        if node['id'] in custom_states:
                            continue
                        st = set(node.get('states', []))
                        props = set(node.get('properties', []))
                        for s in rm: st.discard(s)
                        for s in add:
                            if s == 'PLUGGED_OUT' and 'HAS_PLUG' not in props: continue
                            if s == 'OFF' and 'HAS_SWITCH' not in props: continue
                            st.add(s)
                        for p in add_props:
                            props.add(p)
                        node['states'] = list(st)
                        node['properties'] = list(props)
                        
            return graph
            
        env.get_graph = patched

    from agent.utils.graph_utils import find_node, find_all

    def _hide_extra_nodes(env, nodes_to_hide):
        if not hasattr(env, 'active_hidden_nodes'):
            env.active_hidden_nodes = {}
        for n in nodes_to_hide:
            env.active_hidden_nodes[n['id']] = float('inf')
        if nodes_to_hide:
            env.changed_graph = True

    def _already_has_relation(graph, s_node, rel, obj_node):
        return any(e for e in graph['edges'] if e['from_id'] == s_node['id'] and e['relation_type'] == rel and e['to_id'] == obj_node['id'])

    def execute(action_str):
        obs, reward, done, info = env.step({0: action_str})
        success = info.get('action_success', False)
        return success, info.get('action_message', '')

    def destination_candidates(graph, class_name, in_room=None):
        candidates = find_all(graph, class_name)
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

    # 1. 状态覆盖
    state_overrides = config.get('initial_states_override', [])
    if state_overrides:
        _install_state_patch(env, state_overrides, debug)

    # 2. 关系覆盖 (位置)
    graph = env.get_graph()
    for ro in config.get('initial_relations_override', []):
        subj   = ro['subject'].lower()
        count  = ro.get('count', 1)
        
        subj_nodes = find_all(graph, subj)

        # 隐藏多余的对象实例
        if len(subj_nodes) > count:
            _hide_extra_nodes(env, subj_nodes[count:])
            subj_nodes = subj_nodes[:count]

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
        if not obj_nodes:
            raise RuntimeError(
                f"Scene initialization failed: No destination '{obj}' "
                f"matched in_room={in_room!r}."
            )

        # Use real Unity actions so the configured graph and Unity physics stay
        # aligned. Some scenes contain multiple surfaces of the same class and
        # only a subset accept a given object, so try each matching instance.
        for s_node in subj_nodes[:count]:
            if any(
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
    parser.add_argument('target', type=str, nargs='*', default=[],
                        help='Target scenario IDs or prefixes (e.g. P3 P3_12). Leave empty for all.')
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
    extension_group = parser.add_mutually_exclusive_group()
    extension_group.add_argument(
        '--multi-scale',
        type=int,
        choices=[3, 5, 7],
        help='Run E-only multi-task configs with the selected instruction scale'
    )
    extension_group.add_argument(
        '--semantic-type',
        choices=['sentence_wise', 'summarized', 'vague'],
        help='Run single-task semantic-variation configs of the selected type'
    )
    extension_group.add_argument(
        '--dynamic-difficulty',
        choices=['low', 'medium', 'high'],
        help='Run repeated-hide configs of the selected dynamic difficulty'
    )
    # ============================================================
    parser.add_argument('--daemon', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    configs_dir = os.path.join(base_dir, 'configs')

    log_path = os.path.join(base_dir, 'test_runner.log')
    if not args.daemon:
        import subprocess
        cmd = [sys.executable, __file__]
        if args.target:
            cmd.extend(args.target)
        cmd.append("--daemon")
        # 传递 method 参数到子进程
        cmd.append("--method")
        cmd.extend(args.method)
        cmd.extend(["--model", args.model])
        cmd.extend(["--unity-path", args.unity_path])
        if args.multi_scale is not None:
            cmd.extend(["--multi-scale", str(args.multi_scale)])
        elif args.semantic_type:
            cmd.extend(["--semantic-type", args.semantic_type])
        elif args.dynamic_difficulty:
            cmd.extend(["--dynamic-difficulty", args.dynamic_difficulty])
        if args.force:
            cmd.append("--force")
        
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        print(f"[INFO] Task started in background.")
        print(f"[INFO] Evaluating methods: {', '.join(args.method)}")
        print(f"[INFO] Monitor logs via: tail -f {log_path}")
        sys.exit(0)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Logger(log_path)
    sys.stderr = sys.stdout

    # Gather configs. Extension suites are intentionally mutually exclusive;
    # without an extension selector, preserve the legacy dataset behavior.
    all_configs = []
    selected_extension = None
    selected_value = None
    if args.multi_scale is not None:
        selected_dirs = ['multi']
        selected_extension = 'multi'
        selected_value = args.multi_scale
    elif args.semantic_type:
        selected_dirs = ['semantic']
        selected_extension = 'semantic'
        selected_value = args.semantic_type
    elif args.dynamic_difficulty:
        selected_dirs = ['dynamic']
        selected_extension = 'dynamic'
        selected_value = args.dynamic_difficulty
    else:
        selected_dirs = ['g_class', 'm_class', 'p_class', 'ExRAP']

    for cls_dir in selected_dirs:
        target_dir = os.path.join(configs_dir, cls_dir)
        if os.path.exists(target_dir):
            for path in glob.glob(os.path.join(target_dir, '*.json')):
                with open(path, 'r', encoding='utf-8') as config_file:
                    config_metadata = json.load(config_file)
                scenario_id = config_metadata.get(
                    'scenario_id',
                    os.path.splitext(os.path.basename(path))[0]
                )
                if selected_extension == 'multi':
                    matches_extension = (
                        config_metadata.get('extension_type') == 'multi'
                        and config_metadata.get('instruction_scale') == selected_value
                    )
                elif selected_extension == 'semantic':
                    matches_extension = (
                        config_metadata.get('extension_type') == 'semantic'
                        and config_metadata.get('instruction_type') == selected_value
                    )
                elif selected_extension == 'dynamic':
                    matches_extension = (
                        config_metadata.get('extension_type') == 'dynamic'
                        and config_metadata.get('dynamic_difficulty') == selected_value
                    )
                else:
                    matches_extension = True
                if not matches_extension:
                    continue
                if args.target and not scenario_id.startswith(tuple(args.target)):
                    continue
                all_configs.append((scenario_id, path))
    all_configs = sorted(all_configs)

    if selected_extension and not all_configs:
        raise RuntimeError(
            f"No configs matched extension={selected_extension!r}, "
            f"value={selected_value!r}, targets={args.target!r}."
        )

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
        raw_logs_dir = os.path.join(results_dir, 'raw')
        
        os.makedirs(success_dir, exist_ok=True)
        os.makedirs(fail_dir, exist_ok=True)
        os.makedirs(raw_logs_dir, exist_ok=True)
        
        

        summary = {
            "method": method_name,
            "model": args.model,
            "total": len(all_configs),
            "skipped": 0,
            "success": 0,
            "fail": 0,
            "failures": [],
            "extension_metrics": []
        }

        print(
            f"[INFO] Method={method_name} | "
            f"Model={args.model} | "
            f"Timeout=Dynamic (max_steps * 5)s"
        )

        for scenario_id, config_path in all_configs:
            if not args.force and os.path.exists(os.path.join(success_dir, scenario_id)):
                print(f"[SKIP] {scenario_id} — already succeeded.")
                summary["skipped"] += 1
                fail_path = os.path.join(fail_dir, scenario_id)
                if os.path.exists(fail_path):
                    shutil.rmtree(fail_path, ignore_errors=True)
                continue

            print(f"\n==========================================")
            print(f"[RUN] {scenario_id}")

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            env_id = config.get('environment_id', 0)

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
                summary["fail"] += 1
                summary["failures"].append({"scenario": scenario_id, "reason": reason})
                continue

            # ===================== 根据 method 选择 Agent =====================
            agent_cls = AGENT_REGISTRY[method_name]
            agent = agent_cls(
                model_name=args.model,
                scenario_id=scenario_id
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
            task_tracker = None
            dynamic_runtime = None

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)

                from evaluation.condition_checker import check_success
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
                        "hidden_nodes": env.active_hidden_nodes
                    }

                    try:
                        action_str = agent.get_action(obs, config, env_info)
                    except Exception as e:
                        success = False
                        reason = f"Agent generation crashed: {e}"
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
                    action_history.append(history_entry)

                    try:
                        # Write markdown step
                        logger.write_step(step_count, action_str, None, [])
                    except Exception:
                        pass

                    if env_done:
                        success = False
                        reason = "Environment terminated unexpectedly"
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
            except Exception as e:
                signal.alarm(0)
                success = False
                reason = f"Exception: {e}"
            finally:
                # sys.stdout.close()
                sys.stdout = old_stdout

            execution_time = time.time() - start_time

            if task_tracker is None:
                task_tracker = TaskProgressTracker(config)
            metrics = task_tracker.as_metrics()
            if config.get("extension_type") == "multi" and success and metrics["sr"] < 1.0:
                success = False
                reason = "Not all multi-task success conditions were completed"
            metrics.update(
                {
                    "scenario_id": scenario_id,
                    "extension_type": config.get("extension_type"),
                    "method": method_name,
                    "model": args.model,
                    "success": bool(success),
                    "reason": reason,
                    "steps_executed": step_count,
                    "execution_time_seconds": round(execution_time, 2),
                    "dynamic_event_counts": (
                        dynamic_runtime.event_counts()
                        if dynamic_runtime is not None
                        else {}
                    ),
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
                f"PS={metrics['ps']:.4f} | "
                f"Tasks={metrics['task_completed']}/{metrics['task_total']}"
            )

            dest_parent = success_dir if success else fail_dir
            dest_folder = os.path.join(dest_parent, scenario_id)
            os.makedirs(dest_folder, exist_ok=True)

            config['evaluation_method'] = method_name
            config['evaluation_model'] = args.model
            config['execution_time_seconds'] = round(
                execution_time,
                2
            )
            with open(os.path.join(dest_folder, 'config.json'), 'w', encoding='utf-8') as cf:
                json.dump(config, cf, indent=4, ensure_ascii=False)
            with open(os.path.join(dest_folder, 'metrics.json'), 'w', encoding='utf-8') as mf:
                json.dump(metrics, mf, indent=4, ensure_ascii=False)

            if os.path.exists(scenario_log_file):
                shutil.copy(
                    scenario_log_file,
                    os.path.join(
                        dest_folder,
                        f"run_{scenario_id}.md"
                    )
                )

            if success:
                summary["success"] += 1
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
            f"❌ Fail: {summary['fail']}"
        )
        if summary["extension_metrics"]:
            measured = summary["extension_metrics"]
            summary["aggregate_sr"] = round(
                sum(item["sr"] for item in measured) / len(measured),
                4,
            )
            summary["aggregate_ps"] = round(
                sum(item["ps"] for item in measured) / len(measured),
                4,
            )
            print(
                f"Aggregate: SR={summary['aggregate_sr']:.4f} | "
                f"PS={summary['aggregate_ps']:.4f}"
            )

        summary_suffix = (
            f"{selected_extension}_{selected_value}"
            if selected_extension
            else "legacy"
        )
        summary_path = os.path.join(
            results_dir,
            f"summary_{summary_suffix}.json",
        )
        with open(summary_path, 'w', encoding='utf-8') as summary_file:
            json.dump(summary, summary_file, indent=4, ensure_ascii=False)

    if hasattr(sys.stdout, 'log') and not sys.stdout.log.closed:
        sys.stdout.log.close()
    sys.stdout = original_stdout
    sys.stderr = original_stderr

if __name__ == '__main__':
    main()
