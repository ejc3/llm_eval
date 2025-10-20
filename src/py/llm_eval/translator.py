import os, yaml, re
from typing import Any, Dict, List, Set
from .utils import read_text, write_text, find_section, run_llm

TRANSLATOR_SYS = """You convert an evaluation Markdown file into a small YAML used for guardrails and grading.
Rules:
- Use ONLY information present in the Markdown.
- Copy the full ## Prompt into `prompt_text` verbatim.
- Copy the full ## Success into `success.human_text` verbatim.
- Parse ## Session Mock Setup into `guardrails`, `caps`, and strictness hints.
- Do not invent tools, commands, or policies; if uncertain, omit the field.
- Output YAML only, no code fences, no commentary.
YAML keys:
  id: <slug from title or filename>
  prompt_text: <string>
  guardrails:
    allowed_tools: [string]
    wrong_tool_patterns: [regex-string]
    help_policy: { allow_system_help: boolean }
    strictness:
      wrong_tool: nudge_only|nudge_then_block_after_3|block
      mutating_kubectl: block_and_remind|allow
      critical_misuse: block_and_remind|allow
      otherwise: allow|block
  caps:
    max_calls: int
    max_minutes: int
  success:
    human_text: <string>
    heuristics:
      must_use_family: [string]
      polling_required: boolean
      single_target_required: boolean
      terminal_states_any: [string]
      must_show_logs_after_terminal: boolean
      require_read_only: boolean
      inconclusive_on: string
"""

def _slug_from_path(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    slug = re.sub(r'[^a-z0-9]+', '_', base.lower()).strip('_')
    return slug or base.lower()

def _normalize_tool(token: str) -> str:
    token = token.strip()
    if '=' in token:
        return ''
    token = re.split(r'[|/]', token, maxsplit=1)[0]
    token = token.split()[0]
    return token

def _ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    return list(value)

def _augment_from_markdown(data: Dict[str, Any], md: str, eval_md_path: str) -> Dict[str, Any]:
    slug = _slug_from_path(eval_md_path)
    if data.get('id') in (None, '', 'eval'):
        data['id'] = slug

    if not data.get('prompt_text'):
        data['prompt_text'] = find_section(md, 'Prompt')

    success = data.setdefault('success', {})
    if not success.get('human_text'):
        success['human_text'] = find_section(md, 'Success')
    heuristics = success.setdefault('heuristics', {})

    setup = find_section(md, 'Session Mock Setup')
    guardrails = data.setdefault('guardrails', {})
    existing_allowed = guardrails.get('allowed_tools') or []
    existing_wrong = guardrails.get('wrong_tool_patterns') or []
    allowed_from_md: Set[str] = set()
    wrong_from_md: Set[str] = set()
    strictness = guardrails.setdefault('strictness', {})

    for line in setup.splitlines():
        tokens = re.findall(r'`([^`]+)`', line)
        lower = line.lower()
        stripped_lower = line.strip().lower()
        if tokens and (
            stripped_lower.startswith('- intercepted') or
            stripped_lower.startswith('- allowed') or
            stripped_lower.startswith('allowed:')
        ):
            for tok in tokens:
                norm = _normalize_tool(tok)
                if norm:
                    allowed_from_md.add(norm)
        if tokens and ('wrong-tool' in lower or 'wrong tool' in lower):
            for tok in tokens:
                norm = _normalize_tool(tok)
                if norm:
                    wrong_from_md.add(f"^{norm}")
        if 'mutating' in lower and 'kubectl' in lower:
            strictness.setdefault('mutating_kubectl', 'block_and_remind')
        if 'wrong tool' in lower:
            strictness.setdefault('wrong_tool', 'nudge_then_block_after_3')
        if 'critical misuse' in lower:
            strictness.setdefault('critical_misuse', 'block_and_remind')
        if 'otherwise' in lower and 'allow' in lower:
            strictness.setdefault('otherwise', 'allow')

    if allowed_from_md:
        guardrails['allowed_tools'] = sorted(allowed_from_md)
    elif existing_allowed:
        guardrails['allowed_tools'] = existing_allowed
    if wrong_from_md:
        guardrails['wrong_tool_patterns'] = sorted(wrong_from_md)
    elif existing_wrong:
        guardrails['wrong_tool_patterns'] = existing_wrong

    help_policy = guardrails.setdefault('help_policy', {})
    if 'allow_system_help' not in help_policy:
        help_policy['allow_system_help'] = 'no help' not in setup.lower()

    caps = data.setdefault('caps', {})
    if 'max_calls' not in caps:
        m_calls = re.search(r'>(\d+)\s+tool calls', setup)
        caps['max_calls'] = int(m_calls.group(1)) if m_calls else 12
    if 'max_minutes' not in caps:
        m_minutes = re.search(r'>(\d+)\s+minutes', setup)
        caps['max_minutes'] = int(m_minutes.group(1)) if m_minutes else 5

    allowed_tools = guardrails.get('allowed_tools', [])
    families = {f for f in _ensure_list(heuristics.get('must_use_family')) if f in allowed_tools}
    if 'job_tool' in allowed_tools:
        families.add('job_tool')
        heuristics.setdefault('polling_required', True)
        heuristics.setdefault('single_target_required', True)
        heuristics.setdefault('terminal_states_any', ['SUCCEEDED', 'FAILED'])
        heuristics.setdefault('must_show_logs_after_terminal', True)
    if 'kubectl' in allowed_tools:
        families.add('kubectl')
        heuristics.setdefault('require_read_only', True)
    else:
        heuristics.pop('require_read_only', None)
    if families:
        heuristics['must_use_family'] = sorted(families)
    heuristics.setdefault('inconclusive_on', 'SIM-UNKNOWN::')

    return data

def translate_eval_md(eval_md_path: str, out_yaml_path: str, llm_cmd: str):
    md = read_text(eval_md_path)
    prompt = f"""{TRANSLATOR_SYS}

<BEGIN EVAL MARKDOWN>
{md}
<END EVAL MARKDOWN>"""
    yaml_text = run_llm(llm_cmd, prompt, timeout=180).strip()
    try:
        data = yaml.safe_load(yaml_text)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    data = _augment_from_markdown(data, md, eval_md_path)
    os.makedirs(os.path.dirname(out_yaml_path), exist_ok=True)
    write_text(out_yaml_path, yaml.safe_dump(data, sort_keys=False))
    return data
