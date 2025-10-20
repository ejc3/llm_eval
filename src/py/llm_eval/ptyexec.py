import os, sys, time
from typing import Tuple, Optional

def run_in_shell(command: str, env: dict = None, cwd: Optional[str] = None, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        import pexpect
        child = pexpect.spawn('/bin/bash', ['-lc', command], cwd=cwd, env=env, timeout=timeout, echo=False, encoding='utf-8')
        child.expect(pexpect.EOF)
        output = child.before or ""
        child.close()
        rc = child.exitstatus if child.exitstatus is not None else (child.signalstatus or 1)
        return rc or 0, output, ""
    except Exception:
        import subprocess
        proc = subprocess.run(command, shell=True, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
