"""Merge job output into the dashboard catalog (CSV + three JSON copies)."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from . import backend
from .gap import DONE_IN_RUN001, GAP
from .run import frankl_wilson_n, oeis_reference, erdos_bound, fit_exponential

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public" / "data"
SRC_DATA = ROOT / "src" / "data"


def load_catalog() -> dict:
    path = DATA / "catalog.json"
    if not path.exists():
        return {"graphs": [], "gap": GAP, "run001_done": DONE_IN_RUN001}
    return json.loads(path.read_text())


def upsert_graphs(new_rows: list[dict]) -> dict:
    cat = load_catalog()
    by_id = {g["graph_id"]: g for g in cat.get("graphs", [])}
    for row in new_rows:
        clean = {k: v for k, v in row.items() if _jsonable(v)}
        by_id[clean["graph_id"]] = clean
    rows = list(by_id.values())
    rows.sort(key=lambda r: (r.get("construction_type", ""), r.get("N", 0), r.get("graph_id", "")))
    types = sorted({r["construction_type"] for r in rows})
    fits = [fit_exponential(rows, t) for t in types]
    fits.append(fit_exponential(rows, None))
    best = []
    for t in types:
        cand = [r for r in rows if r["construction_type"] == t and r.get("is_k_free")]
        if not cand:
            continue
        b = max(cand, key=lambda r: r.get("n_1_over_k", 0))
        best.append(
            {
                "construction_type": t,
                "graph_id": b["graph_id"],
                "N": b["N"],
                "k_target": b["k_target"],
                "n_1_over_k": b["n_1_over_k"],
                "run001": b.get("run001"),
                "gpu_kernel": b.get("gpu_kernel"),
            }
        )
    payload = {
        **cat,
        "device": backend.device_name(),
        "n_graphs": len(rows),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run001_done": DONE_IN_RUN001,
        "gap": GAP,
        "fits": fits,
        "oeis_a000791": cat.get("oeis_a000791") or oeis_reference(),
        "reference_curves": cat.get("reference_curves")
        or [
            {"name": "Erdős probabilistic", "points": [{"k": k, "N": erdos_bound(k)} for k in range(3, 16)]},
            {"name": "Frankl–Wilson (explicit, inverted)", "points": [{"k": k, "N": frankl_wilson_n(k)} for k in range(3, 16)]},
            {"name": "Target C=1.01 exponential", "points": [{"k": k, "N": 1.01 ** k} for k in range(3, 16)]},
        ],
        "graphs": rows,
        "best_by_type": best,
        "heatmaps": cat.get("heatmaps") or {},
    }
    return payload


def write_catalog(payload: dict) -> None:
    for d in (DATA, PUBLIC, SRC_DATA):
        d.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str, allow_nan=False)
    for dest in (DATA / "catalog.json", PUBLIC / "catalog.json", SRC_DATA / "catalog.json"):
        dest.write_text(text)
    rows = payload.get("graphs") or []
    if rows:
        keys: list[str] = []
        seen = set()
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        csv_path = DATA / "ramsey_constructions.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        (PUBLIC / "ramsey_constructions.csv").write_text(csv_path.read_text())


def _jsonable(v: Any) -> bool:
    if v is None or isinstance(v, (bool, int, float, str)):
        return True
    if isinstance(v, (list, dict)):
        return True
    return False
