# Phase5 campaign (30 Aug 2026)

Run on RunPod A40 `armed_yellow_buzzard` / `amyrwqft651q8i`, container
`3631e8666026`. Code at `07a4e8c`. tmux `ramsey5`.

**No published +1.** \(R(4,20)\ge 252\) (Yu) is unchanged. Paley(17) is
still the exact diagonal jewel. There was no `CELL?` that passed mixed-set
and residual \(\le 256\).

| | Zulu | GMT+8 |
|---|---|---|
| Start T0 | 2026-08-30T05:43:58Z | 13:43:58 |
| 5a green | ~05:45:01Z (63.17 s) | 13:45 |
| Finished | 2026-08-30T06:03:30Z | 14:03:30 |
| Wall | 1171.55 s (~19.5 min) | |

## 5a (the result that matters)

Yu residual \(n=186\), decision “no independent set of size 19”:

- `found=false`, `timed_out=false`, `exact=true`
- `nodes=216275634`, `seconds=63.171`, `backend=c-decide`
- `alpha_certified=true`
- CP-SAT 18-IS: `ortools not installed` (no second backend)
- Greedy lower 15 (Yu’s paper used CP-SAT to witness 18)

This is a **one-backend residual decision**, not a second-solver
recertify of the published graph. Do not announce a new cell.

## 5b–5f

- **5b:** `n=257` skip OK; Paley(17) exact.
- **5c:** hunt \(p\in[200,400]\) through \(p=353\). Greedy \(\alpha\)
  rejected almost every walk. No `CELL?`.
- **5e:** W(3,7) leftover 84, \(\alpha=21\), \(R(4,22)>84\) vs published
  \(\ge 314\). Below floor; not a cell.
- **5f:** TG / Yip Hoffman vs Paley. Paley wins the same-\(n\) comparison.
  Spectral `exact` on TG is not a theorem.
- `graphs=9` in the phase5 catalog emit.

## Where the bits live after archive

See `docs/REPRODUCING.md`. After `bash scripts/mac-archive-repro.sh`:

| Object | Git clone (Cursor / GitHub) | Downloads |
|---|---|---|
| phase5 log, cert, post-run catalog | `data/phase5/` | `~/Downloads/Ramsey-GPU-Constructions/phase5-from-pod/` |
| A40 2a/4a copies saved before reset | `data/a40/pod-keep/` | `…/a40-from-pod/keep-a40/` |
| Earlier committed 2a/4abc dumps | `data/a40/` | copied by `sync-to-downloads.sh` |
| A40 `.so` + `gcc -v` + `nvidia-smi` | `data/phase5/binaries/` + `data/phase5/meta/` | same under Downloads |
