import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from core_agent import IntentReasoningAgent
from PIL import Image

def build_observation_text(partial_graph, agent_id=1):
    visible_nodes = partial_graph['nodes']
    nodes_str = []
    for node in visible_nodes:
        if node['category'] in ['Rooms', 'Doors']:
            continue
        nodes_str.append(node['class_name'])
    return "You can see: " + ", ".join(set(nodes_str)) + "."

def build_skill_set(action_space_ids, partial_graph):
    id2node = {node['id']: node for node in partial_graph['nodes']}
    skills = []
    for nid in action_space_ids:
        if nid not in id2node: continue
        node = id2node[nid]
        name = node['class_name']
        skills.append(f"[Walk] <{name}> ({nid})")
        if 'GRABBABLE' in node['properties']:
            skills.append(f"[Grab] <{name}> ({nid})")
        if 'CAN_OPEN' in node['properties']:
            skills.append(f"[Open] <{name}> ({nid})")
            skills.append(f"[Close] <{name}> ({nid})")
        skills.append(f"[PutBack] <{name}> ({nid})")
        skills.append(f"[PutIn] <{name}> ({nid})")
    skills.append("done")
    return list(set(skills))

def run_task(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    instruction = config.get("instruction", "None")
    
    # file_name=None 表示直接连接已运行的 Unity 进程，不重新启动
    env = UnityEnvironment(num_agents=1, observation_types=['partial'], executable_args={'file_name': None})
    obs = env.reset()
    
    modifiers = config.get("init_graph_modifiers", [])
    if modifiers:
        s, graph = env.comm.environment_graph()
        for mod in modifiers:
            target = mod["target"]
            prop = mod["property"]
            for node in graph["nodes"]:
                if node["class_name"] == target:
                    if prop not in node["properties"]:
                        node["properties"].append(prop)
        obs = env.reset(environment_graph=graph)

    agent = IntentReasoningAgent(episode_id="impossible_01", log_dir="./logs")
    
    for step_idx in range(50):
        partial_graph = env.get_observation(0, 'partial')
        action_space = env.get_action_space()[0]
        
        obs_text = build_observation_text(partial_graph)
        skills = build_skill_set(action_space, partial_graph)
        
        env.observation_types[0] = 'image'
        img_np = env.get_observation(0, 'image')
        env.observation_types[0] = 'partial'
        
        os.makedirs("logs", exist_ok=True)
        img_path = f"logs/step_{step_idx}_agent_0.png"
        
        if img_np is not None:
            im = Image.fromarray(img_np)
            im.save(img_path)
            
        result = agent.step(
            instruction=instruction,
            observation_text=obs_text,
            skill_set=skills,
            step_idx=step_idx,
            img_path=img_path
        )
        
        if result.get("stop_and_save", False):
            print(f"Agent requested communication: {result.get('communication_to_user')}")
            break
            
        action_id = result.get("action_id", 0)
        if action_id >= len(skills):
            action_id = 0
        selected_action = skills[action_id]
        if selected_action == "done":
            break
            
        print(f"Step {step_idx}: Agent selected {selected_action}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    run_task(args.config)
