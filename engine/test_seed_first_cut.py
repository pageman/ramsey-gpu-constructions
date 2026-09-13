"""Regression test: seed-first reject must add IS cuts (GitHub issue #6 follow-on).

When warm-start seed-first evaluation finds an independent set (found=True),
it must extract the IS witness and add a leftover IS hitting cut to the model
before proceeding to cold CEGIS rounds.

This test verifies that the IS-cut machinery works: extract_is + is_cut_lits → non-empty cut.
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


if __name__ == "__main__":
    # Suppress decide_alpha_le backend chatter
    os.environ["RAMSEY_BACKEND_QUIET"] = "1"
    
    try:
        test_seed_first_reject_adds_cut()
        print("\n✓ test_seed_first_reject_adds_cut PASSED")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ test_seed_first_reject_adds_cut FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ test_seed_first_reject_adds_cut ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
