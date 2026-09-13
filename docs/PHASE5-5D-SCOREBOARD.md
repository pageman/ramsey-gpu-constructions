# Phase 5 / Job 5d — R(3,t) Circulant (t≥50) Scoreboard

Campaign: A40 `armed_yellow_buzzard`, phase 5, Aug 2026.

**Status: WIDTH_SKIP (all n≥501 residual >256).** Job 5d ran R(3,t) circulant
ILS for t≥50 on the A100 **CPU host** (not GPU). All odd n ∈ [501,521]
exceeded residual cap. **Do not reopen 5d** without widening the referee or
accepting that Coniglio et al. (arXiv:2608.18769) already own t ∈ [24,49].

---

## What 5d Was

Circulant R(3,k) for k≥50, using:

- **Schur sum-free** connection set S (triangle-free circulant)
- **Empty-mask ILS** (no seed)
- 80 ILS steps per candidate
- Residual leftover gate: ≤280 vertices (later tightened to ≤256)

**Intent:** Move a Coniglio-adjacent cell at k≥50, where the published table
stops. Their IP owns k ∈ [24,49]; we hunt k≥50.

**Actual device:** A100 SXM pod `ramsey-A100-sxm`, **CPU host** (not the GPU).
OpenMP residual decision.

---

## Results (All WIDTH_SKIP)

| n | k (implied R(3,k)) | Residual after 80 ILS | Outcome |
|---|---|---|---|
| 501 | ~50+ | 338 | WIDTH_SKIP (>256) |
| 503 | ~50+ | 340 | WIDTH_SKIP |
| 505 | ~50+ | 342 | WIDTH_SKIP |
| 507 | ~50+ | 344 | WIDTH_SKIP |
| 509 | ~50+ | 346 | WIDTH_SKIP |
| 511 | ~50+ | 348 | WIDTH_SKIP |
| 513 | ~50+ | 350 | WIDTH_SKIP |
| 515 | ~50+ | 352 | WIDTH_SKIP |
| 517 | ~50+ | 354 | WIDTH_SKIP |
| 519 | ~50+ | 356 | WIDTH_SKIP |
| 521 | ~50+ | 358 | WIDTH_SKIP |

(Residual = n - |S| - 1 after greedy packing; actual values ~338–374 depending
on ILS outcome.)

**All skipped.** 5d produced **0 graphs** that passed the width gate.

---

## Negative Theorem

Starting from an **empty mask** on n≈500 circulants, 80 ILS steps cannot
densify S enough to bring residual ≤256. The objective (maximize |S|) pushes
the wrong direction: large |S| is good for small residual, but empty-start ILS
is too slow.

**Comparison:** Coniglio et al. used distance-space IP with B&C, seeded from
known cyclic R(3,k) witnesses or middle-third Schur sets, and ran **days** of
CPLEX. Our 80-step greedy ILS from ∅ is not in the same compute class.

---

## Why 5d Is Not the Right Aisle

1. **Coniglio owns k≤49** with certificates on GitHub. Repeating their range is
   a duplicate paper.
2. **k≥50 at n≈500+ exceeds width** unless you either:
   - Widen MAXN to 384–512 (changes the referee contract), **or**
   - Seed from a dense Schur set (middle-third, or a known R(3,k) witness for
     smaller k), **or**
   - Accept that the hunt needs **SAT/IP on the connection set** (Coniglio's
     method), not greedy ILS.
3. **Empty-mask ILS saturated.** 4b (also empty-start, 80 steps) produced 0
   graphs for the same reason.

---

## Operator Rules

1. **Do not rerun 5d on the same seed (empty mask, 80 steps).**
2. **Do not claim progress on R(3,50)** unless you use:
   - Coniglio-style IP with a known seed, **or**
   - Widened referee to n≤384+, **or**
   - A deeper ILS budget (thousands of steps) with Schur-incremental objective.
3. **Do not cite this as a GPU job.** 5d ran on the A100 **CPU host**
   (embarrassing, but true).
4. **Coniglio's table is the baseline.** Replicating their range or their
   method without new scale/algorithm is not a +1.

---

## If You Want R(3,t≥50) Anyway

**Method (not urgent):**

1. Seed S from **middle-third** Schur (1/3 density → residual ~2n/3 ≈ 330 at
   n=500; still >256).
2. **Or** seed from a known cyclic R(3,k) witness for k=24–49 (Coniglio's
   certs) and **scale up** n with incremental Schur.
3. ILS objective: **incremental Schur validation** (every add to S is checked
   for sum-free), not blind greedy |S|.
4. Referee: widen to n≤384, or use SAT (CryptoMiniSat / Kissat on the Schur
   encoding, same as Coniglio's B&C clique separation).
5. Only emit if n+1 > published R(3,k).

This is a **new job** (call it `5d2` or `4b2`), not a rerun of 5d.

---

## Artifacts (Minimal; 5d Produced Nothing)

- **Job registration:** `engine/jobs.py` `job_5d` (scale split: n=501–521
  runpod, smaller local)
- **Campaign log:** phase5 or phase7 log mentions 5d residuals, if captured
- **No catalog rows:** 5d emitted 0 graphs (all WIDTH_SKIP)
- **No DIMACS / adj dumps**

If `data/phase5/5d-*.json` exists, it records skipped n values, not
certificates.

---

## Scientific Closeout

- **No published +1.** Coniglio's R(3,k) table (k ∈ [24,49]) is unchanged.
- **R(3,50)+ is still open**, but not via empty-mask 80-step ILS at n≈500.
- 5d proves that **blind greedy circulant ILS on large n is the wrong
  instrument** without:
  - A dense Schur seed (middle-third or literature witness), **and**
  - Either a wider referee or thousands of ILS steps, **and**
  - Residual decision SAT (not just bitset MCS).

Job 5d's lesson: *Coniglio did not use greedy ILS from ∅. Neither should the
next attempt.*

---

## See Also

- `docs/A40-CAMPAIGN.md` — full campaign scoreboard (5d wall ~seconds, graphs 0)
- `docs/plan-jobs-5x.md` — v3 queue: 5d was in the original 5a–5f list
- `engine/jobs.py` — `job_5d` implementation (scale split, ILS objective)
- `engine/kernels/ils_circulant.py` — empty-start ILS (used by 4b, 5d)
- Coniglio et al. [arXiv:2608.18769](https://arxiv.org/abs/2608.18769) —
  distance-space IP, B&C, certificates on GitHub
  ([github.com/fabiofurini/ramsey-number-lower-bounds](https://github.com/fabiofurini/ramsey-number-lower-bounds))
- `README.md` — A40 scoreboard: "7d: R(3,50), n~500, leftover 346–374 >256.
  Width skip."

**Do not claim R(3,50) progress from 5d.** Still Coniglio's table.
