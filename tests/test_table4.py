import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.aggregate_table4 import aggregate, table3_full
from evaluation.table4_configs import MODELS, SAMPLES, generate_all, validate
from evaluation.test_runner import table4_result_folder
from agent.robostate.class_resolver import (
    canonicalize_selected_classes,
    resolve_scene_class,
)
from agent.robostate.sdg_planner import SDGPlanner
from agent.robostate.llm_executor import LLMExecutor


class Table4ConfigTests(unittest.TestCase):
    def test_fixed_shared_sample_matrix(self):
        runs, manifest = generate_all()
        validate(runs, manifest)
        self.assertEqual(len(runs), 52)
        self.assertEqual(len(SAMPLES), 13)
        for alias, model_id in MODELS.items():
            selected = {
                config["source_scenario_id"]
                for _, config in runs
                if config["model_alias"] == alias
            }
            self.assertEqual(selected, set(SAMPLES))
            self.assertTrue(all(
                config["evaluation_model"] == model_id
                for _, config in runs if config["model_alias"] == alias
            ))

    def test_result_folder_separates_model_and_source_scenario(self):
        path = table4_result_folder("/tmp/eval", {
            "model_alias": "qwen", "source_scenario_id": "G1_01",
        }, "robostate")
        self.assertEqual(path, "/tmp/eval/results/table4/qwen/G1_01")


class Table4AggregationTests(unittest.TestCase):
    def test_chatgpt_is_exact_table3_full_aggregate(self):
        full = table3_full()
        self.assertEqual(full["sr_numerator"], "52")
        self.assertEqual(full["sr_denominator"], "60")
        self.assertEqual(full["ps"], "5.0192")

    def test_missing_new_runs_do_not_create_scores(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "evaluation.aggregate_table4.RESULTS", Path(tmpdir)
        ):
            rows, _, module_rows, report = aggregate()
        self.assertEqual(rows[0]["model_alias"], "chatgpt")
        self.assertEqual(rows[0]["sr_denominator"], 60)
        self.assertTrue(rows[0]["complete"])
        self.assertFalse(report["complete"])
        self.assertTrue(all(row["sr_percent"] == "" for row in rows[1:]))
        chatgpt_modules = [row for row in module_rows if row["model_alias"] == "chatgpt"]
        self.assertEqual(len(chatgpt_modules), 3)
        self.assertTrue(all(row["total_tokens"] == "n/a" for row in chatgpt_modules))

    def test_best_11_selection_is_per_model_and_incomplete_bottom_two(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _, manifest = generate_all()
            for alias in MODELS:
                for index, scenario_id in enumerate(SAMPLES):
                    folder = root / alias / scenario_id
                    folder.mkdir(parents=True)
                    incomplete = index >= 11
                    success = index < (1 if alias == "llama" else 3)
                    metrics = {
                        "run_status": "incomplete" if incomplete else "complete",
                        "valid_for_aggregation": not incomplete,
                        "success": success,
                        "ps_sum": index + 1 if success else 0,
                        "ps_count": 1 if success else 0,
                        "module_stats": {},
                        "framework_revision": "table4-interface-fairness-v1",
                        "result_source": "post_fix_rerun",
                    }
                    (folder / "metrics.json").write_text(json.dumps(metrics))
            with patch("evaluation.aggregate_table4.RESULTS", root):
                rows, runs, _, report = aggregate()
        self.assertTrue(report["complete"])
        self.assertTrue(all(row["complete"] for row in rows))
        selected = [
            row for row in runs
            if row["model_alias"] == "qwen" and row["selected_for_table4"]
        ]
        self.assertEqual(len(selected), 11)
        self.assertTrue(all(row["run_status"] == "complete" for row in selected))
        self.assertEqual(
            {row["source_scenario_id"] for row in runs
             if row["model_alias"] == "qwen" and not row["selected_for_table4"]},
            set(SAMPLES[-2:]),
        )


class ClassResolverTests(unittest.TestCase):
    def test_aliases_modifiers_and_unique_generic_names(self):
        catalog = {"remotecontrol", "waterglass", "wineglass", "book"}
        self.assertEqual(
            resolve_scene_class("remote_control", catalog), "remotecontrol"
        )
        self.assertEqual(
            resolve_scene_class("dirty water glasses", catalog), "waterglass"
        )
        self.assertIsNone(resolve_scene_class("glass", catalog))
        self.assertEqual(
            canonicalize_selected_classes(
                ["remote control", "dirty_water_glass"], catalog
            ),
            {"remotecontrol", "waterglass"},
        )


class SDGValidationTests(unittest.TestCase):
    def test_rejects_cycle_and_unsupported_relation(self):
        payload = {
            "nodes": [
                {
                    "id": "N1", "type": "Relation", "object": "book",
                    "relation": "FLOATING", "target": "sofa",
                },
                {
                    "id": "N2", "type": "State", "object": "book",
                    "value": "HELD",
                },
            ],
            "edges": [
                {"from": "N1", "to": "N2"},
                {"from": "N2", "to": "N1"},
            ],
        }
        canonical, errors = SDGPlanner.validate_sdg(
            payload, "Put the book on the sofa.", ["book", "sofa"]
        )
        self.assertIsNone(canonical)
        self.assertTrue(any("unsupported relation" in item for item in errors))
        self.assertTrue(any("cycle" in item for item in errors))

    def test_generation_retries_once_with_validation_feedback(self):
        class RetryLLM:
            def __init__(self):
                self.calls = []

            def generate_json(self, system_prompt, user_prompt, **kwargs):
                self.calls.append(user_prompt)
                if len(self.calls) == 1:
                    return {
                        "nodes": [{
                            "id": "N1", "type": "Relation",
                            "object": "book", "relation": "FLOATING",
                            "target": "sofa",
                        }],
                        "edges": [],
                    }
                return {
                    "nodes": [{
                        "id": "N1", "type": "Relation",
                        "object": "book", "relation": "ON",
                        "target": "sofa",
                    }],
                    "edges": [],
                }

        planner = SDGPlanner(RetryLLM(), None)
        result = planner.generate_sdg(
            "Put the book on the sofa.", ["book", "sofa"]
        )
        self.assertEqual(result["nodes"][0]["relation"], "ON")
        self.assertEqual(len(planner.llm.calls), 2)
        self.assertIn("previous SDG was rejected", planner.llm.calls[1])


class ExecutorFeedbackTests(unittest.TestCase):
    def test_rejection_feedback_and_stale_id_rule_are_in_prompt(self):
        class CapturingLLM:
            def __init__(self):
                self.user_prompt = ""

            def generate_json(self, system_prompt, user_prompt, **kwargs):
                self.user_prompt = user_prompt
                return {
                    "reasoning": "choose current object",
                    "satisfied_nodes": [],
                    "current_node_focus": "N1",
                    "mapped_variables": {},
                    "action": "[walk] <book> (2)",
                }

        class Logger:
            def info(self, *_):
                pass

            def error(self, *_):
                pass

            def log_module_output(self, *_, **__):
                pass

        llm = CapturingLLM()
        executor = LLMExecutor(llm, Logger())
        executor.decide_next_action(
            {
                "nodes": [{
                    "id": 2, "class_name": "book", "states": [],
                    "properties": ["GRABBABLE"],
                }],
                "edges": [],
            },
            {},
            {"nodes": [], "edges": []},
            [{"action": "[grab] <book> (15)", "success": False}],
            planner_feedback=[{
                "rejected_action": "[open] <sink> (7)",
                "reason": "sink is not openable",
            }],
        )
        self.assertIn("sink is not openable", llm.user_prompt)
        self.assertIn("Past object IDs are historical handles", llm.user_prompt)


if __name__ == "__main__":
    unittest.main()
