# Job 7e1: Two-Orbit Search (200≤n≤256)

## Overview

Job `7e1` is a **standalone CLI job** (not in the `phase7` loop) that searches for K4-free two-orbit graphs on 200≤n≤256 vertices using minimal ILS and decides **all open t values** with priority on t=20,21.

**Key principle**: Decide every open t, not just t=17. Target=t (NOT t-1).

## Smoke Run Finding (A100)

Initial smoke run revealed that using only `open_t[0]` (t=17) was insufficient:

- **m=126 n=252**: K4_free=True, greedyα=9, decide t=17 found=True (reject)
- **m=127 n=254**: K4_free=False
- **m=128 n=256**: K4_free=True, greedyα=5, decide t=17 found=True (reject)
- **Result**: 0 CELL? candidates

### The t=17 Calibration Caveat

**Problem**: Using only t=17 proves α≥17, NOT whether α≤19 (the 253 question).

For n=252, open cells are t ∈ {17,18,19,20,21}. Deciding only t=17 with found=True means there exists a 17-IS, but says nothing about whether α<20 (which would beat the published R(4,20)≥252 floor).

**Fix**: Decide **all** open t values, prioritizing t=20,21 first, then remaining ascending.

## What It Does

1. **Multi-restart search**: Run `restarts_per_m` restarts per m value
2. **Seed families**: Three seeding strategies per restart cycle:
   - `roll`: Paley or alternating base, rolled by restart offset
   - `random_density`: Random inversion-closed with densities {0.25, 0.33, 0.40}
   - `sparse_s1`: Sparse S1 (≤0.15 density) with denser S0 (0.35)
3. **Minimal ILS**: Greedy K4-free flip (NOT stock `ils_two_block` with k_clique=5)
4. **Decide all open t**: 
   - Prioritize t ∈ {20,21} first, then remaining open t ascending
   - For each t: `decide_alpha_le(nbr, target=t, ...)` on full-graph adjacency
   - Extract and persist IS witnesses when found=True
5. **Persistence**: Write JSON dumps to `data/phase7/7e1/m{m}_r{restart}.json` with:
   - Seed vectors (s0, s1)
   - K4-free status
   - Greedy alpha
   - Decision results for each t (found, timeout, exact, witness)
   - Mixed-set result (if residual-accept path reached)

## Environment Variables

- **`RAMSEY_7E1_M`**: Focus on specific m values (comma-separated)
  - Example: `RAMSEY_7E1_M="126,128"` skips m=127
  - Default: `"126,127,128"` on RunPod, `"127"` locally

- **`RAMSEY_7E1_RESTARTS`**: Restarts per m value (default: 20 RunPod, 4 local)

- **`RAMSEY_7E1_STEPS`**: ILS steps per restart (default: 120 RunPod, 24 local)

- **`RAMSEY_YU_MIS_LIMIT`**: Decide time limit per t (default from limits)

- **`RAMSEY_FORCE_7`**: Override halt-file (set to `"1"` to run despite halt)

## Running Job 7e1

### Default (RunPod P0 night)
```bash
python3 -m engine.cli --job 7e1
```

### Focus on m=126,128 with deeper search
```bash
RAMSEY_7E1_M="126,128" RAMSEY_7E1_RESTARTS=30 RAMSEY_7E1_STEPS=200 python3 -m engine.cli --job 7e1
```

### Local smoke test
```bash
RAMSEY_SCALE=local RAMSEY_7E1_RESTARTS=2 RAMSEY_7E1_STEPS=16 python3 -m engine.cli --job 7e1
```

## Reading the Dumps

Dumps are written to `data/phase7/7e1/m{m}_r{restart}.json`:

```json
{
  "m": 126,
  "n": 252,
  "restart": 0,
  "seed_family": "roll",
  "s0": [0, 1, 1, 0, ...],
  "s1": [0, 0, 1, 1, ...],
  "k4_free": true,
  "greedy_alpha": 9,
  "open_t": [20, 21, 17, 18, 19],
  "decisions": {
    "20": {
      "found": false,
      "timed_out": false,
      "exact": true,
      "backend": "decide",
      "nodes": 1234567,
      "seconds": 45.2,
      "residual_accept": true,
      "witness": null
    },
    "21": {
      "found": true,
      "timed_out": false,
      "exact": false,
      "witness": [0, 3, 7, 11, 19, 23, ...]
    },
    ...
  },
  "best_residual_accept_t": 20,
  "mixed_ok": false,
  "mixed_reason": "residual α≤18<19 — not residual-only α=19 accept"
}
```

### Key Fields

- **`k4_free`**: Whether the graph is K4-free (required for R(4,t))
- **`greedy_alpha`**: Greedy MIS lower bound (used to filter open t)
- **`open_t`**: Prioritized list of t values decided (20,21 first)
- **`decisions[t]`**: Per-t decision results
  - `found`: True if a t-IS was found (reject for α<t)
  - `residual_accept`: True if α<t proven (not found, not timeout, exact)
  - `witness`: IS vertex list if found=True (for verification)
- **`best_residual_accept_t`**: Smallest t with residual-accept (or null)
- **`mixed_ok`**: Whether mixed-set check passed (CELL? gate)

### Interpreting Results

1. **REJECT (found=True)**: A t-IS exists, so α≥t. Does NOT prove α<t.
2. **residual-accept**: α<t proven. Check `mixed_ok` for CELL? eligibility.
3. **TIMEOUT**: Inconclusive. Timeout ≠ accept.
4. **CELL? candidate**: `residual_accept=True` AND `mixed_ok=True` AND n+1 beats published floor.

## Do NOT Treat t=17 Reject as 7c1-Style Cut

**Important**: A t=17 reject (found=True) means α≥17, NOT that there's a leftover-19 IS to cut on.

- **7c1 cuts** are on residual 19-IS when target was 20 (to exclude that specific S)
- **7e1 t=17 reject** just means the graph is not α<17; it might still be α<20

Do not attempt to extract a "cut" from a t=17 found=True result. If you want to exclude this graph, record it as a restart failure and continue searching.

## Mixed-Set Two-Block Note

The current `mixed_set_check` via `adj[0]` row is **imperfect for two-block graphs**. The full-graph mixed-set requires reasoning about both orbits, not just the circulant structure of the first block.

**TODO**: Implement two-block-aware mixed-set or document as preliminary/skip for two-orbit.

For now: treat `mixed_ok` as a preliminary filter. A `mixed_ok=False` on two-orbit should be noted as "residual_only (two-block mixed-set imperfect)" rather than a hard CELL? rejection.

## Example Log Output

```
  [7e1] === m=126 n=252 ===
  [7e1] m=126 restart 1/20 family=roll
      step 1/120 greedyα=10 (improvement)
      step 41/120 greedyα=9 (improvement)
  [7e1] restart 1 K4_free=True greedyα=9
  [7e1] open_t=[17, 18, 19, 20, 21] prioritized=[20, 21, 17, 18, 19]
  [7e1]   decide t=20 (published≥252) α<20…
  [7e1]   t=20 found=False timeout=False exact=True backend=decide nodes=2345678
  [7e1]   t=20 residual-accept (α<20 proven)
  [7e1]   decide t=21 (published≥252) α<21…
  [7e1]   t=21 found=True timeout=False exact=False backend=decide nodes=123456
  [7e1]   t=21 witness: greedy |I|=21
  [7e1]   t=21 REJECT (found 21-IS)
  [7e1]   mixed_set t=20 residual α≤18<19 — not residual-only α=19 accept mixed_ok=False
  [7e1]   NOTE: two-block mixed_set via adj[0] is imperfect; treat as preliminary
  [7e1]   residual_only n=252 t=20  residual α≤18<19  not CELL?
  [7e1]   wrote data/phase7/7e1/m126_r0.json
```

## See Also

- `engine/phase7.py`: Implementation of job_7e1
- `docs/JOB-6A-BAKEOFF.md`: Second-solver bake-off gate
- `docs/JOB-PHASE7.md`: Phase 7 look structure
- `WHERE-TO-LOOK.md`: Campaign ordering
