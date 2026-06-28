import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'virtualhome'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from agent.core_agent import VirtualHomeAgent

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'agent/configs/scenario_broken_microwave.json'
    with open(config_path) as f:
        config = json.load(f)
        
    env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
    env.reset(environment_id=config['environment_id'])
    env.hidden_broken_ids = set()
    hidden_broken_classes = config.get('hidden_broken_classes', [])
    if hidden_broken_classes:
        _, initial_graph = env.comm.environment_graph()
        if initial_graph:
            for node in initial_graph['nodes']:
                if node['class_name'].lower() in [c.lower() for c in hidden_broken_classes]:
                    env.hidden_broken_ids.add(node['id'])

    # Apply sabotage
    original_get_graph = env.get_graph
    def sabotaged_get_graph(*args, **kwargs):
        graph = original_get_graph(*args, **kwargs)
        sabotage = config.get('sabotage')
        if sabotage:
            targets = sabotage['target_class']
            if isinstance(targets, str): targets = [targets]
            to_remove = sabotage['remove_properties']
            for node in graph['nodes']:
                if node['class_name'].lower() in [t.lower() for t in targets]:
                    node['properties'] = [p for p in node['properties'] if p not in to_remove]
        overrides = config.get('initial_states_override', [])
        for override in overrides:
            t_classes = override.get('target_classes', [])
            rm_states = override.get('remove_states', [])
            add_states = override.get('add_states', [])
            i_filter = override.get('instance_filter')
            
            for t_class in t_classes:
                target_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == t_class.lower()]
                if i_filter:
                    if 'index' in i_filter:
                        idx = i_filter['index']
                        target_nodes = [target_nodes[idx]] if idx < len(target_nodes) else []
                    if 'color' in i_filter:
                        color = i_filter['color'].upper()
                        target_nodes = [n for n in target_nodes if color in [p.upper() for p in n.get('properties', [])] or color in [s.upper() for s in n.get('states', [])]]
                
                for node in target_nodes:
                    if getattr(env, 'custom_states', None) is not None and node['id'] in env.custom_states:
                        continue
                    st = set(node.get('states', []))
                    props = node.get('properties', [])
                    for rs in rm_states: st.discard(rs)
                    for as_ in add_states:
                        if as_ == 'PLUGGED_OUT' and 'HAS_PLUG' not in props: continue
                        if as_ == 'OFF' and 'HAS_SWITCH' not in props: continue
                        st.add(as_)
                    node['states'] = list(st)

        return graph
    env.get_graph = sabotaged_get_graph
    
    # Run physical initial overrides ONCE
    rel_overrides = config.get('initial_relations_override', [])
    for ro in rel_overrides:
        subj_class = ro['subject'].lower()
        rel_type = ro['relation'].upper()
        obj_class = ro['object'].lower()
        count = ro.get('count', 1)
        
        graph = env.get_graph()
        if subj_class == 'character':
            obj_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == obj_class]
            if obj_nodes:
                env.step({0: f'[walk] <{obj_class}> ({obj_nodes[0]["id"]})'})
            continue

        subj_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == subj_class]
        obj_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == obj_class]
        
        if not obj_nodes: continue
        obj_id = obj_nodes[0]['id']

        # HIDE EXTRA INSTANCES PERMANENTLY
        if len(subj_nodes) > count:
            if getattr(env, 'active_hidden_nodes', None) is None:
                env.active_hidden_nodes = {}
            for extra_node in subj_nodes[count:]:
                env.active_hidden_nodes[extra_node['id']] = 999999
            subj_nodes = subj_nodes[:count]

        # Add missing objects via expand_scene
        missing_count = count - len(subj_nodes)
        if missing_count > 0:
            if getattr(env, 'custom_nodes', None) is None:
                env.custom_nodes = []
            if getattr(env, 'custom_edges', None) is None:
                env.custom_edges = []
            max_id = max([n['id'] for n in graph['nodes']]) if graph['nodes'] else 0
            for i in range(missing_count):
                new_id = max_id + 1 + i
                new_node = {
                    'id': new_id,
                    'class_name': subj_class,
                    'category': 'Decor',
                    'states': []
                }
                graph['nodes'].append(new_node)
                env.custom_nodes.append(new_node)
                subj_nodes.append(new_node)
                new_edge = {
                    'from_id': new_id,
                    'relation_type': 'ON',
                    'to_id': obj_id
                }
                graph['edges'].append(new_edge)
                env.custom_edges.append(new_edge)
            
            success, msg = env.comm.expand_scene(graph)
            if not success:
                print(f"Error expanding scene: {msg}")
            
            graph = env.get_graph()
            subj_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == subj_class]

        targets = subj_nodes[:count]
        for s_node in targets:
            s_id = s_node['id']
            existing_edges = [e for e in graph['edges'] if e['from_id'] == s_id and e['relation_type'] == rel_type and e['to_id'] == obj_id]
            if existing_edges:
                continue

            env.step({0: f'[walk] <{subj_class}> ({s_id})'})
            env.step({0: f'[grab] <{subj_class}> ({s_id})'})
            env.step({0: f'[walk] <{obj_class}> ({obj_id})'})
            if rel_type == 'INSIDE':
                env.step({0: f'[open] <{obj_class}> ({obj_id})'})
                env.step({0: f'[putin] <{subj_class}> ({s_id}) <{obj_class}> ({obj_id})'})
                env.step({0: f'[close] <{obj_class}> ({obj_id})'})
            else:
                env.step({0: f'[putback] <{subj_class}> ({s_id}) <{obj_class}> ({obj_id})'})
    
    env.dynamic_events = config.get('dynamic_events', [])
    env.scheduled_rules = config.get('scheduled_rules', [])
    env.current_step = 0
    
    if '--test-init' in sys.argv:
        print(f"\n--- TEST INIT GRAPH for {config_path} ---")
        graph = env.get_graph()
        if 'test_G3' in config_path:
            tvs = [n for n in graph['nodes'] if n['class_name'].lower() == 'television']
            for tv in tvs: print(f"TV {tv['id']}: props={tv.get('properties', [])}, states={tv.get('states', [])}")
        elif 'test_M1' in config_path:
            remotes = [n for n in graph['nodes'] if n['class_name'].lower() == 'remotecontrol']
            if remotes: print(f"Remote {remotes[0]['id']}: edges={[e for e in graph['edges'] if e['from_id'] == remotes[0]['id']]}")
        elif 'test_M2' in config_path:
            cups = [n for n in graph['nodes'] if n['class_name'].lower() == 'cup'][:2]
            for c in cups: print(f"Cup {c['id']}: states={c.get('states', [])}, edges={[e for e in graph['edges'] if e['from_id'] == c['id']]}")
        elif 'test_M3' in config_path:
            apples = [n for n in graph['nodes'] if n['class_name'].lower() == 'apple'][:2]
            for a in apples: print(f"Apple {a['id']}: edges={[e for e in graph['edges'] if e['from_id'] == a['id']]}")
        sys.exit(0)

    scenario_id = os.path.basename(config_path).replace('.json', '')
    agent = VirtualHomeAgent(scenario_id=scenario_id)
    agent.run_episode(env, config)

if __name__ == "__main__":
    main()
