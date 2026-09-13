# Job 4a — Void Audit (Yu Pool Hunt, p ∈ [200,400])

Campaign: A40 `armed_yellow_buzzard`, 29–30 Aug 2026.

**Status: Incomplete (audit + do-not-cite).** Job 4a finished with 6 emits
across 3 graph_ids. Yu p=251 kept as literature witness. Two p=337,353 hits
were **void** (residual n>256, silent C MIS false-accept). Do not cite
R(4,20)≥354.

---

## What 4a Did

Hunt Yu-style 2-class pools at primes p ∈ [200,400], exponents e ∈ {4,5,8,10},
with:

- 64 restricted-process walks per (p,e,i,j) pool
- Greedy α < t reject
- Bitset residual MIS on leftover (C `native_mis`, n≤256 contract)
- Multiplier lex-min orbit deduplication

**Wall time:** 1715 s (~29 min). **Device:** A40. **Code:** git `9335659`
through `18d2aeb`.

---

## Results

| p | e | i,j | graph_id | |S| | residual | exact | outcome |
|---|---|---|---|---|---|---|---|
| 251 | 5 | 0,2 | `yu_pool_p251_e5_kindyu_published` | 32 | 186 | lit | **keep** (Yu witness) |
| 337 | 4 | — | `yu_pool_p337_e4` | 37 | 262 | **void** | n>256 → do not cite |
| 353 | 8 | — | `yu_pool_p353_e8` | 44 | 264 | **void** | n>256 → do not cite |

Yu p=251: structural gate passed; α=19 from **literature**, not this kernel
(6a/7a timeout). Residual 186 was the Yu target.

### p=337 residual 262

4a emitted `CELL? R(4,20)≥338` with `exact=True`, `alpha=19`. The residual
(262 vertices) exceeded `MAXN=256`. C MIS returned `found=0` **without**
`timed_out=1` (silent contract violation). Python hardcoded `exact=True` on
emit. **Do not announce.**

### p=353 residual 264

Same failure mode: `CELL? R(4,20)≥354`. Residual 264 > 256. Four registry rows
share the `graph_id` (no i,j,S in id); last upsert wins. **Do not announce.**

---

## Operator Rules

1. **Width gate:** C MIS n≤256 is a hard axiom. Residual n>256 → skip or widen
   the kernel.
2. **Timeout ≠ accept:** `found=0` with `timed_out=0` is NOT a proof when
   n>MAXN.
3. **Emit exact only when certified:** Yu p=251 `exact` is from structural gate,
   **not** from α_certified. 4a's `exact=True` on 337/353 was a code path error
   (fixed after the run).
4. **Do not cite void:** p=337,353 emits are retracted. README banner (git
   `18d2aeb`) says so.

---

## Fix Landed on main (after the run)

```python
# engine/kernels/bitset_mcs.py
if len(residual) > skip_n:
    return dict(
        found=False, timed_out=False, exact=False, backend=...,
        reason=f"residual {len(residual)} > {skip_n} (MAXN={MAXN})"
    )
```

**Regression test:** `test_mis_n_over_256_is_not_a_certificate()`.

---

## Scientific Closeout

- **No published +1.** R(4,20)≥252 (Yu) unchanged.
- Yu p=251 structural: kept as smoke/witness in the catalog.
- p=337,353: retracted as void. Width violation.
- **Do not reopen 4a** on the same seed/parameters without either:
  - Widening MAXN to 320–384, **or**
  - Forcing |S| high enough that residual ≤256 (requires denser S, larger
    greedy α — likely no 20-cell).

Job 4a proved that a blind Yu-pool hunt at primes near p=353 will hit
residual>256 before it mints a cell. The hunt is not complete without a wider
referee or a residual-size gate.

---

## Artifacts

- **Catalog:** `data/a40/catalog-4abc.json` (3 graph_ids, 270 total rows)
- **Registry:** `data/a40/registry.jsonl` (6 emit lines for 4a)
- **Ledger:** `data/a40/bound_ledger.json` (statements; some void)
- **Yu witness:** `data/yu_r4_20.json` (p=251, S of size 32)

Yu p=251 row is kept as literature witness. p=337,353 rows are marked void in
docs; they exist in the catalog for forensic audit, **not** as theorems.

---

## See Also

- `docs/A40-CAMPAIGN.md` — full campaign scoreboard
- `docs/plan-move-a-number.md` — plan v2 rationale
- `docs/SESSION-HANDOFF.md` — methodological arc (§M27a, M33a, M66a–M67a)
- `engine/yu_pool.py` — job 4a implementation
- `engine/kernels/native_mis.c` — n≤256 contract
- `README.md` — retraction banner (git `18d2aeb`)

**Do not cite R(4,20)≥338 or R(4,20)≥354.** Still **252** (Yu).
