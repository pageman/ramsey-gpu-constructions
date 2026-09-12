# Job 6a: Second-Solver Bake-off (Yu Residual 186)

## Overview

Job `6a` runs a **second-solver bake-off** on the Yu residual (186 vertices) to independently verify that α < 19. This is the gate that authorizes phase 7 hunts.

**Key principle**: Timeout ≠ accept. Only a proven UNSAT or a completed search with no 19-IS counts as agreement.

## What It Does

1. Loads the Yu witness S from `data/yu_r4_20.json`
2. Builds the residual graph G[N^c(0)] (186 vertices)
3. Writes the complement as a DIMACS clique instance to `data/yu_r4_20.complement.clq`
4. Runs multiple independent solvers (if available):
   - **CP-SAT (OR-Tools)**: Attempts α ≥ 19 and α ≥ 18
   - **Cliquer**: Searches for a 19-clique in the complement (⇔ 19-IS in residual)
5. Writes results to:
   - `data/yu_r4_20.cert2.json` (full bake-off record)
   - `data/yu_r4_20.cert2.summary.json` (docs-friendly summary)

## Environment Variables

- **`RAMSEY_6A_LIMIT`**: Time limit in seconds for each solver (default: 180)
- **`RAMSEY_6A_BACKENDS`**: Comma-separated list of backends to run (default: `"cpsat,cliquer"`)
  - Valid values: `cpsat`, `cliquer`
  - Example: `RAMSEY_6A_BACKENDS="cpsat"` to run only CP-SAT

## Reading the Bake-off on RunPod

### Quick Check

```bash
python3 -m engine.cli --job 6a
# Look for:
#   [6a] wrote data/yu_r4_20.cert2.json  no_19_is=True  backend=ortools-cp-sat
```

If `no_19_is=True`, the hunt is authorized. If `False`, phase 7 will halt.

### Detailed Results

1. **Full record**: `data/yu_r4_20.cert2.json`
   - Contains all solver outputs, timings, and status codes
   - Fields: `cpsat_19`, `cpsat_18`, `cliquer_19`, `no_19_is`, `second_solver_agrees`, `backend`

2. **Summary**: `data/yu_r4_20.cert2.summary.json`
   - Human-readable version with conclusion and per-backend results
   - Look at `conclusion.no_19_is` and `conclusion.backend`

### Example Output

```json
{
  "conclusion": {
    "no_19_is": true,
    "second_solver_agrees": true,
    "backend": "ortools-cp-sat"
  },
  "backends_attempted": {
    "cpsat_alpha_19": {
      "available": true,
      "found_19_is": false,
      "unsat": true,
      "timed_out": false,
      "seconds": 47.3,
      "status": "INFEASIBLE"
    }
  }
}
```

## Agreement Logic

`second_solver_agrees` is `True` only if:

1. **CP-SAT reports INFEASIBLE** (proven no 19-IS) without timeout, OR
2. **Cliquer finishes** without finding a 19-clique and without timeout

A timeout, missing solver, or found 19-IS all result in `second_solver_agrees=False`, which halts phase 7.

## Troubleshooting

### No solvers available

```
[6a] no second solver installed. On the pod or Mac:  python3 -m pip install ortools
```

**Fix**: Install OR-Tools:
```bash
python3 -m pip install ortools
```

For Cliquer (optional), ensure the `cliquer` binary is on PATH.

### CP-SAT timeout

```
[6a] CP-SAT α≥19 {'available': True, 'found': False, 'unsat': False, 'timed_out': True, ...}
[phase7] HALT. 6a timeout ≠ proof. Raise RAMSEY_6A_LIMIT or FORCE_7=1.
```

**Fix**: Increase the time limit:
```bash
RAMSEY_6A_LIMIT=600 python3 -m engine.cli --job 6a
```

Or force phase 7 to run anyway (use with caution):
```bash
RAMSEY_FORCE_7=1 python3 -m engine.cli --job phase7
```

### CP-SAT found a 19-IS

```
[phase7] HALT. CP-SAT found a 19-IS. Replay before hunting.
```

This means the Yu witness is invalid or there's a bug. **Do not proceed** — replay the construction and verify.

## Integration with Phase 7

Phase 7 (`job_phase7`) calls `require_6a()` which:

1. Checks if `six_a_green()` returns `True` (i.e., `second_solver_agrees=True` and `no_19_is=True`)
2. If not green, runs `job_6a()` automatically
3. If still not green after running, **halts** and writes `data/phase7.halt`

You can override with `RAMSEY_FORCE_7=1`, but this skips the independent verification.

## Why This Matters

The c-decide kernel in phase 5 found α ≤ 18 on the Yu residual. Job 6a provides **independent confirmation** using different algorithms (SAT solvers, clique finders) before we invest compute in phase 7 hunts.

**Success criterion for science remains finite DS1 +1** — this gate just ensures we're hunting in the right direction.

## See Also

- `engine/phase6.py`: Implementation of job 6a
- `engine/phase7.py`: Phase 7 gate logic (`require_6a()`)
- `data/yu_r4_20.json`: Yu witness (p=251, S of size 32)
- `WHERE-TO-LOOK.md`: Phase 7 look structure
