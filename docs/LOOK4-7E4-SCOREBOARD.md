# Look 4 (7e4 Two-Block CEGIS) Instrument-Negative Scoreboard

**Updated:** 2026-09-15  
**Repository tip:** `e95d67d` (PR #14 — Track A negative scoreboard merge; PR #13 was `3853007` for guided-repair code)  
**Published cell:** R(4,20) ≥ 252 (Yu), R(4,21) ≥ 252 (Yu)

---

## Status: INSTRUMENT-NEGATIVE

**Track A (Guided IS-repair)** closed as **instrument-negative** for best known warms (m126_r9, m128_r6).

Guided search correctly explores singles→pairs→optional hill-climb, but every single cut-lit flip from best warms destroys K₄-freeness. Sampled cross-cut pairs also 0 K₄-free. Repair returns None; cold CEGIS unchanged.

---

## Context

Job 7e4 performs CP-SAT CEGIS on two-block circulants (n=2m) with leftover-IS cuts. After warm-start seed-first evaluation and IS-cuts (PRs #2–#11), cold CEGIS rounds often hit:
- Triangle-repair cap (TRI_FIX exhausted without reaching K4_free)
- Greedy-α≈m nogood (full-graph greedy α≥t)
- IS-cuts saturate at cap (20 per m)

**Hypothesis (Track A):** Warm-start basin retention insufficient because IS-cuts reject the seed but subsequent cold SAT returns assignments far from the K4_free basin. A surgical local-search repair starting from warm bits and flipping only cut-lit participants might stay K4_free while satisfying cuts.

**Implementation (PR #13):** After seed-first extracts an IS I and adds the IS-cut, attempt IS-directed repair:
1. Start from warm free-bits
2. Identify cut literals (distances that hit I)
3. For each cut-lit: try flipping it (single)
4. If no single K4_free: try cross-cut pairs (cut-lit × cut-lit)
5. If hill-climb enabled: random walk from best single/pair
6. If successful: use repaired bits as hint for cold CEGIS

**Objective:** Leave the rejected seed's neighborhood surgically (satisfy the cut) while staying K4_free, rather than cold SAT jumping to distant greedy-dead assignments.

---

## Track A Result: Instrument-Negative

### Mac Smoke Test (2026-09-15)

**Command:**
```bash
RAMSEY_7E4_M=126,128 RAMSEY_7E4_WARM=1 RAMSEY_7E4_WARM_RADIUS=0 \
  RAMSEY_7E4_ROUNDS=6 RAMSEY_7E4_TRI_FIX=16 RAMSEY_7E4_CUTS=8 \
  RAMSEY_7E4_REPAIR_HILLCLIMB=30 python3.11 -m engine.cli --job 7e4
```

**Warms used:**
- **m=126 (n=252):** warm m126_r9 (K4_free=True, greedyα=9)
- **m=128 (n=256):** warm m128_r6 (K4_free=True, greedyα=5)

**Result:** Both printed `IS-REPAIR failed`, cold CEGIS returned to triangle-repair cap / MODEL_INVALID / greedy-α≈m nogood. No graphs emitted (`graphs=0`). Cell remains 252.

### Diagnostic

Extracted full IS graphs via `extract_is_full_graph` and computed cut-lit sets via `is_cut_two_block_lits`:

| Warm | Union |cut_lits| | K4-free singles | Cross-cut pairs sampled | K4-free pairs |
|---|---|---|---|---|
| m126_r9 | 62 | 0/62 | 15×15 = 225 | 0/225 |
| m128_r6 | 63 | 0/63 | 15×15 = 225 | 0/225 |

**Interpretation:**
- Every single cut-lit flip from the warm assignment produces a NOT K4-free graph
- Every sampled cross-cut pair (two cut-lit flips) also NOT K4-free
- Hill-climb (30 rounds) from these broken states also failed to recover K4_free
- The warm basin's K4-freeness is destroyed by any local perturbation that satisfies the IS-cut

**Unit tests:** All 7 tests in `engine/test_warm_repair.py` pass. Repair logic is correct; landscape is the obstacle.

**Log:** Saved locally as `logs/wave-c/wave-c-smoke-guided-repair-3853007.log` (may not be in repo).

---

## Warm Table

Best K4-free warms from job 7e.1 (multi-t decide, priority t=20,21):

| m | n | restart | K4_free | greedy_α | decide t=20 | decide t=21 | IS-repair (PR #13) |
|---|---|---|---|---|---|---|---|
| 126 | 252 | 9 | True | 9 | found=True | found=True | 0/62 singles K4-free, 0/225 pairs K4-free |
| 128 | 256 | 6 | True | 5 | found=True | found=True | 0/63 singles K4-free, 0/225 pairs K4-free |

Notes:
- **found=True** means decide extracted a t-IS on full graph (reject); these warms do not witness α<t
- **IS-repair result:** Guided search correctly explores cut-lits but finds no K4-free flip; repair returns None

---

## Reopen Criteria (Updated 2026-09-15)

Original reopen criteria (pre-Track A):
1. Guided IS-repair from warm (surgical flip of cut-lits only) — **CLOSED as instrument-negative for these warms**
2. New warm with t=20 found=False and residual accept (full-graph α<20) — **still open**
3. New instrument: true two-orbit local search beyond cut-lit flips (e.g., structured neighbor enumeration, not another TRI_FIX–AddHint sweep) — **still open**

**Status after Track A:**
- Criterion (1) is **closed** for m126_r9 and m128_r6 (best known K4-free warms at n=252,256)
- Criterion (2) remains open: if job 7e.1 (or another generator) produces a new dump with found=False (decide residual-accept), that warm does not need IS-repair
- Criterion (3) remains open: a fundamentally different local-search instrument (not cut-lit flips) might escape the greedy-dead basin

**Next action:** Do **not** schedule Wave D (overnight pod with current warms + guided repair). Next increment must be:
- A new warm (7e.1 continuation, different ILS, or another m) with decide found=False, **or**
- A new instrument (e.g., structured two-orbit neighbor enumeration, block-circulant SAT as in Wesley 2024/2025, or Coniglio-style IP on two-block pools), **or**
- A different Look (1, 2, 3, 5, or 6 from WHERE-TO-LOOK.md)

Wave D (GPU overnight with current method + current warms) is **not recommended** given Track A instrument-negative result.

---

## Pull Requests (Through PR #14)

- **PR #2:** Scaffolding + lazy triangle CEGIS + degree LB + sharp IS-cuts
- **PR #3:** Stronger degree LB + greedy nogood + local M≥101
- **PR #4:** Warm-start from 7e1 dumps + TRI_FIX cap raised
- **PR #5:** Seed-first warm round (evaluate warm before cold SAT)
- **PR #6:** Fix AddHint API (ortools 9.15)
- **PR #7:** Seed-first reject installs IS-cut
- **PR #8:** Seed-cut only primary t (20,21) + local cuts cap 5→10
- **PR #9:** Public docs update for session 2026-09-12/13
- **PR #10:** Retain warm hints throughout CEGIS (basin retention)
- **PR #11:** IS-directed local repair + WARM_RADIUS constraint + MODEL_INVALID fix
- **PR #12:** (if any — check git log)
- **PR #13:** Replace random IS-repair with guided search (singles→pairs→hill-climb) — **instrument-negative on best warms**
- **PR #14:** Track A negative scoreboard (update scoreboard after PR #13 Mac smoke result)

---

## References

- Job contract: [JOB-7E4.md](JOB-7E4.md)
- Waves A–E plan: [JOB-7E4-PLAN.md](JOB-7E4-PLAN.md)
- Session note: [SESSION-2026-09-13.md](SESSION-2026-09-13.md)
- Where to look: [WHERE-TO-LOOK.md](WHERE-TO-LOOK.md)
- Campaign: [PHASE7-CAMPAIGN.md](PHASE7-CAMPAIGN.md)

---

## Scientific Conclusion

Guided IS-repair (Track A) is **not** a viable instrument for escaping the warm-basin rejection at m=126,128 given current best warms (m126_r9, m128_r6). The K4-free landscape near these warms is such that any cut-lit flip (single or sampled pairs) destroys K4-freeness. Hill-climb from broken states also fails.

**Implication:** The obstruction is not "repair search is unguided" but "the warm basin's K4-free neighborhood is disconnected from assignments that satisfy the IS-cut." A different instrument (new warm generator, different local-search structure, or SAT/IP on connection sets) is required.

**Cell unchanged:** R(4,20) ≥ 252 (Yu).
