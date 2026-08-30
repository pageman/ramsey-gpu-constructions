# A40 run artifacts

`catalog-2a.json` (~14 MB Hoffman sweep), `catalog-4abc.json`,
`registry.jsonl`, and `bound_ledger.json` are the campaign dumps that
were committed after jobs 2a and 4a–4c.

`pod-keep/` is filled by `scripts/mac-archive-repro.sh`. It is a copy of
`/workspace/keep-a40` on the pod — the live catalogues saved **before**
`git reset --hard origin/main` so phase5 could start. Treat those as
the raw disk state of the A40 after 2a/4c, not as a second theorem.

Mac Downloads mirror:

```
~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/
~/Downloads/Ramsey-GPU-Constructions/a40-from-pod/keep-a40/
```
