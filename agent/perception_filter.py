import json
from .llm_client import LLMClient
from .prompt_templates import PERCEPTION_SYSTEM_PROMPT

class PerceptionFilter:
    def __init__(self, llm_client: LLMClient, logger):
        self.llm = llm_client
        self.logger = logger
        
    def filter_observations(self, raw_graph, intent_dict, current_sdg, max_ids=15):
        """
        Compresses the graph, asks the Attention LLM to pick relevant IDs,
        and returns a trimmed graph.
        """
        self.logger.info("PerceptionFilter: Compressing raw graph for Attention LLM...")
        
        # 1. Compress the raw graph
        # Group items. For simplicity, just list all non-room nodes.
        items = []
        for node in raw_graph.get('nodes', []):
            if node['category'] not in ['Rooms']:
                items.append(f"{node['class_name']}({node['id']})")
                
        compressed_scene = ", ".join(items)
        
        sdg_str = json.dumps(current_sdg, ensure_ascii=False) if current_sdg else "No SDG available."
        intent_str = json.dumps(intent_dict, ensure_ascii=False)
        
        user_prompt = f"Goal Intent:\n{intent_str}\n\nRequired SDG:\n{sdg_str}\n\nObserved Objects:\n{compressed_scene}"
        
        # 2. Call Attention LLM
        self.logger.info("PerceptionFilter: Asking Attention LLM to pick relevant IDs...")
        
        try:
            result_str = self.llm.generate_response(
                system_prompt=PERCEPTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_format="json_object",
                model_override="gpt-5.4-mini" # Use a fast/cheap model for attention
            )
            result_dict = json.loads(result_str)
            selected_ids = result_dict.get("selected_ids", [])
            reasoning = result_dict.get("reasoning", "")
        except Exception as e:
            self.logger.error(f"PerceptionFilter failed: {e}")
            selected_ids = []
            reasoning = "Fallback due to error."
            
        # Force include objects that are explicitly named in SDG or intent
        sdg_str_lower = sdg_str.lower()
        intent_str_lower = intent_str.lower()
        for node in raw_graph.get('nodes', []):
            cname = node['class_name'].lower()
            if cname in ['character']:
                if node['id'] not in selected_ids: selected_ids.append(node['id'])
                continue
            if cname in sdg_str_lower or cname in intent_str_lower:
                if node['id'] not in selected_ids:
                    selected_ids.append(node['id'])
            

        self.logger.log_module_output("PerceptionFilter", 0, {
            "reasoning": reasoning,
            "selected_ids": selected_ids,
            "raw_item_count": len(items)
        })
        
        # 3. Hydrate the selected IDs + Robot Character
        if not selected_ids:
            return raw_graph # Fallback to all if failed
            
        # Ensure we always keep the character node
        character_id = None
        for node in raw_graph.get('nodes', []):
            if node['class_name'].lower() == 'character':
                character_id = node['id']
                if character_id not in selected_ids:
                    selected_ids.append(character_id)
                break
                
        # Also always keep Rooms to preserve spatial awareness if needed
        # We'll just keep the selected IDs and the character
        selected_ids_set = set(selected_ids)
        
        filtered_nodes = [n for n in raw_graph.get('nodes', []) if n['id'] in selected_ids_set]
        
        # Keep edges only if BOTH from_id and to_id are in the filtered set
        filtered_edges = [
            e for e in raw_graph.get('edges', []) 
            if e['from_id'] in selected_ids_set and e['to_id'] in selected_ids_set
        ]
        
        filtered_graph = {
            "nodes": filtered_nodes,
            "edges": filtered_edges
        }
        
        self.logger.info(f"PerceptionFilter: Graph reduced from {len(raw_graph.get('nodes', []))} to {len(filtered_nodes)} nodes.")
        return filtered_graph

