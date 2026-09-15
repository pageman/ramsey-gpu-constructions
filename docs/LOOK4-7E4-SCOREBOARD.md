# Look 4 / Job 7e.4 Wave C — Instrument-Negative Scoreboard

Date: **2026-09-14**  
Tip: **~397b4c7** (PR #11, Wave C stack on main)  
Device: **Mac** local smoke only  
Status: **INSTRUMENT_NEGATIVE** — R(4,20)≥252 unchanged. **No CELL?**.

---

## Verdict

**Instrument-negative** under the 7e.1→7e.4 Wave C stack (seed-first, IS-cuts, AddHint, WARM_RADIUS, random IS-REPAIR, MODEL_INVALID rebuild). **Not a proof** that R(4,20)=252.

Wave C local smoke (m=126, WARM=1) validates wiring:
- Seed-first warm round loads 7e.1 dumps
- Multi-t decide runs (priority t=20,21)
- IS-cuts fire when seed-first rejects
- Cold CEGIS rounds continue after warm

**No CELL?** produced. Cold CEGIS mostly hits:
- **Triangle-repair cap** (TRI_FIX exhausted), or
- **Greedy-α≈126 nogood** (full-graph α ≥ greedy α ≥ 126, reject)

---

## Warm Table (All K₄-free, Decide Outcomes)

| Warm seed | greedy_α | t | found | Notes |
|---|---|---|---|---|
| m126_r9 | 9 | 20 | True | IS-REPAIR fail; tri-cap; MODEL_INVALID churn |
| m126_r6 | 18 | 20 | True | — |
| m126_r15 | 20 | — | — | — |
| m128_r6 | 5 | 20 | True | IS-REPAIR fail (RADIUS 15 and 0) |
| m128_r12 | 10 | 20 | True | — |
| m128_r15 | 13 | 20 | True | — |
| m128_r3 | 16 | 20 | True | — |

**All** warms are K₄-free. **All** decided warms with t=20 had found=True (reject: full-graph α≥t). Obstruction from 7e.1 persists: K₄-free graphs with low greedy α can still have full-graph α≥t.

---

## Smoke Logs

Local validation artifacts under `data/phase7/7e4/`:
- `wave-c-smoke-m126-isrepair` — m=126 WARM=1, IS-REPAIR failures
- `m128-warm-r15` — m=128 r=15 decide
- `m128-warm-r0` — m=128 r=0 IS-REPAIR RADIUS test
- `m126-128-warm` — multi-seed warm round summary

---

## Do-Nots

1. **Do not raise 6a** (CP-SAT unsat-19 timeout is negative, not a gate)
2. **Do not reopen 7c / 7c1** (leftover-IS CEGIS already ran; 181 pools, 13935 cuts, 0 graphs)
3. **Do not start Wave D** until reopen criteria met

---

## Reopen Criteria (Wave D Unblocked When)

Wave D overnight pod is blocked until **any one** of:

1. **Guided IS-repair** yields a K₄-free cut-satisfying neighbor **and** cold decide finds found=False at t=20, **or**
2. **New warm** with found=False at t=20 (escape the obstruction), **or**
3. **New instrument** (not another Wave C parameter sweep)

Warm-basin retention open: keep AddHint diversity, TRI_FIX diversity, or neighborhood bias to preserve K₄-free low-greedy-α basin.

---

## See Also

- `docs/JOB-7E4.md` — operator guide (runpod defaults, environment knobs)
- `docs/JOB-7E4-PLAN.md` — Wave A–D roadmap
- `docs/WHERE-TO-LOOK.md` — next ≠ Wave D (§3, queue item 5)
- PRs #2–#8 — Wave A–C merges (triangle repair, warm-start, seed-first, IS-cuts)
- `data/phase7/7e1/` — 7e.1 warm-start dumps (multi-t decide seeds)

**Next action:** Guided IS-repair or new instrument validation. Do not schedule Wave D pod without an escape from the greedy-α≈126 obstruction.
