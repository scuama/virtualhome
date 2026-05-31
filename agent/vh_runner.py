import os
import sys
import json
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from core_agent import IntentReasoningAgent

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
        name = node['class_name'].lower()
        # USE LOWERCASE actions as VirtualHome unity engine expects
        skills.append(f"[walk] <{name}> ({nid})")
        if 'GRABBABLE' in node['properties']:
            skills.append(f"[grab] <{name}> ({nid})")
        if 'CAN_OPEN' in node['properties']:
            skills.append(f"[open] <{name}> ({nid})")
            skills.append(f"[close] <{name}> ({nid})")
        if 'HAS_SWITCH' in node['properties']:
            skills.append(f"[switchon] <{name}> ({nid})")
            skills.append(f"[switchoff] <{name}> ({nid})")
        skills.append(f"[putback] <{name}> ({nid})")
        skills.append(f"[putin] <{name}> ({nid})")
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
            action = mod.get("action", "add_property")
            for node in graph["nodes"]:
                if node["class_name"] == target:
                    if action == "add_property":
                        if prop not in node["properties"]:
                            node["properties"].append(prop)
                    elif action == "remove_property":
                        if prop in node["properties"]:
                            node["properties"].remove(prop)
        obs = env.reset(environment_graph=graph)

    from datetime import datetime
    run_log_dir = os.path.join("logs", f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_log_dir, exist_ok=True)
    agent = IntentReasoningAgent(episode_id="impossible_01", log_dir=run_log_dir)
    
    action_success = True
    
    for step_idx in range(50):
        partial_graph = env.get_observation(0, 'partial')
        action_space = env.get_action_space()[0]
        
        obs_text = build_observation_text(partial_graph)
        skills = build_skill_set(action_space, partial_graph)
        
        # 获取所有的房间信息
        available_rooms = [f"[walk] <{r[0].lower()}> ({r[1]})" for r in env.rooms]
        
        img_path = os.path.join(run_log_dir, f"step_{step_idx}_agent_0.png")
        try:
            agent_id = 0
            base_cam = env.num_static_cameras + agent_id * env.num_camera_per_agent
            cam_ids = [base_cam + 0, base_cam + 1, base_cam + 2]
            s, images = env.comm.camera_image(cam_ids, mode='normal', image_width=400, image_height=300)
            if s and len(images) > 0:
                import numpy as np
                from PIL import Image
                stitched_img = np.concatenate(images, axis=1)
                im = Image.fromarray(stitched_img)
                im.save(img_path)
        except Exception as e:
            print(f"Failed to save stitched image: {e}")
            
        result = agent.step(
            instruction=instruction,
            observation_text=obs_text,
            skill_set=skills,
            available_rooms=available_rooms,
            action_success=action_success,
            step_idx=step_idx,
            img_path=img_path
        )
        
        if result.get("stop_and_save", False):
            print(f"Agent requested communication: {result.get('communication_to_user')}")
            break
            
        action_id = result.get("action_id", 0)
        
        # 修正: 从 agent 的 solution_space 的 legal_combinations 取字典，不要当下标
        current_solution_space = agent.solution_space.get_solution_space_dict()
        legal_combinations = current_solution_space.get("legal_combinations", {})
        
        selected_action = legal_combinations.get(action_id)
        if not selected_action:
            print(f"Warning: action_id {action_id} not found in legal_combinations! Falling back to 0")
            selected_action = skills[0] if skills else "done"
            
        if selected_action == "done":
            break
            
        print(f"Step {step_idx}: Agent selected {selected_action}")
        
        # 真正执行物理动作
        action_dict = {0: selected_action}
        obs, reward, done, info = env.step(action_dict)
        
        # 解析真实物理引擎成功标志
        action_success = info.get('action_success', True)
        if not action_success:
            print(f"Engine rejected action: {info.get('action_message', '')}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    run_task(args.config)
