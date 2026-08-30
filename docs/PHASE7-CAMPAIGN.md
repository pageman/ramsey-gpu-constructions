# Phase7 + 7c1 campaign (30 Aug 2026)

Run on RunPod A40 `armed_yellow_buzzard`, container `3631e8666026`.
Code at **`98473e5`** for 7c1; 7a–7f ran from the same tree after `fb32807`.

**No published +1.** \(R(4,20)\ge 252\) (Yu, arXiv:2608.18169) is unchanged.
Paley(17) is still the exact diagonal jewel. No `CELL?` that passed mixed-set
and residual \(\le 256\).

| Job | Look | Wall | graphs | Thesis vs result |
|---|---|---|---|---|
| 6a | gate | 600 s cap | — | CP-SAT \(\alpha\ge 18\) found; \(\alpha\ge 19\) **timeout**. Timeout ≠ proof. Residual is 5a/7a `c-decide`. |
| 7a | 3 | 81.13 s | Paley cert | Residual 186: no 19-IS, \(3.52\times 10^7\) nodes. Nodes \(\times 1/6\) vs 5a; wall **worse**. Yu 1.4 s not reached. |
| 7b | 1 | 400.56 s | 228 | Other \((i,j)\), \(p\le 400\). No `CELL?`. Residual always had a 17/18-IS. Width skip \(p=353\) residual 264. |
| 7c | 6 | 83.16 s | 163 | SAT \(\max\lvert S\rvert\). Greedy \(\alpha=7\)–\(14\); leftover still a 16-IS. Generator worked; cell machine did not. |
| 7d | 2 | 4.77 s | 0 | \(R(3,50)\), \(n=501\)–\(521\). Leftover 346–374 \(>256\). Width skip. |
| 7e | 4 | 0.61 s | 0 | 2-block \(m\in\{29,41,53,61\}\). Never \(K_4\)-free; \(n\le 122<200\). |
| 7f | 5 | 0.37 s | 1 | \(W(3,7)\) leftover 84, exact \(\alpha=21\), \(R(4,22)>84\) vs 314. Catalogue. |
| **7c1** | 6′ | **1098.06 s** | **0** | CEGIS: **181** pools, **13935** cuts, **0** timeouts, **30** pool-UNSAT. No `CELL?`. |

7c1 log on the Mac after scp: `data/phase7-7c1.log` (5.0 MB, 30 Aug 20:23 PHT).
Promote it with `bash scripts/mac-finish-archive.sh`.

## Still true

- \(R(4,20)\ge 252\)
- Paley(17) exact \(\omega=\alpha=3\)
- Yu leftover 186: no 19-IS under `c-decide` (5a and 7a)
- Width gate held. Timeout ≠ accept. Mixed-set hole not used as a cell.

## Replay

Local wiring (not a hunt):

```
RAMSEY_FORCE_7=1 python3 -u -m engine.cli --job 7c1 --scale local
python3 engine/test_kernels.py
```

A40 hunt (do not re-run unless you mean a new search):

```
python3 -u -m engine.cli --job 7c1 --scale runpod
```

## Where the bits live

| Object | Git clone | Downloads |
|---|---|---|
| 2a Hoffman catalogue (~14 MB) | `data/a40/catalog-2a.json` | rsync of clone |
| 4a–4c dumps | `data/a40/catalog-4abc.json` | same |
| Pod keep before phase5 reset | `data/a40/pod-keep/` | `a40-from-pod/keep-a40/` |
| Phase5 log, cert, env | `data/phase5/` | `phase5-from-pod/` |
| Phase7+7c1 log | `data/phase7/` after Mac script | `phase7-from-pod/` |
| Yu \(S\) | `data/yu_r4_20.json` | same |
| This night’s write-up | `docs/PHASE7-CAMPAIGN.md` `docs/JOB-7C1.md` | same |
