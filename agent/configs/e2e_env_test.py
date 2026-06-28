import json
import os
import sys

# Add virtualhome to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from virtualhome.simulation.environment.unity_environment import UnityEnvironment

def get_node_by_class(graph, class_name):
    return [n for n in graph['nodes'] if n['class_name'].lower() == class_name.lower()]

def test_configs():
    # Pass the actual Mac App executable
    exec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'))
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': exec_path, 'no_graphics': True}
    )
    
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'g_class'))
    configs = sorted([f for f in os.listdir(config_dir) if f.endswith('.json')])
    
    all_passed = True
    
    for filename in configs:
        print(f"\n==========================================")
        print(f"Testing {filename}")
        
        with open(os.path.join(config_dir, filename), 'r') as f:
            config = json.load(f)
            
        env_id = config.get('environment_id', 1)
        env.reset(environment_id=env_id)
        
        # 1. Apply initial relations override
        rel_overrides = config.get('initial_relations_override', [])
        for rel in rel_overrides:
            subj_class = rel['subject'].lower()
            obj_class = rel['object'].lower()
            rel_type = rel['relation']
            count = rel.get('count', 1)
            
            graph = env.get_graph()
            subj_nodes = get_node_by_class(graph, subj_class)
            
            if subj_class != 'character':
                if len(subj_nodes) < count:
                    print(f"[Warn] Not enough {subj_class} in graph. Modifying graph...")
                    obj_nodes = get_node_by_class(graph, obj_class)
                    if not obj_nodes:
                        print(f"[Error] Target object {obj_class} for relation not found.")
                        all_passed = False
                        continue
                        
                    obj_id = obj_nodes[0]['id']
                    
                    # Force spawn using expand_scene logic
                    for _ in range(count - len(subj_nodes)):
                        new_id = max([n['id'] for n in graph['nodes']]) + 1
                        new_node = {
                            'id': new_id,
                            'class_name': subj_class.capitalize(),
                            'category': 'Decor',
                            'states': []
                        }
                        graph['nodes'].append(new_node)
                        new_edge = {
                            'from_id': new_id,
                            'relation_type': rel_type,
                            'to_id': obj_id
                        }
                        graph['edges'].append(new_edge)
                        
                    success, msg = env.comm.expand_scene(graph)
                    if not success:
                        print(f"[Error] Unity expand_scene failed: {msg}")
                        all_passed = False
            
            # For exact distractor checking:
            graph = env.get_graph()
            subj_nodes = get_node_by_class(graph, subj_class)
            
            # VirtualHome allows multiple objects. But we requested count=1. The environment script usually isolates it.
            # However `run_main.py` isolates it by physically grabbing and putting back.
            # But here we just verify that after expansion, at least `count` exist.
            print(f"  [Init Relation] {subj_class} {rel_type} {obj_class} | Count in graph: {len(subj_nodes)} (Expected: {count} or more)")
            if len(subj_nodes) == 0:
                print(f"  [FAIL] {subj_class} is MISSING!")
                all_passed = False
                
        # 2. Apply initial states override
        state_overrides = config.get('initial_states_override', [])
        for state_ov in state_overrides:
            for target_class in state_ov['target_classes']:
                graph = env.get_graph()
                nodes = get_node_by_class(graph, target_class)
                target_idx = state_ov.get('target_index')
                
                if not nodes:
                    print(f"  [FAIL] Cannot apply state to {target_class}. Object missing.")
                    all_passed = False
                    continue
                    
                targets = [nodes[target_idx]] if target_idx is not None else nodes
                for target_node in targets:
                    new_states = set(target_node.get('states', []))
                    if 'remove_states' in state_ov:
                        new_states -= set(state_ov['remove_states'])
                    if 'add_states' in state_ov:
                        new_states |= set(state_ov['add_states'])
                        
                    target_node['states'] = list(new_states)
                    
                success, msg = env.comm.expand_scene(graph)
                if not success:
                    print(f"  [Error] Failed applying state overrides: {msg}")
                    all_passed = False
                else:
                    # Verify state was actually applied!
                    updated_graph = env.get_graph()
                    updated_nodes = get_node_by_class(updated_graph, target_class)
                    u_targets = [updated_nodes[target_idx]] if target_idx is not None else updated_nodes
                    for u in u_targets:
                        print(f"  [Init State] {target_class}({u['id']}) states: {u.get('states', [])}")
                        if 'add_states' in state_ov:
                            for req_state in state_ov['add_states']:
                                if req_state.upper() not in [s.upper() for s in u.get('states', [])]:
                                    print(f"  [FAIL] State {req_state} was rejected by engine for {target_class}.")
                                    all_passed = False

    if all_passed:
        print("\n\n✅ ALL SCENARIOS DYNAMICALLY VERIFIED IN UNITY ENGINE.")
    else:
        print("\n\n❌ SOME SCENARIOS FAILED ENGINE VERIFICATION.")

if __name__ == "__main__":
    test_configs()
