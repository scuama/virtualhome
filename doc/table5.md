# Table 5: clarification-budget experiment

Table 5 evaluates RoboState with clarification budgets `b=0/1/2/3` on nine
scenarios. The generated matrix contains 36 runnable configurations under
`evaluation/configs/table5/runs/`.

Each source scenario contains one evaluator-only `simulated_user_intent`.
`evaluation/test_runner.py` never includes that field in the RoboState config.
When RoboState emits `[ask]`, the runner calls the fixed simulated-user model
with temperature 0. The model answers only the first information request in
the current question and does not volunteer later details.

Generate or validate the matrix:

```bash
PYTHONPATH=. evaluation/venv/bin/python evaluation/table5_configs.py generate
PYTHONPATH=. evaluation/venv/bin/python evaluation/table5_configs.py validate
```

Run one configuration or one budget directory:

```bash
PYTHONPATH=. evaluation/venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table5/runs/B2/G2_09.json --method robostate

PYTHONPATH=. evaluation/venv/bin/python evaluation/test_runner.py \
  evaluation/configs/table5/runs/B2 --method robostate
```

Aggregate only after the required runs finish:

```bash
PYTHONPATH=. evaluation/venv/bin/python evaluation/aggregate_table5.py
```

The aggregator uses a fixed denominator of nine scenarios per budget and
writes blank scores whenever any required cell is missing or invalid. Only
unchanged, explicitly listed legacy `b=1` logs are eligible for reuse.
