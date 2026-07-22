# Table 3 ablation protocol

Table 3 reuses the 60 existing RoboState G/M/P results as the Full baseline. An
old episode without explicit success evidence is a failed SR episode. The
accepted SR/PS aggregate covers 195/195 runnable ablation configs and 540
profile/scenario contributions.

## Runtime matrix

Each ablation profile has all 60 source tasks in the manifest. Its directly
affected category is evaluated on 20 tasks; five fixed samples from each other
category are rerun and receive weight four. Reused tasks use the Full result.
Consequently every SR/PS row has effective denominator 60.

| Profile | Directly rerun subclasses | Runnable configs |
|---|---|---:|
| without_goal_reasoning | G1-G4 | 30 |
| without_intention | G3-G4 | 20 |
| without_parameter_binding | G2 | 15 |
| without_memory | M1-M4 | 30 |
| without_memory_structure | M2 | 15 |
| without_state_alignment | M3 | 15 |
| without_stg_planning | P1-P4 | 30 |
| without_stg_construction | P1-P2 | 20 |
| without_path_merging | P3-P4 | 20 |

The counts include ten cross-category configs per profile. The source dataset
currently has no separate P4 files; its P3 range contains scenarios P3_11
through P3_20.

## Manual metrics

The persistent item-level decisions live in
`evaluation/results/table3/table3_manual_items.csv`. Rebuilding the derived
review and table does not overwrite those decisions.

- `GoalAlign` is reviewed only for Full and the three Goal ablations, on G
  scenarios. The denominator is the auditable gold goal atoms; navigation and
  other execution prerequisites are excluded.
- `SlotID` is reviewed only for Full and the three Memory ablations, on M
  scenarios. M1 uses the first post-hide binding, M2 the first state-qualified
  selection, M3 is excluded, and M4 the first history-qualified binding.
- `Halluc.` is reviewed only for Full, `without_stg_planning`, and
  `without_stg_construction`, on P scenarios. It reads original LLMExecutor
  proposals and treats only action names absent from `ActionValidator.ARITY` as
  hallucinations. `ask`, `wait`, and `FINISH` are not physical proposals.

Missing Markdown logs do not inherit the episode's SR failure label. They are
excluded from the manual denominator and remain visible in scenario coverage.
Current Halluc. coverage is 17/20, 16/20, and 17/20 respectively.

`without_state_alignment` currently reruns M3, while the approved SlotID metric
excludes M3. Its SlotID value therefore comes from reused M1/M2/M4 evidence and
does not measure an M4-specific state-alignment intervention.

## Commands and outputs

Validate the 195 generated configs:

```bash
venv/bin/python evaluation/table3_configs.py validate
```

Run a single profile or the complete config directory with
`evaluation/test_runner.py`. To reconstruct the manual audit from the reviewed
judgements and original LLMExecutor output, then aggregate:

```bash
PYTHONPATH=. venv/bin/python evaluation/build_table3_manual_audit.py
PYTHONPATH=. venv/bin/python evaluation/aggregate_table3.py
```

The aggregator preserves the accepted SR/PS snapshot and writes `table3.csv`,
`table3_manual_review.csv`, and `completeness_report.json`. It also records each
manual metric's numerator, denominator, and scenario coverage. The existing
`table3_runs.csv` and `baseline_audit.csv` remain the SR/PS evidence indexes.
