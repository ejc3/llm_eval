#!/usr/bin/env bash
set -euo pipefail
pip install -r requirements.txt
export LLM_CMD="python3 -m llm_eval.mock_claude"
buck2 run //:llm_eval -- translate evals/job_monitor.md
RUN=$(buck2 run //:llm_eval -- run evals/job_monitor.md --tools mock --engine chat | tail -n 1)
echo "Trajectory: $RUN"
buck2 run //:llm_eval -- grade "$RUN" --junit "${RUN%.jsonl}.junit.xml" --json "${RUN%.jsonl}.summary.json"
echo "Done."
