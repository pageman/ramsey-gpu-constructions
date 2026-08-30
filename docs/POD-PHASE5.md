# Super-granular operator guide: run 5a→5f on the pod in one go

This is the **leave-it-running** procedure for plan v3 (`docs/plan-jobs-5x.md`).
It is written so you can follow it at 3 a.m. without inventing a second
command. Every failure mode from Act VII (wrong machine, pasted `tmux`
and `python` on one line, attached `ramsey` instead of a new session,
`scp` with a literal `<ssh-port>`, Terminate vs Stop) is a numbered
step here.

**Scientific invariant.** #78 is unchanged. Published \(R(4,20)\) is
still **252**. Paley **17** is still the exact diagonal jewel. Job 4a’s
`CELL? R(4,20)≥354` rows are **void**. This wave does not get to shout a
new cell unless 5a is green **and** 5c/5e print `CELL?` under the new
referee (width + timeout≠accept + mixed-set).

---

## 0. What “one go” means

You type **one command on the pod**:

```bash
bash scripts/pod-phase5.sh
```

That script:

1. Refuses to run on a Mac.
2. Finds the repo.
3. Compiles `native_decide.so` (OpenMP) and `native_mis.so`.
4. Creates tmux session **`ramsey5`** (not `ramsey`, not `ramsey4`).
5. Starts `python3 -u -m engine.cli --job phase5 --scale runpod` **inside**
   that session and tees `data/phase5.log`.
6. Prints how to detach / attach / tail.

`phase5` itself is:

```
5a recertify Yu residual 186
    └─ if not alpha_certified → write data/phase5.halt, run 5b (freeze API), STOP
    └─ if green → 5b → 5c → 5d → 5e → 5f
```

You do **not** paste `tmux new` and `python3` in the same block. That is
how `duplicate session: ramsey4` happened and the hunt ran on raw SSH.

You do **not** attach leftover tmux `ramsey` (job 2a, finished). You do
**not** re-run `phase4`.

---

## 1. Three machines (do not mix them)

| Machine | What it is | What you type here |
|---|---|---|
| **Mac** | Your laptop. Git clone `~/ramsey-gpu-constructions`. Remotes: `origin` = GitHub, `cursor` / extra remote = Origin. | `git fetch`, `git merge`, `git push github main`, `scp` **from here**, `ssh` **from here**. Never `tmux`. Never `python3 -m engine.cli --job phase5` unless you want a local smoke. |
| **Pod** | RunPod A40 container. Last nick `armed_yellow_buzzard`. Repo path `/workspace/ramsey-gpu-constructions`. | `bash scripts/pod-phase5.sh`, `tmux attach -t ramsey5`, `bash scripts/phase5-status.sh`. Never `scp` with a placeholder port. |
| **This Cursor agent** | Cloud checkout. Pushes Origin `main` only. Cannot `gh` push. Cannot see your live SSH IP after a restart. | Code + this guide. |

If the prompt is `pageman@…` or `zsh` and `tmux: command not found`, you
are on the **Mac**. Stop. SSH to the pod.

If the prompt is `root@…` and the cwd is `/workspace/…`, you are on the
**pod**. Good.

---

## 2. Preflight on the Mac (before you SSH)

### 2.1 Do not Terminate the pod

- **Stop** = disk stays. SSH IP/port **change** on next start.
- **Terminate** = volume wipe. The 2a catalogue and any in-progress
  `phase5.log` die. Do not Terminate.

If the pod is Stopped, Start it. Then open RunPod → the pod →
**Connect** → **SSH over exposed TCP** (the line meant for `scp` /
ordinary `ssh`, not `ssh.runpod.io`). Copy host and port. They will
look like `root@A.B.C.D -p NNNNN`.

Example from the last campaign (stale; **do not reuse blindly**):

```
ssh root@69.30.85.91 -p 22061 -i ~/.ssh/id_ed25519
```

### 2.2 Publish this tree to a place the pod can pull

On the Mac clone (the folder that **has** `.git`, not
`~/Downloads/Ramsey-GPU-Constructions`):

```bash
cd ~/ramsey-gpu-constructions    # or wherever the real clone lives
git fetch cursor                 # Origin, if that remote exists
git merge cursor/main            # take the agent’s 5a–5f commit
git push origin main             # GitHub public
git push cursor main             # optional, keep Origin even
```

If you do not have an Origin remote on the Mac, fetch however you
usually pull agent commits, then `git push github main` / `git push origin main`.

You need these files on the pod, not just in chat:

- `engine/phase5.py`
- `engine/kernels/native_decide.c`
- `engine/kernels/decide_alpha.py`
- `scripts/pod-phase5.sh`
- `scripts/phase5-status.sh`
- `data/yu_r4_20.json` (already there if the 4a tree is there)

### 2.3 Optional: tarball if `git pull` on the pod is painful

From the Mac clone:

```bash
cd ~/ramsey-gpu-constructions
tar czf /tmp/ramsey-phase5.tgz \
  engine/phase5.py engine/jobs.py engine/cli.py engine/registry.py engine/scale.py \
  engine/kernels/native_decide.c engine/kernels/decide_alpha.py engine/kernels/bitset_mcs.py \
  engine/constructions.py \
  scripts/pod-phase5.sh scripts/phase5-status.sh \
  docs/POD-PHASE5.md docs/plan-jobs-5x.md \
  data/yu_r4_20.json
```

You will `scp` this **from the Mac** after you know the live IP/port
(step 3).

---

## 3. SSH to the pod (from the Mac)

```bash
# replace HOST PORT with Connect → SSH over exposed TCP
ssh root@HOST -p PORT -i ~/.ssh/id_ed25519
```

Checks after login:

```bash
hostname
pwd
whoami
# expect: a linux hostname, /root or /workspace, root
command -v tmux
command -v gcc
command -v python3
ls /workspace/ramsey-gpu-constructions/engine/cli.py
tmux ls || true
# leftover 'ramsey' = finished 2a. Do not attach it to start phase5.
# leftover 'ramsey4' = finished phase4, or gone. Do not reuse it.
```

If `tmux` is missing:

```bash
apt-get update && apt-get install -y tmux build-essential
```

---

## 4. Get this commit onto the pod

**Preferred — git:**

```bash
cd /workspace/ramsey-gpu-constructions
git status
git fetch origin
git checkout main
git pull origin main
git log -1 --oneline
# expect a commit that adds engine/phase5.py and scripts/pod-phase5.sh
test -f engine/phase5.py && test -f scripts/pod-phase5.sh && test -f engine/kernels/native_decide.c
python3 -m engine.cli --list
# must print 5a 5b 5c 5d 5e 5f phase5
```

If the pod’s `origin` is stale or auth-blocked, use the tarball
**from a second Mac terminal** (not from the pod):

```bash
# ON THE MAC, after you have HOST and PORT
scp -P PORT -i ~/.ssh/id_ed25519 /tmp/ramsey-phase5.tgz root@HOST:/tmp/ramsey-phase5.tgz
```

Then **on the pod**:

```bash
cd /workspace/ramsey-gpu-constructions
tar xzf /tmp/ramsey-phase5.tgz
python3 -m engine.cli --list
```

Do **not** type `scp -P <ssh-port>` on the pod. The brackets are not a
port.

---

## 5. The one command (this is the whole job)

Still **on the pod**:

```bash
cd /workspace/ramsey-gpu-constructions
bash scripts/pod-phase5.sh
```

You should see:

- `compiling native_decide`
- `jobs_ok 5a 5b 5c 5d 5e 5f phase5`
- `phase5 is running in tmux session: ramsey5`
- a `tmux ls` line with `ramsey5`
- the first `[5a] Yu residual decision` lines, or “log not flushed yet”

**Now leave.** You may close the SSH window. tmux keeps the process.
Laptop sleep does not kill it (that was the SIGHUP death of 2a before
tmux existed).

If you are still in an attached pane (you should not be — the script
starts **detached**), detach with **Ctrl-B**, then **D**. Two keys,
not `Ctrl-B D` as a single chord.

### 5.1 What you must not type

| Forbidden | Why |
|---|---|
| `tmux new -s ramsey5` **and** `python3 -m engine.cli …` in one paste | `duplicate session` → python runs on raw SSH → laptop sleep kills it |
| `tmux attach -t ramsey` | That session is leftover **2a**. You will stare at a finished Hoffman sweep. |
| `tmux new -s ramsey4` | phase4 is done. 4a’s false 354 must not be replayed on the old `.so`. |
| `RAMSEY_JOB=4a` / `phase4` | Wrong wave. |
| `Terminate` in the RunPod UI | Wipes the volume. |
| A second `bash scripts/pod-phase5.sh` while python is live | Script refuses (exit 3). Good. |

### 5.2 Watching without attaching

New SSH (Mac → pod), then:

```bash
cd /workspace/ramsey-gpu-constructions
bash scripts/phase5-status.sh
tail -f data/phase5.log
```

`Ctrl-C` only kills `tail`, not the job.

Attach only if you want the live pane:

```bash
tmux attach -t ramsey5
# leave: Ctrl-B, D
```

---

## 6. What each job prints (so you know it is alive)

### 6a. Job 5a — recertify Yu residual 186

You must see, in order:

1. `[5a] Yu residual decision  α<19  limit=1800s`
2. `structural=True  residual=186`
3. `CP-SAT 18-IS …` (or `ortools not installed` — that is OK)
4. `decide α≥19 found=False timed_out=False nodes=… backend=c-decide-omp`
   **or** `found=True` / `timed_out=True` (fail). A 30 Aug 2026
   measurement on this kernel: **200 million nodes / 45 s / timeout**
   on Yu’s 186-vertex residual (matching UB on; OpenMP on). Yu’s paper
   is \(2.7\times 10^7\) nodes / 1.4 s. Same node-rate class, **worse
   pruning**. Expect the 1800 s cap unless the A40 OpenMP tree dies
   early.
5. `wrote …/data/yu_r4_20.cert.json  alpha_certified=True|False`

**Green.** `alpha_certified=True`, `found=False`, `timed_out=False`.
File `data/yu_r4_20.cert.json` has `"alpha_certified": true`. No
`data/phase5.halt`. phase5 continues.

**Red.** `timed_out=True` or `found=True` (a 19-IS would **refute** Yu
and must be treated as a bug until a second backend agrees). Writes
`data/phase5.halt`. Runs 5b only. **Stops.** Further 4a/5c nights are
forbidden. Published number stays **252**.

5a is **not** a new cell. It is stage three of Yu’s already-published
252.

### 6b. Job 5b — referee freeze

1. `n=257 skip OK`
2. `Paley(17) decision` with `exact=True` (ω=3, residual α)
3. `toy mixed …`
4. If 5a halted: 5b still runs, then phase5 exits.

If 5b raises `5b contract failed`, the kernel is wrong. Stop the
session (`tmux kill-session -t ramsey5`) and do not hunt.

### 6c. Job 5c — Yu pool hunt (only if 5a green)

1. `hunt p∈[200,400] walks=64`
2. `skip p=… min_resid=…>256` for fat residuals (this is the 337/353
   fix). Those rows must **never** print `CELL?`.
3. Walks: `|S|=… tri_free=… greedyα=…`
4. Occasional `residual_only` — residual accepted, mixed-set not
   proved. **Not a cell.**
5. `CELL?` only if `mixed_ok` and `p+1` beats `R4_LOWER`.

4a wall time was **1715 s** on this A40. 5c should be similar or
shorter (more skips). Checkpoints append `{"job":"5c","checkpoint":true,"p":…}`
to `data/registry.jsonl`.

### 6d. Job 5d — \(R(3,t)\) \(t\ge 50\), middle-third seed

1. `middle-third seed` (not the empty mask that made 4b print 0 graphs)
2. `n=501 seed |S|=…` … through 521 odd
3. `skip residual>256` is the expected majority outcome
4. No Coniglio 24–49 hunt

### 6e. Job 5e — polarity leftover + floor gate

1. `W(3,7) K4-clean… leftover=84` (same as 4c)
2. `exact but below floor` — \(R(4,22)>84\) vs published \(\ge 314\).
   **Not a cell.**
3. `q=11,13` only if leftover ≤256 **and** `N+1` beats the floor
   (runpod `gq_clean_q` is `(7,)` unless you changed scale)

### 6f. Job 5f — catalogue hour

1. `TG_3,2` / `TG_4,2` / `TG_5,2` Hoffman vs Paley
2. Yip-poly \(p=17,29,37\) vs Paley at the same \(p\)
3. Will not beat Paley(17) on exact diagonal \(C\)

Then: `== phase5 done ==` and the tmux pane sits so the tail remains
readable.

---

## 7. Fermi estimate (rigorous, with ranges)

Zulu = UTC. GMT+8 = Asia/Singapore (Philippine clock). Add **+8 hours**
to every Zulu clock below.

Let **T0** be the UTC instant `pod-phase5.sh` prints
`[phase5] start …Z`. Example if you start at **05:00Z on 30 Aug 2026**
(13:00 GMT+8 the same calendar day):

### 7.1 Work items and rates

| Item | Model | Source of the rate |
|---|---|---|
| 5a decision tree | Yu: \(2.7\times 10^7\) nodes, 1.4 s wall, 12 OpenMP threads ⇒ \(\approx 1.9\times 10^7\) nodes/s aggregate, \(\approx 1.6\times 10^6\) nodes/s per thread | arXiv:2608.18169 |
| 5a, this kernel, **decision** (not Östergård dolls) | Same node count if pruning matches; 10×–100× if it does not | 4a timed out at 25 s on **exact-α dolls**, which is a different algorithm |
| 5a cap | 1800 s wall (`RAMSEY_5A_LIMIT`, `yu_5a_limit`) | this repo; 45 s already exhausted \(2\times 10^8\) nodes without a decision |
| CP-SAT 18-IS | seconds–tens of seconds if `ortools` exists; else 0 | Yu used it as a lower bound only |
| 5b | \(O(1)\) + Paley(17) MIS + toy mixed | should be < 30 s |
| 5c search | 4a: **1715 s**, 64 walks, \(p\in[200,400]\), greedy killed almost every walk | A40 29 Aug 2026 |
| 5c extra skips | pools with `min_resid>256` do not call MIS | new; **saves** time vs 4a |
| 5c disaster | one Yu-class residual × 25–600 s each × up to `yu_mis_keep=8` per pool | only if many residuals look like 186 |
| 5d | 11 odd \(n\) × 80 ILS steps + skip if residual >256 | 4b was **8.56 s** empty; seed adds cheap ILS, not 11 hard MIS |
| 5e | 4c was **1.58 s** at leftover 84 | floor gate adds 0 |
| 5f | FFT/Hoffman on \(n\le 341\) | ~10–60 s |
| GPU | not in the inner loop | 4a/2a were CPU; A40 is a **CPU rental** again |

### 7.2 Three clocks (start = T0)

**A. 5a fails (most important clock to believe).**

- 5a runs until timeout **1800 s** (or finishes early with `found`/`timeout`).
- 5b ~20 s.
- Halt. 5c–5f skipped.

| | Seconds | If T0 = 05:00:00Z / 13:00:00 GMT+8 |
|---|---|---|
| 5a | 45–1800 | 05:00:45–05:30Z / 13:00:45–13:30 GMT+8 |
| 5b | +20 | 05:31Z / 13:31 |
| **Done (halt)** | **≈ 1–31 min** | **05:02–05:31Z / 13:02–13:31 GMT+8** |

This is the **expected** outcome if the decision kernel is still weaker
than Yu’s 1.4 s OpenMP. It is **not** a failed night. It is the
measurement the last campaign did not finish.

**B. Typical green path (5a in Yu’s complexity class).**

Assume decision-only + 12 threads explores \(\sim 10^7\) nodes in 2–40 s
(1×–30× slower than Yu, still under the cap). Then 5c ≈ 4a.

| Job | Fermi seconds | Cumulative from T0 | Clock if T0=05:00Z | Clock if T0=05:00Z in GMT+8 |
|---|---|---|---|---|
| 5a | 5–40 if Yu-class; else up to 1800 | 0:00–0:30 | 05:00–05:30Z | 13:00–13:30 |
| 5b | 15–40 | 0:01–0:11 | 05:01–05:11Z | 13:01–13:11 |
| 5c | 1200–2400 (20–40 min) | 0:21–0:51 | 05:21–05:51Z | 13:21–13:51 |
| 5d | 10–90 | 0:22–0:53 | 05:22–05:53Z | 13:22–13:53 |
| 5e | 2–15 | 0:22–0:53 | 05:22–05:53Z | 13:22–13:53 |
| 5f | 15–90 | 0:23–0:55 | 05:23–05:55Z | 13:23–13:55 |
| **Done** | **≈ 25–60 min** | | **05:25–06:00Z** | **13:25–14:00 GMT+8** |

Central estimate if 5a is 15 s and 5c matches 4a (1715 s):

\[
15 + 25 + 1715 + 30 + 5 + 40 \approx 1830\ \mathrm{s} \approx 30.5\ \mathrm{min}.
\]

**Finish ≈ T0 + 31 min.** Example: **05:31Z / 13:31 GMT+8**.

**C. Pessimistic green path (5a slow, 5c hits several 186-class residuals).**

- 5a: 1200–1800 s (finishes near cap).
- 5c: 4a’s 1715 s + 8 extra MIS × 60 s = +480 s ⇒ ~37 min, or
  8 × 10 pools × 120 s = +9600 s ≈ 2.7 h if many residuals need a full
  tree (unlikely: 4a showed greedy already kills the walks).
- 5d: if a residual **does** fall ≤256, one target-49 decision can
  eat the 25 s cap × 11 \(n\) = 275 s and still not certify.

| | Seconds | If T0 = 05:00Z / 13:00 GMT+8 |
|---|---|---|
| 5a | 1800 | 05:30Z / 13:30 |
| 5b | 40 | 05:11Z / 13:11 |
| 5c typical-pessimistic | 2400–7200 | 05:51–07:11Z / 13:51–15:11 |
| 5d–5f | 60–400 | +few min |
| **Done** | **≈ 1–3 h** | **06:00–08:15Z / 14:00–16:15 GMT+8** |

**Disaster bound** (do not plan the night on this): 5c calls 50 full
600 s decisions. \(50\times 600 = 30000\) s ≈ **8.3 h**. Finish
**13:20Z / 21:20 GMT+8** if T0=05:00Z. The skip `min_resid>256` exists
to make this bound fictional. If `phase5.log` shows a MIS hanging past
10 minutes on one row, attach and read `nodes=`; you may
`tmux kill-session -t ramsey5` — the halt file is only for 5a, so a
stuck 5c is a manual stop.

### 7.3 Conversion cheat sheet

| Zulu (UTC) | GMT+8 |
|---|---|
| 00:00 | 08:00 same date |
| 05:00 | 13:00 |
| 06:00 | 14:00 |
| 08:00 | 16:00 |
| 12:00 | 20:00 |
| 16:00 | 00:00 **next** date |
| 18:00 | 02:00 next date |

On the pod:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
TZ=Asia/Singapore date +%Y-%m-%dT%H:%M:%S%z
```

`phase5.status.json` timestamps are **Zulu** (`…Z`).

### 7.4 When to look (if T0 unknown)

1. **T0 + 2 min** — log must exist; `[5a]` line must exist. If not, the
   script never started (wrong machine / compile fail).
2. **T0 + 32 min** — 5a has either greened, halted, or just hit the
   1800 s cap. Run `bash scripts/phase5-status.sh`.
3. **T0 + 40 min** — on the typical green path, 5c is finishing or 5f
   is done.
4. **T0 + 3 h** — pessimistic green should be done. If `tmux ramsey5`
   still shows `python` and `status.job` is `5c` with a stuck `p`,
   read the last MIS line.
5. **T0 + 10 h** — something is wrong (2a-class hang). Kill the
   session. Do not leave an A40 on a silent Python colouring.

---

## 8. After it finishes

### 8.1 On the pod

```bash
bash scripts/phase5-status.sh
grep -n "CELL?" data/phase5.log || true
grep -n "HALT" data/phase5.log || true
python3 -c "import json; print(json.load(open('data/yu_r4_20.cert.json')).get('alpha_certified'))"
```

Copy off the pod **from the Mac** (HOST/PORT from Connect again):

```bash
mkdir -p ~/Downloads/Ramsey-GPU-Constructions/phase5-from-pod
scp -P PORT -i ~/.ssh/id_ed25519 \
  root@HOST:/workspace/ramsey-gpu-constructions/data/phase5.log \
  root@HOST:/workspace/ramsey-gpu-constructions/data/phase5.status.json \
  root@HOST:/workspace/ramsey-gpu-constructions/data/yu_r4_20.cert.json \
  root@HOST:/workspace/ramsey-gpu-constructions/data/registry.jsonl \
  root@HOST:/workspace/ramsey-gpu-constructions/data/bound_ledger.json \
  root@HOST:/workspace/ramsey-gpu-constructions/data/catalog.json \
  ~/Downloads/Ramsey-GPU-Constructions/phase5-from-pod/
```

Then **Stop** the pod (not Terminate) if you do not need another wave.

### 8.2 What you are allowed to say

| Log line | Say |
|---|---|
| `alpha_certified=true` | “This kernel decided Yu’s 186-vertex residual: no 19-IS.” Recertify, not a new bound. |
| `alpha_certified=false` / HALT | “Referee still cannot finish 186. Number is still 252. No hunt.” |
| `CELL?` **and** residual ≤256 **and** `mixed_ok` **and** `p+1` > published | Show the `graph_id`, `shash`, cert JSON. Then a second solver. |
| `CELL?` with residual 262/264 | **Void.** Same bug as 4a. Do not announce 338 or 354. |
| 5e `R(4,22)>84` | Exact and weak. Survey is 314. |
| 5f Hoffman \(k\) | Catalogue. Not \(C\ge 1.01\). |

---

## 9. Environment knobs (optional, before the one command)

```bash
export RAMSEY_5A_LIMIT=1800     # 5a wall seconds (default runpod 1800)
export OMP_NUM_THREADS=12       # Yu used 12
export RAMSEY_SCALE=runpod
export RAMSEY_FORCE_5C=1        # NEVER for a real night; bypasses 5a halt
export RAMSEY_TMUX_SESSION=ramsey5
```

Local laptop smoke (not the night):

```bash
RAMSEY_SCALE=local RAMSEY_5A_LIMIT=8 python3 -u -m engine.cli --job 5b --scale local
```

`5a` on `local` uses a 20 s cap and will likely **halt**. That is the
correct local behaviour.

---

## 10. Failure → fix table

| Symptom | Machine | Fix |
|---|---|---|
| `WRONG MACHINE` | Mac | SSH to the pod, run the script there |
| `tmux: command not found` | Mac | You are on the Mac |
| `tmux: command not found` | Pod | `apt-get install -y tmux` |
| `duplicate session: ramsey5` | Pod | You pasted `tmux new` by hand. `tmux kill-session -t ramsey5` only if python is **not** the hunt you want, then `bash scripts/pod-phase5.sh` |
| Script exit 3 | Pod | Hunt already running. `tmux attach -t ramsey5` |
| `unknown job phase5` | Pod | Old tree. Pull / untar step 4 |
| `[5a]` never appears | Pod | `tail data/phase5.log`; `tmux attach -t ramsey5`; compile error is in the first 20 lines |
| SSH dies, job dies | Pod | You ran python **outside** tmux. Start over with the script |
| IP/port changed | Mac | Pod was Stopped/Started. New Connect line |
| `CELL?` 354 | — | Bug regression. `grep residual data/phase5.log`. If \(n>256\), void |
| Want to stop | Pod | `tmux kill-session -t ramsey5`. Then Stop (not Terminate) the pod |

---

## 11. Order of operations (checklist you can print)

- [ ] Pod is **Started**, not Terminated
- [ ] Mac has latest `main` (this guide + `engine/phase5.py`)
- [ ] Mac `ssh` using **SSH over exposed TCP**
- [ ] Pod `git pull` or tarball extract; `python3 -m engine.cli --list` shows `phase5`
- [ ] `tmux ls` inspected; you will **not** attach `ramsey`
- [ ] `bash scripts/pod-phase5.sh`
- [ ] First `[5a]` line exists
- [ ] Close SSH / sleep the Mac
- [ ] T0+32 min: `phase5-status.sh` — green or halt
- [ ] If halt: Stop pod, scp cert, stop. Number is 252
- [ ] If green: wait T0+40 min (typical) or T0+3 h (pessimistic)
- [ ] scp log + cert + registry **from the Mac**
- [ ] Stop pod
- [ ] Do not announce a cell unless mixed_ok and residual ≤256

Until 5a is green, another construction family is a catalogue hour.
The numbers that matter are **186** (did 5a decide it?) and **256**
(did the kernel refuse anything larger?).
