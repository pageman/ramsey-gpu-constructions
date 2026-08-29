# Session hand-off: GPU Ramsey constructions

This is a **new-LLM bootstrap**. Read this before code. It is not a paper and not a status slide. It records the narrative arc, the method arc, every box that was on or under the table, and the questions that are still live.

**As of 28 Aug 2026 ~16:24 UTC (last operator contact ~12:08 UTC).**

---

## 0. Current state in one screen

| Item | Fact |
|---|---|
| Repo (this workspace) | GPU-native explicit Ramsey catalogue + Next.js dashboard + Python engine. Empty-repo new project that grew into a research instrument. |
| Origin | Internal/Private `pageman/ramsey-gpu-constructions` (cannot be made Public). |
| Public GitHub | `https://github.com/pageman/ramsey-gpu-constructions` |
| Owner | The Pageman / pageman@gmail.com / GitHub `pageman` / Docker Hub `pageman` |
| Local catalogue | 263 graphs, **all jobs 1a–3d run at `local` scale**, Paley(17) exact \(\omega=\alpha=3\). |
| A40 pod | RunPod PyTorch 2.4 template, 1× A40 48GB, ~$0.44/hr, CA-MTL-1. Container id `3631e8666026`. Pod nick `armed_yellow_buzzard` / id `amyrwqft651q8i` (may have changed). |
| A40 code path | `/workspace/ramsey-gpu-constructions` cloned from **public GitHub**, not this Origin remote. |
| A40 done | `1a` Paley \(p\le 997\); `1b` F2 n=8–12; `1c` GQ+PG; `1d` FW+Sidon; `2c` circulant \(R(3,k)\) n≤56-ish, 46 graphs, 29s. |
| A40 in flight | **`2a` restarted in tmux session `ramsey`**, last operator screenshot **p=631** at 12:06 UTC 28 Aug. Prior 2a died at **p=5347 / 01:01 UTC / 5358 registry rows** after laptop close + `disown` (SIGHUP still won). Restart **re-enumerates from p=13**. |
| A40 not started | `3a` `3b` `3c` `3d`. Skip `2b`. Job **`4a` (Yu-pool) does not exist in CLI**. |
| Do not | Terminate the pod (volume wipe). Train PPO/GAT. Treat Hoffman \(N^{1/k}\) as \(C\ge 1.01\). Claim Erdős #78 progress. |

**Scientific one-liner:** this session built a GPU-native *map* of algebraic families Run001 skipped. It did **not** produce an infinite-family exponential. The only remaining path to a *survey number* is Yu-style restricted cyclotomic-pool search + exact residual \(\alpha\), which is planned (`docs/plan-move-a-number.md`) and not implemented.

---

## 1. Narrative arc

### Act I — Commission (empty repo, New Project)

A cloud agent is asked to recover what **RamseyConstructor-GNN Run001** never ran: GPU-native *explicit* constructions aimed at Erdős’s constructive challenge \(R(k,k)\ge C^k\) with \(C\ge 1.01\). The implied antagonist is not “Ramsey theory is hard”; it is **a specific failed GPU run** that spent budget on CPU Paley/FW CSVs, Hoffman instead of Lovász \(\vartheta\), and never shipped `gnn_model.pt`.

The agent scaffolds a Next.js dashboard (port **43123**, later dual-stack `--hostname ::` after IPv4-only bind refused `[::1]`) plus a Python engine. Taste constraint: one complete slice, not a platform; no auth/db; shadcn; honest copy (no “Welcome to your app”).

**Story beat:** “We will fill the compute gap.” Subtext already in the README: *filling the gap is not solving #78*.

### Act II — Instrument (kernels, jobs, honesty)

The engine is built as **non-overlapping jobs** (1a–1d, 2a–2c, 3a–3d) with cell ownership so four pods could run phase 1 in parallel. Kernels are deliberately \(O(n)\) / \(O(n\log n)\): Paley via squares not Euler, FFT circulant spectrum, FWHT Boolean Cayley, VT \(\omega=1+\omega(N(0))\), Tomita MCS for \(n\le 64\), Hoffman/Delsarte as *proxies*.

Local run: 263 graphs. Paley(17) is the jewel: exact 3/3, \(R(4,4)>17\), \(N^{1/k}\approx 2.03\). Large Paley spectral \(k\) inflates; \(N^{1/k}\) *falls* with \(N\) toward ~1.2. Kasami often degenerate. GNN/PPO is **refused** (Berghaus–Wagner ICLR 2025: RL can lose to random on \(R(4,4)\)). The one “learned” object is a Hoffman mask ranker (`data/mask_ranker.json`).

**Story beat:** the dashboard is a *catalogue of absences* — what Run001 skipped — not a leaderboard of new \(C\).

### Act III — Field (A40, SSH, mortality)

The user rents a live A40. Jobs 1a–1d complete in seconds to minutes. 2a (cyclotomic to \(N\sim 10^4\)) is the long job. The pod image has **no tmux**. Foreground SSH dies with the laptop. `Ctrl-Z` / `bg` / `disown -h` is attempted; 2c is accidentally/opportunistically run during the pause (29s, 46 graphs); 2a resumes at p=4999 then continues to **5347 at 01:01 UTC** and dies anyway. Morning after: only Jupyter is alive. 2a is restarted **inside tmux `ramsey`**, last seen at p=631.

**Story beat:** the bottleneck shifted from algebra to **process supervision**. The scientific object (cyclotomic ranker) is hostage to SIGHUP.

### Act IV — Recalibration (what can we hope for?)

User asks the ceiling. Answer: finite catalogue, not \(C\ge 1.01\). Paley(17) stays the exact diagonal jewel; Paley(101) exact 5/5 would look “better” on \(C^*\) only because \(k\) grew; 2A might beat Paley by \(10^{-4}\) Hoffman; 3B matching Yu \(R(4,20)\ge 252\) is the only headline number.

Then: **recent Erdős problems**. #78 still open (Li 2023 extractors = \((\log N)^C\), not GPU-MCS). #986 solved by Bradač (Jun 2026) off-diagonal exponent — not enumerable. #165 \(R(3,k)\) constant now \(1/2+o(1)\) — triangle-free *process*, not Paley. #183 multicolour triangles claimed divergent (OpenAI+Lean) — different problem. 2026 papers that *do* move finite cells: Yu quintic-pool, IP circulants, Mattheus–Verstraete polarity (asymptotic already; finite \(\alpha\) still open computationally).

**Story beat:** the quest reframes from “Erdős $100” to “Radziszowski +1”.

### Act V — Plan without execution (move-a-number)

A kernel/search plan is written: MCS to \(n\sim 256\), Östergård \(c[i]\), incremental \(K_4\)/Schur, multiplier canonicalisation, then jobs A/B/C (Yu-pool / \(R(3,t)\) / polarity exact \(\alpha\)). **None of this is coded.** The live A40 is still running the *old* 2a (Hoffman ranker on whole class unions).

**Story beat (unresolved):** will the next session implement 4a, or finish the original 3a–3d queue, or scp the A40 catalogue and stop spending?

### Dramatic through-line

> A reconstruction of a missed GPU run discovers that the missed families were never going to pay the Erdős prize, then discovers that a *different* 2026 construction (Yu’s 32-subset of two quintic classes) is the only thing an A40 can still add to the survey — while the actual GPU is busy re-enumerating cyclotomic class unions for a spectral score that will not enter the survey.

---

## 2. Methodological arc

### M1. Forensic reconstruction
Start from Run001 artifacts (later a Kosmos PDF): Paley/FW/synthetic mix, N≲300, RF/GAT/Hoffman, missing `gnn_model.pt`, Paley rigid attractor, annealing → random. Method = **gap table**: family × kernel × “why skipped”.

### M2. Explicit-family generator, not a learner
Decision: implement closed-form adjacency (Paley, GP, cyclotomic, F2 quadratic/Gold/Kasami, PG(2,q), GQ W(3,q), Nagy, FW, Singer, products, Sidon, ANF, two-block ILS). **Do not** train PPO. Ranker = Hoffman of \(G\) and \(\bar G\). This is a methodological *refusal*, not a missing feature.

### M3. Certificate ledger with two grades
- **Exact:** VT MCS on \(N(0)\) / \(N^c(0)\) for small Cayley (Paley 5, 17). Theorem: \(R(k,k)>N\).
- **Spectral:** Hoffman / Delsarte / ratio / inertia. **Not a theorem.** Dashboard still plots \(N^{1/k}\) as a *pessimistic proxy* that gets worse as \(N\) grows when \(k\) is inflated.

### M4. Job ownership as concurrency control
`(job → (families, cell))` in `engine/registry.py`. Designed for four pods. On one A40, ownership does **not** prevent GPU contention or `catalog.json` last-writer-wins. `registry.jsonl` is append-only; catalog rewrite is not atomic across processes.

### M5. Scale split
`RAMSEY_SCALE=local|runpod`. Local: Paley ≤101, cyclo ≤181, F2 n≤10. Runpod: Paley ≤997, cyclo ≤10⁴, F2 n≤12, ANF 13–16, circ_n_max 251. CUDA presence defaults to runpod — dangerous if a CPU box has a stub CUDA.

### M6. Recalibration to survey cells
Literature pass (Aug 2026 arXiv + erdosproblems.com) changes the *objective function*: from \(C^*\) / #78 to Radziszowski DS1 rev.18 finite cells. Plan document states the **hard rule**: search with a cheap filter; certify with a *decision* \(\alpha\le t-1\). Never Hoffman in the ILS loop.

### M7. Operational method (unplanned, now first-class)
tmux on RunPod; never foreground SSH; never Terminate; `disown` is insufficient; 2a has **no checkpoint** (restart = p=13). Catalogue on the pod and catalogue in Origin/GitHub have **diverged**.

### Method through-line

> Speculative GPU search → explicit algebraic enumeration with cheap spectral proxies → admission that proxies cannot publish → planned exact residual MCS that the running job still does not do.

---

## 3. Story boxes

Legend: **E** explicit (said in chat/README) · **I** implicit (in code/docs, not stressed) · **N** inferred (from behavior) · **X** extrapolated (likely true, not checked) · **H** hidden (not in user-facing copy; next LLM must know)

### 3.1 Quest and stakes
| ID | Kind | Box |
|---|---|---|
| S01 | E | Original goal: explicit \(R(k,k)\ge C^k\), \(C\ge 1.01\). |
| S02 | E | Honest result: none of these families give that infinite exponential. Paley is \(\sim k^2\). |
| S03 | E | Paley(17) is the standout exact certificate: \(\omega=\alpha=3\), \(R(4,4)>17\). |
| S04 | E | Run001 skipped GPU-native families; this repo exists to run them. |
| S05 | E | Best hope of GPU runs: finite catalogue + small chance of an off-diagonal finite bound, not #78. |
| S06 | I | Dashboard rhetoric (“gap Run001 skipped”) is the *product*; a new bound would be a bonus. |
| S07 | N | User’s real desire shifted mid-session from “what did Run001 miss?” to “can the A40 move a number?” |
| S08 | X | If 2a finishes, user will still ask “did we beat Paley?” and the answer will be spectral noise. |
| S09 | H | Erdős $100 for constructive exponential is **not** closer because of this repo. Saying otherwise is a scientific error. |
| S10 | E | Yu \(R(4,20)\ge 252\) is the 3B literature target (order 251, \(251\equiv 3\pmod 4\), not Paley). |

### 3.2 People, venues, provenance
| ID | Kind | Box |
|---|---|---|
| S11 | E | Owner: The Pageman, pageman@gmail.com. |
| S12 | E | Origin cannot be Public; GitHub public copy was pushed after adding the Mac SSH key to GitHub. |
| S13 | I | Cloud agent Origin remote ≠ GitHub remote. Pod clones **GitHub**. Code changes here do not appear on the A40 until push-to-GitHub + `git pull` on the pod. |
| S14 | E | Run001 compared via uploaded Kosmos PDF: RF/GAT/Hoffman, Paley attractor. |
| S15 | E | Berghaus–Wagner ICLR 2025: do not train PPO edge-flip. |
| S16 | N | User is operating the pod from a Mac laptop that sleeps; they are not a Linux sysadmin. Every instruction must be key-chord explicit (`Ctrl-Z` ≠ the string Ctrl-Z). |
| S17 | H | SSH `root@69.30.85.91 -p 22061` **changes on pod restart**. Always read the RunPod UI. |
| S18 | E | Mac key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKB+AI4iaHv7pjjAmW1DD8r4OmqWXr6Pb+K4SBXAaL+1 pageman@gmail.com` labeled **Ramsey** on RunPod and GitHub. |
| S19 | I | Template is official `runpod/pytorch:2.4.0-…` not the repo Dockerfile pin `1.0.3-cu1281-…`. Torch on pod `2.4.1+cu124 True`. |
| S20 | H | `/post_start.sh` must not override image CMD; Jupyter owns port 8888 (token appeared in `ps`: treat as secret, rotate if this doc is public). |

### 3.3 Characters of the graphs
| ID | Kind | Box |
|---|---|---|
| S21 | E | Paley = quadratic-residue circulant, \(p\equiv 1\pmod 4\). |
| S22 | E | Cyclotomic class unions = 2A; *subsets of two classes* = Yu, not implemented. |
| S23 | E | GQ \(W(3,q)\) polarity = Mattheus–Verstraete *style*, not their unital sampling theorem. |
| S24 | I | Kasami degeneracy (\(k>N+1\)) is a family failure, not a kernel bug. |
| S25 | I | Job 3A docstring says “from 2A winners”; **code only seeds Paley + Singer**. Waiting for 2a is optional for 3a. |
| S26 | E | 2C is \(R(3,k)\) only (Schur sum-free). 3B is \(R(4,k)\). Mixing them is a cell-ownership bug. |
| S27 | N | 2C on A40 skipped many \(n\) (no n=44,48,51… in the paste) because ILS failed `triangle_free` — those \(n\) are absent, not certified triangle-containing. |
| S28 | X | Paley(101) exact \(\omega=\alpha=5\) would give \(R(6,6)>101\), \(101^{1/5}\approx 2.52\), a prettier \(C^*\) that is still not asymptotic. |
| S29 | H | Spectral \(k\) on large Paley is an *upper bound on \(\omega,\alpha\) that is loose*, used as if it were a Ramsey \(k\). It **inflates** \(k\) and **deflates** \(N^{1/k}\). Plotting it vs Erdős \(2^{k/2}\) is visually damning and methodologically correct only as a negative result. |

### 3.4 Operations drama
| ID | Kind | Box |
|---|---|---|
| S30 | E | Foreground SSH ⇒ job dies with laptop. |
| S31 | E | `disown -h` after `Ctrl-Z`/`bg` was done; 2a still died by 01:01 UTC. |
| S32 | E | tmux was not on the image; installed 28 Aug ~12:05 UTC. |
| S33 | E | 2a has no checkpoint. Restart = from p=13. First run reached 5347; second run last seen 631. |
| S34 | I | `catalog.json` on pod last write 00:17 (2c end). `registry.jsonl` continued until 01:01 (2a). Catalog can lag registry until `run_job` finishes. |
| S35 | I | `mask_ranker.json` on pod dated Aug 27 20:02 until 2a **completes**. Stale ranker ≠ 2a running. |
| S36 | E | User ran 2c while 2a was SIGTSTP’d; 2c finished 29.46s; then `bg` resumed 2a. Harmless scientifically; shows jobs share one shell. |
| S37 | H | `upsert_graphs` + `write_catalog` is last-writer-wins. Two parallel `engine.cli` on one pod can drop graphs from catalog.json (jsonl survives). |
| S38 | E | Do not Terminate the pod. Stop/pause if spending must halt. |
| S39 | N | User will close the laptop again. Any advice that requires an open SSH window will fail. |
| S40 | X | 2a to p=9973 at ~10s/prime×masks could be many hours; first death at 5347 after ~40 min post-disown suggests ~1–2s per emit at that size, so full 2a is hours not days. |

### 3.5 Literature / prize boxes
| ID | Kind | Box |
|---|---|---|
| S41 | E | Erdős **#78** constructive \(R(k)>C^k\): open. Li 2023: no clique/IS of size \((\log N)^C\). Extractors are not an A40 MCS target. |
| S42 | E | Erdős **#986** off-diagonal exponent: solved Bradač Jun 2026. Containers; not enumerable here. |
| S43 | E | Erdős **#165** \(R(3,k)\): lower constant \(1/2+o(1)\) (Hefty et al. Oct 2025). Process, not circulant. |
| S44 | E | Erdős **#183** \(\lim R(3;k)^{1/k}\): claimed divergent (OpenAI 2026 + Lean). Orthogonal (Schur / multicolour). |
| S45 | E | Mattheus–Verstraete Annals 2024: \(r(4,t)=\Omega(t^3/\log^4 t)\). Asymptotic. Finite exact \(\alpha\) still a compute job. |
| S46 | E | Ihringer–Mattheus 22 Aug 2026: \(TG_{d,h}\), first explicit \(R(33,t)\ge t^{2.1-o(1)}\). Catalogue family, not #78. |
| S47 | E | Yu arXiv:2608.18169: quintic 2-class *subset*, \(\lvert S\rvert=32\), \(\alpha=19\), residual 186, bitset BnB 1.4s. |
| S48 | E | Coniglio et al. Aug 2026 IP circulants: +1..+11 on 25 values \(R(3,n)\), \(n\le 410\). Do not rerun \(t\le 49\) against Gurobi. |
| S49 | E | Nagda–Raghavan–Thakurta AlphaEvolve: nine small cells; Yu then beat their \(R(4,20)\ge 237\). |
| S50 | I | Forum debate on #78: method of conditional probabilities may be “constructive” in an algorithmic sense but is **not** strongly explicit (adjacency in polylog time). This project is in the strongly-explicit / algebraic camp. |
| S51 | H | Campos–Griffiths–Morris–Sahasrabudhe *upper* bound improvement on \(R(s,s)\) is the other 2023–26 Ramsey news. It does not help *lower* bounds and was easy to confuse with “Ramsey breakthrough” headlines. |

### 3.6 Emotional / rhetorical (hidden, but they steer the user)
| ID | Kind | Box |
|---|---|---|
| S52 | H | “GPU-native” was a grant/spec aesthetic; the graphs that move numbers are **CPU bitset MCS** on n=186. Selling more CUDA is the wrong next spend. |
| S53 | H | \(N^{1/k}\) is a seductive KPI that systematically rewards small exact certificates and punishes large honest spectral bounds. Paley(17) will always “win” the dashboard. |
| S54 | N | User’s “what’s after 2a?” and “can they run in parallel?” are *queue anxiety*, not a request to change the math. |
| S55 | X | A published +1 on \(R(4,21)\) would satisfy the session more than a perfect 2a catalogue. |

---

## 4. Method boxes

### 4.1 Explicit kernels (in repo, working)
| ID | Kind | Box |
|---|---|---|
| M01 | E | Paley row = \(\{x^2\}\) in \(O(p)\). Spectrum closed form. |
| M02 | E | Linear (Euler) sieve. |
| M03 | E | Circulant eigenvalues = FFT of first row. |
| M04 | E | Boolean Cayley eigenvalues = FWHT. |
| M05 | E | VT identities \(\omega=1+\omega(N(0))\), \(\alpha=1+\alpha(N^c(0))\). |
| M06 | E | \(K_4\)-free \(\Leftrightarrow\) \(N(0)\) triangle-free. |
| M07 | E | Triangle-free circulant \(\Leftrightarrow\) Schur sum-free \(S\). |
| M08 | E | Distance-space ILS: \(\lfloor n/2\rfloor\) bits. |
| M09 | E | Cyclotomic \(S=-S\): \(2^{e/2}\) masks, Gray-ish enumeration. |
| M10 | E | Tomita MCS + colour bound, **n≤64 python ints**. |
| M11 | E | Delsarte / Hoffman / Cvetković inertia from spectrum. |
| M12 | E | Two-block circulant constructor (materialises \(n\times n\)). |
| M13 | I | `ils_connection_set(..., mask=)` exists for Yu pools and **no job passes a pool mask**. |
| M14 | I | `incremental_triangle_delta` exists and **is unused**. |
| M15 | I | `pack_neighbours` uint64 limbs exist; MCS for n>64 does **not** use a full limb solver. |

### 4.2 Explicit failures / ceilings (must not “fix” by more Paley)
| ID | Kind | Box |
|---|---|---|
| M16 | E | MCS n>64 = 64-core subsample + greedy. Cannot certify Yu residual 186. |
| M17 | E | ILS objective = \(\max(\alpha_{\mathrm{Hoff}}(G),\alpha_{\mathrm{Hoff}}(\bar G))\). Wrong for survey bounds. |
| M18 | E | Full FFT every ILS flip. Eigenvalue update is \(O(n)\): \(\lambda_j\pm 2\cos(2\pi jd/n)\). |
| M19 | E | \(K_4\) test \(O(d^3)\) nested loops. |
| M20 | E | No multiplier canonicalisation (\(T=\lambda S\) isomorphic). |
| M21 | E | No Östergård \(c[i]\), no matching colour bound, no decision API \(\alpha<t\). |
| M22 | E | 2A enumerates **whole class unions**, not k-subsets of a 2-class pool. |
| M23 | E | 3B unrestricted ILS on primes ≤313, Hoffman score. |
| M24 | I | Job 2B recertify path is a stub (skips FW, skips most F2). Not worth A40. |
| M25 | I | `write_ledger` overwrites claims with **this job only**, not a merge. |
| M26 | I | `catalog.json` triplicated (`data/`, `public/data/`, `src/data/`). |

### 4.3 Planned, not implemented (`docs/plan-move-a-number.md` **v2**)

v2 (29 Aug 2026) rewrites the algorithm from A40 evidence: jobs 2a/3b proved Hoffman ILS does not move a cell; `max_clique` \(n>64\) cannot certify Yu’s residual. SAT/CliSAT/MoMC and GPU MCS are **deprioritized** — one bitset Östergård/Tomita in decision mode first. Implementation order is the table in the plan (§10): MCS → residual-from-row → Yu \(S\) gate (`data/yu_r4_20.json`) → process → job 4a dry-run → A40 night.

| ID | Kind | Box |
|---|---|---|
| M27 | E | Bitset MCS to n~256, **decision** \(\alpha\le t-1\). CPU, not GPU BnB. |
| M28 | E | Decision API `clique_at_least` / `independent_set_at_most`. Abort on witness or colour-bound death. |
| M29 | I | SAT/CP-SAT (CliSAT) only if a residual at \(n\sim 220\) exceeds ~10 s after colour-bound Tomita is tight. |
| M30 | E | Incremental Schur / triangle filter \(O(|S|)\); never \(O(d^3)\) \(K_4\) on all vertices. |
| M31 | E | Job 4a Yu-pool: primes 200–400, e∈{4,5,8,10}, 2-class pools, restricted process, greedy-\(\alpha\) reject, lex-min, exact residual. Targets 241, 251, 269. |
| M32 | E | Job 4b: rewrite 2c for \(t\ge 50\) and polycirculant; do not compete IP paper on 24–49. |
| M33 | E | Job 4c: exact \(\alpha\) on GQ after \(K_4\)-clean, **q=7 only** first. |
| M34 | E | GPU role = batched legality + greedy reject, not MCS trees. |
| M35 | E | Reproduce Yu’s published \(S\) as a regression **before** any A40 search. |
| M36 | I | numba/C on MCS inner loop only after the Python bitset is correct on Yu’s residual. |

### 4.4 Families implemented vs not
| ID | Kind | Box |
|---|---|---|
| M37 | E | Implemented: Paley prime, GP, cyclotomic union, F2 quadric/Gold/Kasami, PG(2,q), GQ W(3,q), FW, Sidon, Singer, Kronecker products, ANF quadratic, block-circulant ILS, circulant r3/r4 ILS. |
| M38 | E | Not implemented: Ihringer–Mattheus \(TG_{d,h}\), polynomial Paley-like (Yip et al. 2024), Yu pool subset search, extractor Ramsey graphs, Bradač products, triangle-free process on \(K_n\). |
| M39 | I | Paley of prime *powers* \(\mathbb F_{p^n}\), n>1, is listed in README gap table; check `constructions.py` before claiming it ships (prime Paley is the 1a path). |
| M40 | N | Nagy intersecting-family may be present as a builder and unused by jobs. |

### 4.5 Experimental design (jobs)
| ID | Kind | Box |
|---|---|---|
| M41 | E | CLI: `python3 -m engine.cli --job {phase0\|1a…3d} --scale local\|runpod`. |
| M42 | E | Phase 0 = kernel tests. Must pass Paley(17) FFT=eigvalsh, VT ω=3. |
| M43 | E | Intended parallelism: 1a–1d on four pods; 2c ∥ 2a; 3* after 2a. |
| M44 | E | Actual parallelism: one A40; 1a–1d sequential; 2c during 2a pause; 3* queued. |
| M45 | I | Local workspace catalogue already contains **local-scale** 2a–3d. A40 runpod-scale is the missing data, not the missing code paths (except 4a). |
| M46 | H | Comparing local 2a (p≤181) to A40 2a (p≤9973) without tagging `scale` in analysis will mix spectral regimes. Every graph row has `"scale"`. |

### 4.6 Inferred methodology (not written as policy, but followed)
| ID | Kind | Box |
|---|---|---|
| M47 | N | Prefer closed-form / FFT over \(O(n^3)\) eigensolvers. |
| M48 | N | Prefer not claiming theorems from Hoffman. README is careful; dashboard copy must stay careful. |
| M49 | N | Prefer reproducing a published witness (Yu \(S\)) over open-ended ILS. |
| M50 | N | Prefer one A40 job at a time. |
| M51 | X | Next method change that pays: MCS decision n≤256, then 4a, **not** more cyclotomic e or Paley p. |

### 4.7 Hidden computational hazards
| ID | Kind | Box |
|---|---|---|
| M52 | H | 2a nested loops: for each prime ≤10000, for each eligible e\|(p−1), for each negation-closed mask, FFT + maybe MCS. Cost is why 2a is the long pole. |
| M53 | H | `time_limit` 0.05s for p>61 means large 2a graphs are **almost purely spectral**. Exact=False is by design. |
| M54 | H | Numpy FFT on n=9973 is CPU anyway; “GPU job” 2a may barely use the A40. Check `backend.py` before buying more GPU hours for 2a. |
| M55 | H | ANF n=16 is \(N=65536\) FWHT + spectral k. Looks good on \(C^*\) if k is underestimated. Trap called out in chat. |
| M56 | H | RunPod billed while 2a was **dead** ~01:01–12:05 UTC (~11 h idle GPU). |
| M57 | I | Tests: `engine/test_kernels.py`, `engine/test_invariants.py`. No Yu-\(S\) regression yet. |

### 4.8 Extrapolated SOTA to import (literature, not yet code)
| ID | Kind | Box |
|---|---|---|
| M58 | X | Östergård Cliquer + BBMC + matching bound = Yu’s cert stack. |
| M59 | X | Exoo tabu on partition flips; Benlic–Hao BLS for plateau. |
| M60 | X | KaMIS reductions before exact α. |
| M61 | X | Multiplier lex-min cuts Yu pool by \(\varphi(p)/2\). |
| M62 | X | Instance space (arXiv:2512.03419): dense residuals → CliSAT; do not port IPDPS GPU MCS. |
| M63 | X | Additive combinatorics: max sum-free in \(\mathbb Z/n\) is “middle third”; seed 2c/4b from that, not random bits. |

---

## 5. Artifact map (where truth lives)

| Artifact | Path | Trust |
|---|---|---|
| Engine jobs | `engine/jobs.py` | Source of what a job *actually* does (trust this over README if they disagree). |
| Ownership | `engine/registry.py` `OWNERS` | Cells/families. Not enforced at runtime. |
| Scale knobs | `engine/scale.py` | local vs runpod limits. |
| MCS | `engine/kernels/mcs.py` | n≤64 real; n>64 fake. |
| ILS | `engine/kernels/cayley.py` | Hoffman objective; unused mask/incremental. |
| Cert from row | `engine/kernels/rowcert.py` | VT + FFT. |
| Local graphs | `data/catalog.json` (263) | Local scale only. |
| Local registry | `data/registry.jsonl` | 196 lines locally; **pod has 5358+ 2a rows** (diverged). |
| Ranker | `data/mask_ranker.json` | Written at **end** of 2a. |
| Move-a-number plan | `docs/plan-move-a-number.md` | Next scientific work. Not in CLI. |
| This hand-off | `docs/SESSION-HANDOFF.md` | Session memory. |
| Dashboard | `src/components/dashboard.tsx` port 43123 | Visualises *bundled* catalog, not live A40 unless files copied. |
| Pod data | `/workspace/ramsey-gpu-constructions/data/` on A40 | **Canonical runpod results.** scp before Terminate. |
| Pod tmux | session `ramsey` | 2a as of 12:06 UTC 28 Aug. |

Git on Origin `main` (this agent): kernels + dashboard + plan. **Does not contain A40 runpod catalog.**

---

## 6. Job queue (operational)

```
DONE on A40:  1a 1b 1c 1d 2c
RUNNING:      2a  in tmux ramsey  (restart; last seen p=631; target ~9973)
SKIP:         2b
NOT STARTED:  3b  (do next — Yu order)  then 3a 3c 3d
NOT IN CLI:   4a Yu-pool / MCS n=256  (plan only)
```

Sequential on one GPU. After `job 2a done` in tmux:

```bash
RAMSEY_SCALE=runpod python3 -m engine.cli --job 3b --scale runpod
RAMSEY_SCALE=runpod python3 -m engine.cli --job 3a --scale runpod
RAMSEY_SCALE=runpod python3 -m engine.cli --job 3c --scale runpod
RAMSEY_SCALE=runpod python3 -m engine.cli --job 3d --scale runpod
```

Then **scp** `data/{catalog.json,registry.jsonl,mask_ranker.json,bound_ledger.json}` off the pod.

---

## 7. Questions for a new LLM session

Paste this file and ask a subset. Grouped so the next session does not re-litigate #78 unless asked.

### 7.1 Immediate operations (ask first if the user is at a terminal)
1. Is tmux session `ramsey` still alive, and what is the last `cyclotomic_union_p*` line?
2. Did 2a print `job 2a done`? If yes, is `mask_ranker.json` timestamped after that?
3. What is the current RunPod SSH IP/port (do not reuse 69.30.85.91 blindly)?
4. Has the pod been Stopped/Terminated since 28 Aug 12:08 UTC?
5. Should we scp `data/` off the pod **now**, even if 2a is incomplete?
6. Idle GPU cost vs finishing 2a: is the user still willing to pay ~$0.44/hr?
7. Confirm: one process only — no second `engine.cli` while 2a runs?

### 7.2 Scientific priority (fork in the road)
8. Finish original queue 3b→3a→3c→3d on the **existing** Hoffman/ILS kernels, or pause A40 and implement plan 4a (Yu-pool + MCS n=256) first?
9. Is a Radziszowski +1 the success criterion, or a complete runpod catalogue?
10. Is Paley(17) still the “answer” we show on the dashboard, or do we hide spectral \(N^{1/k}\) for N>64 so it stops looking like a failed exponential?
11. Do we ever want PPO/GAT despite Berghaus–Wagner? (Default: no.)
12. Is Erdős #78 in scope for this repo at all after the literature pass? (Default: no.)

### 7.3 Kernel work (if implementing the plan)
13. Can we reproduce Yu’s published \(S\) mod 251 with \(\omega=3,\alpha=19\) as a regression in `test_kernels.py` before writing search?
14. Cython vs numba vs a 50-line C bitset MCS for n≤256?
15. Decision-only MCS with Östergård \(c[i]\) — what target \(t\) per prime (survey gaps)?
16. OpenMP flatten vs Python multiprocessing vs just single-thread first?
17. OR-Tools CP-SAT on the pod image, or skip SAT until CPU MCS works?
18. Wire `mask=` on ILS to 2-class pools without waiting for a new job name?
19. Incremental \(K_4\) bitset: is `uint64` enough for n=400 (7 limbs)?
20. Multiplier canonical form: store `min_hash` in catalog to dedupe 2a/3b?

### 7.4 Job 4a design
21. Prime list: 241, 251, 269 first, or full 200–400?
22. e ∈ {4,5,8,10} only when −1 ∈ H, as Yu, or also odd e?
23. Process+anneal budget per (p, pair): 10⁴ or 10⁵?
24. Objective: maximise |S| among K4-free, or minimise greedy α on residual?
25. Shortlist size handed to exact cert?
26. Independent checker language (C vs second Python)?
27. Must 4a wait for 2a, or is 2a scientifically optional now?

### 7.5 Jobs 3* on old kernels (if finishing the queue)
28. 3b on current ILS: expected to match Yu 252, or only to produce Hoffman-scored circulants that cannot be certified at n=251?
29. If 3b cannot exact-certify n=251, is running it a waste of A40 hours?
30. 3a: change code to actually load 2a winners, or Paley/Singer only as written?
31. 3c q=11,13: Hoffman only — worth running?
32. 3d n=16: publish with a spectral-disclaimer banner, or skip as a trap?

### 7.6 Catalogue / dashboard / provenance
33. How to merge pod `registry.jsonl` (thousands of 2a rows, including a dead-run duplicate prefix after restart) into Origin `data/catalog.json` without doubling graph_ids?
34. Restarted 2a will duplicate graph_ids `cyclotomic_union_p*_e*_mask*` — upsert by graph_id is OK; timestamps which run wins?
35. Should dashboard ingest runpod scale as a second catalog, not overwrite local 263?
36. Dual-stack port 43123 still the preview, or is the user’s live object the pod logs?
37. GitHub public vs Origin internal: which is source of truth for *code*? (Code: Origin/this branch. Data: pod.)

### 7.7 Literature / claims hygiene
38. What sentence is allowed in a README/paper about C≥1.01? (Suggested: “these families do not.”)
39. Cite Yu 252 as “3B target” or as “already achieved by Yu, our job is to recertify/search nearby primes”?
40. Bradač / Li extractors: mention in Related Work only, never as “GPU next steps”?
41. AlphaEvolve: steal initialization families for 4b, do not wrap an LLM search loop on the pod?
42. Radziszowski DS1 rev.18 (24 Apr 2026): which cells are still the weakest \(R(4,t)\) after Yu?

### 7.8 Process / reliability
43. Add checkpointing to 2a (last p in a file) before another multi-hour run?
44. `tee` + tmux on every job in `post_start.sh` so a future pod is laptop-safe by default?
45. Write catalog incrementally every N graphs to survive death?
46. Heartbeat file `data/heartbeat.json` with last graph_id + rss + gpu util?
47. Separate CPU pod for MCS cert vs A40 for batched filters (plan says CPU cert is faster per dollar)?

### 7.9 Things a new LLM should **not** spend the first hour on
48. Re-deriving Paley spectrum.
49. Re-arguing whether Hoffman is Lovász \(\vartheta\).
50. Scaffolding a second app / auth / database.
51. Training a GNN to “escape Paley.”
52. Building extractor graphs at N=2^20.
53. Enumerating \(2^{50}\) Yu-pool subsets.
54. Creating a PR (New Project: user did not ask).
55. Changing Origin visibility to Public (impossible).

### 7.10 Closure questions (for the human)
56. If 2a is still at p<2000, do we kill it and implement 4a, accepting the sunk 2a GPU spend?
57. If 2a is done, do we scp and stop the pod until 4a exists in git (pull on pod), or burn 3b–3d on old kernels tonight?
58. What would count as *session success* in one sentence, from the user, not from Erdős?

---

## 8. Suggested first prompt for the next session

> You are continuing `ramsey-gpu-constructions`. Read `docs/SESSION-HANDOFF.md` and `docs/plan-move-a-number.md`. Do not re-solve Erdős #78. Live A40: tmux session `ramsey` was running job `2a` (restarted, last seen p=631 toward 9973) at 12:06 UTC 28 Aug 2026; prior 2a died at p=5347. Jobs 1a–1d and 2c are done on the pod. Job 4a is not in the CLI. MCS cannot certify n>64. ILS uses Hoffman.  
> First: tell me whether to (A) babysit 2a→3b→3a→3c→3d on current kernels, or (B) stop 2a and implement Yu-pool + MCS n=256 as in the plan. Then check the pod if I paste SSH output.

---

## 9. One-page chronology

| When (UTC, 2026) | Event |
|---|---|
| 27 Aug | Empty repo → engine + dashboard; local 263 graphs; Origin + GitHub. |
| 27 Aug evening | A40: 1a 14.5s, 1b 131s, 1c 1.1s, 1d 1.2s; 2a started. |
| 27 Aug ~20:23 | “Best we can hope for” + Erdős-problem literature. |
| 27 Aug 22:48+ | Plan `docs/plan-move-a-number.md` committed. |
| 28 Aug 00:17 | 2c completed during 2a SIGTSTP; catalog write. |
| 28 Aug 00:18 | `bg` + `disown -h`; 2a resumes ~p=4999. Laptop closed. |
| 28 Aug 01:01 | Last 2a registry row p=5347. Process dies sometime after. |
| 28 Aug 12:02–12:08 | Diagnosed dead 2a; installed tmux; restarted 2a; last seen p=631. |
| 28 Aug 12:08 | User asked remaining jobs / parallelism. Answer: sequential; 3b next. |
| 28 Aug 16:24 | This hand-off. Pod state **unchecked in this session**. |
