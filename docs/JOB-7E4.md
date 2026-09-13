# Job 7e4 — CP-SAT CEGIS on two-orbit (S0,S1) with leftover-IS cuts

CLI name: **`7e4`**. Prose name: **7e.4**. There is no `--job 7e.4`.

This is a **new hunt** on two-block circulants, NOT a rerun of 7c or 7e.
Do **not** run `bash scripts/pod-phase7.sh`. That re-enters 6a and can halt.

Published cell remains **252** unless a `CELL?` line fires **and** you replay
the certificate. Timeout ≠ accept. Residual \(n>256\) is a skip.

---

## 0. One-page contract

| | |
|---|---|
| Look | 4 (two-orbit 2-block circulant on 2m vertices) |
| Variables | O(m) inversion-closed free bits of (S0, S1): floor(m/2) per block |
| Hard constraints | Neighbourhood triangle-free (including cross-block S1 triangles) |
| Objective | **Feasibility / random feasible** (NOT maximize \|S0\|+\|S1\|) |
| Oracle | `decide_alpha_le` on **full graph** nbr (not residual), target t |
| Learning | if oracle **finds** a t-IS I, add hitting clause on free bits, resolve |
| Accept | full-graph α < t **and** mixed-set **and** \(n+1\) beats `R4_LOWER` → `CELL?` |
| Cut cap | 20 cuts per m (not per pool — this is per modulus) |
| Priority targets | t = 20, 21, then other open t with n+1 > R4_LOWER[t] |
| Open cells at n=252 | R(4,20), R(4,21) only at 252; 126→250,251; 128→254,255,256 |

**One sentence:** 7e4 does CEGIS on the O(m) free bits of a 2-block circulant,
cuts leftover independent sets on the **full graph** (not residual), and caps
cuts at 20/m.

---

## 1. Why NOT 7c, NOT 7e, NOT maximize |S|

| Temptation | Why it is not 7e4 |
|---|---|
| Rerun `--job 7c` | Wrong variables (Yu pool distances vs two-orbit free bits) |
| Rerun `--job 7e` | 7e is single-round ILS, not CEGIS; no cuts |
| Maximize \|S0\|+\|S1\| | Contract forbids; leftover becomes enormous |
| Raise `look6_sat` / more rounds on 7c | 7c is Yu pools, not two-block |
| SMS / SAT on full \(K_n\) | Wrong aisle (Look 6 is connection-set SAT) |
| Unbounded cuts | Cut saturation at 20/m is a design constraint |

7e4 keeps the **two-orbit inversion-closure parametrization** (O(m) variables
instead of O(n²)), adds **hard triangle-free clauses** (same as 7c's N(0)
encoding but for cross-block edges), and uses **feasibility** or a mild degree
soft bound (NOT packing) so the leftover stays ≲200 vertices.

---

## 2. Variables and inversion closure

A 2-block circulant on 2m vertices has two blocks of m vertices. Edges:
- within block b: circulant connection set S_b
- cross-block: circulant connection set S₁

Inversion closure: if d ∈ S_b, then (m-d) ∈ S_b. This reduces free bits from
m to floor(m/2) per block. S_b[0]=0 by construction.

Total free bits: 2 * floor(m/2). At m=126, that's 2×63=126 free bits (vs
251²/2 ≈ 31k for a Yu pool at p=251).

### Warm-starts from 7e1

When `RAMSEY_7E4_WARM=1`, the job scans `data/phase7/7e1/` for dumps matching
`m{m}_r{restart}.json` (where restart is an integer). It prefers K4-free dumps
with the lowest greedy α, then converts (S0, S1) arrays to free bits via
`s0_s1_to_bits` and hints CP-SAT with `model.AddHint`. Expected dump schema:

```json
{
  "m": 126,
  "n": 252,
  "restart": 0,
  "s0": [0, 1, 0, ...],  // m-length indicator array or distance list
  "s1": [0, 0, 1, ...],
  "k4_free": true,
  "greedy_alpha": 18
}
```

If no dumps exist or none match, the job skips warm-start cleanly.

---

## 3. The cut (hitting clause on free bits)

When the referee finds a t-IS I on the **full graph**, the next (S0,S1) must
**hit I**: put an edge with both endpoints in I.

For each pair (a,b) in I:
- same block → need the intra-block distance in S0
- cross-block → need the cross-block distance in S1

Only distances ≤ floor(m/2) become free-bit lits. If no lits, the model is
unsat (this set of free bits cannot kill I). Otherwise, at least one lit must
be true.

---

## 4. Per-m loop (what the code actually does)

For each m in `RAMSEY_7E4_M` (default 126,128 runpod / 101,113 local; m≥101 needed for open R(4,t) at n≥202):

0. Build one CP-SAT model: triangle-free N(0) (including cross-block).
   - Optional: apply warm-start hint from 7e1 dumps if `RAMSEY_7E4_WARM=1`.
1. **Round r=1,2,...** until `RAMSEY_7E4_ROUNDS` or `RAMSEY_7E4_POOL_WALL` seconds.
2. Solve **feasibility** (seeded). NOT maximize |S|. Cuts make the next solve a new point.
3. `INFEASIBLE` → every remaining triangle-free (S0,S1) was cut. Next m.
4. `UNKNOWN` → SAT timeout. **No cut.** Next m.
5. **Triangle repair loop** (lazy CEGIS, up to `RAMSEY_7E4_TRI_FIX` iterations):
   - If NOT K4-free → find triangle support bits → add triangle cut → re-solve.
   - If still NOT K4-free after cap → nogood (S0,S1). Next round.
   - If pool_wall exhausted during repair → nogood. Next m.
6. Greedy α on full graph.
7. For each t in priority list (20, 21, then other open):
   - `decide_alpha_le` target t, budget `RAMSEY_7E4_MIS` seconds.
   - Residual **accept** (no t-IS, tree finished) → mixed-set. `CELL?` only if
     mixed_ok and n+1 beats published. Stop this m.
   - **Timeout** → nogood (S0,S1). **Do not cut.** Next round.
   - **Found t-IS** → extract witness I with `extract_is_full_graph`. If
     witness fails → nogood, no cut. If I checks independent → add hitting
     clause. Cut counter += 1. If cut_count ≥ 20 → stop this m. Next round.
8. If cut_count ≥ 20 → `cuts_saturated`. Next m.

A **nogood** is "not this exact 0/1 vector on the free bits." A **cut** is the
hit-I clause. They are not the same.

---

## 5. Scale knobs

| Key | local | runpod | Meaning |
|---|---|---|---|
| `RAMSEY_7E4_M` | 101,113 | 126,128 | Comma-separated moduli (n=2m); m≥101 for open cells |
| `RAMSEY_7E4_CUTS` | 5 | 20 | Cut cap per m |
| `RAMSEY_7E4_ROUNDS` | 4 | 16 | Max CEGIS rounds per m |
| `RAMSEY_7E4_SAT` | 8 s | 30 s | Max SAT wall per round |
| `RAMSEY_7E4_POOL_WALL` | 20 s | 90 s | Max wall per m (all rounds) |
| `RAMSEY_7E4_MIS` | 8 s | 25 s | Full-graph decide per round |
| `RAMSEY_7E4_TRI_FIX` | 12 | 24 | Triangle-repair budget per round |
| `RAMSEY_7E4_WARM` | 0 | 0 | Load warm-starts from `data/phase7/7e1/` if =1 |

Env overrides:

| Env | Effect |
|---|---|
| `RAMSEY_SCALE=local\|runpod` | which row of defaults |
| `RAMSEY_FORCE_7=1` | ignore `data/phase7.halt` (6a never agreed) |
| `RAMSEY_SAT_WORKERS` | CP-SAT workers, default 8 |

7e4 **does not** call `require_6a()` directly. Individual jobs never did. The
halt **file** still skips 7e4 unless `RAMSEY_FORCE_7=1`, same as 7c1.

---

## 6. Preflight (pod or Mac)

### 6.1 Land in the repo

```bash
pwd
cd /workspace/ramsey-gpu-constructions
ls engine/phase7.py engine/cegis_two_block.py docs/JOB-7E4.md
```

### 6.2 OR-Tools

```bash
python3 -c 'from ortools.sat.python import cp_model; print("ortools ok")'
```

If missing:

```bash
python3 -m pip install --user ortools
```

### 6.3 Halt file

```bash
ls -l data/phase7.halt 2>/dev/null || echo 'no halt file'
```

If the file exists and you still want to hunt:

```bash
export RAMSEY_FORCE_7=1
```

### 6.4 Native decide `.so`

Warm from 7a. Optional recompile:

```bash
gcc -O3 -shared -fPIC -fopenmp -o engine/kernels/native_decide.so engine/kernels/native_decide.c \
  || gcc -O3 -shared -fPIC -o engine/kernels/native_decide.so engine/kernels/native_decide.c
```

---

## 7. Local wiring (Mac or pod, not the hunt)

### Without 7e1 warm-starts (basic wiring)

```bash
cd /workspace/ramsey-gpu-constructions
python3 engine/test_kernels.py
RAMSEY_FORCE_7=1 RAMSEY_7E4_M=101 RAMSEY_7E4_CUTS=3 RAMSEY_7E4_TRI_FIX=12 python3 -u -m engine.cli --job 7e4 --scale local
```

Local default is **m=101,113; 4 rounds, 5 cuts cap, 12 tri_fix, 20 s/m**.
Note: m=17 will skip (no open R(4,t) cells at n=34). It checks wiring(triangle-cuts, leftover-IS-cuts). It will not mint 252. Do not read a local
`graphs=0` as the runpod result.

### With 7e1 warm-starts (recommended for m=126)

If you have 7e1 dumps at `data/phase7/7e1/m126_r*.json`:

```bash
cd /workspace/ramsey-gpu-constructions
RAMSEY_FORCE_7=1 RAMSEY_7E4_M=126 RAMSEY_7E4_WARM=1 RAMSEY_7E4_CUTS=8 RAMSEY_7E4_ROUNDS=6 RAMSEY_7E4_TRI_FIX=16 python3 -u -m engine.cli --job 7e4 --scale local
```

This will:
- Load K4-free (S0,S1) from a 7e1 dump as warm-start
- Run 6 rounds with higher triangle-repair budget (16 instead of 4)
- Attempt to reach K4_free=True and call decide_alpha_le

Expected log lines:
```
  [7e4] loaded warm-start from m126_r0.json (restart=0, K4_free=True, greedyα=18)
  [7e4] applied warm-start hint: 42/126 bits set
  ...
    [7e4]   |S0|=21 |S1|=18 deg(0)=67 leftover=184 K4_free=True greedyα=18
    [7e4]   decide α≥20 found=False timeout=False exact=True backend=...
```

If you don't have 7e1 dumps, job_7e1 must be run first, or accept that m=126
local smoke without warm-starts may hit triangle-repair treadmill.

---

## 8. Launch on the pod (exact)

Copy as a block. This block is for **bash on the pod**.

```bash
cd /workspace/ramsey-gpu-constructions
tmux new-session -d -s ramsey7e4 -c /workspace/ramsey-gpu-constructions \
  'export RAMSEY_FORCE_7=1 PYTHONUNBUFFERED=1; \
   python3 -u -m engine.cli --job 7e4 --scale runpod 2>&1 | tee -a data/phase7.log'
tmux has-session -t ramsey7e4 && echo live
```

Wait **five seconds**, then:

```bash
cd /workspace/ramsey-gpu-constructions
grep -n '\[7e4\]\|job 7e4' data/phase7.log | tail -n 30
tmux capture-pane -t ramsey7e4 -p | tail -n 40
```

You want:

```
== job 7e4  scale=runpod  device=cuda:NVIDIA A40 ...
  [7e4] Look 4 / R(4,20)≥252 CEGIS on two-orbit (S0,S1) m=[126, 128] ...
  [7e4] m=126 n=252 open_t=[20, 21] priority=[20, 21] free_bits=126
    [7e4] round 1/16 SAT FEASIBLE ...
```

---

## 9. Every log line (decode while it runs)

| Line | Meaning | What you do |
|---|---|---|
| `== job 7e4  scale=runpod  device=cuda:NVIDIA A40` | CLI started | nothing |
| `HALT file — skip` | `data/phase7.halt` and no `RAMSEY_FORCE_7` | export FORCE, relaunch once |
| `ortools missing` | no CP-SAT | pip install, relaunch once |
| `Look 4 / R(4,20)≥252 CEGIS` | banner. Confirm `NOT maximize \|S\|` and `tri_fix_cap` | if you see maximize, wrong job |
| `loaded warm-start from ...` | 7e1 dump found and applied | warm-start working |
| `no K4-free 7e1 dumps found` | no warm-start available | expected if 7e1 not run |
| `skip m=... n=>256` | referee gate (decide_alpha n≤256) | expected |
| `skip m=... no open R(4,t)` | n+1 does not beat `R4_LOWER` | expected |
| `m=126 n=252 open_t=[20, 21]` | a real m | watch rounds |
| `N(0) triangle fix=X/Y TRIANGLE-CUT` | lazy triangle repair (X of Y budget) | expected during repair |
| `triangle-repair cap hit (Y)` | hit `RAMSEY_7E4_TRI_FIX` cap, nogood | expected; raised from 4 to 12/24 |
| `pool_wall exhausted during triangle-repair` | time limit during repair | nogood, next m |
| `round r SAT INFEASIBLE` | cuts exhausted free bits | not a cell; next m |
| `SAT UNKNOWN/timeout ≠ accept` | no bits, **no cut** | next m |
| `greedyα=... ≥ t` | skip decide for this t | greedy already rejected |
| `decide α≥t found=True ...` | full graph has a t-IS | expect a `CUT` or witness-fail |
| `timeout ≠ accept` | tree not finished | nogood bits; **no cut** |
| `witness \|I\|=... independent=True` | reconstructed full-graph IS | good |
| `found=True but witness extract failed` | cannot cut | nogood bits only |
| `CUT \|lits\|=k` | clause added | this is 7e4 working |
| `empty cut — free bits cannot hit I` | model unsat | not a cell |
| `cuts saturated at 20` | cap reached | next m |
| `residual_only` | full-graph decided; mixed hole | **not** a cell |
| `CELL? R(4,t) ≥ n+1` | full-graph **and** mixed **and** beats floor | **stop and replay** |
| `m=... done=unsat\|wall\|rounds\|cuts_saturated\|accept` | that m finished | next m |
| `summary ms=... cuts=...` | job-level counts | |
| `job 7e4 done in ...s  graphs=...` | process exit | session will vanish |

`graphs=` counts catalogue rows, **not** published +1. 7e4 can print many
graphs the same way 7c1 did.

---

## 10. When is it done?

Session gone:

```bash
tmux has-session -t ramsey7e4 && echo live
```

`can't find session: ramsey7e4` plus `job 7e4 done` in the log.

### Fermi (runpod)

Let M = number of moduli (default 2: m=126,128).

Per m, worst case: `RAMSEY_7E4_POOL_WALL=90` s. 2×90 s = 180 s ≈ 3 min.

Typical decide at m=126,128 on full graph (n=252,256): if α is small, decide
can be milliseconds (greedy wins); if α is near t, the tree is large. SAT is
the bulk after triangle enumeration finishes.

Median guess: **10–60 s/m** if IS cuts fire quickly → **20 s – 2 min** for
the default window.

If many SAT `UNKNOWN` at 30 s or decide timeouts: closer to the 90 s/m cap.

A40 GPU stays idle. This is OR-Tools + `decide_alpha_le` on CPU.

---

## 11. How to decide if the thesis lived or died

After `job 7e4 done`, from the repo cwd:

```bash
grep -c 'CELL?' data/phase7.log
grep '\[7e4\] summary' data/phase7.log | tail
grep -c 'CUT |lits|' data/phase7.log
grep -c 'timeout ≠ accept' data/phase7.log
grep -c 'pool UNSAT' data/phase7.log
grep -c 'empty cut' data/phase7.log
grep -c 'cuts saturated' data/phase7.log
```

| Pattern | Thesis |
|---|---|
| `cuts` ≫ 0, no `CELL?`, many `found=True` | generator+cuts **work**; full-graph α still ≥ t. Falsified as a cell machine on this window |
| `pool UNSAT` on m | that m's free bits cannot hide a t-IS. Strong negative |
| `empty cut` | free bits cannot hit the full-graph IS. Model dead |
| `cuts_saturated` | 20 cuts reached; model may still be SAT |
| `CELL?` | **stop.** Replay mixed-set and DS1. Do not keep hunting |
| `cuts=0` and only feasibility | you launched **7e** by mistake (no CEGIS) |
| lots of `timeout ≠ accept` | full-graph decide budget too small; **do not** treat as accept; raising `RAMSEY_7E4_MIS` is a different job |

Success is still Radziszowski finite +1, not \(C\ge 1.01\), not "more cuts."

---

## 12. What not to do (checklist)

- Do not `bash scripts/pod-phase7.sh`
- Do not `--job 7c` or `--job 7c1` or `--job 7e` or `--job phase7`
- Do not raise `RAMSEY_6A_LIMIT` expecting unsat-19
- Do not set `RAMSEY_7E4_CUTS` > 20 per m in this wave
- Do not raise `RAMSEY_7E4_M` to 512 (n=1024 > 256 referee gate)
- Do not attach `ramsey` / `ramsey5`
- Do not `tmux new-session -s ramsey7e4` a second time
- Do not type into the tmux pane
- Do not Terminate the pod (Stop is OK after scp)
- Do not emit `CELL?` from residual-only
- Do not start 7e.5 (Waves C/D/E) in the same night
- Do not maximize |S0|+|S1| as the default objective
- Do not change MAXN=256
- Do not mix unrelated docs from other jobs

---

## 13. After the run (archive)

```bash
cd /workspace/ramsey-gpu-constructions
tmux has-session -t ramsey7e4 && echo live
tail -n 40 data/phase7.log
python3 -c 'import json; print(json.load(open("data/phase7.status.json")))'
```

Copy off the pod (from the Mac, with your current HOST/PORT):

```bash
scp -P $RAMSEY_POD_PORT -i ~/.ssh/id_ed25519 \
  root@$RAMSEY_POD_HOST:/workspace/ramsey-gpu-constructions/data/phase7.log \
  ~/ramsey-gpu-constructions/data/phase7-7e4.log
scp -P $RAMSEY_POD_PORT -i ~/.ssh/id_ed25519 \
  root@$RAMSEY_POD_HOST:/workspace/ramsey-gpu-constructions/data/phase7/7e4/*.json \
  ~/ramsey-gpu-constructions/data/phase7/7e4/
```

Then **Stop** the pod. Do not Terminate.

---

## 14. Code map

| File | Role |
|---|---|
| `engine/cegis_two_block.py` | free bits, triangle-free model, witness extract, hit-I lits |
| `engine/phase7.py` `job_7e4` | m loop, logging, halt, CEGIS rounds, decide_alpha_le on full graph |
| `engine/kernels/cayley.py` `two_block_adj` | 2-block circulant adjacency |
| `engine/kernels/decide_alpha.py` | full-graph decide; mixed-set before `CELL?` |
| `engine/test_kernels.py` | inversion round-trip; hitting clause; empty cut; `7e4` registered |
| `engine/jobs.py` / `registry.py` | `--job 7e4` |
| `docs/JOB-7E4-PLAN.md` | Waves A–E summary and non-goals |

7e4 is **not** in `job_phase7()`'s list. That is deliberate.

---

## 15. Waves C/D/E are NOT in this PR

This PR contains Waves A–B only: scaffolding + operator surface. Waves C/D/E
(pod night, full hunt, result analysis) are future work. Do not run the pod
night until Waves A–B tests pass locally.

---

## 16. Number that is still true

Until `CELL?` fires and you replay: **R(4,20)≥252** (Yu). Paley(17) exact. Yu
leftover 186: no 19-IS under `c-decide` (5a/7a). 6a SAT-unsat-19 is still a
timeout. Width gate held through 7a–7f. 7c1 did not mint 252.
