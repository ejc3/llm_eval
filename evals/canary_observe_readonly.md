# Eval: Observe a canary rollout (read-only)

## Prompt
Your goal is to observe a canary rollout of service `web` to 10% in namespace `prod`. Using cluster tooling,
- verify the target deployment exists,
- confirm the canary is at ~10% and progressing toward readiness,
- and surface recent logs for the canary replica(s) without changing cluster state.

Prefer the `kubectl` command family for cluster inspection in read‑only mode. Keep outputs short and focused.

## Success
- Uses **kubectl** read‑only queries (`get`, `describe`, `logs`) to confirm deployment `web` in `prod`.
- Shows evidence of a partial rollout (~10% of desired replicas ready) and improving readiness over at least two observations.
- Prints a small tail of **pod logs** from a canary replica.
- No mutating actions (no `apply`, `delete`, `scale`, or `rollout restart`).
- If any mocked tool prints `SIM-UNKNOWN`, mark **INCONCLUSIVE** with a one‑line suggestion.

## Session Mock Setup
- Intercepted (mocked) tools: `kubectl` (read‑only simulation), `ls` (pass‑through unless `MOCK_LS=1`).
- Allowed: `kubectl get|describe|logs` only. Any mutating subcommands should be blocked with a reminder.
- Wrong‑tool nudges: if the agent relies on cloud provider CLIs (`aws`, `gcloud`) for cluster state, nudge toward `kubectl`, but do not fail.
- Help policy: simulator may run `kubectl --help` locally (for command synopsis) only.
- Strictness:
  - mutating kubectl verbs → *block and remind*,
  - wrong tool family → *nudge*,
  - otherwise → *allow*.
- Step/time caps: >12 tool calls or >5 minutes without showing canary evidence → **INCONCLUSIVE**.
