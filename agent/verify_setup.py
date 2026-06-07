import json
import sys
sys.path.insert(0, '../')
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

def verify(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    env_id = config.get("environment_id", 0)
    setup = config.get("setup", {})
    init_room = setup.get("init_room", None)
    init_rooms = [init_room] if init_room else None

    env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
    obs = env.reset(environment_id=env_id, init_rooms=init_rooms)

    print(f"--- Verifying config: {config_path} ---")
    print(f"Expected Initial Room: {init_room}")

    s, graph = env.comm.environment_graph()

    # Apply setup just like vh_runner.py does
    remove_classes = setup.get("remove_nodes", [])
    if remove_classes:
        remove_ids = [n["id"] for n in graph["nodes"] if n["class_name"] in remove_classes]
        graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in remove_ids]
        graph["edges"] = [e for e in graph["edges"] if e["from_id"] not in remove_ids and e["to_id"] not in remove_ids]

    mod_props = setup.get("modify_properties", {})
    for tgt_class, actions in mod_props.items():
        for node in graph["nodes"]:
            if node["class_name"] == tgt_class:
                if "remove" in actions:
                    for p in actions["remove"]:
                        if p in node["properties"]:
                            node["properties"].remove(p)
                if "add" in actions:
                    for p in actions["add"]:
                        if p not in node["properties"]:
                            node["properties"].append(p)

    env.comm.expand_scene(graph)
    s, new_graph = env.comm.environment_graph()
    
    # Check if fridge CAN_OPEN is stripped
    fridge_node = next((n for n in new_graph["nodes"] if n["class_name"] == "fridge"), None)
    if fridge_node:
        print(f"Fridge properties: {fridge_node['properties']}")
        assert "CAN_OPEN" not in fridge_node["properties"], "Fridge still has CAN_OPEN!"
        print("[SUCCESS] Fridge CAN_OPEN property successfully stripped (G3 verified).")
    
    # Check agent's room
    agent_node = next((n for n in new_graph["nodes"] if n["class_name"] == "character"), None)
    if agent_node:
        # find what room it is in
        edges = new_graph["edges"]
        inside_edges = [e for e in edges if e["from_id"] == agent_node["id"] and e["relation_type"] == "INSIDE"]
        if inside_edges:
            room_node = next((n for n in new_graph["nodes"] if n["id"] == inside_edges[0]["to_id"]), None)
            if room_node:
                print(f"Agent is in room: {room_node['class_name']}")
                if init_room:
                    assert room_node['class_name'] == init_room, f"Agent is in {room_node['class_name']}, but expected {init_room}"
                print("[SUCCESS] Agent spawned in the correct room.")

if __name__ == "__main__":
    verify("configs/scene_03.json")
