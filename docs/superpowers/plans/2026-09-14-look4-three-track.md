# Look 4 Three-Track Plan (2026-09-14)

**Context:** Job 7e.4 Wave C (PRs #2–#8) merged to main (~397b4c7). Local smoke validates wiring. All warms K₄-free; all t=20 decides found=True (reject). No CELL?.

---

## Three Tracks

### Track A — Guided IS-Repair
**Goal:** Escape greedy-α≈126 obstruction via guided IS-repair to find K₄-free cut-satisfying neighbor, then cold decide.

**Status:** Open (not yet implemented).

**Gate:** Found=False at t=20 after repair, or abandon.

---

### Track B — Exhaust Warm Basin
**Goal:** Test remaining 7e.1 dumps (m=126,128 other radii).

**Status:** **Exhausted** (2026-09-14). All tested warms: K₄-free + found=True at t=20.

**Outcome:** Obstruction persists across warm seeds.

---

### Track C — This Scoreboard
**Goal:** Document Wave C instrument-negative outcome.

**Status:** **Complete** (docs/LOOK4-7E4-SCOREBOARD.md, data/phase7/7e4-look4-scoreboard.json).

**Outcome:** R(4,20)≥252 unchanged. Wave D blocked on Track A or new instrument.

---

## Next

Track A (guided IS-repair) or new instrument validation before Wave D pod scheduling.
