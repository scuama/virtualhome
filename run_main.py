import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'virtualhome'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from agent.core_agent import VirtualHomeAgent

def main():
    with open('agent/configs/scenario_broken_microwave.json') as f:
        config = json.load(f)
        
    env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
    env.reset(environment_id=config['environment_id'])
    
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
            for node in graph['nodes']:
                if node['class_name'].lower() in t_classes:
                    st = set(node.get('states', []))
                    props = node.get('properties', [])
                    for rs in rm_states: st.discard(rs)
                    for as_ in add_states:
                        # Only add PLUGGED_OUT if it actually supports plugs
                        if as_ == 'PLUGGED_OUT' and 'HAS_PLUG' not in props:
                            continue
                        # Only add OFF if it actually supports switches
                        if as_ == 'OFF' and 'HAS_SWITCH' not in props:
                            continue
                        st.add(as_)
                    node['states'] = list(st)
        return graph
    env.get_graph = sabotaged_get_graph

    agent = VirtualHomeAgent()
    agent.run_episode(env, config)

if __name__ == "__main__":
    main()
