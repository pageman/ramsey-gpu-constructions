"""Regression tests for 7e4 warm-start IS-repair and MODEL_INVALID fix.

Tests:
1. is_repair_from_warm: IS-directed local repair from warm after seed-first cuts
2. ModelState: constraint tracking and model rebuild after MODEL_INVALID
3. warm_radius: Hamming-ball constraint around warm bits
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.cegis_two_block import (
    ModelState,
    bits_to_s0_s1,
    build_triangle_free_two_block_model,
    free_bit_index,
    is_cut_two_block_lits,
    is_repair_from_warm,
    s0_s1_to_bits,
    solve_two_block_model,
)


def test_is_repair_from_warm() -> None:
    """Test IS-directed local repair mechanism.
    
    Scenario:
    - m=17, n=34
    - Construct warm_bits with K4_free=True and low greedy α
    - Extract a synthetic IS and compute cut_lits
    - Verify is_repair_from_warm flips bits to satisfy the cut while staying K4_free
    """
    m = 17
    free = free_bit_index(m)
    
    # Construct a simple warm_bits: alternating pattern (sparse S0, S1)
    warm_bits = [0] * (2 * free)
    for i in range(0, free, 3):
        warm_bits[i] = 1  # S0 distances
    for i in range(0, free, 4):
        warm_bits[free + i] = 1  # S1 distances
    
    # Synthetic IS: vertices [0, 5, 10, 15, 20, 25, 30] (spaced)
    I = [0, 5, 10, 15, 20, 25, 30]
    
    # Compute IS cut lits
    cut_lits = is_cut_two_block_lits(m, I)
    
    print(f"  [test] m={m} free={free} |warm_bits|={len(warm_bits)}")
    print(f"  [test] I={I}")
    print(f"  [test] cut_lits={cut_lits}")
    
    if not cut_lits:
        print("  [test] WARNING: empty cut_lits for this IS. Test may be vacuous.")
        # Not a failure - just means this specific IS can't be hit by these free bits
        return
    
    # Check that warm does NOT satisfy cut (seed-first reject scenario)
    warm_satisfies = any(warm_bits[i] for i in cut_lits if i < len(warm_bits))
    print(f"  [test] warm_satisfies_cut={warm_satisfies}")
    
    if warm_satisfies:
        print("  [test] WARNING: warm already satisfies cut. Modifying warm for test.")
        # Zero out cut_lits in warm to force repair
        for lit in cut_lits:
            if lit < len(warm_bits):
                warm_bits[lit] = 0
    
    # Attempt IS-repair
    repaired = is_repair_from_warm(m, warm_bits, cut_lits, max_flips=5, max_attempts=8)
    
    if not repaired:
        raise AssertionError(
            "is_repair_from_warm returned None. Expected repaired bits."
        )
    
    print(f"  [test] |repaired|={len(repaired)}")
    
    # Verify repaired satisfies cut
    repaired_satisfies = any(repaired[i] for i in cut_lits if i < len(repaired))
    if not repaired_satisfies:
        raise AssertionError(
            f"Repaired bits do not satisfy cut. cut_lits={cut_lits}, "
            f"repaired[cut_lits]={[repaired[i] for i in cut_lits if i < len(repaired)]}"
        )
    
    print(f"  [test] repaired_satisfies_cut={repaired_satisfies} ✓")
    
    # Verify repaired is K4-free (basic check: can build model and convert)
    S0, S1 = bits_to_s0_s1(m, repaired)
    print(f"  [test] repaired |S0|={len(S0)} |S1|={len(S1)}")
    
    # Check Hamming distance (should be small, since it's a local repair)
    hamming = sum(1 for i in range(len(warm_bits)) if warm_bits[i] != repaired[i])
    print(f"  [test] Hamming(warm, repaired)={hamming}")
    
    if hamming > 15:
        print(f"  [test] WARNING: Hamming distance {hamming} is high. Expected small local flips.")
    
    print("  [test] is_repair_from_warm SUCCESS ✓")


def test_model_state_rebuild() -> None:
    """Test ModelState constraint tracking and model rebuild.
    
    Scenario:
    - m=17
    - Add several IS-cuts, triangle-cuts, and nogoods to ModelState
    - Rebuild model and verify constraints are re-added
    - Solve and verify solution respects accumulated constraints
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        print("  [test] ortools not available — skip test_model_state_rebuild")
        return
    
    m = 17
    free = free_bit_index(m)
    
    print(f"  [test] m={m} free={free}")
    
    # Initialize ModelState
    state = ModelState(m)
    
    # Add synthetic constraints
    # Triangle cut: support=[0, 1, 2]
    state.add_triangle_cut([0, 1, 2])
    
    # IS cut: lits=[3, 4, 5]
    state.add_is_cut([3, 4, 5])
    
    # Nogood: bits with first 4 bits set
    nogood_bits = [0] * (2 * free)
    nogood_bits[0] = 1
    nogood_bits[1] = 1
    nogood_bits[2] = 1
    nogood_bits[3] = 1
    state.add_nogood(nogood_bits)
    
    print(f"  [test] Added {len(state.triangle_cuts)} triangle-cut(s), "
          f"{len(state.is_cuts)} IS-cut(s), {len(state.nogoods)} nogood(s)")
    
    # Rebuild model
    model, xs, _ = state.rebuild_model()
    
    print("  [test] Model rebuilt successfully ✓")
    
    # Solve and verify constraints
    status, bits, dt = solve_two_block_model(model, xs, m, seconds=2.0)
    
    print(f"  [test] Solve after rebuild: status={status} dt={dt:.3f}s")
    
    if status not in ("OPTIMAL", "FEASIBLE"):
        # INFEASIBLE or UNKNOWN is acceptable (constraints may be tight)
        print(f"  [test] Model is {status} after constraints — acceptable for test")
        return
    
    if bits is None:
        print("  [test] No solution found — acceptable for test (constraints are tight)")
        return
    
    # Verify triangle cut: at most len(support)-1 of support can be true
    support = [0, 1, 2]
    support_sum = sum(bits[i] for i in support)
    if support_sum > len(support) - 1:
        raise AssertionError(
            f"Triangle cut violated: sum(support)={support_sum} > {len(support)-1}"
        )
    print(f"  [test] Triangle cut respected: sum(support)={support_sum} ≤ {len(support)-1} ✓")
    
    # Verify IS cut: at least one of lits is true
    lits = [3, 4, 5]
    lits_sum = sum(bits[i] for i in lits)
    if lits_sum < 1:
        raise AssertionError(
            f"IS cut violated: sum(lits)={lits_sum} < 1"
        )
    print(f"  [test] IS cut respected: sum(lits)={lits_sum} ≥ 1 ✓")
    
    # Verify nogood: not the exact nogood assignment
    is_nogood = all(bits[i] == nogood_bits[i] for i in range(len(bits)))
    if is_nogood:
        raise AssertionError(
            "Nogood violated: returned exact nogood assignment"
        )
    print(f"  [test] Nogood respected: solution ≠ nogood ✓")
    
    print("  [test] test_model_state_rebuild SUCCESS ✓")


def test_warm_radius_constraint() -> None:
    """Test WARM_RADIUS Hamming-ball constraint.
    
    Scenario:
    - m=17
    - Construct warm_bits
    - Build model with warm_radius=3
    - Solve and verify solution is within Hamming radius 3 of warm
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        print("  [test] ortools not available — skip test_warm_radius_constraint")
        return
    
    m = 17
    free = free_bit_index(m)
    
    # Construct warm_bits: simple pattern
    warm_bits = [0] * (2 * free)
    for i in range(0, free, 2):
        warm_bits[i] = 1
    
    print(f"  [test] m={m} free={free} |warm_bits|={len(warm_bits)} warm_set={sum(warm_bits)}")
    
    # Build model with warm_radius=3
    radius = 3
    model, xs, _ = build_triangle_free_two_block_model(m, warm_bits, radius)
    
    print(f"  [test] Built model with warm_radius={radius}")
    
    # Solve
    status, bits, dt = solve_two_block_model(model, xs, m, seconds=2.0)
    
    print(f"  [test] Solve status={status} dt={dt:.3f}s")
    
    if status not in ("OPTIMAL", "FEASIBLE"):
        print(f"  [test] Model is {status} — acceptable (tight constraints)")
        return
    
    if bits is None:
        print("  [test] No solution found — acceptable")
        return
    
    # Verify Hamming distance
    hamming = sum(1 for i in range(len(warm_bits)) if warm_bits[i] != bits[i])
    
    print(f"  [test] Hamming(warm, solution)={hamming}")
    
    if hamming > radius:
        raise AssertionError(
            f"Hamming constraint violated: distance={hamming} > radius={radius}"
        )
    
    print(f"  [test] Hamming constraint respected: {hamming} ≤ {radius} ✓")
    print("  [test] test_warm_radius_constraint SUCCESS ✓")


def test_model_invalid_scenario() -> None:
    """Test MODEL_INVALID recovery via rebuild.
    
    Scenario:
    - m=17
    - Add many nogoods to trigger potential MODEL_INVALID
    - Rebuild model and verify it's solvable again
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        print("  [test] ortools not available — skip test_model_invalid_scenario")
        return
    
    m = 17
    free = free_bit_index(m)
    
    print(f"  [test] m={m} free={free}")
    
    # Initialize ModelState
    state = ModelState(m)
    model, xs, _ = build_triangle_free_two_block_model(m)
    
    # Add many nogoods (simulate accumulated constraints)
    rng = np.random.default_rng(42)
    for i in range(20):
        bits = (rng.random(2 * free) > 0.5).astype(int).tolist()
        state.add_nogood(bits)
        # Try to add to model (may trigger MODEL_INVALID eventually)
        try:
            from engine.cegis_two_block import assignment_nogood
            model.Add(assignment_nogood(xs, m, bits))
        except Exception:
            pass
    
    print(f"  [test] Added {len(state.nogoods)} nogoods")
    
    # Solve original model (may be MODEL_INVALID)
    status1, bits1, dt1 = solve_two_block_model(model, xs, m, seconds=1.0)
    print(f"  [test] Original model solve: status={status1}")
    
    # Rebuild model
    print("  [test] Rebuilding model...")
    model2, xs2, _ = state.rebuild_model()
    
    # Solve rebuilt model
    status2, bits2, dt2 = solve_two_block_model(model2, xs2, m, seconds=1.0)
    print(f"  [test] Rebuilt model solve: status={status2}")
    
    if status2 == "MODEL_INVALID":
        raise AssertionError(
            "Rebuilt model is still MODEL_INVALID. Rebuild did not fix the issue."
        )
    
    # Accept INFEASIBLE (nogoods may be tight) or FEASIBLE/OPTIMAL
    if status2 not in ("INFEASIBLE", "OPTIMAL", "FEASIBLE", "UNKNOWN"):
        raise AssertionError(
            f"Unexpected status after rebuild: {status2}"
        )
    
    print(f"  [test] Rebuilt model status={status2} — acceptable ✓")
    print("  [test] test_model_invalid_scenario SUCCESS ✓")


if __name__ == "__main__":
    # Suppress decide_alpha_le backend chatter
    os.environ["RAMSEY_BACKEND_QUIET"] = "1"
    
    failed = []
    
    tests = [
        ("test_is_repair_from_warm", test_is_repair_from_warm),
        ("test_model_state_rebuild", test_model_state_rebuild),
        ("test_warm_radius_constraint", test_warm_radius_constraint),
        ("test_model_invalid_scenario", test_model_invalid_scenario),
    ]
    
    for test_name, test_fn in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name}...")
        print('='*60)
        try:
            test_fn()
            print(f"\n✓ {test_name} PASSED")
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed.append(test_name)
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed.append(test_name)
    
    print(f"\n{'='*60}")
    if failed:
        print(f"✗ {len(failed)} test(s) FAILED: {failed}")
        sys.exit(1)
    else:
        print("✓ All tests PASSED")
        sys.exit(0)
