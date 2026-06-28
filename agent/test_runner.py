import os
import json
import glob
import shutil
import time

# Update path to import correctly
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from agent.core_agent import VirtualHomeAgent

def apply_overrides(env, config):
    # Retrieve current graph
    raw_obs = env.get_observations()
    raw_graph = raw_obs[0] if isinstance(raw_obs, list) and raw_obs else None
        
    if not raw_graph:
        print("Error: Could not retrieve graph for overrides.")
        return False

    nodes = raw_graph['nodes']
    
    def find_node(cls_name):
        cls_name = cls_name.lower()
        for n in nodes:
            if n['class_name'].lower() == cls_name:
                return n
        return None

    # Helper to execute action
    def execute(action_str):
        print(f"    Setup Action: {action_str}")
        obs, reward, done, info = env.step({0: action_str})
        if not info.get('action_success', False):
            print(f"      -> FAILED: {info.get('action_message', '')}")
            return False
        return True

    # 1. Apply initial relations
    for rel in config.get('initial_relations_override', []):
        subj = rel.get('subject')
        rel_type = rel.get('relation')
        obj = rel.get('object')
        
        if subj == 'character' and rel_type == 'INSIDE':
            obj_node = find_node(obj)
            if obj_node:
                # Teleport character
                execute(f"[walk] <{obj_node['class_name']}> ({obj_node['id']})")
            continue
            
        if subj and obj and rel_type in ['ON', 'INSIDE']:
            s_node = find_node(subj)
            o_node = find_node(obj)
            if s_node and o_node:
                # To move it: walk to subj, grab, walk to obj, putback/putin
                if not execute(f"[walk] <{s_node['class_name']}> ({s_node['id']})"): continue
                if not execute(f"[grab] <{s_node['class_name']}> ({s_node['id']})"): continue
                if not execute(f"[walk] <{o_node['class_name']}> ({o_node['id']})"): continue
                
                if rel_type == 'ON':
                    execute(f"[putback] <{s_node['class_name']}> ({s_node['id']}) <{o_node['class_name']}> ({o_node['id']})")
                elif rel_type == 'INSIDE':
                    execute(f"[putin] <{s_node['class_name']}> ({s_node['id']}) <{o_node['class_name']}> ({o_node['id']})")

    # 2. Apply initial states
    for state_override in config.get('initial_states_override', []):
        state = state_override.get('state')
        for cls in state_override.get('target_classes', []):
            node = find_node(cls)
            if node:
                if state.upper() == 'OPEN':
                    execute(f"[walk] <{node['class_name']}> ({node['id']})")
                    execute(f"[open] <{node['class_name']}> ({node['id']})")
                elif state.upper() == 'CLOSED':
                    execute(f"[walk] <{node['class_name']}> ({node['id']})")
                    execute(f"[close] <{node['class_name']}> ({node['id']})")
                elif state.upper() == 'ON':
                    execute(f"[walk] <{node['class_name']}> ({node['id']})")
                    execute(f"[switchon] <{node['class_name']}> ({node['id']})")
                elif state.upper() == 'OFF':
                    execute(f"[walk] <{node['class_name']}> ({node['id']})")
                    execute(f"[switchoff] <{node['class_name']}> ({node['id']})")

    return True

def main():
    base_dir = os.path.dirname(__file__)
    configs_dir = os.path.join(base_dir, 'configs')
    results_dir = os.path.join(base_dir, 'results')
    success_dir = os.path.join(results_dir, 'success')
    fail_dir = os.path.join(results_dir, 'fail')
    logs_dir = os.path.join(base_dir, 'logs')
    
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(fail_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Gather all JSON configs
    all_configs = []
    for cls_dir in ['g_class', 'm_class', 'p_class']:
        target_dir = os.path.join(configs_dir, cls_dir)
        if os.path.exists(target_dir):
            for path in glob.glob(os.path.join(target_dir, '*.json')):
                all_configs.append(path)
                
    all_configs = sorted(all_configs)
    
    # Initialize Engine
    exec_path = os.path.abspath(os.path.join(base_dir, '../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'))
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': exec_path, 'no_graphics': True}
    )
    
    summary = {
        "total": len(all_configs),
        "skipped": 0,
        "success": 0,
        "fail": 0,
        "failures": []
    }
    
    for config_path in all_configs:
        scenario_id = os.path.basename(config_path).replace('.json', '')
        
        # Skip if already succeeded
        if os.path.exists(os.path.join(success_dir, scenario_id)):
            print(f"Skipping {scenario_id}, already succeeded.")
            summary["skipped"] += 1
            continue
            
        print(f"\n==========================================")
        print(f"Running Scenario: {scenario_id}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        env_id = config.get('environment_id', 0)
        try:
            env.reset(environment_id=env_id)
        except Exception as e:
            print(f"Failed to reset env to {env_id}: {e}")
            summary["fail"] += 1
            summary["failures"].append({"scenario": scenario_id, "reason": "Engine Reset Failed"})
            continue
            
        print(f"Applying physical overrides...")
        apply_overrides(env, config)
        
        # Run Episode
        agent = VirtualHomeAgent(model_name="gpt-5.4-mini", scenario_id=scenario_id)
        try:
            # We updated run_episode to return (success, reason)
            success, reason = agent.run_episode(env, config)
        except Exception as e:
            success, reason = False, f"Exception: {e}"
            print(f"Exception during run_episode: {e}")
            
        print(f"Result: {'SUCCESS' if success else 'FAILED'} - {reason}")
        
        # Archive results
        dest_parent = success_dir if success else fail_dir
        dest_folder = os.path.join(dest_parent, scenario_id)
        os.makedirs(dest_folder, exist_ok=True)
        
        # Copy config
        shutil.copy(config_path, os.path.join(dest_folder, 'config.json'))
        
        # Move log
        log_file = os.path.join(logs_dir, f"run_{scenario_id}.md")
        if os.path.exists(log_file):
            shutil.copy(log_file, os.path.join(dest_folder, f"run_{scenario_id}.md"))
            
        if success:
            summary["success"] += 1
        else:
            summary["fail"] += 1
            summary["failures"].append({"scenario": scenario_id, "reason": reason})

    # Generate final report
    print("\n\n==========================================")
    print("Testing Complete!")
    print(f"Total: {summary['total']} | Skipped: {summary['skipped']} | Success: {summary['success']} | Fail: {summary['fail']}")
    
    report_path = os.path.join(results_dir, "test_summary_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# VirtualHome E2E Test Summary\n\n")
        f.write(f"- **Total Scenarios**: {summary['total']}\n")
        f.write(f"- **Skipped (Already Success)**: {summary['skipped']}\n")
        f.write(f"- **Newly Succeeded**: {summary['success']}\n")
        f.write(f"- **Failed**: {summary['fail']}\n\n")
        
        if summary["failures"]:
            f.write("## Failure Details\n")
            for fail in summary["failures"]:
                f.write(f"- **{fail['scenario']}**: {fail['reason']}\n")
                
    print(f"Summary report written to {report_path}")

if __name__ == '__main__':
    main()
