# Job 3d — ANF Search Closeout (n=13,14 only; hung on max_clique)

Campaign: A40 `armed_yellow_buzzard`, 28 Aug 2026.

**Status: Abandoned as cell-hunt aisle.** Job 3d placed n=13,14 ANF quadratic
graphs into the registry, then hung on the old `max_clique` path (no timeout,
100% CPU on one core). Do not reopen `--job 3d` overnight.

---

## What 3d Was Supposed to Do

Algebraic normal form (ANF) quadratic Cayley graphs over F₂ⁿ:

- Boolean quadratic Q: F₂ⁿ → F₂
- Adjacency: edge (x,y) ⇔ Q(x ⊕ y) = 1
- Parameters: n ∈ {13,14,15,16}, enumerate nondegenerate forms
- Spectral Hoffman + optional exact ω if residual fits
- Cell: R(4,t) off-diagonal

**Scale intent:** n=13→N=8192, n=14→N=16384. FWHT eigenvalues. Exact MCS only
if cheap.

---

## What Actually Happened

1. **n=13, n=14 registered:** Some ANF graphs entered
   `data/a40/registry.jsonl` (or an earlier 2a-era registry on Mac Downloads).
2. **Hung on old colouring:** The `engine/kernels/mcs.py` path for n>64 used a
   **degeneracy colour bound** with no wall-clock timeout. One quadratic form
   at n=14 or n=15 hit a dense subgraph; the colour loop never returned.
3. **Operator aborted:** After observing 100% CPU on one core, GPU idle, and no
   log progress, the job was killed. Catalog mtime stayed at 2a (no
   `write_catalog` from 3d).
4. **No n=15,16 reached.**

---

## Negative Theorem

ANF n=13,14 are **catalogue entries** (they exist, some have decent Hoffman
bounds), **not** R(4,t) cell machines at this campaign's scale.

- The old MCS (n>64 subsample + greedy colour) cannot certify a 186-vertex Yu
  residual and is even less useful at N≈8k–16k.
- Spectral Hoffman on N=8192 is a *pessimistic bound*, not a +1.
- If a form yields ω=α=k (diagonal), it is a real construction. If it yields
  loose Hoffman, it is not Erdős #78.

3d proves that **hunting cells in ANF at n≥13 requires a decision α≤t−1**, not
a Hoffman rank. The catalogue can hold these graphs; a night hunt should not
wait on a colour loop.

---

## Operator Rules (Do Not Regress)

1. **Do not reopen `--job 3d` as a night aisle** without a wall-clock timeout
   on MCS or a decision-MIS gate.
2. **Do not claim ANF n=16 FWHT as Erdős progress.** Spectral k inflates; large
   N with loose bounds is not C≥1.01.
3. **ANF n=13,14 can stay in the catalog** as algebraic constructions. They are
   not survey cells.
4. **If you want exact ω on n=13,14 leftovers**, call the fixed
   `bitset_mcs.residual_alpha` with a timeout, or link Cliquer. Do not hang on
   the 64-core subsample again.

---

## Fix (Already on main)

The decision-MIS infrastructure (`decide_alpha_le`, `c-decide`) now exists for
n≤256 and has a mandatory timeout. Job 3d predates that. A future ANF job
could:

- Enumerate forms at n=13,14 (fast)
- Filter: K₄-free (FWHT triangle count)
- Greedy α
- For each open t with n+1 > R4_LOWER[t]:
  - `decide_alpha_le(full_adj, target=t, limit=30)` on the full graph
  - residual_accept → mixed-set → `CELL?`
  - timeout → skip

This would be a **new job** (call it `3d2` or `1e`), not a rerun of the
original 3d.

---

## Artifacts

- **Registry:** n=13,14 rows live in the **2a-era registry** on Mac
  `~/Downloads/...` or `data/a40/registry.jsonl` (check both; 2a registry was
  ~2.3 MB, 4abc registry is 37 KB).
- **No 3d-specific dumps** under `data/a40/` or `data/phase3/`.
- **Catalog:** `data/a40/catalog-4abc.json` has 270 rows total; check for
  `"construction_type": "anf_quadratic"` or similar (catalog mtime stayed 2a,
  so 3d may not have updated it).

---

## Scientific Closeout

- **No published +1.** R(4,20)≥252 (Yu) unchanged.
- n=13,14 ANF graphs: **catalogue** status (algebraic constructions exist).
- **Not a cell-hunt aisle** without timeout-safe exact MCS or decision-MIS.
- **Do not reopen 3d night.** If you want ANF at n≥13, design a new job with
  the fixed decision referee, not the old unbounded colour loop.

Job 3d's lesson: *Hoffman on large N is not the objective.* The survey
instrument is a **decision oracle** on a finished construction, not a spectral
ranker on an enumeration that never completes.

---

## See Also

- `docs/A40-CAMPAIGN.md` — full campaign scoreboard
- `docs/SESSION-HANDOFF.md` — operations drama (§S34, S41a)
- `engine/constructions.py` — ANF quadratic builder (still exists, unused)
- `engine/kernels/mcs.py` — old n>64 path (do not use for cert)
- `engine/kernels/decide_alpha.py` — fixed decision-MIS (use this)
- `README.md` — A40 scoreboard: "3d: ANF n=13,14; hung on old max_clique"

**Do not wait on the colour loop overnight.**
