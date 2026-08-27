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

type Pt = { k: number; n: number };

function log10(n: number) {
  return Math.log(Math.max(n, 1.0001)) / Math.log(10);
}

export function GrowthChart({ catalog }: { catalog: Catalog }) {
  const ks = Array.from({ length: 13 }, (_, i) => i + 3);
  const byType = new Map<string, Pt[]>();
  for (const g of catalog.graphs) {
    if (!g.is_k_free) continue;
    const list = byType.get(g.construction_type) ?? [];
    list.push({ k: g.k_target, n: g.N });
    byType.set(g.construction_type, list);
  }

  const series: { key: string; label: string; color: string; dash?: string; pts: Pt[] }[] =
    [
      {
        key: "erdos",
        label: "Erdős probabilistic",
        color: "#3b6dc2",
        pts:
          catalog.reference_curves
            .find((c) => c.name.startsWith("Erdős"))
            ?.points.map((p) => ({ k: p.k, n: p.N })) ?? [],
      },
      {
        key: "fw",
        label: "Frankl–Wilson explicit",
        color: "#3b8a6a",
        pts:
          catalog.reference_curves
            .find((c) => c.name.startsWith("Frankl"))
            ?.points.map((p) => ({ k: p.k, n: p.N })) ?? [],
      },
      {
        key: "target",
        label: "C = 1.01 (stated goal)",
        color: "#e8e0d4",
        dash: "4 4",
        pts:
          catalog.reference_curves
            .find((c) => c.name.startsWith("Target"))
            ?.points.map((p) => ({ k: p.k, n: p.N })) ?? [],
      },
    ];

  for (const [type, pts] of byType) {
    const best = new Map<number, number>();
    for (const p of pts) {
      best.set(p.k, Math.max(best.get(p.k) ?? 0, p.n));
    }
    series.push({
      key: type,
      label: FAMILY_LABEL[type] ?? type,
      color: FAMILY_COLOR[type] ?? "#888",
      pts: [...best.entries()]
        .map(([k, n]) => ({ k, n }))
        .sort((a, b) => a.k - b.k),
    });
  }

  const allN = series.flatMap((s) => s.pts.map((p) => p.n)).filter((n) => n > 0);
  const yMin = Math.min(...allN.map(log10), 0);
  const yMax = Math.max(...allN.map(log10), 1);
  const kMin = 3;
  const kMax = 15;
  const W = 840;
  const H = 420;
  const L = 52;
  const R = 16;
  const T = 18;
  const B = 88;
  const iw = W - L - R;
  const ih = H - T - B;
  const xOf = (k: number) => L + ((k - kMin) / (kMax - kMin)) * iw;
  const yOf = (n: number) => T + ((yMax - log10(n)) / (yMax - yMin || 1)) * ih;

  const yTicks = [1, 10, 100, 1000, 10000].filter(
    (n) => log10(n) >= yMin - 0.05 && log10(n) <= yMax + 0.05
  );

  return (
    <div className="w-full overflow-x-auto rounded-md bg-[#0c0b0a]">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full min-h-[280px]"
        role="img"
        aria-label="Log-scale growth trajectories of Ramsey constructions"
      >
        <rect width={W} height={H} fill="#0c0b0a" />
        {yTicks.map((n) => (
          <g key={n}>
            <line
              x1={L}
              x2={W - R}
              y1={yOf(n)}
              y2={yOf(n)}
              stroke="rgba(232,224,212,0.12)"
              strokeDasharray="3 3"
            />
            <text
              x={L - 8}
              y={yOf(n) + 4}
              textAnchor="end"
              fill="#b7ae9f"
              fontSize="11"
              fontFamily="ui-monospace, monospace"
            >
              {n}
            </text>
          </g>
        ))}
        {ks.map((k) => (
          <text
            key={k}
            x={xOf(k)}
            y={H - B + 18}
            textAnchor="middle"
            fill="#b7ae9f"
            fontSize="11"
            fontFamily="ui-monospace, monospace"
          >
            {k}
          </text>
        ))}
        <text
          x={(L + W - R) / 2}
          y={H - B + 36}
          textAnchor="middle"
          fill="#b7ae9f"
          fontSize="11"
        >
          k  (claim R(k,k) &gt; N)
        </text>
        <text
          x={16}
          y={T + ih / 2}
          fill="#b7ae9f"
          fontSize="11"
          transform={`rotate(-90 16 ${T + ih / 2})`}
          textAnchor="middle"
        >
          N (log scale)
        </text>
        {series.map((s) => {
          if (s.pts.length === 0) return null;
          const d = s.pts
            .map((p, i) => `${i === 0 ? "M" : "L"} ${xOf(p.k).toFixed(1)} ${yOf(p.n).toFixed(1)}`)
            .join(" ");
          return (
            <g key={s.key}>
              <path
                d={d}
                fill="none"
                stroke={s.color}
                strokeWidth={s.key === "paley_prime" || s.key === "erdos" ? 2.2 : 1.6}
                strokeDasharray={s.dash}
              />
              {s.pts.map((p) => (
                <circle
                  key={`${s.key}-${p.k}-${p.n}`}
                  cx={xOf(p.k)}
                  cy={yOf(p.n)}
                  r={s.dash ? 0 : 2.4}
                  fill={s.color}
                />
              ))}
            </g>
          );
        })}
        {series.map((s, i) => {
          const col = i % 4;
          const row = Math.floor(i / 4);
          const x = L + col * 200;
          const y = H - 42 + row * 16;
          return (
            <g key={`leg-${s.key}`}>
              <line
                x1={x}
                x2={x + 18}
                y1={y}
                y2={y}
                stroke={s.color}
                strokeWidth={2}
                strokeDasharray={s.dash}
              />
              <text
                x={x + 24}
                y={y + 4}
                fill="#b7ae9f"
                fontSize="10"
                fontFamily="ui-monospace, monospace"
              >
                {s.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
