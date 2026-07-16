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
    parser.add_argument('target', type=str, nargs='?', default='',
                        help='Target scenario ID or prefix (e.g. P3 or P3_12). Leave empty for all.')
    # ===================== 新增 --method 参数 =====================
    parser.add_argument(
        '--method',
        type=str,
        default='robostate',
        choices=list(AGENT_REGISTRY.keys()),
        help='Method to evaluate: ' + ', '.join(AGENT_REGISTRY.keys())
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
    # ============================================================
    parser.add_argument('--daemon', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    logs_dir = os.path.join(base_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(
        logs_dir,
        f"test_runner_{args.method}.log"
    )

    if not args.daemon:
        import subprocess
        cmd = [sys.executable, __file__]
        if args.target:
            cmd.append(args.target)
        cmd.append("--daemon")
        # 传递 method 参数到子进程
        cmd.append("--method")
        cmd.append(args.method)
        
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        print(f"[INFO] Task started in background.")
        print(f"[INFO] Monitor logs via: tail -f {log_path}")
        sys.exit(0)

    sys.stdout = Logger(log_path)
    sys.stderr = sys.stdout

    configs_dir = os.path.join(base_dir, 'configs')
    results_dir = os.path.join(
        base_dir,
        'results',
        args.method
    )
    success_dir = os.path.join(results_dir, 'success')
    fail_dir = os.path.join(results_dir, 'fail')
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)
    
    # Gather configs
    all_configs = []
    for cls_dir in ['g_class', 'm_class', 'p_class','ExRAP']:
        target_dir = os.path.join(configs_dir, cls_dir)
        if os.path.exists(target_dir):
            for path in glob.glob(os.path.join(target_dir, '*.json')):
                scenario_id = os.path.splitext(os.path.basename(path))[0]
                if args.target and not scenario_id.startswith(args.target):
                    continue
                all_configs.append((scenario_id, path))
    all_configs = sorted(all_configs)

    # Init engine
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': None}
    )

    summary = {
        "method": args.method,
        "model": args.model,
        "total": len(all_configs),
        "skipped": 0,
        "success": 0,
        "fail": 0,
        "failures": []
    }

    print(
        f"[INFO] Method={args.method} | "
        f"Model={args.model} | "
        f"Timeout={args.timeout}s"
    )

    for scenario_id, config_path in all_configs:
        if os.path.exists(os.path.join(success_dir, scenario_id)):
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
        agent_cls = AGENT_REGISTRY[args.method]
        agent = agent_cls(
            model_name=args.model,
            scenario_id=scenario_id
        )
        # ================================================================

        # Prevent a failed run from copying a stale log produced by
        # another method or an earlier execution of the same scenario.
        scenario_log_file = os.path.join(
            logs_dir,
            f"run_{scenario_id}.md"
        )
        if os.path.exists(scenario_log_file):
            os.remove(scenario_log_file)

        class TimeoutException(Exception):
            pass

        def timeout_handler(signum, frame):
            raise TimeoutException(
                f"Episode timed out after {args.timeout} seconds"
            )

        import time
        start_time = time.time()

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(args.timeout)
            success, reason = agent.run_episode(env, config)
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
        
        config['evaluation_method'] = args.method
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

if __name__ == '__main__':
    main()