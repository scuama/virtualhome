from abc import ABC, abstractmethod
from typing import Tuple

class BaseAgent(ABC):
    # Agents should override this to specify their required observation modalities (e.g., ['partial'], ['image'])
    REQUIRED_OBSERVATION = ['partial']

    def __init__(self, model_name: str, scenario_id: str):
        self.model_name = model_name
        self.scenario_id = scenario_id

    @abstractmethod
    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        """
        Takes the current observation and configuration, and returns the next action string.
        
        Args:
            obs: The observation from the environment (e.g. graph dictionary for 'partial', image arrays for 'image').
            config: The scenario configuration dictionary.
            env_info: Optional dict containing metadata (like previous action success, etc).
            
        Returns:
            The action string to execute (e.g. '[walk] <apple> (12)').
        """
        pass
