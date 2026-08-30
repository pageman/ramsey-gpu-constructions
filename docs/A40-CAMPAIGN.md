# A40 campaign (28–30 Aug 2026)

What actually ran on RunPod pod `armed_yellow_buzzard` (A40), and what it
did **not** prove. Success criterion was a published finite +1 in
Radziszowski DS1, not Erdős #78.

**No survey cell moved.** Yu’s \(R(4,20)\ge 252\) is still the headline
for that diagonal. Paley(17) is still the best exact diagonal in this
repo (\(\omega=\alpha=3\), \(R(4,4)>17\)).

## Where the files live

| What | Where |
|---|---|
| Engine + jobs `1a`–`4c` | this git tree (`main` after `a49da0c`) |
| Job 2a catalogue (~14 MB, ~9288 Hoffman rows) | Mac `~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/catalog-2a.json` |
| Jobs 4a/4c catalogue (436 KB) | same folder, `catalog.json` |
| Append-only run log | `registry.jsonl` in that folder |
| Ledger | `bound_ledger.json` in that folder |
| In-tree `data/catalog.json` | local / tarball scale, **not** the 2a sweep |

The 14 MB 2a catalogue **is** in git under `data/a40/catalog-2a.json`.
The dashboard still reads the small `data/catalog.json` tree.

## Jobs

| Job | What ran | Outcome |
|---|---|---|
| 1a Paley | A40 recertify | No new exact diagonal |
| 1b–1d | F2 / GQ / FW | Certificates only |
| **2a** | Cyclotomic Hoffman enum \(p\le 9973\) | **99755 s**, 9288 graphs. No cell. tmux `ramsey` |
| 2c | Circulant \(R(3,k)\) | 46 graphs, 29 s, no table beat |
| 3a | Block-circulant | No diagonal cell |
| 3b | Hoffman ILS | Never recertified Yu \(S\); ~59 graphs |
| 3c | GQ scale-up | q=11,13 Hoffman only |
| **3d** | ANF n=13,14 | n=13 `N=8192` and n=14 `N=16384` in registry; hung / died (old `max_clique` n>64). n=15/16 never emitted |
| **4a** | Yu 2-class pool, p∈[200,400], 64 walks | **1715 s**, 6 catalog rows. See false cells below |
| **4b** | Circulant \(R(3,50)\), n=501–521 | **8.56 s**, 0 graphs (every residual >280 skipped) |
| **4c** | \(K_4\)-clean W(3,7) | leftover 84, exact \(\alpha=21\), \(R(4,22)>84\). Published cell is \(\ge 314\) |

## Job 4a — do not announce 338 or 354

| `graph_id` | residual | Meaning |
|---|---|---|
| `yu_pool_p251_e5_kindyu_published` | 186 | Yu’s paper \(S\), structural gate only |
| `yu_pool_p337_e4` | **262** | False `exact α=19` — C MIS is n≤256 |
| `yu_pool_p353_e8` | **264** | Same bug; `CELL? R(4,20)≥354` is void |

`engine/kernels/native_mis.c` stores 256 vertices. On n>256 it used to
`return 0` without `timed_out`, and job 4a treated that as “no 19-IS”.
Fixed on `main` after the run (`skip_n>256`, `CELL?` only if the
decision proof finished).

## Operator notes

- Pod SSH (changes on restart): Connect → **SSH over exposed TCP** (SCP).
- Do not **Terminate** (volume wipe). **Stop** is OK after `scp`.
- Old tmux `ramsey` is job 2a leftover. `ramsey4` is gone after phase4.
- Public GitHub: [pageman/ramsey-gpu-constructions](https://github.com/pageman/ramsey-gpu-constructions).
  This cloud session pushes Cursor Origin. Publish GitHub from the Mac:
  `git fetch origin && git merge origin/main && git push github main`.
  Later jobs (5a–7c1) are in `docs/PHASE5-CAMPAIGN.md` and
  `docs/PHASE7-CAMPAIGN.md`.
