import os, sys, shlex
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src", "py")
if SRC not in sys.path:
    sys.path.insert(0, SRC)
default_py = shlex.quote(sys.executable)
os.environ.setdefault("LLM_CMD", f"{default_py} -m llm_eval.mock_claude")
