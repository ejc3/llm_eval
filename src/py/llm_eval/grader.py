import json, yaml

def grade_trajectory(traj_path: str, eval_yaml_path: str):
    with open(eval_yaml_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    heur = cfg.get('success', {}).get('heuristics', {})

    must_family = set(heur.get('must_use_family', []))
    terminal_any = set(heur.get('terminal_states_any', []))
    polling_required = heur.get('polling_required', False)
    single_target_required = heur.get('single_target_required', False)
    must_show_logs_after = heur.get('must_show_logs_after_terminal', False)
    inconclusive_on = heur.get('inconclusive_on', 'SIM-UNKNOWN')

    with open(traj_path, 'r', encoding='utf-8') as f:
        events = [json.loads(l) for l in f if l.strip()]

    used_family = False
    poll_count = 0
    terminal_state = None
    logs_after_terminal = False
    sim_unknowns = 0
    wrong_tool_nudges = 0

    for e in events:
        if e['event'] == 'nudge':
            wrong_tool_nudges += 1
        if e['event'] == 'tool_end':
            tool = e.get('tool')
            if must_family and tool in must_family:
                used_family = True
            if 'terminal_state' in e and e['terminal_state']:
                terminal_state = e['terminal_state']
            if e.get('stdout_text_contains_cat_after_terminal'):
                logs_after_terminal = True
        if e['event'] == 'assistant':
            if inconclusive_on in e.get('text', ''):
                sim_unknowns += 1
        if e.get('event') == 'tool_start' and 'status' in e.get('argv', []):
            poll_count += 1

    if sim_unknowns > 0 and not terminal_state:
        verdict = "INCONCLUSIVE"
        reason = "SIM-UNKNOWN observed without recovery."
    else:
        ok = True
        reasons = []
        if must_family and not used_family:
            ok = False; reasons.append("Required tool family not used.")
        if polling_required and poll_count < 2:
            ok = False; reasons.append("Polling not observed.")
        if terminal_any and terminal_state and terminal_state not in terminal_any:
            ok = False; reasons.append(f"Terminal state {terminal_state} not accepted.")
        if must_show_logs_after and terminal_state and not logs_after_terminal:
            ok = False; reasons.append("Logs not shown after terminal state.")
        verdict = "PASS" if ok else "FAIL"
        reason = "; ".join(reasons) if reasons else "Outcome achieved."

    return {
        "verdict": verdict,
        "reason": reason,
        "signals": {
            "used_family": used_family,
            "poll_count": poll_count,
            "terminal_state": terminal_state,
            "logs_after_terminal": logs_after_terminal,
            "sim_unknowns": sim_unknowns,
            "wrong_tool_nudges": wrong_tool_nudges,
        }
    }
