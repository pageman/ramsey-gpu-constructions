# Where to look (after this campaign’s “where not to look”)

Retrieved **30 Aug 2026**. Filter: a **finite** Radziszowski DS1 +1, A40-class
hardware, residual decision of width \(\le 256\) (or a declared wider kernel).
Not Erdős #78, not \(C\ge 1.01\), not Hoffman \(N^{1/k}\).

This note is the campaign’s negative experimental theorem turned into a
**search map**. Part 1 is the literature deep dive (what actually minted a
finite cell, 2015–2026). Part 2 is an arXiv retrieval pass restricted to the
surviving aisles: current / SOTA / frontier on *those* objects, not every
PDF with “Ramsey” in the title.

Machine-readable query log and paper verdicts:
[`arxiv-rag/where-to-look-corpus.json`](arxiv-rag/where-to-look-corpus.json).

---

## 0. Baseline: where this tree already looked and failed

| Job | What was tried | Negative theorem |
|---|---|---|
| 2a | Whole cyclotomic class-unions, \(p\le 9973\), Hoffman score, 9288 rows, 28 h | No survey cell. Paley exact \(\omega\) in range is Shearer / Exoo. |
| 3a | Block-circulant ILS, Hoffman-scored | Wrong objective; never a residual accept. |
| 3b | Unrestricted circulant ILS, Hoffman(\(G\))+Hoffman(\(\overline G\)) | Never recovered Yu’s published \(S\). Every Paley-like mask looks the same. |
| 3c | GQ \(q=11,13\) exact MCS | Leftover too big; Hoffman only. |
| 4a | Yu-pool hunt, 256-word kernel | Silent accept on residual 262/264. Void `CELL?` \(R(4,20)\ge 354\). |
| 4b / 5d | Empty-mask \(R(3,t)\) ILS | No graphs. Coniglio already owns 24–49. |
| 4c / 5e | Polarity leftover \(W(3,7)\) | Exact \(R(4,22)>84\) vs published \(\ge 314\). Below the floor. |
| 5a | Yu residual 186, one backend (`c-decide`) | GREEN: no 19-IS, \(2.16\times 10^8\) nodes, 63 s. Recertify, not a +1. |
| 5c | 64 walks, \(p\in[200,400]\) | Greedy \(\alpha\) 24–40. No real `CELL?`. Cheap walks on those pools are saturated. |
| 5f | \(TG_{d,h}\) / Yip vs Paley | Paley wins same-\(n\) Hoffman. Catalogue. |

The number that is still true is **252**. The place it can increment is a
**new connection set \(S\)** plus a **finished accept**, not a new GPU kernel
and not another Hoffman night.

---

## 1. Literature deep dive — the field’s actual +1 machines

Every recent **finite** cell that moved used one of a small set of
instruments. The family list is secondary. The instrument is the paper.

### 1.0 Instruments that minted a published +1 (2015–2026)

| Instrument | What moved | Papers / artifacts |
|---|---|---|
| Sparse **subset of two cyclotomic classes** + residual bitset BnB | \(R(4,20)\ge 252\), same graph \(\Rightarrow R(4,21)\ge 252\) | Yu [2608.18169](https://arxiv.org/abs/2608.18169) v2 |
| **Full** quartic-residue circulant on a convenient prime | \(R(4,22)\ge 314\), \(R(4,25)\ge 458\) | Lindsay–Cain [1510.06102](https://arxiv.org/abs/1510.06102); DS1 r18 |
| Full cubic-residue circulant | \(R(4,21)\ge 242\) (now obsolete vs Yu’s 252) | Su–Luo–Zhang–Li 1999 (survey); Yu cites the 241-vertex 60-regular witness |
| Distance-space IP, \(O(n)\) binaries, B&C + exact clique separation | 25 values of \(R(3,n)\) for \(24\le n\le 49\), \(n\neq 27\); eight exact \(R_C(3,n)\) | Coniglio–Furini–Ljubić–San Segundo–Thürauf–Traversi [2608.18769](https://arxiv.org/abs/2608.18769); [github.com/fabiofurini/ramsey-number-lower-bounds](https://github.com/fabiofurini/ramsey-number-lower-bounds) |
| Paley / cubic / QR **seeds** + local search (not Hoffman) | AlphaEvolve \(R(4,20)\ge 237\) (obsolete); several smaller \(R(4,t)\) +1s | Nagda–Raghavan–Thakurta [2603.09172](https://arxiv.org/abs/2603.09172) |
| Paley / cubic **modifications** (not whole-class unions) | Several DS1 cells marked [ExT] | Exoo–Tatarevic 2015; Tatarevic; Kuznetsov distance graphs |
| 2-polycirculant / block-circulant enumeration + tabu / SAT | Books, wheels, \(K_k-e\); **not** classical \(R(4,t)\) | Lidický–McKinley–Pfender–Van Overberghe [2407.07285](https://arxiv.org/abs/2407.07285); Wesley [2410.03625](https://arxiv.org/abs/2410.03625), [2509.03784](https://arxiv.org/abs/2509.03784); Goedgebeur–Van Overberghe [2107.04460](https://arxiv.org/abs/2107.04460) |
| Exact clique/MIS **routing** by instance space | Which referee to call on a 186–280 residual | ISA [2512.03419](https://arxiv.org/abs/2512.03419); CliSAT (San Segundo et al., EJOR 2023); MOMC; LearnAndReduce / KaMIS [2412.14198](https://arxiv.org/abs/2412.14198) |

Algebraic/asymptotic papers that **do not** mint 253 at this scale are
catalogued in §1.7 and §2.6. They are real theorems. They are the wrong
aisle for a DS1 +1 on an A40.

### 1.1 Look 1 — A *new* 2-class \(S\) whose residual the referee can finish

**This is the only 2026 method that moved \(R(4,20)\).** Yu is not
“cyclotomic + Hoffman”. It is: pick a prime, take two undirected cyclotomic
classes, walk a **sparse subset** until \(N(0)\) is triangle-free and
\(|S|\) is large enough that the residual fits a bitset kernel, then
**decide** \(\alpha(G[N^c(0)])<t-1\) and close the mixed-set hole.

Search space (not “more primes”):

- \(p\) prime, \(e\in\{4,5\}\) (quartic / quintic), \(-1\in\langle g^e\rangle\)
- pool \(= D_i\cup D_j\), \(|S|\) large enough that \(p-1-2|S|\le\) kernel width
- \(N(0)\) triangle-free; greedy \(\alpha<t\); lex-min orbit
- decision \(\alpha(G[N^c(0)])<t-1\) **and** mixed-set close before `CELL?`

**Already looked in this tree:** \(p\in[200,400]\), 64 walks, greedy killed
almost every \(S\). Remaining volume is not “more walks on the same pools.”

| Remaining volume | Why it is still open | Gate |
|---|---|---|
| Higher \(\lvert S\rvert\) at \(p=251\) | Residual \(<186\). \(\alpha\le 18\) on the residual is still 252 unless the *full* graph has \(\alpha\le 18\) | Yu already has \(\alpha=19\). A denser \(S\) at 251 is a \((4,19)\)-hope, not a 253. |
| Other \((i,j)\) at 251 | Yu published \(D_0\cup D_2\) (and the isomorphic \(D_0\cup D_3\)). Other pairs exist | Same residual-width + mixed-set contract |
| Next primes after 251 with residual \(\le 256\) | Need \(2\lvert S\rvert\ge p-1-256\). At \(p=337\), \(\lvert S\rvert\ge 40\); 4a’s 262 residual was \(\lvert S\rvert\) too small | Do not call the 256-word entry |
| \(t\) other than 20 | Yu: \(R(4,21)\) was the weak cell (242 vs 314). Same graph gives 252 for 20 and 21. Next weak strip vs \(R(4,22)\ge 314\): \(R(4,23)\)–\(R(4,25)\) | Refresh `R4_LOWER` from DS1 r18 + Yu + Lindsay–Cain before picking \(t\) |

**Lindsay–Cain (2015) is the ancestor, not a competitor.** They used *full*
quartic (and higher) residue classes on primes \(\le 500\): \(R(4,22)>313\)
in 7 hours, \(R(4,25)>457\) in ~10 days, and they already *tried* quintic
and 6th–8th power residues. Quintic mod 71 gave a respectable \(R(3,15)\)
bound; it did not mint a new \(R(4,t)\) cell. Yu’s increment is the
**32-subset of a 50-set 2-class pool**, not another full class. That is
why 2a (whole-class unions) and 5c (cheap walks) are different failures.

**AlphaEvolve [2603.09172] is a seed library, not a night objective.**
The working-paper table claims several small-cell +1s
(\(R(3,13)\ge 61\), \(R(3,18)\ge 100\), \(R(4,13)\ge 139\), …) and
\(R(4,20)\ge 237\). Yu already beat 237. Their four initialization
families (circulant difference-set, cubic residue, Paley/QR, tabu SA
with look-ahead) are the right *generators* to port into a Yu-class
walk. Evolving Python on the pod is not a kernel.

SOTA pointer: Yu v2 HTML, §§2–5 (process + OpenMP flatten + CP-SAT
lower bound). DS1 revision #18 (24 Apr 2026) is the table you must beat;
Yu is the 17 Aug 2026 delta.

### 1.2 Look 2 — Distance-space IP for \(R(3,t)\), \(t\ge 50\) only

Coniglio et al. **own** \(24\le n\le 49\) except \(n=27\), on circulants
up to 410 vertices, with a stand-alone clique checker and GitHub
certificates. Looking there is a duplicate paper.

**Where to look:** \(t\ge 50\), **nonempty** Schur seed (middle-third or
a known cyclic \(R(3,k)\) witness), incremental Schur \(O(|S|)\), residual
\(\le\) width. Their model — projected distance space, coefficient
reduction, circulant neighbourhood separation — is the SOTA *search*
for this family. Empty-mask ILS (4b/5d) is the method they replaced.

Older cyclic lore that is still a **seed**, not a ranker:

- Harborth–Krause: no cyclic improvement below \(n=102\) except possibly
  \(R(3,k)\) for large \(k\). Do not look below that for 1-circulant miracles.
- Exoo–Tatarevic / Tatarevic / Kuznetsov / Ji–Li–Liu–Xu: cyclic and
  distance-graph table lore in DS1. Seeds for \(t\ge 50\).
- Rowley [2203.13476](https://arxiv.org/abs/2203.13476): SAT-found
  *template graphs* that compound into larger cyclic colourings. The
  template idea is the Schur-seed analogue for multicolour; for
  two-colour \(R(3,t)\) it is “start from a known cyclic witness, do
  not start from \(\emptyset\).”

SOTA pointer: [2608.18769](https://arxiv.org/abs/2608.18769);
CPLEX package + certificates on GitHub. Reuse their **checker**. Do
not rerun their \(n\le 49\) table.

### 1.3 Look 3 — Referee upgrades (not new graphs)

The campaign proved the hunt is idle without a Yu-class prune. Look
here before another 5c night.

| Residual regime | Call | Why the literature says so |
|---|---|---|
| Sparse, \(n\sim 186\), target 19 | Yu OpenMP / BBMC / matching colour / flatten 2 levels | Only 1.4 s proof in the literature; our `c-decide` took 63 s / \(2.16\times 10^8\) nodes |
| Same, second backend | CP-SAT decision (job 6a); Cliquer on the **complement** | Yu used SAT for the 18-set only. Timeout \(\neq\) proof |
| Denser leftover | CliSAT / MOMC | ISA [2512.03419](https://arxiv.org/abs/2512.03419): CliSAT wins dense clique-y graphs (~11% of their space); MOMC wins ~75% of their (mostly sparse/ML) space; Gurobi MIP ~14% |
| Sparse leftover after kernelization | KaMIS `branch_reduce`; LearnAndReduce [2412.14198](https://arxiv.org/abs/2412.14198) | GNN here is a **filter on which reduction rules to try**, not PPO edge-flip |
| Width 262–264 | **Widen WORDS and timeout≠accept**, or raise \(\lvert S\rvert\) | Do not call the 256-word entry. This is how 354 was born |

Do **not** look at IPDPS GPU MCS trees for this instance class (ISA:
wrong regime). Do **not** look at GNN branching as week-one work.
Gao et al. [2412.07685](https://arxiv.org/abs/2412.07685) auto-discovers
branching rules with exponent \(O(1.044^n)\) on **3-regular** graphs.
A Yu residual is not 3-regular; do not expect that exponent.

SAT modulo symmetries (Kirchweger–Szeider, ToCL 2024; Wesley’s
enumeration of book-critical graphs) enumerates *all* \((3,5)\)- and
\((4,4)\)-graphs. That is a completeness tool at \(n\le 17\), not a
search tool at \(n\sim 250\).

### 1.4 Look 4 — 2-polycirculant / two-orbit, only if residual \(\le\) width

Lidický–McKinley–Pfender–Van Overberghe and Wesley show 2-polycirculants
still find finite cells when 1-circulants saturate. For classical
\(R(4,t)\) this is **untested in this tree** (3a was Hoffman-scored).

Look: two orbits, triangle-free neighbourhoods, **decision \(\alpha\)**
on each leftover, same certificate contract. SAT encodings of
block-circulants (Wesley 2024/2025/2026) are SOTA for *small*
book/wheel/\(K_k-e\) cells. At \(n\sim 250\) they are a second search
generator, not a replacement for the residual referee.

Goedgebeur–Van Overberghe [2107.04460](https://arxiv.org/abs/2107.04460)
already enumerated circulant and block-circulant Ramsey graphs for
\(K_n\), \(K_n-e\), wheels, bipartites. They report **no improvement
on classical \(R(s,t)\)** inside 1-circulants, agreeing with
Harborth–Krause. That is why Look 4 is *two* orbits, and only after
Look 1 saturates.

Code to steal, not rerun: [gwen-mckinley/ramsey-books-wheels](https://github.com/gwen-mckinley/ramsey-books-wheels)
(tabu + polycirculant graph6); Steven-VO circulant enumerator (cited
from 2107.04460).

### 1.5 Look 5 — Finite polarity leftover **above the floor**

Mattheus–Verstraete [2306.04007](https://arxiv.org/abs/2306.04007)
(\(r(4,t)=\Omega(t^3/\log^4 t)\), Annals 2024) is asymptotic: random
bipartition of unital cliques + containers. The finite cousin is:
build \(W(3,q)\) / Hermitian polarity, delete a hitting set of \(K_4\)s,
leftover \(H\) with \(\omega\le 3\), exact \(\alpha(H)\), emit only if
\(N+1\) beats published \(R(4,\alpha+1)\).

5e at \(q=7\) gave \(R(4,22)>84\) vs 314. Look: **larger \(q\) only
after a leftover-size gate** (\(\le 256\)) **and** a floor gate. Raw
Hoffman on the polarity graph stays catalogue.

Ihringer–Mattheus [2608.21769](https://arxiv.org/abs/2608.21769)
(\(TG_{d,h}\), \(R(33,t)\ge t^{2.1-o(1)}\)) is the first explicit
\(R(s,t)\ge t^{c}\) for fixed \(s\) with \(c>2\). Job 5f already
compared it to Paley. It will not beat Paley(17) on exact small \(n\).

Dai–Lin [2606.07214](https://arxiv.org/abs/2606.07214) construct new
strongly regular graphs for **book** Ramsey numbers. Same algebraic
aisle as Paley-for-books (Rousseau–Sheehan). Not a classical \(R(4,t)\)
machine.

### 1.6 Look 6 — SAT / IP on the *connection set*, not on \(K_n\)

A second retrieval finding: the 2025–2026 SAT papers that actually
produce graphs do not encode “exists a \((4,20)\)-graph on 251
vertices.” They encode a **structured colouring** (circulant,
block-circulant, Cayley, ordered, dihedral) whose variable count is
linear in \(n\) or in \(\lvert S\rvert\).

| Paper | Encoding | Scale that worked | Use here |
|---|---|---|---|
| Coniglio et al. 2608.18769 | Distance-space IP, \(O(n)\) binaries | \(n\le 410\), \(R(3,n)\) | Look 2 generator |
| Wesley 2410.03625 / 2509.03784 | SAT + IP on block-circulant \(S_c\) | Books, small multicolour | Look 4 generator |
| Bašić–Damnjanović–Stevanović–Stošić 2604.16188 | Kissat on ordered / cyclic | Small ordered \(R_{\mathrm{ord}}\) | Seed encoding; \(n\) is tiny |
| Damnjanović–Đorđević 2607.06817 | Reflective / dihedral permutational | Small | Catalogue of symmetry, not a 251-vertex hunt |
| Rowley 2203.13476 | SAT clauses for linear/cyclic templates | Multicolour compounds | Template-seed idea |

If 5c’s random walks stay greedy-dead, the next generator is
**Coniglio’s IP or Wesley’s SAT on a Yu pool**, with our residual
referee as the accept. It is not SMS on the full edge set of \(K_{251}\).

### 1.7 Do not look (literature agrees with the campaign)

| Place | Why the literature + this tree agree |
|---|---|
| Full cyclotomic class unions + Hoffman | 2a; Shearer/Exoo already own exact Paley \(\omega\) in range; Lindsay–Cain already swept full higher-power residues \(\le 500\) |
| AlphaEvolve / PPO / GAT as the night | 2603.09172 lost to Yu on \(R(4,20)\); Berghaus–Wagner RL loses to random on \(R(4,4)\) |
| \(TG_{d,h}\), polynomial Paley (Yip), more Paley | 2608.21769 is explicit **asymptotic**; 5f: Paley wins same-\(n\) \(C\) |
| Extractors, Bradač products, \(C=N^{1/k}\) | Different theorems; no adjacency to certify at A40 \(N\) |
| Coniglio range \(R(3,24)\)–49 | They shipped certificates |
| GQ \(q=11,13\) exact MCS | Leftover too big; 3c already Hoffman |
| SMS full-graph generation | Kirchweger–Szeider: \(R(3,5)\), \(R(4,4)\). Completeness at \(n\le 17\) |
| Tatarevic increment [2608.06531](https://arxiv.org/abs/2608.06531) | \(R(k+1,s+1)\ge R(k,s)+2k+2s\), Lean 4, \(R(12,12)\ge 1641\). Real theorem. \(n\sim 1640\), no residual-width story. Wrong scale |
| Two-bite / sphere-graph \(R(3,k)\) and \(r(\ell,C\ell)\) | Hefty–Horn–King–Pfender [2510.19718](https://arxiv.org/abs/2510.19718) \(\tfrac12+o(1)\); Campos–Jenssen–Michelen–Sahasrabudhe [2505.13371](https://arxiv.org/abs/2505.13371) \(\tfrac13+o(1)\); Ma–Shen–Xie [2507.12926](https://arxiv.org/abs/2507.12926) exponential off-diagonal. Asymptotic. No graph to enumerate at \(n\sim 250\) |
| Ordered / canonical / online / hypergraph / book-exact | 2604.16188, 2511.04364, 2608.27405, 2606.24198, 2606.07214. Different numbers |

---

## 2. ArXiv RAG — current / SOTA / frontier on the look-heres

Protocol (30 Aug 2026):

1. Take the Look 1–6 objects from §1 as the **query filter**.
2. Query `export.arxiv.org/api` by id and by boolean phrase, newest first.
3. Keep a paper iff it (a) moved a finite DS1-style cell, (b) is the
   current method for generating or deciding one of those cells, or
   (c) is a tempting wrong aisle that a later agent will otherwise
   re-open.
4. “Frontier” = the paper that last moved the object. “SOTA” = the
   method you would run tomorrow. “Bleeding-edge” = newest method
   that is not yet a cell machine. “Current” = still-used ancestor.

Full query strings and hit lists live in the corpus JSON. Narrative
verdicts below.

### 2.1 Finite \(R(4,t)\) constructions (Look 1) — frontier is Yu

| Status | Paper | Claim | Verdict |
|---|---|---|---|
| **Frontier** | Yu [2608.18169](https://arxiv.org/abs/2608.18169) v2, 17 Aug 2026 | Circulant \(p=251\), \(\lvert S\rvert=32\subset D_0\cup D_2\), \(\omega=3\), \(\alpha=19\), residual 186 decided by bitset BnB | The object. Process + OpenMP flatten + CP-SAT LB. Explicitly says \(R(4,21)\) was the weak survey cell vs \(R(4,22)\ge 314\) |
| **Obsolete bound, live seed lore** | Nagda–Raghavan–Thakurta [2603.09172](https://arxiv.org/abs/2603.09172) | AlphaEvolve: \(R(4,20)\ge 237\); several smaller +1s; four init families | Use the **algorithms**, not the 237. Do not wrap an LLM loop on the pod |
| **Current ancestor** | Lindsay–Cain [1510.06102](https://arxiv.org/abs/1510.06102), 2015 | Full quartic residues: \(R(4,22)>313\), \(R(4,25)>457\); higher-power sweep \(\le 500\) verts | The analogy Yu cites. Other residue *indices* at primes near 313 only if residual \(\le\) width after a large \(S\) |
| **Current table** | Radziszowski DS1 r18, 24 Apr 2026 | The numbers you must beat | Refresh `R4_LOWER` from this + Yu before any \(p=353\) hunt |
| **Current small-cell lore** | Exoo–Tatarevic 2015; Tatarevic; Kuznetsov | Paley(101) / cubic(127) modifications; distance graphs | Seeds. Not Hoffman rankers |

No 2026 arXiv hit other than Yu claims a new classical \(R(4,t)\)
circulant cell. That is the retrieval result, not a taste judgment.

### 2.2 Finite \(R(3,t)\) constructions (Look 2) — frontier is Coniglio for \(n\le 49\)

| Status | Paper | Claim | Verdict |
|---|---|---|---|
| **Frontier (finite circulant)** | Coniglio et al. [2608.18769](https://arxiv.org/abs/2608.18769), 19 Aug 2026 | +up to 11 on 25 values \(R(3,n)\), \(24\le n\le 49\), \(n\neq 27\); eight exact \(R_C(3,n)\); \(n\le 410\) | Own that range. Frontier *method* for \(t\ge 50\): **their IP**, not our empty mask |
| **Frontier (asymptotic \(R(3,k)\))** | Hefty–Horn–King–Pfender [2510.19718](https://arxiv.org/abs/2510.19718) v3 | \(R(3,k)\ge(\tfrac12+o(1))k^2/\log k\) via a two-bite random construction | Wrong aisle for a finite cell. Do not implement the nibble |
| **Superseded constant** | Campos–Jenssen–Michelen–Sahasrabudhe [2505.13371](https://arxiv.org/abs/2505.13371) | \(R(3,k)\ge(\tfrac13+o(1))k^2/\log k\); killed the Fiz–Griffiths–Morris \(\tfrac14\) conjecture | Same aisle as two-bites. Historical |
| **Current cyclic lore** | Harborth–Krause; JiLTX; Exoo/Tatarevic/Kuznetsov | Cyclic saturation, heuristic cyclic \(R(3,k)\) | Seeds for \(t\ge 50\) |

### 2.3 Referees (Look 3) — bleeding-edge of the *decision*

| Status | Paper / system | Regime | Verdict |
|---|---|---|---|
| **SOTA combinatorial tree (sparse residual)** | Yu’s bitset + Prosser survey (MC / MCR / BBMC / Östergård) + matching colour | Sparse, \(n\sim 186\), target 19 | Port matching colour + flatten into `native_decide` before another hunt |
| **SOTA exact, dense interlocking cliques** | CliSAT (San Segundo et al., EJOR 2023) | Dense MCP | Complements of residuals; polarity leftovers |
| **SOTA exact, sparse / hub-and-spoke (ISA mix)** | MOMC (Li et al.) | ISA: best on ~75% of their space | Route by density. Do not pick one solver for all 5c hits |
| **SOTA MIP third backend** | Gurobi (ISA ~14%); OR-Tools CP-SAT (job 6a) | Recertify, not hunt score | `cpsat_19.unsat` = second-solver agree; timeout \(\neq\) accept |
| **Bleeding-edge reductions** | LearnAndReduce / KaMIS [2412.14198](https://arxiv.org/abs/2412.14198) | Sparse MWIS after kernelization | Optional filter on reduction rules. Not PPO |
| **Bleeding-edge branching synthesis** | Gao–Wang–Zhang–Liu [2412.07685](https://arxiv.org/abs/2412.07685) | 3-regular MIS | Wrong degree sequence |
| **Current routing paper** | ISA [2512.03419](https://arxiv.org/abs/2512.03419) | Predict CliSAT vs MOMC vs Gurobi | Use the *routing*, not their GNN-as-solver (HGS never won) |
| **Wrong scale** | SMS (Kirchweger–Szeider 2024; Lean+SMS 2026) | \(n\le 17\) completeness | Do not encode \(K_{251}\) |

### 2.4 Extra symmetry (Look 4) — frontier is two orbits for *non-classical* cells

| Status | Paper | Claim | Verdict |
|---|---|---|---|
| **Frontier two-orbit (books/wheels)** | Lidický–McKinley–Pfender–Van Overberghe [2407.07285](https://arxiv.org/abs/2407.07285) (EJC 2025) | Polycirculant tabu + flag-algebra *upper* bounds; several exact book/wheel numbers | Frontier for “two orbits beat one.” Flag algebras are upper bounds — not our job |
| **Frontier SAT block-circulant** | Wesley [2410.03625](https://arxiv.org/abs/2410.03625) (Discrete Math. 2025) | \(R(B_{n-1},B_n)=4n-1\) infinite family; SAT/IP block-circulants; SMS critical-graph counts | Encoding to steal for Look 4 |
| **Current SAT Cayley/multicolour** | Wesley [2509.03784](https://arxiv.org/abs/2509.03784) | \(R(K_4,K_4-e,K_4-e)\ge 35\), \(R(K_3,K_4,C_4,C_4)\ge 49\); SMS on small critical graphs | Same encoding family. Different numbers |
| **Current enumerator** | Goedgebeur–Van Overberghe [2107.04460](https://arxiv.org/abs/2107.04460) | Circulant + block-circulant enum; **no** classical \(R(s,t)\) +1 | Evidence that 1-circulant is saturated for classical cells |
| **Small ordered/dihedral SAT** | [2604.16188](https://arxiv.org/abs/2604.16188), [2607.06817](https://arxiv.org/abs/2607.06817) | Kissat / permutational Ramsey | Wrong \(n\). Keep as encoding folklore |

### 2.5 Geometry (Look 5) — frontier is asymptotic; finite is leftover-\(\alpha\)

| Status | Paper | Claim | Verdict |
|---|---|---|---|
| **Frontier asymptotic \(r(4,t)\)** | Mattheus–Verstraete [2306.04007](https://arxiv.org/abs/2306.04007) v5 / Annals 2024 | \(r(4,t)=\Omega(t^3/\log^4 t)\) | Look at the **unital / O’Nan \(K_4\) structure**, then delete, then exact \(\alpha\). Do not optimise \(C\) |
| **Frontier explicit algebraic** | Ihringer–Mattheus [2608.21769](https://arxiv.org/abs/2608.21769), 22 Aug 2026 | \(R(33,t)\ge t^{2.1-o(1)}\); Frankl–Wilson exponent \(1/4\to 1\) | Catalogue (5f already). Will not beat Paley(17) on exact small \(n\) |
| **Book-algebraic, not \(R(4,t)\)** | Dai–Lin [2606.07214](https://arxiv.org/abs/2606.07214) | New SRGs; \(R(B_n,B_n)=4n+1\) infinitely often | Wrong number. Same “do not Hoffman the raw polarity graph” lesson |

### 2.6 Papers that look frontier and are the wrong aisle

Retrieved in the same 2025–2026 window. Listed so the next agent does
not “discover” them.

| Paper | Why it looks hot | Why it is the wrong aisle |
|---|---|---|
| Ma–Shen–Xie [2507.12926](https://arxiv.org/abs/2507.12926) | First exponential improvement over Erdős 1947 for \(r(\ell,C\ell)\) | Random sphere graph. No A40 adjacency |
| Hunter–Milojević–Sudakov follow-up; [2601.15183](https://arxiv.org/abs/2601.15183) | Multicolour exponential increment from the same model | Same |
| Tatarevic [2608.06531](https://arxiv.org/abs/2608.06531) | Lean 4 increment, \(R(12,12)\ge 1641\) | Connector lift on *existing* certificates. \(n\sim 1640\) |
| Brosch–Lidický–Miyasaki–Puges [2511.04364](https://arxiv.org/abs/2511.04364) | Canonical / ordered Ramsey SAT + flag algebras | Different numbers |
| [2608.27405](https://arxiv.org/abs/2608.27405) online stars vs paths | Posted 27 Aug 2026 | Online Ramsey. Different game |
| [2606.24198](https://arxiv.org/abs/2606.24198) tower hypergraph | “New tower-type lower bounds” | Hypergraph. #78-adjacent scale |
| Extractors / Li / Cohen / BRSW | Explicit \((\log N)^C\) | No graph to MCS at feasible \(N\) |
| Bradač containers | Product constructions | No graph to enumerate |
| Berghaus–Wagner ICLR 2025 | RL on \(R(4,4)\) | Loses to random |
| Communications Physics 2026 MCP review | Quantum / AI clique survey | Survey of MCP, not a Ramsey cell machine |
| [2608.12673](https://arxiv.org/abs/2608.12673) weakened Gallai–Ramsey books | Aug 2026 | Different Ramsey |
| [2608.01962](https://arxiv.org/abs/2608.01962) / [2608.01921](https://arxiv.org/abs/2608.01921) new *upper* bounds | Aug 2026 | Upper bounds. We mint lowers |

### 2.7 Retrieval queries that returned the *right* aisle

These are the queries that should be re-run, not “Ramsey 2026”:

```
all:"Ramsey number" AND (circulant OR cyclotomic) AND (construction OR "lower bound")
all:"Ramsey" AND (polycirculant OR "block-circulant" OR "block circulant")
ti:"Ramsey" AND (SAT OR "integer programming") AND (lower OR construction)
ti:Ramsey AND (quintic OR quartic OR "cyclotomic class")
id:2608.18169   id:2608.18769   id:2603.09172
id:1510.06102   id:2407.07285   id:2410.03625
id:2512.03419   id:2412.14198   id:2306.04007
id:2608.21769   id:2509.03784   id:2107.04460
```

Queries that **look** relevant and are traps:

```
ti:"Ramsey numbers" AND (new OR improved OR lower) AND (2025 OR 2026)
  → dumps online / hypergraph / Gallai / upper-bound papers
all:"Yu" AND "R(4,20)"
  → only Yu (good, but complete)
all:"distance-space" AND Ramsey
  → IR/clustering noise; only Coniglio is on-topic
all:Exoo Tatarevic Ramsey circulant
  → arXiv keyword search drifted to 26 Aug 2026 unrelated IDs
```

---

## 3. One queue (if someone continues this tree)

**7a–7f ran on the A40 (30 Aug 2026).** No `CELL?`. 7c packed fat \(S\)
and leftover still had a 16-IS. The next search change is **`7c1`**
(SAT-on-pool + leftover-IS cuts), not `pod-phase7.sh` and not more SAT
seconds on \(\max\lvert S\rvert\). Guide: [`JOB-7C1.md`](JOB-7C1.md).

Implemented as **`phase7`** (`docs/JOB-PHASE7.md`) for Looks 3→1→6→2→4→5.
That wrapper is **done**. Do not re-run it.

1. ~~Finish **6a**~~ Hygiene only. CP-SAT unsat-19 **timed out**. Timeout \(\neq\) proof. Residual is 5a/7a `c-decide`.
2. ~~Port Yu’s **matching colour + flatten**~~ 7a: nodes \(\times 1/6\), wall clock **worse**. Residual theorem holds.
3. Hunt **only** pools with `min_resid ≤ width` — **7c1** now, CEGIS cuts, not max \(\lvert S\rvert\).
4. If 1-circulant saturates: **2-polycirculant** with the same referee (7e.1, \(n\ge 200\)). Not 7e’s \(m\le 61\).
5. \(R(3,t)\) \(t\ge 50\) — 7d leftover 346–374 \(>256\). Width skip.
6. Polarity leftover iff leftover \(\le\) width **and** \(N+1\) beats the floor. 7f: exact 84 vs 314.

The number that is still true is **252**. The place it can increment is a
**new \(S\)** plus a **finished accept**, not a new GPU kernel.
