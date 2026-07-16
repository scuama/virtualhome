import json
import os
import datetime
from ..utils.llm_client import LLMClient
from ..utils.logger import AgentLogger
from .goal_reasoner import GoalReasoner
from .sdg_planner import SDGPlanner
from .perception_filter import PerceptionFilter
from .llm_executor import LLMExecutor
from ..base_agent import BaseAgent

class RoboStateAgent(BaseAgent):
    def __init__(self, model_name="gpt-4o-mini", scenario_id=""):
        super().__init__(model_name, scenario_id)
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
            target_class = cond.get('target_class', 'ANY')
            min_count = cond.get('min_count', 1)
            req_states = cond.get('states', [])
            req_props = cond.get('properties', [])
            relation = cond.get('relation')
            dest_class = cond.get('destination_class')
            dest_states = cond.get('destination_states', [])
            dest_props = cond.get('destination_properties', [])
            
            if target_class.upper() == 'ANY':
                candidates = graph['nodes']
            elif target_class.lower() == 'character':
                candidates = [n for n in graph['nodes'] if n.get('id') == 1 or n['class_name'].lower() == 'character']
            else:
                candidates = [n for n in graph['nodes'] if n['class_name'].lower() == target_class.lower()]

            if not candidates:
                return False
                
            if req_states:
                valid_candidates = []
                for n in candidates:
                    node_states = [s.upper() for s in n.get('states', [])]
                    if all(req.upper() in node_states for req in req_states):
                        valid_candidates.append(n)
                candidates = valid_candidates
                
            if req_props:
                valid_candidates = []
                for n in candidates:
                    node_props = [p.upper() for p in n.get('properties', [])]
                    if all(req.upper() in node_props for req in req_props):
                        valid_candidates.append(n)
                candidates = valid_candidates
                
            if relation:
                valid_candidates = []
                for n in candidates:
                    rel_matched = False
                    for e in graph['edges']:
                        e_rel = e.get('relation_type', e.get('relation', '')).upper()
                        target_rels = [r.strip() for r in relation.upper().split('|')]
                        if e['from_id'] == n['id'] and e_rel in target_rels:
                            target_node = next((tn for tn in graph['nodes'] if tn['id'] == e['to_id']), None)
                            if not target_node: continue
                            
                            # Check destination class
                            if dest_class and dest_class.upper() != 'ANY':
                                if target_node['class_name'].lower() != dest_class.lower():
                                    continue
                            
                            # Check destination states
                            if dest_states:
                                tn_states = [s.upper() for s in target_node.get('states', [])]
                                if not all(req.upper() in tn_states for req in dest_states):
                                    continue
                                    
                            # Check destination properties
                            if dest_props:
                                tn_props = [p.upper() for p in target_node.get('properties', [])]
                                if not all(req.upper() in tn_props for req in dest_props):
                                    continue
                            
                            rel_matched = True
                            break
                    if rel_matched:
                        valid_candidates.append(n)
                candidates = valid_candidates
                
            if len(candidates) < min_count:
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
            
        # Initialize Spatial Memory with FULL graph (Mental Map)
        full_graph_init = env.get_graph()
        self.memory_nodes = {n['id']: n.copy() for n in full_graph_init.get('nodes', [])}
        self.memory_edges = {}
        for e in full_graph_init.get('edges', []):
            self.memory_edges.setdefault(e['from_id'], []).append(e)

        # --- PRIOR MEMORY INJECTION ---
        self.action_history = config.get('prior_action_history', [])

        # 3. Execution Loop
        steps = 0
        max_steps = config.get('max_steps', 15)
        
        while steps < max_steps:
            raw_obs = env.get_observations()
            partial_graph = raw_obs[0]
            
            # --- UPDATE SPATIAL MEMORY ---
            visible_ids = set()
            for n in partial_graph.get('nodes', []):
                self.memory_nodes[n['id']] = n.copy()
                visible_ids.add(n['id'])
                # Clear old outward edges for this visible node
                self.memory_edges[n['id']] = []
                
            for e in partial_graph.get('edges', []):
                if e['from_id'] in visible_ids:
                    self.memory_edges[e['from_id']].append(e)
                    
            # Reconstruct merged graph from memory
            raw_graph = {
                'nodes': list(self.memory_nodes.values()),
                'edges': [e for edge_list in self.memory_edges.values() for e in edge_list]
            }

            # --- GRAPH PRUNING FOR HIDDEN NODES ---
            hidden_nodes = getattr(env, 'active_hidden_nodes', {})
            if hidden_nodes:
                raw_graph['nodes'] = [n for n in raw_graph['nodes'] if n['id'] not in hidden_nodes]
                raw_graph['edges'] = [e for e in raw_graph['edges'] if e['from_id'] not in hidden_nodes and e['to_id'] not in hidden_nodes]

            
            # 4. Perception Filter
            if self.current_sdg:
                filtered_graph = self.perception_filter.filter_observations(
                    raw_graph, goal_intent, self.current_sdg
                )
            else:
                filtered_graph = raw_graph
            
            observed = self._get_observed_items(filtered_graph)
            
            # Check success BEFORE action using the true full graph to avoid partial/memory errors
            true_full_graph = env.get_graph()
            if self._check_success(true_full_graph, config.get('success_condition'), self.action_history):
                if config.get("require_ask_to_pass", False):
                    has_asked = any(entry.get('action', '').lower().startswith('[ask]') for entry in self.action_history)
                    if not has_asked:
                        self.logger.error("❌ FAILED: Goal physically reached, but agent failed to ask as required.")
                        return False, "Failed: Did not ask for clarification"
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
                        rewrite_user = f"Original instruction: '{config['goal_instruction']}'\nUser clarification: '{clarification}'\nCombine them into a single, natural, and complete instruction in English. Output ONLY the instruction."
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

                    policy = config.get("on_ask_policy", "FAIL")
                    if policy == "SUCCESS":
                        self.logger.info("✅ SUCCESS: Agent requested help, fulfilling the on_ask_policy SUCCESS condition.")
                        return True, "Goal Reached (Help Asked)"
                    else:
                        self.logger.error("❌ FAILED: Agent requested help, which triggers immediate failure under current policy.")
                        return False, "Agent requested help, which is not permitted"
                
                # --- DYNAMIC EVENTS TRIGGER ---
                dynamic_events = config.get('dynamic_events', [])
                for ev in dynamic_events:
                    trigger = ev['trigger']
                    ev['times_triggered'] = ev.get('times_triggered', 0)
                    if ev['times_triggered'] >= ev.get('max_triggers', 1):
                        continue

                    if f"[{trigger['action']}]" in next_action.lower() and f"<{trigger['target'].lower()}>" in next_action.lower():
                        match = re.search(r'\(\s*(\d+)\s*\)', next_action)
                        if match:
                            t_id = int(match.group(1))
                            req_state = trigger.get('target_state')
                            node_ok = True
                            if req_state:
                                n_node = next((n for n in raw_graph['nodes'] if n['id'] == t_id), None)
                                if n_node and req_state.upper() not in [s.upper() for s in n_node.get('states', [])]:
                                    node_ok = False
                            
                            if node_ok:
                                effect = ev['effect']
                                if effect['type'] == 'hide':
                                    dur = effect['duration_steps']
                                    if not hasattr(env, 'active_hidden_nodes'):
                                        env.active_hidden_nodes = {}
                                    if t_id not in env.active_hidden_nodes:
                                        env.active_hidden_nodes[t_id] = dur
                                        ev['times_triggered'] += 1
                                        self.logger.info(f"⚡ DYNAMIC EVENT: {trigger['target']}({t_id}) hidden for {dur} steps.")

                # --- INTERCEPT HIDDEN OBJECTS ---
                target_match = re.search(r'\(\s*(\d+)\s*\)', next_action)
                intercepted = False
                if target_match:
                    target_id = int(target_match.group(1))
                    hidden_nodes = getattr(env, 'active_hidden_nodes', {})
                    if target_id in hidden_nodes:
                        success = False
                        msg = "动作失败：目标物品突然消失了，请等待或重新规划。"
                        history_entry = {"step": steps, "action": next_action, "success": success, "reasoning": reasoning, "error": msg}
                        self.action_history.append(history_entry)
                        intercepted = True
                        
                if not intercepted:
                    self.logger.info(f"Executing action: {next_action}")
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
            
            # --- DYNAMIC EVENTS TICK ---
            if hasattr(env, 'active_hidden_nodes'):
                expired = []
                for k, v in env.active_hidden_nodes.items():
                    if v != float('inf'):
                        env.active_hidden_nodes[k] = v - 1
                        if env.active_hidden_nodes[k] <= 0:
                            expired.append(k)
                for k in expired:
                    del env.active_hidden_nodes[k]
                    self.logger.info(f"⚡ DYNAMIC EVENT: object {k} reappeared.")
            
        self.logger.error("❌ FAILED: Max steps reached.")
        return False, "Max steps reached"
