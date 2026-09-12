# Job 7e4 Plan — Waves A–E and non-goals

Job 7e4 = CP-SAT CEGIS on two-orbit (S0,S1) for Look 4 / R(4,20)≥252 search.

---

## Waves A–E

### Wave A — Scaffolding ✓ (this PR)

- `engine/cegis_two_block.py` with:
  - `free_bit_index(m)`, `bits_to_s0_s1`, `s0_s1_to_bits` (inversion closure)
  - `build_triangle_free_two_block_model(m)` — hard forbid neighbourhood triangles (including cross-block)
  - `is_cut_two_block_lits(m, I)` — hitting clause on free bits
  - `assignment_nogood` for whole (S0,S1)
  - `extract_is_full_graph(nbr, t, seconds)` — must return nonempty witness when α≥t
- Tests in `engine/test_kernels.py`:
  - Inversion closure round-trip
  - Planted cross-triangle forbidden by model
  - Hitting clause kills a synthetic witness
  - Empty-cut detection
  - Job registration test includes `7e4`

### Wave B — Operator surface ✓ (this PR)

- `job_7e4` in `engine/phase7.py`:
  - Environment knobs: `RAMSEY_7E4_M`, `RAMSEY_7E4_CUTS`, `RAMSEY_7E4_ROUNDS`, 
    `RAMSEY_7E4_SAT`, `RAMSEY_7E4_POOL_WALL`, `RAMSEY_7E4_MIS`, `RAMSEY_7E4_WARM`
  - CEGIS loop: model = triangle_free_two_block(m) + optional degree/leftover soft bounds
  - For each round until cut_count≥20 or pool UNSAT or wall:
    - Solve → INFEASIBLE: pool-UNSAT; UNKNOWN: timeout≠cut; if not K4_free: nogood
    - Greedy α on full graph
    - For t in prioritize([20,21] + other open_t):
      - `decide_alpha_le(full_nbr, target=t)`
      - timed_out → nogood assignment, NO cut
      - found → extract witness; empty → nogood no cut; else add hitting clause, cut_count+=1
      - if residual_accept and mixed_ok and beats floor → CELL?
  - Dumps under `data/phase7/7e4/` + SUMMARY.json
- Registration in `engine/jobs.py` and `engine/registry.py`
- Documentation:
  - `docs/JOB-7E4.md` on JOB-7C1 pattern (contract, knobs, log recipe)
  - `docs/JOB-7E4-PLAN.md` (this file)

### Wave C — Local validation (NOT in this PR)

- Run test suite: `python3 engine/test_kernels.py`
- Run local wiring:
  ```bash
  RAMSEY_FORCE_7=1 RAMSEY_7E4_M=17 RAMSEY_7E4_CUTS=5 \
    python3 -u -m engine.cli --job 7e4 --scale local
  ```
- Verify:
  - Tests pass for new unit cases
  - At least one cut fires for m=17 or m=29
  - Logs show `[7e4]` banner with "NOT maximize |S|"
  - `data/phase7/7e4/m*_SUMMARY.json` written

### Wave D — Pod night (NOT in this PR)

- Launch on A40 pod:
  ```bash
  cd /workspace/ramsey-gpu-constructions
  tmux new-session -d -s ramsey7e4 -c /workspace/ramsey-gpu-constructions \
    'export RAMSEY_FORCE_7=1 PYTHONUNBUFFERED=1; \
     python3 -u -m engine.cli --job 7e4 --scale runpod 2>&1 | tee -a data/phase7.log'
  ```
- Default: m=[126,128], cuts_cap=20, rounds=16, pool_wall=90s
- Monitor: `grep '\[7e4\]' data/phase7.log | tail`
- Outcome gates:
  - `CELL?` → stop, replay mixed-set and DS1
  - `cuts_saturated` → model may still be SAT; analyze
  - `pool UNSAT` → strong negative at this m
  - `graphs=0` and `cuts=0` → no cell, no cuts (unexpected)

### Wave E — Analysis and reporting (NOT in this PR)

- After `job 7e4 done`:
  ```bash
  grep -c 'CELL?' data/phase7.log
  grep '\[7e4\] summary' data/phase7.log
  grep -c 'CUT' data/phase7.log
  ```
- Write analysis:
  - If `CELL?` → replay certificate, update published floor
  - If `cuts>0` and no `CELL?` → generator works, α still ≥ t (falsified as cell machine)
  - If `pool UNSAT` → document strong negative
  - If `cuts_saturated` → check if model is truly INFEASIBLE or just cut-capped
- Archive logs:
  ```bash
  scp -P $PORT root@$HOST:/workspace/.../data/phase7.log ~/...
  scp -P $PORT root@$HOST:/workspace/.../data/phase7/7e4/*.json ~/...
  ```
- Commit analysis docs and log excerpts (not full log, just summary)

---

## Non-goals (what NOT to do)

1. **Do NOT maximize |S0|+|S1|**
   - Contract explicitly forbids packing as default objective
   - Prefer feasibility mode (objective mode C) or mild degree lower bound
   - Leftover must stay ≲200 vertices for decide_alpha_le

2. **Do NOT reopen or modify `--job 7c` / `7c1` / `pod-phase7.sh`**
   - 7c/7c1 are Yu pools, not two-orbit
   - pod-phase7.sh re-enters 6a and can halt
   - 7e4 is a standalone job

3. **Do NOT raise MAXN to 512**
   - decide_alpha_le caps at n≤256
   - m=256 → n=512 would skip referee
   - Default m=[126,128] → n=[252,256] is correct

4. **Do NOT use Hoffman scoring**
   - 7e4 uses decide_alpha_le on full graph
   - Hoffman α is a bound, not a decision oracle
   - Residual-only accepts need mixed-set check

5. **Do NOT unbounded cuts**
   - Cap at 20 cuts per m by design
   - Cut saturation is a valid outcome, not a bug
   - If saturated and SAT, report it; don't keep adding cuts

6. **Do NOT mix unrelated docs**
   - This PR is 7e4 only
   - Do not edit JOB-7C1.md, JOB-7E.md, etc.
   - Do not change 6a, do not raise MAXN in phase5

7. **Do NOT start Waves C/D/E in this PR**
   - This PR is scaffolding + operator surface only
   - Pod night is a separate run after tests pass
   - Analysis is a separate doc after the night completes

---

## Success criteria for Waves A–B (this PR)

- [ ] `engine/cegis_two_block.py` exists and has all required functions
- [ ] Tests added to `engine/test_kernels.py` and include `7e4` in job registration test
- [ ] `job_7e4` in `engine/phase7.py` with full CEGIS loop
- [ ] Job registered in `engine/jobs.py` and `engine/registry.py`
- [ ] `docs/JOB-7E4.md` exists (contract, knobs, log recipe)
- [ ] `docs/JOB-7E4-PLAN.md` exists (this file)
- [ ] PR title: `job-7e4-cegis-two-block` (or similar)
- [ ] PR description: "Implement Job 7e.4 Waves A–B only (scaffolding + operator surface)"

---

## Success criteria for Wave C (future, not this PR)

- [ ] `python3 engine/test_kernels.py` passes all tests
- [ ] Local run produces at least one cut
- [ ] Logs show `[7e4]` banner with "NOT maximize |S|"
- [ ] `data/phase7/7e4/m*_SUMMARY.json` written

---

## Success criteria for Wave D (future, not this PR)

- [ ] Pod night completes without crash
- [ ] Logs have `job 7e4 done` line
- [ ] `cuts>0` or explicit `no cuts` explanation in log
- [ ] `CELL?` line present (success) or absent (expected negative)

---

## Success criteria for Wave E (future, not this PR)

- [ ] Analysis doc committed
- [ ] Log excerpts archived (not full log)
- [ ] If `CELL?`, certificate replayed and published floor updated
- [ ] If falsified, summary explains why α≥t despite cuts

---

## Contract summary for quick reference

**7e.4 = CP-SAT on O(m) inversion-closed free bits of (S0,S1), hard 
neighbourhood-triangle-free clauses, soft search that does NOT maximize |S|, 
leftover/full-graph IS CEGIS capped at 20 cuts/m, referee = decide_alpha_le 
on full graph with target=t (prioritize t=20,21). Success = CELL? with 
mixed-set OK, or written pool-UNSAT / cut-saturated negative at P0 {126,128}.**

Same instrument as 7c1 (CP-SAT CEGIS), different variables (two-orbit free bits
vs Yu pool distances). Same referee (decide_alpha_le), different graph (full
graph vs residual). Same cut cap (20), different scope (per m vs per pool).

---

## Related jobs (do not confuse)

| Job | Variables | Graph | Objective | Cuts | Target |
|---|---|---|---|---|---|
| **7e4** | O(m) free bits (S0,S1) | full n=2m | feasibility | 20/m | R(4,20)≥252 |
| 7c | Yu pool distances | residual | max \|S\| once | 0 | R(4,t) |
| 7c1 | Yu pool distances | residual | max \|S\| per round | unbounded | R(4,t) |
| 7e | O(m) free bits (S0,S1) | full n=2m | greedy ILS | 0 | R(4,t) |
| 7e1 | O(m) free bits (S0,S1) | full n=2m | Hoffman ILS | 0 | R(4,t) |

Do not run 7c/7c1/7e/7e1 when the task is 7e4. Do not run pod-phase7.sh (it
enters 6a).

---

## Banner one-liner (must appear in `job_7e4` output)

```
7e.4 = CP-SAT on O(m) inversion-closed free bits of (S0,S1), hard 
neighbourhood-triangle-free clauses, soft search that does NOT maximize |S|, 
leftover/full-graph IS CEGIS capped at 20 cuts/m, referee = decide_alpha_le 
on full graph with target=t (prioritize t=20,21). Success = CELL? with 
mixed-set OK, or written pool-UNSAT / cut-saturated negative at P0 {126,128}.
NOT --job 7c.
```

This must be visible in the log for Wave C/D operators to confirm they launched
the right job.
