import json
from .llm_client import LLMClient
from .prompt_templates import EXECUTOR_SYSTEM_PROMPT

class LLMExecutor:
    def __init__(self, llm_client: LLMClient, logger):
        self.llm = llm_client
        self.logger = logger
        
    def _compress_filtered_graph(self, filtered_graph):
        """Convert the filtered graph into a readable string for the LLM"""
        items = []
        for node in filtered_graph.get('nodes', []):
            name = node['class_name']
            nid = node['id']
            states = node.get('states', [])
            props = node.get('properties', [])
            
            # Extract relevant relations
            relations = []
            for edge in filtered_graph.get('edges', []):
                if edge['from_id'] == nid:
                    to_node = next((n for n in filtered_graph['nodes'] if n['id'] == edge['to_id']), None)
                    if to_node:
                        relations.append(f"{edge['relation_type']} {to_node['class_name']}({to_node['id']})")
                        
            desc = f"- {name}({nid}) | States: {states} | Props: {props}"
            if relations:
                desc += f" | Relations: {relations}"
            items.append(desc)
            
        return "\n".join(items)

    def decide_next_action(self, filtered_graph, intent_dict, current_sdg, action_history):
        self.logger.info("LLMExecutor: Analyzing filtered graph to decide next action...")
        
        graph_str = self._compress_filtered_graph(filtered_graph)
        sdg_str = json.dumps(current_sdg, ensure_ascii=False) if current_sdg else "No SDG available."
        intent_str = json.dumps(intent_dict, ensure_ascii=False)
        history_str = json.dumps(action_history[-3:], ensure_ascii=False) if action_history else "None"
        
        user_prompt = f"Goal Intent:\n{intent_str}\n\nRequired SDG:\n{sdg_str}\n\nPast Actions (last 3):\n{history_str}\n\nCurrent Filtered Graph:\n{graph_str}\n\nWhat is the SINGLE NEXT action to execute? (Do not repeat a walk action if you just did it)"
        
        try:
            result_str = self.llm.generate_response(
                system_prompt=EXECUTOR_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_format="json_object",
                model_override="gpt-5.4-mini" # Use fast model for action step
            )
            result_dict = json.loads(result_str)
            action = result_dict.get("action", "WAIT")
            reasoning = result_dict.get("reasoning", "")
            mapped_vars = result_dict.get("mapped_variables", {})
            
        except Exception as e:
            self.logger.error(f"LLMExecutor failed: {e}")
            action = "WAIT"
            reasoning = "Fallback due to error."
            mapped_vars = {}
            
        self.logger.log_module_output("LLMExecutor", 0, {
            "reasoning": reasoning,
            "mapped_variables": mapped_vars,
            "action": action
        })
        
        return action
