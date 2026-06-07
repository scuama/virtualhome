import sys
from vh_runner import run_task
import vh_runner

def patch_and_run():
    original_step = vh_runner.UnityEnvironment.step
    
    def mock_step(self, action_dict):
        print("\n--- VERIFICATION START ---")
        s, current_graph = self.comm.environment_graph()
        
        # Check fridge CAN_OPEN property
        fridge_node = next((n for n in current_graph["nodes"] if n["class_name"] == "fridge"), None)
        if "CAN_OPEN" in fridge_node["properties"]:
            print("[FAIL] Fridge still has CAN_OPEN property")
        else:
            print("[PASS] Fridge CAN_OPEN property was successfully stripped!")
            
        # Check agent room
        agent_node = next((n for n in current_graph["nodes"] if n["class_name"] == "character"), None)
        edges = current_graph["edges"]
        inside_edges = [e for e in edges if e["from_id"] == agent_node["id"] and e["relation_type"] == "INSIDE"]
        if inside_edges:
            room_node = next((n for n in current_graph["nodes"] if n["id"] == inside_edges[0]["to_id"]), None)
            if room_node:
                print(f"Agent is in room: {room_node['class_name']}")
                if room_node['class_name'] == "kitchen":
                    print("[PASS] Agent correctly spawned in 'kitchen'.")
                else:
                    print(f"[FAIL] Agent spawned in {room_node['class_name']}")
        
        print("--- VERIFICATION END ---\n")
        sys.exit(0)
        
    vh_runner.UnityEnvironment.step = mock_step
    run_task("configs/scene_03.json")

if __name__ == "__main__":
    patch_and_run()
