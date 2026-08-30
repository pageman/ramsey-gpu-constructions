# Extreme reproducibility

Two copies of every run artifact:

1. **Git clone** `~/ramsey-gpu-constructions` — Cursor Desktop, Origin
   after `git push origin main`, GitHub after `git push github main`.
2. **Downloads snapshot** `~/Downloads/Ramsey-GPU-Constructions/` —
   rsync of the clone plus labelled campaign folders. **No `.git`.**
   Do not `git push` from there.

Published cell is still **252**. No `CELL?` in 2a–7f or 7c1 that beats
Radziszowski. GitHub:
[pageman/ramsey-gpu-constructions](https://github.com/pageman/ramsey-gpu-constructions)
(this session updates Origin; the Mac `git push github main` publishes
that tree).

## What you must have to replay

| Piece | Path | SHA / note |
|---|---|---|
| Code that ran 7c1 | git `98473e5` | `Add job 7c1` |
| Code that ran 5a | `data/phase5/meta/git-head.txt` | `07a4e8c` |
| Yu published \(S\) | `data/yu_r4_20.json` | residual 186 |
| Residual cert (5a) | `data/phase5/yu_r4_20.cert.json` | no 19-IS, 63.17 s |
| Decide kernel source | `engine/kernels/native_decide.c` | rebuild `.so` |
| 2a catalogue | `data/a40/catalog-2a.json` | ~14 MB Hoffman |
| 4a–4c dumps | `data/a40/catalog-4abc.json` | 354 is **void** |
| Phase5 log | `data/phase5/phase5.log` | 5a–5f |
| Phase7+7c1 log | `data/phase7/phase7.log` | after Mac script |
| Scale knobs | `engine/scale.py` | `local` vs `runpod` |
| 7c1 operator guide | `docs/JOB-7C1.md` | CEGIS contract |
| Campaign write-ups | `docs/A40-CAMPAIGN.md` `docs/PHASE5-CAMPAIGN.md` `docs/PHASE7-CAMPAIGN.md` | |

## Archive 2a–7c1 into git + Downloads (Mac, now)

Prompt must be `paulpajo@…MacBook-Pro`. You already scp’d the 5 MB log
to `data/phase7-7c1.log`.

```
cd ~/ramsey-gpu-constructions
git fetch origin
git merge origin/main
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
bash scripts/mac-finish-archive.sh
```

If the pod is already **Stopped**, the script still works: it promotes
`data/phase7-7c1.log`, rsyncs the clone, and writes
`~/Downloads/Ramsey-GPU-Constructions/`. Connection refused is OK.

Then publish from the **clone** (not Downloads):

```
git add data/phase7 docs/PHASE7-CAMPAIGN.md docs/REPRODUCING.md
git commit -m "Archive phase7 and 7c1 A40 log."
git push github main
git push origin main
```

`origin` on the Mac is Cursor Origin. `github` is the public repo.

To skip SSH entirely: `RAMSEY_SKIP_POD=1 bash scripts/mac-finish-archive.sh`

## Older: pack a live pod tarball (phase5-era)

```
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
bash scripts/mac-archive-repro.sh
```

That still builds `repro-from-pod/ramsey-repro.tgz` if the pod is up.

## Replay 5a (residual 186)

```
cd ~/ramsey-gpu-constructions
RAMSEY_SCALE=runpod RAMSEY_5A_LIMIT=1800 OMP_NUM_THREADS=12 \
  python3 -u -m engine.cli --job 5a --scale runpod
```

Expect ~63 s, `found=false`, `timed_out=false`. Do not announce a cell.

## Replay 7c1 wiring only

```
RAMSEY_FORCE_7=1 python3 -u -m engine.cli --job 7c1 --scale local
python3 engine/test_kernels.py
```

## Directory map

```
~/ramsey-gpu-constructions
  data/a40/                 2a + 4abc dumps (committed)
  data/a40/pod-keep/        A40 catalogues saved before phase5 reset
  data/phase5/              5a–5f log, cert, env, SHA256
  data/phase7/              7a–7f + 7c1 log after mac-finish-archive
  data/yu_r4_20.json        Yu S
  docs/PHASE7-CAMPAIGN.md   this night’s scoreboard
  docs/JOB-7C1.md           CEGIS operator guide

~/Downloads/Ramsey-GPU-Constructions     no .git
  SNAPSHOT.txt
  a40-from-pod/             copy of data/a40
  phase5-from-pod/
  phase7-from-pod/
  data/  docs/  engine/     rsync of the clone
```

## What not to commit

- `engine/kernels/*.so` at the source path (A40 copies may live under
  `data/phase5/binaries/` or `data/phase7/`)
- live scratch `data/phase7.log` at repo root (gitignored); the archive
  copy is `data/phase7/phase7.log`
- `data/phase7-7c1.log` (scp landing pad; gitignored after this commit)
- `~/Downloads/…`
- secrets / RunPod API keys
