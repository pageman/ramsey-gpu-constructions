# Session hand-off: GPU Ramsey constructions

This is a **new-LLM bootstrap**. Read this before code. It is not a paper
and not a status slide. It records the narrative arc, the method arc,
every box that was on or under the table, and the questions that are
still live.

**As of 30 Aug 2026 ~04:13 UTC.** Campaign result sheet:
`docs/A40-CAMPAIGN.md`. Plan v2: `docs/plan-move-a-number.md`. Public
repo: https://github.com/pageman/ramsey-gpu-constructions (`main` =
`18d2aeb` when this was written).

Legend used below: **E** explicit (said in chat/README) · **I** implicit
(in code/docs, not stressed) · **N** inferred (from behavior) · **X**
extrapolated (likely true, not checked) · **H** hidden (not in
user-facing copy; next LLM must know)

---

## 0. Current state in one screen

| Item | Fact |
|---|---|
| Scientific result | **No published +1.** \(R(4,20)\ge 252\) is Yu (arXiv:2608.18169). Paley(17) still the best exact diagonal here. |
| False cells | 4a printed `CELL? R(4,20)≥338/354` for `p=337` residual **262** and `p=353` residual **264**. C MIS is n≤256; `return 0` looked like “no 19-IS”. **Do not announce.** Fixed after the run (`skip_n>256`). |
| Real weak cert | 4c leftover 84, exact \(\alpha=21\), \(R(4,22)>84\). Survey already \(\ge 314\). |
| Jobs on A40 | **All of 1a–4c ran.** 2a: 99755 s, 9288 Hoffman rows. 3d: n=13/14 only, then died. 4a: 1715 s, 6 rows. 4b: 8.56 s, 0 graphs. 4c: 1.58 s, 1 graph. |
| Pod | RunPod A40 `armed_yellow_buzzard` / `amyrwqft651q8i`, container `3631e8666026`. SSH last seen `root@69.30.85.91 -p 22061`. **Stop is OK. Do not Terminate.** |
| tmux | `ramsey` = leftover 2a (done). `ramsey4` **gone** (phase4 finished; user exited the pane). |
| Code | Jobs 4a/4b/4c in CLI. Yu gate + restricted process + C Östergård MIS n≤256. Residual n>256 is no longer an exact certificate. |
| Git | Mac `~/ramsey-gpu-constructions`: `origin` = Cursor Origin, `github` = `git@github.com:pageman/ramsey-gpu-constructions.git`. Both at `18d2aeb` after README banner. |
| Data on GitHub | `data/a40/` = 2a catalogue (~14 MB), 4abc catalogue, registry, ledger. In-tree `data/catalog.json` is still the **small** dashboard tree. |
| Mac Downloads | `~/Downloads/Ramsey-GPU-Constructions/` is an **rsync snapshot**, not a git clone. Do not `git push` from there. |
| This agent | Cannot `gh` push. User publishes with `git fetch origin && git merge origin/main && git push github main`. |
| Do not | Claim #78 progress. Treat Hoffman \(N^{1/k}\) as \(C\ge 1.01\). Announce 338/354. Train PPO. Terminate the pod. Create a PR unless asked. |

**Scientific one-liner:** the session built a GPU-native map of families
Run001 skipped, then learned that the only survey path is Yu-style
pool + exact residual \(\alpha\), then implemented that path, then
**failed the certificate** on the first “hits” because the solver lied
at n>256. The literature number did not move.

---

## 1. Narrative arc

### Act I — Commission (empty repo, New Project)

A cloud agent is asked to recover what **RamseyConstructor-GNN Run001**
never ran: GPU-native *explicit* constructions aimed at Erdős’s
constructive challenge \(R(k,k)\ge C^k\) with \(C\ge 1.01\). The
antagonist is a **failed GPU run** (CPU Paley/FW CSVs, Hoffman instead
of Lovász \(\vartheta\), no `gnn_model.pt`), not “Ramsey theory is hard”.

Scaffold: Next.js dashboard (port **43123**, later `--hostname ::`) +
Python engine. One slice, no auth/db, honest copy.

**Beat:** “Fill the compute gap.” Subtext already in the README:
*filling the gap is not solving #78*.

### Act II — Instrument (kernels, jobs, honesty)

Non-overlapping jobs 1a–3d. Kernels \(O(n)\) / \(O(n\log n)\). Local
263 graphs. Paley(17) jewel: exact 3/3, \(R(4,4)>17\). PPO refused
(Berghaus–Wagner). One “learned” object: Hoffman mask ranker.

**Beat:** the dashboard is a *catalogue of absences*.

### Act III — Field (A40, SSH, mortality)

User rents an A40. 1a–1d finish. 2a is the long job. No tmux on the
image. Laptop sleep + `disown` still loses to SIGHUP (death at p=5347).
Restart in tmux `ramsey` from p=13. 2a eventually **completes**: 99755 s,
9288 graphs. No cell.

**Beat:** bottleneck = process supervision, then = wrong objective.

### Act IV — Recalibration (what can we hope for?)

Ceiling: finite catalogue, not \(C\ge 1.01\). #78 still open. Quest
reframes to **Radziszowski +1**. Yu \(R(4,20)\ge 252\) is the only
nearby headline.

**Beat:** $100 prize → survey cell.

### Act V — Plan v2 (algorithm, not more families)

A40 evidence becomes three negative theorems: Hoffman class-unions do
not move a cell; Hoffman ILS never recertifies Yu \(S\); `max_clique`
n>64 cannot certify a 186-vertex residual and can hang 3d. Plan v2:
cheap filter + decision \(\alpha\le t-1\); never Hoffman; never dense
\((p/2)\times(p/2)\).

**Beat:** the kernel is the plot, not the family list.

### Act VI — Implementation (4a/4b/4c on Origin, GitHub still `a49da0c`)

Bitset Östergård in C (`native_mis.c`, n≤256), residual-from-row,
`data/yu_r4_20.json`, restricted process + anneal + lex-min, jobs
4a/4b/4c, catalog/ledger **merge** so 4a can sit beside 3d. Yu gate:
structural OK; exact \(\alpha=19\) **not** kernel-certified (timeout on
“no 19-IS”). Public GitHub stays at IPv6 bind. Sync path = tarball
`ramsey-4abc-update.tgz` because drag-download fails.

**Beat:** the instrument can now *ask* the right question. It cannot yet
*answer* Yu’s residual in 25 s.

### Act VII — Operator comedy (getting phase4 to stay alive)

User extracts tarball on the pod, lists jobs including 4a–4c, compiles
`.so`, then pastes `tmux new` **and** `python3` together. `duplicate
session: ramsey4`; hunt runs on raw SSH `pts/3`. Later they attach
correctly. They paste chat prompts into bash (`command not found:
root@…`). They run `tmux ls` on the **Mac**. They `tmux attach` after
the job is already done. They run `scp` **on the pod** with literal
`<ssh-port>`.

**Beat:** the science is hostage to *which machine and which pane*.

### Act VIII — Peripeteia (CELL? then retraction)

phase4 finishes. 4b empty. 4c weak exact. 4a prints four `CELL?
R(4,20)≥354`. Catalog shows `yu_pool_p337_e4` residual **262** and
`yu_pool_p353_e8` residual **264**, both `exact True α 19`. That is a
**solver lie**, not a theorem. Fix lands on `main` after the run.

**Beat:** the session’s only “discovery” is a bug that looks like a paper.

### Act IX — Publication (dual remotes, README banner)

User scp’s 436 KB 4abc catalog + 14 MB 2a catalog to the Mac. Merges
Origin `a49da0c..9335659` in `~/ramsey-gpu-constructions`, commits
`data/a40/`, `git push github main` → `2b13b8f`, then `git push origin
main`. README banner `18d2aeb` pushed to both. Origin cannot be Public;
GitHub is the public copy. Those are **different remotes**, already
wired on the Mac.

**Beat:** the campaign is now a public negative result plus a kernel
warning.

### Dramatic through-line

> A reconstruction of a missed GPU run discovers that the missed
> families will not pay the Erdős prize; discovers that Yu’s 32-subset
> of two cyclotomic classes is the only A40-sized survey attack;
> implements that attack; watches the GPU spend 28 hours ranking the
> *wrong* set; then spends 29 minutes on the *right* set and prints a
> fake \(R(4,20)\ge 354\) because the certificate was a 256-bit mask
> pretending to be a 264-vertex proof. The published sentence is
> therefore a retraction.

---

## 2. Methodological arc

### M1. Forensic reconstruction
Gap table: family × kernel × “why Run001 skipped”.

### M2. Explicit-family generator, not a learner
Closed-form adjacency. **Do not** train PPO. Ranker = Hoffman. Refusal,
not a missing feature.

### M3. Certificate ledger with two grades
Exact VT MCS vs spectral Hoffman/Delsarte. Spectral is **not** a theorem.

### M4. Job ownership as concurrency control
`(job → (families, cell))`. `registry.jsonl` append-only. `catalog.json`
was last-writer-wins; **later upsert-by-graph_id** so 3d and 4a can
finish in either order.

### M5. Scale split
`RAMSEY_SCALE=local|runpod`. CUDA defaults to runpod.

### M6. Recalibration to survey cells
Objective: Radziszowski DS1 finite +1. Hard rule: cheap filter in the
loop; decision \(\alpha\le t-1\) in the cert; never Hoffman in ILS.

### M7. Operational method (first-class)
tmux; never foreground SSH; never Terminate; 2a had **no checkpoint**
(restart = p=13, 28 h rerun). Catalogue on pod / Origin / GitHub /
Downloads can all diverge.

### M8. Solver + search-space rewrite (plan v2, then code)
Restricted process on a 2-class pool; greedy-\(\alpha\) reject;
multiplier lex-min; bitset decision MIS on \(G[N^c(0)]\). Yu published
\(S\) is a **regression gate**, not a search seed that must be rediscovered.

### M9. Residual identity as the primitive
\(\alpha(G)\ge 1+\alpha(G[N^c(0)])\) when 0 can join any residual IS.
A residual IS of size \(t-1\) **rejects** \(R(4,t)\). Accept = prove
none. Accept is the hard side (Yu: 1.4 s OpenMP, ~2.7e7 nodes on 186
vertices). This kernel timed out on Yu’s own residual.

### M10. Width as a silent axiom
C MIS: 4×uint64 = 256 bits, `MAXN 256`. Python residuals use arbitrary
ints. Calling C on n>256 used to return `found=0` **without**
`timed_out=1`. Job 4a hardcoded `exact=True` on emit. That conjunction
is how a false cell is *methodologically produced*: an interface
contract (n≤256) treated as a theorem (α<t).

### M11. Operator-in-the-loop as part of the method
Tarball, `gcc`, named tmux, `PYTHONUNBUFFERED`, detach, scp from the
**Mac** using RunPod **SSH over exposed TCP**. Every failure mode in
Act VII is a method box, not colour.

### M12. Publication as dual-home provenance
Origin = team. GitHub = public. Downloads = working copy without `.git`.
`data/a40/` is the run record; `data/catalog.json` is the dashboard
fixture. Mixing them in analysis is a method error.

### Method through-line

> Speculative GPU search → explicit algebraic enumeration with cheap
> spectral proxies → admission that proxies cannot publish → planned
> exact residual decision → implemented decision that **silently
> accepts** when the instance does not fit the bitset → retraction →
> public negative result.

---

## 3. Story boxes

### 3.1 Quest and stakes
| ID | Kind | Box |
|---|---|---|
| S01 | E | Original goal: explicit \(R(k,k)\ge C^k\), \(C\ge 1.01\). |
| S02 | E | Honest result: none of these families give that infinite exponential. Paley is \(\sim k^2\). |
| S03 | E | Paley(17) is the standout exact certificate: \(\omega=\alpha=3\), \(R(4,4)>17\). |
| S04 | E | Run001 skipped GPU-native families; this repo exists to run them. |
| S05 | E | Best hope of GPU runs: finite catalogue + small chance of an off-diagonal finite bound, not #78. |
| S06 | I | Dashboard rhetoric (“gap Run001 skipped”) is the *product*; a new bound would be a bonus. |
| S07 | N | User’s real desire shifted from “what did Run001 miss?” to “can the A40 move a number?” |
| S08 | E | 2a finished; “did we beat Paley?” is spectral noise. Confirmed: no cell. |
| S09 | H | Erdős $100 for constructive exponential is **not** closer. Saying otherwise is a scientific error. |
| S10 | E | Yu \(R(4,20)\ge 252\) is the literature target (order 251, not Paley). |
| S11a | E | Session success criterion (late): Radziszowski +1 vs catalogue. **Missed.** |
| S12a | E | 4a `CELL?` is not a +1. Public README says so. |
| S13a | I | A “pretty” \(C^*\) from Paley(101) exact 5/5 would still not be asymptotic. |
| S14a | X | A true \(R(4,21)\) +1 would have closed the emotional arc; 4c’s 84 did not. |
| S15a | H | The most publishable object this session produced is a **negative experimental theorem** about Hoffman ILS + a **retracted certificate**. |

### 3.2 People, venues, provenance
| ID | Kind | Box |
|---|---|---|
| S11 | E | Owner: The Pageman / Paul Pajo, pageman@gmail.com, GitHub `pageman`. |
| S12 | E | Origin cannot be Public (Internal/Private only). GitHub is the public copy. |
| S13 | E | Cloud agent Origin ≠ GitHub. Pod was cloned from **public GitHub** (stale `a49da0c`) until tarball. |
| S14 | E | Run001 compared via Kosmos PDF: RF/GAT/Hoffman, Paley attractor. |
| S15 | E | Berghaus–Wagner ICLR 2025: do not train PPO edge-flip. |
| S16 | N | User operates from a Mac that sleeps; not a Linux sysadmin. Instructions must be one pane, one machine, no `#` comments if they paste the `#`. |
| S17 | H | SSH `root@69.30.85.91 -p 22061` **changes on pod restart**. Read RunPod Connect. |
| S18 | E | Mac key labeled **Ramsey** on RunPod and GitHub (`ssh-ed25519 … pageman@gmail.com`). |
| S19 | I | Template is official `runpod/pytorch:2.4.0-…`, not the repo Dockerfile pin. |
| S20 | H | Jupyter owns 8888; treat tokens in `ps` as secrets. |
| S21a | E | Mac git clone: `~/ramsey-gpu-constructions`. `origin`→Cursor, `github`→GitHub. |
| S22a | E | `~/Downloads/Ramsey-GPU-Constructions` has **no `.git`**. Fatal if used as the clone. |
| S23a | E | Agent cannot `gh auth`; user pushes `github main`. |
| S24a | I | New Project rule: no PR unless asked. User did not ask for a PR. |
| S25a | H | Temporary Origin remote name must not be mentioned in user copy. Speak “this project” / GitHub name. |
| S26a | N | User will paste *assistant prose* into bash (prompts, `root@…#`, markdown). |
| S27a | N | User conflates “GitHub clone” with Origin-visibility notes. Same English word “repo”, three objects. |
| S28a | E | Docker Hub `pageman` exists in older notes; unused this wave. |

### 3.3 Characters of the graphs
| ID | Kind | Box |
|---|---|---|
| S21 | E | Paley = QR circulant, \(p\equiv 1\pmod 4\). |
| S22 | E | Cyclotomic **class unions** = 2A. **Subsets of two classes** = Yu / 4a. |
| S23 | E | GQ \(W(3,q)\) polarity = Mattheus–Verstraete *style*, not their unital theorem. |
| S24 | I | Kasami degeneracy (\(k>N+1\)) is a family failure. |
| S25 | I | Job 3A docstring “from 2A winners”; code seeds Paley+Singer. |
| S26 | E | 2C is \(R(3,k)\) only. 3B/4a are \(R(4,t)\). Mixing cells is a bug. |
| S27 | N | 2C skipped many n because ILS failed triangle-free — absent, not certified bad. |
| S28 | X | Paley(101) exact 5/5 → \(R(6,6)>101\) prettier \(C^*\), still not #78. |
| S29 | H | Spectral \(k\) inflates and deflates \(N^{1/k}\). Plot vs \(2^{k/2}\) is a negative result. |
| S30a | E | Yu undirected \(S\) (32 distances), g=6, e=5, \(D_0\cup D_2\), deg 64, residual 186, \(\omega=3\), \(\alpha=19\). First directed list was wrong. |
| S31a | E | `data/yu_r4_20.json` holds that \(S\). |
| S32a | E | 4a hunt: p∈[200,400], e∈{4,5,8,10}, 64 walks, 64 anneal, 8 MIS × 25 s. |
| S33a | E | Hits claimed: `yu_pool_p337_e4` \|S\|=37 deg=74 residual=262; `yu_pool_p353_e8` \|S\|=44 deg=88 residual=264. |
| S34a | I | Four 353 registry lines share `graph_id` `yu_pool_p353_e8` (no i,j,S in id). Last upsert wins. |
| S35a | I | `_small` used to drop lists longer than 32 from *features* meta; emit still dumped raw `params` so S survived in catalog. |
| S36a | E | 4c leftover 84, \(\alpha=21\) exact, \(R(4,22)>84\). |
| S37a | I | Ledger often prints `R(k,k)>N` even for off-diagonal cells (diagonal-shaped statement). Hygiene bug. |
| S38a | H | \(\alpha(G)=1+\alpha(\mathrm{residual})\) is **not** automatic if a large IS lives in \(N(0)\) or mixes. Yu’s paper uses the residual; this code assumes the same. Unchecked mixed IS is a hole. |
| S39a | X | A residual 262 with greedy \(\alpha(G)<20\) is already surprising; if true, exact no-19-IS on 262 verts in <25 s is *more* surprising — hence the bug prior. |

### 3.4 Operations drama
| ID | Kind | Box |
|---|---|---|
| S30 | E | Foreground SSH ⇒ job dies with laptop. |
| S31 | E | `disown -h` after Ctrl-Z/bg; 2a still died. |
| S32 | E | tmux installed 28 Aug ~12:05 UTC. |
| S33 | E | 2a no checkpoint. First death p=5347; restart from 13; **finished** 99755 s. |
| S34 | I | catalog can lag registry until `run_job` finishes. 3d never `write_catalog` (catalog mtime stayed 2a). |
| S35 | I | `mask_ranker.json` written at **end** of 2a. |
| S36 | E | 2c during 2a SIGTSTP; harmless scientifically. |
| S37 | H | Two `engine.cli` can still race if both write the same graph_id; upsert helps, does not serialize MIS. |
| S38 | E | Do not Terminate. Stop after scp. |
| S39 | N | User will close the laptop / paste into the wrong host. |
| S40 | E | Full 2a was ~28 h, not days. Fermi estimate was in the right order. |
| S41a | E | 3d hung ~100% of **one CPU**, GPU idle; died after n=14. Old colouring path, no timeout. |
| S42a | E | Do not attach tmux `ramsey` to start 4a. New session `ramsey4`. |
| S43a | E | Tarball `/root/ramsey-4abc-update.tgz` extracted on pod; `engine/yu_pool.py` + `data/yu_r4_20.json`. |
| S44a | E | `gcc -O3 -shared -fPIC` → `native_mis.so` 15976 bytes. User `ls`’d the `.c` first. |
| S45a | E | Pasting `tmux new -s ramsey4` + python together → `duplicate session` + hunt on SSH. |
| S46a | E | Live hunt PID 19265, 100% CPU, pts/3, started 23:24Z 29 Aug. |
| S47a | E | User ran check commands on Mac zsh (`tmux: command not found`). |
| S48a | E | User attached `ramsey4` after exit; session gone. Catalog is the evidence. |
| S49a | E | `scp` with `<ssh-port>` on the **pod**. Correct: Mac + Connect TCP 69.30.85.91:22061. |
| S50a | E | scp OK: catalog 436 KB, registry 37 KB, ledger 1222 B. 2a 14 MB kept as `catalog-2a.json`. |
| S51a | I | Pod `catalog.json` after 4a is the **tarball** tree + upsert, not the 14 MB 2a file. 2a catalog was scp’d earlier to `a40-from-pod/`. |
| S52a | E | `jobs.4b` in that catalog said `scale=local` — leftover smoke in the tarball, not the A40 4b (`graphs=0`). |
| S53a | N | Mid-range 4a ETA 2–5 h was high; greedy reject made most pools skip MIS. Wall 1715 s. |
| S54a | X | If they rerun 4a with the fix, wall time stays ~30 min unless many residuals land in 186–256. |
| S55a | H | `Polyfit RankWarning` in 4c is `engine/run.py` slope on too-few k’s. Ignore. |

### 3.5 Literature / prize boxes
| ID | Kind | Box |
|---|---|---|
| S41 | E | #78 open. Li 2023 extractors \((\log N)^C\). Not an A40 MCS target. |
| S42 | E | #986 solved Bradač Jun 2026. Containers. |
| S43 | E | #165 \(R(3,k)\) constant \(1/2+o(1)\). Process, not circulant. |
| S44 | E | #183 claimed divergent (OpenAI+Lean). Orthogonal. |
| S45 | E | Mattheus–Verstraete 2024: \(r(4,t)=\Omega(t^3/\log^4 t)\). Asymptotic. |
| S46 | E | Ihringer–Mattheus \(TG_{d,h}\): catalogue, not hunt. |
| S47 | E | Yu 2608.18169: \|S\|=32, α=19, residual 186, 1.4 s. |
| S48 | E | Coniglio IP: do not rerun \(t\le 49\). 4b is t≥50. |
| S49 | E | AlphaEvolve: Yu beat their \(R(4,20)\ge 237\). Do not wrap an LLM loop on the pod. |
| S50 | I | Strongly explicit / algebraic camp, not MCP / conditional probabilities. |
| S51 | H | Campos–Griffiths–Morris–Sahasrabudhe is an **upper** bound story. Easy headline confusion. |
| S52b | E | Quartic literature: \(R(4,22)\ge 314\). Do not hunt p=313 to *match* 314; hunt 21 or 23. |
| S53b | E | R4_LOWER in code: 20→252, 21→252, 22→314. Incomplete vs full DS1. |
| S54b | X | Weakest \(R(4,t)\) after Yu is still a table question; do not trust R4_LOWER as DS1. |
| S55b | H | Publishing a false 354 on social/arXiv would be a priority-one retraction. The README exists to prevent that. |

### 3.6 Emotional / rhetorical (steer the next LLM)
| ID | Kind | Box |
|---|---|---|
| S52 | H | “GPU-native” is spec aesthetic; numbers move on **CPU bitset MCS**. More CUDA is the wrong spend. |
| S53 | H | \(N^{1/k}\) rewards small exact jewels. Paley(17) always “wins” the dashboard. |
| S54 | N | “What next / can they run in parallel?” is queue anxiety. |
| S55 | E | A published +1 would have satisfied more than a perfect 2a catalogue. Did not happen. |
| S56 | N | `CELL?` produced a hope spike; the next session must not re-inflate it. |
| S57 | N | User asked “how to publish” the *retraction sentence* — they want the negative result visible, not buried. |
| S58 | I | Dual-remote explanation was re-asked three times (Origin vs GitHub vs Downloads). |
| S59 | H | Praise of “the hunt is running” was correct operationally and **not** a scientific endorsement of upcoming CELL? lines. |
| S60 | X | Next hope-spike risk: a residual **≤256** with greedy α<20 and a 25 s timeout-as-accept if someone weakens the timed_out check again. |

### 3.7 Inferred / extrapolated / hidden story (not already above)
| ID | Kind | Box |
|---|---|---|
| S61 | N | User is willing to pay A40 hours and to follow long command blocks if they are *single-host*. |
| S62 | N | User treats the agent as the operator’s copilot, not as a paper coauthor, until the README banner. |
| S63 | N | “Publish on GitHub” means README + artifacts, not a journal. |
| S64 | X | If 4a is rerun with n>256 skip, the public story does not change unless a residual ≤256 certifies. |
| S65 | X | A second A40 night without a wider MIS (n~300 or SAT) repeats 4b-empty / 4a-timeout. |
| S66 | H | Job 4a still emits the Yu witness as `exact=True` from **structural** `gate["ok"]`, not `alpha_certified`. Catalog α=19 on p=251 is **literature**, not this kernel. |
| S67 | H | `_decision_cert(..., True)` was hardcoded on 4a hits; `search_pool` already required `cert.exact`. The C lie made `cert.exact` true. Two bugs stacked. |
| S68 | H | Features() builds graph_id from a **2×2 dummy adj**; N is overwritten. Degree columns can be nonsense. Dashboard rows for 4a are not to be trusted for degree stats. |
| S69 | I | `public/data/catalog.json` and `src/data/catalog.json` still triplicate the small tree. A40 dumps are only under `data/a40/`. |
| S70 | H | 3d n=13/14 live in the **2a-era registry** on the Mac (`catalog-2a` / earlier scp), not necessarily in `data/a40/registry.jsonl` from the 4abc scp (37 KB). Check both files before claiming 3d provenance. |

---

## 4. Method boxes

### 4.1 Kernels that exist and what they actually do
| ID | Kind | Box |
|---|---|---|
| M01 | E | Paley row = \(\{x^2\}\) \(O(p)\). Closed-form spectrum. |
| M02 | E | Linear sieve. |
| M03 | E | Circulant eigs = FFT of first row. |
| M04 | E | Boolean Cayley eigs = FWHT. |
| M05 | E | VT: \(\omega=1+\omega(N(0))\), \(\alpha=1+\alpha(N^c(0))\) (used as residual MIS +1). |
| M06 | E | \(K_4\)-free \(\Leftrightarrow\) \(N(0)\) triangle-free (`nbhd_triangle_free`). |
| M07 | E | Triangle-free circulant \(\Leftrightarrow\) Schur sum-free. |
| M08 | E | Distance-space ILS: \(\lfloor n/2\rfloor\) bits. |
| M09 | E | Cyclotomic \(S=-S\): \(2^{e/2}\) masks (job 2a). |
| M10 | E | Tomita MCS + colour, **n≤64** python (`mcs.py`). n>64 = 64-core subsample + greedy colour **no timeout**. |
| M11 | E | Delsarte / Hoffman / Cvetković from spectrum. |
| M12 | E | Two-block circulant constructor. |
| M13 | I | `ils_connection_set(..., mask=)` still unused by 2a/3b. 4a does **not** use that ILS. |
| M14 | I | `incremental_triangle_delta` still unused. |
| M15 | E | `native_mis.c` Östergård, n≤256, 4 uint64 words. Preferred by `bitset_mcs.py`. |
| M16a | E | `residual_nbr(row)`: verts = non-neighbours of 0 except 0; Python int bitsets. |
| M17a | E | `greedy_alpha_row` = 1 + greedy MIS on residual. |
| M18a | E | `certify_row_decision`: reject triangle; reject greedy α≥t; MIS target **t−1** on residual; found ⇒ reject; timeout ⇒ not exact; empty tree ⇒ α≤t−1. |
| M19a | E | `restricted_process`: add random unused pool d while N(0) stays triangle-free. |
| M20a | E | `anneal_pool`: swap in pool; reject triangles; reject greedy α≥t. |
| M21a | E | `lexmin_distances`: multiplier orbit, undirected min. |
| M22a | E | `iter_yu_pools`: primes, e∈{4,5,8,10}, −1 in subgroup, all class pairs. |
| M23a | E | After fix: n>256 → C sets timed_out; Python `skip_n>256`; certify reason `residual k > 256`. |
| M24a | I | Python MIS fallback can handle n>256 in theory; 4a now **refuses** rather than running a 25 s tree on 260 verts. |
| M25a | E | Yu gate `ok` = structural (pool, \|S\|=32, deg 64, residual 186, triangle-free). `alpha_certified` is separate and was false. |

### 4.2 Failures / ceilings (do not “fix” with more Paley)
| ID | Kind | Box |
|---|---|---|
| M16 | E | Old MCS n>64 cannot certify Yu 186. Still true for `mcs.py`. |
| M17 | E | Hoffman ILS objective is wrong for survey cells. 3b proved it. |
| M18 | E | Full FFT every ILS flip; update could be \(O(n)\). |
| M19 | I | \(K_4\) still \(O(\lvert S\rvert^3)\) bit tests on N(0) — acceptable for \|S\|~30. |
| M20 | E | Multiplier lex-min **now exists** for 4a. 2a still stores raw masks. |
| M21 | E | Decision API exists for residual MIS. Not a general `clique_at_least` on arbitrary adj. |
| M22 | E | 2A = whole unions. 4A = k-subsets of a 2-class pool. Both ran. Neither moved a cell. |
| M23 | E | 3B unrestricted ILS, Hoffman, never recertified Yu S. |
| M24 | I | 2B stub. Not worth A40. |
| M25 | I | `write_ledger` now **merges by graph_id**. Old overwrite bug fixed for 4*. |
| M26 | I | catalog still triplicated for the dashboard tree. |
| M27a | E | **C MIS n>256 silent false-accept.** Fixed after 4a. Regression: `test_mis_n_over_256_is_not_a_certificate`. |
| M28a | E | 4a emit used to force `exact=True`. Fixed: use `cert.exact and not rejected`. |
| M29a | E | `CELL?` used to fire on p+1>published alone. Fixed: also requires exact. |
| M30a | E | 4b skip residual>280 ⇒ all n∈[501,521] skipped (sparse ILS from empty mask, 80 steps). |
| M31a | E | 4c leftover>256 would stop; q=7 leftover 84, so it ran. |
| M32a | I | 4c “keep 3 verts per line” is a heuristic K4-clean, not a uniqueness theorem. |
| M33a | H | `mis_decide` n>MAXN originally returned 0 **without writing** timed_out/lower (ctypes stayed 0). That is the precise lie. |
| M34a | H | `_pack_nbr` only packs 256 bits; bits ≥256 are dropped even if C were called with n≤256 by mistake. |
| M35a | X | Yu’s 186-vertex “no 19-IS” is still too hard for 25 s in this C kernel (gate timed out). A true new cell at residual ~186–220 needs Yu-class OpenMP or SAT. |
| M36a | X | Extending WORDS to 5–6 (n≤384) without a timeout-safe accept path will reprint CELL? on timeouts if someone sets exact on `not found`. |

### 4.3 Plan v2 vs what shipped
| ID | Kind | Box |
|---|---|---|
| M27 | E | Bitset decision n~256: **shipped** (C+Python). |
| M28 | E | Abort on witness or timeout: **shipped**, then violated by C n>256, then fixed. |
| M29 | I | SAT/CliSAT still not in the loop. |
| M30 | E | Incremental N(0) triangle filter: **shipped** for 4a process. |
| M31 | E | Job 4a Yu-pool 200–400: **ran on A40**. |
| M32 | E | Job 4b t≥50: **ran**, produced 0 graphs. |
| M33 | E | Job 4c q=7: **ran**, weak exact. |
| M34 | E | GPU role remained unused for 4a MIS (CPU). A40 was a **CPU rental** for phase4. |
| M35 | E | Yu S regression: structural **yes**, α=19 **no**. |
| M36 | I | C inner loop exists; it is not validated against Yu’s 1.4 s node count. |
| M37a | I | Plan said “never Hoffman in the loop” — 4a honours that. 2a/3b still Hoffman. |
| M38a | I | Plan said do not materialise (p/2)×(p/2) — `residual_nbr` is \(O(r^2)\) bit sets, r=residual. For r=264 that is fine; C cannot store it. |
| M39a | E | Yu pool search **is implemented** (M38 old “not implemented” is stale). |
| M40a | E | Ihringer–Mattheus / Yip / extractors / Bradač / 3d n=16 / AlphaEvolve-on-pod: still do not run. |

### 4.4 Families implemented vs not
| ID | Kind | Box |
|---|---|---|
| M37 | E | Implemented: Paley prime, GP, cyclotomic union, F2 quadric/Gold/Kasami, PG(2,q), GQ W(3,q), FW, Sidon, Singer, Kronecker, ANF quadratic, block-circulant ILS, circulant r3/r4 ILS, **Yu pool 4a**, **K4-clean polarity 4c**. |
| M38 | E | Not implemented: \(TG_{d,h}\), polynomial Paley (Yip), extractors, Bradač products, triangle-free process, polycirculant 4b as specified (4b is plain circulant). |
| M39 | I | Paley of prime powers \(\mathbb F_{p^n}\) n>1: check `constructions.py` before claiming. |
| M40 | N | Nagy builder may exist unused. |

### 4.5 Experimental design (jobs)
| ID | Kind | Box |
|---|---|---|
| M41 | E | CLI: `python3 -m engine.cli --job {phase0\|1a…3d\|4a\|4b\|4c\|phase4} --scale local\|runpod`. |
| M42 | E | Phase 0 = kernel tests. Paley(17) FFT=eigvalsh, VT ω=3. |
| M43 | E | Intended: 1a–1d parallel pods; 2c ∥ 2a; 4a ∥ 3d. |
| M44 | E | Actual: one A40, sequential waves. 4a started after 3d died. |
| M45 | E | Local catalogue ≠ A40. `data/a40/` is the runpod record. |
| M46 | H | Every analysis must filter `"scale"` and `"job"`. Mixing local 4b smoke with runpod 4b is how `jobs.4b scale=local` confused the 4abc catalog. |
| M47a | E | `phase4` = 4a then 4b then 4c in one process. |
| M48a | I | 4a `t_cell` = first t in {20,21,22} with p+1 > R4_LOWER[t]. For p=353 that is **20**, so they hunted α≤19, not a 22-cell. |
| M49a | I | `mis_keep=8` on runpod: up to 8 lowest-greedy candidates per pool get MIS. |
| M50a | E | Tests: `engine/test_kernels.py` (11), `engine/test_invariants.py` (8). Include Yu structural + n>256. |

### 4.6 Inferred methodology (policy-by-conduct)
| ID | Kind | Box |
|---|---|---|
| M47 | N | Prefer closed-form / FFT over \(O(n^3)\) eigensolvers. |
| M48 | N | Prefer not claiming theorems from Hoffman. |
| M49 | N | Prefer reproducing a published witness before search. |
| M50 | N | Prefer one A40 job at a time (then violated by “4a beside 3d”, then 3d was already dead). |
| M51 | E | Next method that *could* pay: MIS/SAT that decides n~186–280 in seconds, **or** keep residual ≤256 by taking denser S. |
| M52a | N | Prefer upsert/merge after the 3d/4a race was designed. |
| M53a | N | Prefer a public retraction over a quiet catalog row. |
| M54a | N | Prefer operator scripts over “just tmux” after the paste failures — **not yet written** as a pod `post_start` job wrapper. |

### 4.7 Hidden computational hazards
| ID | Kind | Box |
|---|---|---|
| M52 | H | 2a cost = primes × e × masks × FFT + maybe MCS. Why 28 h. |
| M53 | H | `time_limit` tiny for large 2a ⇒ almost purely spectral. |
| M54 | H | 2a barely needs the A40. Phase4 MIS is CPU. Billing GPU for 4a is convenience. |
| M55 | H | ANF n=16 FWHT + spectral k is a \(C^*\) trap. 3d never reached n=16. |
| M56 | H | Idle GPU billed while 2a was dead (~11 h) and while 3d hung one core. |
| M57 | I | Yu α=19 regression is **not** a passing exact test. |
| M58a | H | Empty-start 4b ILS cannot densify enough in 80 steps to get residual≤280 on n~500. |
| M59a | H | `features()` dummy 2×2 + `_id_suffix` without S-hash ⇒ collisions and junk degrees. |
| M60a | H | Clock source in C is `clock()` (CPU time). 25 s limit is CPU-seconds, OK for one thread. |
| M61a | H | `create-next-app` / dashboard port 43123 still exists; it does not show `data/a40/catalog-2a.json` unless copied into `data/catalog.json` (will blow the UI). |
| M62a | X | Loading 9288 Hoffman rows into the Next app without pagination will stutter. |

### 4.8 Extrapolated SOTA still to import
| ID | Kind | Box |
|---|---|---|
| M58 | X | Yu’s OpenMP BnB / Cliquer / BBMC for residual 186. |
| M59 | X | Exoo tabu; Benlic–Hao BLS. |
| M60 | X | KaMIS reductions before exact α. |
| M61 | X | Lex-min already cuts orbit; store hash in graph_id. |
| M62 | X | Instance space: dense residual → CliSAT; do not port IPDPS GPU MCS. |
| M63 | X | Seed 4b from middle-third sum-free, not empty bits. |
| M64 | X | WORDS=5–8 + mandatory timeout≠accept + independent checker. |
| M65 | X | Recertify any future hit with a second implementation before README. |

### 4.9 Provenance / git method
| ID | Kind | Box |
|---|---|---|
| M66 | E | Code truth: git `main` on GitHub **and** Origin after dual push. |
| M67 | E | Run truth: `data/a40/*` + Mac Downloads copies. |
| M68 | I | Agent workspace and Mac clone can be one commit apart; always `fetch` both remotes. |
| M69 | H | `git push origin main` on the Mac updates Cursor, not GitHub. `git push github main` is the public one. |
| M70 | E | Visibility notes (Internal/Private) are about Origin, not about the GitHub clone path. |

---

## 5. Artifact map (where truth lives)

| Artifact | Path | Trust |
|---|---|---|
| Engine jobs | `engine/jobs.py` | What a job **does**. Trust over README. |
| Yu search | `engine/yu_pool.py` | Gate, process, certify, R4_LOWER. |
| C MIS | `engine/kernels/native_mis.c` | n≤256 axiom. |
| Python MIS | `engine/kernels/bitset_mcs.py` | skip_n>256 after greedy. |
| Residual | `engine/kernels/residual.py` | No dense p/2 matrix. |
| Scale | `engine/scale.py` | local vs runpod knobs. |
| Ownership | `engine/registry.py` | Cells; upsert ledger. |
| Old MCS | `engine/kernels/mcs.py` | Do not use for n>64 cert. |
| Yu S | `data/yu_r4_20.json` | Undirected published witness. |
| Campaign | `docs/A40-CAMPAIGN.md` | What the A40 proved/did not. |
| Plan v2 | `docs/plan-move-a-number.md` | Why 4a looks like this. |
| This file | `docs/SESSION-HANDOFF.md` | Session memory. |
| README banner | `README.md` top | Public retraction sentence. |
| Small catalog | `data/catalog.json` (+ public/ + src/) | Dashboard fixture. **Not 2a.** |
| A40 2a catalog | `data/a40/catalog-2a.json` | ~9288 Hoffman rows. |
| A40 4abc catalog | `data/a40/catalog-4abc.json` | Yu + false 337/353 + 4c. |
| A40 registry | `data/a40/registry.jsonl` | 4a checkpoints + emits + 4c. **Check size** vs older 2.3 MB 2a+3d registry on Downloads. |
| A40 ledger | `data/a40/bound_ledger.json` | Statements; some diagonal-shaped. |
| Mac snapshot | `~/Downloads/Ramsey-GPU-Constructions/` | Files; no git. |
| Mac clone | `~/ramsey-gpu-constructions` | Dual remotes. |
| Pod path | `/workspace/ramsey-gpu-constructions` | Stale after Stop; do not Terminate. |
| Dashboard | port 43123 | Bundled small catalog. |
| Tests | `engine/test_kernels.py` | Includes n>256 lie test. |

---

## 6. Job queue (operational) — **closed**

```
DONE on A40:  1a 1b 1c 1d 2a 2c 3a 3b 3c 3d(n=13,14) 4a 4b 4c
SKIP:         2b
DEAD SESSIONS: tmux ramsey (2a leftover), ramsey4 (gone)
POD:          Stop OK. Do not Terminate.
NEXT CODE:    wider MIS or denser-S 4a; 4b middle-third seed; graph_id+S hash
NEXT PUBLISH: already on GitHub README + docs/A40-CAMPAIGN.md
```

Do **not** restart phase4 on the old `.so` without pulling the n>256 fix.

---

## 7. Questions for a new LLM session

Paste this file plus `docs/A40-CAMPAIGN.md` and `docs/plan-move-a-number.md`.
Do not re-litigate #78 unless the user asks.

### 7.1 Immediate operations
1. Has the A40 been **Stopped** (good) or **Terminated** (volume gone)?
2. What is the current RunPod SSH IP/port if anything must still be copied?
3. Does `data/a40/registry.jsonl` include 2a+3d, or only the 4abc scp (37 KB)? Where is the 2.3 MB registry?
4. Is `~/ramsey-gpu-constructions` still the dual-remote clone, and are `origin`/`github` both at the same SHA as GitHub HEAD?
5. Should anyone still attach tmux `ramsey`? (Default: no.)
6. Idle cost: is the pod still billing?

### 7.2 Scientific priority (do not reopen CELL?)
7. Confirm in code+catalog: residuals 262 and 264, exact must be treated as **false**. Has the user announced 354 anywhere else (social, issues)?
8. Is the next success criterion still Radziszowski +1, or is the session closed as a negative result?
9. Widen MIS to n≤320 / SAT, or force |S| high enough that residual≤256, or stop hunting \(R(4,20)\)?
10. Recertify Yu’s residual α=19 with a second solver before any new hunt?
11. Is Paley(17) still the dashboard jewel, or do we hide spectral \(N^{1/k}\) for N>64?
12. Erdős #78 in scope? (Default: no.) PPO? (Default: no.)

### 7.3 Certificate hygiene
13. Stop emitting Yu p=251 as `exact=True` unless `alpha_certified`?
14. Fix ledger statements so off-diagonal cells are `R(4,t)>N` not `R(k,k)>N`?
15. Put i,j and a hash of S into `graph_id` so 353 hits do not collide?
16. Independent checker (second language) for any future `CELL?`?
17. Property test: random n=257 empty / complete graphs must never be exact-accept?
18. Should `CELL?` require residual_n logged on the same line?

### 7.4 Kernel work if continuing
19. WORDS=5–8 vs SAT vs linking a known Cliquer/MoMC?
20. Validate C node counts on Paley(17) and a known residual with α=2,3?
21. Mixed IS in \(N(0)\cup\) residual: prove \(\alpha(G)=1+\alpha(\mathrm{residual})\) for this family, or bound both sides?
22. KaMIS / colour bound before BnB on 186–256?
23. Incremental eigenvalue ILS — still irrelevant if Hoffman is banned?
24. GPU batched legality for 4a walks — worth it when 4a was 29 min CPU?

### 7.5 Job 4a/4b/4c redesign
25. Rerun 4a with the fix only to prove “0 exact hits” on the same seed 20260829?
26. Change t_cell policy so p=353 hunts \(R(4,21)\) or \(R(4,23)\), not a fake 20-cell?
27. 4b: seed middle-third sum-free; more than 80 steps; residual cap vs n=700?
28. 4c: q=8 leftover size — skip or SAT?
29. Keep `phase4` as one process or split so 4a failure cannot be confused with 4c success?
30. Log every MIS `{n, target, found, timed_out, backend, residual}` to jsonl.

### 7.6 Catalogue / dashboard
31. Should the dashboard grow a second “A40 2a” page, or stay on 263 locals?
32. How to join 2a registry + 4a registry without graph_id collisions?
33. `catalog-2a.json` vs live `data/catalog.json` — which does `npm run dev` read?
34. Strip Hoffman \(N^{1/k}\) from the hero chart?

### 7.7 Provenance / git
35. After this hand-off commit, did the user `fetch origin && merge && push github`?
36. Are there uncommitted Mac-only files in Downloads that are not in `data/a40/`?
37. Origin Internal vs GitHub Public: any secret (Jupyter token, SSH) still in git history?
38. Should `native_mis.so` stay gitignored on all machines?

### 7.8 Literature / claims
39. Allowed README sentence on C≥1.01? (“these families do not.”)
40. Cite Yu as “already achieved; we recertify / search nearby” not “3B target we might hit first”?
41. Refresh R4_LOWER from DS1 r18 + any post-Yu notes before the next hunt?
42. AlphaEvolve families as 4b seeds only?

### 7.9 Process / reliability
43. Pod wrapper: `tmux new -s JOB` *inside a script* so users cannot paste two lines?
44. Checkpoint 2a-style jobs (last p) even though 2a is done?
45. Heartbeat `data/heartbeat.json`?
46. Refuse to start 4a if `native_mis.so` mtime < `native_mis.c`?
47. Print residual size **before** MIS on every candidate?

### 7.10 Do not spend the first hour on
48. Re-deriving Paley spectrum.
49. Re-arguing Hoffman vs Lovász \(\vartheta\).
50. A second app / auth / database.
51. Training a GNN to escape Paley.
52. Extractor graphs at \(N=2^{20}\).
53. Enumerating \(\binom{50}{32}\).
54. Creating a PR unless asked.
55. Making Origin Public (impossible).
56. Re-running 2a.
57. Re-attaching `ramsey` / `ramsey4`.
58. Announcing \(R(4,20)\ge 338\) or \(354\).

### 7.11 Closure questions (for the human)
59. Is the public negative result the intended end of this wave?
60. If they want a number, will they fund a solver that can decide n=186 in seconds, or accept that this A40 cannot?
61. One sentence of *session success* from the user now that +1 failed — catalogue? retraction? both?

---

## 8. Suggested first prompt for the next session

> You are continuing `ramsey-gpu-constructions`. Read
> `docs/SESSION-HANDOFF.md`, `docs/A40-CAMPAIGN.md`, and
> `docs/plan-move-a-number.md`. Do not re-solve Erdős #78. Do not treat
> 4a `CELL? R(4,20)≥354` as a theorem: residuals 262/264 exceeded the
> C MIS n≤256 contract; that lie is fixed on `main`. Public GitHub
> `pageman/ramsey-gpu-constructions` and Cursor Origin should both have
> the README banner and `data/a40/`. A40 pod may be Stopped; never
> Terminate.  
> First: confirm GitHub HEAD states the retraction. Then say whether
> the next work is (A) close the wave, (B) recertify Yu α=19 with a
> real solver, or (C) rerun 4a with residual>256 refused and a denser-S
> or wider bitset. I will paste `git log -1` / catalog snippets if needed.

---

## 9. Chronology (UTC 2026)

| When | Event |
|---|---|
| 27 Aug | Empty repo → engine + dashboard; local 263; Origin + GitHub. |
| 27 Aug evening | A40: 1a–1d; 2a started. |
| 27 Aug ~20:23 | Ceiling + Erdős literature. Quest → Radziszowski. |
| 27 Aug 22:48+ | Plan v1 `docs/plan-move-a-number.md`. |
| 28 Aug 00:17 | 2c during 2a SIGTSTP. |
| 28 Aug 01:01 | 2a death p=5347. |
| 28 Aug 12:02–12:08 | tmux; 2a restart p=13. |
| 28 Aug later | 2a **done** 99755 s / 9288 graphs. |
| 29 Aug | Plan v2 from A40 negatives. 3d visibility; 3d hangs/dies n=13/14. |
| 29 Aug | Jobs 4a/4b/4c implemented; Yu json; C MIS; tarball to pod. |
| 29 Aug 22:33+ | Pod idle; 3d dead. GitHub still `a49da0c`. |
| 29 Aug 23:22 | `native_mis.so` on pod. |
| 29 Aug 23:24 | phase4 starts (eventually in `ramsey4` / pts/3). |
| 29 Aug 23:50–23:53 | False 353 emits; 4b 8.56 s; 4c 1.58 s. |
| 30 Aug ~03:48 | User pastes 4b/4c done. |
| 30 Aug ~03:56 | Catalog residuals 186 / 262 / 264. Retraction. |
| 30 Aug ~04:01 | scp 4abc data to Mac. |
| 30 Aug ~04:08 | Mac merge + `data/a40/` + `git push github` `2b13b8f`. |
| 30 Aug ~04:09 | `git push origin main` (Cursor = GitHub). |
| 30 Aug ~04:11 | README banner `18d2aeb` on GitHub. |
| 30 Aug ~04:13 | This hand-off rewritten. |

---

## 10. One-screen warning for the next model

If the user pastes `CELL? R(4,20) ≥ 354`, you say **no**. If they paste
tmux on a Mac prompt, you say **wrong machine**. If they paste `scp`
with angle brackets on `root@3631e8…`, you say **wrong machine**. If
they want Origin made Public, you say **impossible**. If they want #78,
you say **out of scope**. If they want a new hunt without a solver that
can decide a 186-vertex residual, you say **the last hunt already
showed the certificate is the bottleneck**.
