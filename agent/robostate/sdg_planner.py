import json
from ..utils.llm_client import LLMClient
from .prompt_templates import SDG_SYSTEM_PROMPT, SDG_USER_PROMPT

class SDGPlanner:
    def __init__(self, llm_client: LLMClient, logger):
        self.llm = llm_client
        self.logger = logger
        self.current_sdg = None

    def generate_sdg(self, goal_description: str) -> dict:
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


