import json
from ..utils.llm_client import LLMClient
from .prompt_templates import SDG_SYSTEM_PROMPT, SDG_USER_PROMPT
from .ablation import get_ablation_policy

class SDGPlanner:
    def __init__(self, llm_client: LLMClient, logger, ablation_profile="full"):
        self.llm = llm_client
        self.logger = logger
        self.current_sdg = None
        self.policy = get_ablation_policy(ablation_profile)

    def generate_sdg(self, goal_description: str) -> dict:
        if not self.policy.stg_planning:
            return {"planning_ablation": "no_stg_planning"}
        if not self.policy.stg_construction:
            checklist = self.llm.generate_json(
                system_prompt=(
                    "Turn the embodied household instruction into a short, ordered, flat "
                    "action checklist. Do not create graph nodes, dependencies, or edges. "
                    "Return JSON as {\"checklist\": [\"step\"]}."
                ),
                user_prompt=f"Task: {goal_description}",
            )
            result = {
                "planning_ablation": "flat_checklist",
                "checklist": list(checklist.get("checklist", [])),
            }
            self.current_sdg = result
            return result
        user_prompt = SDG_USER_PROMPT.format(goal_description=goal_description)
        sdg_data = self.llm.generate_json(
            system_prompt=SDG_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
        
        if sdg_data:
            self.current_sdg = sdg_data
            if self.logger:
                self.logger.log_info(f"Generated SDG with {len(sdg_data.get('nodes', []))} nodes.")
            return sdg_data
        else:
            if self.logger:
                self.logger.log_error(f"SDG JSON 解析失败, 返回空。")
            return None

