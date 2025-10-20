# Tool: job_tool

## Overview
`job_tool` manages and inspects batch jobs. Common subcommands: `list-jobs`, `status <id>`, `cat <id>`.

## Output Style
- Plain text, no colors.
- `list-jobs` prints tab‑separated rows: "<id>\t<STATUS>\t<submitted_at ISO8601>" sorted newest first.
- `status <id>` prints: "Status: <PENDING|RUNNING|SUCCEEDED|FAILED> (progress N%)"
- `cat <id>` prints the last ~50 lines of job output; if none, print "No output yet".

## Behavior Notes
- Progress typically increases by 5–20% each poll; may repeat once if polled too quickly.
- After SUCCEEDED, `cat <id>` shows the final log tail.
- If the id does not exist, print "job not found: <id>" and exit 0.
- `list-jobs` usually includes at least two jobs (one current RUNNING/PENDING, one historical SUCCEEDED/FAILED).

## Examples
$ job_tool list-jobs
42   RUNNING   2025-10-10T20:01:55Z
41   SUCCEEDED 2025-10-10T18:33:12Z

$ job_tool status 42
Status: RUNNING (progress 35%)

$ job_tool status 42
Status: RUNNING (progress 57%)

$ job_tool status 42
Status: SUCCEEDED (progress 100%)

$ job_tool cat 42
[2025-10-10 20:02:03] starting map phase...
[2025-10-10 20:05:44] 12/34 shards done...
[2025-10-10 20:10:12] all shards complete
[2025-10-10 20:10:45] job succeeded

## Edge Cases
- Very new jobs: `cat` → "No output yet"
- Missing id: "job not found: <id>"
- Failed job: `status <id>` → "Status: FAILED (progress 100%)"; `cat` shows error stack tail.

## Failure Modes
- Transient "backend unavailable" messages may occur for `list-jobs`; retry returns normal output.

## Fallback
If unsure, print exactly:
SIM-UNKNOWN::job_tool::insufficient-context
