# GPU constructions after Run001: what an A40 actually certified

**A revision of the Kosmos discovery report**
*RamseyConstructor-GNN Run001* ([Edison Scientific playground, report PDF](https://playground.edisonscientific.com/kosmos/77856386-f79a-436a-84ab-0a28be7f94a9/outputs/report-pdf))

Paul Pajo (`pageman`) and a Cursor cloud agent  
Code and artefacts: [github.com/pageman/ramsey-gpu-constructions](https://github.com/pageman/ramsey-gpu-constructions) (`main` as of 30 August 2026)  
Campaign log: `docs/A40-CAMPAIGN.md`. Session memory: `docs/SESSION-HANDOFF.md`.

---

## Abstract

The Kosmos Run001 report framed an explicit-construction search for
\(R(k,k)\ge C^k\) with \(C\ge 1.01\), then delivered four *surrogate*
discoveries: a compute-capped invariant pipeline; a family-dependent
inversion of spectral predictors of a Hoffman growth proxy \(C_{\mathrm{Hoff}}\);
a Paley *attractor* under degree-preserving edits; and a ranking in
which Paley wins that proxy. None of those results is a constructive
exponential, and none is a new cell in Radziszowski’s survey.

This revision reports the follow-on instrument and a one-A40 campaign
(jobs 1a–4c, 28–30 August 2026). We implemented the GPU-native algebraic
families Run001 specified but did not run, then replaced Hoffman-guided
search with Yu’s actual pipeline: a 2-class cyclotomic *pool*, a
triangle-free process, a greedy-\(\alpha\) reject, and a bitset decision
MIS on the residual \(G[N^c(0)]\).

**Results.** No published finite lower bound moved. Paley(17) remains
the best *exact diagonal* certificate in the tree (\(\omega=\alpha=3\),
\(R(4,4)>17\)). Job 2a enumerated 9288 cyclotomic class-unions through
\(p\le 9973\) in 99755 s and produced no survey cell. Job 3b’s Hoffman
ILS never recertified Yu’s published connection set. Job 4a reproduced
Yu’s \(S\subset\mathbb Z/251\mathbb Z\) structurally (degree 64,
residual 186, \(N(0)\) triangle-free) but did **not** certify
\(\alpha=19\) (the hard “no 19-IS” branch timed out). Two 4a rows
(\(p=337\), residual 262; \(p=353\), residual 264) were logged as
exact \(\alpha=19\) and printed `CELL? \(R(4,20)\ge 354\)`. Those
rows are **void**: the C MIS kernel stores 256 vertices and, on
\(n>256\), returned “not found” without setting a timeout. Job 4c
exactly certified \(\alpha=21\) on an 84-vertex \(K_4\)-cleaned
\(W(3,7)\) leftover, hence \(R(4,22)>84\), which is far below the
published \(\ge 314\).

The revised claim is therefore negative and methodological: Hoffman
\(C=N^{1/k}\) and \(C(\alpha)=\alpha^{1/\alpha}\) are the wrong
objectives for a survey number; the certificate for a Yu-scale residual
is a CPU decision problem of width \(\sim 186\)–\(280\), not a GNN
or a GPU GEMM; and a bitset solver’s width is part of the theorem.
Yu’s \(R(4,20)\ge 252\) (arXiv:2608.18169) is unchanged.

---

## 1. Introduction

### 1.1 The Run001 commission

The Kosmos specification asked for a *constructive* infinite family
with \(R(k,k)\ge C^k\) and target \(C\ge 1.01\), against OEIS A000791,
with adjacency given by a parametric formula or a deterministic
polynomial-time algorithm. The compute envelope was \(\approx 100\)
GPU-hours. The prescribed mix was 40% Paley, 30% Frankl–Wilson hybrids,
20% synthetic, 10% DIMACS; the prescribed learners were a Random Forest
and a GAT; the prescribed constructor was PPO edge-flip; Task 4 asked
for a cyclotomic-class search guided by feature importance; Task 5 asked
for a three-tier exact / SAT / Lovász-\(\vartheta\) hierarchy.

That is Erdős’s constructive challenge (problem #78), not a finite
table hunt.

### 1.2 What Run001 actually shipped

The artefacts and the 20-page discovery report do **not** contain
`gnn_model.pt`, a SAT audit of the top 100 candidates, or a family
with \(N\sim C^k\). They contain:

- a 1 500-graph corpus with \(N\le 300\), exact \(\omega,\alpha\) only
  for \(N\le 50\), Hoffman in place of \(\vartheta\);
- RF/GAT models of a *growth-base* \(C=N^{1/k_{\mathrm{eff}}}\) and of
  \(C_{\mathrm{Hoff}}\) derived from Hoffman’s \(\alpha\);
- the empirical statement that Paley is a rigid attractor under
  degree-preserving edits, and that annealing escapes only into
  dense random-like graphs;
- a later missing-file failure (`ramseyconstructions.csv` not in the
  archive) that the report itself flags as a reproducibility hazard.

Berghaus–Wagner (ICLR 2025) had already shown that RL edge-flip can
lose to random on \(R(4,4)\). We did not train PPO.

### 1.3 What this session asked instead

Two questions replaced the exponential:

1. **Compute gap.** Which GPU-native families did the spec name and
   the run never emit? (Paley of prime powers, generalized Paley,
   cyclotomic class-unions, \(\mathbb F_2^n\) quadrics / Gold / Kasami,
   polarity graphs of \(\mathrm{PG}(2,q)\) and \(W(3,q)\), Nagy, Singer,
   Kronecker lifts, block-circulant ILS.)
2. **Survey gap.** Can an A40 move a *published finite* lower bound
   in Radziszowski DS1? The only nearby 2026 headline in this
   size class is Yu’s \(R(4,20)\ge 252\) on a 251-vertex quintic
   circulant.

Erdős #78 remains open (Li 2023 extractors give \((\log N)^C\), not
an A40 MCS target). #986 is solved (Bradač, June 2026) by containers,
not by enumerating Cayley graphs. The session’s success criterion was
a Radziszowski +1, not \(C\ge 1.01\).

---

## 2. The Kosmos baseline, kept and demoted

We keep the four Run001 discoveries as *statements about surrogates*,
and we demote them from “exponential lower bounds” to diagnostics.

### Discovery 1 (kept): a compute-capped pipeline

Staging exact \(\omega,\alpha\) on small \(N\) and filling Hoffman /
networkx approximations on the rest is a valid way to *label a
training set*. It is not a way to *publish* \(R(s,t)\ge N+1\). The
report’s own later missing-CSV incident is the operational twin of
our A40 lesson: `catalog.json` last-writer-wins, `registry.jsonl`
is the source of truth, and a Stop/scp ritual is part of the method.

### Discovery 2 (kept, narrowed): spectral predictors invert by family

That the same global eigenvalue features change sign between Paley /
cubic-residue graphs and general Cayley graphs is consistent with
association-scheme spectra versus representation-theoretic ones. It
justifies *family-aware ranking*. It does not justify using
\(C_{\mathrm{Hoff}}\) as a search score for a cell. Job 2a ranked
every eligible cyclotomic class-union through \(p=9973\) by Hoffman
and moved no cell.

### Discovery 3 (strengthened): Paley is an attractor for the *wrong* objective

Run001 showed that degree-preserving edits of Paley worsen
\(C(\alpha)=\alpha^{1/\alpha}\), which peaks at \(\alpha=e\). This
session showed the same pathology at job scale: circulant ILS scored
by Hoffman(\(G\))+Hoffman(\(\overline G\)) never recovered Yu’s
published \(S\), because every Paley-like mask has Hoffman
\(\alpha\sim\sqrt n\) and the score has no gradient toward
\(\omega\le 3\), \(\alpha\le 19\).

Annealing that destroys regularity and converges to an Erdős–Rényi
cloud is not an explicit family. We treat that as a negative theorem
about the surrogate, not as a construction.

### Discovery 4 (revised): Paley wins the proxy; Paley(17) wins the *theorem*

In the 1 500-graph Kosmos mix, Paley had the highest median
\(C=N^{1/k_{\mathrm{eff}}}\). That ranking is an artefact of the
proxy. On *exact* certificates in this repo the jewel is Paley(17):
\(\omega=\alpha=3\), hence \(R(4,4)>17\), \(N^{1/k}\approx 2.03\).
As \(N\) grows and \(k\) is replaced by a loose spectral upper
bound, \(N^{1/k}\) *falls* toward \(\sim 1.2\). The dashboard will
always crown the smallest exact graph if \(C\) is the KPI. That is
why we no longer treat \(C\ge 1.01\) as a success test.

---

## 3. Methods

### 3.1 Instrument

A Next.js catalogue (port 43123) plus a Python engine
(`python3 -m engine.cli --job … --scale local|runpod`). Jobs are
non-overlapping in *cell ownership* (`engine/registry.py`). Scale
knobs live in `engine/scale.py`. Adjacency for circulants is the
first row; spectra are FFT (circulant) or FWHT (Boolean Cayley).
Paley’s connection set is the image of \(x\mapsto x^2\) in \(O(p)\),
not an Euler loop.

We did not train a GNN. The one learned object is a Hoffman mask
ranker written at the *end* of job 2a (`data/mask_ranker.json`).

### 3.2 What “a number moved” means

A graph \(G\) on \(n\) vertices with \(\omega(G)<s\) and
\(\alpha(G)<t\) implies \(R(s,t)\ge n+1\). Spectral \(k\) is a
ranking key, not a theorem. The hard rule of plan v2
(`docs/plan-move-a-number.md`):

> Cheap **filter** in the search loop; exact **decision**
> \(\alpha\le t-1\) in the certificate; **never Hoffman** in either;
> **never** materialise the \((p/2)\times(p/2)\) residual as a dense
> matrix.

If a candidate cannot be rejected in \(O(p)\) or decided on a bitset
of width equal to the residual, it is not a job for this A40.

### 3.3 Residual identity

For a circulant, \(K_4\)-freeness is equivalent to \(G[N(0)]\) being
triangle-free. Vertex 0 is non-adjacent to the residual
\(V\setminus(\{0\}\cup N(0))\), so a residual independent set of
size \(t-1\) yields \(\alpha(G)\ge t\) and **rejects** \(R(4,t)\).
Accepting \(R(4,t)\ge n+1\) requires proving there is *no* such set
(and that mixed independent sets in \(N(0)\) do not exceed \(t-1\);
this code uses Yu’s residual reduction and does not separately bound
mixed sets — a hole, not a theorem).

Yu’s published witness (arXiv:2608.18169), stored in
`data/yu_r4_20.json`, is the undirected distance set

```
S = {1,2,4,9,10,13,18,25,26,33,36,37,43,45,50,52,
     65,66,71,72,74,79,86,90,93,100,103,104,107,109,119,121}
```

on \(p=251\), \(e=5\), primitive root 6, pool \(D_0\cup D_2\),
\(|S|=32\), degree 64, residual 186, \(\omega=3\), \(\alpha=19\),
hence \(R(4,20)\ge 252\). Yu’s OpenMP certificate of the missing
19-IS on that residual is 1.4 s / \(\sim 2.7\times 10^7\) nodes.

### 3.4 Decision MIS

`engine/kernels/native_mis.c` is Östergård MIS, \(n\le 256\), four
`uint64` words. Python `bitset_mcs.mis_decision` prefers the C
kernel. A residual independent set of size \(t-1\) is a reject;
exhaustion without one is an accept; a timeout is *not* an accept.

**Defect (fixed after the run).** On \(n>256\) the C entry point
returned 0 without writing `timed_out`. ctypes left that flag at 0,
so the job treated “no 19-IS” as exact. Job 4a also hardcoded
`exact=True` on emit. Those two bugs stacked. After the run:
`n>256` sets timeout, Python short-circuits `skip_n>256`,
`CELL?` prints only if the decision proof finished. Regression:
`test_mis_n_over_256_is_not_a_certificate`.

### 3.5 Job 4a search

For each prime \(p\in[200,400]\) and each eligible \(e\in\{4,5,8,10\}\)
with \(-1\) in the index-\(e\) subgroup, form every 2-class undirected
pool. Run 64 restricted processes (add a random unused pool distance
while \(N(0)\) stays triangle-free), 64 anneal swaps (reject triangles
and greedy \(\alpha\ge t\)), multiplier lex-min, then bitset MIS on
the `mis_keep=8` lowest-greedy survivors. Target \(t\) is the first
of \(\{20,21,22\}\) with \(p+1\) above the coded published floors
252 / 252 / 314.

### 3.6 Hardware and provenance

One RunPod A40 48 GB (`armed_yellow_buzzard`, container
`3631e8666026`), billed as a GPU while most of jobs 2a and 4a were
CPU. Code on the pod began as a clone of public GitHub at
`a49da0c` and was updated by tarball. Canonical run records are
`data/a40/` (2a catalogue \(\sim\)14 MB; 4a/4c catalogue; registry;
ledger). The dashboard still reads the small local `data/catalog.json`.
Public GitHub and Cursor Origin are dual remotes of the same `main`.

---

## 4. Results

### 4.1 Local instrument check

Kernel tests: Paley(17) FFT spectrum equals `eigvalsh`; vertex-transitive
\(\omega=3\); Yu \(S\) is \(K_4\)-free with residual 186; C MIS on
Paley(17)’s residual decides \(\alpha=2\) vs 3; an empty 257-vertex
residual is not an exact “\(\alpha<19\)”. Local jobs produced 263
graphs, all at `scale=local`.

### 4.2 A40 jobs 1a–3d

| Job | What | Wall / size | Survey effect |
|---|---|---|---|
| 1a | Paley recertify \(p\le 997\) | seconds–minutes | no new exact diagonal |
| 1b | \(\mathbb F_2^n\) Gold/Kasami \(n=8..12\) | 131 s | certificates only |
| 1c | \(W(3,q)\), \(\mathrm{PG}(2,q)\) | 1.1 s | Hoffman / small exact |
| 1d | Frankl–Wilson + Sidon | 1.2 s | explicit-diag only |
| **2a** | cyclotomic class-unions \(p\le 9973\) | **99755 s**, 9288 graphs | **no cell** |
| 2c | circulant \(R(3,k)\) | 29 s, 46 graphs | no table beat vs Coniglio \(t\le 49\) |
| 3a | block-circulant ILS | short | no diagonal cell |
| 3b | circulant ILS, Hoffman score | \(\sim\)59 graphs, \(\sim\)12 s | never recertified Yu \(S\) |
| 3c | GQ q=11,13 | Hoffman only | no exact \(\alpha\) at q=16 |
| **3d** | ANF \(n=13,14\) | n=13 \(N=8192\), n=14 \(N=16384\) | hung / died; `max_clique` \(n>64\) is a 64-core subsample plus a colouring **with no timeout**. n=15,16 never emitted |

Job 2a had no checkpoint. A laptop-sleep death at \(p=5347\) forced a
restart from \(p=13\) and a 28-hour rerun. That is an operational
result, not a combinatorial one.

### 4.3 Phase 4 (29 August 23:24Z – 23:53Z)

| Job | Wall | Graphs | What was true |
|---|---|---|---|
| **4a** | 1715 s | 6 catalog rows (Yu + collisions) | structural Yu gate; two false exact rows (below) |
| **4b** | 8.56 s | 0 | every odd \(n\in[501,521]\) stayed residual \(>280\) (ILS from the empty mask, 80 steps) |
| **4c** | 1.58 s | 1 | leftover 84, greedy \(\alpha=20\), C MIS found 21 in 1.29 s / \(1.4\times 10^7\) nodes, exact \(\alpha=21\), \(R(4,22)>84\) |

The 2–5 h Fermi estimate for 4a was high because greedy \(\alpha\ge 20\)
rejected almost every walk before MIS. The A40 was a CPU rental.

Yu gate on the published \(S\): pool membership, \(|S|=32\), degree 64,
residual 186, \(N(0)\) triangle-free: **pass**. Exact \(\alpha=19\):
**fail** (timeout). The catalogue still marks that row `exact=True`
from the *structural* flag. That is literature, not this kernel.

### 4.4 The 337/353 rows are not theorems

| `graph_id` | \(\lvert S\rvert\) | deg | residual | Logged | Verdict |
|---|---|---|---|---|---|
| `yu_pool_p251_e5_kindyu_published` | 32 | 64 | 186 | exact \(\alpha=19\) | Yu’s paper; this kernel did not decide α |
| `yu_pool_p337_e4` | 37 | 74 | **262** | exact \(\alpha=19\) | **false** (\(n>256\)) |
| `yu_pool_p353_e8` | 44 | 88 | **264** | exact \(\alpha=19\); four `CELL? \(R(4,20)\ge 354\)` | **false** (\(n>256\)); four emits share one `graph_id` |

Do not write \(R(4,20)\ge 338\) or \(354\). Published remains **252**.

### 4.5 Job 4c in context

\(R(4,22)>84\) is a real exact certificate on a cleaned polarity
graph. The survey already has \(R(4,22)\ge 314\) (quartic / literature
floor used in `R4_LOWER`). The line is a kernel smoke test, not a
headline.

---

## 5. Negative theorems (this codebase)

These are statements about *this* instrument, strong enough to stop
a class of follow-ups.

**T1.** Ranking whole cyclotomic class-unions by Hoffman, for every
prime \(p\le 9973\), does not produce a survey cell. Exact Paley
\(\omega\) in this range is already in Shearer / Exoo. 9973 is just
`cyclo_max`.

**T2.** Circulant ILS with score Hoffman(\(G\))+Hoffman(\(\overline G\))
does not recertify Yu’s \(S\) and has no gradient toward
\(\omega\le 3\), \(\alpha\le 19\).

**T3.** `max_clique` for \(n>64\), implemented as a 64-vertex core
plus a Python greedy colouring with no timeout, cannot certify a
186-vertex residual and can hang job 3d on a \(4096\times 4096\)
colouring. A 64-subset clique number is a lower bound on \(\omega\)
of a *different* graph.

**T4.** A bitset MIS with width 256 that returns “not found” on
\(n>256\) without a timeout flag will, if treated as exact, emit
false survey cells. Width is part of the certificate.

**T5.** The Kosmos surrogate \(C=N^{1/k_{\mathrm{eff}}}\) systematically
rewards small exact jewels and punishes large honest spectral bounds.
It is a useful *diagnostic* of the Run001 mix and a harmful *objective*
for DS1.

**T6.** PPO / GAT / more Paley / full class-unions / ANF \(n=16\)
spectral \(C^*\) / AlphaEvolve-on-the-pod are out of scope for a
+1. The bottleneck is a decision MIS (or SAT) at residual
\(n\sim 186\)–\(280\).

---

## 6. Discussion

### 6.1 The compute gap was real and is now closed as a *catalogue*

Run001’s Task 4 asked for cyclotomic masks and shipped correlation
CSVs. This repo runs the masks (job 2a) and the 2-class *subsets*
(job 4a). The GPU-native families in the README gap table have
constructors. That is the honest delivery of the “families the spec
paid for.” It is not \(C\ge 1.01\).

### 6.2 The survey gap is a solver gap

Yu’s paper is not “cyclotomic + Hoffman”. It is a three-stage
pipeline on one prime: a 50-set pool, a restricted process, and a
full BnB on a 186-vertex residual. We implemented stages one and
two. Stage three is still Yu’s 1.4 s OpenMP (or Cliquer / SAT),
not this 25 s single-thread C kernel. Until that decision is
independent and tight, a `CELL?` line is a bug report.

### 6.3 GPU was the wrong scarce resource for phase 4

Job 2a’s FFTs are CPU. Job 4a’s MIS is CPU. The A40 billed GPU
hours for a process-supervision problem (tmux vs SIGHUP) and a
bitset problem. Plan v2’s GPU role — batched legality and greedy
reject — was never the inner loop.

### 6.4 Provenance is part of the result

Kosmos lost `ramseyconstructions.csv`. This campaign split truth
across a 14 MB 2a catalogue, a 436 KB 4abc catalogue, an append-only
registry, a Mac Downloads tree without `.git`, Cursor Origin
(Internal), and public GitHub. The retraction is in the README
because a catalogue row with `exact=True` is how a false 354
escapes.

---

## 7. What we are not claiming

- We are not claiming \(R(k,k)\ge C^k\) with \(C\ge 1.01\), for any
  infinite family constructed here.
- We are not claiming progress on Erdős #78.
- We are not claiming \(R(4,20)\ge 338\) or \(354\).
- We are not claiming that job 4c improves \(R(4,22)\).
- We are not claiming that this kernel certified Yu’s \(\alpha=19\).
- We are not claiming that Hoffman, Delsarte, or \(N^{1/k}\) is a
  Ramsey number.

---

## 8. Remaining work (if the criterion is still +1)

1. Recertify Yu’s residual with a second solver (OpenMP BnB, Cliquer,
   or SAT) before any new hunt.
2. Either extend the bitset past 256 *and* make timeout \(\ne\) accept,
   or force \(|S|\) high enough that the residual is \(\le 256\).
3. Prove or drop \(\alpha(G)=1+\alpha(G[N^c(0)])\) for mixed sets.
4. Put \(i,j\) and a hash of \(S\) in `graph_id`; emit Yu p=251 as
   exact only if `alpha_certified`.
5. Reseed 4b from a middle-third sum-free set; do not start from the
   empty mask.
6. Refresh `R4_LOWER` from DS1 r18 + post-Yu notes before choosing
   \(t\) for \(p=353\).

If the criterion is the public negative result, the wave is closed.

---

## 9. Conclusion

Run001 asked for an explicit exponential and delivered a surrogate
pipeline in which Paley wins \(C_{\mathrm{Hoff}}\) and local search
cannot leave Paley without becoming random. This session ran the
families that pipeline skipped, spent 28 hours confirming that
Hoffman class-unions do not move a survey cell, implemented Yu’s
search space, and then emitted a false \(R(4,20)\ge 354\) because
a 256-bit kernel was treated as a 264-vertex proof.

The number that moved is zero. The number that is still true is
Yu’s 252. The number that is still exact and diagonal in this tree
is Paley’s 17. The methodological number that matters is 256: the
width of the certificate.

---

## References

- Berghaus, J. and Wagner, A. ICLR 2025. RL edge-flip vs random on \(R(4,4)\).
- Bradač, D. June 2026. Off-diagonal Ramsey exponent (Erdős #986).
- Brouwer, A. E. and Haemers, W. H. *Spectra of Graphs*. 2012.
- Coniglio et al. August 2026. IP circulants; +1…+11 on \(R(3,n)\), \(n\le 410\).
- Erdős problems #78, #165, #183, #986. https://erdosproblems.com
- Kosmos Run001 discovery report. Edison Scientific playground
  `77856386-f79a-436a-84ab-0a28be7f94a9`.
- Li, X. 2023. Extractor lower bounds \((\log N)^C\).
- Mattheus, S. and Verstraete, J. *Annals of Mathematics*, 2024.
  \(r(4,t)=\Omega(t^3/\log^4 t)\).
- Nagda, Raghavan, Thakurta. AlphaEvolve small-cell constructions;
  Yu later beat their \(R(4,20)\ge 237\).
- Radziszowski, S. P. DS1, rev. 18 (24 April 2026).
- Yu. arXiv:2608.18169. \(R(4,20)\ge 252\) via a 32-subset of two
  quintic classes on \(\mathbb Z/251\mathbb Z\).

## Artefacts

| Object | Path |
|---|---|
| This paper | `docs/paper-a40-revision.md` |
| Campaign sheet | `docs/A40-CAMPAIGN.md` |
| Plan v2 | `docs/plan-move-a-number.md` |
| Hand-off | `docs/SESSION-HANDOFF.md` |
| Yu \(S\) | `data/yu_r4_20.json` |
| A40 dumps | `data/a40/` |
| Engine | `engine/jobs.py`, `engine/yu_pool.py`, `engine/kernels/native_mis.c` |
| Public tree | https://github.com/pageman/ramsey-gpu-constructions |
