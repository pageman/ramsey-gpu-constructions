# Plan: GPU algorithms that can actually move a number

This is an implementation plan, not a research essay. The target is a **published finite lower bound** in Radziszowski DS1 (rev. 18, 2026), not Erdős #78 and not \(N^{1/k}\).

Current kernels already know the right *identities* (VT reduction, FFT spectrum, sum-free \(\Leftrightarrow\) triangle-free, distance-space ILS). They spend the budget on the wrong *objective* and cannot *certify* the graphs that would move a cell.

---

## 0. What “move a number” means

A graph \(G\) on \(n\) vertices with \(\omega(G)<s\) and \(\alpha(G)<t\) is a theorem: \(R(s,t)\ge n+1\). Spectral \(k\) is not a theorem. Hoffman-\(k\) on Paley(997) will never enter the survey.

Three attack surfaces, ranked by chance of a survey entry:

| # | Attack | Survey cells | Witness size | Status in this repo |
|---|---|---|---|---|
| **A** | Yu-style 2-class cyclotomic *subsets*, \(K_4\)-free process, exact \(\alpha\) on \(N^c(0)\) | \(R(4,20)\)–\(R(4,25)\); Yu has \(R(4,20)\ge 252\) on order 251 | \(n\in[200,400]\), residual \(\sim 150\)–\(250\) | Job 3B does unrestricted Hoffman ILS. **Wrong search, weak cert.** |
| **B** | Distance-space circulant \(R(3,t)\), exact residual \(\alpha\) | \(R(3,24)\)–\(R(3,49)\); Coniglio et al. Aug 2026 already took +1..+11 on 25 cells | \(n\le 410\) | Job 2C: sum-free ILS, Hoffman score, MCS only to \(n\le 64\). |
| **C** | Exact \(\alpha\) on GQ / unital polarity after \(K_4\)-deletion | concrete \(R(4,t)>N\) at small \(q\) | \(q\le 9\) exact; \(q=11,13\) decision | Jobs 1C/3C emit Hoffman on the *raw* polarity graph. |

Jobs 4 (Ihringer–Mattheus \(TG_{d,h}\)) and 5 (polynomial Paley-like) are catalogue. They do not move a survey cell on an A40 weekend. Do not schedule them ahead of A–C.

**Hard rule:** search uses a *cheap filter*; only a shortlist is handed to an *exact decision* solver \(\alpha\le t-1\) / \(\omega\le s-1\). Never score the ILS loop with Hoffman.

---

## 1. Why the current kernels cannot move a number

Read against `engine/kernels/{cayley,mcs,rowcert,spectrum}.py`.

| Bottleneck | What the code does | Why it blocks a bound |
|---|---|---|
| **Wrong objective** | `_score_row` = \(\max(\alpha_{\mathrm{Hoff}}(G),\alpha_{\mathrm{Hoff}}(\bar G))\) | Yu maximised \(\lvert S\rvert\) among \(K_4\)-free subsets of a 50-element pool, then *proved* \(\alpha=19\). Hoffman is a loose \(\alpha\) *upper* bound; minimising it does not produce \(K_4\)-free dense witnesses. |
| **MCS dies at \(n>64\)** | `max_clique` takes the 64 highest-degree vertices and greedy-colours the rest | Yu’s residual has **186** vertices. A 64-core subsample cannot certify \(\alpha\le 19\). |
| **No decision mode** | Always computes \(\omega\), never “is \(\alpha < t\)?” | Decision with a target is \(10\)–\(100\times\) faster (Östergård prune \(c[i]\), early abort). |
| **Full FFT every flip** | ILS rebuilds the row and FFTs \(G\) and \(\bar G\) each step | Flip of distance \(d\) updates every eigenvalue in **\(O(n)\)**: \(\lambda_j \gets \lambda_j \pm 2\cos(2\pi jd/n)\). Hoffman is not needed in the loop anyway. |
| **`incremental_triangle_delta` unused** | Exists, never called from `ils_connection_set` | Triangle / \(K_4\) filters should be \(O(n)\) / \(O(d)\) bitset, not a fresh convolution. |
| **\(K_4\) test is \(O(d^3)\)** | Triple loop over \(S\) | Induced \(G[S]\) is triangle-free iff no Schur triple in \(S\) among neighbours of a new point. Bitset: \(O(d^2/64)\) or \(O(d)\) incremental on add. |
| **No cyclotomic *pool*** | 2A enumerates *whole class unions*; 3B ILS is unrestricted on \(\lfloor n/2\rfloor\) bits | Yu searched a **32-subset of a 50-element pair of classes**. The mask argument of `ils_connection_set` is wired and unused by any job. |
| **No multiplier canonicalisation** | Every \(\lambda S\) for \(\lambda\in(\mathbb Z/n)^\times\) is isomorphic | Search space is \(\varphi(n)\) too large. Keep lex-min under multiplication. |
| **No Russian-doll / matching colour** | Greedy colour via Python `set` | Yu: smallest-last + matching colour bound on the complement + \(c[i]=\alpha(G[\{i,\ldots\}])\). |
| **Two-block ILS materialises \(n\times n\)** | `two_block_adj` then greedy clique | For \(n>80\) this is the wrong representation. Stay in \(O(n)\) rows. |

---

## 2. Shared kernel upgrades (do these first)

Every later job is blocked on the certifier. Ship these before any new search.

### 2.1 Word-RAM MCS that survives \(n\sim 256\) — `engine/kernels/mcs.py`

Replace the \(n>64\) “core subsample” with a real bit-parallel solver. Literature stack, in the order Yu / Prosser actually used:

1. **Bitset adjacency**, `uint64` limbs, already sketched in `pack_neighbours`. Finish it: `P`, `X`, `R` as limb arrays; intersection = `AND`; popcount = `np.bitwise_count` / `__builtin_popcountll`.
2. **Smallest-last / degeneracy order** (MCR / BBMC). Current `degeneracy_order` is \(O(n^2)\) numpy `argmin`. Batagelj–Zaversnik **bucket queue** is \(O(n+m)\).
3. **Tomita MCS pivot** on limbs (already in `_mcs_small` for \(n\le 64\)). Lift to multi-word.
4. **Greedy colour bound via bitsets**, not Python `set` (San Segundo BBMC). Recolouring (MCS, Tomita–Sutani) if the first colouring does not prune.
5. **Greedy matching colour bound on the complement** (Yu §5). Cheap, often tighter than greedy colour on circulant residuals.
6. **Östergård Russian dolls** \(c[i]=\omega(G[\{v_i,\ldots,v_{n-1}\}])\) in the static order. Prune: `depth + c[min P] < target`. This is the single highest-leverage prune for *decision*.
7. **Decision API**: `clique_at_least(adj, k, time_limit) -> bool` and `independent_set_at_most(adj, t, ...)`. Search calls these, not exact \(\omega\).
8. **Flatten first two branch levels** into independent work items (Yu: 12 OpenMP threads, \(2.7\cdot 10^7\) nodes, 1.4 s on a 186-vertex residual). On the A40: CPU OpenMP for the BnB tree (irregular; GPUs lose), GPU only for batched *filters* (see §3).

Instance-space note (arXiv:2512.03419): dense, uniform, small-diameter graphs (circulant residuals) favour **CliSAT / Gurobi**; sparse hub graphs favour **MoMC**. Circulant \(N^c(0)\) is dense-ish. Keep a SAT fallback:

- Encode \(\exists\) independent set of size \(t\) as SAT (at-most-one on edges of \(G\), cardinality \(t\)). Kissat / Cadical are faster than a mediocre BnB on some densities.
- CP-SAT maximisation for the *lower* bound \(\alpha\ge\cdot\) (Yu used this to get 18, then BnB to rule out 19).

Do **not** write a GPU BnB for \(n=186\). IPDPS 2025 “Less is More” and 2024 many-core MCS win on *sparse million-vertex* graphs. Our residuals are the opposite: tiny, dense, need strong bounds. CPU bitset + OpenMP is the SOTA for this shape (Yu, Prosser, BBMC).

### 2.2 \(O(n)\) Cayley filters — `engine/kernels/cayley.py`

**Eigenvalues, if ever needed.** Symmetric circulant, flip distance \(d\) (and \(n-d\)):

\[
\lambda_j \;\leftarrow\; \lambda_j \;+\; \sigma\cdot 2\cos\bigl(2\pi j d / n\bigr),
\quad \sigma\in\{+1,-1\}.
\]

Precompute the cosine table once per \(n\). Update in \(O(n)\), maintain running \(\lambda_{\max},\lambda_{\min}\) in the same pass. **Do not call this inside the \(K_4\)-free process.** Keep it for optional post-hoc Hoffman on the shortlist.

**Triangle-free / Schur (job B).** Maintain the convolution \(c = S*S\) as an integer array of length \(n\). Flipping \(d\):

\[
c \;\leftarrow\; c \;+\; \sigma\cdot\bigl(\mathrm{roll}(S,d)+\mathrm{roll}(S,-d)\bigr)
\]

plus the \(2d\) diagonal term, all \(O(n)\). Triangle exists iff \(c[s]>0\) for some \(s\in S\setminus\{0\}\). Incremental check of the *new* distance only is \(O(\lvert S\rvert)\): scan \(x\in S\) and test \(d-x\in S\) (bitset).

**\(K_4\)-free (job A).** Circulant is \(K_4\)-free \(\Leftrightarrow\) \(G[N(0)]\) is triangle-free \(\Leftrightarrow\) the set \(S\) induces no triangle. Adding \(d\):

- \(N_S(d)=\{x\in S: d-x\in S\}\)  (`AND` of bitset \(S\) with `roll(S, d)`), \(O(n/64)\).
- Accept iff \(N_S(d)\) is independent in \(G[S]\): for all \(x,y\in N_S(d)\), \(y-x\notin S\). Bitset: for each \(x\in N_S(d)\), `(N_S(d) AND roll(S, x)) == 0`.

That is Yu’s “restricted cyclic \(K_4\)-free process” in \(O(d\cdot n/64)\) per candidate, not \(O(d^3)\).

Store \(S\) as:

- a `uint64` bitset of length \(\lceil n/64\rceil\) (membership),
- a packed list of the \(\lfloor n/2\rfloor\) *undirected* distances (the true decision variables).

Never rebuild `row_from_bits` by Python loops in the inner loop (`cayley.py:48–56`).

### 2.3 Multiplier orbit — `engine/kernels/sieve.py`

Two circulants with \(T=\lambda S\bmod n\), \(\gcd(\lambda,n)=1\), are isomorphic (multiplier). Canonical key: lex-min of \(\{\lambda S: \lambda\in(\mathbb Z/n)^\times, \lambda\le n/2\}\) packed as a bitset integer (or Zobrist hash + lex bitstring). Dedup before exact cert. Cuts the Yu pool search by \(\sim\varphi(n)/2\).

For prime \(n=p\), \((\mathbb Z/p)^\times\) is cyclic; it is enough to try \(\lambda = g^0,\ldots,g^{(p-3)/2}\).

### 2.4 Tests that lock the certifier

Extend `engine/test_kernels.py`:

- Paley(17): decision \(\alpha\le 3\) on the 8-vertex residual, Russian-doll \(c[i]\).
- C5: triangle-free incremental vs FFT convolution.
- Flip one Paley(17) distance: \(O(n)\) eigenvalue update vs `fft_eigenvalues`.
- Quintic classes mod 251: reproduce Yu’s Table 1 distances \(D_0,\ldots,D_4\) (hardcoded regression).
- Yu’s \(S\) of size 32: `k4_free_via_neighbourhood` true; residual order 186; *decision* \(\alpha\le 19\) (this is the integration test — allow a few seconds).
- Multiplier: \(S\) and \(116S\bmod 251\) hash equal.

Until the Yu \(S\) certifies in this repo, do not run a 2000-step ILS on the A40.

---

## 3. Job A — Yu-pool \(R(4,t)\) (highest leverage)

New job `4a` / rewrite `3b`. This is the only job with a realistic shot at \(R(4,21)\) or beating 252.

### 3.1 Search space (algebra, not ML)

For each prime \(p\in[200,400]\) (extend to 521 if A40 is idle):

1. Factor \(p-1\). Keep indices \(e\in\{4,5,8,10\}\) that divide \(p-1\).
2. Require \(-1\in H=(\mathbb F_p^\times)^{(p-1)/e}\) so each cyclotomic class folds to an undirected distance set \(D_r\) of size \((p-1)/(2e)\). (Yu: \(e=5\), \(p=251\), \(\lvert D_r\rvert=25\).)
3. For each pair \(\{D_r,D_s\}\) (10 pairs when \(e=5\)), form the pool \(P=D_r\cup D_s\), \(\lvert P\rvert\sim 50\).
4. Pre-filter pairs: a pair is *viable* if it admits a \(K_4\)-free subset of size \(\ge \tau(p)\) with \(\tau(p)\approx 0.12\,p\) (Yu: 31 out of 50). Probe with 32 random restricted-process runs; drop dead pairs (Yu dropped 5 of 10).

Decision variables: a subset \(S\subset P\), \(\lvert S\rvert\in[k_{\min},k_{\max}]\), \(S=-S\) automatic because each \(D_r\) is folded. For \(p=251\), Yu used \(31\le k\le 38\). That is \(\binom{50}{32}\approx 4.7\cdot 10^{13}\) — not enumerable. Generation is a **process**, not a mask sweep.

### 3.2 Generator: restricted \(K_4\)-free process + annealing (Yu §3)

CP / statistical-physics, not PPO.

**Phase 1 — process (Rödl nibble / triangle-free process analogue).**  
Start from \(S=\emptyset\). Repeatedly add a uniform unused \(d\in P\) such that \(G[S\cup\{\pm d\}]\) stays triangle-free (the \(O(n/64)\) test of §2.2). Stop when no legal add remains. This is the cyclic analogue of the Bohman–Keevash triangle-free process, restricted to a 50-element ground set (so it is cheap).

**Phase 2 — simulated annealing inside the same pool.**  
Neighbourhood: flip / swap one pool distance, reject if \(K_4\) appears. Objective for the annealer is **not** Hoffman:

\[
f(S) = \begin{cases}
\infty & \text{if not }K_4\text{-free},\\
-\lvert S\rvert + \lambda\cdot \widehat\alpha_{\mathrm{greedy}}(G[N^c(0)]) & \text{otherwise}.
\end{cases}
\]

Greedy \(\alpha\) on the residual is \(O(n)\) (smallest-last or max-degree-in-complement). \(\lambda\approx 2\). Dense \(K_4\)-free \(\Rightarrow\) small residual \(\Rightarrow\) small \(\alpha\), which is exactly Yu’s density bet.

**Phase 3 — tabu / breakout (Exoo 1998, BLS).**  
Tabu list = recently flipped distances (length \(1\)–\(3\cdot\lvert P\rvert\)), not whole graphs. After a plateau of \(L\) steps, breakout: drop \(b\) random distances and re-grow with the process (Benlic–Hao breakout local search). Exoo’s “union/disunion of one part of a partition” is the same move in disguise.

**Phase 4 — shortlist.**  
Keep the Pareto front: \(K_4\)-free, \(\lvert S\rvert\) large, greedy \(\alpha\) small, distinct under multipliers. Budget: \(10^4\)–\(10^5\) process+anneal runs per \((p,\text{pair})\), batched.

### 3.3 GPU role (honest)

The BnB certifier is CPU. GPU earns its rent on **batched filters**:

- \(10^5\) candidate bitsets of length 251 fit in a few MB.
- One CUDA kernel: for each candidate, compute \(N_S(d)\) via batched 256-bit `AND`/`OR` (four `uint64`), reject \(K_4\).
- Second kernel: greedy \(\alpha\) (32 independent sequential greedy walks per graph, warp-shuffle reductions).
- Do **not** FFT \(10^5\) rows. Do **not** launch a GPU MCS tree.

A40 occupancy: one grid of candidates, 256 threads/block, bitset in registers / shared. This is a LeetCode “bit DP / bitset convolution” kernel, not a GNN.

### 3.4 Certification (the actual theorem)

For each shortlisted \(S\):

1. Inspect \(G[N(0)]\) (degree \(\sim 64\)): triangle-free \(\Rightarrow \omega\le 3\). Exact MCS on 64 vertices is milliseconds (`_mcs_small` already works).
2. Residual \(R=G[N^c(0)]\), \(n_R=p-1-\deg\). **Decision:** no independent set of size \(t\) (i.e. clique of size \(t\) in \(\bar R\)). Target \(t\) from the survey gap: for \(p=251\), Yu used \(t=19\) so \(R(4,20)\ge 252\). For \(p=241\) (old \(R(4,21)\ge 242\)), try \(t=20\).
3. Reductions before BnB (PMC / KaMIS / unconfined / folding). Circulant residuals may not shrink much; still peel dominated vertices.
4. Östergård \(c[i]\) + bitset MCS + matching colour. Flatten depth \(\le 2\) across CPU threads.
5. Independent checker: dump `S` as a sorted list, recompute \(\omega,\alpha\) in a second implementation (bitset vs SAT). Yu-style: CP-SAT for a *lower* bound on \(\alpha\), BnB for the *upper*.

### 3.5 Meet-in-the-middle and Gray codes (what *not* to do, and when)

- \(\lvert P\rvert=50\), \(k=32\): MITM \(\binom{25}{16}^2\) is still huge. **Don’t.**
- Gray-code enumeration of all \(2^{25}\) free bits: \(3\cdot 10^7\), feasible *if* the pair were 25 undirected distances, not 50. For \(e=4\), \(\lvert D_r\rvert=(p-1)/8\); at \(p=313\) quartic residues, one class is already the *whole* connection set of the \(R(4,22)\ge 314\) graph (Lindsay–Cain). Enumerate 2-class *subsets* only when \(\lvert P\rvert\le 40\) *and* \(k\) is extreme; otherwise the process is the right generator.
- When \(\lvert P\rvert\le 28\) (small \(e\) or smaller \(p\)), Gray-code the subsets of size \(k\) with combinadic rank / revolving-door (Knuth TAOCP 7.2.1.3, CP staple). Incremental \(K_4\) test is \(O(n/64)\) per Gray step.

### 3.6 Target list (concrete)

| \(p\) | why | hope |
|---|---|---|
| 251 | Yu’s graph; regression + search *other* pairs / sizes 33–38 | \(R(4,19)\ge 252\) or denser \(\alpha\le 18\) |
| 241 | Su–Luo–Zhang–Li \(R(4,21)\ge 242\) is the weak cell vs 314 | \(\omega\le 3,\alpha\le 20\) |
| 269, 271, 277, 281, 283 | next primes, mixed \(e\mid p-1\) | \(R(4,21)\) / \(R(4,22)\) |
| 313 | quartic-residue baseline \(R(4,22)\ge 314\); subsets of two octic classes | long shot |
| 337, 349, 353, 373, 397 | \(e=4,5\) when they divide | fill \(R(4,23)\)–\(R(4,25)\) gaps |

Do not waste the A40 on \(p>520\) until 241/251/269 have exact certificates.

---

## 4. Job B — circulant \(R(3,t)\) (second leverage)

Rewrite `2c`. Coniglio–Ljubić–Furini–Traversi–Thürauf–San Segundo (Optimization Online, 19 Aug 2026) already IP-searched this space to \(n=410\) and moved 25 cells. A me-too Hoffman ILS will not beat Gurobi+cuts. Two remaining angles:

### 4.1 Where IP is weak, CP is strong

- **Larger \(n\)** than 410, if we only need *heuristics + exact cert of a shortlist*, not a proof of circulant-Ramsey optimality. Survey cells \(R(3,t)\) for \(t\ge 50\) are still open to +1 constructions.
- **Non-prime \(n\)** (IP paper emphasises structure; composite moduli have smaller multiplier groups and more Schur triples — sometimes *better* \(\alpha\) at the same triangle-free density, cf. quadratic residues only when \(n\) prime).
- **Block-circulant / polycirculant** (Exoo, Mathon, McKinley / Steven-VO): 2-orbit on \(2m\) vertices is still \(O(m)\) bits. Job 3A materialises the matrix; keep two rows and use VT on the *group* \(\mathbb Z_m\rtimes\mathbb Z_2\) (two neighbourhood types). Exact cert: \(\omega=1+\max_i\omega(G[N(v_i)])\) over orbit representatives (usually 2).

### 4.2 Algorithm

1. **Ground set:** undirected distances \(1,\ldots,\lfloor n/2\rfloor\). Triangle-free \(\Leftrightarrow\) \(S\) is sum-free in \(\mathbb Z/n\mathbb Z\) (Schur). Maintain the \(O(n)\) convolution of §2.2.
2. **Constructor:** odd-order “middle third” \(\{\lceil n/3\rceil,\ldots,\lfloor n/2\rfloor\}\) is the classical maximum sum-free set in \(\mathbb Z/n\) (Yap / Diananda–Yap; Tao–Vu inverse theorems: large sum-free sets are subgroups or progressions). Seed ILS from that, from random, and from Paley when \(n\equiv 1\pmod 4\).
3. **Moves:** flip one distance; reject if a Schur triple appears (\(O(\lvert S\rvert)\) bitset). Tabu the distance. Objective: greedy \(\alpha\) of \(G\), then exact decision \(\alpha\le t-1\).
4. **Exact cert:** VT \(\alpha(G)=1+\alpha(G[N^c(0)])\). Residual size \(n-1-2\lvert S\rvert\). For triangle-free circulants aiming at \(R(3,30)\), residual is the bottleneck — same MCS as Job A.
5. **Do not compete with the IP paper on \(24\le t\le 49\)** unless we have a *different* graph. First recertify their certificates (GitHub `fabiofurini/ramsey-number-lower-bounds`) as a checker test, then hunt \(t\ge 50\) or polycirculant.

### 4.3 Additive-combinatorics filters (Tao / Green–Ruzsa / MathOverflow)

- If \(\lvert S+S\rvert\) is tiny, Freiman says \(S\) is a progression: \(\alpha\) will be huge. Discard (compute \(\lvert S+S\rvert\) from the same convolution).
- 3-AP-free is *stronger* than sum-free and the wrong constraint (Behrend sets are small). Do not import Behrend into \(R(3,t)\).
- Sidon / Golomb rulers: already job 1D; they are too sparse for \(R(3,t)\).

---

## 5. Job C — polarity exact \(\alpha\) (third leverage)

Mattheus–Verstraete (Annals 2024) prove \(r(4,t)=\Omega(t^3/\log^4 t)\) by *counting* independent sets in a \(K_4\)-deleted polarity graph. A finite bound needs \(\omega\le 3\) and a hard \(\alpha\le t-1\).

### 5.1 What to compute

- Raw \(W(3,q)\) collinearity: already `polarity_gq`. Hoffman on it is not \(R(4,t)\).
- **Delete \(K_4\)s:** either take a unital-derived subgraph \(G_q^\ast\) (paper) or a random induced subgraph that is \(K_4\)-free (their sampling idea). For small \(q\) the whole graph may already have small \(\omega\); check exactly.
- Orders: \(q=2\) (\(N=15\), toy), \(3\) (\(40\)), \(4\) (\(85\)), \(5\) (\(156\)), \(7\) (\(400\)), \(8\) (\(585\)). Exact \(\alpha\) at \(q=5\) (\(N=156\)) is in MCS range after VT if the graph is vertex-transitive; GQ polarity is not always VT in the same way as Paley — fall back to full MCS / KaMIS reductions / SAT.
- **Do not** scale to \(q=16\) (\(N=4369\)) expecting exact \(\alpha\). Spectral only.

### 5.2 GPU

Building the polarity graph is GEMM of homogeneous coordinates — already the 1C kernel. Batch many random \(K_4\)-free samples (delete a random vertex subset, then greedily delete vertices of remaining \(K_4\)s). Exact \(\alpha\) per sample is CPU.

---

## 6. Technique map (survey → code)

Compressed so the implementation checklist is one page.

### 6.1 \(O(n)\) / \(O(n\log n)\) (already half-wired)

| Trick | Source | Use |
|---|---|---|
| Linear sieve | Euler / CP | primes \(p\le 520\) |
| QR = image of \(x\mapsto x^2\) | PE / CP | Paley seeds |
| Circulant spectrum = FFT of row | Davis / Diaconis | post-hoc only |
| \(\lambda_j \pm 2\cos(2\pi jd/n)\) | circulant DFT, rank-1 on the symbol | unused; wire if Hoffman is ever in a loop |
| FWHT Boolean Cayley | Bernasconi–Codenotti | job 3D, not A–C |
| Convolution = triangles | CP FFT trick, already `convolution_bool` | incrementalise |
| VT \(\omega=1+\omega(N(0))\), \(\alpha=1+\alpha(N^c(0))\) | Cayley folklore, Yu 2026 | cert |
| Distance space \(O(n)\) bits | arXiv:2608.18769 IP | search |
| \(S=-S\) \(\Rightarrow\) \(2^{e/2}\) class masks | cyclotomy | 2A; Job A uses *subsets* of two classes instead |
| Batagelj–Zaversnik degeneracy | \(O(n+m)\) | MCS order |
| Combinadic / revolving-door Gray | Knuth 7.2.1.3 | only \(\lvert P\rvert\le 28\) |
| Zobrist hash of bitset \(S\) | chess CP | tabu / seen set |
| Multiplier lex-min | Schur rings / Muzychuk | dedup |
| Word-RAM popcount / blsr / ctz | TopCoder bitset, BBMC | MCS inner loop |
| Bucket queue / 64-bit bitset neighbourhood | LeetCode graph + CP | \(K_4\) filter |
| Meet-in-the-middle | CP knapsack | **skip** at \(\lvert P\rvert=50\) |

### 6.2 Competitive programming / olympiad

| Trick | Where it pays |
|---|---|
| Bitset `N(u) AND N(v)` common neighbours | \(K_4\) / triangle incremental |
| `__builtin_ctzll` iterate bits | MCS candidates, Gray |
| SoS DP / Fast zeta on \(e\le 12\) class masks | 2A already; not Job A subsets |
| Rolling hash of \(S\) | isomorphism + tabu |
| Two-pointers on sorted \(S\) for \(x+y=z\) | Schur check \(O(\lvert S\rvert)\) without FFT |
| Sparse table / prefix XOR | not needed (\(n\le 400\)) |
| Dancing links X | exact cover of a pool; worse than the process |
| Branch and bound with *bitmask DP* on \(n\le 40\) | composite small \(R(3,t)\) exhaustive |
| Parallel independent first-level recursion | Yu OpenMP; `joblib` / OpenMP in Cython |

IMO/Putnam: the only relevant classical fact is the Schur / sum-free characterisation and the Paley clique bound \(\omega\le\sqrt p\). No olympiad construction beats Yu’s pool.

### 6.3 Algorithmic literature (MCP / MIS / ILS)

| Paper | Take |
|---|---|
| Tomita MCS / MCR | pivot + colour bound; we have a 64-bit sketch |
| San Segundo BBMC / BBMCR / BITRDS | bit-parallel colour + Russian dolls |
| Östergård Cliquer 2002 | \(c[i]\) suffix; **must have** |
| Prosser 2012 survey | which solver wins on dense vs sparse |
| MoMC (Li–Quan, MaxSAT bound) | optional second solver on stubborn residuals |
| CliSAT | dense 186-vertex: often beats BnB (arXiv:2512.03419) |
| PMC (Rossi et al.) | k-core kernelization; little help at \(n=186\) dense |
| IPDPS 2025 work-avoidance GPU MCS | skip; wrong instance class |
| Exoo tabu 1998 / EJC R29 | partition-flip on circulants; still SOTA metaheuristic |
| Benlic–Hao BLS | adaptive perturbation after plateau |
| Nagda–Raghavan–Thakurta AlphaEvolve 2026 | evolved *search code*; Yu then beat their \(R(4,20)\ge 237\). Do not train a GNN. Steal their *initialization families* (algebraic bootstrap + triangle-free growth) for job B. |
| KaMIS / redumis | MIS reductions before exact \(\alpha\) |
| Kissat / Cadical | SAT fallback for \(\alpha\ge t\) / \(\alpha<t\) |

### 6.4 ArXiv / 2024–2026 frontier (mapped to jobs)

| Paper | Job | Action |
|---|---|---|
| Yu arXiv:2608.18169 \(R(4,20)\ge 252\) | **A** | Reproduce \(S\), then hunt 241/269/… |
| Coniglio et al. Aug 2026 IP circulants | **B** | Recertify their checker; don’t rerun \(t\le 49\) |
| Ihringer–Mattheus arXiv:2608.21769 \(TG_{d,h}\) | catalogue | After A–C |
| Mattheus–Verstraete Annals 2024 | **C** | Exact \(\alpha\) at small \(q\), not the asymptotic |
| Bradač arXiv:2605.28793 off-diagonal | none | Containers; not enumerable |
| Li FOCS 2023 extractors | none | \(N\) huge, bound in the analysis |
| Campos–Jenssen–Michelen–Sahasrabudhe 2025 \(R(3,k)\) \(c\ge 1/3\); Hefty–Horn–King–Pfender 2025 \(c\ge 1/2\) | none | Triangle-free *process on \(K_n\)*, not circulant. Do not implement the process at survey scale. |
| Kocbek arXiv:2507.09235 geometric CPR | catalogue / C-adjacent | Linear-time \(\alpha\) *approximation* only |
| Yip et al. 2024 Paley-like polynomials | catalogue | Hoffman vs Paley at same order |
| Lindsay–Cain arXiv:1510.06102 \(R(4,22)\ge 314\) | **A** | Baseline quartic residue mod 313 |
| Berghaus–Wagner ICLR 2025 | none | RL loses to random on \(R(4,4)\) |

Erdős #78 is unchanged. Li \((\log N)^C\) is not an A40 MCS target. Polymath/Tao on sum-free sets inform the *seed* for job B, not a new family.

### 6.5 Cursor / Grok stack (what to actually use)

- **Cython or numba** on the MCS inner loop and the \(K_4\) bitset filter. Pure numpy Python `for` in `k4_free_via_neighbourhood` is the present bottleneck.
- **OpenMP** (Yu) for depth-2 flattening; `joblib` as the portable fallback on RunPod.
- **CUDA**: one batched bitset-filter kernel, optional. Not required for the first bound.
- **OR-Tools CP-SAT** (already the Yu lower-bound tool) for \(\alpha\) maximisation on the residual. Optional Kissat via stdin DIMACS.
- **Independent checker** in a second language (the IP paper’s lesson; AlphaEvolve verification repos). A 50-line bitset MCS in C is enough.
- **Do not**: PyG, PPO, GAT, full eigendecomposition, `networkx.graph_clique_number`, Gurobi (no license on the pod).

---

## 7. Implementation order

Ship in this order. Each step is a kernel test + a job that can run on the A40 without the next step.

1. **MCS decision + Russian dolls + bitset colour**, \(n\le 256\). Test: Paley(17), then Yu’s published \(S\) on 251 (\(\alpha=19\) in seconds).
2. **\(O(n/64)\) incremental \(K_4\) / Schur filters** + stop calling FFT inside ILS.
3. **Multiplier canonicalisation + Zobrist tabu.**
4. **Job `4a`:** cyclotomic 2-class pools, restricted process, anneal, shortlist, exact cert. Hardcode Yu’s \(D_r\) and \(S\) as a regression. Then search \(p=241,251,269\).
5. **Job `4b`:** sum-free ILS with greedy-\(\alpha\) objective, exact residual decision, polycirculant 2-orbit. Recertify Furini certificates. Hunt \(t\ge 50\).
6. **Job `4c`:** GQ \(q\le 7\) exact \(\alpha\) after \(K_4\)-clean. Only then \(q=8,9\).
7. Catalogue only after a survey cell moves, or if A–C are exhausted: \(TG_{d,h}\), polynomial Paley-like.

RunPod: one pod, `RAMSEY_JOB=4a`, `nohup` / tmux. MCS is CPU-heavy; an A40 is still useful for batched filters and for not killing the process. A 16-vCPU CPU pod would certify faster per dollar than an A40 if CUDA filters are not yet written — write the CPU path first.

### Success criteria

- **Repro:** Yu \(S\) certifies \(\omega=3,\alpha=19\) in this repo.
- **Move:** any of \(R(4,21)>242\), \(R(4,20)>252\), \(R(4,23)\) / \(R(4,24)\) gap, or \(R(3,t)\) for some \(t\ge 50\) not in the IP paper, with a dumped connection set and a second-implementation checker.
- **Non-goals:** larger Paley, better Hoffman \(N^{1/k}\), GNN, extractor graphs, Bradač products.

### Explicit non-work

- Training PPO / GAT (Berghaus–Wagner).
- GPU MCS trees for \(n=186\).
- Enumerating \(2^{50}\) pool subsets.
- Hoffman inside the inner loop.
- Cyclotomic *class unions* beyond 2A (already running; 3A may perturb winners, it will not beat a pool subset).
- ANF \(n=16\) as a bound (spectral underestimation).
