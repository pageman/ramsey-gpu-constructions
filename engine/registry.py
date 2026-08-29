"""Non-overlapping seed registry. Every job reads/writes here; cells are unique."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REG_PATH = ROOT / "data" / "registry.jsonl"
LEDGER_PATH = ROOT / "data" / "bound_ledger.json"

# Job owns a (family, cell) pair. Enforced by writers.
OWNERS = {
    "1a": {"cells": ("cert",), "families": ("paley_prime", "catalogue")},
    "1b": {"cells": ("cert",), "families": ("quadratic_form_f2", "gold_trace_f2")},
    "1c": {"cells": ("R(4,t)-geom",), "families": ("polarity_gq", "polarity_pg2")},
    "1d": {"cells": ("explicit-diag",), "families": ("frankl_wilson", "disperser")},
    "2a": {"cells": ("cert",), "families": ("cyclotomic_union",)},
    "2b": {"cells": ("cert",), "families": ("quadratic_form_f2", "gold_trace_f2", "polarity_gq", "frankl_wilson")},
    "2c": {"cells": ("R(3,k)",), "families": ("circulant_r3",)},
    "3a": {"cells": ("R(k,k)",), "families": ("block_circulant",)},
    "3b": {"cells": ("R(4,k)",), "families": ("circulant_r4",)},
    "3c": {"cells": ("R(4,t)-geom",), "families": ("polarity_gq",)},
    "3d": {"cells": ("explicit-diag",), "families": ("quadratic_form_f2", "gold_trace_f2")},
    "4a": {"cells": ("R(4,t)",), "families": ("yu_pool",)},
    "4b": {"cells": ("R(3,k)",), "families": ("circulant_r3",)},
    "4c": {"cells": ("R(4,t)-geom",), "families": ("polarity_gq",)},
}


def append_record(rec: dict[str, Any], path: Path = REG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = dict(rec)
    rec.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with path.open("a") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def load_records(path: Path = REG_PATH) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def write_ledger(claims: Iterable[dict], path: Path = LEDGER_PATH) -> None:
    """Merge by graph_id so 3d and 4a/4b/4c can finish in either order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if path.exists():
        try:
            existing = list((json.loads(path.read_text()) or {}).get("claims") or [])
        except json.JSONDecodeError:
            existing = []
    by_id = {c.get("graph_id"): c for c in existing if c.get("graph_id")}
    orphan = [c for c in existing if not c.get("graph_id")]
    for c in claims:
        gid = c.get("graph_id")
        if gid:
            by_id[gid] = c
        else:
            orphan.append(c)
    payload = {
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claims": orphan + list(by_id.values()),
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
