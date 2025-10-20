#!/usr/bin/env python3
import sys, re, json, os

def read_stdin() -> str:
    return sys.stdin.read()

def between(s: str, start: str, end: str) -> str:
    a = s.find(start)
    if a == -1: return ""
    b = s.find(end, a + len(start))
    if b == -1: return s[a+len(start):]
    return s[a+len(start):b]

def simulate_tool(prompt: str) -> str:
    m = re.search(r'You simulate the CLI tool "([^"]+)"', prompt)
    tool = m.group(1) if m else "tool"
    call_block = between(prompt, "<BEGIN CALL>", "<END CALL>").strip()
    m2 = re.search(r'cmdline:\s*(.+)', call_block)
    cmd = m2.group(1).strip() if m2 else ""
    if tool == "job_tool":
        if "list-jobs" in cmd:
            return "42   RUNNING   2025-10-10T20:01:55Z\n41   SUCCEEDED 2025-10-10T18:33:12Z"
        if re.search(r'\bstatus\b\s+(\d+)', cmd):
            return "Status: SUCCEEDED (progress 100%)"
        if re.search(r'\bcat\b\s+(\d+)', cmd):
            return "[2025-10-10 20:02:03] starting map phase...\n[2025-10-10 20:05:44] 12/34 shards done...\n[2025-10-10 20:10:12] all shards complete\n[2025-10-10 20:10:45] job succeeded"
        return "SIM-UNKNOWN::job_tool::insufficient-context"
    if tool == "kubectl":
        if re.search(r'\b(apply|delete|scale|rollout\s+restart)\b', cmd):
            return "READ-ONLY: kubectl mutating command blocked; use get/describe/logs."
        if "get deploy" in cmd and "web" in cmd:
            return "NAME   READY   UP-TO-DATE   AVAILABLE   AGE\nweb    9/10    10           9           21d"
        if "describe deploy" in cmd and "web" in cmd:
            return "Name:                   web\nNamespace:              prod\nSelector:               app=web\nReplicas:               10 desired | 10 updated | 9 available | 1 unavailable\nStrategyType:           RollingUpdate\nEvents:\n  Normal  ScalingReplicaSet  ...  Scaled up replica set web-7f9d to 10"
        if "logs" in cmd and "deploy/web" in cmd:
            return "2025-10-10T20:01:12Z GET /healthz 200\n2025-10-10T20:01:13Z GET /api/v1/canary 200"
        return "SIM-UNKNOWN::kubectl::insufficient-context"
    if tool == "ls":
        if re.search(r'\\bls\\s+jobs\\b', cmd):
            return "42.log\n43.log"
        if re.search(r"\\bls\\s+missing\\b", cmd):
            return "ls: cannot access 'missing': No such file or directory"
        return "README.md\njobs\nsrc"
    return "SIM-UNKNOWN::{}::insufficient-context".format(tool)

def translate_eval(prompt: str) -> str:
    md = between(prompt, "<BEGIN EVAL MARKDOWN>", "<END EVAL MARKDOWN>")
    def section(title: str) -> str:
        pat = re.compile(r'^##\\s+' + re.escape(title) + r'\\s*$', re.M)
        m = pat.search(md)
        if not m: return ""
        start = m.end()
        m2 = re.compile(r'^##\\s+', re.M).search(md, start)
        end = m2.start() if m2 else len(md)
        return md[start:end].strip()
    prompt_text = section("Prompt")
    success_text = section("Success")
    setup = section("Session Mock Setup")
    allowed = []
    code_ticks = re.findall(r'`([a-zA-Z0-9_\\-]+)`', setup) + re.findall(r'`([a-zA-Z0-9_\\-]+)`', prompt_text)
    if "job_tool" in code_ticks or "job_tool" in md: allowed.append("job_tool")
    if "kubectl" in code_ticks or "kubectl" in md: allowed.append("kubectl")
    allowed = sorted(set(allowed))
    wrong = []
    if "kubectl" in md and "aws" in md: wrong.append("^aws")
    if "kubectl" in md and "gcloud" in md: wrong.append("^gcloud")
    if "job_tool" in md and "kubectl" in md: wrong.append("^kubectl")
    if "curl" in md: wrong.append("^curl")
    heur = {}
    if "job_tool" in allowed:
        heur.update({"must_use_family":["job_tool"],"polling_required":True,"single_target_required":True,"terminal_states_any":["SUCCEEDED","FAILED"],"must_show_logs_after_terminal":True,"inconclusive_on":"SIM-UNKNOWN::"})
    if "kubectl" in allowed:
        heur.update({"must_use_family":["kubectl"],"require_read_only":True,"inconclusive_on":"SIM-UNKNOWN::"})
    yml = {"id":"eval","prompt_text":prompt_text or "","guardrails":{"allowed_tools":allowed,"wrong_tool_patterns":wrong or ["^aws","^gcloud","^curl","^kubectl"] if "job_tool" in allowed else ["^aws","^curl"],"help_policy":{"allow_system_help":True},"strictness":{"wrong_tool":"nudge_then_block_after_3","critical_misuse":"block_and_remind","otherwise":"allow"}},"caps":{"max_calls":12,"max_minutes":5},"success":{"human_text":success_text or "","heuristics":heur}}
    import yaml
    return yaml.safe_dump(yml, sort_keys=False)

def chat_eval(prompt: str) -> str:
    if "monitor a batch job" in prompt or "monitor a batch job from submission" in prompt:
        return (
            "Plan: discover job, poll status until terminal, then tail logs.\n\n"
            "$ job_tool list-jobs\n"
            "$ job_tool status 42\n"
            "$ job_tool status 42\n"
            "$ job_tool cat 42\n"
        )
    if "canary rollout" in prompt and "kubectl" in prompt:
        return (
            "Plan: verify deploy exists, observe readiness trend, tail logs from canary pods.\n\n"
            "$ kubectl get deploy web -n prod\n"
            "$ kubectl describe deploy web -n prod\n"
            "$ kubectl get deploy web - n prod\n"
            "$ kubectl logs deploy/web -n prod --tail=20\n"
        ).replace(" - n ", " -n ")
    return "Plan: run basic commands.\n\n$ ls\n"

def main():
    p = read_stdin()
    if "<BEGIN SIMULATOR SYSTEM>" in p:
        sys.stdout.write(simulate_tool(p)); return 0
    if "You convert an evaluation Markdown file into a small YAML used for guardrails and grading." in p:
        sys.stdout.write(translate_eval(p)); return 0
    sys.stdout.write(chat_eval(p)); return 0

if __name__ == "__main__":
    sys.exit(main())
