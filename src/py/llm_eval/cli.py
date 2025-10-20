import os, sys, argparse, yaml, json, glob, itertools, subprocess, shlex
from .translator import translate_eval_md
from .runner import run_eval
from .grader import grade_trajectory
from .simulator import simulate
from .utils import read_text, write_text

def main():
    ap = argparse.ArgumentParser(prog="llm_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_run = sub.add_parser("run")
    ap_run.add_argument("eval_md")
    ap_run.add_argument("--tools", default="mock", choices=["mock","real"])
    ap_run.add_argument("--engine", default="chat", choices=["chat"])
    ap_run.add_argument("--model", default=None)
    ap_run.add_argument("--profile", default=None)
    ap_run.add_argument("--out", default=None)

    ap_t = sub.add_parser("translate")
    ap_t.add_argument("eval_md")

    ap_g = sub.add_parser("grade")
    ap_g.add_argument("trajectory_jsonl")
    ap_g.add_argument("--junit", default=None)
    ap_g.add_argument("--json", dest="json_out", default=None)

    ap_m = sub.add_parser("matrix")
    ap_m.add_argument("--evals_glob", default="evals/*.md")
    ap_m.add_argument("--matrix", required=True)

    ap_shadow = sub.add_parser("shadow")
    ap_shadow.add_argument("trajectory_jsonl")
    ap_shadow.add_argument("--sample", type=int, default=25)
    ap_shadow.add_argument("--out", default=None)

    ap_s = sub.add_parser("shim")
    ap_s.add_argument("argv0")
    ap_s.add_argument("args", nargs=argparse.REMAINDER)

    args = ap.parse_args()

    llm_cmd = os.environ.get("LLM_CMD") or "claude -p default -m claude-3-5-sonnet -t 0"
    if args.cmd == "run":
        if args.profile and "-p " not in llm_cmd:
            llm_cmd = f"claude -p {args.profile}"
        os.environ['LLM_EVAL_TOOLS_MODE'] = args.tools
        traj_path = run_eval(args.eval_md, args.tools, args.engine, llm_cmd, out_dir=args.out)
        return 0

    elif args.cmd == "translate":
        eval_id = os.path.splitext(os.path.basename(args.eval_md))[0]
        out_yaml = os.path.join("runtime", f"{eval_id}.eval.yaml")
        os.makedirs("runtime", exist_ok=True)
        translate_eval_md(args.eval_md, out_yaml, llm_cmd)
        print(out_yaml)
        return 0

    elif args.cmd == "grade":
        with open(args.trajectory_jsonl, 'r', encoding='utf-8') as f:
            first = f.readline()
        run_meta = json.loads(first)
        eval_id = run_meta.get("eval_id", "unknown")
        eval_yaml = os.path.join("runtime", f"{eval_id}.eval.yaml")
        res = grade_trajectory(args.trajectory_jsonl, eval_yaml)
        print(json.dumps(res, indent=2))
        if args.json_out:
            write_text(args.json_out, json.dumps(res, indent=2))
        if args.junit:
            junit = f"""<testsuite name="llm_eval" tests="1" failures="{1 if res['verdict']=='FAIL' else 0}" skipped="{1 if res['verdict']=='INCONCLUSIVE' else 0}" time="0.0">
  <testcase classname="{eval_id}" name="{os.path.basename(args.trajectory_jsonl)}" time="0.0">
    <system-out>{res['verdict']}: {res['reason']}</system-out>
  </testcase>
</testsuite>
"""
            write_text(args.junit, junit)
        if res['verdict'] == "PASS":
            return 0
        elif res['verdict'] == "INCONCLUSIVE":
            return 2
        else:
            return 1

    elif args.cmd == "matrix":
        with open(args.matrix, 'r', encoding='utf-8') as f:
            m = yaml.safe_load(f)
        evals = glob.glob(args.evals_glob)
        dims = m.get('dimensions', {})
        keys = list(dims.keys())
        vals = [dims[k] for k in keys]
        combos = list(itertools.product(*vals)) or [()]
        for e in evals:
            for combo in combos:
                env = os.environ.copy()
                model = None; tools = None; engine = None
                for k,v in zip(keys, combo):
                    if k == 'model': model = v
                    elif k == 'tools_mode': tools = v
                    elif k == 'engine': engine = v
                cmd = ["buck2","run","//:llm_eval","--","run", e]
                if tools: cmd += ["--tools", tools]
                if engine: cmd += ["--engine", engine]
                if model: env['LLM_CMD'] = f"claude -p default -m {model} -t 0"
                print("RUN:", " ".join(shlex.quote(x) for x in cmd))
                subprocess.run(cmd, env=env, check=False)
        return 0

    elif args.cmd == "shadow":
        from .shadow import shadow_run
        res = shadow_run(args.trajectory_jsonl, sample=args.sample, out_path=args.out)
        print(json.dumps(res, indent=2))
        return 0

    elif args.cmd == "shim":
        from .simulator import simulate
        argv0 = os.path.basename(args.argv0)
        cmdline = " ".join([argv0] + args.args)
        runtime_dir = os.environ.get("LLM_EVAL_RUNTIME_DIR", "runtime")
        eval_md = os.environ.get("LLM_EVAL_EVAL_MD")
        mocks_dir = os.environ.get("LLM_EVAL_MOCKS_DIR", "mocks")
        allow_help = os.environ.get("LLM_EVAL_ALLOW_HELP", "true") == "true"
        shim_dir = os.environ.get("LLM_EVAL_SHIM_DIR", ".mock/bin")
        # Build small world-state from recent trajectory (if available)
        world_state_text = ""
        traj_path = os.environ.get("LLM_EVAL_TRAJ_PATH")
        if traj_path and os.path.isfile(traj_path):
            try:
                import json, yaml as _yaml
                base = os.path.dirname(traj_path)
                with open(traj_path, "r", encoding="utf-8") as tf:
                    evs = [json.loads(l) for l in tf if l.strip()]
                last = [e for e in evs if e.get("event")=="tool_end"][-3:]
                lines = []
                for e in last:
                    sh = e.get("stdout_sha256")
                    p = os.path.join(base, "stdout", sh) if sh else None
                    out_prev = ""
                    if p and os.path.isfile(p):
                        with open(p, "r", encoding="utf-8") as pf:
                            out_prev = pf.read()
                    lines.append({"cmd": " ".join(e.get("argv", [])), "stdout": out_prev[:400]})
                world_state_text = _yaml.safe_dump({"recent_tool_outputs": lines}, sort_keys=False)
            except Exception:
                world_state_text = ""
        tool_md_path = os.path.join(mocks_dir, f"{argv0}.md")
        out = simulate(argv0, cmdline, eval_md, tool_md_path, llm_cmd, allow_help, shim_dir, world_state_text=world_state_text)
        sys.stdout.write(out)
        return 0

if __name__ == "__main__":
    sys.exit(main())
