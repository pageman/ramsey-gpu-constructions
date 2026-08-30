# GPU constructions Run001 never ran

**A40 result (30 Aug 2026):** jobs 2a–4c ran. **No published +1.**
\(R(4,20)\ge 252\) is Yu’s (arXiv:2608.18169). The 4a rows on \(p=337\) and
\(p=353\) are **false certificates** (residual \(n>256\); C MIS returned
“no 19-IS”). Job 4c’s \(R(4,22)>84\) is exact and far below the survey
\(\ge 314\). Revised paper (Kosmos Run001 baseline):
[`docs/paper-a40-revision.md`](docs/paper-a40-revision.md). Campaign:
[`docs/A40-CAMPAIGN.md`](docs/A40-CAMPAIGN.md). Dumps: [`data/a40/`](data/a40/).

Explicit Ramsey-graph families that are **GPU-native** — adjacency is a batched tensor kernel — and that **RamseyConstructor-GNN Run001 did not generate**.

This is not a claim that any of them prove \(R(k,k)\ge C^k\) with \(C\ge 1.01\). Paley, Frankl–Wilson, NLFSR, and these GPU families all live in the sub-exponential explicit regime. The point is the compute gap: Run001 spent its budget on CPU Paley/FW feature CSVs and never launched the kernels the original spec paid 100 GPU-hours for.

## The answer

Run001 **did** build Paley primes \(p\equiv 1\pmod 4\), Frankl–Wilson hybrids, synthetic 1% flips, a DIMACS slice, NLFSR sketches for Erdős 78, and a Random Forest on algebraic features. Hoffman/spectral proxies replaced Lovász \(\vartheta\). There is no `gnn_model.pt` in the artifact list.

These constructions **can** run on GPU and **were not** run:

| Family | GPU kernel | Why Run001 missed it |
|---|---|---|
| Paley of prime powers \(\mathbb F_{p^n}\), \(n>1\) | batched \(\mathbb F_{p^2}\) multiply-exponentiate on outer differences | Spec locked Paley to primes in \([17,997]\) |
| Generalized Paley \(\mathrm{GP}(p,k)\), \(k>2\) | outer-diff + \(a^{(p-1)/k}=1\) | Only quadratic residues; cubic/quartic Paley unused |
| Cyclotomic class-union Cayley | discrete-log table + class mask | Task 4 asked for this; artifacts are correlation CSVs, not a mask sweep |
| Quadratic-form Cayley on \(\mathbb F_2^n\) | XOR outer product + bitwise \(Q\) | Most GPU-native kernel in the catalogue; absent from the 40/30/20/10 mix |
| Gold / trace-of-power graphs on \(\mathbb F_2^n\) | XOR outer + \(\mathrm{GF}(2^n)\) power + Frobenius trace | NLFSR was the nonlinear CPU sibling; linear Gold/Kasami/m-sequences were not batched |
| Orthogonal polarity graphs of \(\mathrm{PG}(2,q)\) | GEMM of homogeneous coordinates \(x\cdot y\equiv 0\) | Finite-geometry polarity (Mattheus–Verstraete style) never built |
| Nagy intersecting-family graphs | pair bitset AND + popcount | Classical explicit cubic; not in the mix |
| Strong products / Kronecker lifts | `kronecker(A+I, A+I)` | Atoms only, no Abbott-style product family |
| Singer difference-set circulants | circulant broadcast of a \((q^2+q+1,q+1,1)\) set | Linear design-theory cousin of NLFSR, unused |
| Block-circulant / Galois cycle-type search | GPU local search on connection sets | The R(5,5)-style GPU annealer the budget was meant to buy |
| PPO + GAT | PyTorch Geometric | Required deliverable `gnn_model.pt` was not in the Run001 files |
| GPU Lovász \(\vartheta\) SDP | CVXPY / randomized SDP | Replaced by Hoffman proxies; no `verification_log.json` |
| GEMM clique counting | \(A^3\) / neighborhood \(A^3\) | Exact \(\omega\) assigned to CPU cliquer |

This repo **implements** the algebraic families **and** the search jobs Run001 skipped, with certificates that stay on the O(n) / O(n log n) side of the ledger. It does **not** train PPO edge-flip — Berghaus–Wagner (ICLR 2025) already showed RL can lose to random on \(R(4,4)\). Job 2A’s one learned object is a spectral Hoffman ranker on cyclotomic masks (`data/mask_ranker.json`).

## Algorithmic upgrades (wired into the kernels)

| Trick | Source | Where |
|---|---|---|
| Paley connection row = image of \(x\mapsto x^2\) in \(O(p)\) | CP / Project Euler | `kernels/sieve.py` |
| Paley spectrum in closed form \((q-1)/2\), \((-1\pm\sqrt q)/2\) | Paley 1933 | `kernels/rowcert.py` |
| Linear sieve for primes | Euler sieve | `kernels/sieve.py` |
| Circulant eigenvalues = FFT of the first row | Davis / Diaconis | `kernels/spectrum.py` |
| Boolean Cayley eigenvalues = Walsh–Hadamard | Bernasconi–Codenotti | `fwht` |
| \(\omega(G)=1+\omega(G[N(0)])\), \(\alpha(G)=1+\alpha(G[N^c(0)])\) | Yu arXiv:2608.18169 (R(4,20)≥252) | `rowcert.py` |
| \(K_4\)-free ⇔ neighbourhood triangle-free | same + Cayley folklore | `kernels/cayley.py` |
| \(R(3,k)\) circulant ⇔ Schur sum-free \(S\) | additive combinatorics | job 2C |
| Distance space: \(O(n)\) binary variables | arXiv:2608.18769 IP circulant | ILS |
| Cyclotomic \(S=-S\): \(2^{e/2}\) masks, Gray code | cyclotomy / Yu quintic | job 2A |
| Tomita MCS + degeneracy colour bound | CP bitset BK / BBMC | `kernels/mcs.py` |
| Delsarte \(\omega\le 1-d/\lambda_{\min}\), Cvetković inertia | association schemes | `spectrum.py` |
| Two-block circulant ILS | Exoo / DSC-3 | job 3A |

Exact certificates (Paley 5/17, …) are theorems. Spectral \(k\) on large \(N\) is **not** \(C\ge 1.01\).

## Run locally

```bash
python3 engine/test_kernels.py      # FFT Paley(17) = eigvalsh, VT ω=3, FWHT
python3 engine/test_invariants.py
python3 -m engine.cli --job phase0 --scale local
python3 -m engine.cli --job 1a --scale local     # Paley p≤101
python3 -m engine.cli --job 1c --scale local     # W(3,q)
# phases: --job phase1 | phase2 | phase3 | all
```

`RAMSEY_SCALE=local` keeps Paley ≤101, cyclotomic \(p\le 181\), \(\mathbb F_2^n\) with \(n\le 10\). CUDA sets the default to `runpod` (Paley ≤997, cyclotomic \(p\le 10^4\), \(n\le 12\), ANF \(n=13..16\)).

## RunPod

No API key is required in this repo. Build from the official pre-cached image and launch **one job per pod**:

```bash
docker build --platform=linux/amd64 -t YOUR_REGISTRY/ramsey-gpu:latest .
```

On [runpod.io](https://runpod.io) create a GPU pod from that image. **Do not override the container command** — the base image’s `/start.sh` owns SSH/Jupyter. Work starts from `/post_start.sh`.

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
| | `3d` | ANF search | \(n=13..16\), FWHT only if residual \(>64\) (prints every trial) |
| then | `4a` | Yu 2-class pool + bitset residual MIS | \(R(4,t)\) |
| | `4b` | Circulant \(R(3,t)\) for \(t\ge 50\) | \(R(3,k)\) |
| | `4c` | GQ \(K_4\)-clean exact \(\alpha\) | \(R(4,t)\)-geom |

Also set `RAMSEY_SCALE=runpod`. Base image pin: `runpod/pytorch:1.0.3-cu1281-torch280-ubuntu2404`.

### Run 4a/4b/4c without stopping 3d

Job 3d is **one CPU thread**. 4a–4c use other cores (and compile `engine/kernels/native_mis.c` on first MIS). They **append** `data/registry.jsonl` and **merge** `catalog.json` / `bound_ledger.json` by `graph_id`, so 3d finishing later will not wipe them (and they will not wipe 3d if 3d writes last — both upsert).

On the pod, in a **new** SSH (not the 3d pane, not the stuck `ramsey` 2a paste):

```bash
# do not attach to the 3d pts/1 session
cd /workspace/ramsey-gpu-constructions
# get this commit onto the pod (Origin or scp engine/ + data/yu_r4_20.json)
gcc -O3 -shared -fPIC -o engine/kernels/native_mis.so engine/kernels/native_mis.c
tmux new -s ramsey4
cd /workspace/ramsey-gpu-constructions
PYTHONUNBUFFERED=1 python3 -u -m engine.cli --job 4a --scale runpod
# later, another window:  --job 4b   then  --job 4c
# detach: Ctrl-B, D
```

You should see `[4a] Yu S regression…` within a second.

The A40 wave (2a → 4c) is recorded in `docs/A40-CAMPAIGN.md`. **No published
cell moved.** Job 4a `CELL?` lines for \(p=337,353\) were a residual-\(n>256\)
false certificate (fixed on `main` after the run).

## Publish to GitHub (`pageman/ramsey-gpu-constructions`)

This cloud session can push Origin only. On the **Mac**, in your GitHub clone
(the folder that already has `origin` → `github.com/pageman/ramsey-gpu-constructions`):

```bash
cd /path/to/ramsey-gpu-constructions   # the git clone, not Downloads/
git remote add cursor https://origin.cursor.com/git/pageman/ramsey-gpu-constructions.git
git fetch cursor
git merge cursor/main
# optional: keep the A40 dumps in-tree
mkdir -p data/a40
cp ~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/catalog-2a.json data/a40/
cp ~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/catalog.json data/a40/catalog-4abc.json
cp ~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/registry.jsonl data/a40/
cp ~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/bound_ledger.json data/a40/
git add data/a40 && git commit -m "Add A40 2a and 4a-4c run artifacts."
git push origin main
```

If `git fetch cursor` asks for auth, open the agent page and use Download /
the Cursor git remote shown there, then `git push origin main` as usual.

## Run the dashboard

```bash
npm install
npm run dev     # http://127.0.0.1:43123
```

## What the numbers mean

For each graph we report a **certified** \(k=\max(\omega^\uparrow,\alpha^\uparrow)+1\), so \(R(k,k)>N\) whenever the bounds are valid. Vertex-transitive exact MCS on the neighbourhood recovers Paley(17): \(\omega=\alpha=3\), hence \(R(4,4)>17\). Larger graphs use Hoffman / Delsarte / ratio bounds, which are **loose** — they inflate \(k\) and therefore shrink \(N^{1/k}\). Treat large-\(N\) \(N^{1/k}\) as a pessimistic proxy, not a new exponential lower bound.

OEIS A000791: \(R(3,3)=6\), \(R(4,4)=18\), \(R(5,5)\in[43,48]\). Yu 2026: \(R(4,20)\ge 252\) via a 251-vertex quintic-cyclotomic circulant (the 3B target order).

## Copy to `Downloads/Ramsey-GPU-Constructions`

On the Mac, from the repo:

```bash
chmod +x scripts/sync-to-downloads.sh
./scripts/sync-to-downloads.sh
```

That writes `~/Downloads/Ramsey-GPU-Constructions/` (code, docs, local `data/`). To add the A40 files from the pod (confirm IP/port in the RunPod UI first):

```bash
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
./scripts/sync-to-downloads.sh
```

Pod data lands in `~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/` (`catalog.json` ~15 MB, `registry.jsonl` with job 2a + 3d n=13/14).

## Layout

- `engine/constructions.py` — parametric families (Paley, GP, cyclotomic, \(\mathbb F_2\), GQ, FW, …)
- `engine/kernels/` — FFT / FWHT / MCS / ILS / sieve
- `engine/cli.py` — `python3 -m engine.cli --job …`
- `engine/jobs.py` — ownership table; writes `data/registry.jsonl` + `bound_ledger.json`
- `docs/plan-move-a-number.md` — **v2** kernel/search plan: cheap filter + exact decision \(\alpha\), never Hoffman in the loop; Yu \(S\) regression before any hunt (`data/yu_r4_20.json`)
- `docs/paper-a40-revision.md` — revised paper vs the Kosmos Run001 PDF
- `docs/SESSION-HANDOFF.md` — narrative/method arc and questions for a new LLM session
- `Dockerfile` + `post_start.sh` — RunPod
- `src/` — Next.js dashboard
