#!/bin/zsh
set -eu

repo_dir=${0:A:h:h}
cd "$repo_dir"

if [[ -z ${OPENROUTER_API_KEY:-} ]]; then
  print -u2 "OPENROUTER_API_KEY is required"
  exit 2
fi
export OPENAI_API_BASE=${OPENAI_API_BASE:-https://openrouter.ai/api/v1}

if [[ ${TABLE4_CAFFEINATED:-0} != 1 ]]; then
  export TABLE4_CAFFEINATED=1
  exec caffeinate -dimsu "$0" "$@"
fi

PYTHONPATH=. venv/bin/python evaluation/table4_smoke.py
PYTHONPATH=. venv/bin/python evaluation/prepare_table4_rerun.py
for model_alias in qwen llama claude gemini; do
  PYTHONPATH=. venv/bin/python evaluation/test_runner.py \
    "evaluation/configs/table4/runs/${model_alias}" \
    --method robostate \
    --retry-sr-lt 0 \
    --daemon \
    "$@"
done
PYTHONPATH=. venv/bin/python evaluation/aggregate_table4.py
