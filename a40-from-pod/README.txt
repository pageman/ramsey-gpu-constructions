A40 RunPod artefacts land here after:

  export RAMSEY_POD_HOST=<ip from RunPod UI>
  export RAMSEY_POD_PORT=<ssh port from RunPod UI>
  ./scripts/sync-to-downloads.sh

Expected files (from container 3631e8666026, last seen 29 Aug 2026):
  catalog.json          ~15 MB, mtime 18:18Z — 2a Hoffman catalogue (write_catalog
                        before 3d finished; does not include 3d n=13/14)
  registry.jsonl        ~2.3 MB, mtime 19:12Z — append-only; includes 2a +
                        3d n=13 (N=8192, k>66) and n=14 (N=16384, k>129)
  mask_ranker.json      Hoffman ranker from job 2a
  bound_ledger.json
  ramsey_constructions.csv

Those files are NOT in git (too large / pod-only). Pull them before you Stop
the pod. Do not Terminate (volume wipe).
