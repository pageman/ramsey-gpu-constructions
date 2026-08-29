# Plan v2: GPU algorithms that can actually move a number

Supersedes the first `plan-move-a-number.md`. Same target: a **published finite
lower bound** in Radziszowski DS1, not Erdős #78. What changed is the
algorithm, not the ranking of families.

The A40 wave (jobs 1a–3c, 2a done 99755 s / 9288 Hoffman rows) is now
evidence, not a plan. It proved three negative theorems about *this* codebase:

1. Ranking whole cyclotomic class unions by Hoffman (job 2a, every prime
   \(p\le 9973\)) does not produce a survey cell. Paley exact \(\omega\) in
   this range is already in Shearer / Exoo. 9973 is just `cyclo_max`.
2. Job 3b’s circulant ILS for \(R(4,t)\) used Hoffman as the *search score*
   and never recertified Yu’s published \(S\). Wrong objective, no certificate.
3. `max_clique` for \(n>64\) is a 64-core subsample plus a Python greedy
   colouring that **has no timeout**. That is why 3d looks hung and why Yu’s
   186-vertex residual is unreachable. The kernel gap, not the family list,
   is why no number moved.

v2 is therefore a **solver + search-space** plan. Families stay Yu / distance
circulant / polarity. The algorithm is rewritten from Yu’s paper, the 2024–26
clique-solver instance-space, Coniglio’s IP paper, and the CP / Polymath
toolkit that actually applies at \(n\sim 250\).

---

## 0. One sentence

Cheap **filter** in the search loop; exact **decision** \(\alpha\le t-1\) in
the certificate; **never Hoffman** in either; **never** materialise the
\((p/2)\times(p/2)\) residual as a dense `numpy` matrix.

If a candidate cannot be rejected in \(O(p)\) or certified on a bitset of
width \(p\), it is not a job for this A40.

---

## 1. What “move a number” means (unchanged, tighter)

\(G\) on \(n\) vertices, \(\omega(G)<s\), \(\alpha(G)<t\) \(\Rightarrow\)
\(R(s,t)\ge n+1\). Spectral \(k\) is a ranking key, not a theorem.

| # | Attack | Cells | Witness | Why v1 failed | v2 change |
|---|---|---|---|---|---|
| **A** | Yu-style 2-class *subsets* | \(R(4,20)\)–\(R(4,25)\); beat 252 | \(p\in[200,400]\), residual \(\sim 150\)–\(250\) | 3b = Hoffman ILS on unrestricted masks | Restricted process on the 50-set pool + bitset decision MCS |
| **B** | Distance-space circulant \(R(3,t)\) | \(t\ge 50\) only | \(n\sim 500\)–\(900\) | 2c competed with Coniglio on \(t\le 49\); Hoffman score; MCS \(n\le 64\) | Incremental Schur filter + exact residual \(\alpha\); skip 24–49 |
| **C** | Polarity after \(K_4\)-delete | concrete \(R(4,t)>N\) at \(q\le 7\) | residual a few hundred | 1c/3c Hoffman on the *raw* graph | Delete \(K_4\)s, then exact \(\alpha\); \(q\ge 8\) is a maybe |

Catalogue (do not hunt): Ihringer–Mattheus \(TG_{d,h}\); Yip polynomial Paley.
Do not run: extractors, Bradač containers, PPO, more Paley / full class unions,
job 3d \(n=16\), AlphaEvolve-on-the-pod.

---

## 2. Why the current kernels cannot move a cell

Concrete, from this repo, not from taste.

| Kernel | What it does | Why it blocks a cell |
|---|---|---|
| `max_clique` \(n>64\) | 64-core subsample + `greedy_colour_bound` | Yu certifies \(\alpha=19\) on 186 vertices by **full** BnB. A 64-subset \(\omega\) is a lower bound on \(\omega\), an *upper* bound on \(\alpha\) of a *different graph*. Not a certificate. |
| `greedy_colour_bound` | Python loop, no timeout | 3d n=13 residual is \(4096\times 4096\). Colouring can run for hours with no log. |
| `ils_connection_set` | score = Hoffman(\(G\))+Hoffman(\(\overline G\)) | Hoffman on Paley-like graphs is \(\sim\sqrt n\). Every mask looks the same. The ILS has no gradient toward \(\omega\le 3\), \(\alpha\le 19\). |
| `mask=` argument | implemented, **never called by a job** | Yu’s space is \(\binom{50}{32}\) inside \(D_0\cup D_2\). Jobs 2a/3b search the wrong set. |
| `incremental_triangle_delta` | implemented, unused | \(K_3\)-free ILS rebuilds \(A^3\) or scans \(O(d^2)\). |
| `certify_boolean_cayley` / `certify_circulant_row` | materialises induced \(N\times N\) | 2a spent ~28 h building neighbourhoods of size \(\sim p/2\). Yu never does this. |
| Job 3A | docstring “from 2A winners”; code seeds Paley+Singer | Dead wiring. |
| `catalog.json` | last-writer-wins | Two jobs cannot run. `registry.jsonl` is the source of truth. |
| Job 2a | no checkpoint | Restart = p=13. The 28 h rerun was this. |

v2 does not “add job 4a on top of 3b”. It replaces the objective, the
certificate, and the memory layout.

---

## 3. Yu’s algorithm, as actually published (arXiv:2608.18169)

Read this before writing a kernel. The paper is **not** “cyclotomic +
Hoffman”. It is a three-stage pipeline on one prime.

**Stage 0 — pool.** Prime \(p=251\), \(e=5\), classes
\(D_i = g^i\langle g^5\rangle\). Pool \(P = D_0\cup D_2\), \(|P|=50\).
\(-1\in\langle g^e\rangle\) so the Cayley graph is undirected.
Connection set \(S\subset P\), \(|S|=32\), \(S=-S\).

Published witness (the regression test; if this fails, the cert is wrong):

```
S = {2, 4, 8, 10, 16, 21, 32, 37, 39, 42, 45, 63, 64, 73, 74, 78,
     84, 90, 91, 105, 126, 128, 146, 147, 148, 156, 168, 180,
     189, 210, 233, 243}
```

\(\omega(G)=3\), \(\alpha(G)=19\), hence \(R(4,20)\ge 252\).

**Stage 1 — restricted \(K_4\)-free process (search, cheap).**
Maintain \(S\) growing inside \(P\). A candidate \(x\in P\setminus S\) is
legal iff \(N(0)\) stays triangle-free after adding \(\pm x\).
Equivalently: no pair \(a,b\in S\) with \(a-b\in S\) and
\(\{a,b,a-b\}\) all in the new neighbourhood — the Schur / additive
formulation. Yu also runs simulated annealing on the same pool after the
process saturates.

This is **not** “enumerate \(\binom{50}{32}\)”. It is a filtered walk on a
50-element ground set. An A40 can run thousands of independent walks; it
does not need to store 50-choose-32.

**Stage 2 — certificate (exact, once per survivor).**
Vertex-transitive \(\Rightarrow\)

\[
\omega(G)=1+\omega(G[N(0)]),\qquad
\alpha(G)=1+\alpha(G[N^c(0)]).
\]

- \(N(0)=S\), \(|S|=32\). \(\omega(G[S])\le 2\) (triangle-free) is the
  process invariant. Check by bit-AND of neighbourhoods, \(O(|S|^2/64)\).
- \(N^c(0)=(\mathbb Z/p)^\times\setminus S\), 186 vertices. \(\alpha(G)=19\)
  iff the maximum clique of the **complement** residual is 19, iff
  \(\omega(\overline{G}[N^c(0)])=19\). Yu runs a bitset MCS (they cite the
  Tomita family) and report ~1.4 s for this one residual.

**What Yu does not do:** Hoffman, FFT, whole-class unions, GNN, IP on the
full edge set.

**What job 2a did:** every mask of *whole* classes, Hoffman only, \(p\) to
9973. Different search space, different (non-)certificate. Do not recertify
2a’s 9288 rows hoping one is Yu-like. A whole-class union that is \(K_4\)-free
with small \(\alpha\) would already be a Paley / GP cousin and would have
shown up in the survey.

---

## 4. The only data structure that matters

Store the connection set as a **length-\(p\) bitset** (four `uint64` at
\(p=251\); seven at \(p=400\)).

Circulant adjacency: \(i\sim j\) iff `row[(j-i) mod p]` is set. Vertex 0’s
neighbourhood *is* the row. The residual \(G[N^c(0)]\) is **not** a matrix.
Vertex \(u\in N^c(0)\) has residual neighbours

\[
v\in N^c(0),\quad v\neq u,\quad (v-u)\bmod p\in S.
\]

A bitset MCS on the residual needs, for each residual vertex \(u\), one
bitset of width \(|N^c(0)|\) — the columns of the induced graph. Build that
in \(O(p\cdot |N^c|/64)\) from the **row**, once, then throw the dense
matrix away. Never allocate \(186\times 186\) `float64`.

This is the O(n) rule the first plan stated and the kernels violated.

Memory at \(p=400\), residual 300: \(300\times 5\) uint64 \(\approx 12\) KB
for the MCS bitsets. An A40 can hold tens of thousands of residuals. The
bottleneck is the *CPU* BnB on each residual, not VRAM.

---

## 5. Algorithmic upgrades, ranked by effect on a cell

Literature and CP, only the tricks that change the **certificate** or the
**filter**. Asymptotic romance (better Hoffman, better \(\vartheta\),
extractor seed) is excluded.

### 5.1 Decision, not optimisation (CP / LeetCode binary-search-on-answer)

Survey cell \(R(4,t)\ge p+1\) needs \(\alpha\le t-1\), not \(\alpha\) exactly.
Östergård’s algorithm (Discrete Applied Math 2002) is designed for this:
colour-bound clique search that **stops when the incumbent reaches \(t-1\)**.
Yu needed the exact 19 to publish \(\alpha=19\). We need \(\alpha\le 20\) to
claim \(R(4,21)\ge p+1\). Abort the BnB the moment a clique of size \(t-1\)
is found — that *rejects* the candidate. Abort as **proven**
\(\omega_{\mathrm{comp}}<t-1\) when the colour bound dies. Do not sit in
optimisation mode for 1.4 s if a 20-clique appears at 50 ms.

This is the highest-leverage change vs “run Tomita to completion”.

### 5.2 Bitset Tomita / MCS, width \(n\le 256\) (Yu; Tomita–Sutani; San Segundo)

Replace `max_clique`’s \(n>64\) subsample with a real bitset solver:

- Adjacency: `uint64[n][(n+63)//64]`.
- Colour order: greedy colouring on the bitset (San Segundo / BBMC style).
- Recursion: `P & N[v]`, popcount, branch on the colour-bound cut.
- Optional: **bitset complement** so \(\alpha(G)=\omega(\overline G)\) is the
  same code path Yu uses.

Python + `numpy` uint64 is fine for \(n\le 220\) if the inner loop is tight
(numba, or a 50-line C extension). Do **not** start from NetworkX. Do **not**
call the current `greedy_colour_bound` as a substitute for the BnB.

Instance-space (San Segundo / CliSAT / MoMC 2024–26): sparse DIMACS and
crafted hard graphs need different solvers. **Circulant residuals are not
DIMACS random.** They are vertex-transitive leftovers: regular, structured,
colour-bound usually tight. CliSAT’s SAT encoding and MoMC’s recency
weighting are for a different instance class. Implement **one** bitset
Östergård/Tomita well before shopping solvers. If a residual at \(n=220\)
exceeds ~10 s with a colour bound, *then* try a second solver, not before.

### 5.3 Incremental \(K_3\) / \(K_4\) filter (additive combinatorics + Fenwick)

Yu’s legal-move test: after adding \(x\), \(G[S]\) stays triangle-free.

Additive form (circulant): \(S\) is triangle-free in \(G[N(0)]\) iff there
are no \(a,b\in S\) with \(a-b\in S\) *as an edge of the residual of 0*,
i.e. no Schur triple in \(S\) relative to the connection set — for a
Cayley graph on \(\mathbb Z/p\), a triangle on \(\{0,a,b\}\) is
\(a,b,b-a\in S\). So \(S\) is sum-free in the usual sense **and** the
neighbourhood graph has no triangle iff \(S\) is \(K_3\)-free as a Cayley
connection on itself.

Maintain:

- `row`: bitset of \(S\).
- `pair_counts[p]`: number of representations \(s-s'\) with \(s,s'\in S\)
  that would close a triangle when a new \(x\) is added.

Adding \(x\): scan \(S\) (32 bits), test `row[x-s]`. \(O(|S|)=O(32)\), not
\(O(d^3)\). Removing \(x\): same. This is the Fenwick / difference-array
move: store the **delta**, not the graph.

The existing `incremental_triangle_delta` is this idea unused. Wire it.
Drop the \(O(d^3)\) \(K_4\) scan on the full vertex set — VT says it is
enough to test \(G[N(0)]\).

### 5.4 Restricted process + ILS, not Hoffman ILS (Yu; Hansen–Mladenović ILS)

Search state = subset of the **pool**, not a free \(\{0,1\}^{(p-1)/2}\).

```
process(pool P, target |S| or saturation):
    S ← ∅
    while legal moves exist:
        pick x in P\S uniformly (or by a cheap score: #new illegal)
        if G[S ∪ {±x}] triangle-free: S ← S ∪ {±x}
    return S

anneal(S, steps):
    propose: swap x in S ∩ P with y in P\S (preserve S=-S)
    accept if still triangle-free and (exact-α-proxy improves or Metropolis)
```

**Score inside the loop (in order, stop early):**

1. Illegal \(\to\) reject. \(O(|S|)\).
2. `|S|` (larger neighbourhood \(\Rightarrow\) smaller residual \(\Rightarrow\)
   easier \(\alpha\)). Yu sat at 32/50.
3. Degree of \(G[N^c(0)]\) or a **sampled** greedy-\(\alpha\) (one random
   permutation, \(O(p)\)). This is a *lower* bound on \(\alpha\). If the
   greedy already finds an independent set of size \(t\), **reject** — the
   graph cannot certify \(R(4,t)\). This is the CP “fail fast on a witness”
   trick. Do not run MCS on a graph that already has a greedy \(\alpha\ge t\).
4. Hoffman: **never**, except as a catalogue field after a survivor is
   certified.

### 5.5 Multiplier automorphism / lex-min (CP Burnside; circulant folklore)

If \(S\) is a witness, so is \(\lambda S\) for \(\lambda\in(\mathbb Z/p)^\times\).
Store only the lex-min rotate-and-multiply representative. When a process
emits \(S\), replace it by \(\min\{\mathrm{lex}(\lambda S):\lambda\in(\mathbb Z/p)^\times\}\).
Dedup across GPU walks. This is why Yu can publish one \(S\) and not 250
rotates.

Cost: \(O(p\varphi(p)/2)\) bit rotations; at \(p=251\) this is nothing.
Do it **before** MCS, so 80 walks that found the same orbit burn one cert.

### 5.6 Batched filter on GPU, serial cert on CPU (workload split)

A40 job layout:

| Phase | Device | Work | Batch |
|---|---|---|---|
| Enumerate primes \(p\in[200,400]\) with \(e\mid(p-1)\), \(-1\in\langle g^e\rangle\) | CPU, once | sieve + discrete log | — |
| Build 2-class pools (quartic \(p\equiv 1\pmod 8\), quintic \(p\equiv 1\pmod 10\)) | CPU | \(O(p)\) | — |
| \(10^3\)–\(10^5\) restricted processes + anneal swaps | GPU or batched CPU | legal-move kernel | 10k states × 64-bit row |
| Greedy-\(\alpha\) reject | CPU vectorised | \(O(p)\) per state | all survivors |
| Lex-min + unique | CPU | hash of bitset | — |
| Decision MCS \(\alpha < t\) | **CPU, one core per residual** | bitset BnB | A40 has idle SMs here; that is fine |
| Ledger row | CPU | append jsonl | — |

Do not write a GPU MCS. San Segundo-style GPU clique is a research project
and the residuals are few (hundreds of unique \(S\), not millions). The A40
earns its rent on **batched legality + greedy reject**. The 1.4 s MCS is a
CPU problem Yu already solved.

If the process is so cheap that CPU saturates the pool in minutes, skip the
CUDA kernel. Profile first. A numba legal-move loop on 50-set pools may
beat a bad GPU launch.

### 5.7 Prefix / orbit pruning of the pool (IMO combinatorics; Knuth dancing)

\(\binom{50}{32}\) is \(4.7\times 10^{13}\). Do not enumerate.
If a *prefix* of the sorted pool already contains a Schur triple, every
superset dies. Branch-and-bound on the 50-set: add the next pool element
or not, prune when \(G[S]\) has a triangle, bound when
\(|S| + |remaining| < s_{\min}\) (Yu needed 32; we can take any even
\(|S|\) that beats a cell). This is exact search of the pool, complementary
to the random process. Run it on the **three** primes nearest Yu (241, 251,
269) where a missed 33-subset would be embarrassing. Do not B&B the pool
at every prime in 200–400.

### 5.8 Two-class, not \(2^e\) (Yu vs job 2a)

Job 2a searched all \(2^{e-1}\) class-union masks. Yu searched subsets of
**one** union of two classes. Those are incomparable. A 4-class union that
is \(K_4\)-free is a different (harder) filter. Do not reopen 2a. Optional
later: 3-class pools at \(e=6\) if 2-class saturates. Not this week.

### 5.9 Paley-clique incremental construction (Backelin-style; not for Yu)

Literature on Paley cliques (Shearer, Exoo, Backelin) incrementally grows a
clique in the residue graph. Dual: grow an independent set in the residual
to **kill** a candidate (the greedy reject of 5.4, but with a Paley-aware
pivot: start from a known QR configuration). Cheap. Use as a rejector, not
as a certifier.

### 5.10 What the survey of “algorithmic improvement literature” does *not* buy

| Paper / trick | Why it is not this week |
|---|---|
| CliSAT / SAT encoding of MCS | Residuals are structured circulant; SAT overhead > bitset |
| MoMC recency-weighted clique | For hard DIMACS; colour bound is the right cut here |
| GPU MCS (2023–26 surveys) | We have \(\ll 10^4\) residuals, not \(10^8\) |
| Incremental *exact* MCS (dynamic clique) | \(S\) changes every anneal step; rebuilding 12 KB bitsets is cheaper than dynamic MCS |
| Lovász \(\vartheta\) / Hoffman in the loop | Proved useless by 2a/3b on this instance class |
| AlphaEvolve / evolve the search code | Yu beat AlphaEvolve’s \(R(4,20)\ge 237\) with one pool. Evolving Python is not a kernel. |
| GNN / PPO (Berghaus–Wagner; Run001) | Paley attractor. Already decided. |
| Coniglio MIP on \(n\le 410\) | Already took \(R(3,24)\)–\(49\). Competing with a solved IP is wasted A40. |
| Extractors / Bradač | No enumerable adjacency. |

---

## 6. Job 4a (implement first): Yu-style pool search

**Name:** `4a`. **Owns:** Yu-pool. **Cell:** \(R(4,t)\) for \(t=20\dots 25\).

### 6.1 Regression gate (write this test before the search)

`data/yu_r4_20.json` holds the published \(S\). A unit test must:

1. Build Paley-style cyclotomic classes mod 251, \(e=5\), confirm
   \(S\subset D_0\cup D_2\).
2. Confirm \(S=-S\), \(|S|=32\).
3. Confirm \(G[S]\) is triangle-free (bitset), hence \(\omega(G)=3\).
4. Run the **new** bitset decision MCS on the 186-vertex residual and
   report \(\alpha\le 19\). If this takes >5 s or is wrong, **stop** — the
   cert is not ready for a hunt.

Until (4) is green, do not burn A40 hours.

### 6.2 Prime / pool enumerator

```
for p in primes(200, 400):
    for e in {4, 5, 8, 10}:
        if (p-1) % e: continue
        g = primitive_root(p)
        if pow(g, (p-1)//2, p) == p-1 and (p-1)//e even-or-minus-one-in-subgroup:
            # -1 in <g^e>  ⇔  e | (p-1)/2
            if (p-1)//2 % e: continue
            classes = cyclotomic_classes(p, e, g)
            for (i,j) in pairs with i < j:
                pool = classes[i] ∪ classes[j]
                yield Job(p, e, pool)
```

Quartic (\(e=4\)) when \(p\equiv 1\pmod 8\); quintic (\(e=5\)) when
\(p\equiv 1\pmod 10\). Also allow \(e=8,10\) as *coarser* pools (smaller
classes, still 2-class unions). Skip primes where the pool is the full
quadratic residues — that is Paley, already catalogued.

### 6.3 Search budget (A40, one night)

Per \((p,e,\mathrm{pool})\):

- 2 048 independent restricted processes (different RNG seeds).
- 4 096 anneal swaps per saturated \(S\), triangle-filter + greedy-\(\alpha\) reject.
- Lex-min, unique, keep the 32 smallest greedy-\(\alpha\) (best chance of
  \(\alpha < t\)).
- Decision MCS with \(t\) from the current survey lower bound for
  \(R(4,\cdot)\) at this \(n=p\).

Targets, in order:

| Priority | Goal | Why |
|---|---|---|
| 0 | Recertify Yu \(S\) | Gate |
| 1 | Any \(S\subset\) pool on \(p=251\) with \(\alpha\le 18\) | Beat 252, or a second witness |
| 2 | \(p=241,269,271,281,311,313,331,349,353,359,373,379,389,397\) | Neighbours; 313 already has quartic \(R(4,22)\ge 314\) — do not waste time matching that cell, try \(R(4,21)\) and \(R(4,23)\) |
| 3 | \(R(4,21)\) on some \(p\sim 260\)–\(310\) | Survey still weak vs the 314 next to it |
| 4 | \(R(4,23)\)–\(R(4,25)\) | Diminishing; only if 1–3 are dry |

Checkpoint every prime to `registry.jsonl`. Restart = last prime, not p=13.

### 6.4 Acceptance

A ledger row is a **cell** only if:

- `omega_exact == 3` (triangle-free \(N(0)\), bitset),
- `alpha_exact <= t-1` (decision MCS, full residual, not a 64-subset),
- `n == p`, `family == yu_pool`,
- `S` stored as a sorted list, plus `p, e, pool_id, seed`.

Hoffman may be attached as metadata. It must not gate acceptance.

---

## 7. Job 4b: distance-space \(R(3,t)\) for \(t\ge 50\)

Coniglio–Lancia–Lodi–Sanità (Optimization Online, 19 Aug 2026) already
moved 25 cells of \(R(3,n)\) for \(n\le 49\) by IP in the projected
distance space, \(N\le 410\). **Do not rerun \(t\le 49\).** That is
competing with a solved MIP on CPU.

What they did not hand us:

- Circulants for \(R(3,t)\) at \(t\ge 50\) (\(n\) will exceed 410; IP dies).
- Polycirculants / two-block (our 3a shape) at those \(t\).
- A GPU process that is not IP.

Algorithm (retarget 2c):

- State: bitstring of length \((n-1)/2\), \(n\) odd, \(S=-S\).
- Filter: incremental Schur — \(S\) sum-free \(\Leftrightarrow\) triangle-free
  circulant. \(O(1)\) / \(O(|S|)\) per flip via the difference table.
- Reject: greedy \(\alpha\) on \(N^c(0)\) \(\ge t\).
- Cert: decision MCS \(\alpha\le t-1\) on residual of size \((n-1)/2-|S|\).
  At \(n=500\), residual can be ~200–300. Same solver as 4a.
- Score: **not** Hoffman. Use \(|S|\) (larger clique-cover of the complement
  side) and greedy \(\alpha\).

Stop a run if the residual exceeds ~280 before the MCS is proven <10 s on
the Yu residual. Otherwise you reinvent 3d’s hang.

---

## 8. Job 4c: polarity graphs, \(K_4\)-clean, exact \(\alpha\)

Mattheus–Verstraete is an **asymptotic** independent-set count. A finite
cell needs \(\omega\le 3\) and \(\alpha\le t-1\) on a concrete graph.

v1 said \(q=7,8,9,11\). v2 tightens:

| \(q\) | Raw polarity \(n\) | After deleting vertices of \(K_4\)s | Exact \(\alpha\)? |
|---|---|---|---|
| 5 | tiny | toy | yes, already uninteresting |
| 7 | hundreds | possibly MCS | **do this** |
| 8, 9 | larger | maybe | only if \(q=7\) cert is <1 min |
| 11, 13 | job 3c already Hoffman-\(k>123,171\) | residual too big | **do not** run exact MCS |

Algorithm:

1. Build the polarity graph (already in `constructions.py`).
2. Enumerate \(K_4\)s — on a polarity graph this is geometric (totally
   isotropic 2-spaces), not \(O(n^4)\). Delete a hitting set of vertices
   (greedy set cover on the \(K_4\) list) to kill all \(K_4\)s.
3. The leftover \(H\) has \(\omega\le 3\). Compute **decision** \(\alpha(H)<t\)
   with the same bitset solver. \(H\) is **not** vertex-transitive — no VT
   residual. If \(|V(H)|>256\), this job stops.

Hoffman on the raw graph (1c/3c) underestimates \(H\). That statement from
v1 is still true. The honest counterpart of Mattheus–Verstraete is this
deletion + exact \(\alpha\), not a new theorem.

---

## 9. Catalogue only (one CLI flag, no hunt)

- **Ihringer–Mattheus \(TG_{d,h}\)** (arXiv:2608.05712): Singer-circulant,
  \(n=(2^{hd}-1)/(2^h-1)\), adjacency \(\mathrm{Tr}(ax/y)=0\). Emit
  \(d=4,5\), \(h\le 8\), FFT spectrum, compare to Paley at the same \(n\).
  Will not beat Paley(17) on \(C^*\). Fills the algebraic gap.
- **Yip et al. polynomial Paley-like (2024):** low-degree \(f\in\mathbb F_q[x]\),
  not Cayley. Build, Hoffman-compare to Paley, stop. Expected: Paley wins.

Neither gets an A40 night.

---

## 10. Implementation order (this is the job list)

Write code in this order. Each step has a test that must pass before the
next burns GPU time.

| Step | Deliverable | Test |
|---|---|---|
| 0 | Bitset graph + Östergård/Tomita, \(n\le 256\), **decision** mode | Random graphs \(n=40\) match NetworkX; \(n=64\) match current MCS |
| 1 | Residual-from-row: bitsets of \(G[N^c(0)]\) in \(O(p\cdot r/64)\) | Paley(17): \(\alpha=3\); Paley(29): known \(\alpha\) |
| 2 | Yu \(S\) regression | \(\omega=3\), \(\alpha=19\) on 186 vertices, <5 s |
| 3 | Incremental triangle on a pool bitset | Adding Yu’s last point stays legal; a Schur triple is rejected |
| 4 | Restricted process + anneal + lex-min + greedy-\(\alpha\) reject | Recovers a 32-subset of \(D_0\cup D_2\) mod 251 that is triangle-free (not necessarily Yu’s) |
| 5 | Job `4a` CLI: primes 200–400, checkpoint jsonl | Dry-run \(p=251\) only, 64 seeds, <2 min |
| 6 | A40 night: full 4a | Ledger cells or a written negative (pools saturated, \(\alpha\) too big) |
| 7 | Job `4b` only if 4a is dry or as a second night | \(t\ge 50\) |
| 8 | Job `4c` \(q=7\) | Exact \(\alpha\) or “residual >256” |

Do not start step 6 until step 2 is green. That is the whole lesson of 3d.

---

## 11. What not to spend A40 hours on (v2, evidence-based)

| Item | Why, now with A40 data |
|---|---|
| More Paley / full cyclotomic class unions \(p>10^4\) | 2a already did \(\le 9973\) Hoffman. Spectral \(k\) inflates. Exact Paley \(\omega\) is Exoo’s job, not ours. |
| Recertifying 2a’s 9288 rows with MCS | Wrong space (whole classes). Almost all have \(\omega\ge 4\) or huge \(\alpha\). |
| Job 3d \(n=16\) | Induced \(32768\times 32768\) + Python colouring. Spectral trap. Ctrl-C after n=13/14. |
| Job 3b-style Hoffman ILS | 59 graphs, 12 s, zero cells. The score is blind. |
| Li / Cohen / BRSW extractors | Clique bound is in the analysis. GPU MCS at feasible \(N\) cannot certify \((\log N)^C\). |
| Bradač product | Containers; no adjacency to enumerate. |
| PPO / GNN / AlphaEvolve-on-the-pod | Paley attractor; Yu already beat AlphaEvolve on \(R(4,20)\). |
| Coniglio range \(R(3,24)\)–\(49\) | IP paper owns these cells. |
| GQ \(q=11,13\) exact MCS | 3c Hoffman already; residual not in bitset range. |
| Training a ranker on 2a masks | `mask_ranker.json` predicts Hoffman. Hoffman is not the objective. |

---

## 12. Bottom line

#78 is unchanged: no GPU family here is an infinite \(C\ge 1.01\).

The 2026 papers that move **finite** bounds are:

1. Restricted cyclotomic **subsets** + exact residual MCS (Yu).
2. Circulant distance-space search (Coniglio IP; our piece is the
   \(t\ge 50\) process they did not run).
3. Exact \(\alpha\) on a \(K_4\)-cleaned polarity graph (computational
   counterpart of Mattheus–Verstraete, not a new theorem).

Everything else is catalogue or a different Erdős problem.

The highest-leverage **new** job is still Yu-style — but the first A40
wave already ran the *wrong* Yu-adjacent jobs (2a, 3b). The next wave is
not “more primes”. It is:

**bitset decision MCS on residuals built from the circulant row, gated on
a reproduction of Yu’s \(S\), then a restricted process on 2-class pools
for \(p\in[200,400]\).**

Until that certificate exists, an A40 hour spent on another construction
family is a catalogue hour, not a cell hour.
