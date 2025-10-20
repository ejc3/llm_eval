import os, subprocess
from .utils import read_text, run_llm, which_skip_shim

def build_envelope(tool_name: str, fallback: str, eval_prompt: str, tool_md: str,
                   system_help: str, world_state: str, raw_cmdline: str, stdin_text: str = '') -> str:
    return f"""<BEGIN SIMULATOR SYSTEM>
You simulate the CLI tool "{tool_name}".
Rules:
- Print ONLY what the real command would print to stdout for the provided call.
- No explanations, no extra lines, no code fences.
- Preserve the tool’s formatting style exactly (spacing, tabs, ordering).
- If you are uncertain or lack context to answer plausibly, print exactly:
  {fallback}
<END SIMULATOR SYSTEM>

<BEGIN EVAL PROMPT>
{eval_prompt}
<END EVAL PROMPT>

<BEGIN TOOL DOC MARKDOWN>
{tool_md}
<END TOOL DOC MARKDOWN>

<BEGIN SYSTEM HELP OPTIONAL>
{system_help}
<END SYSTEM HELP OPTIONAL>

<BEGIN SESSION WORLD STATE>
{world_state}
<END SESSION WORLD STATE>

<BEGIN CALL>
cmdline: {raw_cmdline}
stdin: {stdin_text or '(empty)'}
<END CALL>
"""

def simulate(tool_name: str, cmdline: str, eval_prompt_path: str, tool_md_path: str,
             llm_cmd: str, allow_help: bool, shim_dir: str, traj_writer=None, world_state_text: str = '') -> str:
    eval_md = read_text(eval_prompt_path)
    tool_md = read_text(tool_md_path)
    fallback = f"SIM-UNKNOWN::{tool_name}::insufficient-context"
    for line in tool_md.splitlines():
        if line.strip().startswith("SIM-UNKNOWN"):
            fallback = line.strip()
            break
    help_txt = ""
    if allow_help:
        real = which_skip_shim(tool_name, shim_dir)
        if real:
            try:
                out = subprocess.run([real,"--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
                help_txt = f"$ {tool_name} --help\n" + out.stdout
            except Exception:
                help_txt = ""
    envelope = build_envelope(tool_name, fallback, eval_md, tool_md, help_txt, world_state_text, cmdline)
    out = run_llm(llm_cmd, envelope, timeout=240)
    stripped = out.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`\n ")
    return stripped
