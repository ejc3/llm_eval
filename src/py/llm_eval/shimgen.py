import os, stat, sys, shlex

def make_shim(bin_dir: str, tool: str):
    os.makedirs(bin_dir, exist_ok=True)
    path = os.path.join(bin_dir, tool)
    shim_text = """#!/usr/bin/env bash
# Generic shim: delegate to python module which will simulate this tool if configured.
exec {python} -m llm_eval.cli shim "$0" "$@"
""".format(python=shlex.quote(sys.executable))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(shim_text)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
    return path
