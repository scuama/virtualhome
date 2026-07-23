import json
from ..utils.llm_client import LLMClient
from .prompt_templates import EXECUTOR_SYSTEM_PROMPT
from .ablation import get_ablation_policy

class LLMExecutor:
    def __init__(self, llm_client: LLMClient, logger, ablation_profile="full"):
        self.llm = llm_client
        self.logger = logger
        self.policy = get_ablation_policy(ablation_profile)
        
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

    def decide_next_action(
        self,
        filtered_graph,
        intent_dict,
        current_sdg,
        action_history,
        scheduled_rules=None,
        allow_ask=True,
        task_context=None,
    ):
        self.logger.info("LLMExecutor: Analyzing filtered graph to decide next action...")
        
        graph_str = self._compress_filtered_graph(filtered_graph)
        sdg_str = json.dumps(current_sdg, ensure_ascii=False) if current_sdg else "No SDG available."
        intent_str = json.dumps(intent_dict, ensure_ascii=False)
        visible_history = action_history[-10:]
        if not self.policy.memory:
            visible_history = [entry for entry in visible_history if not entry.get("success", False)]
        elif not self.policy.state_alignment:
            visible_history = [entry for entry in visible_history if not entry.get("success", False)]
        history_str = json.dumps(visible_history, ensure_ascii=False) if visible_history else "None"
        
        current_step = len(action_history)
        active_rules = []
        if scheduled_rules:
            for rule in scheduled_rules:
                if rule.get('start_step', 0) <= current_step <= rule.get('end_step', 9999):
                    rule_text = rule['rule_text']
                    if rule.get('end_step', 9999) < 999:
                        rule_text += f" (Note: This rule is temporary and will expire at step {rule.get('end_step')+1}. If this blocks your required preconditions, you MUST output [wait] until it expires.)"
                    active_rules.append(rule_text)
        
        rules_str = "\n".join([f"- {r}" for r in active_rules]) if active_rules else "None"
        
        if allow_ask:
            clarification_rule = "Clarification is still available once if genuinely required."
        elif not self.policy.parameter_binding:
            clarification_rule = (
                "Parameter clarification is disabled by this ablation. The [ask] "
                "action is forbidden for ambiguous wording; choose a physical binding "
                "autonomously."
            )
        else:
            clarification_rule = (
                "A clarification reply has already been received. The [ask] "
                "action is now strictly forbidden for the rest of this "
                "episode. Continue autonomously using physical actions or "
                "[wait]."
            )
        task_context_str = json.dumps(
            task_context or {}, ensure_ascii=False
        )
        user_prompt = f"Task Scheduling Context:\n{task_context_str}\n\nGoal Intent FOR THE ACTIVE TASK ONLY:\n{intent_str}\n\nRequired SDG FOR THE ACTIVE TASK ONLY:\n{sdg_str}\n\nPast Actions (last 10):\n{history_str}\n\nCurrent Filtered Graph:\n{graph_str}\n\nActive Global Rules:\n{rules_str}\n\nClarification Rule:\n{clarification_rule}\n\nWork only on active_task_id. Never manipulate objects belonging to satisfied_task_ids. What is the SINGLE NEXT action to execute? (Do not repeat a walk action if you just did it)"

        system_prompt = EXECUTOR_SYSTEM_PROMPT
        if not self.policy.state_alignment:
            system_prompt += (
                "\n\nSTATE ALIGNMENT ABLATION (HIGHEST PRIORITY): Use only object "
                "states and IDs in the current graph. Do not associate a current node with "
                "a previously observed node, infer state evolution from successful past "
                "actions, or recover identity from historical properties."
            )
        if not self.policy.path_merging:
            system_prompt += (
                "\n\nPATH MERGING ABLATION (HIGHEST PRIORITY): Follow the configured "
                "task/checklist order independently. Do not reorder branches to share "
                "navigation, containers, appliances, or other prerequisites."
            )
        if not allow_ask:
            if not self.policy.parameter_binding:
                system_prompt += (
                    "\n\nPARAMETER BINDING ABLATION (HIGHEST PRIORITY): You MUST "
                    "NOT output [ask] for ambiguous or underspecified parameters. Choose "
                    "an autonomous physical binding and act."
                )
            else:
                system_prompt += (
                    "\n\nEPISODE OVERRIDE (HIGHEST PRIORITY): A clarification "
                    "reply has already been provided. You MUST NOT output [ask] "
                    "again under any circumstances. Choose an autonomous physical "
                    "action or [wait]."
                )
        
        try:
            result_dict = self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                module_name="llm_executor",
            )
            action = result_dict.get("action", "WAIT")
            reasoning = result_dict.get("reasoning", "")
            mapped_vars = result_dict.get("mapped_variables", {})
            satisfied_nodes = result_dict.get("satisfied_nodes", [])
            current_node_focus = result_dict.get("current_node_focus", "")
            
        except Exception as e:
            self.logger.error(f"LLMExecutor failed: {e}")
            action = "WAIT"
            reasoning = "Fallback due to error."
            mapped_vars = {}
            satisfied_nodes = []
            current_node_focus = ""

        if not allow_ask and str(action).strip().lower().startswith("[ask]"):
            self.logger.info(
                "LLMExecutor suppressed a repeated [ask] after clarification."
            )
            action = "[wait]"
            reasoning = (
                reasoning
                + " Repeated clarification is forbidden; waiting and replanning."
            ).strip()
            
        self.logger.log_module_output("LLMExecutor", 0, {
            "reasoning": reasoning,
            "satisfied_nodes": satisfied_nodes,
            "current_node_focus": current_node_focus,
            "mapped_variables": mapped_vars,
            "action": action
        })
        
        return action, reasoning, current_node_focus, satisfied_nodes
