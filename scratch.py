import json
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

with open("evaluation/configs/table1/dynamic/T1_DYN_E1_15_medium.json") as f:
    config = json.load(f)

env = UnityEnvironment(
    num_agents=1,
    observation_types=['partial'],
    executable_args={'file_name': None}
)
env.reset(environment_id=config["scene"])
env.expand_scene(config["initial_graph"])

def step(action):
    success, msg = env.step({"action": action})
    print(f"{action}: {success}")

step("[walk] <bedroom> (241)")
step("[walk] <closet> (395)")
step("[walk] <folder> (276)")
step("[grab] <folder> (276)")
step("[walk] <closet> (395)")
step("[putin] <folder> (276) <closet> (395)")

graph = env.get_environment_graph()
for edge in graph['edges']:
    if edge.get('from_id') == 276 or edge.get('to_id') == 276:
        print(edge)
