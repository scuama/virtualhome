# Table 3 ablation protocol

Table 3 reuses the 60 existing RoboState G/M/P results as the Full baseline.
An old run without explicit success evidence is counted as a failure. The
baseline audit is written to `evaluation/results/table3/baseline_audit.csv`.

Component ablations rerun only the directly affected subclasses; other samples
in the same 20-scenario row reuse their Full result:

| Profile | Rerun | Reuse |
|---|---|---|
| without_goal_reasoning | G1-G4 (20) | none |
| without_intention | G3-G4 (10) | G1-G2 |
| without_parameter_binding | G2 (5) | G1, G3-G4 |
| without_memory | M1-M4 (20) | none |
| without_memory_structure | M2 (5) | M1, M3-M4 |
| without_state_alignment | M4 (5) | M1-M3 |
| without_stg_planning | P1-P3 (20) | none |
| without_stg_construction | P3 (10) | P1-P2 |
| without_path_merging | P1-P2 (10) | P3 |

This produces 105 new episodes and 180 ablation-row contributions. Every Table
3 ablation row still has denominator 20; the Full row has denominator 60.

Generate or validate configs:

```bash
venv/bin/python evaluation/table3_configs.py generate
venv/bin/python evaluation/table3_configs.py validate
```

Run one profile (the runner backgrounds itself unless `--daemon` is supplied):

```bash
venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table3/runs/without_parameter_binding \
  --method robostate --model gpt-5.4-mini
```

Run all 105 new episodes by passing `evaluation/configs/table3/runs`. Existing
complete Table 3 metrics are skipped unless `--force` is specified.

Aggregate the table:

```bash
venv/bin/python evaluation/aggregate_table3.py
```

The aggregator writes `table3.csv`, `table3_runs.csv`,
`baseline_audit.csv`, `table3_manual_review.csv`, and
`completeness_report.json`. GoalAlign, SlotID, and Halluc remain manual fields.
