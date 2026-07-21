# Evaluation config layout

`evaluation/test_runner.py` accepts one or more JSON config files or
directories. Directories are searched recursively and metadata files such as
`manifest.json` are ignored.

```text
evaluation/configs/
├── table1/          # formal Table 1 configs (57)
├── table2/          # formal Table 2 configs (45)
└── source_tasks/    # original G, M, P, and ExRAP task configs (79)
```

Examples:

```bash
# One scenario
python evaluation/test_runner.py \
  evaluation/configs/table2/scale/E_MULTI_G01_S3.json

# One Table 2 axis
python evaluation/test_runner.py \
  evaluation/configs/table2/non_stationarity

# All formal Table 2 configs
python evaluation/test_runner.py evaluation/configs/table2

# Multiple inputs are supported and overlapping inputs are deduplicated
python evaluation/test_runner.py \
  evaluation/configs/table2/scale \
  evaluation/configs/table2/instruction_type
```

Public options are limited to `--method`, `--model`, `--force`, and
`--unity-path`. The hidden `--daemon` option is used only by the runner's
background subprocess.

Benchmark configuration tools use explicit subcommands:

```bash
python evaluation/table1_configs.py generate
python evaluation/table1_configs.py validate
python evaluation/table2_configs.py generate
python evaluation/table2_configs.py validate
```

Add `--unity` to either `validate` command for live Unity initialization
checks. Table 1 result aggregation remains a separate reporting operation:

```bash
python evaluation/aggregate_table1.py
```
