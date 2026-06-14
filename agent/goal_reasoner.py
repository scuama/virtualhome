import json
from .llm_client import LLMClient
from .prompt_templates import GOAL_REASONER_SYSTEM_PROMPT, GOAL_REASONER_USER_PROMPT, STATE_MACHINE_GENERATOR_SYSTEM_PROMPT, STATE_MACHINE_GENERATOR_USER_PROMPT

class GoalReasoner:
    def __init__(self, llm_client: LLMClient, logger):
        self.llm = llm_client
        self.logger = logger
        self.global_intent = {}

    def extract_intent(self, instruction: str, use_state_machine: bool = False) -> dict:
        """
        根据初始指令，使用 5 Whys 提取全局深度意图，并可选地生成状态机
        """
        user_prompt = GOAL_REASONER_USER_PROMPT.format(instruction=instruction)
        
        self.logger.info(f"GoalReasoner evaluating instruction: '{instruction}'")
        
        result_dict = self.llm.generate_json(
            system_prompt=GOAL_REASONER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model_override="gpt-5.4-mini"
        )
        
        if result_dict:
            self.global_intent = result_dict
            self.logger.log_module_output(
                module_name="GoalReasoner (Module A - Intent)",
                step=0,
                output_data=json.dumps(self.global_intent, indent=2, ensure_ascii=False)
            )
            
            # Optional: Generate State Machine
            if use_state_machine and "target_object" in self.global_intent:
                self.logger.info("GoalReasoner building state machine for target object.")
                sm_user_prompt = STATE_MACHINE_GENERATOR_USER_PROMPT.format(
                    instruction=instruction,
                    target_object=self.global_intent["target_object"],
                    deep_intent=self.global_intent.get("deep_intent", "")
                )
                sm_result = self.llm.generate_json(
                    system_prompt=STATE_MACHINE_GENERATOR_SYSTEM_PROMPT,
                    user_prompt=sm_user_prompt,
                    model_override="gpt-5.4-mini"
                )
                if sm_result and "state_machine" in sm_result:
                    self.global_intent["state_machine_rules"] = sm_result["state_machine"]
                    self.logger.log_module_output(
                        module_name="GoalReasoner (Module A - State Machine)",
                        step=0,
                        output_data=json.dumps(sm_result["state_machine"], indent=2, ensure_ascii=False)
                    )
        else:
            self.logger.error("GoalReasoner failed to extract intent.")
            
        return self.global_intent

    def get_global_intent(self):
        return self.global_intent
