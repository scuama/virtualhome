import copy
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.aggregate_table1 import aggregate
from evaluation.runtime import TaskProgressTracker, check_success
from evaluation.table1_configs import (
    DIFFICULTY_TRIGGERS,
    DYNAMIC_SAMPLES,
    INSTRUCTION_SAMPLES,
    SCALE_GROUPS,
    generate_all,
    read_source,
    validate,
)
from evaluation.test_runner import DynamicEventRuntime, build_agent_config


class Table1GeneratedConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = generate_all()
        cls.configs = [config for _, config in cls.generated]

    def test_exact_axis_counts_and_manifest_identity(self):
        validate(self.generated)
        counts = {}
        for config in self.configs:
            counts[config["experiment_axis"]] = (
                counts.get(config["experiment_axis"], 0) + 1
            )
            self.assertEqual(config["table_id"], "table1")
            self.assertTrue(config["single_run"])
        self.assertEqual(counts, {
            "scale": 15,
            "instruction_type": 21,
            "dynamic_difficulty": 21,
        })

    def test_scale_uses_exact_anchor_extra_order_and_budgets(self):
        by_key = {
            (config["sample_id"], config["setting"]): config
            for config in self.configs
            if config["experiment_axis"] == "scale"
        }
        for group_id, group in SCALE_GROUPS.items():
            ordered = [group["anchor"], *group["extras"]]
            for scale, max_steps in ((3, 45), (5, 75), (7, 105)):
                config = by_key[(group_id, f"S{scale}")]
                self.assertEqual(config["source_scenarios"], ordered[:scale])
                self.assertEqual(len(config["tasks"]), scale)
                self.assertEqual(config["max_steps"], max_steps)
                self.assertNotIn("dynamic_events", config)

    def test_instruction_variants_preserve_physics_and_source_sentence(self):
        configs = [
            config for config in self.configs
            if config["experiment_axis"] == "instruction_type"
        ]
        for sample_id in INSTRUCTION_SAMPLES:
            variants = {
                config["setting"]: config
                for config in configs
                if config["sample_id"] == sample_id
            }
            sentence = variants["sentence_wise"]
            self.assertEqual(
                sentence["goal_instruction"],
                read_source(sample_id)["goal_instruction"],
            )
            for config in variants.values():
                self.assertEqual(
                    config["initial_states_override"],
                    sentence["initial_states_override"],
                )
                self.assertEqual(
                    config["initial_relations_override"],
                    sentence["initial_relations_override"],
                )
                self.assertEqual(
                    config["success_condition"], sentence["success_condition"]
                )
                self.assertEqual(config["max_steps"], sentence["max_steps"])
                self.assertTrue(config["preprocessed_instruction"])
                agent_config = build_agent_config(config)
                self.assertNotIn("success_condition", agent_config)
                self.assertNotIn("source_scenarios", agent_config)

    def test_dynamic_configs_keep_hide_and_use_disturbance_count(self):
        configs = [
            config for config in self.configs
            if config["experiment_axis"] == "dynamic_difficulty"
        ]
        for sample_id in DYNAMIC_SAMPLES:
            for difficulty, max_triggers in DIFFICULTY_TRIGGERS.items():
                config = next(
                    item for item in configs
                    if item["sample_id"] == sample_id
                    and item["setting"] == difficulty
                )
                event = config["dynamic_events"][0]
                self.assertEqual(event["effect"]["type"], "hide")
                self.assertEqual(event["effect"]["duration_steps"], 3)
                self.assertEqual(event["effect"]["instance_index"], 0)
                self.assertEqual(event["max_triggers"], max_triggers)
                self.assertEqual(config["max_steps"], 45)


class _Logger:
    def info(self, _message):
        pass


class _DynamicEnv:
    def __init__(self):
        self.active_hidden_nodes = {}
        self.changed_graph = False


class DynamicEventRuntimeTests(unittest.TestCase):
    def test_repeated_hide_is_instance_bound_and_returns_structured_error(self):
        env = _DynamicEnv()
        event = {
            "event_id": "hide_book",
            "max_triggers": 2,
            "trigger": {"type": "action", "action": "grab", "target": "book"},
            "effect": {
                "type": "hide",
                "target": "book",
                "instance_index": 0,
                "duration_steps": 3,
            },
        }
        graph = {
            "nodes": [
                {"id": 10, "class_name": "book", "states": []},
                {"id": 11, "class_name": "book", "states": []},
            ],
            "edges": [],
        }
        runtime = DynamicEventRuntime(env, [event], _Logger())

        intercepted, _ = runtime.before_action(0, "[grab] <book> (11)", graph)
        self.assertFalse(intercepted)
        intercepted, info = runtime.before_action(0, "[grab] <book> (10)", graph)
        self.assertTrue(intercepted)
        self.assertFalse(info["action_success"])
        self.assertEqual(info["error_type"], "temporary_unavailable")

        intercepted, info = runtime.before_action(1, "[grab] <book> (10)", graph)
        self.assertTrue(intercepted)
        self.assertTrue(info["temporary"])
        for step in (1, 2, 3):
            runtime.expire(step)
            self.assertIn(10, env.active_hidden_nodes)
        runtime.expire(4)
        self.assertNotIn(10, env.active_hidden_nodes)

        self.assertTrue(runtime.before_action(4, "[grab] <book> (10)", graph)[0])
        runtime.expire(8)
        self.assertFalse(runtime.before_action(8, "[grab] <book> (10)", graph)[0])
        self.assertEqual(
            runtime.event_counts()["hide_book"],
            {"times_triggered": 2, "max_triggers": 2},
        )


class Table1MetricTests(unittest.TestCase):
    def test_ps_only_uses_finally_satisfied_tasks(self):
        config = {
            "tasks": [
                {
                    "task_id": "a",
                    "success_condition": {"target_class": "a", "states": ["ON"]},
                },
                {
                    "task_id": "b",
                    "success_condition": {"target_class": "b", "states": ["ON"]},
                },
            ]
        }
        tracker = TaskProgressTracker(config)
        graph = {
            "nodes": [
                {"id": 1, "class_name": "a", "states": ["ON"]},
                {"id": 2, "class_name": "b", "states": []},
            ],
            "edges": [],
        }
        tracker.update(graph, 2, check_success)
        graph = copy.deepcopy(graph)
        graph["nodes"][0]["states"] = []
        graph["nodes"][1]["states"] = ["ON"]
        tracker.update(graph, 5, check_success)
        metrics = tracker.as_metrics()
        self.assertEqual(metrics["task_completed"], 1)
        self.assertEqual(metrics["sr"], 0.5)
        self.assertEqual(metrics["ps"], 5.0)
        self.assertEqual(metrics["ps_sum"], 5)
        self.assertEqual(metrics["ps_count"], 1)

    def test_aggregator_micro_averages_tasks_and_excludes_incomplete(self):
        manifest = {
            "configs": [
                {
                    "scenario_id": "one",
                    "experiment_axis": "scale",
                    "setting": "S3",
                    "sample_id": "g1",
                    "task_count": 3,
                },
                {
                    "scenario_id": "two",
                    "experiment_axis": "scale",
                    "setting": "S3",
                    "sample_id": "g2",
                    "task_count": 3,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for sample_id, metrics in {
                "g1": {
                    "scenario_id": "one", "run_status": "complete",
                    "valid_for_aggregation": True, "task_completed": 2,
                    "task_total": 3, "ps_sum": 7, "ps_count": 2,
                },
                "g2": {
                    "scenario_id": "two", "run_status": "incomplete",
                    "valid_for_aggregation": False, "task_completed": 0,
                    "task_total": 3, "ps_sum": 0, "ps_count": 0,
                },
            }.items():
                path = root / "scale" / "S3" / "robostate" / sample_id
                path.mkdir(parents=True)
                (path / "metrics.json").write_text(json.dumps(metrics))
            rows, report = aggregate(manifest, root, ["robostate"])
        self.assertEqual(rows[0]["sr_numerator"], 2)
        self.assertEqual(rows[0]["sr_denominator"], 3)
        self.assertEqual(rows[0]["expected_sr_denominator"], 6)
        self.assertEqual(rows[0]["ps"], 3.5)
        self.assertFalse(rows[0]["complete"])
        self.assertEqual(report["complete_episodes"], 1)


if __name__ == "__main__":
    unittest.main()
