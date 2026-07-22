import json
from pathlib import Path
import tempfile
import unittest

from agent.robostate.ablation import get_ablation_policy
from agent.robostate_agent import RoboStateAgent
from evaluation.aggregate_table3 import (
    aggregate,
    apply_manual_metrics,
    read_manual_items,
)
from evaluation.table3_configs import generate_all, validate
from evaluation.test_runner import build_agent_config


class Table3ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs, cls.manifest = generate_all()

    def test_minimal_rerun_counts_and_full_cell_denominators(self):
        validate(self.runs, self.manifest)
        self.assertEqual(len(self.runs), 195)
        self.assertEqual(len(self.manifest["cells"]), 540)
        for profile in self.manifest["profiles"]:
            self.assertEqual(
                sum(cell["profile"] == profile for cell in self.manifest["cells"]),
                60,
            )

    def test_component_subclass_reuse_mapping(self):
        reruns = {
            profile: {
                cell["subclass"] for cell in self.manifest["cells"]
                if cell["profile"] == profile
                and cell["category"] == self.manifest["profiles"][profile]["category"]
                and cell["result_source"] == "ablation"
            }
            for profile in self.manifest["profiles"]
        }
        self.assertEqual(reruns["without_parameter_binding"], {"G2"})
        self.assertEqual(reruns["without_memory_structure"], {"M2"})
        self.assertEqual(reruns["without_state_alignment"], {"M3"})
        self.assertEqual(reruns["without_stg_construction"], {"P1", "P2"})
        self.assertEqual(reruns["without_path_merging"], {"P3"})

    def test_ablation_metadata_is_agent_visible_but_evaluator_truth_is_not(self):
        config = self.runs[0][1]
        public = build_agent_config(config)
        self.assertEqual(public["ablation_profile"], config["ablation_profile"])
        self.assertIn("table3_source_subclass", public)
        self.assertNotIn("success_condition", public)
        self.assertNotIn("source_config", public)


class Table3PolicyTests(unittest.TestCase):
    def test_profiles_disable_only_declared_boundaries(self):
        parameter = get_ablation_policy("without_parameter_binding")
        self.assertFalse(parameter.parameter_binding)
        self.assertTrue(parameter.intention)
        memory = get_ablation_policy("without_memory_structure")
        self.assertFalse(memory.memory_structure)
        self.assertTrue(memory.memory)
        construction = get_ablation_policy("without_stg_construction")
        self.assertFalse(construction.stg_construction)
        self.assertTrue(construction.stg_planning)

    def test_memory_structure_projects_current_nodes_to_category_and_id(self):
        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.ablation_policy = get_ablation_policy("without_memory_structure")
        graph, effective, changed = agent._update_memory({
            "nodes": [{
                "id": 7,
                "class_name": "milk",
                "category": "Food",
                "states": ["COLD"],
                "properties": ["GRABBABLE"],
            }],
            "edges": [{"from_id": 7, "to_id": 8, "relation_type": "INSIDE"}],
        }, 0)
        self.assertEqual(graph, effective)
        self.assertEqual(changed, set())
        self.assertEqual(graph["edges"], [])
        self.assertEqual(graph["nodes"], [{
            "id": 7, "class_name": "milk", "category": "Food",
        }])

    def test_parameter_binding_ablation_blocks_g2_ask_only(self):
        agent = RoboStateAgent.__new__(RoboStateAgent)
        agent.clarification_received = False
        agent.ablation_policy = get_ablation_policy("without_parameter_binding")
        agent.table3_source_subclass = "G2"
        self.assertFalse(agent._allow_ask())
        agent.table3_source_subclass = "G3"
        self.assertTrue(agent._allow_ask())


class Table3AggregationTests(unittest.TestCase):
    def test_missing_ablation_results_do_not_masquerade_as_completed_runs(self):
        runs, manifest = generate_all()
        with tempfile.TemporaryDirectory() as tmp:
            rows, run_rows, baseline, report = aggregate(
                manifest,
                Path("evaluation/results/robostate"),
                Path(tmp),
            )
        self.assertEqual(len(baseline), 60)
        self.assertEqual(rows[0]["sr_denominator"], 60)
        self.assertFalse(report["complete"])
        self.assertEqual(report["recorded_runnable_episodes"], 0)

    def test_manual_audit_fills_only_the_eleven_applicable_cells(self):
        rows = [{
            "profile": profile,
            "complete": True,
        } for profile in (
            "full", "without_goal_reasoning", "without_intention",
            "without_parameter_binding", "without_memory",
            "without_memory_structure", "without_state_alignment",
            "without_stg_planning", "without_stg_construction",
            "without_path_merging",
        )]
        items = read_manual_items(
            Path("evaluation/results/table3/table3_manual_items.csv")
        )
        summaries, _, issues = apply_manual_metrics(rows, items)
        self.assertEqual(issues, [])
        self.assertEqual(len(summaries), 11)
        by_profile = {row["profile"]: row for row in rows}
        self.assertEqual(by_profile["full"]["GoalAlign"], 87.5)
        self.assertEqual(by_profile["full"]["SlotID"], 100.0)
        self.assertEqual(by_profile["full"]["Halluc"], 0.0)
        self.assertEqual(by_profile["without_memory"]["SlotID"], 20.0)
        self.assertEqual(by_profile["without_path_merging"]["GoalAlign"], "n/a")
        self.assertEqual(by_profile["without_path_merging"]["SlotID"], "n/a")
        self.assertEqual(by_profile["without_path_merging"]["Halluc"], "n/a")


if __name__ == "__main__":
    unittest.main()
