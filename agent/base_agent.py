from abc import ABC, abstractmethod
from typing import Tuple

class BaseAgent(ABC):
    def __init__(self, model_name: str, scenario_id: str):
        self.model_name = model_name
        self.scenario_id = scenario_id

    @abstractmethod
    def run_episode(self, env, config) -> Tuple[bool, str]:
        """
        Executes the agent in the environment for a given config.
        Returns: (success: bool, reason: str)
        """
        pass
