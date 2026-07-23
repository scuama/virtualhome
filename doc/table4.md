# Table 4 model-backbone protocol

Table 4 compares RoboState with five model backbones. The ChatGPT cell is the
accepted Table 3 Full aggregate and is never rerun: SR is 52/60 (86.67%) and PS
is 261/52 (5.0192). Claude, Gemini, Llama, and Qwen share 13 candidate
scenarios selected from the harder successful GPT baseline cases. Each model
independently contributes its best 11 valid candidates, so its SR denominator
is 11. This asymmetric denominator and per-model selection must remain visible
in the table note; the result is a preliminary sampled comparison rather than
a fully paired experiment.

Valid successes from the pre-fix run are reused byte-for-byte. Only failed or
incomplete model/scenario pairs are archived and rerun with the common
interface-fairness revision. The run CSV records selection rank, whether the
candidate enters the table, framework revision, result source, and previous
attempt path.

The four OpenRouter models are `anthropic/claude-haiku-4.5`,
`google/gemini-3.5-flash`, `meta-llama/llama-3.1-8b-instruct`, and
`qwen/qwen3-8b`. The Llama column is not labelled local.

Generate and validate the 52 candidate configs:

```bash
PYTHONPATH=. venv/bin/python evaluation/table4_configs.py generate
PYTHONPATH=. venv/bin/python evaluation/table4_configs.py validate
```

Set the key only in the environment, then run the complete batch. The wrapper
performs four JSON smoke requests, keeps macOS awake with `caffeinate -dimsu`,
runs models in Qwen/Llama/Claude/Gemini order, and aggregates the result:

```bash
export OPENROUTER_API_KEY='<openrouter-key>'
evaluation/run_table4.sh
```

The wrapper uses `--retry-sr-lt 0`: successful episodes are skipped, while
complete failures and infrastructure-incomplete episodes are retried.
Infrastructure failures remain incomplete; model-level planning, parsing,
action, and max-step failures remain completed failures.

The paper table contains only SR/PS. `table4_module_stats.csv` separately
reports Goal Reasoner, SDG Planner, and Memory mean time and tokens per task.
Memory is deterministic local graph processing and therefore uses zero tokens.
Legacy ChatGPT module telemetry is `n/a`.

Extra reasoning is disabled where the endpoint permits it. Gemini 3.5 Flash
rejects disabled reasoning, so it uses the provider's `minimal` effort and its
reasoning tokens are recorded explicitly.
