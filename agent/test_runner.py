import os
import json
import glob
import shutil
import argparse
import traceback

import sys
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
    # IMPORTANT: Must use env.get_graph() (full scene graph), NOT get_raw_graph() (partial/visible).
    # After env.reset() the character spawns at a room entrance; most objects are out of sight
    # in the partial graph, so find_node() would silently return None and skip all overrides.
    raw_graph = env.get_graph()
    if not raw_graph:
        print("  [Override] WARNING: Could not retrieve full scene graph – skipping overrides.")
        return False

    nodes = raw_graph['nodes']

    # Build room membership lookup: node_id -> room_class_name
    room_classes = {'kitchen', 'bedroom', 'livingroom', 'bathroom'}
    node_room = {}
    for e in raw_graph['edges']:
        if e['relation_type'] == 'INSIDE':
            dest = next((n for n in nodes if n['id'] == e['to_id']), None)
            if dest and dest['class_name'].lower() in room_classes:
                node_room[e['from_id']] = dest['class_name'].lower()

    def find_node(cls_name, in_room=None):
        """Find first node matching cls_name, optionally filtered by room."""
        cls_name = cls_name.lower()
        candidates = [n for n in nodes if n['class_name'].lower() == cls_name]
        if in_room:
            in_room_l = in_room.lower()
            room_candidates = [n for n in candidates if node_room.get(n['id']) == in_room_l]
            if room_candidates:
                return room_candidates[0]
        return candidates[0] if candidates else None


    def execute(action_str):
        if debug:
            print(f"    [Setup] {action_str}")
        obs, reward, done, info = env.step({0: action_str})
        success = info.get('action_success', False)
        if not success and debug:
            print(f"      -> FAILED: {info.get('action_message', '')}")
        return success

    # 1. Apply initial_relations_override
    for rel in config.get('initial_relations_override', []):
        subj = rel.get('subject')
        rel_type = rel.get('relation')
        obj = rel.get('object')

        if subj == 'character' and rel_type == 'INSIDE':
            obj_node = find_node(obj)
            if obj_node:
                execute(f"[walk] <{obj_node['class_name']}> ({obj_node['id']})")
            continue

        if subj and obj and rel_type in ['ON', 'INSIDE']:
            s_node = find_node(subj)
            o_node = find_node(obj)
            if s_node and o_node:
                if not execute(f"[walk] <{s_node['class_name']}> ({s_node['id']})"): continue
                if not execute(f"[grab] <{s_node['class_name']}> ({s_node['id']})"): continue
                if not execute(f"[walk] <{o_node['class_name']}> ({o_node['id']})"): continue
                if rel_type == 'ON':
                    execute(f"[putback] <{s_node['class_name']}> ({s_node['id']}) <{o_node['class_name']}> ({o_node['id']})")
                elif rel_type == 'INSIDE':
                    execute(f"[putin] <{s_node['class_name']}> ({s_node['id']}) <{o_node['class_name']}> ({o_node['id']})")

    # 2. Apply initial_states_override
    # States that can be set via physical actions:
    ACTION_STATES = {'OPEN', 'CLOSED', 'ON', 'OFF'}
    # States that CANNOT be set via physical actions → need expand_scene graph injection
    GRAPH_STATES = {'DIRTY', 'CLEAN', 'HOT', 'COLD', 'WARM', 'FULL', 'EMPTY',
                    'BROKEN', 'FILLED', 'PLUGGED_IN', 'PLUGGED_OUT', 'COOKED'}

    # Collect all graph-level state changes first, apply in one expand_scene call
    graph_state_changes = []  # list of (node_id, add_states, remove_states)

    for state_override in config.get('initial_states_override', []):
        states_to_add = state_override.get('add_states', [])
        states_to_remove = state_override.get('remove_states', [])
        if not states_to_add and state_override.get('state'):
            states_to_add = [state_override['state']]

        for cls in state_override.get('target_classes', []):
            in_room = state_override.get('in_room', None)
            node = find_node(cls, in_room=in_room)
            if not node:
                if debug:
                    print(f"    [Setup] WARNING: Class '{cls}' not found in graph{' (room: ' + in_room + ')' if in_room else ''}.")
                continue

            # Split into action-based vs graph-based
            action_adds = [s for s in states_to_add if s.upper() in ACTION_STATES]
            graph_adds  = [s for s in states_to_add if s.upper() in GRAPH_STATES]
            graph_removes = [s for s in states_to_remove if s.upper() in GRAPH_STATES]

            # Physical actions
            for state in action_adds:
                s = state.upper()
                execute(f"[walk] <{node['class_name']}> ({node['id']})")
                if s == 'OPEN':
                    execute(f"[open] <{node['class_name']}> ({node['id']})")
                elif s == 'CLOSED':
                    execute(f"[close] <{node['class_name']}> ({node['id']})")
                elif s == 'ON':
                    execute(f"[switchon] <{node['class_name']}> ({node['id']})")
                elif s == 'OFF':
                    execute(f"[switchoff] <{node['class_name']}> ({node['id']})")

            # Collect graph-level changes
            if graph_adds or graph_removes:
                graph_state_changes.append((node['id'], graph_adds, graph_removes))

    # Apply all graph-level state changes via expand_scene
    if graph_state_changes:
        current_graph = env.get_graph()
        modified = False
        for node_id, adds, removes in graph_state_changes:
            for n in current_graph['nodes']:
                if n['id'] == node_id:
                    current_states = set(n.get('states', []))
                    for r in removes:
                        current_states.discard(r.upper())
                    for a in adds:
                        current_states.add(a.upper())
                    n['states'] = list(current_states)
                    if debug:
                        print(f"    [Setup] Graph-inject states on {n['class_name']}({node_id}): +{adds} -{removes} → {n['states']}")
                    modified = True
                    break
        if modified:
            success, msg = env.comm.expand_scene(current_graph)
            if not success:
                print(f"    [Setup] WARNING: expand_scene failed: {msg}")
            elif debug:
                print(f"    [Setup] expand_scene: OK")
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
                all_configs.append(path)
    all_configs = sorted(all_configs)

    # Filter by --scenario if specified
    if args.scenario:
        all_configs = [p for p in all_configs if os.path.basename(p).replace('.json', '') == args.scenario]
        if not all_configs:
            print(f"ERROR: Scenario '{args.scenario}' not found.")
            return

    # Init engine
    exec_path = os.path.abspath(os.path.join(
        base_dir, '../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'))
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': exec_path, 'no_graphics': True}
    )

    summary = {"total": len(all_configs), "skipped": 0, "success": 0, "fail": 0, "failures": []}

    for config_path in all_configs:
        scenario_id = os.path.basename(config_path).replace('.json', '')

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
        try:
            success, reason = agent.run_episode(env, config)
        except Exception as e:
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
