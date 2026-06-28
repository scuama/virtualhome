import json
import os
import datetime
from .llm_client import LLMClient
from .goal_reasoner import GoalReasoner
from .sdg_planner import SDGPlanner
from .perception_filter import PerceptionFilter
from .llm_executor import LLMExecutor

class AgentLogger:
    def __init__(self, log_mode="text", scenario_id=""):
        self.log_mode = log_mode
        os.makedirs("agent/logs", exist_ok=True)
        prefix = f"run_{scenario_id}" if scenario_id else "run_log"
        self.log_file = f"agent/logs/{prefix}.md"
        
        # Initialize markdown file
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("# 🚀 VirtualHome Agent Episode Log\n\n")
            
    def info(self, msg):
        print(f"INFO: {msg}")
        
    def log_info(self, msg):
        self.info(msg)
        
    def error(self, msg):
        print(f"ERROR: {msg}")
        
    def log_error(self, msg):
        self.error(msg)
        
    def log_module_output(self, module_name, step, output_data):
        with open(self.log_file, "a", encoding="utf-8") as f:
            if isinstance(output_data, str):
                formatted_data = output_data
            else:
                formatted_data = json.dumps(output_data, ensure_ascii=False, indent=2)
            f.write(f"\n### [{module_name}] Output\n```json\n{formatted_data}\n```\n")
        
    def write_step(self, step, action, sdg, observed_items, current_node_focus=None, satisfied_nodes=None):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"## Step {step}\n")
            f.write(f"- **Action**: `{action}`\n")
            
            # Always output the Mermaid graph for SDG
            f.write(f"- **SDG Status**:\n")
            if sdg:
                f.write(f"```mermaid\n{self._generate_mermaid(sdg, current_node_focus, satisfied_nodes)}\n```\n")
            else:
                f.write("No SDG active.\n")
                
            f.write(f"- **Observed Items ({len(observed_items)})**: {', '.join(observed_items[:15])}{'...' if len(observed_items) > 15 else ''}\n")
            f.write("\n")

    def _generate_mermaid(self, sdg, current_node_focus=None, satisfied_nodes=None):
        if satisfied_nodes is None:
            satisfied_nodes = []
            
        lines = ["graph TD"]
        nodes = sdg.get("nodes", [])
        edges = sdg.get("edges", [])

        for node in nodes:
            nid = node["id"]
            if node["type"] == "State":
                label = f"{node['object']}<br>({node['value']})"
            elif node["type"] == "Relation":
                label = f"{node.get('object', '')}<br>{node.get('relation', node.get('state', node.get('value', '')))}<br>{node.get('target', '')}"
            else:
                label = f"{node['object']}"
            
            # Escape quotes in label to avoid syntax errors
            label = label.replace('"', '\\"')
            
            style_str = ""
            if current_node_focus and nid == current_node_focus:
                style_str = f"\n    style {nid} fill:#ff9,stroke:#333,stroke-width:4px"
            elif nid in satisfied_nodes:
                style_str = f"\n    style {nid} fill:#9f9,stroke:#333,stroke-width:2px"
                
            lines.append(f'    {nid}["{label}"]{style_str}')

        for edge in edges:
            reason = edge.get('reason', '')
            reason = reason.replace('"', '\\"')
            lines.append(f'    {edge["from"]} -->|"{reason}"| {edge["to"]}')
        return "\n".join(lines)


class VirtualHomeAgent:
    def __init__(self, model_name="gpt-5.4-mini", scenario_id=""):
        self.llm = LLMClient(model_name=model_name)
        self.action_history = []
        self.current_sdg = None
        self.goal_reasoner = None
        self.sdg_planner = None
        self.perception_filter = None
        self.llm_executor = None
        self.scenario_id = scenario_id
        self.logger = AgentLogger(log_mode="markdown", scenario_id=scenario_id)

    def _get_observed_items(self, graph, current_step=0):
        active_rules = []
        for r in getattr(self, 'env_rules', []):
            if r['start_step'] <= current_step <= r['end_step']:
                rule_text = r['rule_text']
                if r['end_step'] < 999:
                    rule_text += f" (Note: This rule is temporary and will expire at step {r['end_step']+1}. If this rule blocks your required preconditions, you MUST output [wait] until it expires instead of giving up.)"
                active_rules.append(rule_text)
        items = []
        for n in graph.get('nodes', []):
            states = n.get('states', [])
            state_str = f" [{','.join(states)}]" if states else ""
            items.append(f"{n['class_name']}({n['id']}){state_str}")
        return items

    def _check_success(self, graph, condition, action_history=None):
        if not condition: return False
        
        mode = condition.get('mode', 'SINGLE')
        conditions = condition.get('conditions', [condition]) if mode == 'AND' else [condition]
        
        for cond in conditions:
            check_type = cond.get('check_type', 'state')
            
            if check_type == 'state' or check_type == 'physical_state':
                # Support both 'require_state' (str) and 'require_states' (list)
                req_states = cond.get('require_states', [])
                if not req_states and cond.get('require_state'):
                    req_states = [cond['require_state']]
                quantifier = cond.get('quantifier', 'any')
                target_class = cond['target_class']
                instance_filter = cond.get('instance_filter', {})
                
                target_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == target_class.lower()]
                if 'color' in instance_filter:
                    color = instance_filter['color'].upper()
                    target_nodes = [n for n in target_nodes if color in [p.upper() for p in n.get('properties', [])] or color in [s.upper() for s in n.get('states', [])]]
                if not target_nodes: return False
                
                for req_state in req_states:
                    hot_count = sum(1 for n in target_nodes if req_state.upper() in [s.upper() for s in n.get('states', [])])
                    if quantifier == 'any' and hot_count == 0: return False
                    if quantifier == 'all' and hot_count != len(target_nodes): return False
                
            elif check_type == 'relation':
                # Support both flat fields and require_relation: [relation, subject, object] array
                req_rel_arr = cond.get('require_relation')
                if req_rel_arr and isinstance(req_rel_arr, list) and len(req_rel_arr) == 3:
                    relation, target_class, dest_class = req_rel_arr
                else:
                    target_class = cond.get('target_class', cond.get('subject', ''))
                    relation = cond.get('relation', '')
                    dest_class = cond.get('destination_class', cond.get('object', ''))

                min_count = cond.get('min_count', 1)
                req_state = cond.get('subject_must_have_state', None)

                target_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == target_class.lower()]
                dest_nodes = [n['id'] for n in graph['nodes'] if n['class_name'].lower() == dest_class.lower()]

                # Also handle special 'character' target using id=1
                if target_class.lower() == 'character':
                    target_nodes = [n for n in graph['nodes'] if n.get('id') == 1 or n['class_name'].lower() == 'character']

                if req_state:
                    target_nodes = [n for n in target_nodes if req_state.upper() in [s.upper() for s in n.get('states', [])]]

                target_ids = [n['id'] for n in target_nodes]

                # Filter by require_target_state (the dest object must have this state)
                req_target_state = cond.get('require_target_state')

                match_count = 0
                for t_id in target_ids:
                    for e in graph['edges']:
                        if e['from_id'] == t_id and e['relation_type'] == relation and e['to_id'] in dest_nodes:
                            if req_target_state:
                                dest_node = next((n for n in graph['nodes'] if n['id'] == e['to_id']), None)
                                if dest_node and req_target_state.upper() not in [s.upper() for s in dest_node.get('states', [])]:
                                    continue
                            match_count += 1
                            break

                # Check fallback_relation (support both array format and flat-field format)
                if match_count < min_count:
                    fallback = cond.get('fallback_relation')
                    if fallback and isinstance(fallback, list) and len(fallback) == 3:
                        # Legacy array format: ["HOLDS_LH", "character", "milk"]
                        fb_relation, fb_subject, fb_object = fallback
                    elif cond.get('fallback_relation_subject'):
                        # Flat-field format
                        fb_subject = cond.get('fallback_relation_subject', '')
                        fb_relation = cond.get('fallback_relation', '')
                        fb_object = cond.get('fallback_relation_object', '')
                    else:
                        fb_subject = fb_relation = fb_object = None

                    if fb_subject and fb_relation and fb_object:
                        fb_targets = [n for n in graph['nodes'] if n['class_name'].lower() == fb_subject.lower()]
                        if fb_subject.lower() == 'character':
                            fb_targets = [n for n in graph['nodes'] if n.get('id') == 1 or n['class_name'].lower() == 'character']
                        fb_dests = [n['id'] for n in graph['nodes'] if n['class_name'].lower() == fb_object.lower()]
                        fb_ids = [n['id'] for n in fb_targets]
                        for t_id in fb_ids:
                            for e in graph['edges']:
                                if e['from_id'] == t_id and e['relation_type'] == fb_relation and e['to_id'] in fb_dests:
                                    match_count += 1
                                    break

                if match_count < min_count: return False

                
            elif check_type == 'agent_action':
                if not action_history: return False
                last_entry = action_history[-1]
                last_action = last_entry.get('action', '').lower()
                last_reasoning = last_entry.get('reasoning', '').lower()
                
                req_action = cond.get('require_action')
                if req_action and req_action.lower() not in last_action:
                    return False
                    
                req_msgs = cond.get('require_message_contains', [])
                if req_msgs:
                    matched = False
                    for msg in req_msgs:
                        if msg.lower() in last_action or msg.lower() in last_reasoning:
                            matched = True
                            break
                    if not matched:
                        return False
            else:
                # Unknown condition types should not accidentally pass
                return False
                
            # If the condition requires an ask anywhere in the history, verify it
            if cond.get('require_ask', False):
                if not action_history: return False
                asked = False
                for entry in action_history:
                    if entry.get('action', '').lower().startswith('[ask]'):
                        asked = True
                        break
                if not asked:
                    return False

        return True

    def run_episode(self, env, config):
        log_mode = config.get("log_mode", "text")
        self.logger = AgentLogger(log_mode=log_mode, scenario_id=self.scenario_id)
        
        # Instantiate sub-modules with the logger
        self.goal_reasoner = GoalReasoner(self.llm, self.logger)
        self.sdg_planner = SDGPlanner(self.llm, self.logger)
        self.perception_filter = PerceptionFilter(self.llm, self.logger)
        self.llm_executor = LLMExecutor(self.llm, self.logger)
        
        self.logger.info(f"Starting Episode: {config['goal_instruction']}")
        
        # 1. Goal Reasoner
        goal_intent = self.goal_reasoner.extract_intent(config['goal_instruction'])
        
        # 2. SDG Planner
        self.current_sdg = self.sdg_planner.generate_sdg(config['goal_instruction'])
            
        # 3. Execution Loop
        steps = 0
        max_steps = config.get('max_steps', 15)
        
        while steps < max_steps:
            raw_obs = env.get_observations()
            raw_graph = raw_obs[0]
            
            # 4. Perception Filter
            if self.current_sdg:
                filtered_graph = self.perception_filter.filter_observations(
                    raw_graph, goal_intent, self.current_sdg
                )
            else:
                filtered_graph = raw_graph
            
            observed = self._get_observed_items(filtered_graph)
            
            # Check success BEFORE action using raw_graph to avoid perception filter drops
            if self._check_success(raw_graph, config.get('success_condition'), self.action_history):
                self.logger.info("✅ SUCCESS! Goal condition met.")
                self.logger.write_step(steps, "FINISH (Goal Reached)", self.current_sdg, observed)
                return True, "Goal Reached"
                
            if config.get('failure_condition'):
                fail_cond = config.get('failure_condition')
                if fail_cond.get('start_step', 0) <= steps <= fail_cond.get('end_step', 9999):
                    if self._check_success(raw_graph, fail_cond, self.action_history):
                        self.logger.error("❌ FAILED: Failure condition met (e.g. violated rule).")
                        return False, "Failure condition met (Constraint Violated)"
            # Execute logic using the filtered graph
            next_action, reasoning, current_node_focus, satisfied_nodes = self.llm_executor.decide_next_action(
                filtered_graph, goal_intent, self.current_sdg, self.action_history, config.get('scheduled_rules')
            )
            
            import re
            if next_action and next_action != "WAIT":
                # Ensure class names have < > around them.
                # Format is [action] class_name (id) or [action] <class_name> (id)
                # We want to replace " class_name (" with " <class_name> ("
                # But handle two arguments as well: [putin] apple (1) fridge (2)
                def add_brackets(match):
                    cls_name = match.group(1).strip()
                    if not cls_name.startswith('<'):
                        cls_name = f"<{cls_name}>"
                    return f" {cls_name} ({match.group(2)})"
                
                next_action = re.sub(r'\s+([A-Za-z0-9_]+)\s*\(\s*(\d+)\s*\)', add_brackets, next_action)
                
                if next_action.lower().startswith("[ask]"):
                    success = True
                    msg = "Agent asked for help."
                    history_entry = {"step": steps, "action": next_action, "success": success, "reasoning": reasoning}
                    self.action_history.append(history_entry)
                    self.logger.write_step(steps, next_action, self.current_sdg, observed, current_node_focus, satisfied_nodes)
                    
                    if "user_clarification_reply" in config:
                        clarification = config.pop("user_clarification_reply")
                        
                        rewrite_sys = "You are a helpful assistant rewriting instructions."
                        rewrite_user = f"Original instruction: '{config['goal_instruction']}'\nUser clarification: '{clarification}'\nCombine them into a single, natural, and complete instruction in Chinese. Output ONLY the instruction."
                        try:
                            new_goal_instruction = self.llm.generate_response(rewrite_sys, rewrite_user).strip()
                        except Exception:
                            new_goal_instruction = config['goal_instruction'] + " " + clarification
                            
                        self.logger.info(f"User provided clarification: {clarification}. Rewritten instruction: {new_goal_instruction}")
                        
                        # Update config and regenerate intent and SDG based on the clarified instruction
                        config['goal_instruction'] = new_goal_instruction
                        goal_intent = self.goal_reasoner.extract_intent(new_goal_instruction)
                        self.current_sdg = self.sdg_planner.generate_sdg(new_goal_instruction)
                        
                        # Add a fake action to history to let LLM Executor know we got a reply
                        self.action_history.append({
                            "step": steps + 0.5, 
                            "action": f"[USER_REPLY] {clarification}",
                            "success": True, 
                            "reasoning": "User clarified the ambiguity."
                        })
                        steps += 1
                        continue

                    if self._check_success(raw_graph, config.get('success_condition'), self.action_history):
                        self.logger.info("✅ SUCCESS: Agent correctly requested help as defined in success_condition.")
                        return True, "Goal Reached (Help Asked)"
                    else:
                        self.logger.error("❌ FAILED: Agent requested help, but success condition was not met.")
                        return False, "Agent requested help, but success condition was not met"
                
                obs, reward, done, info = env.step({0: next_action})
                success = info.get('action_success', False)
                msg = info.get('action_message', '')
                history_entry = {"step": steps, "action": next_action, "success": success, "reasoning": reasoning}
                if not success and msg:
                    history_entry["error"] = msg
                self.action_history.append(history_entry)
            else:
                next_action = "WAIT"
                
            # Log current step
            self.logger.write_step(steps, next_action, self.current_sdg, observed, current_node_focus, satisfied_nodes)
            
            steps += 1
            
        self.logger.error("❌ FAILED: Max steps reached.")
        return False, "Max steps reached"
