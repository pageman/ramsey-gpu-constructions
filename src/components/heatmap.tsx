"use client";

import { cn } from "@/lib/utils";

const LABELS: Record<string, string> = {
  paley_17: "Paley(17) — Run001 did this",
  paley_f9: "Paley(F₉) — prime power, skipped",
  f2_symplectic_16: "F₂⁴ symplectic Cayley — skipped",
  polarity_pg2_3: "PG(2,3) polarity — skipped",
  nagy_6: "Nagy t=6 — skipped",
};

export function Heatmap({
  matrix,
  id,
  className,
}: {
  matrix: number[][];
  id: string;
  className?: string;
}) {
  const n = matrix.length;
  return (
    <figure className={cn("flex flex-col gap-2", className)}>
      <div
        className="grid aspect-square w-full overflow-hidden rounded-md border border-[var(--line)]"
        style={{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }}
        role="img"
        aria-label={LABELS[id] ?? id}
      >
        {matrix.flatMap((row, i) =>
          row.map((bit, j) => (
            <span
              key={`${i}-${j}`}
              className={
                i === j
                  ? "bg-[var(--ink)]"
                  : bit
                    ? "bg-[var(--red)]"
                    : "bg-[var(--blue-dim)]"
              }
            />
          ))
        )}
      </div>
      <figcaption className="font-mono text-[11px] leading-snug text-[var(--muted)]">
        {LABELS[id] ?? id}. Red = edge, blue = non-edge. This is the adjacency
        matrix, not a GNN attention map — Run001 never shipped{" "}
        <code>gnn_model.pt</code>.
      </figcaption>
    </figure>
  );
}
