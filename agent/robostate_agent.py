import json
import os
import datetime
from .utils.llm_client import LLMClient
from .utils.logger import AgentLogger
from .robostate.goal_reasoner import GoalReasoner
from .robostate.sdg_planner import SDGPlanner
from .robostate.perception_filter import PerceptionFilter
from .robostate.llm_executor import LLMExecutor
from .base_agent import BaseAgent

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
        self.logger = None

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

    REQUIRED_OBSERVATION = ["partial"]

    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        goal_instruction = config.get("goal_instruction", "")
        if not goal_instruction:
            return "done()"
            
        env_info = env_info or {}
        step = env_info.get("step", 0)
        self.logger = env_info.get("logger") or getattr(self, "logger", None)
        if not self.logger:
            self.logger = AgentLogger(log_mode=config.get("log_mode", "markdown"), scenario_id=self.scenario_id)
            
        self.action_history = env_info.get("action_history", [])

        if step == 0:
            self.goal_reasoner = GoalReasoner(self.llm, self.logger)
            self.sdg_planner = SDGPlanner(self.llm, self.logger)
            self.perception_filter = PerceptionFilter(self.llm, self.logger)
            self.llm_executor = LLMExecutor(self.llm, self.logger)
            
            self.logger.info(f"Starting Episode: {goal_instruction}")
            self.goal_intent = self.goal_reasoner.extract_intent(goal_instruction)
            self.current_sdg = self.sdg_planner.generate_sdg(goal_instruction)
            
            self.memory_nodes = {}
            self.memory_edges = {}
            self.active_hidden_nodes = {}
            self.dynamic_events = config.get("dynamic_events", [])
            for ev in self.dynamic_events:
                ev["times_triggered"] = 0

        # --- UPDATE SPATIAL MEMORY ---
        visible_ids = set()
        for n in obs.get('nodes', []):
            self.memory_nodes[n['id']] = n.copy()
            visible_ids.add(n['id'])
            self.memory_edges[n['id']] = []
            
        for e in obs.get('edges', []):
            if e['from_id'] in visible_ids:
                self.memory_edges[e['from_id']].append(e)
                
        # Reconstruct merged graph from memory
        raw_graph = {
            'nodes': list(self.memory_nodes.values()),
            'edges': [e for edge_list in self.memory_edges.values() for e in edge_list]
        }

        # --- GRAPH PRUNING FOR HIDDEN NODES ---
        if self.active_hidden_nodes:
            raw_graph['nodes'] = [n for n in raw_graph['nodes'] if n['id'] not in self.active_hidden_nodes]
            raw_graph['edges'] = [e for e in raw_graph['edges'] if e['from_id'] not in self.active_hidden_nodes and e['to_id'] not in self.active_hidden_nodes]

        # 4. Perception Filter
        if self.current_sdg:
            filtered_graph = self.perception_filter.filter_observations(
                raw_graph, self.goal_intent, self.current_sdg
            )
        else:
            filtered_graph = raw_graph
        
        observed = self._get_observed_items(filtered_graph)

        # Decide next action
        next_action, reasoning, current_node_focus, satisfied_nodes = self.llm_executor.decide_next_action(
            filtered_graph, self.goal_intent, self.current_sdg, self.action_history, config.get('scheduled_rules')
        )
        
        import re
        if next_action and next_action != "WAIT":
            def add_brackets(match):
                cls_name = match.group(1).strip()
                if not cls_name.startswith('<'):
                    cls_name = f"<{cls_name}>"
                return f" {cls_name} ({match.group(2)})"
            
            next_action = re.sub(r'\s+([A-Za-z0-9_]+)\s*\(\s*(\d+)\s*\)', add_brackets, next_action)
            
            if next_action.lower().startswith("[ask]"):
                if "user_clarification_reply" in config:
                    clarification = config.pop("user_clarification_reply")
                    rewrite_sys = "You are a helpful assistant rewriting instructions."
                    rewrite_user = f"Original instruction: '{config.get('goal_instruction')}'\nUser clarification: '{clarification}'\nCombine them into a single, natural, and complete instruction in English. Output ONLY the instruction."
                    try:
                        new_goal_instruction = self.llm.generate_response(rewrite_sys, rewrite_user).strip()
                    except Exception:
                        new_goal_instruction = config.get('goal_instruction') + " " + clarification
                        
                    self.logger.info(f"User provided clarification: {clarification}. Rewritten instruction: {new_goal_instruction}")
                    config['goal_instruction'] = new_goal_instruction
                    self.goal_intent = self.goal_reasoner.extract_intent(new_goal_instruction)
                    self.current_sdg = self.sdg_planner.generate_sdg(new_goal_instruction)
                    return "wait()" # Let step fail/retry with new plan
            
            # --- DYNAMIC EVENTS TRIGGER ---
            for ev in self.dynamic_events:
                trigger = ev['trigger']
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
                                if t_id not in self.active_hidden_nodes:
                                    self.active_hidden_nodes[t_id] = dur
                                    ev['times_triggered'] += 1
                                    self.logger.info(f"⚡ DYNAMIC EVENT: {trigger['target']}({t_id}) hidden for {dur} steps.")

            # --- INTERCEPT HIDDEN OBJECTS ---
            target_match = re.search(r'\(\s*(\d+)\s*\)', next_action)
            if target_match:
                target_id = int(target_match.group(1))
                if target_id in self.active_hidden_nodes:
                    # Actually we want test_runner to try and fail, but to mimic exact behavior, 
                    # we can change the action to a WAIT or let it fail naturally.
                    pass
        else:
            next_action = "WAIT"
            
        # --- DYNAMIC EVENTS TICK ---
        expired = []
        for k, v in self.active_hidden_nodes.items():
            if v != float('inf'):
                self.active_hidden_nodes[k] = v - 1
                if self.active_hidden_nodes[k] <= 0:
                    expired.append(k)
        for k in expired:
            del self.active_hidden_nodes[k]
            self.logger.info(f"⚡ DYNAMIC EVENT: object {k} reappeared.")
            
        return next_action
