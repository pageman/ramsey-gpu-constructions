# Job 6a — second solver on Yu residual 186

One short job. Not a hunt. Does not move \(R(4,20)\) off 252.

Same \(S\) as `data/yu_r4_20.json`. Residual 186 vertices. A program
**other than** `c-decide` answers: is there an independent set of size 19?

Writes `data/yu_r4_20.cert2.json`. Time budget: minutes
(`RAMSEY_6A_LIMIT`, default 180 s).

## What it runs

1. Builds the residual, writes `data/yu_r4_20.complement.clq` (DIMACS).
   A clique of size 19 in the complement is a residual 19-IS.
2. **OR-Tools CP-SAT** (if installed): decide \(\alpha\ge 19\) (expect
   INFEASIBLE) and \(\alpha\ge 18\) (Yu used this as a lower bound).
3. **Cliquer** (if `cliquer` is on `PATH`): clique 19 on the complement.

`second_solver_agrees` is true only if CP-SAT reports INFEASIBLE for 19
or Cliquer clearly reports no 19-clique. A timeout is not a proof.

Yu’s `certify_r420.cpp` is not in this repo (arXiv:2608.18169). If you
have that binary, run it on the DIMACS / residual yourself and keep the
log next to `cert2.json`. 6a does not download it.

## On the Mac (no SSH)

Prompt must be `paulpajo@…MacBook-Pro`.

```
cd ~/ramsey-gpu-constructions
git fetch origin
git merge origin/main
python3 -m pip install --user ortools
export RAMSEY_6A_LIMIT=180
python3 -u -m engine.cli --job 6a --scale local
```

Then:

```
python3 -c "import json; print(json.load(open('data/yu_r4_20.cert2.json'))['second_solver_agrees'])"
```

## On the pod (already SSH’d)

Prompt must be `root@…`.

```
cd /workspace/ramsey-gpu-constructions
git pull origin main || true
python3 -m pip install --user ortools
export RAMSEY_6A_LIMIT=180
python3 -u -m engine.cli --job 6a --scale runpod
```

Or, from the Mac, one line after you have HOST/PORT set:

```
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
ssh -i ~/.ssh/id_ed25519 -p $RAMSEY_POD_PORT root@$RAMSEY_POD_HOST "cd /workspace/ramsey-gpu-constructions && python3 -m pip install --user ortools && RAMSEY_6A_LIMIT=180 python3 -u -m engine.cli --job 6a --scale runpod"
```

Do not wrap this in tmux unless you set a limit of many minutes. Default
is three minutes.

## How to read the JSON

| Field | Meaning |
|---|---|
| `cpsat_18.found=true` | second solver found an 18-IS (Yu’s lower bound) |
| `cpsat_19.unsat=true` | second solver proved no 19-IS |
| `cpsat_19.timed_out=true` | not a proof; raise `RAMSEY_6A_LIMIT` or stop |
| `second_solver_agrees=true` | you may say two local backends agree with Yu on the residual |
| `second_solver_agrees=false` | missing package, timeout, or a 19-IS (the last would refute 252 — treat as a bug until replayed) |

Then copy `data/yu_r4_20.cert2.json` into `data/phase5/` if you are
archiving, commit, and `git push github main`.
