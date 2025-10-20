import os, sys, uuid, yaml, time
from .utils import read_text, write_text, parse_commands_from_text, ensure_dir, run_llm
from .translator import translate_eval_md
from .shimgen import make_shim
from .ptyexec import run_in_shell
from .trajectory import Trajectory

def run_eval(eval_md_path: str, tools_mode: str, engine: str, llm_cmd: str, out_dir: str = None):
    eval_id = os.path.splitext(os.path.basename(eval_md_path))[0]
    runtime_dir = os.path.join('runtime')
    ensure_dir(runtime_dir)
    eval_yaml_path = os.path.join(runtime_dir, f"{eval_id}.eval.yaml")
    data = translate_eval_md(eval_md_path, eval_yaml_path, llm_cmd=llm_cmd)

    allowed_tools = data.get('guardrails', {}).get('allowed_tools', [])
    shim_dir = os.path.abspath(os.path.join('.mock','bin'))
    for t in allowed_tools:
        make_shim(shim_dir, t)

    run_id = f"r-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    out_dir = out_dir or os.path.join('logs', run_id)
    ensure_dir(out_dir)
    traj_path = os.path.join(out_dir, f"{run_id}.trajectory.jsonl")
    traj = Trajectory(traj_path)
    traj.write({"run_id": run_id, "event":"session_start", "eval_id": eval_id, "engine": engine})

    prompt_text = data.get('prompt_text', read_text(eval_md_path))
    assistant = run_llm(llm_cmd, prompt_text, timeout=240)
    traj.write({"event":"assistant", "text": assistant})

    commands = parse_commands_from_text(assistant)
    env = os.environ.copy()
    env.update({
        "PATH": f"{shim_dir}{os.pathsep}" + env.get("PATH",""),
        "LLM_EVAL_RUNTIME_DIR": os.path.abspath(runtime_dir),
        "LLM_EVAL_EVAL_MD": os.path.abspath(eval_md_path),
        "LLM_EVAL_EVAL_YAML": os.path.abspath(eval_yaml_path),
        "LLM_EVAL_MOCKS_DIR": os.path.abspath("mocks"),
        "LLM_EVAL_TRAJ_PATH": os.path.abspath(traj_path),
        "LLM_EVAL_SHIM_DIR": shim_dir,
        "LLM_EVAL_ALLOW_HELP": str(data.get('guardrails', {}).get('help_policy', {}).get('allow_system_help', True)).lower(),
        "LLM_EVAL_TOOLS_MODE": tools_mode,
        "LLM_CMD": llm_cmd,
    })

    last_terminal = False
    for cmd in commands:
        tool_name = cmd.split()[0]
        is_sim = tool_name in allowed_tools and tools_mode == "mock"
        traj.write({"event":"tool_start", "tool": tool_name, "argv": cmd.split(), "cwd": os.getcwd(), "simulated": is_sim})
        rc, out, err = run_in_shell(cmd, env=env, cwd=os.getcwd(), timeout=120)
        terminal = None
        if "Status: SUCCEEDED" in out:
            terminal = "SUCCEEDED"; last_terminal = True
        stdout_hash = traj.sidecar_write(os.path.join(out_dir, "stdout"), out)
        stderr_hash = traj.sidecar_write(os.path.join(out_dir, "stderr"), err)
        traj.write({
            "event":"tool_end", "tool": tool_name, "argv": cmd.split(), "exit_code": rc,
            "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash, "terminal_state": terminal,
            "stdout_text_contains_cat_after_terminal": (last_terminal and tool_name == "job_tool" and "cat" in cmd)
        })

    traj.write({"event":"session_end", "run_id": run_id})
    print(traj_path)
    return traj_path
