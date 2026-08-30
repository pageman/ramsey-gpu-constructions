# Deliverables 2a → 7c1

Inventory of what the A40 campaign produced. Nothing here is a published
+1. The number that is still true is **252**.

| Job | In git clone | In Downloads after `mac-finish-archive.sh` |
|---|---|---|
| 2a | `data/a40/catalog-2a.json` (~14 MB), `data/a40/registry.jsonl` | `a40-from-pod/` + `data/a40/` |
| 2b | catalogue / Hoffman only; see `docs/A40-CAMPAIGN.md` | same docs |
| 2c | `docs/A40-CAMPAIGN.md` | docs |
| 3a–3d | A40 campaign write-up; 3d n=13/14 in registry | docs + a40 registry |
| 4a | `data/a40/catalog-4abc.json` — **354 is void** (residual >256) | a40 |
| 4b | same dump; graphs=0 | a40 |
| 4c | leftover 84, \(R(4,22)>84\) vs 314 | a40 + phase5 replay |
| 5a–5f | `data/phase5/` log, cert, meta | `phase5-from-pod/` |
| 6a | `data/phase7/yu_r4_20.cert2.json` if pod pull succeeded; else timeout recorded in PHASE7-CAMPAIGN | phase7-from-pod |
| 7a–7f | `data/phase7/phase7.log` | `phase7-from-pod/phase7.log` |
| 7c1 | same log + `data/phase7/SUMMARY.txt`, `engine-src/`, DIMACS `yu_r4_20.complement.clq` | same |

Kernel sources to rebuild the referee: `engine/kernels/native_decide.c`,
`native_mis.c`. Tests: `python3 engine/test_kernels.py`.
