import os, sys, subprocess, hashlib, json, textwrap, re, pathlib, time
from typing import Dict, Any, Optional

def read_text(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8', errors='ignore')).hexdigest()

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def find_section(md: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    lines = md.splitlines()
    out = []
    in_sec = False
    for line in lines:
        if re.match(pattern, line.strip(), re.IGNORECASE):
            in_sec = True
            continue
        if in_sec and line.startswith('## '):
            break
        if in_sec:
            out.append(line)
    return '\n'.join(out).strip()

def run_llm(cmd: str, prompt: str, timeout: int = 300) -> str:
    env = os.environ.copy()
    src_root = pathlib.Path(__file__).resolve().parent.parent
    pythonpath_entries = [str(src_root)]
    existing_pp = env.get('PYTHONPATH')
    if existing_pp:
        pythonpath_entries.append(existing_pp)
    env['PYTHONPATH'] = os.pathsep.join(pythonpath_entries)
    proc = subprocess.run(
        cmd,
        input=prompt.encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        timeout=timeout,
        env=env,
    )
    out = proc.stdout.decode('utf-8', errors='ignore')
    if proc.returncode != 0 and not out.strip():
        err = proc.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"LLM command failed: rc={proc.returncode}\n{err[:4000]}")
    return out

def which_skip_shim(binary: str, shim_dir: str) -> Optional[str]:
    path = os.environ.get('PATH', '')
    for p in path.split(os.pathsep):
        if os.path.abspath(p) == os.path.abspath(shim_dir):
            continue
        candidate = os.path.join(p, binary)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None

def now_ts_iso() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def parse_commands_from_text(text: str):
    cmds = []
    for line in text.splitlines():
        if line.strip().startswith('$ '):
            cmds.append(line.strip()[2:].strip())
    fence_pat = re.compile(r"```(?:bash|sh)?\n(.*?)```", re.DOTALL)
    for m in fence_pat.finditer(text):
        block = m.group(1).strip()
        for line in block.splitlines():
            if line.strip():
                cmds.append(line.strip())
    return cmds

def text_canonicalize(s: str) -> str:
    s2 = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "<TS>", s)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2

def similarity(a: str, b: str) -> float:
    import difflib
    return difflib.SequenceMatcher(a=a, b=b).ratio()
