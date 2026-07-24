import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.robostate.ablation import get_ablation_policy
from agent.robostate.prompt_templates import GOAL_REASONER_SYSTEM_PROMPT
from agent.robostate.task_manager import MultiTaskManager
from agent.robostate_agent import RoboStateAgent
from evaluation import aggregate_table5
from evaluation.aggregate_table5 import aggregate
from evaluation.table5_configs import (
    BUDGETS,
    SCENARIOS,
    generate_all,
    validate,
)
from evaluation.test_runner import (
    SimulatedUser,
    build_agent_config,
    clarification_trace,
    table5_result_folder,
)


class Table5ConfigTests(unittest.TestCase):
    def test_exact_nine_by_four_matrix(self):
        runs, manifest = generate_all()
        validate(runs, manifest)
        self.assertEqual(len(runs), 36)
        self.assertEqual(len(SCENARIOS), 9)
        self.assertEqual(tuple(manifest["budgets"]), BUDGETS)
        self.assertEqual(
            {
                (config["source_scenario_id"], config["clarification_budget"])
                for _, config in runs
            },
            {(scenario, budget) for scenario in SCENARIOS for budget in BUDGETS},
        )

    def test_intent_is_evaluator_only_but_budget_is_public(self):
        config = generate_all()[0][0][1]
        public = build_agent_config(config)
        self.assertEqual(
            public["clarification_budget"], config["clarification_budget"]
        )
        self.assertNotIn("simulated_user_intent", public)
        self.assertNotIn("success_condition", public)

    def test_new_scenarios_use_supported_condition_fields(self):
        runs, _ = generate_all()
        new = {
            config["source_scenario_id"]: config
            for _, config in runs
            if config["source_scenario_id"].startswith("T5_")
            and config["clarification_budget"] == 0
        }
        self.assertEqual(new["T5_G2_12"]["success_condition"]["min_count"], 2)
        appliance = new["T5_G2_13"]["success_condition"]
        self.assertEqual(appliance["mode"], "AND")
        self.assertEqual(
            {item["target_class"] for item in appliance["conditions"]},
            {"toaster", "coffeemaker"},
        )

    def test_result_folder_separates_scenario_and_budget(self):
        path = table5_result_folder("/tmp/eval", {
            "source_scenario_id": "T5_G2_11",
            "clarification_budget": 2,
        }, "robostate")
        self.assertEqual(
            path, "/tmp/eval/results/table5/robostate/T5_G2_11/B2"
        )


class ClarificationBudgetTests(unittest.TestCase):
    def test_goal_reasoner_must_not_guess_proper_storage(self):
        self.assertIn(
            "DO NOT INFER A STORAGE DESTINATION",
            GOAL_REASONER_SYSTEM_PROMPT,
        )
        self.assertIn('"where it belongs"', GOAL_REASONER_SYSTEM_PROMPT)

    def test_budget_allows_two_successful_replies(self):
        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.clarification_budget = 2
        agent.clarifications_used = 0
        agent.table3_source_subclass = ""
        agent.ablation_policy = get_ablation_policy("full")
        self.assertTrue(agent._allow_ask())
        agent.clarifications_used = 1
        self.assertTrue(agent._allow_ask())
        agent.clarifications_used = 2
        self.assertFalse(agent._allow_ask())

    def test_budget_one_blocks_a_second_question(self):
        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.clarification_budget = 1
        agent.clarifications_used = 1
        agent.table3_source_subclass = ""
        agent.ablation_policy = get_ablation_policy("full")
        self.assertFalse(agent._allow_ask())

    def test_two_replies_revise_the_same_task_twice(self):
        class LLM:
            def generate_response(self, _system, user, **_kwargs):
                clarification = user.split("User clarification: ", 1)[1]
                return clarification.splitlines()[0].strip("'")

        manager = MultiTaskManager({
            "scenario_id": "two_turns",
            "goal_instruction": "Put it away properly.",
        })
        task = manager.tasks[0]
        manager.active_task_id = task.task_id
        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.llm = LLM()
        agent.task_manager = manager
        agent.clarifications_used = 0
        agent._processed_clarification_steps = set()
        agent._issued_task_by_step = {0: task.task_id, 1: task.task_id}

        agent.action_history = [{
            "step": 0,
            "action": "[ask] Which item?",
            "success": True,
            "message": "The mug.",
        }]
        agent._handle_clarification()
        self.assertEqual(agent.clarifications_used, 1)

        agent.action_history.append({
            "step": 1,
            "action": "[ask] Where?",
            "success": True,
            "message": "In the kitchen cabinet.",
        })
        agent._handle_clarification()
        self.assertEqual(agent.clarifications_used, 2)
        self.assertIn("kitchen cabinet", task.instruction)


class SimulatedUserTests(unittest.TestCase):
    def test_prompt_requests_only_first_information_need(self):
        class LLM:
            def __init__(self):
                self.system = ""
                self.user = ""
                self.kwargs = {}

            def generate_response(self, system, user, **kwargs):
                self.system = system
                self.user = user
                self.kwargs = kwargs
                return "Move all three books."

        llm = LLM()
        user = SimulatedUser(
            llm,
            "Put the books back neatly.",
            "Put all three books on the living-room desk.",
        )
        answer = user.answer(
            "Which books, and where should I put them?",
            [],
        )
        self.assertEqual(answer, "Move all three books.")
        self.assertIn("first information request", llm.system)
        self.assertIn(
            "For a destination question, answer only the destination phrase",
            llm.system,
        )
        self.assertIn("Do not name or describe the object", llm.system)
        self.assertIn(
            'answer "The juice.", never "The cold juice."',
            llm.system,
        )
        self.assertIn("Never invent specificity absent", llm.system)
        self.assertIn('"information_type"', llm.system)
        self.assertIn("living-room desk", llm.user)
        self.assertEqual(llm.kwargs["temperature"], 0.0)
        self.assertEqual(llm.kwargs["response_format"], "json_object")

    def test_exact_duplicate_answer_is_not_repeated(self):
        class LLM:
            def generate_response(self, *_args, **_kwargs):
                return json.dumps({
                    "information_type": "state",
                    "answer": "Turn it on.",
                })

        user = SimulatedUser(
            LLM(),
            "Adjust the lamp appropriately.",
            "Turn on the table lamp.",
        )
        answer = user.answer("What exact setting?", [{
            "step": 0,
            "action": "[ask] What state?",
            "success": True,
            "message": "Turn it on.",
        }])
        self.assertEqual(answer, "I have no additional preference.")

    def test_trace_counts_only_successful_answered_asks(self):
        history = [
            {
                "step": 0, "action": "[ask] Which one?", "success": True,
                "message": "The mug.",
            },
            {
                "step": 1, "action": "[ask] Where?", "success": False,
                "error": "budget exhausted",
            },
            {
                "step": 2, "action": "[ask] Where?", "success": True,
                "message": "",
            },
            {"step": 3, "action": "[walk] <mug> (1)", "success": True},
        ]
        self.assertEqual(len(clarification_trace(history)), 1)


class Table5AggregationTests(unittest.TestCase):
    def test_complete_matrix_uses_fixed_nine_scenario_denominator(self):
        _, manifest = generate_all()
        manifest["legacy_b1_candidates"] = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for source_id in SCENARIOS:
                for budget in BUDGETS:
                    folder = root / source_id / f"B{budget}"
                    folder.mkdir(parents=True)
                    (folder / "metrics.json").write_text(json.dumps({
                        "success": budget > 0,
                        "run_status": "complete",
                        "valid_for_aggregation": True,
                        "clarification_count": min(budget, 2),
                    }))
            with patch.object(aggregate_table5, "RESULTS", root):
                rows, run_rows, report = aggregate(manifest)
        self.assertTrue(report["complete"])
        self.assertEqual(len(run_rows), 36)
        self.assertTrue(all(row["sr_denominator"] == 9 for row in rows))
        self.assertEqual(rows[0]["sr_percent"], 0.0)
        self.assertEqual(rows[1]["sr_percent"], 100.0)
        self.assertEqual(rows[1]["delta_sr_per_clarification"], 100.0)

    def test_missing_cells_do_not_create_final_scores(self):
        _, manifest = generate_all()
        manifest["legacy_b1_candidates"] = {}
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            aggregate_table5, "RESULTS", Path(tmpdir)
        ):
            rows, _, report = aggregate(manifest)
        self.assertFalse(report["complete"])
        self.assertTrue(all(row["sr"] == "" for row in rows))


if __name__ == "__main__":
    unittest.main()
