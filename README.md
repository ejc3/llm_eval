# llm_eval — Buck2 + Claude CLI (full, offline-capable)

**Everything you need is here, in this zip.** No stubs. No external services required.

## Highlights
- Single-file **evals** in Markdown (Prompt / Success / Session Mock Setup)
- **Tool mocks** in Markdown (rich prose; examples; fallback lines)
- **Eval translator** (MD → tiny YAML heuristics) via configurable LLM command
- **PATH shims** for the mocked tool names only
- **Big-envelope simulator** (includes full eval prompt, tool MD, optional real `--help`, recent outputs)
- **PTY runner** (TTY-friendly) + trajectory logging
- **Heuristic grader** (+ optional LLM judge)
- **Matrix** runner (CLI) + **real-tool shadow** drift checker
- **Claude mock** for completely offline runs
- **Buck2 Starlark macros** + full **unit/integration tests**

## Prereqs
- Python 3.10+
- Buck2 on PATH

## Choose the model
Use the offline mock (recommended to start):
```bash
export LLM_CMD="python3 -m llm_eval.mock_claude"
# or add our PATH wrapper:
# export PATH="$PWD/tools/bin:$PATH"  # now `claude -p` runs the mock
```
Or set to your real Claude CLI:
```bash
export LLM_CMD="claude -p default -m claude-3-5-sonnet -t 0"
```

## Run a full demo
```bash
pip install -r requirements.txt
bash scripts/quickstart_mock.sh
```
It will translate, run, and grade `evals/job_monitor.md` and print the trajectory path.

## Manual flow
```bash
# Translate
buck2 run //:llm_eval -- translate evals/job_monitor.md

# Run (mock tools)
buck2 run //:llm_eval -- run evals/job_monitor.md --tools mock --engine chat

# Grade
RUN=logs/<run-id>.trajectory.jsonl
buck2 run //:llm_eval -- grade "$RUN" --junit "${RUN%.jsonl}.junit.xml" --json "${RUN%.jsonl}.summary.json"
```

## Matrix & Shadow
```bash
# matrix.yaml included at repo root
buck2 run //:llm_eval -- matrix --evals_glob "evals/*.md" --matrix matrix.yaml

# Compare simulated vs real outputs (skips when real binaries missing)
buck2 run //:llm_eval -- shadow "$RUN" --sample 25 --out "${RUN%.jsonl}.drift.json"
```

## Tests
```bash
buck2 test //:unit_tests
buck2 test //:unit_tests_sh
```
Covers: utils, translator, simulator, end-to-end runner+grader, shadow, matrix CLI.

## Where are the evals & mocks?
- `evals/job_monitor.md`, `evals/canary_observe_readonly.md`
- `mocks/job_tool.md`, `mocks/kubectl.md`, `mocks/ls.md`

## Implementation notes
- The runner uses a PTY for commands. Only the mocked tool names are intercepted (via `.mock/bin/<tool>`).
- The simulator builds a large prompt that includes the **full** eval prompt, **full** tool Markdown, optional real `--help` output, recent tool outputs, and the exact command line.
- The translator converts eval MD → YAML for **light guardrails** and **success heuristics**; tool files remain Markdown (no rigid schemas).
- The offline mock understands translator prompts, simulator envelopes, and chat prompts—so you can run everything offline.
- Real-tool shadow replays a sample of commands with actual binaries, canonicalizes noise, and computes similarity to flag drift.

## CI tips
- Default to the offline mock for PRs:
  ```bash
  export LLM_CMD="python3 -m llm_eval.mock_claude"
  buck2 test //:unit_tests
  buck2 test //:all_evals_mock__job_monitor_mock
  ```

## License
MIT
