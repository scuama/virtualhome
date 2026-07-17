import os
import json
import glob
import shutil
import argparse
import traceback

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
                        # Do not skip if in custom, we want to MERGE our colors with physics states like COLD!
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

    def _already_has_relation(graph, s_node, rel, obj_node):
        return any(e for e in graph['edges'] if e['from_id'] == s_node['id'] and e['relation_type'] == rel and e['to_id'] == obj_node['id'])

    def execute(action_str):
        obs, reward, done, info = env.step({0: action_str})
        success = info.get('action_success', False)
        return success

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

        obj_node   = find_node(graph, obj, in_room)
        if not obj_node: continue

        # 依靠物理动作将物品就位
        for s_node in subj_nodes[:count]:
            if _already_has_relation(graph, s_node, rel, obj_node): continue
            execute(f'[walk] <{subj}> ({s_node["id"]})')
            execute(f'[grab] <{subj}> ({s_node["id"]})')
            execute(f'[walk] <{obj}> ({obj_node["id"]})')
            if rel == 'INSIDE':
                execute(f'[open] <{obj}> ({obj_node["id"]})')
                execute(f'[putin] <{subj}> ({s_node["id"]}) <{obj}> ({obj_node["id"]})')
                execute(f'[close] <{obj}> ({obj_node["id"]})')
            else:
                execute(f'[putback] <{subj}> ({s_node["id"]}) <{obj}> ({obj_node["id"]})')
        graph = env.get_graph()

    return True


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
    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Per-episode timeout in seconds (default: 600)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-run even if scenario already succeeded'
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

    # Gather configs
    all_configs = []
    for cls_dir in ['g_class', 'm_class', 'p_class','ExRAP']:
        target_dir = os.path.join(configs_dir, cls_dir)
        if os.path.exists(target_dir):
            for path in glob.glob(os.path.join(target_dir, '*.json')):
                scenario_id = os.path.splitext(os.path.basename(path))[0]
                if args.target and not scenario_id.startswith(tuple(args.target)):
                    continue
                all_configs.append((scenario_id, path))
    all_configs = sorted(all_configs)

    # Init engine
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': None}
    )

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
            "failures": []
        }

        print(
            f"[INFO] Method={method_name} | "
            f"Model={args.model} | "
            f"Timeout={args.timeout}s"
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
                env.reset(environment_id=env_id)
            except Exception as e:
                # sys.stdout.close()
                sys.stdout = old_stdout
                reason = f"Engine Reset Failed: {e}"
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

                step_count = 0
                success = False
                reason = "Max steps reached"
                
                if not hasattr(env, 'active_hidden_nodes'):
                    env.active_hidden_nodes = {}
                env.dynamic_events = config.get("dynamic_events", [])
                for ev in env.dynamic_events:
                    ev["times_triggered"] = 0

                # Initial observation
                obs = env.get_observations()[0]
                if isinstance(obs, list) and len(obs) == 1:
                    obs = obs[0]

                action_history = list(config.get("prior_action_history", []))

                while step_count < max_steps:
                    graph = env.get_graph()

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
                        if "user_clarification_reply" in config:
                            intercepted = True
                            info = {
                                "action_success": True,
                                "action_message": config["user_clarification_reply"]
                            }
                        else:
                            policy = config.get("on_ask_policy", "FAIL")
                            if policy == "SUCCESS":
                                success = True
                                reason = "Goal Reached (Help Asked)"
                                break
                            else:
                                success = False
                                reason = "Agent requested help, which is not permitted"
                                break

                    import re
                    
                    for ev in env.dynamic_events:
                        trigger = ev['trigger']
                        if ev['times_triggered'] >= ev.get('max_triggers', 1):
                            continue

                        if f"[{trigger['action']}]" in action_str.lower() and f"<{trigger['target'].lower()}>" in action_str.lower():
                            ev_match = re.search(r'\(\s*(\d+)\s*\)', action_str)
                            if ev_match:
                                t_id = int(ev_match.group(1))
                                req_state = trigger.get('target_state')
                                node_ok = True
                                if req_state:
                                    n_node = next((n for n in graph['nodes'] if n['id'] == t_id), None)
                                    if n_node and req_state.upper() not in [s.upper() for s in n_node.get('states', [])]:
                                        node_ok = False
                                
                                if node_ok:
                                    effect = ev['effect']
                                    if effect['type'] == 'hide':
                                        dur = effect['duration_steps']
                                        if t_id not in env.active_hidden_nodes:
                                            env.active_hidden_nodes[t_id] = dur
                                            ev['times_triggered'] += 1
                                            logger.info(f"⚡ DYNAMIC EVENT: {trigger['target']}({t_id}) hidden for {dur} steps.")

                    target_match = re.search(r'\(\s*(\d+)\s*\)', action_str)
                    if target_match:
                        target_id = int(target_match.group(1))
                        if target_id in env.active_hidden_nodes:
                            intercepted = True
                            info = {"action_message": "动作失败：目标物品突然消失了，请等待或重新规划。"}

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

                    # Next observation
                    obs = env.get_observations()[0]
                    if isinstance(obs, list) and len(obs) == 1:
                        obs = obs[0]
                        
                    expired = []
                    for k, v in env.active_hidden_nodes.items():
                        if v != float('inf'):
                            env.active_hidden_nodes[k] = v - 1
                            if env.active_hidden_nodes[k] <= 0:
                                expired.append(k)
                    for k in expired:
                        del env.active_hidden_nodes[k]
                        logger.info(f"⚡ DYNAMIC EVENT: object {k} reappeared.")

                    step_count += 1

                # Final verification if loop finished
                if not success and step_count == max_steps:
                    graph = env.get_graph()
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

            print(f"  Result: {'✅ SUCCESS' if success else '❌ FAILED'} — {reason}")
            print(f"  Time: {execution_time:.2f} seconds")

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

    if hasattr(sys.stdout, 'log') and not sys.stdout.log.closed:
        sys.stdout.log.close()
    sys.stdout = original_stdout
    sys.stderr = original_stderr

if __name__ == '__main__':
    main()