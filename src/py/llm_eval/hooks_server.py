#!/usr/bin/env python3
import os, sys, json, time

def main():
    if len(sys.argv) < 2:
        print("usage: hooks_server.py <event>", file=sys.stderr)
        sys.exit(2)
    event = sys.argv[1]
    payload = sys.stdin.read()
    try:
        obj = json.loads(payload) if payload.strip() else {}
    except Exception:
        obj = {"raw": payload}
    traj = os.environ.get("LLM_EVAL_TRAJ_PATH")
    if traj:
        with open(traj, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event": f"hook_{event}", "payload": obj, "ts": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}) + "\n")
    print(json.dumps({"action": "allow"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
