# Phase7 run archive (7a–7f + 7c1)

Code freeze of the tree that ran 7c1 (`98473e5`) plus the Yu leftover
DIMACS and the A40 `c-decide` / MIS binaries copied from `data/phase5/`.

The full 5 MB tee (`phase7.log`) is **not** in this folder until the Mac
promotes `data/phase7-7c1.log` with `bash scripts/mac-finish-archive.sh`.

| File | What |
|---|---|
| `SUMMARY.txt` | 7a–7f + 7c1 counts (181 pools, 13935 cuts, 0 CELL) |
| `yu_r4_20.json` | Yu published \(S\) |
| `yu_r4_20.complement.clq` | DIMACS of the leftover (residual 186) |
| `registry.jsonl` | tree registry at the 7c1 commit |
| `engine-src/` | `phase7.py`, `cegis_pool.py`, `phase6.py`, `scale.py`, `native_*.c` |
| `binaries/` | A40 Linux x86_64 `.so` (same build as phase5) |
| `phase7.log` | A40 tee, after Mac script |
| `ARCHIVE.txt` | stamp written by the Mac script |

See `docs/PHASE7-CAMPAIGN.md` and `docs/REPRODUCING.md`.

Published cell is still **252**.
