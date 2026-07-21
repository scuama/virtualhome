import json
from ..utils.llm_client import LLMClient
from .prompt_templates import GOAL_REASONER_SYSTEM_PROMPT, GOAL_REASONER_USER_PROMPT
from .ablation import get_ablation_policy

class GoalReasoner:
    def __init__(self, llm_client: LLMClient, logger, ablation_profile="full"):
        self.llm = llm_client
        self.logger = logger
        self.global_intent = {}
        self.policy = get_ablation_policy(ablation_profile)

    def extract_intent(self, instruction: str) -> dict:
        """
        根据初始指令，使用 5 Whys 提取全局深度意图
        """
        if not self.policy.goal_reasoning:
            self.global_intent = {"literal_instruction": instruction}
            self._log_output()
            return self.global_intent

        user_prompt = GOAL_REASONER_USER_PROMPT.format(instruction=instruction)
        system_prompt = GOAL_REASONER_SYSTEM_PROMPT
        if not self.policy.intention:
            system_prompt = (
                "Extract only the literal executable parameters from the household "
                "instruction: objects, quantities, states, conditions, and destinations. "
                "Do not infer deeper intent, motivations, or functional alternatives. "
                "You may identify genuine ambiguity and provide one clarification_question. "
                "Return a JSON object."
            )
        elif not self.policy.parameter_binding:
            system_prompt += (
                "\n\nABLATION OVERRIDE: Do not detect ambiguous parameters and do not "
                "produce a clarification question. Make no claims that clarification is "
                "required; retain the intention analysis only."
            )
        
        self.logger.info(f"GoalReasoner evaluating instruction: '{instruction}'")
        
        result_dict = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_override="gpt-5.4-mini"
        )
        
        if result_dict:
            self.global_intent = result_dict
            if not self.policy.intention:
                self.global_intent.pop("deep_intent", None)
                self.global_intent.pop("reasoning_chain", None)
                self.global_intent.pop("acceptable_alternatives_properties", None)
            if not self.policy.parameter_binding:
                self.global_intent["is_instruction_obviously_vague"] = False
                self.global_intent["clarification_question"] = None
            self._log_output()
        else:
            self.logger.error("GoalReasoner failed to extract intent.")
            
        return self.global_intent

    def _log_output(self):
        self.logger.log_module_output(
            module_name="GoalReasoner (Module A - Intent)",
            step=0,
            output_data=json.dumps(self.global_intent, indent=2, ensure_ascii=False),
        )
