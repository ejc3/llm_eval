from .utils import run_llm
import json

JUDGE_SYS = """You grade whether an assistant achieved the evaluation goals.
Return JSON with fields: { "verdict": "PASS|SOFT_PASS|INCONCLUSIVE|FAIL", "rationale": "<one concise paragraph>" }.
Rules:
- Focus on outcomes specified in the Success text.
- Be tolerant of different command sequences as long as goals are met.
- Consider trajectory evidence: tool family usage, repeated polling, terminal state, logs shown, wrong-tool reliance, and any SIM-UNKNOWN events.
"""

def judge(llm_cmd: str, success_text: str, condensed_trajectory: str):
    prompt = f"""{JUDGE_SYS}

## SUCCESS
{success_text}

## TRAJECTORY
{condensed_trajectory}
"""
    out = run_llm(llm_cmd, prompt, timeout=180).strip()
    try:
        data = json.loads(out)
    except Exception:
        data = {"verdict":"INCONCLUSIVE","rationale":"Judge output not JSON."}
    return data
