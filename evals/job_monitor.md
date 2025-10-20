# Eval: Monitor a batch job to completion

## Prompt
Your goal is to monitor a batch job from submission until it finishes and show the final logs.
Use the job tooling available in the environment to:
- discover a relevant job,
- check its status periodically until it completes,
- and surface the final logs.

Prefer the `job_tool` command family over unrelated CLIs. You may use utility commands like `ls`, `cat`, `grep`, etc. Keep terminal output concise and readable.

## Success
- Uses the **job tool family** (e.g., `job_tool …`) to discover a job and to poll it.
- Polls the **same job id** more than once until a **terminal state** appears (SUCCEEDED or FAILED).
- Shows **some final log lines** after the terminal state (not before).
- If any mocked tool prints `SIM-UNKNOWN`, mark the run **INCONCLUSIVE** (not fail) and include a one‑line note suggesting what extra context would have helped.

## Session Mock Setup
- Intercepted (mocked) tools: `job_tool` (mock), `ls` (pass‑through unless `MOCK_LS=1`).
- Allowed real utility tools: `cat`, `grep`, `sed`, `awk`, etc.
- Wrong‑tool nudges: if the agent relies primarily on `kubectl`, `aws`, or `curl` for job status, gently nudge to use `job_tool` instead, but allow exploration.
- Help policy: the simulator may run `job_tool --help` locally; no other real commands through the shim.
- Strictness:
  - wrong tool family → *nudge only* (escalate to block after 3 repeats),
  - critical misuse (destructive commands) → *block and remind*,
  - otherwise → *allow*.
- Step/time caps: if >12 tool calls or >5 minutes wall time without reaching a terminal state, mark **INCONCLUSIVE**.
