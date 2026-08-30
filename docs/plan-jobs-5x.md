# Plan v3: jobs 5a–5f after the A40

Supersedes the *ranking* in `docs/plan-move-a-number.md` (v2). Families
stay Yu / distance circulant / polarity. What changed is the **order of
operations** and the **referee**.

#78 is still open. The A40 did not touch it and did not move a
Radziszowski cell. It killed three algorithms and named the bottleneck:
a **decision MIS of width 186–280**. GPU billed; jobs 2a/4a were CPU.

**Do not start 5c/5d/5e until 5a is green.** That is the whole lesson of
4a’s void `CELL?` lines.

CLI names: `5a` `5b` `5c` `5d` `5e` `5f`, plus `phase5` = 5a then halt
unless 5a reports `alpha_certified`. Pod one-shot:
`docs/POD-PHASE5.md` / `scripts/pod-phase5.sh`.

---

## 0. Job list

| Job | Name | Cell | Success | Depends on |
|---|---|---|---|---|
| **5a** | Recertify Yu residual 186 | \(R(4,20)\) | Independent decision \(\alpha\le 19\) in minutes, node count \(\sim 10^7\) | nothing |
| **5b** | Referee kernel | cert | Width + timeout≠accept + reductions + mixed-set rule; freeze `decide_alpha_le` | 5a green (or 5a proves our C kernel can be made to match) |
| **5c** | Yu pool hunt (4a, corrected) | \(R(4,20)\)–\(R(4,25)\) | New \(S\) with residual the referee can finish; `CELL?` only if `alpha_certified` | 5a + 5b |
| **5d** | \(R(3,t)\) \(t\ge 50\), nonempty seed | \(R(3,k)\) | Residual \(\le\) width; beat a DS1 floor, not Coniglio 24–49 | 5b |
| **5e** | \(K_4\)-clean polarity leftover | \(R(4,t)\)-geom | Leftover \(\le\) width **and** \(N+1\) above published \(R(4,t)\) | 5b |
| **5f** | Catalogue \(TG_{d,h}\) / Yip | cert | One flag, Hoffman vs Paley, no night | none |

`phase5` runs 5a and **stops** if the second solver does not decide
Yu’s residual. It does not chain into 5c.

---

## 1. Empirical negatives this plan must not repeat

| Fact | Consequence for 5x |
|---|---|
| 2a: 9288 unions, \(p\le 9973\), 28 h, no cell | No Hoffman class-union job |
| 3b: never recovered Yu \(S\) | No Hoffman ILS score |
| 4a: structural Yu **pass**; \(\alpha=19\) **timeout**; \(p=337/353\) residual 262/264 printed 354 | Never accept \(n>\)width; never `exact` from structural flag |
| 4b: empty mask, residual \(>280\), 0 graphs | Seed a nonempty sum-free set |
| 4c: \(\alpha=21\) on 84 verts, \(R(4,22)>84\) vs \(\ge 314\) | Gate on leftover size **and** published floor |
| GPU unused in the inner loop | GPU = batched legality + greedy reject only |

Published \(R(4,20)\) remains **252**. Paley(17) remains the exact
diagonal jewel. Width **256** is part of the certificate (T4).

---

## 2. Job 5a — recertify Yu’s residual (do this first)

Same \(S\subset\mathbb Z/251\mathbb Z\) as `data/yu_r4_20.json`. Residual
\(G[N^c(0)]\) has 186 vertices. Need a **second** decision
“no independent set of size 19”.

Yu (arXiv:2608.18169) already specifies the referee:

- Bitset MCS as in Prosser: binomial expand, static smallest-last
  (MCR / BBMC), greedy matching colour bound on the complement,
  Östergård \(c[i]\) prune `depth + c[min P] < 19`.
- Flatten the first two branching levels; OpenMP dynamic schedule,
  twelve threads.
- \(\sim 2.7\times 10^7\) nodes, \(\sim 1.4\) s.
- CP-SAT maximisation on the same residual found an 18-set, so
  \(\alpha(G)\ge 19\). Combined: \(\alpha=19\).

**5a deliverable.** A binary or CLI `decide_alpha_le --graph yu186 --t 19`
that finishes in minutes and prints `{found, nodes, seconds, backend}`.
Acceptable backends, in order:

1. Reimplementation of Yu’s bitset + OpenMP (preferred: same instance
   class).
2. Cliquer / Tomita / BBMC on the **complement** residual (clique of
   size 19).
3. OR-Tools CP-SAT decision (`α ≥ 19` abort; `α < 19` prove).
4. KaMIS `branch_reduce` after kernelization (PACE 2019 vertex-cover
   winner is the complement view).
5. CliSAT / MOMC if the residual is dense in the instance-space sense
   of arXiv:2512.03419.

**Pass.** `found=false`, `timed_out=false`, nodes within an order of
Yu’s \(2.7\times 10^7\), and a second backend agrees. Freeze that
binary. Write `data/yu_r4_20.cert.json`.

**Fail.** Stop. Do not run 5c. Another 4a night reprints 252 or a
false 354.

This is not a new family. It is stage three of the only 2026 method
that already moved \(R(4,20)\).

---

## 3. Job 5b — referee kernel (width, reductions, mixed sets)

Ship `engine/kernels/decide_alpha_le` used by 5c–5e.

### 3.1 Contract (non-negotiable)

- `n > MAXN` → do not call the bitset entry; return
  `{exact: false, timed_out: true, backend: skip_n}`.
- Timeout → `{exact: false}`. Never `CELL?`.
- `exact=True` only if the tree finished **and** mixed-set rule
  (below) is satisfied.
- `graph_id` includes \(p,e,i,j\) and a 64-bit hash of lex-min \(S\).
- Yu \(p=251\) is exact only if `alpha_certified`.

### 3.2 Mixed-set hole

Rejects remain valid: a residual \((t-1)\)-IS implies
\(\alpha(G)\ge t\). Accepts are incomplete if a large IS lives in
\(N(0)\) or mixes \(N(0)\) with the residual.

**Rule for 5b.** Before `CELL?`:

- \(\alpha(G[N(0)])\le t-2\) (triangle-free, \(|S|\) small: exact MIS
  on \(\le 64\) verts is cheap), **and**
- no mixed IS of size \(t-1\) (branch: pick \(k=1..t-2\) vertices from
  \(N(0)\), delete their residual neighbourhood, decide residual IS of
  size \(t-1-k\)). \(k\) is tiny because \(N(0)\) is triangle-free and
  greedy \(\alpha(G)\) already \(<t\).

If that mixed check is not implemented, print `residual_only` and
do not print `CELL?`.

### 3.3 Width

Either `WORDS=5` (\(n\le 320\)) or `WORDS=8` (\(n\le 512\)) **and**
the skip/timeout contract, **or** force \(|S|\) high enough that
\(p-1-2|S|\le 256\). Do not call a 256-word kernel on 262 vertices.

---

## 4. Algorithmic improvements (what 5b/5c actually implement)

### 4.1 \(O(n)\) / \(O(|S|)\) filters (search loop)

These replace the \(O(|S|^3)\) full `nbhd_triangle_free` on every trial
and the \(O(r^2)\) dense residual build.

| Technique | Source | Use |
|---|---|---|
| Incremental Schur | Additive combinatorics; already sketched in `incremental_triangle_delta` | Adding \(d\): only test pairs that use \(d\). \(O(|S|)\) bit tests |
| Neighbourhood bit-AND | Yu stage 1; CP bitset BK | \(N(a)\land N(b)\land S\) empty \(\Leftrightarrow\) no triangle through \(a,b\) |
| Residual-from-row | plan v2 | \(O(p\cdot r/64)\) word writes; never `(p/2)×(p/2)` numpy |
| FFT rank-1 update | circulant lore; unused | If anyone scores spectrum again: \(O(p)\), not a full FFT. **Not** a search score |
| Linear sieve + primitive root cache | Euler / Project Euler | `iter_yu_pools` already; cache \(g\) per \(p\) |
| Lex-min early abort | TopCoder string lex | Compare multipliers left-to-right; stop at first greater prefix. Orbit size \(\varphi(p)/2\) |
| Rolling hash of \(S\) | CP string / Zobrist | `graph_id` suffix; Bloom filter of seen lex-min keys |
| Greedy MIS degree sort | bitset_mcs | Already; keep as rejector only |
| Prefix popcount | LeetCode bit tricks | Colour UB / residual degree in registers |
| Batched legality on GPU | plan v2 GPU role | One kernel: \(k\) candidate distances × current \(S\) bitset, warp vote. Only if CPU filter is the clock (4a showed it was not) |

**Do not** put Hoffman, \(N^{1/k}\), or \(C(\alpha)=\alpha^{1/\alpha}\)
in this loop.

### 4.2 Competitive-programming / olympiad toolkit (referee)

| Technique | Source | Use at \(n\sim 186\) |
|---|---|---|
| Bitset Tomita / BBMC | Prosser survey; Yu | Static smallest-last order; colour-class branch |
| Östergård \(c[i]\) | Yu; our `native_mis.c` | Russian-doll suffixes; keep, but fix `n>MAXN` |
| Matching colour bound | Yu; CP | Greedy matching on the complement for UB |
| Degeneracy / core (Batagelj–Zaversnik) | LeetCode \(O(m)\) | Relabel before BnB (already in C) |
| Isolated / deg-1 / folding / twins | Fomin–Grandoni–Kratsch; KaMIS | Kernelize residual before BnB |
| Mirror / satellite rules | Fomin et al.; Gao–Wang–Zhang–Liu arXiv:2412.07685 | On-the-fly branching rules for sparse leftovers |
| Crown / LP-based VC reductions | PACE 2019 / KaMIS | Complement view if residual is sparse |
| Component split | standard | If residual disconnects, product of α |
| Decision not optimisation | Yu; Polymath | Abort on first 19-set (reject) or colour-bound death (accept) |
| Flatten first two levels + OpenMP | Yu | 12-way dynamic schedule; this is why 1.4 s vs our 25 s |
| CP-SAT for a lower bound only | Yu used it for an 18-set | Witness \(\alpha\ge 19\) cheap; do not use SAT as the only accept |
| Instance-space routing | arXiv:2512.03419 | Dense residual → CliSAT/MOMC; sparse → KaMIS BnR. **Not** IPDPS GPU MCS |
| Gray code | 2a masks | Only for tiny \(e\); 5c uses process+anneal |
| Middle-third sum-free | Cauchy–Davenport / folklore; Putnam-style | Seed 5d, not the empty mask |
| Dihedral lex-min | circulant automorphism | Already; store the representative |
| Meet-in-the-middle / SOS DP | CP \(n\le 40\) | **No.** \(2^{93}\) is not a job |
| GNN branching (SEA 2024) | targeted branching papers | **After** 5a is green; not the first week |

### 4.3 Literature RAG (current solvers, not families)

| Paper / artefact | Take |
|---|---|
| Yu arXiv:2608.18169 | Pool + process + 186-vertex bitset BnB + OpenMP + CP-SAT LB |
| arXiv:2512.03419 | Clique instance space; pick CliSAT vs colouring BnB by density |
| CliSAT / MOMC / WLMC | MaxSAT / mixed-order clique; use if 5a C kernel stays slow |
| KaMIS / PACE 2019 VC | Reductions before exact; good if leftover is sparse |
| Gao et al. arXiv:2412.07685 | Auto branching rules; \(O(1.044^n)\) on 3-regular — residual is **not** 3-regular |
| LearnAndReduce arXiv:2412.14198 | GNN-gated reductions; optional after a CPU referee works |
| Coniglio et al. 2026 | Owns \(R(3,24)\)–\(49\); 5d starts at \(t\ge 50\) |
| Exoo / Tatarevic / Kuznetsov | Circulant table lore; seeds, not Hoffman rankers |
| Mattheus–Verstraete 2024 | Asymptotic \(r(4,t)\); 5e is finite leftover \(\alpha\) only |
| Ihringer–Mattheus \(TG_{d,h}\) | 5f catalogue |
| Berghaus–Wagner ICLR 2025 | No PPO |
| AlphaEvolve (Nagda et al.) | Yu already beat their \(R(4,20)\ge 237\); no LLM loop on the pod |

Refresh `R4_LOWER` from DS1 r18 + Yu before 5c picks \(t\) at \(p=353\).
Coded floors today: 20→252, 21→252 (Yu also improves 21 via the same
graph), 22→314. Hunt \(R(4,21)\) / \(R(4,23)\)–\(25\) if \(p+1\) cannot
beat 252 honestly.

### 4.4 Cursor / Grok resources (what to actually open)

| Resource | Use |
|---|---|
| `engine/yu_pool.py` `certify_row_decision` | Current accept/reject; edit here |
| `engine/kernels/native_mis.c` | Width + `timed_out` writes |
| `engine/kernels/bitset_mcs.py` | `skip_n>256`; wire 5b |
| `engine/kernels/residual.py` | Incremental triangle; mixed-set |
| `data/yu_r4_20.json` | 5a instance |
| `docs/A40-CAMPAIGN.md` | What 4a actually logged |
| `docs/paper/gpu-constructions-after-run001.tex` | Claims we must not contradict |
| Yu HTML arXiv:2608.18169 | Stage-2 algorithm, node counts |
| KaMIS GitHub | Optional second backend |
| OR-Tools on the pod image | CP-SAT LB |
| This file | Job order |

Do not re-derive Paley spectra. Do not re-open #78.

---

## 5. Job 5c — Yu pool hunt (only after 5a+5b)

Keep the 2-class process: \(p\in[200,400]\), \(e\in\{4,5,8,10\}\),
triangle-free \(N(0)\), greedy \(\alpha\ge t\) reject, lex-min.
Change the accept rule:

- Residual \(n>\) width: skip, or raise \(|S|\) until
  \(p-1-2|S|\le\) width. Never call the 256-word entry on 262/264 verts.
- Timeout ≠ accept.
- Mixed-set rule from 5b, or no `CELL?`.
- Targets: a *new* \(S\) at \(p=251\) with \(\alpha\le 18\) (beat 252),
  or \(R(4,21)\) / \(R(4,23)\)–\(25\) where the survey is weak vs
  \(R(4,22)\ge 314\).

4a already showed the **search** is cheap (greedy killed almost every
walk; 1715 s). The **referee** is the job.

GPU role, if any: batch 64 legality tests per walk. Profile first.
If CPU filter \(<1\) ms/walk, skip CUDA.

---

## 6. Job 5d — \(R(3,t)\) for \(t\ge 50\)

Coniglio owns 24–49. 4b from the empty mask stayed residual \(>280\).

Seed from the middle-third sum-free set
\(\{\lfloor n/3\rfloor+1,\ldots,\lfloor 2n/3\rfloor\}\) (or a known
cyclic \(R(3,k)\) seed). Incremental Schur \(O(|S|)\). Same referee
as 5b. Skip if residual \(>\) width. Finite cells, not #165.

---

## 7. Job 5e — polarity leftover vs the published floor

4c proved the kernel works at \(n=84\) and that \(W(3,7)\) leftover
\(\alpha=21\) does not beat 314. Next \(q\) only if after \(K_4\)-delete
the leftover is \(\le\) width **and** \(N+1\) exceeds the current
\(R(4,t)\) floor for \(t=\alpha+1\). Hoffman on the raw polarity graph
stays catalogue (1c/3c).

---

## 8. Job 5f — catalogue hour

Ihringer–Mattheus \(TG_{d,h}\); Yip polynomial Paley-like. One flag,
FFT/Hoffman vs Paley at the same \(n\). Closes the Run001 family gap.
Will not beat Paley(17) on exact diagonal \(C\). 2a already showed
class-unions do not move a cell.

---

## 9. Implementation order

| Step | Job | Test before the next step |
|---|---|---|
| 0 | 5a | Yu residual: no 19-IS, second backend agrees, nodes \(\sim 10^7\) |
| 1 | 5b | Empty \(n=257\) is not exact-accept; Paley(17) residual still exact; mixed-set test on a toy circulant |
| 2 | 5c dry | \(p=251\), 16 walks, no `CELL?` unless `alpha_certified` |
| 3 | 5c A40 | Only if step 0 is green |
| 4 | 5d | Middle-third seed; residual \(\le\) width or skip |
| 5 | 5e | Leftover gate + floor gate |
| 6 | 5f | Optional |

Do not start step 3 until step 0 is green.

---

## 10. What not to spend the next A40 on

- Another 2a / 3b Hoffman night.
- 4a/5c with the 256-word kernel on residuals \(>256\).
- 4b/5d from the empty mask.
- 4c/5e at \(q=11,13\) without leftover-size **and** floor gates.
- 3d ANF \(n=15,16\).
- Structural Yu / `exact=True` as a certificate.
- PPO, GAT, AlphaEvolve-on-the-pod, extractors, Bradač products,
  \(C=N^{1/k}\) as an objective.
- Meet-in-the-middle on 186 vertices.
- IPDPS GPU MCS trees (instance space: wrong regime).

---

## 11. Bottom line

#78 is unchanged. The finite list that can still move is the same
three papers (Yu, Coniglio, polarity-\(\alpha\)). The A40 changed the
order:

1. **5a** — second-solver recertify of Yu’s 186-vertex residual.
2. **5b** — width + timeout + mixed-set rule.
3. **5c** — the same Yu pool hunt, only on residuals the referee can
   finish.
4. **5d** — \(R(3,t)\) for \(t\ge 50\) from a nonempty seed.
5. **5e** — polarity leftovers that sit above the published floor.
6. **5f** — catalogue, one flag.

Until 5a is green, another construction family is a catalogue hour.
The number that is still true is **252**. The number that is still
exact and diagonal in this tree is Paley **17**. The numbers that
matter for the next wave are **186** (can you decide it?) and **256**
(does the kernel admit it?).
