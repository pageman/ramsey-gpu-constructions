# Extreme reproducibility

Two copies of every run artifact:

1. **Git clone** `~/ramsey-gpu-constructions` — this is what Cursor
   Desktop opens, what Origin sees after `git push origin main`, and
   what GitHub serves after `git push github main`.
2. **Downloads snapshot** `~/Downloads/Ramsey-GPU-Constructions/` —
   rsync of the clone plus pod pulls. It has **no `.git`**. Do not
   `git push` from there.

## What “enough to replay 5a–5f” means

You need all of:

- git commit that ran (`07a4e8c` for the 30 Aug 2026 night)
- `data/yu_r4_20.json` (Yu’s published \(S\))
- `engine/kernels/native_decide.c` and the A40 `native_decide.so`
- `data/phase5/yu_r4_20.cert.json` (the 186-vertex decision)
- `data/phase5/phase5.log` and `phase5.status.json`
- `data/phase5/meta/env.txt` (`uname`, `gcc -v`, `nvidia-smi -L`, limits)
- `data/a40/` (committed 2a / 4abc dumps) and `data/a40/pod-keep/`
  (catalogues copied aside before `git reset --hard` on the pod)
- this file and `docs/PHASE5-CAMPAIGN.md`

Replay 5a only:

```
cd /path/to/ramsey-gpu-constructions
RAMSEY_SCALE=runpod RAMSEY_5A_LIMIT=1800 OMP_NUM_THREADS=12
python3 -u -m engine.cli --job 5a --scale runpod
```

Expect ~63 s on an A40-class CPU tree, `alpha_certified=true`, no
second backend unless `ortools` is installed.

## Archive from the live pod (Mac only)

Prompt must be `paulpajo@…MacBook-Pro`, not `root@`.

```
cd ~/ramsey-gpu-constructions
git fetch origin
git merge origin/main
export RAMSEY_POD_HOST=69.30.85.91
export RAMSEY_POD_PORT=22061
bash scripts/mac-archive-repro.sh
```

That script copies `pod-pack-repro.sh` to the pod, builds one tarball
(`/workspace/ramsey-repro-*.tgz`), pulls it to the Mac, and writes:

| Destination | Contents |
|---|---|
| `data/phase5/` | log, status, cert, post-phase5 catalog/registry/ledger, `.so`, `meta/`, `SHA256SUMS` |
| `data/a40/pod-keep/` | `/workspace/keep-a40` (2a/4a catalogues saved before reset) |
| `~/Downloads/Ramsey-GPU-Constructions/phase5-from-pod/` | same phase5 tree |
| `~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/keep-a40/` | same keep |
| `~/Downloads/Ramsey-GPU-Constructions/repro-from-pod/ramsey-repro.tgz` | the single blob |
| `~/Downloads/Ramsey-GPU-Constructions/` | full rsync of the clone (via `sync-to-downloads.sh`) |

Then publish (Mac clone only):

```
git add data/phase5 data/a40/pod-keep docs/PHASE5-CAMPAIGN.md docs/REPRODUCING.md
git commit -m "Archive phase5 run and pod-keep 2a/4a catalogues."
git push github main
git push origin main
```

`origin` on the Mac is Cursor Origin. `github` is the public repo.
This cloud agent can only push Origin; you push GitHub.

## Directory map

```
~/ramsey-gpu-constructions          Cursor project / git clone
  data/a40/                         already-committed 2a + 4abc
  data/a40/pod-keep/                live pod copies from keep-a40
  data/phase5/                      this night
  docs/PHASE5-CAMPAIGN.md           what the night proved
  docs/A40-CAMPAIGN.md              2a–4c negatives
  docs/REPRODUCING.md               this file

~/Downloads/Ramsey-GPU-Constructions
  SNAPSHOT.txt
  a40-from-pod/                     older scp layout
  a40-from-pod/keep-a40/            2a/4a from /workspace/keep-a40
  phase5-from-pod/
  repro-from-pod/ramsey-repro.tgz
```

## What not to commit

- `engine/kernels/*.so` at the source path (rebuild from `.c`)
- live scratch `data/phase5.log` at repo root (the archive copy is
  `data/phase5/phase5.log`)
- `~/Downloads/…` (gitignored)
- secrets / RunPod API keys
