import os, json, random, subprocess
from typing import Dict, Any
from .utils import which_skip_shim, text_canonicalize, similarity

def shadow_run(traj_path: str, sample: int = 25, out_path: str = None) -> Dict[str, Any]:
    base = os.path.dirname(traj_path)
    with open(traj_path, 'r', encoding='utf-8') as f:
        events = [json.loads(l) for l in f if l.strip()]
    tool_calls = [e for e in events if e.get('event') == 'tool_end' and isinstance(e.get('argv'), list)]
    random.shuffle(tool_calls)
    tool_calls = tool_calls[:sample] if sample > 0 else tool_calls
    results = []
    shim_dir = os.environ.get("LLM_EVAL_SHIM_DIR", ".mock/bin")
    for e in tool_calls:
        argv = e['argv']
        tool = argv[0]
        real = which_skip_shim(tool, shim_dir)
        if not real:
            results.append({"argv": argv, "skipped": True, "reason": "no_real_binary"})
            continue
        sidecar = os.path.join(base, "stdout", e.get("stdout_sha256",""))
        sim_out = ""
        try:
            with open(sidecar, 'r', encoding='utf-8') as sf:
                sim_out = sf.read()
        except Exception:
            pass
        try:
            proc = subprocess.run([real] + argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20, cwd=base)
            real_out = proc.stdout
            can_sim = text_canonicalize(sim_out)
            can_real = text_canonicalize(real_out)
            sim = similarity(can_sim, can_real)
            results.append({
                "argv": argv, "similarity": sim, "sim_len": len(sim_out), "real_len": len(real_out),
                "pass": sim >= 0.80, "real_rc": proc.returncode
            })
        except Exception as ex:
            results.append({"argv": argv, "error": str(ex)})
    summary = {
        "trajectory": traj_path,
        "checked": len(results),
        "pass": sum(1 for r in results if r.get("pass")),
        "fail": sum(1 for r in results if r.get("pass") == False),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "threshold": 0.80,
        "results": results,
    }
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
    return summary
