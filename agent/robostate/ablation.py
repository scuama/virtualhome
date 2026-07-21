"""Table 3 ablation switches for RoboState.

The policy is deliberately small: existing modules keep their normal public
interfaces and only change the information or prompt supplied at the ablated
boundary.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AblationPolicy:
    profile: str
    goal_reasoning: bool = True
    intention: bool = True
    parameter_binding: bool = True
    memory: bool = True
    memory_structure: bool = True
    state_alignment: bool = True
    stg_planning: bool = True
    stg_construction: bool = True
    path_merging: bool = True


PROFILES = {
    "full": AblationPolicy("full"),
    "without_goal_reasoning": AblationPolicy(
        "without_goal_reasoning", goal_reasoning=False,
        intention=False, parameter_binding=False,
    ),
    "without_intention": AblationPolicy(
        "without_intention", intention=False,
    ),
    "without_parameter_binding": AblationPolicy(
        "without_parameter_binding", parameter_binding=False,
    ),
    "without_memory": AblationPolicy(
        "without_memory", memory=False, memory_structure=False,
        state_alignment=False,
    ),
    "without_memory_structure": AblationPolicy(
        "without_memory_structure", memory_structure=False,
    ),
    "without_state_alignment": AblationPolicy(
        "without_state_alignment", state_alignment=False,
    ),
    "without_stg_planning": AblationPolicy(
        "without_stg_planning", stg_planning=False,
        stg_construction=False, path_merging=False,
    ),
    "without_stg_construction": AblationPolicy(
        "without_stg_construction", stg_construction=False,
    ),
    "without_path_merging": AblationPolicy(
        "without_path_merging", path_merging=False,
    ),
}


def get_ablation_policy(profile: str = "full") -> AblationPolicy:
    normalized = str(profile or "full").strip().lower()
    if normalized not in PROFILES:
        raise ValueError(
            f"Unknown RoboState ablation profile {profile!r}; "
            f"expected one of {sorted(PROFILES)}"
        )
    return PROFILES[normalized]
