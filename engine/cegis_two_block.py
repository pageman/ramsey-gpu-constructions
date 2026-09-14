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
    Note: 0 is not forced into S0/S1 here; cayley.closed_S handles it.
    """
    free = free_bit_index(m)
    if len(bits) < 2 * free:
        raise ValueError(f"Need {2 * free} bits, got {len(bits)}")
    
    S0 = []
    S1 = []
    
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


def build_triangle_free_two_block_model(m: int, warm_bits: list[int] | None = None, warm_radius: int = 0) -> tuple:
    """Build CP-SAT model for two-block circulant (lazy triangle repair).
    
    No hard triangle-free clauses up front (exponential at m=126). Use lazy CEGIS:
    solve → check K4-free → if triangle, add cut on supporting free bits → repeat.
    
    Add mild search bias: degree/leftover lower bound to prevent all-zero attractor.
    For n=2m, deg(0) ≈ |S0| + |S1| (with inversion closure multiplicity).
    Leftover ≈ n - deg(0) - 1 = 2m - |S0| - |S1| - 1.
    To keep leftover ≲200, force deg(0) ≳ 2m - 201, i.e., enough free bits true.
    
    Optional warm_radius constraint: if warm_bits provided and warm_radius > 0,
    constrain Hamming distance from warm_bits to ≤ warm_radius.
    
    Returns: (model, xs, m) where xs are the free-bit variables.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        raise ImportError("ortools required for CP-SAT")
    
    free = free_bit_index(m)
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"bit{i}") for i in range(2 * free)]
    
    # Degree/leftover lower bound to prevent all-zero attractor
    # Target: deg(0) ≥ n/3 to keep leftover small enough for greedy_alpha < open_t
    # Each free bit contributes ≈2 to degree (with inversion closure)
    # Formula: min_bits = n/6, ensuring deg ≈ n/3 or leftover ≈ 2n/3
    # At m=101 (n=202): min_bits≈34, deg≈68, leftover≈133
    # At m=126 (n=252): min_bits≈42, deg≈84, leftover≈167
    # At m=128 (n=256): min_bits≈43, deg≈86, leftover≈169
    n = 2 * m
    min_bits = max(3, n // 6)  # At least 3 bits; aim for deg ≥ n/3
    
    if min_bits > 0 and min_bits < 2 * free:
        model.Add(sum(xs) >= min_bits)
    
    # Hamming ball constraint: if warm_radius > 0, stay within radius of warm_bits
    if warm_bits is not None and warm_radius > 0:
        free = free_bit_index(m)
        if len(warm_bits) >= 2 * free:
            # Hamming distance = number of flipped bits
            # For bit i: flipped if (warm[i]=0 and x[i]=1) or (warm[i]=1 and x[i]=0)
            # Count: sum((1-warm[i])*x[i] + warm[i]*(1-x[i])) <= radius
            flips = []
            for i in range(2 * free):
                w = int(warm_bits[i])
                if w == 0:
                    flips.append(xs[i])  # Flip if we set it to 1
                else:
                    flips.append(1 - xs[i])  # Flip if we set it to 0
            model.Add(sum(flips) <= int(warm_radius))
    
    # Do NOT maximize |S0|+|S1| as the night objective
    # Feasibility mode with lower bound is the bias
    
    return model, xs, m


class ModelState:
    """Track accumulated constraints to rebuild model after MODEL_INVALID."""
    def __init__(self, m: int):
        self.m = m
        self.triangle_cuts: list[list[int]] = []  # List of support bit indices
        self.is_cuts: list[list[int]] = []  # List of IS cut lits
        self.nogoods: list[list[int]] = []  # List of nogood bit assignments
    
    def add_triangle_cut(self, support: list[int]):
        """Record a triangle cut: at most len(support)-1 of support can be true."""
        self.triangle_cuts.append(support[:])
    
    def add_is_cut(self, lits: list[int]):
        """Record an IS cut: at least one of lits must be true."""
        self.is_cuts.append(lits[:])
    
    def add_nogood(self, bits: list[int]):
        """Record a nogood: not this exact assignment."""
        self.nogoods.append(bits[:])
    
    def rebuild_model(self, warm_bits: list[int] | None = None, warm_radius: int = 0) -> tuple:
        """Rebuild model with all accumulated constraints.
        
        Returns: (model, xs, m)
        """
        model, xs, m = build_triangle_free_two_block_model(self.m, warm_bits, warm_radius)
        
        # Re-add all triangle cuts
        for support in self.triangle_cuts:
            if len(support) >= 2:
                model.Add(sum(xs[i] for i in support) <= len(support) - 1)
        
        # Re-add all IS cuts
        for lits in self.is_cuts:
            if lits:
                model.Add(sum(xs[i] for i in lits) >= 1)
        
        # Re-add all nogoods
        free = free_bit_index(m)
        for bits in self.nogoods:
            terms = []
            for i in range(2 * free):
                if i < len(bits):
                    if bits[i]:
                        terms.append(1 - xs[i])
                    else:
                        terms.append(xs[i])
            if terms:
                model.Add(sum(terms) >= 1)
        
        return model, xs, m


def first_triangle_support_two_block(m: int, bits: list[int]) -> list[int] | None:
    """Free-bit indices that witness one triangle in N(0), or None.
    
    Returns minimal free-bit indices that enable the specific triangle edges
    (0→a, 0→b, 0→c, a↔b, a↔c, b↔c) in two-block geometry, NOT all true bits.
    Pattern after cegis_pool.first_triangle_support_dists.
    """
    S0, S1 = bits_to_s0_s1(m, bits)
    if not S0 and not S1:
        return None
    
    s0_arr = np.zeros(m, dtype=np.uint8)
    s1_arr = np.zeros(m, dtype=np.uint8)
    for d in S0:
        s0_arr[d % m] = 1
    for d in S1:
        s1_arr[d % m] = 1
    
    from .kernels.cayley import two_block_adj
    adj = two_block_adj(s0_arr, s1_arr)
    
    n = 2 * m
    nbrs = [int(i) for i in range(n) if adj[0, i]]
    
    def undirected_dist_m(x: int) -> int:
        """Circular distance in 1..⌊m/2⌋, or 0."""
        x %= m
        if x == 0:
            return 0
        return min(x, m - x)
    
    def dist_to_free_bit(d: int, is_cross: bool) -> int | None:
        """Map a distance d to free-bit index, or None if not in free range."""
        free = free_bit_index(m)
        if d <= 0 or d > free:
            return None
        if is_cross:
            return free + d - 1  # S1 free bits
        else:
            return d - 1  # S0 free bits
    
    # Find a triangle in N(0)
    for i, a in enumerate(nbrs):
        for j in range(i + 1, len(nbrs)):
            b = nbrs[j]
            if not adj[a, b]:
                continue
            for k in range(j + 1, len(nbrs)):
                c = nbrs[k]
                if adj[a, c] and adj[b, c]:
                    # Found triangle (a, b, c) in N(0)
                    # Determine which free bits support the triangle edges
                    support_bits: set[int] = set()
                    
                    # Edges from 0 to {a, b, c}
                    for v in (a, b, c):
                        # Is v in block 0 or block 1?
                        is_cross = (v >= m)
                        v_mod = v % m
                        
                        # Distance from 0 to v
                        if is_cross:
                            # Cross-block: S1 distance
                            d = undirected_dist_m(v_mod)
                            bit_idx = dist_to_free_bit(d, True)
                            if bit_idx is not None:
                                support_bits.add(bit_idx)
                        else:
                            # Intra-block 0: S0 distance
                            d = undirected_dist_m(v_mod)
                            bit_idx = dist_to_free_bit(d, False)
                            if bit_idx is not None:
                                support_bits.add(bit_idx)
                    
                    # Edges within {a, b, c}
                    for u, v in [(a, b), (a, c), (b, c)]:
                        # Same block or cross-block?
                        if (u < m and v < m) or (u >= m and v >= m):
                            # Intra-block: S0 distance
                            d = undirected_dist_m(abs((v % m) - (u % m)))
                            bit_idx = dist_to_free_bit(d, False)
                            if bit_idx is not None:
                                support_bits.add(bit_idx)
                        else:
                            # Cross-block: S1 distance
                            u_mod, v_mod = u % m, v % m
                            d = undirected_dist_m(abs(v_mod - u_mod))
                            bit_idx = dist_to_free_bit(d, True)
                            if bit_idx is not None:
                                support_bits.add(bit_idx)
                    
                    return sorted(support_bits) if support_bits else None
    
    return None


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


def is_repair_from_warm(
    m: int,
    warm_bits: list[int],
    cut_lits: list[int],
    max_flips: int = 5,
    max_attempts: int = 8,
) -> list[int] | None:
    """IS-directed local repair: flip warm bits that participate in the cut to satisfy it.
    
    After seed-first extracts IS I and installs cut (sum(cut_lits) >= 1), start from 
    warm_bits and flip minimal free bits in cut_lits to satisfy the cut while staying 
    K4_free and maintaining low greedy α.
    
    Args:
        m: modulus (n=2m)
        warm_bits: original warm-start free bits
        cut_lits: free-bit indices from is_cut_two_block_lits that must have ≥1 true
        max_flips: maximum number of bits to flip per attempt
        max_attempts: number of repair attempts
    
    Returns:
        Repaired free bits if successful (K4_free + cut satisfied), else None
    """
    import random
    from .kernels.cayley import two_block_adj
    
    free = free_bit_index(m)
    if not cut_lits:
        return None
    
    # Check if warm already satisfies cut (should not, but defensive)
    if any(warm_bits[i] for i in cut_lits if i < len(warm_bits)):
        # Already satisfies cut - return warm
        return warm_bits[:]
    
    best_bits = None
    best_greedy = float('inf')
    
    rng = random.Random(42)
    
    for attempt in range(max_attempts):
        # Start from warm
        bits = warm_bits[:]
        
        # Choose how many cut_lits to flip on (1 to max_flips, prefer fewer)
        n_flip = min(1 + attempt // 2, max_flips, len(cut_lits))
        
        # Select random subset of cut_lits to flip on
        flip_candidates = rng.sample(cut_lits, min(n_flip, len(cut_lits)))
        
        for lit_idx in flip_candidates:
            if lit_idx < len(bits):
                bits[lit_idx] = 1
        
        # Evaluate: K4_free + greedy α
        S0, S1 = bits_to_s0_s1(m, bits)
        
        s0_arr = np.zeros(m, dtype=np.uint8)
        s1_arr = np.zeros(m, dtype=np.uint8)
        for d in S0:
            s0_arr[d % m] = 1
        for d in S1:
            s1_arr[d % m] = 1
        
        adj = two_block_adj(s0_arr, s1_arr)
        
        # Check K4-free
        from .phase7 import _k4_free_adj, _adj_nbr
        if not _k4_free_adj(adj):
            continue
        
        # Greedy α
        nbr = _adj_nbr(adj)
        greedy_alpha = greedy_mis_set(nbr)
        gα = len(greedy_alpha)
        
        if gα < best_greedy:
            best_greedy = gα
            best_bits = bits[:]
    
    return best_bits


def solve_two_block_model(model, xs, m: int, seconds: float, seed: int = 0, warm_bits: list[int] | None = None, warm_radius: int = 0) -> tuple[str, list[int] | None, float]:
    """Solve the two-block model and return (status, bits, elapsed).
    
    Returns feasible or random solution (NOT maximize |S|).
    If warm_bits provided, use as AddHint (seed-first).
    If warm_radius > 0, constrain Hamming distance from warm_bits to ≤ warm_radius.
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return "NO_ORTOOLS", None, 0.0
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = int(__import__("os").environ.get("RAMSEY_SAT_WORKERS", "8"))
    solver.parameters.random_seed = int(seed) & 0x7FFFFFFF
    
    # Apply warm-start hint if provided
    if warm_bits is not None and hasattr(model, 'AddHint'):
        free = free_bit_index(m)
        for i in range(min(len(warm_bits), 2 * free)):
            model.AddHint(xs[i], int(warm_bits[i]))
    
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
