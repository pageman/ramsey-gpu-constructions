# Phase 7 — Look 1–6 after 6a

The night that follows [`docs/WHERE-TO-LOOK.md`](WHERE-TO-LOOK.md).
**6a is the gate.** Phase 7 will not hunt until
`data/yu_r4_20.cert2.json` has `second_solver_agrees=true`, unless you
set `RAMSEY_FORCE_7=1`.

Does not move 252 by existing. A real +1 prints `CELL?` and still needs
the mixed-set flag. Timeout ≠ accept. Residual `n>256` is a skip.

## Order

| Job | Look | What |
|---|---|---|
| **6a** | gate | CP-SAT / Cliquer on Yu residual 186. See [`JOB-6A.md`](JOB-6A.md). |
| **7a** | 3 | Referee bench: Paley(17) regression; on runpod, retime Yu 186 with colour+flatten. |
| **7b** | 1 | Other `(i,j)` at 251, then primes with `min_resid≤256`. Open cells: \(R(4,17)\)–\(19\) at \(n=251\) (252 does **not** beat Yu); \(t=20\) only for \(n\ge 257\). |
| **7c** | 6 | SAT maximises \(\lvert S\rvert\) inside a Yu pool, then the same residual referee. |
| **7c1** | 6′ | **Follow-on, not in `phase7`.** Same pools; drop \(\max\lvert S\rvert\); cut on leftover IS. See [`JOB-7C1.md`](JOB-7C1.md). |
| **7d** | 2 | \(R(3,t)\) \(t\ge 50\) only. Local scale has \(t=12\) and **skips**. |
| **7e** | 4 | 2-polycirculant, \(n\le 256\), decision \(\alpha\), not Hoffman. |
| **7f** | 5 | Polarity leftover + floor gate (same as 5e). |

## On the pod (already SSH’d)

Prompt must be `root@…`. Do **not** attach tmux `ramsey`.

```
cd /workspace/ramsey-gpu-constructions
git pull origin main
python3 -m pip install --user ortools
export RAMSEY_6A_LIMIT=600
bash scripts/pod-phase7.sh
```

That script creates tmux `ramsey7`, runs 6a if needed, then 7a–7f.
Log: `data/phase7.log`. Status: `data/phase7.status.json`.

```
bash scripts/phase7-status.sh
tmux attach -t ramsey7
```

## On the Mac (no SSH)

Phase 7’s hunt is an A40 night. Local scale only checks the wiring:

```
cd ~/ramsey-gpu-constructions
git fetch origin && git merge origin/main
python3 engine/test_kernels.py
RAMSEY_FORCE_7=1 python3 -u -m engine.cli --job 7a --scale local
```

`FORCE_7` is for the Mac / CI. Do not set it on the pod unless 6a
timed out and you accept hunting on the 5a `c-decide` cert alone.

## How to read it

| Line | Meaning |
|---|---|
| `6a GREEN` | second solver agrees: no 19-IS |
| `CELL? R(4,t) ≥ n+1` | residual accept **and** mixed-set. Still check DS1 for \(t=23,24\) (monotonic floor 314). |
| `residual_only` | residual decided; mixed-set hole. Not a cell. |
| `min_resid>256` | Look 1 gate. Same void as 4a’s 354. |
| `timeout ≠ accept` | not a proof |
| `HALT. 6a timeout` | raise `RAMSEY_6A_LIMIT` or install ortools; do not hunt |

Published cell remains **252** unless a `CELL?` line fired and you
replayed the certificate.

## After 7a–7f (Look 6 CEGIS)

7c maximised \(\lvert S\rvert\). The leftover still had a 16-IS. The next
search change is **`--job 7c1`**, not more SAT seconds and not `pod-phase7.sh`.

Full operator guide: [`JOB-7C1.md`](JOB-7C1.md).

```
cd /workspace/ramsey-gpu-constructions
git pull origin main
bash scripts/pod-7c1.sh
```

