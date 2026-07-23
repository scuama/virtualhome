import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evaluation.aggregate_table4 import aggregate, table3_full
from evaluation.table4_configs import MODELS, SAMPLES, generate_all, validate
from evaluation.test_runner import table4_result_folder


class Table4ConfigTests(unittest.TestCase):
    def test_fixed_shared_sample_matrix(self):
        runs, manifest = generate_all()
        validate(runs, manifest)
        self.assertEqual(len(runs), 44)
        self.assertEqual(len(SAMPLES), 11)
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


if __name__ == "__main__":
    unittest.main()
