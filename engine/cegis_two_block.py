"""7e.4: CP-SAT on two-orbit (S0,S1) with leftover-IS CEGIS cuts.

Variables: O(m) inversion-closed free bits of (S0,S1).
Hard: neighbourhood-triangle-free (including cross-block).
Soft: feasibility / mild degree bounds (NOT maximize |S|).
Leftover IS CEGIS: cap at 20 cuts per m.
Referee: decide_alpha_le on full graph with target=t.
"""

from __future__ import annotations

import time

import numpy as np

from .kernels.bitset_mcs import greedy_mis_set


def free_bit_index(m: int) -> int:
    """Number of free bits per block after inversion closure.
    
    S_b[0]=0 by construction. Free bits i=1..floor(m/2) for b in {0,1}.
    Total: 2 * floor(m/2) free bits.
    """
    return m // 2


def bits_to_s0_s1(m: int, bits: list[int]) -> tuple[list[int], list[int]]:
    """Convert free-bit assignment to (S0, S1) with inversion closure.
    
    bits: list of 2*free_bit_index(m) Boolean values (0/1).
    Returns: (S0, S1) where each is a list of distances in [0,m-1] with inversion.
    """
    free = free_bit_index(m)
    if len(bits) < 2 * free:
        raise ValueError(f"Need {2 * free} bits, got {len(bits)}")
    
    S0 = [0] if bits else []
    S1 = [0] if bits else []
    
    for i in range(1, free + 1):
        if bits[i - 1]:
            S0.append(i)
            if i != m - i:
                S0.append(m - i)
    
    for i in range(1, free + 1):
        if bits[free + i - 1]:
            S1.append(i)
            if i != m - i:
                S1.append(m - i)
    
    return sorted(set(S0)), sorted(set(S1))


def s0_s1_to_bits(m: int, S0: list[int], S1: list[int]) -> list[int]:
    """Convert (S0, S1) to free-bit assignment.
    
    Inverse of bits_to_s0_s1.
    """
    free = free_bit_index(m)
    bits = [0] * (2 * free)
    
    s0_set = set(int(d) % m for d in S0)
    s1_set = set(int(d) % m for d in S1)
    
    for i in range(1, free + 1):
        if i in s0_set:
            bits[i - 1] = 1
    
    for i in range(1, free + 1):
        if i in s1_set:
            bits[free + i - 1] = 1
    
    return bits


def build_triangle_free_two_block_model(m: int) -> tuple:
    """Build CP-SAT model forbidding neighbourhood triangles in 2-block circulant.
    
    Hard constraints: no triangles in N(0), including:
    - intra-block S0 triangles
    - cross-block S1 triangles
    - S1-only triangles
    
    Returns: (model, xs, m) where xs are the free-bit variables.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        raise ImportError("ortools required for CP-SAT")
    
    from itertools import combinations
    from .kernels.cayley import two_block_adj
    
    free = free_bit_index(m)
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"bit{i}") for i in range(2 * free)]
    
    # Enumerate small subsets and forbid those that create neighbourhood triangles
    # Test all combinations of free bits up to size 6 (conservative)
    for k in range(1, min(7, 2 * free + 1)):
        for subset_indices in combinations(range(2 * free), k):
            test_bits = [0] * (2 * free)
            for idx in subset_indices:
                test_bits[idx] = 1
            
            S0, S1 = bits_to_s0_s1(m, test_bits)
            if not S0 and not S1:
                continue
            
            s0_arr = np.zeros(m, dtype=np.uint8)
            s1_arr = np.zeros(m, dtype=np.uint8)
            for d in S0:
                s0_arr[d % m] = 1
            for d in S1:
                s1_arr[d % m] = 1
            
            adj = two_block_adj(s0_arr, s1_arr)
            
            # Check if neighbourhood of vertex 0 has a triangle
            n = 2 * m
            nbrs = [int(i) for i in range(n) if adj[0, i]]
            has_triangle = False
            for i, a in enumerate(nbrs):
                for j in range(i + 1, len(nbrs)):
                    b = nbrs[j]
                    if not adj[a, b]:
                        continue
                    for k in range(j + 1, len(nbrs)):
                        c = nbrs[k]
                        if adj[a, c] and adj[b, c]:
                            has_triangle = True
                            break
                    if has_triangle:
                        break
                if has_triangle:
                    break
            
            if has_triangle:
                # Forbid this subset
                model.Add(sum(xs[idx] for idx in subset_indices) <= k - 1)
    
    # Optional: mild degree lower bound to keep leftover ≲200
    # Prefer feasibility mode (objective mode C)
    # Do NOT maximize |S0|+|S1|
    
    return model, xs, m


def is_cut_two_block_lits(m: int, I: list[int]) -> list[int]:
    """Hitting clause on free bits that put an edge inside independent set I.
    
    I: list of vertex indices in [0, 2m-1] of full graph.
    Returns: list of free-bit indices that must have at least one true to hit I.
    
    An edge is "inside I" if both endpoints are in I.
    For two-block circulant: edge (u,v) exists if:
    - u,v in same block and |u-v| ∈ S0
    - u,v in different blocks and |u-v| ∈ S1 (cross-block)
    """
    free = free_bit_index(m)
    lits: set[int] = set()
    n = 2 * m
    
    I_set = set(int(v) % n for v in I)
    
    def undirected_dist_m(x: int) -> int:
        """Circular distance in 1..⌊m/2⌋, or 0."""
        x %= m
        if x == 0:
            return 0
        return min(x, m - x)
    
    # For each pair in I, determine what connection would join them
    for a in I:
        for b in I:
            if a >= b:
                continue
            
            ia, ib = int(a) % n, int(b) % n
            
            # Same block?
            if ia < m and ib < m:
                # Both in block 0: need S0 distance
                d = undirected_dist_m(ib - ia)
                if d > 0 and d <= free:
                    lits.add(d - 1)  # free bit index for S0
            elif ia >= m and ib >= m:
                # Both in block 1: need S0 distance
                d = undirected_dist_m((ib - ia))
                if d > 0 and d <= free:
                    lits.add(d - 1)
            else:
                # Cross-block: need S1 distance
                if ia >= m:
                    ia, ib = ib, ia
                d = undirected_dist_m(abs(ia - (ib - m)))
                if d > 0 and d <= free:
                    lits.add(free + d - 1)  # free bit index for S1
    
    return sorted(lits)


def assignment_nogood(xs: list, m: int, bits: list[int]):
    """Constraint: not this exact 0/1 vector on the free bits."""
    free = free_bit_index(m)
    terms = []
    for i in range(2 * free):
        if i < len(bits):
            if bits[i]:
                terms.append(1 - xs[i])
            else:
                terms.append(xs[i])
    return sum(terms) >= 1


def extract_is_full_graph(nbr: list[int], t: int, seconds: float = 2.0) -> list[int] | None:
    """Extract independent set of size ≥ t from full graph, or None.
    
    Prefer greedy if it already hits target. Else CP-SAT with ∑x≥t + edge forbids.
    Must return nonempty witness when α≥t.
    Fix the 7e1 |I|=0 bug pattern: empty → caller nogoods, no cut.
    """
    if t <= 0:
        return []
    
    greedy = greedy_mis_set(nbr)
    if len(greedy) >= t:
        return greedy
    
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return None
    
    n = len(nbr)
    if n == 0:
        return None
    
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"v{i}") for i in range(n)]
    
    # Edge forbids
    for u in range(n):
        nu = int(nbr[u])
        for v in range(u + 1, n):
            if (nu >> v) & 1:
                model.Add(xs[u] + xs[v] <= 1)
    
    # Must have at least t vertices
    model.Add(sum(xs) >= int(t))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    
    result = [i for i, x in enumerate(xs) if solver.Value(x)]
    
    # Verify independence
    for a in result:
        for b in result:
            if a >= b:
                continue
            if (int(nbr[a]) >> b) & 1:
                # Not independent - return None to trigger nogood
                return None
    
    return result if result else None


def solve_two_block_model(model, xs, m: int, seconds: float, seed: int = 0) -> tuple[str, list[int] | None, float]:
    """Solve the two-block model and return (status, bits, elapsed).
    
    Returns feasible or random solution (NOT maximize |S|).
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return "NO_ORTOOLS", None, 0.0
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(__import__("os").environ.get("RAMSEY_SAT_WORKERS", "8"))
    solver.parameters.random_seed = int(seed) & 0x7FFFFFFF
    
    t0 = time.perf_counter()
    status = solver.Solve(model)
    dt = time.perf_counter() - t0
    
    names = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    label = names.get(status, str(status))
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return label, None, dt
    
    bits = [int(solver.Value(x)) for x in xs]
    return label, bits, dt


def verify_is_independent_full(adj, I: list[int]) -> bool:
    """Verify I is an independent set in the full adjacency matrix."""
    for a in I:
        for b in I:
            if a >= b:
                continue
            ia, ib = int(a), int(b)
            if ia >= len(adj) or ib >= len(adj):
                return False
            if adj[ia, ib]:
                return False
    return True
