import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

def probe():
    print("Connecting to Unity...")
    env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
    
    env_info = []
    
    for i in range(15):
        print(f"Probing environment {i}...")
        try:
            # comm.reset returns a boolean for success
            success = env.comm.reset(i)
            if not success:
                print(f"Environment {i} failed to load or does not exist.")
                break
                
            s, graph = env.comm.environment_graph()
            if not s or not graph or 'nodes' not in graph:
                print(f"Environment {i} returned invalid graph.")
                break
                
            nodes = graph['nodes']
            num_nodes = len(nodes)
            
            rooms = [n['class_name'] for n in nodes if n['category'] == 'Rooms']
            
            # Count some key objects
            num_doors = len([n for n in nodes if n['class_name'] == 'door'])
            num_appliances = len([n for n in nodes if n['category'] == 'Appliances'])
            
            info = {
                "env_id": i,
                "num_nodes": num_nodes,
                "rooms": rooms,
                "num_doors": num_doors,
                "num_appliances": num_appliances
            }
            env_info.append(info)
            print(f"Env {i}: {len(rooms)} rooms, {num_nodes} nodes.")
            
        except Exception as e:
            print(f"Exception at env {i}: {e}")
            break

    # output to JSON for easy reading
    with open("env_probe_results.json", "w") as f:
        json.dump(env_info, f, indent=4)
    print("Done probing. Wrote env_probe_results.json")

if __name__ == "__main__":
    probe()
