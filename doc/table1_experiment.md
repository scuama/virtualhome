# Table 1 VirtualHome experiment

Table 1 is a single-run benchmark generated from the checked-in source JSON.
`doc/config.md` explains category names but never overrides JSON behavior.

## Generate and validate

```bash
./venv/bin/python evaluation/table1_configs.py generate
./venv/bin/python evaluation/table1_configs.py validate
```

The generator writes 57 configs and
`evaluation/configs/table1/manifest.json`:

- scale: 15 configs (five groups at S3/S5/S7);
- instruction type: 21 configs (seven samples in three forms);
- dynamic difficulty: 21 configs (seven samples at low/medium/high).

To validate initialization against Unity without calling an LLM:

```bash
./venv/bin/python evaluation/table1_configs.py validate --unity
```

Use `--target` followed by scenario ID prefixes to validate a smoke subset.

## Run the formal cells

Run axes in the planned order. The runner starts in the background unless
`--daemon` is supplied.

```bash
./venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table1/scale \
  --method robostate saycan llm_planner exrap flare

./venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table1/instruction_type \
  --method robostate saycan llm_planner exrap flare

./venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table1/dynamic \
  --method robostate saycan llm_planner exrap flare
```

Table 1 results are isolated at:

```text
evaluation/results/table1/<axis>/<setting>/<method>/<sample_id>/
```

A complete result is skipped on a later invocation. Missing, invalid, and
incomplete results are eligible for rerun; `--force` reruns complete results as
well. Initialization errors, API errors, timeouts, initially satisfied tasks,
and dynamic-trigger mismatches are excluded from aggregation rather than
counted as task failures.

## Aggregate

```bash
./venv/bin/python evaluation/aggregate_table1.py
```

This writes:

- `evaluation/results/table1/table1.csv` with task-level micro-averaged SR,
  final-success-only PS, raw numerators/denominators, and PS sample counts;
- `evaluation/results/table1/completeness_report.json` with all missing,
  incomplete, invalid, unreadable, or mismatched episodes.

The expected scale task denominators are 15/25/35. Instruction type and
dynamic difficulty each use seven independent samples per setting. The full
run contains 285 episodes and 45 method-setting cells.

## Manuscript consistency

The Table 1 implementation defines dynamic difficulty by action-triggered hide
count: low=1, medium=2, high=3. Each hide lasts three complete decision steps.
The current paper draft's 8/6/4 fixed timestep interval description must be
updated before reporting these results.
