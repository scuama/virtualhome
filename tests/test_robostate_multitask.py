import unittest
from unittest.mock import patch
import re

from agent.robostate_agent import RoboStateAgent
from agent.robostate.action_validator import ActionValidator
from agent.robostate.exploration import RoomFrontierExplorer
from agent.robostate.loop_detector import LoopDetector
from agent.robostate.task_manager import MultiTaskManager
from evaluation.task_progress import TaskProgressTracker
from evaluation.test_runner import apply_overrides


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

    def test_scheduler_uses_evaluator_progress_and_reopens_regression(self):
        manager = MultiTaskManager(self.config)
        manager.update_progress(
            [
                {"task_id": "book_task", "currently_satisfied": False},
                {"task_id": "computer_task", "currently_satisfied": False},
            ],
            0,
        )
        manager.refresh_graph_classes(self.graph)
        self.assertEqual(manager.select_task(self.graph, 0).task_id, "book_task")

        manager.update_progress(
            [
                {"task_id": "book_task", "currently_satisfied": True},
                {"task_id": "computer_task", "currently_satisfied": False},
            ],
            1,
        )
        self.assertEqual(manager.select_task(self.graph, 1).task_id, "computer_task")

        manager.update_progress(
            [
                {"task_id": "book_task", "currently_satisfied": False},
                {"task_id": "computer_task", "currently_satisfied": False},
            ],
            2,
        )
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
        self.assertNotIn("success_condition", tracker.as_env_info()[0])


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
