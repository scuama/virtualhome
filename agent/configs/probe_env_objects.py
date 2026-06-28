import os
import json
import sys

# ensure we import from the correct VirtualHome package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

def probe_environments():
    exec_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '../../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'
    ))
    
    print(f"Using executable: {exec_path}")
    
    env = UnityEnvironment(
        num_agents=1,
        observation_types=['partial'],
        executable_args={'file_name': exec_path, 'no_graphics': True}
    )
    
    env_data = {}
    
    for env_id in [0, 1, 2, 3, 4, 6]:
        print(f"Probing environment {env_id}...")
        try:
            env.reset(environment_id=env_id)
            graph = env.get_graph()
            
            class_counts = {}
            for node in graph['nodes']:
                cname = node['class_name'].lower()
                class_counts[cname] = class_counts.get(cname, 0) + 1
                
            env_data[env_id] = class_counts
            print(f"  Found {len(class_counts)} unique classes in env {env_id}.")
        except Exception as e:
            print(f"  Error probing env {env_id}: {e}")
            env_data[env_id] = {"error": str(e)}

        out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'env_objects.json'))
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(env_data, f, indent=4, ensure_ascii=False)
        
    print(f"Dumped object counts to {out_file}")

if __name__ == '__main__':
    probe_environments()
