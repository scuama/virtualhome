import unittest
from unittest.mock import patch
import json
from pathlib import Path
import re

from agent.robostate_agent import RoboStateAgent
from agent.robostate.action_validator import ActionValidator
from agent.robostate.exploration import RoomFrontierExplorer
from agent.robostate.loop_detector import LoopDetector
from agent.robostate.task_manager import MultiTaskManager
from evaluation.runtime import (
    TaskProgressTracker,
    check_success,
    resolve_config_paths,
)
from evaluation.table2_configs import scene_grounding_candidates, validate_static
from evaluation.test_runner import (
    DynamicEventRuntime,
    apply_overrides,
    build_agent_config,
)
from virtualhome.simulation.environment.unity_environment import UnityEnvironment


def node(node_id, class_name, category="Objects", properties=None, states=None):
    return {
        "id": node_id,
        "class_name": class_name,
        "category": category,
        "properties": properties or [],
        "states": states or [],
    }


class FakeLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)

    def log_info(self, message):
        self.info(message)

    def log_error(self, message):
        self.error(message)

    def log_module_output(self, *args, **kwargs):
        return None


class FakeGoalReasoner:
    def __init__(self):
        self.instructions = []

    def extract_intent(self, instruction):
        self.instructions.append(instruction)
        return {"instruction": instruction}


class FakeSDGPlanner:
    def __init__(self):
        self.instructions = []

    def generate_sdg(self, instruction):
        self.instructions.append(instruction)
        return {
            "nodes": [
                {
                    "id": "N1",
                    "type": "Relation",
                    "object": "book",
                    "relation": "ON",
                    "target": "sofa",
                },
                {
                    "id": "N2",
                    "type": "Relation",
                    "object": "book",
                    "relation": "HELD",
                    "target": "agent",
                },
            ],
            "edges": [],
        }


class MultiTaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "scenario_id": "multi",
            "goal_instruction": "Do two tasks",
            "tasks": [
                {"task_id": "book_task", "instruction": "Put the book on the sofa."},
                {"task_id": "computer_task", "instruction": "Turn on the computer."},
            ],
        }
        self.graph = {
            "nodes": [
                node(1, "character"),
                node(2, "book", properties=["GRABBABLE"]),
                node(10, "kitchen", category="Rooms"),
            ],
            "edges": [],
        }

    def test_scheduler_uses_evaluator_booleans_and_reopens_regression(self):
        manager = MultiTaskManager(self.config)
        manager.update_progress([
            {"task_id": "book_task", "currently_satisfied": False},
            {"task_id": "computer_task", "currently_satisfied": False},
        ], 0)
        manager.refresh_graph_classes(self.graph)
        self.assertEqual(manager.select_task(self.graph, 0).task_id, "book_task")
        manager.update_progress([
            {"task_id": "book_task", "currently_satisfied": True},
            {"task_id": "computer_task", "currently_satisfied": False},
        ], 1)
        self.assertEqual(manager.select_task(self.graph, 1).task_id, "computer_task")
        manager.update_progress([
            {"task_id": "book_task", "currently_satisfied": False},
            {"task_id": "computer_task", "currently_satisfied": False},
        ], 2)
        reopened = manager.get("book_task")
        self.assertEqual(reopened.status, "pending")
        self.assertFalse(reopened.currently_satisfied)

    def test_each_task_gets_its_own_lazy_plan(self):
        manager = MultiTaskManager(self.config)
        reasoner = FakeGoalReasoner()
        planner = FakeSDGPlanner()
        task = manager.select_task(self.graph, 0)
        manager.ensure_plan(task, reasoner, planner)

        self.assertEqual(reasoner.instructions, ["Put the book on the sofa."])
        self.assertEqual(planner.instructions, ["Put the book on the sofa."])
        self.assertEqual(task.required_classes, {"book", "sofa"})

    def test_sdg_requirements_are_limited_to_public_scene_catalog(self):
        config = dict(self.config, grounding_candidates=["book", "sofa", "computer"])
        manager = MultiTaskManager(config)
        task = manager.select_task(self.graph, 0)
        task.sdg = {
            "nodes": [
                {"id": "N1", "object": "book", "target": "sofa"},
                {"id": "N2", "object": "drying", "target": "person"},
            ]
        }
        manager._extract_required_classes(task)
        self.assertEqual(task.required_classes, {"book", "sofa"})


class TaskProgressTrackerTests(unittest.TestCase):
    def test_current_satisfaction_can_regress_but_first_step_is_retained(self):
        tracker = TaskProgressTracker(
            {
                "scenario_id": "one",
                "goal_instruction": "Switch it on",
                "success_condition": {"marker": "done"},
            }
        )

        def check(graph, condition):
            return graph.get("marker") == condition.get("marker")

        tracker.update({"marker": "done"}, 3, check)
        tracker.update({"marker": "undone"}, 4, check)
        metrics = tracker.as_metrics()

        self.assertEqual(metrics["task_completed"], 0)
        self.assertEqual(metrics["tasks"][0]["first_satisfied_step"], 3)
        self.assertTrue(metrics["tasks"][0]["ever_satisfied"])
        self.assertFalse(metrics["tasks"][0]["currently_satisfied"])
        self.assertNotIn("success_condition", tracker.as_log_info()[0])
        self.assertNotIn("instruction", tracker.as_log_info()[0])
        self.assertEqual(tracker.as_agent_info(), [{
            "task_id": "task_1", "currently_satisfied": False
        }])


class SummarizedInstructionTests(unittest.TestCase):
    def test_decomposition_retries_and_returns_three_tasks(self):
        class RetryLLM:
            def __init__(self):
                self.calls = 0

            def generate_json(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return {"tasks": ["only one"]}
                return {"tasks": ["Turn on the computer.", "Move the book.", "Place the mug."]}

        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.llm = RetryLLM()
        agent.logger = FakeLogger()
        tasks = agent._decompose_summarized_instruction("Maintain the room.", 3)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(agent.llm.calls, 2)

    def test_decomposition_never_falls_back_to_evaluator_text(self):
        class InvalidLLM:
            def generate_json(self, *args, **kwargs):
                return {"tasks": []}

        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.llm = InvalidLLM()
        agent.logger = FakeLogger()
        with self.assertRaisesRegex(ValueError, "InstructionDecompositionError"):
            agent._decompose_summarized_instruction("Maintain the room.", 3)

    def test_vague_tasks_are_grounded_against_scene_candidates(self):
        class GroundingLLM:
            def generate_json(self, *args, **kwargs):
                return {"tasks": ["Turn on the computer.", "Move the book to the sofa."]}

        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.llm = GroundingLLM()
        agent.logger = FakeLogger()
        grounded = agent._ground_vague_instructions({
            "tasks": [
                {"instruction": "Turn on the workstation device."},
                {"instruction": "Move reading material to the sitting place."},
            ],
            "grounding_candidates": ["computer", "book", "sofa", "chair"],
        })
        self.assertEqual(grounded, [
            "Turn on the computer.", "Move the book to the sofa."
        ])


class IntervalDynamicEventTests(unittest.TestCase):
    def test_interval_event_changes_state_only_on_schedule(self):
        class Env:
            def __init__(self):
                self.custom_states = {}
                self.changed_graph = False

            def get_graph(self):
                result = {
                    "nodes": [
                        node(2, "computer", states=["ON"]),
                        node(3, "computer", states=["ON"]),
                        node(4, "computer", states=["OFF"]),
                    ],
                    "edges": [],
                }
                for item in result["nodes"]:
                    additions = self.custom_states.get(item["id"], set())
                    removals = self.custom_removed_states.get(item["id"], set())
                    item["states"] = list(
                        (set(item["states"]) - removals) | additions
                    )
                return result

            custom_removed_states = {}

        env = Env()
        runtime = DynamicEventRuntime(env, [{
            "event_id": "off",
            "trigger": {"type": "step_interval", "interval_steps": 4, "start_step": 4},
            "effect": {
                "type": "set_state", "target": "computer",
                "match_states": ["ON"], "apply_to": "all_matching",
                "add_states": ["OFF"], "remove_states": ["ON"],
            },
        }], FakeLogger())
        runtime.before_step(3)
        self.assertEqual(env.custom_states, {})
        self.assertTrue(runtime.before_step(4))
        self.assertEqual(env.custom_states[2], {"OFF"})
        self.assertEqual(env.custom_states[3], {"OFF"})
        self.assertNotIn(4, env.custom_states)
        self.assertFalse(runtime.before_step(4))
        self.assertEqual(runtime.event_counts()["off"]["times_triggered"], 1)
        runtime.before_step(8)
        self.assertEqual(runtime.event_counts()["off"]["times_triggered"], 1)


class GeneratedExperimentConfigTests(unittest.TestCase):
    AXIS_DIRS = ("scale", "non_stationarity", "instruction_type")

    def test_five_groups_cover_all_three_experiment_axes(self):
        root = Path(__file__).resolve().parents[1] / "evaluation" / "configs"
        expected = {"scale": 15, "non_stationarity": 15, "instruction_type": 15}
        observed = {key: [] for key in expected}
        for directory in self.AXIS_DIRS:
            for path in (root / "table2" / directory).glob("*.json"):
                payload = json.loads(path.read_text())
                axis = payload.get("experiment_axis")
                if axis in observed:
                    observed[axis].append(payload)
        self.assertEqual({key: len(value) for key, value in observed.items()}, expected)
        for payloads in observed.values():
            self.assertEqual({item["group_id"] for item in payloads}, {
                "G01", "G02", "G03", "G04", "G05"
            })
            for payload in payloads:
                self.assertEqual(len(payload["tasks"]), payload["instruction_scale"])

        scale_by_group = {}
        for payload in observed["scale"]:
            scale_by_group.setdefault(payload["group_id"], {})[
                payload["instruction_scale"]
            ] = payload["source_scenarios"]
        for scales in scale_by_group.values():
            self.assertEqual(scales[5][:3], scales[3])
            self.assertEqual(scales[7][:5], scales[5])

    def test_vague_candidates_are_complete_scene_catalogs(self):
        root = (
            Path(__file__).resolve().parents[1]
            / "evaluation" / "configs" / "table2" / "instruction_type"
        )
        for path in root.glob("E_SEM_G*_S3_vague.json"):
            payload = json.loads(path.read_text())
            expected = scene_grounding_candidates(payload["environment_id"])
            self.assertEqual(payload["grounding_candidates"], expected)
            self.assertGreater(len(expected), 70)

    def test_every_extension_config_uses_the_complete_scene_catalog(self):
        root = Path(__file__).resolve().parents[1] / "evaluation" / "configs"
        for directory in self.AXIS_DIRS:
            for path in (root / "table2" / directory).glob("*.json"):
                payload = json.loads(path.read_text())
                self.assertEqual(
                    payload["grounding_candidates"],
                    scene_grounding_candidates(payload["environment_id"]),
                    path.name,
                )

    def test_configs_use_semantic_matching_without_hidden_ordinals(self):
        root = Path(__file__).resolve().parents[1] / "evaluation" / "configs"
        forbidden = {
            "target_instance", "destination_instance", "subject_instance",
            "object_instance", "instance_index", "instance_filter",
        }

        def mappings(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from mappings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from mappings(child)

        for directory in self.AXIS_DIRS:
            for path in (root / "table2" / directory).glob("*.json"):
                payload = json.loads(path.read_text())
                for mapping in mappings(payload):
                    self.assertFalse(forbidden.intersection(mapping), path.name)

    def test_static_preflight_accepts_all_45_configs(self):
        self.assertEqual(len(validate_static()), 45)


class ConfigResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1] / "evaluation" / "configs"

    def test_directory_counts_match_named_suites(self):
        self.assertEqual(len(resolve_config_paths([self.root / "table1"])), 57)
        self.assertEqual(len(resolve_config_paths([self.root / "table2"])), 45)
        self.assertEqual(
            len(resolve_config_paths([self.root / "source_tasks"])), 79
        )

    def test_single_file_and_overlapping_directory_are_deduplicated(self):
        config = self.root / "table2" / "scale" / "E_MULTI_G01_S3.json"
        resolved = resolve_config_paths([config, config.parent])
        self.assertEqual(len(resolved), 15)
        self.assertEqual(
            sum(item[0] == "E_MULTI_G01_S3" for item in resolved), 1
        )

    def test_explicit_manifest_is_rejected_as_non_runnable(self):
        manifest = self.root / "table1" / "manifest.json"
        with self.assertRaisesRegex(ValueError, "Not a runnable"):
            resolve_config_paths([manifest])


class PersistentStateOverlayTests(unittest.TestCase):
    def test_later_action_replaces_initial_state_overlay(self):
        class Comm:
            def environment_graph(self):
                return True, {
                    "nodes": [node(2, "dishwasher", states=["CLOSED"])],
                    "edges": [],
                }

        env = UnityEnvironment.__new__(UnityEnvironment)
        env.comm = Comm()
        env.changed_graph = True
        env.custom_states = {}
        env.custom_removed_states = {}
        env.set_state_override(2, ["CLOSED"], ["OPEN"])
        self.assertIn("CLOSED", env.get_graph()["nodes"][0]["states"])
        env.set_state_override(2, ["OPEN"], ["CLOSED"])
        states = set(env.get_graph()["nodes"][0]["states"])
        self.assertIn("OPEN", states)
        self.assertNotIn("CLOSED", states)


class ProtocolIsolationTests(unittest.TestCase):
    def test_agent_config_is_strict_allowlist_and_uses_neutral_task_ids(self):
        private = {
            "scenario_id": "secret",
            "goal_instruction": "Do it.",
            "instruction_type": "sentence_wise",
            "tasks": [{
                "task_id": "E1_11",
                "instruction": "Turn on the computer.",
                "success_condition": {"target_class": "computer", "states": ["ON"]},
            }],
            "success_condition": {"mode": "AND"},
            "dynamic_events": [{"target": "computer"}],
            "source_scenarios": ["E1_11"],
            "dynamic_difficulty": "high",
            "environment_id": 2,
        }
        public = build_agent_config(private)
        self.assertEqual(public["tasks"], [{
            "task_id": "task_1", "instruction": "Turn on the computer."
        }])
        for key in (
            "success_condition", "dynamic_events", "source_scenarios",
            "dynamic_difficulty", "environment_id", "scenario_id",
        ):
            self.assertNotIn(key, public)

    def test_condition_checker_binds_target_and_destination_instances(self):
        graph = {
            "nodes": [node(2, "book"), node(3, "book"), node(4, "sofa"), node(5, "sofa")],
            "edges": [{"from_id": 3, "to_id": 5, "relation_type": "ON"}],
        }
        base = {
            "target_class": "book", "target_instance": 0,
            "relation": "ON", "destination_class": "sofa",
            "destination_instance": 0,
        }
        self.assertFalse(check_success(graph, base))
        bound_second = dict(base, target_instance=1, destination_instance=1)
        self.assertTrue(check_success(graph, bound_second))


class FakeInitializationEnvironment:
    def __init__(self):
        self.graph = {
            "nodes": [
                node(1, "character"),
                node(2, "book", properties=["GRABBABLE"]),
                node(3, "sofa", properties=["SURFACES"]),
                node(10, "kitchen", category="Rooms"),
            ],
            "edges": [],
        }
        self.actions = []
        self.active_hidden_nodes = {}
        self.changed_graph = False
        self.custom_states = {}

    def get_graph(self):
        return self.graph

    def step(self, action_by_agent):
        action = action_by_agent[0]
        self.actions.append(action)
        if action.startswith("[putback]"):
            object_ids = [int(value) for value in re.findall(r"\((\d+)\)", action)]
            self.graph["edges"] = [
                edge
                for edge in self.graph["edges"]
                if not (
                    edge.get("from_id") == object_ids[0]
                    and edge.get("relation_type") in {"ON", "INSIDE"}
                )
            ]
            self.graph["edges"].append(
                {
                    "from_id": object_ids[0],
                    "to_id": object_ids[1],
                    "relation_type": "ON",
                }
            )
        return {}, 0, False, {"action_success": True, "action_message": ""}


class InitializationOrderingTests(unittest.TestCase):
    def test_character_spawn_is_applied_after_object_placement(self):
        env = FakeInitializationEnvironment()
        apply_overrides(
            env,
            {
                "initial_relations_override": [
                    {"subject": "character", "object": "kitchen"},
                    {"subject": "book", "relation": "ON", "object": "sofa"},
                ]
            },
        )
        self.assertTrue(env.actions[-1].startswith("[walk] <kitchen>"))


class RoomFrontierExplorerTests(unittest.TestCase):
    def test_frontier_search_visits_unseen_room_instead_of_waiting(self):
        logger = FakeLogger()
        explorer = RoomFrontierExplorer(logger)
        graph = {
            "nodes": [
                node(1, "character"),
                node(10, "kitchen", category="Rooms"),
                node(20, "bedroom", category="Rooms"),
            ],
            "edges": [
                {"from_id": 1, "to_id": 10, "relation_type": "INSIDE"}
            ],
        }
        explorer.update(graph, 0)

        self.assertEqual(explorer.missing_classes({"closet"}, graph), {"closet"})
        self.assertEqual(explorer.next_action(0), "[walk] <bedroom> (20)")
        explorer.record_action("[walk] <bedroom> (20)", True, 0)
        self.assertEqual(explorer.current_room_id, 20)
        self.assertIsNone(explorer.next_action(1))
        self.assertEqual(explorer.next_action(1, revisit=True), "[walk] <kitchen> (10)")


class ActionValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = ActionValidator()
        self.graph = {
            "nodes": [
                node(1, "character"),
                node(2, "book", properties=["GRABBABLE"]),
                node(3, "sofa", properties=["SURFACES"]),
            ],
            "edges": [
                {"from_id": 1, "to_id": 2, "relation_type": "CLOSE"}
            ],
        }

    def test_rejects_unknown_and_mismatched_ids(self):
        result = self.validator.validate("[walk] <book> (999)", self.graph)
        self.assertFalse(result.valid)
        self.assertIn("unknown object id", result.reason)

        result = self.validator.validate("[walk] <sofa> (2)", self.graph)
        self.assertFalse(result.valid)
        self.assertIn("class/id mismatch", result.reason)

    def test_protects_satisfied_task_subject(self):
        result = self.validator.validate(
            "[grab] <book> (2)", self.graph, protected_classes={"book"}
        )
        self.assertFalse(result.valid)
        self.assertIn("satisfied task", result.reason)

    def test_repairs_missing_destination_proximity(self):
        self.graph["edges"].append(
            {"from_id": 1, "to_id": 2, "relation_type": "HOLDS_RH"}
        )
        result = self.validator.validate(
            "[putback] <book> (2) <sofa> (3)", self.graph
        )
        self.assertTrue(result.valid)
        self.assertTrue(result.repaired)
        self.assertEqual(result.action, "[walk] <sofa> (3)")

    def test_wait_requires_explicit_gate(self):
        self.assertFalse(self.validator.validate("[wait]", self.graph).valid)
        self.assertTrue(
            self.validator.validate("[wait]", self.graph, allow_wait=True).valid
        )


class LoopDetectorTests(unittest.TestCase):
    def test_detects_third_identical_action(self):
        history = [
            {"action": "[walk] <book> (2)", "success": True},
            {"action": "[walk] <book> (2)", "success": True},
        ]
        result = LoopDetector.check("[walk] <book> (2)", history)
        self.assertTrue(result.detected)


class FakeLLMClient:
    def __init__(self, model_name=None):
        self.sdg_prompts = []

    def generate_json(self, system_prompt, user_prompt, model_override=None):
        if "State Dependency Graph" not in system_prompt:
            return {"intent": user_prompt}
        self.sdg_prompts.append(user_prompt)
        if "computer" in user_prompt.lower():
            return {
                "nodes": [
                    {"id": "N1", "type": "State", "object": "computer", "value": "ON"}
                ],
                "edges": [],
            }
        return {
            "nodes": [
                {
                    "id": "N1", "type": "Relation", "object": "book",
                    "relation": "ON", "target": "sofa",
                }
            ],
            "edges": [],
        }

    def generate_response(
        self, system_prompt, user_prompt, response_format="text", model_override=None
    ):
        if "Execution Engine" in system_prompt:
            if "computer_task" in user_prompt and '"active_task_id": "computer_task"' in user_prompt:
                return (
                    '{"reasoning":"turn it on","satisfied_nodes":[], '
                    '"current_node_focus":"N1","mapped_variables":{}, '
                    '"action":"[switchon] <computer> (4)"}'
                )
            return (
                '{"reasoning":"pick it up","satisfied_nodes":[], '
                '"current_node_focus":"N1","mapped_variables":{}, '
                '"action":"[grab] <book> (2)"}'
            )
        return '{"reasoning":"relevant","selected_classes":["book","sofa","computer"]}'


class RoboStateAgentIntegrationTests(unittest.TestCase):
    def test_agent_switches_between_independent_task_plans(self):
        config = {
            "scenario_id": "multi",
            "goal_instruction": "1. Put the book on the sofa. 2. Turn on the computer.",
            "tasks": [
                {"task_id": "book_task", "instruction": "Put the book on the sofa."},
                {"task_id": "computer_task", "instruction": "Turn on the computer."},
            ],
        }
        graph = {
            "nodes": [
                node(1, "character"),
                node(2, "book", properties=["GRABBABLE"]),
                node(3, "sofa", properties=["SURFACES"]),
                node(4, "computer", properties=["HAS_SWITCH"], states=["OFF"]),
                node(10, "kitchen", category="Rooms"),
            ],
            "edges": [
                {"from_id": 1, "to_id": 10, "relation_type": "INSIDE"},
                {"from_id": 1, "to_id": 2, "relation_type": "CLOSE"},
                {"from_id": 1, "to_id": 4, "relation_type": "CLOSE"},
            ],
        }
        logger = FakeLogger()
        with patch("agent.robostate_agent.LLMClient", FakeLLMClient):
            agent = RoboStateAgent("fake", "multi")

        first = agent.get_action(
            graph,
            config,
            {
                "step": 0,
                "logger": logger,
                "action_history": [],
                "task_progress": [
                    {"task_id": "book_task", "currently_satisfied": False},
                    {"task_id": "computer_task", "currently_satisfied": False},
                ],
            },
        )
        self.assertEqual(first, "[grab] <book> (2)")
        self.assertEqual(agent.last_decision["active_task_id"], "book_task")

        graph["edges"].append(
            {"from_id": 2, "to_id": 3, "relation_type": "ON"}
        )
        original_generate = agent.llm.generate_response

        def completed_book(system_prompt, user_prompt, **kwargs):
            if (
                "Execution Engine" in system_prompt
                and '"active_task_id": "book_task"' in user_prompt
            ):
                return (
                    '{"reasoning":"goal observed","satisfied_nodes":["N1"], '
                    '"current_node_focus":"N1","mapped_variables":{}, '
                    '"action":"[wait]"}'
                )
            return original_generate(system_prompt, user_prompt, **kwargs)

        agent.llm.generate_response = completed_book
        second = agent.get_action(
            graph,
            config,
            {
                "step": 1,
                "logger": logger,
                "action_history": [
                    {"step": 0, "action": first, "success": True}
                ],
                "task_progress": [
                    {"task_id": "book_task", "currently_satisfied": True},
                    {"task_id": "computer_task", "currently_satisfied": False},
                ],
            },
        )
        self.assertEqual(second, "[switchon] <computer> (4)")
        self.assertEqual(agent.last_decision["active_task_id"], "computer_task")
        self.assertEqual(len(agent.llm.sdg_prompts), 2)
        self.assertIn("Put the book on the sofa.", agent.llm.sdg_prompts[0])
        self.assertIn("Turn on the computer.", agent.llm.sdg_prompts[1])


if __name__ == "__main__":
    unittest.main()
