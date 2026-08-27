"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Catalog } from "@/lib/types";

const FAMILY_COLOR: Record<string, string> = {
  paley_prime: "#c4a35a",
  paley_prime_power: "#e8c872",
  generalized_paley: "#c23b3b",
  cyclotomic_union: "#d46868",
  quadratic_form_f2: "#3b8a6a",
  gold_trace_f2: "#5aa88a",
  polarity_pg2: "#3b6dc2",
  nagy_intersecting: "#8a6bb8",
  tensor_strong_product: "#d4893b",
  singer_difference: "#6b9bd1",
};

const FAMILY_LABEL: Record<string, string> = {
  paley_prime: "Paley primes (Run001)",
  paley_prime_power: "Paley F_p²",
  generalized_paley: "Generalized Paley k>2",
  cyclotomic_union: "Cyclotomic unions",
  quadratic_form_f2: "F₂ quadratic Cayley",
  gold_trace_f2: "Gold trace F₂",
  polarity_pg2: "PG(2,q) polarity",
  nagy_intersecting: "Nagy intersecting",
  tensor_strong_product: "Strong-product lifts",
  singer_difference: "Singer circulants",
};

export function GrowthChart({ catalog }: { catalog: Catalog }) {
  const ks = Array.from({ length: 13 }, (_, i) => i + 3);
  const byType = new Map<string, { k: number; n: number }[]>();
  for (const g of catalog.graphs) {
    if (!g.is_k_free) continue;
    const list = byType.get(g.construction_type) ?? [];
    list.push({ k: g.k_target, n: g.N });
    byType.set(g.construction_type, list);
  }

  const rows = ks.map((k) => {
    const row: Record<string, number | null> = { k };
    const erdos = catalog.reference_curves.find((c) =>
      c.name.startsWith("Erdős")
    );
    const fw = catalog.reference_curves.find((c) =>
      c.name.startsWith("Frankl")
    );
    const target = catalog.reference_curves.find((c) =>
      c.name.startsWith("Target")
    );
    row.erdos = erdos?.points.find((p) => p.k === k)?.N ?? null;
    row.fw = fw?.points.find((p) => p.k === k)?.N ?? null;
    row.target = target?.points.find((p) => p.k === k)?.N ?? null;
    for (const [type, pts] of byType) {
      const at = pts.filter((p) => p.k === k).sort((a, b) => b.n - a.n)[0];
      row[type] = at ? at.n : null;
    }
    return row;
  });

  return (
    <div className="h-[380px] w-full sm:h-[440px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 12, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="rgba(232,224,212,0.08)" strokeDasharray="3 3" />
          <XAxis
            dataKey="k"
            tick={{ fill: "#b7ae9f", fontSize: 11 }}
            label={{
              value: "k  (claim R(k,k) > N)",
              fill: "#b7ae9f",
              fontSize: 11,
              position: "insideBottom",
              offset: -2,
            }}
          />
          <YAxis
            scale="log"
            domain={["auto", "auto"]}
            tick={{ fill: "#b7ae9f", fontSize: 11 }}
            width={52}
            label={{
              value: "N (log)",
              angle: -90,
              fill: "#b7ae9f",
              fontSize: 11,
              position: "insideLeft",
            }}
          />
          <Tooltip
            contentStyle={{
              background: "#161410",
              border: "1px solid #2a2620",
              borderRadius: 8,
              fontSize: 12,
              color: "#e8e0d4",
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#b7ae9f" }}
            iconType="plainline"
          />
          <Line
            type="monotone"
            dataKey="erdos"
            name="Erdős probabilistic"
            stroke="#3b6dc2"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="fw"
            name="Frankl–Wilson explicit"
            stroke="#3b8a6a"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="target"
            name="C = 1.01 (the stated goal)"
            stroke="#e8e0d4"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            dot={false}
            connectNulls
          />
          {[...byType.keys()].map((type) => (
            <Line
              key={type}
              type="monotone"
              dataKey={type}
              name={FAMILY_LABEL[type] ?? type}
              stroke={FAMILY_COLOR[type] ?? "#888"}
              strokeWidth={type === "paley_prime" ? 2 : 1.75}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
