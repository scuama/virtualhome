import json
import os
import datetime
from .llm_client import LLMClient
from .goal_reasoner import GoalReasoner
from .sdg_planner import SDGPlanner
from .perception_filter import PerceptionFilter
from .llm_executor import LLMExecutor

class AgentLogger:
    def __init__(self, log_mode="text"):
        self.log_mode = log_mode
        os.makedirs("agent/logs", exist_ok=True)
        self.log_file = f"agent/logs/run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
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
        
    def write_step(self, step, action, sdg, observed_items):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"## Step {step}\n")
            f.write(f"- **Action**: `{action}`\n")
            
            # Always output the Mermaid graph for SDG
            f.write(f"- **SDG Status**:\n")
            if sdg:
                f.write(f"```mermaid\n{self._generate_mermaid(sdg)}\n```\n")
            else:
                f.write("No SDG active.\n")
                
            f.write(f"- **Observed Items ({len(observed_items)})**: {', '.join(observed_items[:15])}{'...' if len(observed_items) > 15 else ''}\n")
            f.write("\n")

    def _generate_mermaid(self, sdg):
        lines = ["graph TD"]
        nodes = sdg.get("nodes", [])
        edges = sdg.get("edges", [])

        for node in nodes:
            nid = node["id"]
            if node["type"] == "State":
                label = f"{node['object']}<br>({node['value']})"
            elif node["type"] == "Relation":
                label = f"{node['object']}<br>{node['relation']}<br>{node.get('target', '')}"
            else:
                label = f"{node['object']}"
            
            # Escape quotes in label to avoid syntax errors
            label = label.replace('"', '\\"')
            lines.append(f'    {nid}["{label}"]')

        for edge in edges:
            reason = edge.get('reason', '')
            reason = reason.replace('"', '\\"')
            lines.append(f'    {edge["from"]} -->|"{reason}"| {edge["to"]}')
        return "\n".join(lines)


class VirtualHomeAgent:
    def __init__(self, model_name="gpt-5.4-mini"):
        self.llm = LLMClient(model_name=model_name)
        self.action_history = []
        self.current_sdg = None
        self.goal_reasoner = None
        self.sdg_planner = None
        self.perception_filter = None
        self.llm_executor = None
        self.logger = None

    def _get_observed_items(self, graph):
        items = []
        for n in graph.get('nodes', []):
            states = n.get('states', [])
            state_str = f" [{','.join(states)}]" if states else ""
            items.append(f"{n['class_name']}({n['id']}){state_str}")
        return items

    def _check_success(self, graph, condition):
        if not condition: return False
        req_state = condition['require_state']
        quantifier = condition.get('quantifier', 'any')
        target_class = condition['target_class']
        
        target_nodes = [n for n in graph['nodes'] if n['class_name'].lower() == target_class.lower()]
        if not target_nodes: return False
            
        hot_count = sum(1 for n in target_nodes if req_state in n.get('states', []))
        if quantifier == 'any':
            return hot_count > 0
        elif quantifier == 'all':
            return hot_count == len(target_nodes)
        return False

    def run_episode(self, env, config):
        log_mode = config.get("log_mode", "text")
        self.logger = AgentLogger(log_mode=log_mode)
        
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
        max_steps = config.get('max_steps', 30)
        
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
            if self._check_success(raw_graph, config.get('success_condition')):
                self.logger.info("✅ SUCCESS! Goal condition met.")
                self.logger.write_step(steps, "FINISH (Goal Reached)", self.current_sdg, observed)
                return True
                
            # Execute logic using the filtered graph
            next_action = self.llm_executor.decide_next_action(
                filtered_graph, goal_intent, self.current_sdg, self.action_history
            )
            
            if next_action and next_action != "WAIT":
                obs, reward, done, info = env.step({0: next_action})
                success = info.get('action_success', False)
                self.action_history.append({"step": steps, "action": next_action, "success": success})
            else:
                next_action = "WAIT"
                
            # Log current step
            self.logger.write_step(steps, next_action, self.current_sdg, observed)
            
            steps += 1
            
        self.logger.error("❌ FAILED: Max steps reached.")
        return False
