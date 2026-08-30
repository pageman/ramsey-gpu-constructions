# Ramsey GPU constructions

Explicit **GPU-native** Ramsey-graph families, plus the A40 search that
followed Yu’s \(R(4,20)\ge 252\) (arXiv:2608.18169). Public tree:
[github.com/pageman/ramsey-gpu-constructions](https://github.com/pageman/ramsey-gpu-constructions).

**Status (30 Aug 2026).** No published +1. The number that is still true
is **252**. Paley(17) remains the best exact diagonal in this repo
(\(\omega=\alpha=3\), \(R(4,4)>17\)). Job 4a’s `CELL? R(4,20)≥354` is
**void** (residual \(n>256\)). Mixed-set residual \(\alpha\) is not
\(\alpha(G)\). Timeout ≠ accept.

Campaign write-ups: [`docs/A40-CAMPAIGN.md`](docs/A40-CAMPAIGN.md) ·
[`docs/PHASE5-CAMPAIGN.md`](docs/PHASE5-CAMPAIGN.md) ·
[`docs/PHASE7-CAMPAIGN.md`](docs/PHASE7-CAMPAIGN.md). Inventory:
[`docs/MANIFEST-2A-7C1.md`](docs/MANIFEST-2A-7C1.md). Replay:
[`docs/REPRODUCING.md`](docs/REPRODUCING.md). Next aisle (7c1 is done):
[`docs/WHERE-TO-LOOK.md`](docs/WHERE-TO-LOOK.md) → **7e.1**, not another
`--job 7c`.

## A40 scoreboard (jobs 2a–7c1)

RunPod A40 nick `armed_yellow_buzzard`. Success = a Radziszowski DS1
finite +1, not \(C\ge 1.01\).

| Job | What | Wall | Outcome |
|---|---|---|---|
| 2a | Cyclotomic Hoffman enum \(p\le 9973\) | 99755 s | 9288 graphs. No cell. |
| 2c | Circulant \(R(3,k)\) | 29 s | 46 graphs. No table beat. |
| 3a–3c | Block-circulant / ILS / GQ | — | No residual accept. |
| 3d | ANF \(n=13,14\) | — | \(N=8192,16384\) in registry; hung on old `max_clique`. |
| 4a | Yu 2-class pool, \(p\in[200,400]\) | 1715 s | 6 rows. **354 is void.** |
| 4b | Circulant \(R(3,50)\) | 8.56 s | 0 graphs (residual \(>280\)). |
| 4c | \(W(3,7)\) leftover | — | Exact \(\alpha=21\), \(R(4,22)>84\) vs \(\ge 314\). |
| 5a | Yu residual 186, `c-decide` | 63.17 s | No 19-IS, \(2.16\times 10^8\) nodes. Recertify, not a +1. |
| 5b–5f | Referee / hunt / polarity / TG | ~19.5 min phase | No `CELL?` that passed the gates. |
| 6a | CP-SAT on residual 186 | 600 s cap | \(\alpha\ge 18\) found; \(\alpha\ge 19\) **timeout**. Timeout ≠ proof. |
| 7a | Referee + colour/flatten | 81.13 s | No 19-IS, \(3.52\times 10^7\) nodes. Nodes \(\times\sim 1/6\) vs 5a; wall worse. |
| 7b | Other \((i,j)\), \(p\le 400\) | 400.56 s | 228 graphs. Residual always a 17/18-IS. |
| 7c | SAT \(\max\lvert S\rvert\) | 83.16 s | 163 graphs. Greedy \(\alpha=7\)–\(14\); leftover still a 16-IS. |
| 7d | \(R(3,50)\), \(n\sim 500\) | 4.77 s | Leftover 346–374 \(>256\). Width skip. |
| 7e | 2-block \(m\in\{29,41,53,61\}\) | 0.61 s | Never \(K_4\)-free; \(n\le 122<200\). |
| 7f | Polarity floor gate | 0.37 s | Same \(R(4,22)>84\) catalogue. |
| **7c1** | Leftover-IS CEGIS | **1098.06 s** | **181** pools, **13935** cuts, **0** timeouts, **30** pool-UNSAT. **0** graphs. No `CELL?`. |

Code that ran 7c1: git `98473e5`. Dumps: [`data/a40/`](data/a40/),
[`data/phase5/`](data/phase5/), [`data/phase7/`](data/phase7/). The 5 MB
A40 `phase7.log` is promoted on the Mac by
`bash scripts/mac-finish-archive.sh` (landing pad `data/phase7-7c1.log`).

Do **not** rerun `pod-phase7.sh` or `--job 7c`. Next *search* (if any)
is **7e.1** (\(200\le n\le 256\), two-orbit + residual contract), not
more SAT seconds.

## What this repo is

Run001 built Paley primes \(p\equiv 1\pmod 4\), Frankl–Wilson hybrids,
synthetic 1% flips, a DIMACS slice, NLFSR sketches, and a Random Forest
on algebraic features. Hoffman/spectral proxies replaced Lovász
\(\vartheta\). There is no `gnn_model.pt`.

These constructions **can** run on GPU and **were not** run by Run001:

| Family | GPU kernel | Why Run001 missed it |
|---|---|---|
| Paley of prime powers \(\mathbb F_{p^n}\), \(n>1\) | batched \(\mathbb F_{p^2}\) multiply-exponentiate on outer differences | Spec locked Paley to primes in \([17,997]\) |
| Generalized Paley \(\mathrm{GP}(p,k)\), \(k>2\) | outer-diff + \(a^{(p-1)/k}=1\) | Only quadratic residues |
| Cyclotomic class-union Cayley | discrete-log table + class mask | Artifacts are correlation CSVs, not a mask sweep |
| Quadratic-form Cayley on \(\mathbb F_2^n\) | XOR outer product + bitwise \(Q\) | Absent from the 40/30/20/10 mix |
| Gold / trace-of-power graphs on \(\mathbb F_2^n\) | XOR outer + \(\mathrm{GF}(2^n)\) power + Frobenius trace | NLFSR was the CPU sibling |
| Orthogonal polarity graphs of \(\mathrm{PG}(2,q)\) | GEMM of homogeneous coordinates \(x\cdot y\equiv 0\) | Mattheus–Verstraete style never built |
| Nagy intersecting-family graphs | pair bitset AND + popcount | Not in the mix |
| Strong products / Kronecker lifts | `kronecker(A+I, A+I)` | Atoms only |
| Singer difference-set circulants | circulant broadcast of a \((q^2+q+1,q+1,1)\) set | Unused |
| Block-circulant / Galois cycle-type search | GPU local search on connection sets | The R(5,5)-style annealer the budget was meant to buy |
| PPO + GAT | PyTorch Geometric | Required `gnn_model.pt` missing |
| GPU Lovász \(\vartheta\) SDP | CVXPY / randomized SDP | Replaced by Hoffman proxies |
| GEMM clique counting | \(A^3\) / neighborhood \(A^3\) | Exact \(\omega\) assigned to CPU cliquer |

This repo **implements** the algebraic families **and** the search jobs
Run001 skipped, with certificates that stay on the O(n) / O(n log n)
side of the ledger. It does **not** train PPO edge-flip — Berghaus–Wagner
(ICLR 2025) already showed RL can lose to random on \(R(4,4)\). Job 2A’s
one learned object is a spectral Hoffman ranker on cyclotomic masks
(`data/mask_ranker.json`).

## Scientific rules (do not regress)

- Success = a **published finite +1** in Radziszowski DS1, not \(C\ge 1.01\).
- Residual \(\alpha(G[N^c(0)])\le t-2\) is **not** \(\alpha(G)\le t-1\).
  Do not emit `CELL?` / `exact=True` off residual-only.
- Timeout ≠ accept. Width: C MIS / `c-decide` \(n\le 256\).
- Mixed-set hole: neighbourhood triangle-free + leftover \(\alpha\) is
  not a full-graph certificate.

Exact certificates (Paley 5/17, …) are theorems. Spectral \(k\) on large
\(N\) is **not** \(C\ge 1.01\).

## Algorithmic upgrades (wired into the kernels)

| Trick | Source | Where |
|---|---|---|
| Paley connection row = image of \(x\mapsto x^2\) in \(O(p)\) | CP / Project Euler | `kernels/sieve.py` |
| Paley spectrum in closed form \((q-1)/2\), \((-1\pm\sqrt q)/2\) | Paley 1933 | `kernels/rowcert.py` |
| Linear sieve for primes | Euler sieve | `kernels/sieve.py` |
| Circulant eigenvalues = FFT of the first row | Davis / Diaconis | `kernels/spectrum.py` |
| Boolean Cayley eigenvalues = Walsh–Hadamard | Bernasconi–Codenotti | `fwht` |
| \(\omega(G)=1+\omega(G[N(0)])\), \(\alpha(G)=1+\alpha(G[N^c(0)])\) | Yu arXiv:2608.18169 | `rowcert.py` |
| \(K_4\)-free ⇔ neighbourhood triangle-free | same + Cayley folklore | `kernels/cayley.py` |
| \(R(3,k)\) circulant ⇔ Schur sum-free \(S\) | additive combinatorics | job 2C |
| Distance space: \(O(n)\) binary variables | arXiv:2608.18769 IP circulant | ILS |
| Cyclotomic \(S=-S\): \(2^{e/2}\) masks, Gray code | cyclotomy / Yu quintic | job 2A |
| Tomita MCS + degeneracy colour bound | CP bitset BK / BBMC | `kernels/mcs.py` |
| Delsarte \(\omega\le 1-d/\lambda_{\min}\), Cvetković inertia | association schemes | `spectrum.py` |
| Two-block circulant ILS | Exoo / DSC-3 | job 3A |
| Leftover-IS CEGIS on Yu pools | this campaign, job 7c1 | `engine/cegis_pool.py` |

## Run locally

```bash
python3 engine/test_kernels.py      # FFT Paley(17) = eigvalsh, VT ω=3, FWHT
python3 engine/test_invariants.py
python3 -m engine.cli --job phase0 --scale local
python3 -m engine.cli --job 1a --scale local     # Paley p≤101
python3 -m engine.cli --job 1c --scale local     # W(3,q)
# phases: --job phase1 | phase2 | phase3 | all
```

`RAMSEY_SCALE=local` keeps Paley ≤101, cyclotomic \(p\le 181\),
\(\mathbb F_2^n\) with \(n\le 10\). CUDA sets the default to `runpod`
(Paley ≤997, cyclotomic \(p\le 10^4\), \(n\le 12\), ANF \(n=13..16\)).

Replay the residual that is still true (Yu leftover 186, no 19-IS):

```bash
RAMSEY_SCALE=runpod RAMSEY_5A_LIMIT=1800 OMP_NUM_THREADS=12 \
  python3 -u -m engine.cli --job 5a --scale runpod
```

Expect ~63 s, `found=false`, `timed_out=false`. Do not announce a cell.

Replay 7c1 **wiring** only (not the A40 hunt):

```bash
RAMSEY_FORCE_7=1 python3 -u -m engine.cli --job 7c1 --scale local
python3 engine/test_kernels.py
```

## RunPod

No API key is required in this repo. Build from the official pre-cached
image and launch **one job per pod**:

```bash
docker build --platform=linux/amd64 -t YOUR_REGISTRY/ramsey-gpu:latest .
```

On [runpod.io](https://runpod.io) create a GPU pod from that image.
**Do not override the container command** — the base image’s `/start.sh`
owns SSH/Jupyter. Work starts from `/post_start.sh`.

Environment (see `runpod.env.example`):

| Pod | `RAMSEY_JOB` | Owns | Cell |
|---|---|---|---|
| A | `1a` | Paley recertify \(p\le 997\) | cert |
| B | `1b` | \(\mathbb F_2^n\) Gold/Kasami \(n=8..12\) | cert |
| C | `1c` | GQ polarity W(3,q) | \(R(4,t)\)-geom |
| D | `1d` | Frankl–Wilson + dispersers | explicit-diag |
| then | `2a` | cyclotomic enum \(p\le 10^4\) | cert (3A may only **perturb** these) |
| ∥ | `2c` | circulant | **\(R(3,k)\) only** |
| then | `3a` | block-circulant ILS | diagonal \(R(k,k)\) |
| | `3b` | circulant | \(R(4,k)\), \(k=5..20\) |
| | `3c` | GQ scale-up | large-\(t\) \(R(4,t)\) |
| | `3d` | ANF search | \(n=13..16\), FWHT only if residual \(>64\) |
| then | `4a` | Yu 2-class pool + bitset residual MIS | \(R(4,t)\) |
| | `4b` | Circulant \(R(3,t)\) for \(t\ge 50\) | \(R(3,k)\) |
| | `4c` | GQ \(K_4\)-clean exact \(\alpha\) | \(R(4,t)\)-geom |
| then | `5a` | Recertify Yu residual 186 (second solver) | \(R(4,20)\) |
| | `5b` | Referee: width, timeout≠accept, mixed sets | cert |
| | `5c` | Yu pool hunt on residuals the referee can finish | \(R(4,t)\) |
| | `5d` | Circulant \(R(3,t)\) \(t\ge 50\), nonempty seed | \(R(3,k)\) |
| | `5e` | Polarity leftover only if \(N+1\) beats the floor | \(R(4,t)\)-geom |
| | `5f` | Catalogue \(TG_{d,h}\) / Yip | cert |
| | `6a` | Second solver on Yu residual 186 (CP-SAT / Cliquer) | cert |
| then | `phase7` | Look 1–6 after 6a is green | \(R(4,t)\) / \(R(3,k)\) |
| | `7a`…`7f` | Referee bench, 2-class hunt, SAT-on-pool, \(R(3,t)\ge 50\), 2-orbit, polarity | [`docs/JOB-PHASE7.md`](docs/JOB-PHASE7.md) |
| | `7c1` | Leftover-IS CEGIS; **not** inside `phase7` | [`docs/JOB-7C1.md`](docs/JOB-7C1.md) |

Job **6a** is minutes, not a night (`docs/JOB-6A.md`). It does not hunt
and does not move 252. **Phase 7 already ran.** Gate:
`second_solver_agrees`. Do not start `bash scripts/pod-phase7.sh` again.

Jobs **5a–5f** are CLI flags. Spec: [`docs/plan-jobs-5x.md`](docs/plan-jobs-5x.md).
Pod night (historical): [`docs/POD-PHASE5.md`](docs/POD-PHASE5.md).

If the prompt is `…@…MacBook-Pro` you are on the **laptop**. `/workspace/…`
does not exist there.

```bash
# on the Mac clone (already in ~/ramsey-gpu-constructions — do not cd /workspace)
git fetch origin && git merge origin/main
bash scripts/mac-phase5.sh
```

Only after SSH, when the prompt is `root@…`:

```bash
cd /workspace/ramsey-gpu-constructions
bash scripts/pod-phase5.sh
```

`phase5` = 5a then halt unless `data/yu_r4_20.cert.json` has
`alpha_certified`. `phase7` = 6a gate then Looks 1–6. Base image pin:
`runpod/pytorch:1.0.3-cu1281-torch280-ubuntu2404`. Also set
`RAMSEY_SCALE=runpod`.

The A40 wave (2a → 7c1) is recorded in the campaign docs. **No published
cell moved.** Job 4a `CELL?` lines for \(p=337,353\) were a residual-\(n>256\)
false certificate (fixed on `main` after the run).

## Archive 2a–7c1 into git + Downloads

Two copies of every run artifact:

1. **Git clone** `~/ramsey-gpu-constructions`
2. **Downloads snapshot** `~/Downloads/Ramsey-GPU-Constructions/` —
   rsync of the clone plus labelled campaign folders. **No `.git`.**
   Do not `git push` from there.

On the **Mac** (prompt `paulpajo@…`, not `root@`). You already have
`data/phase7-7c1.log` from scp:

```
cd ~/ramsey-gpu-constructions
git fetch origin && git merge origin/main
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
bash scripts/mac-finish-archive.sh
git add data/phase7
git commit -m "Archive phase7 and 7c1 A40 log."
git push github main
git push origin main
```

If the pod is Stopped: `RAMSEY_SKIP_POD=1 bash scripts/mac-finish-archive.sh`.
The script still rsyncs the clone and promotes the 5 MB log.

A lighter snapshot without contacting the pod:

```
bash scripts/sync-to-downloads.sh
```

Map: [`docs/REPRODUCING.md`](docs/REPRODUCING.md). **Stop** the pod after
archive. Do not Terminate.

## Publish this tree to GitHub

This cloud session pushes Cursor Origin. GitHub
(`pageman/ramsey-gpu-constructions`) is updated from the **Mac** clone
that already has a `github` remote:

```bash
cd ~/ramsey-gpu-constructions
git fetch origin && git merge origin/main
git push github main
```

If that Mac clone’s `origin` already *is* GitHub, fetch the Cursor remote
instead, merge, then `git push origin main`.

## Run the dashboard

```bash
npm install
npm run dev     # http://127.0.0.1:43123
```

## What the numbers mean

For each graph we report a **certified**
\(k=\max(\omega^\uparrow,\alpha^\uparrow)+1\), so \(R(k,k)>N\) whenever
the bounds are valid. Vertex-transitive exact MCS on the neighbourhood
recovers Paley(17): \(\omega=\alpha=3\), hence \(R(4,4)>17\). Larger
graphs use Hoffman / Delsarte / ratio bounds, which are **loose** — they
inflate \(k\) and therefore shrink \(N^{1/k}\). Treat large-\(N\)
\(N^{1/k}\) as a pessimistic proxy, not a new exponential lower bound.

OEIS A000791: \(R(3,3)=6\), \(R(4,4)=18\), \(R(5,5)\in[43,48]\). Yu 2026:
\(R(4,20)\ge 252\) via a 251-vertex quintic-cyclotomic circulant (the 3B
target order).

## Layout

- `engine/constructions.py` — parametric families (Paley, GP, cyclotomic, \(\mathbb F_2\), GQ, FW, …)
- `engine/kernels/` — FFT / FWHT / MCS / ILS / sieve / `c-decide`
- `engine/cegis_pool.py` — leftover-IS cuts for job 7c1
- `engine/cli.py` — `python3 -m engine.cli --job …`
- `engine/jobs.py` — ownership table; writes `data/registry.jsonl` + `bound_ledger.json`
- `data/a40/` — jobs 2a + 4a–4c dumps (`catalog-2a.json` ~14 MB)
- `data/phase5/` — 5a–5f log, Yu residual cert, A40 `.so`, env SHA256
- `data/phase7/` — 7a–7f + 7c1 summary, DIMACS complement, engine-src freeze; log after Mac script
- `data/yu_r4_20.json` — Yu published connection set \(S\)
- `docs/PHASE7-CAMPAIGN.md` — 6a–7f + 7c1 scoreboard (30 Aug 2026)
- `docs/JOB-7C1.md` — leftover-IS CEGIS operator guide
- `docs/WHERE-TO-LOOK.md` — literature + arXiv RAG; queue after 7c1 is 7e.1
- `docs/plan-jobs-5x.md` — **v3** post-A40 queue: jobs 5a–5f
- `docs/plan-move-a-number.md` — **v2** kernel/search plan
- `docs/paper-a40-revision.md` — revised paper vs the Kosmos Run001 PDF
- `docs/paper/gpu-constructions-after-run001.{tex,pdf,docx,txt}` — print copies
- `docs/SESSION-HANDOFF.md` — narrative/method arc
- `scripts/mac-finish-archive.sh` — Mac: promote 7c1 log, rsync Downloads
- `scripts/sync-to-downloads.sh` — rsync clone → `~/Downloads/Ramsey-GPU-Constructions/`
- `Dockerfile` + `post_start.sh` — RunPod
- `src/` — Next.js dashboard
