# GPU constructions Run001 never ran

Explicit Ramsey-graph families that are **GPU-native** — adjacency is a batched tensor kernel — and that **RamseyConstructor-GNN Run001 did not generate**.

This is not a claim that any of them prove \(R(k,k)\ge C^k\) with \(C\ge 1.01\). Paley, Frankl–Wilson, NLFSR, and these GPU families all live in the sub-exponential explicit regime. The point is the compute gap: Run001 spent its budget on CPU Paley/FW feature CSVs and never launched the kernels the original spec paid 100 GPU-hours for.

## The answer

Run001 **did** build Paley primes \(p\equiv 1\pmod 4\), Frankl–Wilson hybrids, synthetic 1% flips, a DIMACS slice, NLFSR sketches for Erdős 78, and a Random Forest on algebraic features. Hoffman/spectral proxies replaced Lovász \(\vartheta\). There is no `gnn_model.pt` in the artifact list.

These constructions **can** run on GPU and **were not** run:

| Family | GPU kernel | Why Run001 missed it |
|---|---|---|
| Paley of prime powers \(\mathbb F_{p^n}\), \(n>1\) | batched \(\mathbb F_{p^2}\) multiply-exponentiate on outer differences | Spec locked Paley to primes in \([17,997]\) |
| Generalized Paley \(\mathrm{GP}(p,k)\), \(k>2\) | outer-diff + \(a^{(p-1)/k}=1\) | Only quadratic residues; cubic/quartic Paley unused |
| Cyclotomic class-union Cayley | discrete-log table + class mask | Task 4 asked for this; artifacts are correlation CSVs, not a mask sweep |
| Quadratic-form Cayley on \(\mathbb F_2^n\) | XOR outer product + bitwise \(Q\) | Most GPU-native kernel in the catalogue; absent from the 40/30/20/10 mix |
| Gold / trace-of-power graphs on \(\mathbb F_2^n\) | XOR outer + \(\mathrm{GF}(2^n)\) power + Frobenius trace | NLFSR was the nonlinear CPU sibling; linear Gold/Kasami/m-sequences were not batched |
| Orthogonal polarity graphs of \(\mathrm{PG}(2,q)\) | GEMM of homogeneous coordinates \(x\cdot y\equiv 0\) | Finite-geometry polarity (Mattheus–Verstraete style) never built |
| Nagy intersecting-family graphs | pair bitset AND + popcount | Classical explicit cubic; not in the mix |
| Strong products / Kronecker lifts | `kronecker(A+I, A+I)` | Atoms only, no Abbott-style product family |
| Singer difference-set circulants | circulant broadcast of a \((q^2+q+1,q+1,1)\) set | Linear design-theory cousin of NLFSR, unused |
| Block-circulant / Galois cycle-type search | GPU local search on connection sets | The R(5,5)-style GPU annealer the budget was meant to buy |
| PPO + GAT | PyTorch Geometric | Required deliverable `gnn_model.pt` was not in the Run001 files |
| GPU Lovász \(\vartheta\) SDP | CVXPY / randomized SDP | Replaced by Hoffman proxies; no `verification_log.json` |
| GEMM clique counting | \(A^3\) / neighborhood \(A^3\) | Exact \(\omega\) assigned to CPU cliquer |

This repo **implements** the algebraic families (first ten rows except the search/SDP/PPO block) as vectorized NumPy kernels that switch to CUDA when `torch.cuda` is available. It does **not** train a GNN or run PPO — Berghaus–Wagner (ICLR 2025) already showed RL edge-flip can lose to random on \(R(4,4)\), and shipping a fake `gnn_model.pt` would not close Erdős 78.

## Run the catalogue

```bash
python3 engine/test_invariants.py   # Paley(17) is K4-free, Nagy(6) has ω=5, …
python3 engine/run.py               # writes data/ramsey_constructions.csv and catalog JSON
```

On a machine with CUDA, the same `engine/backend.py` path uses GPU GEMM and `torch.linalg.eigvalsh`. This cloud box has OpenBLAS + AVX-512, no NVIDIA device.

## Run the dashboard

```bash
npm install
npm run dev     # http://127.0.0.1:43123
```

## What the numbers mean

For each graph we report a **certified** \(k=\max(\omega^\uparrow,\alpha^\uparrow)+1\), so \(R(k,k)>N\) whenever the bounds are valid. Exact Bron–Kerbosch is used for \(N\le 21\) (Paley(17) recovers \(\omega=\alpha=3\), hence \(R(4,4)>17\)). Larger graphs use the ratio / Hoffman spectral bounds, which are **loose** — they inflate \(k\) and therefore shrink \(N^{1/k}\). Treat large-\(N\) \(N^{1/k}\) as a pessimistic proxy, not a new exponential lower bound.

OEIS A000791 is the validation table: \(R(3,3)=6\), \(R(4,4)=18\), \(R(5,5)\in[43,48]\).

## Layout

- `engine/constructions.py` — parametric families
- `engine/certify.py` — exact + GEMM + spectral certificates
- `engine/gap.py` — the Run001 gap list (single source of truth)
- `data/ramsey_constructions.csv` — flat schema compatible with Run001
- `src/` — Next.js dashboard
