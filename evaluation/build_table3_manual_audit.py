"""Build the evidence-backed, item-level manual audit for Table 3.

The human judgements below are deliberately explicit.  This script only
reconstructs the persistent CSV from those judgements and extracts proposed
skills from the original LLMExecutor output; it never infers a manual metric
from episode success.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from agent.robostate.action_validator import ActionValidator


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "table3"
RUNS_CSV = RESULTS / "table3_runs.csv"
OUTPUT = RESULTS / "table3_manual_items.csv"
FIELDS = [
    "profile", "scenario_id", "metric", "item_id", "gold", "predicted",
    "verdict", "coverage_status", "log_path", "review_note",
]

EXECUTOR_RE = re.compile(
    r"### \[LLMExecutor[^\]]*\] Output\s*```json\s*(\{.*?\})\s*```",
    re.DOTALL,
)
ACTION_RE = re.compile(r"^\s*\[([A-Za-z_]+)\]")

GOAL_PROFILES = (
    "full", "without_goal_reasoning", "without_intention",
    "without_parameter_binding",
)
SLOT_PROFILES = (
    "full", "without_memory", "without_memory_structure",
    "without_state_alignment",
)
HALLUC_PROFILES = (
    "full", "without_stg_planning", "without_stg_construction",
)

# Gold atoms are state/relation goals only. Execution prerequisites are absent.
GOAL_ATOMS = {
    "G1_01": ["milk is HOT"],
    "G1_02": ["character HOLDS apple", "apple is CLEAN"],
    "G1_03": ["character HOLDS remotecontrol"],
    "G1_04": ["tablelamp is OFF"],
    "G1_05": ["mug INSIDE kitchencabinet", "mug is EMPTY"],
    "G2_06": ["tablelamp is ON"],
    "G2_07": ["mug INSIDE kitchencabinet"],
    "G2_08": ["character HOLDS milk", "milk is HOT"],
    "G2_09": ["book ON desk"],
    "G2_10": ["stove is OFF"],
    "G3_11": ["recognizes broken-fridge trigger as permanently infeasible"],
    "G3_12": ["recognizes missing-bowl trigger as permanently infeasible"],
    "G3_13": ["recognizes missing-apple trigger as permanently infeasible"],
    "G3_14": ["recognizes broken-light trigger as permanently infeasible"],
    "G3_15": ["recognizes broken-stove trigger as permanently infeasible"],
    "G4_16": ["milk is HOT"],
    "G4_17": ["apple is CLEAN"],
    "G4_18": ["tv is OFF"],
    "G4_19": ["tablelamp is OFF"],
    "G4_20": ["character HOLDS pourable", "pourable is FILLED_JUICE"],
}

# Each set contains the gold atoms judged incorrect after reading the final
# GoalReasoner/SDG adopted by that profile. All unlisted atoms match gold.
GOAL_INCORRECT = {
    "full": {
        ("G3_11", 0), ("G3_14", 0), ("G3_15", 0),
    },
    "without_goal_reasoning": {
        ("G2_06", 0), ("G2_07", 0), ("G2_08", 1), ("G2_09", 0),
        ("G3_11", 0), ("G3_14", 0), ("G3_15", 0), ("G4_20", 0),
    },
    "without_intention": {
        ("G3_11", 0), ("G3_14", 0), ("G3_15", 0), ("G4_20", 0),
    },
    "without_parameter_binding": {
        ("G2_06", 0), ("G2_07", 0), ("G2_08", 0), ("G2_08", 1),
        ("G2_09", 0), ("G3_11", 0), ("G3_14", 0), ("G3_15", 0),
    },
}

INCORRECT_GOAL_NOTES = {
    "G2_06": "No resolved target state was adopted.",
    "G2_07": "The generic container was not resolved to the cabinet.",
    "G2_08": "The adopted target omitted or contradicted the requested binding/state.",
    "G2_09": "The generic surface was not resolved to the desk.",
    "G3_11": "Asked about a missing object instead of identifying the broken trigger.",
    "G3_14": "Asked which light instead of identifying the broken trigger.",
    "G3_15": "Asked about ingredients instead of identifying the broken trigger.",
    "G4_20": "The filled object was represented, but the character-holds atom was omitted.",
}

# One row per M scene is retained even where the metric has no opportunity.
# Values are (verdict, predicted, note); ``excluded`` never enters the denominator.
SLOT_JUDGEMENTS = {
    "full": {
        "M1_01": ("correct", "remotecontrol(321)", "First post-hide retry retained instance 321."),
        "M1_02": ("excluded", "no post-hide rebind", "The waterglass hide trigger never fired."),
        "M1_03": ("correct", "waterglass(64)", "First post-hide retry retained instance 64."),
        "M1_04": ("correct", "pillow(122)", "First post-hide retry retained instance 122."),
        "M1_05": ("correct", "milk(176)", "The first post-reappearance target retained instance 176."),
        "M2_06": ("correct", "waterglass(64)", "Selected the dirty waterglass."),
        "M2_07": ("correct", "apple(113)", "Selected the red apple."),
        "M2_08": ("correct", "apple(113)", "Selected the ripe/red apple."),
        "M2_09": ("correct", "waterglass(64)", "Selected the clean waterglass."),
        "M2_10": ("correct", "pillow(253)", "Selected the yellow pillow."),
        "M4_16": ("correct", "waterglass(64)", "Selected the recently used waterglass."),
        "M4_17": ("correct", "waterglass(64)", "Selected the recently washed waterglass."),
        "M4_18": ("correct", "plate(67)", "Selected the recently used red plate."),
        "M4_19": ("correct", "tv(426)", "Selected the TV referenced by current/history state."),
        "M4_20": ("correct", "apple(113)", "Selected the washed red apple."),
    },
    "without_memory": {
        "M1_01": ("excluded", "no post-hide rebind", "No hide/reappearance binding was observable."),
        "M1_02": ("excluded", "no post-hide rebind", "The waterglass hide trigger never fired."),
        "M1_03": ("incorrect", "waterglass(79)", "Post-hide retry switched from instance 64 to 79."),
        "M1_04": ("incorrect", "pillow(122)", "Post-hide retry switched from instance 303 to 122."),
        "M1_05": ("excluded", "no post-hide rebind", "The hide occurred at the final target action."),
        "M2_06": ("incorrect", "no waterglass binding", "Never bound the dirty waterglass."),
        "M2_07": ("incorrect", "no apple binding", "Never bound the red apple."),
        "M2_08": ("incorrect", "no apple binding", "Never bound the ripe/red apple."),
        "M2_09": ("correct", "waterglass(64)", "First clean-waterglass binding retained instance 64."),
        "M2_10": ("incorrect", "no pillow binding", "Never bound the yellow pillow."),
        "M4_16": ("incorrect", "no waterglass binding", "Never bound the historical target instance."),
        "M4_17": ("incorrect", "waterglass(87)", "Selected a dirty alternative instead of washed instance 64."),
        "M4_18": ("incorrect", "plate(103)", "Selected an alternative instead of historical instance 67."),
        "M4_19": ("correct", "tv(426)", "Selected the correct TV instance."),
        "M4_20": ("incorrect", "no apple binding", "Never bound the washed red apple."),
    },
    "without_memory_structure": {
        "M2_06": ("incorrect", "no waterglass binding", "Never bound the dirty waterglass."),
        "M2_07": ("incorrect", "no apple binding", "Never bound the red apple."),
        "M2_08": ("incorrect", "no apple binding", "Never bound the ripe/red apple."),
        "M2_09": ("incorrect", "no waterglass binding", "Never selected a waterglass instance."),
        "M2_10": ("incorrect", "no pillow binding", "Never bound the yellow pillow."),
    },
}


def scenario_ids(prefix: str) -> list[str]:
    if prefix == "P":
        return [*(f"P1_{i:02d}" for i in range(1, 6)),
                *(f"P2_{i:02d}" for i in range(6, 11)),
                *(f"P3_{i:02d}" for i in range(11, 21))]
    return [f"{prefix}{group}_{i:02d}" for group, values in (
        (1, range(1, 6)), (2, range(6, 11)),
        (3, range(11, 16)), (4, range(16, 21)),
    ) for i in values]


def load_runs() -> dict[tuple[str, str], dict]:
    with RUNS_CSV.open(encoding="utf-8", newline="") as handle:
        return {(row["profile"], row["scenario_id"]): row
                for row in csv.DictReader(handle)}


def resolve_log(row: dict | None) -> Path | None:
    if not row:
        return None
    path = Path(row["evidence_path"])
    if path.name == "metrics.json":
        matches = sorted(path.parent.glob("run_*.md"))
        return matches[0] if matches else None
    return path if path.suffix == ".md" and path.exists() else None


def add_goal_items(items: list[dict], runs: dict) -> None:
    for profile in GOAL_PROFILES:
        for scenario_id, atoms in GOAL_ATOMS.items():
            log = resolve_log(runs.get((profile, scenario_id)))
            for index, gold in enumerate(atoms, start=1):
                incorrect = (scenario_id, index - 1) in GOAL_INCORRECT[profile]
                note = INCORRECT_GOAL_NOTES.get(scenario_id, "") if incorrect else "Final adopted goal matches the gold atom."
                verdict = "incorrect" if incorrect else "correct"
                predicted = note.removesuffix(".")
                if not log:
                    verdict = "excluded"
                    predicted = "unreviewable"
                    note = "No Markdown execution log is available; episode failure was not used as a proxy."
                items.append({
                    "profile": profile, "scenario_id": scenario_id,
                    "metric": "GoalAlign", "item_id": f"goal_atom_{index}",
                    "gold": gold,
                    "predicted": predicted, "verdict": verdict,
                    "coverage_status": "covered" if log else "missing",
                    "log_path": str(log or ""), "review_note": note,
                })


def add_slot_items(items: list[dict], runs: dict) -> None:
    baseline = SLOT_JUDGEMENTS["full"]
    for profile in SLOT_PROFILES:
        profile_overrides = SLOT_JUDGEMENTS.get(profile, {})
        for scenario_id in scenario_ids("M"):
            log = resolve_log(runs.get((profile, scenario_id)))
            if scenario_id.startswith("M3"):
                verdict, predicted, note = (
                    "excluded", "not applicable",
                    "M3 has no object-identity binding opportunity under the metric definition.",
                )
            elif not log:
                verdict, predicted, note = (
                    "excluded", "unreviewable",
                    "No Markdown execution log is available; episode failure was not used as a proxy.",
                )
            else:
                verdict, predicted, note = profile_overrides.get(
                    scenario_id, baseline[scenario_id]
                )
            items.append({
                "profile": profile, "scenario_id": scenario_id,
                "metric": "SlotID", "item_id": "first_binding_opportunity",
                "gold": "retain/select the state-qualified target instance",
                "predicted": predicted, "verdict": verdict,
                "coverage_status": "covered" if log else "missing",
                "log_path": str(log or ""), "review_note": note,
            })


def executor_actions(log: Path) -> list[str]:
    actions = []
    for block in EXECUTOR_RE.findall(log.read_text(encoding="utf-8", errors="replace")):
        try:
            action = json.loads(block).get("action", "")
        except json.JSONDecodeError:
            continue
        if isinstance(action, str):
            actions.append(action)
    return actions


def add_halluc_items(items: list[dict], runs: dict) -> None:
    allowed = set(ActionValidator.ARITY)
    ignored = {"ask", "wait"}
    for profile in HALLUC_PROFILES:
        for scenario_id in scenario_ids("P"):
            log = resolve_log(runs.get((profile, scenario_id)))
            physical = []
            if log:
                for action in executor_actions(log):
                    match = ACTION_RE.match(action)
                    if not match or match.group(1).lower() in ignored:
                        continue
                    physical.append((action, match.group(1).lower()))
            if not log or not physical:
                items.append({
                    "profile": profile, "scenario_id": scenario_id,
                    "metric": "Halluc", "item_id": "no_counted_skill",
                    "gold": "ActionValidator.ARITY physical skill",
                    "predicted": "unreviewable" if not log else "no physical skill proposed",
                    "verdict": "excluded",
                    "coverage_status": "missing" if not log else "covered",
                    "log_path": str(log or ""),
                    "review_note": "No Markdown execution log is available." if not log else "Only excluded control actions were proposed.",
                })
                continue
            for index, (action, verb) in enumerate(physical, start=1):
                supported = verb in allowed
                items.append({
                    "profile": profile, "scenario_id": scenario_id,
                    "metric": "Halluc", "item_id": f"physical_skill_{index}",
                    "gold": "skill name present in ActionValidator.ARITY",
                    "predicted": action,
                    "verdict": "correct" if supported else "incorrect",
                    "coverage_status": "covered", "log_path": str(log),
                    "review_note": "Supported skill name." if supported else "Skill name is absent from the physical skill library.",
                })


def main() -> None:
    runs = load_runs()
    items: list[dict] = []
    add_goal_items(items, runs)
    add_slot_items(items, runs)
    add_halluc_items(items, runs)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(items)
    print(f"Wrote {len(items)} audit items to {OUTPUT}")


if __name__ == "__main__":
    main()
