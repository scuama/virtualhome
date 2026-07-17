import json
import re
from typing import List, Dict, Any

from .base_agent import BaseAgent
from .utils.llm_client import LLMClient


class ExRAPAgent(BaseAgent):
    """
    Simplified ExRAP Agent for continual instruction following.
    Prioritizes fast implementation while capturing the core idea:
    Maintaining a Temporal Embodied Knowledge Graph (TEKG) and balancing exploration vs exploitation.
    """

    # Define the observation mode
    REQUIRED_OBSERVATION = ['partial']

    def __init__(self, model_name: str = "gpt-4o-mini", scenario_id: str = ""):
        super().__init__(model_name, scenario_id)
        self.llm = LLMClient(model_name=model_name)

        # Temporal Embodied Knowledge Graph (TEKG)
        # We store it as a dict mapping node ID to its properties and relations
        self.tekg: Dict[int, Dict[str, Any]] = {}

    def _update_tekg(self, obs: dict):
        """
        Updates the TEKG with the current observations.
        Resolves simple contradictions by overwriting old states.
        """
        nodes = obs.get('nodes', [])
        edges = obs.get('edges', [])

        # Update node states and properties
        for node in nodes:
            node_id = node['id']
            if node_id not in self.tekg:
                self.tekg[node_id] = {
                    'class_name': node['class_name'],
                    'states': [],
                    'properties': [],
                    'relations': []
                }

            # Overwrite with latest states/properties
            self.tekg[node_id]['states'] = node.get('states', [])
            self.tekg[node_id]['properties'] = node.get('properties', [])
            self.tekg[node_id]['relations'] = [] # Reset relations to update from current edges

        # Update edges
        for edge in edges:
            from_id = edge['from_id']
            to_id = edge['to_id']
            rel_type = edge.get('relation_type', edge.get('relation', ''))

            if from_id in self.tekg:
                to_class = next((n['class_name'] for n in nodes if n['id'] == to_id), f"Node_{to_id}")
                self.tekg[from_id]['relations'].append((rel_type, to_id, to_class))

    def _format_tekg_for_prompt(self) -> str:
        """
        Formats the current TEKG into a string for the LLM.
        """
        lines = []
        for node_id, data in self.tekg.items():
            class_name = data['class_name']
            states = data['states']
            relations = data['relations']

            state_str = f" States: {states}" if states else ""
            rel_str = f" Relations: {[(r[0], r[2]) for r in relations]}" if relations else ""

            lines.append(f"- {class_name}({node_id}){state_str}{rel_str}")

        return "\n".join(lines)

    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        """
        Main decision loop.
        """
        env_info = env_info or {}
        goal = config.get("goal_instruction", "").strip()

        if not goal:
            return "done()"

        # 1. Update Memory (TEKG)
        self._update_tekg(obs)

        # 2. Extract context
        tekg_context = self._format_tekg_for_prompt()
        print(f"[DEBUG TEKG] {tekg_context}")
        action_history = env_info.get("action_history", [])
        recent_actions = [h['action'] for h in action_history[-5:]] if action_history else []

        # 3. LLM Query for Exploration-Integrated Task Planning
        # We combine exploration and exploitation into a single prompt for speed.
        system_prompt = (
            "You are an embodied agent controlling a character in a household environment.\n"
            "You follow the ExRAP (Exploratory Retrieval-Augmented Planning) principles.\n"
            "Your task is to balance EXPLORATION (finding objects/rooms needed for the goal) "
            "and EXPLOITATION (executing task actions when conditions are met).\n"
            "Available primitive actions:\n"
            "- [walk] <object/room> (id)\n"
            "- [grab] <object> (id)\n"
            "- [putin] <object> (id) <receptacle> (id)\n"
            "- [putback] <object> (id) <receptacle> (id)\n"
            "- [switchon] / [switchoff] <object> (id)\n"
            "- [open] / [close] <object> (id)\n\n"
            "Rules:\n"
            "1. Output exactly ONE action.\n"
            "2. If you lack information to execute the goal, prioritize exploring (e.g., [walk] to different rooms).\n"
            "3. If conditions are met in your knowledge graph, execute the task action.\n"
            "4. Do not repeat recent actions fruitlessly.\n"
            "5. CRITICAL: You MUST ONLY use the object names and numerical IDs exactly as listed in the TEKG. Do NOT invent IDs.\n"
            "6. CRITICAL FORMAT: The object name MUST be surrounded by angle brackets, and the ID MUST be surrounded by parentheses. Examples:\n"
            "   CORRECT: [walk] <livingroom> (183)\n"
            "   CORRECT: [switchon] <tv> (238)\n"
            "   INCORRECT: [walk] livingroom (183)\n"
            "7. If you are already in a room, do NOT [walk] to that room again. Directly [walk] to the target object.\n"
            "8. To interact with an object (e.g. switchon, open, grab), you MUST first [walk] directly to that exact object."
        )

        user_prompt = (
            f"Goal: {goal}\n\n"
            f"Recent Actions:\n{recent_actions}\n\n"
            f"Current Knowledge (TEKG):\n{tekg_context}\n\n"
            "Analyze the situation. What is the most valuable next action?\n"
            "Provide your reasoning, then output the action on a new line starting with the action format, e.g., '[walk] <livingroom> (1)'."
        )

        try:
            response = self.llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            # Extract action
            for line in response.split('\n')[::-1]:
                line = line.strip()
                if line.startswith('['):
                    return line

            # Fallback regex
            match = re.search(r'\[\w+\].*', response)
            if match:
                return match.group(0).strip()

            return "[walk] <livingroom> (1)" # Safe fallback

        except Exception as e:
            print(f"[ExRAP Error] LLM generation failed: {e}")
            return "[walk] <livingroom> (1)"
