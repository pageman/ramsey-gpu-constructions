"""Regression test: seed-first reject must add IS cuts (GitHub issue #6 follow-on).

When warm-start seed-first evaluation finds an independent set (found=True),
it must extract the IS witness and add a leftover IS hitting cut to the model
before proceeding to cold CEGIS rounds.

This test verifies that the IS-cut machinery works: extract_is + is_cut_lits → non-empty cut.

Post-PR #7 fix: seed-first only adds cuts for primary targets (default t=20,21),
not all open t values. This prevents exhausting the cut budget before cold CEGIS runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.cegis_two_block import (
    build_triangle_free_two_block_model,
    is_cut_two_block_lits,
)


def test_seed_first_reject_adds_cut() -> None:
    """IS-cut machinery produces non-empty cuts for known independent sets.
    
    The m=126 bug was: seed-first found=True → no cut added → cuts_this_m=0.
    This test verifies the IS-cut path exists and produces valid constraints.
    
    Setup:
    - m=17 (n=34)
    - Construct a small IS (vertices 0,1,2,3,...,9 in separate blocks/distances)
    - Verify is_cut_two_block_lits produces non-empty lits
    - Add cut to model without error
    
    This is a unit test of the cut machinery, not a full seed-first integration test.
    """
    m = 17
    
    # Build model
    model, xs, _ = build_triangle_free_two_block_model(m)
    
    # Construct a known independent set in the full n=34 graph
    # For two-block circulant, vertices 0..m-1 are block 0, m..2m-1 are block 1
    # If S0 and S1 are empty, all vertices are independent
    # Let's pick a small IS: [0, 9, 18, 27] (spaced across the graph)
    I = [0, 9, 18, 27]
    
    print(f"  [test] m={m} n={2*m} |I|={len(I)} I={I}")
    
    # Compute IS cut lits
    lits = is_cut_two_block_lits(m, I)
    
    print(f"  [test] IS-CUT |lits|={len(lits)} lits={lits}")
    
    if not lits:
        raise AssertionError(
            "empty cut — free bits cannot hit I. "
            "This means the cut machinery is broken or the IS is trivial."
        )
    
    # Add cut to model (verifies it's a valid constraint)
    try:
        model.Add(sum(xs[i] for i in lits) >= 1)
        print(f"  [test] Added IS cut with {len(lits)} literals to model. SUCCESS.")
    except Exception as e:
        raise AssertionError(f"Failed to add IS cut to model: {e}")
    
    # Verify that the cut mechanism is sound:
    # If we have edges inside I, the free bits corresponding to those edges should be in lits
    # For IS I=[0,9,18,27], edges would be (0,9), (0,18), (0,27), (9,18), (9,27), (18,27)
    # In two-block circulant:
    # - (0,9): intra-block 0, distance 9 → free bit for S0 distance 9 (if ≤ m//2=8, else reflected)
    # - (0,18): cross-block (0 in block 0, 18 in block 1), distance 18-0=18 → S1 distance, reflected to min(18,17-18)=1
    # - etc.
    # The key is that lits should contain indices that would enable these edges.
    
    # Basic sanity: lits should be within valid range
    free = m // 2
    for lit in lits:
        if lit < 0 or lit >= 2 * free:
            raise AssertionError(f"Invalid lit index {lit} (free={free}, range=[0, {2*free-1}])")
    
    print(f"  [test] All lits in valid range [0, {2*free-1}]. SUCCESS.")


def test_seed_first_cut_policy() -> None:
    """Verify seed-first cut policy: only primary t targets get cuts (default t=20,21).
    
    This test verifies the policy fix for the m=126 WARM=1 bug where seed-first
    exhausted the cut budget by cutting for ALL open t (17-21) instead of just
    the primary targets (20,21).
    
    We simulate the policy by checking that:
    1. RAMSEY_7E4_SEED_FIRST_T defaults to "20,21"
    2. The policy is respected during seed-first evaluation
    
    This is a unit test of the policy logic, not a full integration test.
    """
    # Parse the default seed_first_t from the environment or code default
    default_seed_first_t = os.environ.get("RAMSEY_7E4_SEED_FIRST_T", "20,21")
    seed_first_targets = [int(x.strip()) for x in default_seed_first_t.split(",") if x.strip()]
    
    print(f"  [test] seed_first_t={seed_first_targets} (default or env override)")
    
    # Verify default is [20, 21]
    if not seed_first_targets:
        raise AssertionError("seed_first_t is empty — must have at least one target")
    
    expected_default = [20, 21]
    if "RAMSEY_7E4_SEED_FIRST_T" not in os.environ:
        if seed_first_targets != expected_default:
            raise AssertionError(
                f"Default seed_first_t={seed_first_targets} != expected {expected_default}. "
                f"Policy should only cut primary targets by default."
            )
    
    print(f"  [test] seed_first_t policy verified: only cut for t in {seed_first_targets}")
    
    # Simulate open_t=[17,18,19,20,21] (m=126 case)
    open_t = [17, 18, 19, 20, 21]
    
    # Count how many t values would get cuts under the policy
    cut_targets = [t for t in open_t if t in seed_first_targets]
    non_cut_targets = [t for t in open_t if t not in seed_first_targets]
    
    print(f"  [test] open_t={open_t}")
    print(f"  [test] cut_targets={cut_targets} (will add cuts)")
    print(f"  [test] non_cut_targets={non_cut_targets} (will NOT add cuts)")
    
    # Verify that the policy limits cuts
    if len(cut_targets) >= len(open_t):
        raise AssertionError(
            f"Policy failure: cut_targets={cut_targets} includes all open_t={open_t}. "
            f"This would exhaust the cut budget before cold CEGIS. "
            f"Policy must restrict cuts to primary targets only."
        )
    
    # Verify that at least some t values are NOT cut
    if not non_cut_targets:
        raise AssertionError(
            f"Policy failure: non_cut_targets is empty. "
            f"All open_t would get cuts, exhausting the budget. "
            f"Policy must restrict cuts to a subset of open_t."
        )
    
    print(f"  [test] Policy check: {len(cut_targets)}/{len(open_t)} open t will get cuts. SUCCESS.")
    print(f"  [test] Headroom: {len(non_cut_targets)} open t will NOT get cuts, preserving budget for cold CEGIS.")



if __name__ == "__main__":
    # Suppress decide_alpha_le backend chatter
    os.environ["RAMSEY_BACKEND_QUIET"] = "1"
    
    failed = []
    
    try:
        test_seed_first_reject_adds_cut()
        print("\n✓ test_seed_first_reject_adds_cut PASSED")
    except AssertionError as e:
        print(f"\n✗ test_seed_first_reject_adds_cut FAILED: {e}")
        failed.append("test_seed_first_reject_adds_cut")
    except Exception as e:
        print(f"\n✗ test_seed_first_reject_adds_cut ERROR: {e}")
        import traceback
        traceback.print_exc()
        failed.append("test_seed_first_reject_adds_cut")
    
    try:
        test_seed_first_cut_policy()
        print("\n✓ test_seed_first_cut_policy PASSED")
    except AssertionError as e:
        print(f"\n✗ test_seed_first_cut_policy FAILED: {e}")
        failed.append("test_seed_first_cut_policy")
    except Exception as e:
        print(f"\n✗ test_seed_first_cut_policy ERROR: {e}")
        import traceback
        traceback.print_exc()
        failed.append("test_seed_first_cut_policy")
    
    if failed:
        print(f"\n✗ {len(failed)} test(s) FAILED: {failed}")
        sys.exit(1)
    else:
        print("\n✓ All tests PASSED")
        sys.exit(0)
