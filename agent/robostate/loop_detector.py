"""Small deterministic loop detector used before issuing an action."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LoopDetection:
    detected: bool
    reason: Optional[str] = None


class LoopDetector:
    @staticmethod
    def check(candidate: str, action_history: list) -> LoopDetection:
        action = LoopDetector._canonical(candidate)
        recent = [
            LoopDetector._canonical(item.get("action", ""))
            for item in action_history[-11:]
        ]

        if action == "[wait]":
            return LoopDetection(False)

        if len(recent) >= 2 and action and recent[-2:] == [action, action]:
            return LoopDetection(True, "same action would be issued three times")

        sequence = recent + [action]
        if len(sequence) >= 5 and sequence[-5] == sequence[-3] == sequence[-1]:
            if sequence[-4] == sequence[-2]:
                return LoopDetection(True, "two-action cycle detected")

        failures = [item for item in action_history[-3:] if not item.get("success", True)]
        if len(failures) >= 2:
            last_actions = {
                LoopDetector._canonical(item.get("action", "")) for item in failures[-2:]
            }
            last_errors = {str(item.get("error", "")) for item in failures[-2:]}
            if action in last_actions and len(last_errors) == 1:
                return LoopDetection(True, "same failed action and error repeated")

        return LoopDetection(False)

    @staticmethod
    def _canonical(action: str) -> str:
        return " ".join(str(action or "").strip().lower().split())
