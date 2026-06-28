import os
import json
import glob
import shutil
import argparse
import traceback

import sys
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from agent.core_agent import VirtualHomeAgent


def get_raw_graph(env):
    """get_observations() returns dict keyed by agent_id (int). Agent 0's graph is the scene graph.
    NOTE: this is a PARTIAL (vision-limited) graph. Only use for perception simulation.
    For scene setup, always use env.get_graph() which returns the FULL scene graph."""
    obs_dict = env.get_observations()
    return obs_dict.get(0)


def apply_overrides(env, config, debug=False):
    """
    Applies scenario overrides using monkey-patching for states and physical actions for relations.
    """
    def _install_state_patch(env, overrides, debug):
        original = env.get_graph
        def patched(*args, **kwargs):
            graph = original(*args, **kwargs)
            custom = getattr(env, 'custom_states', {}) or {}
            for ov in overrides:
                rm, add = ov.get('remove_states', []), ov.get('add_states', [])
                i_filter = ov.get('instance_filter')
                in_room  = ov.get('in_room')
                for cls in ov.get('target_classes', []):
                    candidates = [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]
                    if in_room:
                        room_ids  = {n['id'] for n in graph['nodes'] if n['class_name'].lower() == in_room.lower()}
                        inside_ids = {e['from_id'] for e in graph['edges'] if e['relation_type']=='INSIDE' and e['to_id'] in room_ids}
                        candidates = [n for n in candidates if n['id'] in inside_ids]
                    if i_filter and 'index' in i_filter:
                        idx = i_filter['index']
                        candidates = [candidates[idx]] if idx < len(candidates) else []
                    
                    for node in candidates:
                        if node['id'] in custom: continue  # 真实动作优先
                        st = set(node.get('states', []))
                        props = node.get('properties', [])
                        for s in rm: st.discard(s)
                        for s in add:
                            if s == 'PLUGGED_OUT' and 'HAS_PLUG' not in props: continue
                            if s == 'OFF' and 'HAS_SWITCH' not in props: continue
                            st.add(s)
                        node['states'] = list(st)
                        if debug:
                            print(f"    [Setup] Patched state on {node['class_name']}({node['id']}): {node['states']}")
            return graph
        env.get_graph = patched
        if debug:
            print("    [Setup] Installed get_graph monkey-patch for state overrides.")

    def _find_node(graph, cls, in_room=None):
        candidates = [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]
        if in_room:
            room_ids = {n['id'] for n in graph['nodes'] if n['class_name'].lower() == in_room.lower()}
            inside_ids = {e['from_id'] for e in graph['edges'] if e['relation_type']=='INSIDE' and e['to_id'] in room_ids}
            candidates = [n for n in candidates if n['id'] in inside_ids]
        return candidates[0] if candidates else None

    def _find_all(graph, cls):
        return [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]
        
    def _hide_extra_nodes(env, nodes_to_hide):
        if not hasattr(env, 'active_hidden_nodes'):
            env.active_hidden_nodes = {}
        for n in nodes_to_hide:
            env.active_hidden_nodes[n['id']] = 999999

    def _get_scene_without_chars(env):
        _, raw = env.comm.environment_graph()
        char_ids = {n['id'] for n in raw['nodes'] if n['class_name'].lower() == 'character'}
        return {
            'nodes': [n for n in raw['nodes'] if n['id'] not in char_ids],
            'edges': [e for e in raw['edges'] if e['from_id'] not in char_ids and e['to_id'] not in char_ids]
        }

    def _add_virtual_nodes(scene_graph, subj_class, obj_id, count):
        max_id = max(n['id'] for n in scene_graph['nodes']) if scene_graph['nodes'] else 0
        for i in range(count):
            new_id = max_id + 1 + i
            scene_graph['nodes'].append({'id': new_id, 'class_name': subj_class, 'category': 'Decor', 'states': []})
            scene_graph['edges'].append({'from_id': new_id, 'relation_type': 'ON', 'to_id': obj_id})

    def _readd_characters(env):
        for i in range(env.num_agents):
            if hasattr(env, 'agent_info') and i in env.agent_info:
                env.comm.add_character(env.agent_info[i])
            else:
                env.comm.add_character()
        env.changed_graph = True

    def _already_has_relation(graph, s_node, rel, obj_node):
        return any(e for e in graph['edges'] if e['from_id'] == s_node['id'] and e['relation_type'] == rel and e['to_id'] == obj_node['id'])

    def execute(action_str):
        print(f"    [Setup] {action_str}")
        obs, reward, done, info = env.step({0: action_str})
        success = info.get('action_success', False)
        if not success:
            print(f"      -> FAILED: {info.get('action_message', '')}")
        return success

    # 1. 状态覆盖
    state_overrides = config.get('initial_states_override', [])
    if state_overrides:
        _install_state_patch(env, state_overrides, debug)

    # 2. 关系覆盖 (位置)
    graph = env.get_graph()
    for ro in config.get('initial_relations_override', []):
        subj   = ro['subject'].lower()
        rel    = ro.get('relation', 'ON').upper()
        obj    = ro['object'].lower()
        count  = ro.get('count', 1)
        in_room = ro.get('in_room')

        # 角色初始位置特殊处理
        if subj == 'character':
            obj_node = _find_node(graph, obj)
            if obj_node:
                execute(f'[walk] <{obj}> ({obj_node["id"]})')
            graph = env.get_graph()
            continue

        subj_nodes = _find_all(graph, subj)
        obj_node   = _find_node(graph, obj, in_room)
        if not obj_node: continue

        # 隐藏多余的对象实例
        if len(subj_nodes) > count:
            _hide_extra_nodes(env, subj_nodes[count:])
            subj_nodes = subj_nodes[:count]

        # 若对象不足，用 expand_scene 补充
        if len(subj_nodes) < count:
            missing = count - len(subj_nodes)
            scene_graph = _get_scene_without_chars(env)
            _add_virtual_nodes(scene_graph, subj, obj_node['id'], missing)
            env.comm.expand_scene(scene_graph)
            _readd_characters(env)          
            graph = env.get_graph()
            subj_nodes = _find_all(graph, subj)

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



def analyze_failure(scenario_id, config, reason, log_file_path, debug=False):
    """Print a structured debug analysis of a failed scenario."""
    print(f"\n{'='*60}")
    print(f"  🔍 DEBUG ANALYSIS: {scenario_id}")
    print(f"{'='*60}")
    print(f"  Goal: {config.get('goal_instruction', 'N/A')}")
    print(f"  Environment ID: {config.get('environment_id', 'N/A')}")
    print(f"  Failure Reason: {reason}")

    sc = config.get('success_condition', {})
    print(f"\n  Success Condition:")
    print(f"    check_type: {sc.get('check_type', 'N/A')}")
    for k, v in sc.items():
        if k != 'check_type':
            print(f"    {k}: {v}")

    if config.get('initial_relations_override'):
        print(f"\n  Initial Relations Override:")
        for r in config['initial_relations_override']:
            print(f"    {r}")

    if config.get('initial_states_override'):
        print(f"\n  Initial States Override:")
        for s in config['initial_states_override']:
            print(f"    {s}")

    if log_file_path and os.path.exists(log_file_path):
        print(f"\n  Run Log: {log_file_path}")
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Show last 20 lines of log
        lines = content.strip().split('\n')
        print(f"  --- Last {min(20, len(lines))} lines of run log ---")
        for line in lines[-20:]:
            print(f"  | {line}")

    # Classify root cause
    if "'relation'" in reason or "KeyError" in reason:
        print(f"\n  ⚠️  ROOT CAUSE: success_condition 关系检查时发生 KeyError。")
        print(f"     检查 subject/relation/object 字段是否正确填写。")
    elif "Max steps" in reason:
        print(f"\n  ⚠️  ROOT CAUSE: Agent 在 {config.get('max_steps', 15)} 步内未完成目标。")
        print(f"     可能原因：目标物体超出感知范围 / 动作序列过长 / 物品未正确初始化。")
    elif "help" in reason.lower() or "success condition was not met" in reason.lower():
        print(f"\n  ⚠️  ROOT CAUSE: Agent 触发了 [ask]，但 success_condition 未通过。")
        print(f"     检查：1) TV/condition object 的初始状态是否已正确设置")
        print(f"           2) success_condition.check_type 是否匹配场景意图")
    elif "Constraint" in reason or "Violation" in reason:
        print(f"\n  ⚠️  ROOT CAUSE: Agent 触发了禁制条件 (failure_condition)。")
    elif "Exception" in reason:
        print(f"\n  ⚠️  ROOT CAUSE: 运行时异常。检查配置格式和环境物体是否存在。")
    print(f"{'='*60}\n")



def main():
    parser = argparse.ArgumentParser(description='VirtualHome E2E Test Runner')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode: stop and analyze on each failure')
    parser.add_argument('--scenario', type=str, default=None,
                        help='Run a single scenario by ID (e.g. G1_01)')
    parser.add_argument('--category', type=str, default=None,
                        help='Run a specific category of scenarios (e.g. G2)')
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    configs_dir = os.path.join(base_dir, 'configs')
    results_dir = os.path.join(base_dir, 'results')
    success_dir = os.path.join(results_dir, 'success')
    fail_dir = os.path.join(results_dir, 'fail')
    logs_dir = os.path.join(base_dir, 'logs')

    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # Gather configs
    all_configs = []
    for cls_dir in ['g_class', 'm_class', 'p_class']:
        target_dir = os.path.join(configs_dir, cls_dir)
        if os.path.exists(target_dir):
            for path in glob.glob(os.path.join(target_dir, '*.json')):
                scenario_id = os.path.splitext(os.path.basename(path))[0]
                if args.scenario and scenario_id != args.scenario:
                    continue
                if args.category and not scenario_id.startswith(args.category):
                    continue
                all_configs.append((scenario_id, path))
    all_configs = sorted(all_configs)

    # Init engine
    exec_path = os.path.abspath(os.path.join(
        base_dir, '../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'))
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': None}
    )

    summary = {"total": len(all_configs), "skipped": 0, "success": 0, "fail": 0, "failures": []}

    for scenario_id, config_path in all_configs:
        # Skip already-succeeded
        if os.path.exists(os.path.join(success_dir, scenario_id)):
            print(f"[SKIP] {scenario_id} — already succeeded.")
            summary["skipped"] += 1
            continue

        print(f"\n==========================================")
        print(f"[RUN] {scenario_id}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        env_id = config.get('environment_id', 0)
        try:
            env.reset(environment_id=env_id)
        except Exception as e:
            reason = f"Engine Reset Failed: {e}"
            print(f"  {reason}")
            summary["fail"] += 1
            summary["failures"].append({"scenario": scenario_id, "reason": reason})
            if args.debug:
                analyze_failure(scenario_id, config, reason, None, debug=True)
                input("  [DEBUG] Press Enter to continue to next scenario...")
            continue

        apply_overrides(env, config, debug=args.debug)

        agent = VirtualHomeAgent(model_name="gpt-5.4-mini", scenario_id=scenario_id)

        class TimeoutException(Exception):
            pass

        def timeout_handler(signum, frame):
            raise TimeoutException("Episode timed out after 5 minutes")

        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(300) # 5 minutes
            success, reason = agent.run_episode(env, config)
            signal.alarm(0)
        except TimeoutException as e:
            success = False
            reason = str(e)
            print(f"  [TIMEOUT] Scenario {scenario_id} exceeded 5 minutes.")
        except Exception as e:
            signal.alarm(0)
            success = False
            reason = f"Exception: {e}"
            if args.debug:
                traceback.print_exc()

        print(f"  Result: {'✅ SUCCESS' if success else '❌ FAILED'} — {reason}")

        # Archive
        dest_parent = success_dir if success else fail_dir
        dest_folder = os.path.join(dest_parent, scenario_id)
        os.makedirs(dest_folder, exist_ok=True)
        shutil.copy(config_path, os.path.join(dest_folder, 'config.json'))
        log_file = os.path.join(logs_dir, f"run_{scenario_id}.md")
        if os.path.exists(log_file):
            shutil.copy(log_file, os.path.join(dest_folder, f"run_{scenario_id}.md"))

        if success:
            summary["success"] += 1
        else:
            summary["fail"] += 1
            summary["failures"].append({"scenario": scenario_id, "reason": reason})
            if args.debug:
                analyze_failure(scenario_id, config, reason, log_file, debug=True)
                try:
                    input("  [DEBUG] Press Enter to continue to next scenario, or Ctrl+C to abort...")
                except KeyboardInterrupt:
                    print("\n  [DEBUG] Aborted by user.")
                    break

    # Final report
    print(f"\n\n==========================================")
    print(f"Testing Complete!")
    print(f"Total: {summary['total']} | Skipped: {summary['skipped']} | ✅ Success: {summary['success']} | ❌ Fail: {summary['fail']}")

    report_path = os.path.join(results_dir, "test_summary_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# VirtualHome E2E Test Summary\n\n")
        f.write(f"- **Total Scenarios**: {summary['total']}\n")
        f.write(f"- **Skipped (Already Success)**: {summary['skipped']}\n")
        f.write(f"- **Newly Succeeded**: {summary['success']}\n")
        f.write(f"- **Failed**: {summary['fail']}\n\n")
        if summary["failures"]:
            f.write("## Failure Details\n\n")
            f.write("| Scenario | Reason |\n|---|---|\n")
            for fail in summary["failures"]:
                f.write(f"| **{fail['scenario']}** | {fail['reason']} |\n")

    print(f"Summary report: {report_path}")


if __name__ == '__main__':
    main()
