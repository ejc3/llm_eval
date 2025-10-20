# Tool: kubectl (read-only simulation)

## Overview
Kubernetes CLI. This mock allows only read‑only verbs: `get`, `describe`, `logs`. Other verbs should be blocked with a reminder.

## Output Style
- `get` shows tabular output with headers.
- `describe` shows multi‑section resource details (annotations, selectors, events).
- `logs` prints timestamped lines; `-f` (follow) is not simulated.

## Behavior Notes
- Canary rollout example: deployment `web` in `prod` targeting 10% canary may show READY like `9/10` initially, then `10/10`.
- `get deploy web -n prod -o wide` includes image tags and availability.
- When resource is missing: "Error from server (NotFound): <kind> '<name>' not found"

## Examples
$ kubectl get deploy web -n prod
NAME   READY   UP-TO-DATE   AVAILABLE   AGE
web    9/10    10           9           21d

$ kubectl describe deploy web -n prod
Name:                   web
Namespace:              prod
Selector:               app=web
Replicas:               10 desired | 10 updated | 9 available | 1 unavailable
StrategyType:           RollingUpdate
...
Events:
  Normal  ScalingReplicaSet  ...  Scaled up replica set web-7f9d to 10

$ kubectl logs deploy/web -n prod --tail=20
2025-10-10T20:01:12Z GET /healthz 200
2025-10-10T20:01:13Z GET /api/v1/canary 200
...

## Edge Cases
- Insufficient permissions: "Error from server (Forbidden): ..."
- Pod churn: logs may show gaps; still print recent lines.

## Mutating Verbs (blocked)
- `apply`, `delete`, `scale`, `rollout restart`, etc. Should be blocked with:
READ-ONLY: kubectl mutating command blocked; use get/describe/logs.

## Fallback
If unsure, print exactly:
SIM-UNKNOWN::kubectl::insufficient-context
