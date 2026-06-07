import os
import sys
import json
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from virtualhome.simulation.environment.unity_environment import UnityEnvironment
from core_agent import IntentReasoningAgent

def apply_setup_to_graph(graph, setup):
    """在 Python 侧动态应用环境修改，防止 Unity 引擎强制覆盖"""
    if "remove_nodes" in setup:
        remove_classes = setup["remove_nodes"]
        remove_ids = [n["id"] for n in graph["nodes"] if n["class_name"] in remove_classes]
        graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in remove_ids]
        graph["edges"] = [e for e in graph["edges"] if e["from_id"] not in remove_ids and e["to_id"] not in remove_ids]
    
    if "modify_properties" in setup:
        for tgt_class, actions in setup["modify_properties"].items():
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
    return graph

def build_observation_text(partial_graph, agent_id=1):
    visible_nodes = partial_graph['nodes']
    edges = partial_graph.get('edges', [])
    
    id2name = {n['id']: n['class_name'] for n in visible_nodes}
    
    loc_map = {}
    for e in edges:
        if e['relation_type'] in ['ON', 'INSIDE']:
            loc_map[e['from_id']] = (e['relation_type'], e['to_id'])
            
    obs_lines = ["You can see the following objects:"]
    for node in visible_nodes:
        if node['category'] in ['Rooms', 'Doors']:
            continue
            
        nid = node['id']
        name = node['class_name']
        states = node.get('states', [])
        
        state_str = f" States: {states}" if states else ""
        
        loc_str = ""
        if nid in loc_map:
            rel, to_id = loc_map[nid]
            to_name = id2name.get(to_id, f"unknown_{to_id}")
            loc_str = f" [{rel} {to_name} ({to_id})]"
            
        obs_lines.append(f"- {name} ({nid}){state_str}{loc_str}")
        
    return "\n".join(obs_lines)

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
        if 'HAS_PLUG' in node['properties']:
            skills.append(f"[plugin] <{name}> ({nid})")
            skills.append(f"[plugout] <{name}> ({nid})")
        # 很多物品可以被擦拭，不仅限于特定属性，这里统一加上或者判断是否带有 'CLEAN'/'DIRTY' 状态
        if 'DIRTY' in node['states'] or 'CLEAN' in node['states']:
            skills.append(f"[wipe] <{name}> ({nid})")
        
        skills.append(f"[putback] <{name}> ({nid})")
        skills.append(f"[putin] <{name}> ({nid})")
    skills.append("done")
    return list(set(skills))

def run_task(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    instruction = config.get("instruction", "None")
    global_rules = config.get("global_rules", [])
    env_id = config.get("environment_id", 0)
    setup = config.get("setup", {})
    init_room = setup.get("init_room", None)
    init_rooms = [init_room] if init_room else None
    
    env = UnityEnvironment(num_agents=1, executable_args={'file_name': None})
    obs = env.reset(environment_id=env_id, init_rooms=init_rooms)
    
    use_state_machine = config.get("use_state_machine", False)
    
    # 1. 初始化图篡改 (G1, G3, G4, P1, M2)
    if setup:
        s, graph = env.comm.environment_graph()
        
        # [G4] 移除节点
        remove_classes = setup.get("remove_nodes", [])
        if remove_classes:
            remove_ids = [n["id"] for n in graph["nodes"] if n["class_name"] in remove_classes]
            graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in remove_ids]
            graph["edges"] = [e for e in graph["edges"] if e["from_id"] not in remove_ids and e["to_id"] not in remove_ids]
            
        # [G3] 修改属性（物理卡死/锁死）
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
                                
        # [G1] 修改状态
        mod_states = setup.get("modify_states", {})
        for tgt_class, states in mod_states.items():
            for node in graph["nodes"]:
                if node["class_name"] == tgt_class:
                    for st in states:
                        if st not in node["states"]:
                            node["states"].append(st)
                            
        # [M2] 增加混淆节点
        add_nodes = setup.get("add_nodes", [])
        max_id = max([n["id"] for n in graph["nodes"]]) if graph["nodes"] else 1000
        for an in add_nodes:
            max_id += 1
            new_node = {
                "id": max_id,
                "class_name": an["class_name"],
                "category": "Props",
                "properties": ["GRABBABLE"],
                "states": an.get("states", [])
            }
            graph["nodes"].append(new_node)
            if "location" in an:
                loc_node = next((n for n in graph["nodes"] if n["class_name"] == an["location"] or n["id"] == 10000), None) # Fallback if loc not found
                if loc_node:
                    graph["edges"].append({"from_id": max_id, "to_id": loc_node["id"], "relation_type": "ON"})
                    
        # [P1] 资源占用（双手满载）
        inventory = setup.get("agent_inventory", [])
        agent_node = next((n for n in graph["nodes"] if n["class_name"] == "character"), None)
        if agent_node and inventory:
            hands = ["HOLDS_RH", "HOLDS_LH"]
            for i, item_class in enumerate(inventory):
                if i >= 2: break
                item_node = next((n for n in graph["nodes"] if n["class_name"] == item_class and not any(e["to_id"] == n["id"] and "HOLDS" in e["relation_type"] for e in graph["edges"])), None)
                if item_node:
                    graph["edges"] = [e for e in graph["edges"] if e["from_id"] != item_node["id"] or e["relation_type"] not in ["ON", "INSIDE"]]
                    graph["edges"].append({"from_id": agent_node["id"], "to_id": item_node["id"], "relation_type": hands[i]})
        
        print("Restarting environment with modified setup graph...")
        obs = env.reset(environment_graph=graph, environment_id=env_id, init_rooms=init_rooms)
        
        print("[System] Environment modifications dispatched to engine.")

    from datetime import datetime
    run_log_dir = os.path.join("logs", f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_log_dir, exist_ok=True)
    agent = IntentReasoningAgent(episode_id="dataset_run", log_dir=run_log_dir, use_state_machine=use_state_machine)
    
    action_success = True
    dynamic_events = config.get("dynamic_events", [])
    
    def extract_target(act_str):
        act_str = act_str.lower()
        match = re.search(r'\[.*?\]\s*<(.*?)>', act_str)
        if match:
            return match.group(1).strip()
        return ""

    for step_idx in range(50):
        partial_graph = env.get_observation(0, 'partial')
        s, current_graph = env.comm.environment_graph()
        current_graph = apply_setup_to_graph(current_graph, setup)
        
        action_space = env.get_action_space()[0]
        
        obs_text = build_observation_text(current_graph)
        skills = build_skill_set(action_space, current_graph)
        
        available_rooms = [f"[walk] <{r[0].lower()}> ({r[1]})" for r in env.rooms]
        
        img_path = os.path.join(run_log_dir, f"step_{step_idx}_agent_0.png")
        try:
            base_cam = env.num_static_cameras
            cam_ids = [base_cam + 0, base_cam + 1, base_cam + 2]
            s, images = env.comm.camera_image(cam_ids, mode='normal', image_width=400, image_height=300)
            if s and len(images) > 0:
                import numpy as np
                from PIL import Image
                stitched_img = np.concatenate(images, axis=1)
                im = Image.fromarray(stitched_img)
                im.save(img_path)
        except Exception as e:
            print(f"Failed to save image: {e}")
            
        result = agent.step(
            instruction=instruction,
            observation_text=obs_text,
            skill_set=skills,
            available_rooms=available_rooms,
            action_success=action_success,
            step_idx=step_idx,
            img_path=img_path,
            global_rules=global_rules
        )
        
        if result.get("stop_and_save", False):
            print(f"Agent requested communication: {result.get('communication_to_user')}")
            break
            
        action_id = result.get("action_id", 0)
        current_solution_space = agent.solution_space.get_solution_space_dict()
        legal_combinations = current_solution_space.get("legal_combinations", {})
        
        selected_action = legal_combinations.get(action_id)
        if not selected_action:
            selected_action = skills[0] if skills else "done"
            
        if selected_action == "done":
            break
            
        print(f"Step {step_idx}: Agent selected {selected_action}")
        
        # [M3] Watchdog 拦截判败逻辑
        if global_rules:
            action_lower = selected_action.lower()
            s, current_graph = env.comm.environment_graph()
            target = extract_target(action_lower)
            tgt_node = next((n for n in current_graph["nodes"] if n["class_name"] == target), None) if target else None
            
            if "NO_WIPE_WHILE_ON" in global_rules and "[wipe]" in action_lower:
                if tgt_node and "ON" in tgt_node["states"]:
                    print("==================================================")
                    print(f"CRITICAL FAILURE: WATCHDOG TRIGGERED!")
                    print(f"Rule NO_WIPE_WHILE_ON violated. Cannot wipe {target} while it is ON!")
                    print("==================================================")
                    break
        
        obs, reward, done, info = env.step({0: selected_action})
        action_success = info.get('action_success', True)
        if not action_success:
            print(f"Engine rejected action: {info.get('action_message', '')}")
            
        # [M1/M4] 动态事件轮询
        if dynamic_events:
            s, current_graph = env.comm.environment_graph()
            agent_node = next((n for n in current_graph["nodes"] if n["class_name"] == "character"), None)
            if agent_node and "bounding_box" in agent_node:
                for ev in dynamic_events:
                    if ev.get("triggered"): continue
                    target_cls = ev["target_class"]
                    tgt_node = next((n for n in current_graph["nodes"] if n["class_name"] == target_cls), None)
                    if tgt_node and "bounding_box" in tgt_node:
                        p1 = agent_node["bounding_box"]["center"]
                        p2 = tgt_node["bounding_box"]["center"]
                        dist = sum((a-b)**2 for a, b in zip(p1, p2))**0.5
                        if dist < ev.get("trigger_distance", 2.0):
                            ev["triggered"] = True
                            print(f"\n*** DYNAMIC EVENT TRIGGERED: {ev['action']} on {target_cls} ***\n")
                            if ev["action"] == "teleport":
                                dest_cls = ev.get("destination_class", "floor")
                                dest_node = next((n for n in current_graph["nodes"] if n["class_name"] == dest_cls), None)
                                if dest_node:
                                    current_graph["edges"] = [e for e in current_graph["edges"] if not (e["from_id"] == tgt_node["id"] and e["relation_type"] in ["ON", "INSIDE"])]
                                    current_graph["edges"].append({"from_id": tgt_node["id"], "to_id": dest_node["id"], "relation_type": "ON"})
                                    env.comm.expand_scene(current_graph)
                            elif ev["action"] == "vanish_reappear":
                                # 强行移除该物品
                                current_graph["edges"] = [e for e in current_graph["edges"] if not (e["from_id"] == tgt_node["id"] and e["relation_type"] in ["ON", "INSIDE"])]
                                env.comm.expand_scene(current_graph)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    run_task(args.config)

