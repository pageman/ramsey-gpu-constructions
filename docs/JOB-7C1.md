# Job 7c1 — SAT-on-pool + residual-IS CEGIS (Look 6, after 7c)

CLI name: **`7c1`**. Prose name: **7c.1**. There is no `--job 7c.1`.

This is a **new hunt**, not more SAT seconds on 7c. 7a–7f are finished.
Do **not** run `bash scripts/pod-phase7.sh`. That re-enters 6a and can halt.

Published cell remains **252** unless a `CELL?` line fires **and** you replay
the certificate. Timeout ≠ accept. Residual \(n>256\) is a skip.

---

## 0. One-page contract

| | |
|---|---|
| Look | 6 (SAT / IP on the **connection set** \(S\), not on \(K_n\)) |
| Variables | one Boolean per undirected distance in a Yu 2-class pool \(D_i\cup D_j\) |
| Hard constraints | \(N(0)\) triangle-free (same 1-/2-/3-subset forbids as 7c); leftover \(\le 256\) |
| Objective | **Per-round** \(\max\lvert S\rvert\) (search bias so SAT does not return \(\emptyset\)). **Learning** = leftover-IS cuts. Not 7c’s one-shot pack-and-halt |
| Oracle | `c-decide` / `decide_alpha_le` on \(G[N^c(0)]\), target \(t-1\) |
| Learning | if the oracle **finds** an independent set \(I\), add a clause that \(S\) **hits** \(I\), resolve |
| Accept | residual unsat for a \((t-1)\)-IS **and** mixed-set **and** \(n+1\) beats `R4_LOWER` → `CELL?` |
| Open cells at \(n=251\) | \(R(4,17)\), \(R(4,18)\), \(R(4,19)\) only. 252 does **not** beat Yu 252 |

If you remember one sentence: **7c packed a fat \(S\); 7c1 cuts the leftover IS the referee already found.**

---

## 1. Why 7c is the wrong rerun

7c solved, once per pool:

```
max |S|
s.t. S ⊆ pool
     no 1-, 2-, or 3-subset of S makes N(0) contain a triangle
```

Residual **order** is \(p-1-2\lvert S\rvert\). Fatter \(S\) ⇒ smaller leftover.
On the A40 that produced \(\lvert S\rvert=52\)–\(88\), **greedy** \(\alpha=7\)–\(14\)
(already \(<17\)), then `c-decide` still **found a 16-IS** on the leftover.

Greedy had already “won.” Exact residual \(\alpha\) had not.

So:

| Temptation | Why it is not 7c1 |
|---|---|
| Raise `look6_sat` / rerun `--job 7c` | Same one fat \(S\) per pool, same 16-IS |
| Min greedy \(\alpha\) as a CP-SAT objective | Not linear; 7c already had greedy 7–14 |
| Encode “no 16-IS” up front | \(\binom{\sim 186}{16}\) clauses. That **is** the referee |
| SMS / SAT on \(K_{251}\) | Wrong aisle (Look 6 table in `docs/WHERE-TO-LOOK.md`) |
| `--job 7e` again | Look 4; Paley 2-block \(n\le 122\) never \(K_4\)-free |
| `phase7` / `pod-phase7.sh` | Re-runs 6a; 6a SAT-unsat-19 is still a **timeout** |

7c1 keeps 7c’s **variables, triangle-free clauses, and packing heuristic**,
and **does not halt at the first pack**. Each leftover IS becomes a clause;
the next Maximize is a *different* \(S\).

Empty \(S\) is triangle-free. A model with no objective returns \(\lvert S\rvert=0\),
greedy \(\alpha=p\), and never reaches the referee. That is why packing stays.

---

## 2. The cut, in the circulant dictionary

Vertices are \(\mathbb Z/p\mathbb Z\). Undirected Cayley: \(0\sim v\) iff the
circular distance \(\min(v,p-v)\) is in \(S\).

The leftover vertices are \(N^c(0)=\{1,\ldots,p-1\}\setminus N(0)\).

A leftover independent set \(I\) means:

1. no \(i\in I\) is adjacent to \(0\) → \(\min(i,p-i)\notin S\)
2. no two of \(I\) are adjacent → \(\min(\lvert v-u\rvert,\,p-\lvert v-u\rvert)\notin S\)

To **kill this particular \(I\)** the next \(S\) must hit it:

\[
\bigvee_{i\in I} x_{\min(i,p-i)}
\;\lor\;
\bigvee_{u<v\in I} x_{\min(\lvert v-u\rvert,\,p-\lvert v-u\rvert)}
\]

only those distances that actually sit in the **pool** become SAT literals.
If the clause is empty, the pool cannot kill \(I\): every \(S\subseteq\mathrm{pool}\)
still has this leftover IS. The model is forced unsat. That pool is **dead**
for this \(t\). Not a cell.

The native MIS kernel (`native_decide.c`) sets `FOUND=1` and does **not**
return \(I\). 7c1 reconstructs a witness with greedy (if greedy already
\(\ge t-1\)) else a short CP-SAT on the leftover (`extract_is_local`).
If reconstruction fails after `found=True`, 7c1 **nogoods that \(S\)** and
does **not** cut. Timeout ≠ cut.

---

## 3. Per-pool loop (what the code actually does)

For each Yu pool from `iter_yu_pools(p_lo, p_hi)` with `min_resid≤256`
and `r4_cells_open(p)` nonempty:

0. Build one CP-SAT model: triangle-free \(N(0)\) + leftover-width
   \(\lvert S\rvert \ge \lceil(p-1-256)/2\rceil\) (vacuous at \(p=251\)).
1. **Round \(r=1,2,\ldots\)** until `look6_rounds` or `look6_cegis` seconds.
2. Solve **\(\max\lvert S\rvert\)** (seeded). Same bias as 7c. Cuts make the next pack a new point.
3. `INFEASIBLE` → every remaining triangle-free \(S\) was cut. Next pool.
4. `UNKNOWN` → SAT timeout. **No cut.** Next pool.
5. If \(S\) is Yu’s published 32-set → nogood it. Not a new cell. Next round.
6. If \(N(0)\) has a triangle → nogood \(S\) (model bug / stale). Next round.
7. If leftover \(>256\) → nogood \(S\). Same void as 4a’s 354.
8. If greedy \(\alpha\) opens no \(t\) → nogood \(S\).
9. `certify_row_decision` / `decide_alpha_le` target \(t-1\), budget `yu_mis_limit`.
10. Residual **accept** (no \((t-1)\)-IS, tree finished) → mixed-set via
    `_emit_yu_hit`. `CELL?` only if mixed_ok and \(n+1\) beats published.
    Stop this pool.
11. **Timeout** → nogood this \(S\). **Do not cut.** Next round.
12. **Found IS** → reconstruct \(I\). If witness fails → nogood \(S\), no cut.
    If \(I\) checks independent → add the hit-\(I\) clause. Next round.

A **nogood** is “not this exact 0/1 vector on the pool.” A **cut** is the
hit-\(I\) clause. They are not the same.

---

## 4. Scale knobs (`engine/scale.py`)

| Key | local | runpod | Meaning |
|---|---|---|---|
| `look1_p_lo` / `look1_p_hi` | 251 / 251 | 251 / 400 | 7c1 uses the same keys as 7c. Runpod hi is **400** (the 313 in 7c’s fallback is unused because the key exists) |
| `look6_sat` | 8 s | 45 s | max SAT wall **per round** |
| `look6_cegis` | 20 s | 90 s | max wall **per pool** (all rounds) |
| `look6_rounds` | 8 | 32 | max CEGIS rounds per pool |
| `look6_witness` | 2 s | 3 s | CP-SAT to reconstruct \(I\) |
| `yu_mis_limit` | 8 s | 25 s | leftover decide per round |

Local also stops after **2 pools**. Runpod is not capped that way.

Env overrides:

| Env | Effect |
|---|---|
| `RAMSEY_SCALE=local\|runpod` | which row of `LIMITS` |
| `RAMSEY_FORCE_7=1` | ignore `data/phase7.halt` (6a never agreed) |
| `RAMSEY_SAT_WORKERS` | CP-SAT workers, default 8 |
| `RAMSEY_MIS_LIMIT` | fallback if a decide call has no explicit limit |

7c1 **does not** call `require_6a()`. Individual jobs never did. The halt
**file** still skips 7c1 unless `RAMSEY_FORCE_7=1`, same as 7c.

On the A40 night, 6a CP-SAT unsat-19 **timed out**. That is not a proof and
not a 19-IS. Hunting on the 5a/7a `c-decide` residual is what you already
did for 7b–7f. Set `RAMSEY_FORCE_7=1` if `data/phase7.halt` exists.

---

## 5. Preflight (pod). Do these in order. Do not skip.

SSH prompt must be `root@…`. If it is `paulpajo@…MacBook-Pro` you are on
the Mac. Stop. The job is an A40 night.

### 5.1 Land in the repo

SSH lands in `~`. `data/phase7.log` is **not** there.

```
pwd
cd /workspace/ramsey-gpu-constructions
pwd
ls engine/phase7.py engine/cegis_pool.py docs/JOB-7C1.md
```

You need `engine/cegis_pool.py`. If it is missing, you have not pulled this
commit.

### 5.2 Pull this commit

```
git fetch origin
git merge origin/main
git log -1 --oneline
python3 -c 'from engine.jobs import JOBS; assert "7c1" in JOBS; print("7c1 ok")'
```

If `assert` fires: you merged the wrong branch. Stop.

### 5.3 OR-Tools

7c already needed this. If 7c ran, you have it.

```
python3 -c 'from ortools.sat.python import cp_model; print("ortools ok")'
```

If missing:

```
python3 -m pip install --user ortools
```

No ortools → 7c1 prints `ortools missing` and exits 0 with `graphs=0`.
That is not a cell and not a crash.

### 5.4 Halt file

```
ls -l data/phase7.halt 2>/dev/null || echo 'no halt file'
```

If the file exists and you still want to hunt (6a timeout, 5a `c-decide` is
the residual proof):

```
export RAMSEY_FORCE_7=1
```

Put that **in the tmux command** below, not only in the outer shell, unless
you `export` before `tmux new-session` **and** pass it into the session
string. The snippet in §6 exports inside the tmux command.

### 5.5 Do not attach leftover sessions

```
tmux ls
```

| Session | Action |
|---|---|
| `ramsey` | leftover 2a. **Do not attach.** |
| `ramsey5` | phase5 done. **Do not attach.** |
| `ramsey7` | full phase7 wrapper. Do not start. |
| `ramsey7b`…`ramsey7f` | should be **gone**. If `ramsey7c1` already live, do not create a second |

### 5.6 Native decide `.so`

Warm from 7a. Optional recompile:

```
gcc -O3 -shared -fPIC -fopenmp -o engine/kernels/native_decide.so engine/kernels/native_decide.c \
  || gcc -O3 -shared -fPIC -o engine/kernels/native_decide.so engine/kernels/native_decide.c
```

### 5.7 Local wiring (Mac or pod, not the hunt)

On the Mac, after `git fetch` / `git merge origin/main`:

```
cd ~/ramsey-gpu-constructions
python3 engine/test_kernels.py
RAMSEY_FORCE_7=1 python3 -u -m engine.cli --job 7c1 --scale local
```

Local is **2 pools, 8 rounds, 20 s/pool**. It checks wiring (triangle-cuts, then leftover-IS-cuts). It will not mint 252. Do not read a local `graphs=0` as the A40 result.

---

## 6. Launch on the pod (exact)

Copy as a block. **zsh on the Mac:** `#` is **not** a comment. Do not paste
`# ...` on a zsh line. This block is for **bash on the pod**.

```
cd /workspace/ramsey-gpu-constructions
tmux new-session -d -s ramsey7c1 -c /workspace/ramsey-gpu-constructions 'export RAMSEY_FORCE_7=1 PYTHONUNBUFFERED=1; python3 -u -m engine.cli --job 7c1 --scale runpod 2>&1 | tee -a data/phase7.log'
tmux has-session -t ramsey7c1 && echo live
```

You will see `live` **before** any `[7c1]` line. That is the same race as 7e.
Do **not** run `tmux new-session -s ramsey7c1` again. Duplicate session.

Wait **five seconds**, then:

```
cd /workspace/ramsey-gpu-constructions
grep -n '\[7c1\]\|job 7c1' data/phase7.log | tail -n 30
tmux capture-pane -t ramsey7c1 -p | tail -n 40
```

You want:

```
== job 7c1  scale=runpod  device=cuda:NVIDIA A40 ...
  [7c1] Look 6 CEGIS p∈[251,400] rounds≤32 pool_wall=90s sat=45s mis=25s  per-round=max|S|; learning=leftover-IS-cuts (not one-shot 7c)
  [7c1] pool #1 p=251 e=… D…∪D… pool=… open_t=[17, 18, 19]
    [7c1] round 1/32 SAT FEASIBLE …
```

If the pane is still empty and `live`: import. Wait. Do not relaunch.

Detach stays detached. If you attach (`tmux attach -t ramsey7c1`), prefix
then `d`. **Do not type into the pane** (that is how 7b ate `^B`/`d`).

Or use the script (same thing, extra checks):

```
cd /workspace/ramsey-gpu-constructions
bash scripts/pod-7c1.sh
```

---

## 7. Every log line (decode while it runs)

| Line | Meaning | What you do |
|---|---|---|
| `== job 7c1  scale=runpod  device=cuda:NVIDIA A40` | CLI started, CUDA visible, A40 idle for this CPU job | nothing |
| `HALT file — skip` | `data/phase7.halt` and no `RAMSEY_FORCE_7` | export FORCE, relaunch **once** |
| `ortools missing` | no CP-SAT | pip install, relaunch once |
| `Look 6 CEGIS … leftover-IS-cuts` | banner. Confirm `leftover-IS-cuts` and `not one-shot 7c` | if you see only 7c packing and halt, wrong job |
| `skip … min_resid=…>256` | width gate. Same void as 4a | expected for fat \(e\) / small pool |
| `skip p=… no open R(4,t)` | \(n+1\) does not beat `R4_LOWER` | expected |
| `pool #k p=251 … open_t=[17, 18, 19]` | a real pool | watch rounds |
| `TRIANGLE-CUT \|lits\|=k` | 3-subset encoding missed a triangle in \(N(0)\) | expected; not a crash |
| `triangle-repair cap — fallback process+anneal` | Maximize kept packing \(K_4\)s; Yu process gives a triangle-free \(S\) to referee | expected; then greedyα / decide |
| `round r SAT INFEASIBLE` | cuts exhausted the pool | not a cell; next pool |
| `SAT UNKNOWN/timeout ≠ accept` | no \(S\), **no cut** | next pool |
| `recovered Yu S` | published 32-set | nogood; not a +1 |
| `\|S\|=… greedyα=… resid=… t_cell=17` | candidate | greedy 7–14 is a tease, same as 7c |
| `residual >256` | skip | not a cell |
| `decide … found=True …` | leftover has a \((t-1)\)-IS | expect a `CUT` or witness-fail |
| `timeout ≠ accept` | tree not finished | nogood \(S\); **no cut** |
| `witness \|I\|=16 independent=True` | reconstructed leftover IS | good |
| `found=True but witness extract failed` | cannot cut | nogood \(S\) only |
| `CUT \|lits\|=k kills_this_S=True` | clause added | this is 7c1 working |
| `empty cut — pool … dead` | pool cannot hit \(I\) | not a cell |
| `residual ACCEPT` | leftover has no \((t-1)\)-IS | read mixed / `CELL?` |
| `CELL? R(4,t) ≥ n+1` | residual **and** mixed **and** beats floor | **stop and replay** |
| `residual_only` | leftover decided; mixed hole | **not** a cell |
| `pool … done=unsat\|wall\|rounds\|accept` | that pool finished | next pool |
| `summary pools=… cuts=…` | job-level counts | |
| `job 7c1 done in …s  graphs=…` | process exit | session will vanish |

`graphs=` counts catalogue rows, **not** published +1. 7c had 163 graphs and
zero `CELL?`. 7c1 can print many graphs the same way.

---

## 8. When is it done?

Session gone:

```
tmux has-session -t ramsey7c1 && echo live
```

`can't find session: ramsey7c1` plus `job 7c1 done` in the log.

### Fermi (runpod)

Let \(P\) = number of pools with `min_resid≤256` in \(p\in[251,400]\)
(7c reported **163 graphs**, same generator, so \(P\sim 10^2\)).

Per pool, worst case: `look6_cegis=90` s. \(100\times 90\,\mathrm{s}=9000\,\mathrm{s}\approx 2.5\,\mathrm{h}\).

Typical 7c decide was **milliseconds** on a found 16-IS, SAT was the bulk.
7c1 SAT is **feasibility** after cuts, usually cheaper than 7c’s 45 s
`Maximize`. Median guess: **20–60 s/pool** if IS cuts fire immediately
(7c’s pattern) → **0.5–2 h** for the window.

If many SAT `UNKNOWN` at 45 s: closer to the 90 s/pool cap.

A40 GPU stays idle. This is OR-Tools + `c-decide` on CPU.

---

## 9. How to decide if the thesis lived or died

After `job 7c1 done`, from the repo cwd:

```
grep -c 'CELL?' data/phase7.log
grep '\[7c1\] summary' data/phase7.log | tail
grep -c 'CUT |lits|' data/phase7.log
grep -c 'timeout ≠ accept' data/phase7.log
grep -c 'pool UNSAT' data/phase7.log
grep -c 'empty cut' data/phase7.log
```

| Pattern | Thesis |
|---|---|
| `cuts` ≫ 0, no `CELL?`, many `found=True` | generator+cuts **work**; leftover \(\alpha\) still \(\ge t-1\). Falsified as a cell machine on this window |
| `pool UNSAT` on Yu’s \((p,e,i,j)\) | that 2-class cannot hide a 16-IS. Strong negative for that pool |
| `empty cut` | pool algebra cannot hit the leftover IS. Pool dead |
| `CELL?` | **stop.** Replay mixed-set and DS1. Do not keep hunting |
| `cuts=0` and only `max` behaviour | you launched **7c** by mistake |
| lots of `timeout ≠ accept` | leftover decide budget too small; **do not** treat as accept; raising `yu_mis_limit` is a different job |

Success is still Radziszowski finite +1, not \(C\ge 1.01\), not “more cuts.”

---

## 10. What not to do (checklist)

- Do not `bash scripts/pod-phase7.sh`
- Do not `--job 7c` or `--job phase7`
- Do not raise `RAMSEY_6A_LIMIT` expecting unsat-19
- Do not raise `look6_sat` on 7c instead of running 7c1
- Do not attach `ramsey` / `ramsey5`
- Do not `tmux new-session -s ramsey7c1` a second time
- Do not type into the tmux pane
- Do not Terminate the pod (Stop is OK after scp)
- Do not emit `CELL?` from residual-only
- Do not start 7e.1 in the same night
- Do not rerun Coniglio \(R(3,24)\)–\(49\)
- Do not wait for ILS step lines (7c1 has rounds, not 5d steps)

---

## 11. After the run (archive)

```
cd /workspace/ramsey-gpu-constructions
tmux has-session -t ramsey7c1 && echo live
tail -n 40 data/phase7.log
python3 -c 'import json; print(json.load(open("data/phase7.status.json")))'
```

Copy off the pod (from the Mac, with your current HOST/PORT):

```
scp -P $RAMSEY_POD_PORT -i ~/.ssh/id_ed25519 \
  root@$RAMSEY_POD_HOST:/workspace/ramsey-gpu-constructions/data/phase7.log \
  ~/ramsey-gpu-constructions/data/phase7-7c1.log
```

Live `phase7.status.json` / `cert2` are gitignored. Commit the **log excerpt
and this doc** from the Mac after `git fetch origin && git merge origin/main`.
Agent pushes Origin only. You push GitHub.

Then **Stop** the pod. Do not Terminate.

---

## 12. Code map

| File | Role |
|---|---|
| `engine/cegis_pool.py` | triangle-free model, feasible solve, witness extract, hit-\(I\) lits |
| `engine/phase7.py` `job_7c1` | pool loop, logging, halt, `_emit_yu_hit` |
| `engine/kernels/bitset_mcs.py` `greedy_mis_set` | greedy witness when greedy already \(\ge t-1\) |
| `engine/kernels/decide_alpha.py` | leftover decide; mixed-set before `CELL?` |
| `engine/scale.py` | `look6_rounds` / `look6_cegis` / `look6_witness` |
| `engine/jobs.py` / `registry.py` | `--job 7c1` |
| `scripts/pod-7c1.sh` | pod launcher (not phase7) |
| `engine/test_kernels.py` | cut excludes \(S\); empty cut; `7c1` registered |

7c1 is **not** in `job_phase7()`’s list. That is deliberate.

---

## 13. 7e.1 is not this job

Two-orbit + residual contract at \(200\le n\le 256\) is **7e.1**. Different
look. Do not start it until 7c1 has a `job 7c1 done` line and you have read
§9.

---

## 14. Number that is still true

Until `CELL?` fires and you replay: **\(R(4,20)\ge 252\)** (Yu). Paley(17)
exact. Yu leftover 186: no 19-IS under `c-decide` (5a/7a). 6a SAT-unsat-19
is still a timeout. Width gate held through 7a–7f.
