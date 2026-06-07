import sys
import json
sys.path.insert(0, '../')
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
env.comm.reset(0) # 0 is the environment id
s, graph = env.comm.environment_graph()

rooms = [node for node in graph['nodes'] if node['category'] == 'Rooms']
items = [node for node in graph['nodes'] if node['category'] != 'Rooms']

print("Rooms:")
for r in rooms:
    print(f"- {r['class_name']} (ID: {r['id']})")

print("\nItems count by room:")
room_item_counts = {r['class_name']: 0 for r in rooms}
for r in rooms:
    room_items = [e['from_id'] for e in graph['edges'] if e['to_id'] == r['id'] and e['relation_type'] == 'INSIDE']
    print(f"{r['class_name']}: {len(room_items)} direct items")

print("\nAll Items Summary:")
item_counts = {}
for n in items:
    name = n['class_name']
    item_counts[name] = item_counts.get(name, 0) + 1

for k, v in sorted(item_counts.items(), key=lambda x: x[0]):
    print(f"- {k}: {v}")

