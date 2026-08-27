"use client";

import { useMemo, useState } from "react";
import { Gpu, MinusCircle, PlusCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { GrowthChart } from "@/components/growth-chart";
import { Heatmap } from "@/components/heatmap";
import type { Catalog } from "@/lib/types";

function fmt(x: number | null | undefined, digits = 3) {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return x.toFixed(digits);
}

export function Dashboard({ catalog }: { catalog: Catalog }) {
  const missed = catalog.gap.filter((g) => g.run001 === "not_done");
  const implemented = missed.filter((g) => g.implemented_here !== false);
  const stillOpen = missed.filter((g) => g.implemented_here === false);
  const types = useMemo(
    () =>
      Array.from(new Set(catalog.graphs.map((g) => g.construction_type))).sort(),
    [catalog.graphs]
  );
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const shown = catalog.graphs.filter(
    (g) => typeFilter === "all" || g.construction_type === typeFilter
  );
  const bestMissed = catalog.best_by_type
    .filter((b) => b.run001 === "not_done")
    .sort((a, b) => b.n_1_over_k - a.n_1_over_k);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 py-8 sm:px-6 sm:py-12">
      <header className="flex flex-col gap-5 border-b border-[var(--line)] pb-8">
        <p className="font-mono text-xs tracking-[0.22em] text-[var(--gold)] uppercase">
          RamseyConstructor-GNN · Run001 gap analysis
        </p>
        <h1 className="max-w-4xl font-serif text-3xl leading-tight text-[var(--cream)] sm:text-5xl">
          GPU constructions Run001 never ran
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-[var(--muted)] sm:text-lg">
          The previous session built Paley primes, Frankl–Wilson hybrids, NLFSR
          sketches, and a Random Forest on CPU features. It did{" "}
          <strong className="font-medium text-[var(--cream)]">not</strong>{" "}
          fire the GPU kernels that turn finite-field arithmetic, XOR tables,
          and GEMMs into infinite parametric families. Those kernels are listed
          below, and {catalog.n_graphs} explicit graphs from them are certified
          on this machine ({catalog.device}).
        </p>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="GPU families skipped" value={String(missed.length)} />
          <Stat label="Built in this run" value={String(implemented.length)} />
          <Stat label="Explicit graphs" value={String(catalog.n_graphs)} />
          <Stat
            label="Still GPU-only (search/SDP)"
            value={String(stillOpen.length)}
          />
        </dl>
      </header>

      <section className="flex flex-col gap-4">
        <h2 className="font-serif text-2xl text-[var(--cream)]">
          The constructions
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-[var(--muted)]">
          Every row is a deterministic polynomial-time family (adjacency is a
          closed-form tensor). Probabilistic Erdős graphs are a comparison
          curve, not a construction. The exponential target was{" "}
          <span className="font-mono text-[var(--cream)]">N ≥ C^k</span> with{" "}
          <span className="font-mono text-[var(--cream)]">C ≥ 1.01</span> —
          Paley-type families remain ~k², which is why they look strong at
          small k and stall on a log-N plot.
        </p>
        <div className="grid gap-3">
          {missed.map((g) => (
            <article
              key={g.id}
              className="grid gap-3 rounded-lg border border-[var(--line)] bg-[var(--card)] p-4 sm:grid-cols-[minmax(0,1.1fr)_minmax(0,1.4fr)] sm:gap-6"
            >
              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-medium text-[var(--cream)]">{g.name}</h3>
                  <Badge
                    variant="outline"
                    className="border-[var(--red)]/40 text-[var(--red)]"
                  >
                    not in Run001
                  </Badge>
                  <Badge
                    variant="outline"
                    className="border-[var(--gold)]/40 text-[var(--gold)]"
                  >
                    <Gpu className="size-3" />
                    GPU
                  </Badge>
                  {g.implemented_here === false ? (
                    <Badge variant="secondary">not executed here</Badge>
                  ) : (
                    <Badge variant="secondary">built here</Badge>
                  )}
                </div>
                <p className="font-mono text-[11px] text-[var(--gold)]">
                  {g.kernel}
                </p>
                <p className="text-xs text-[var(--muted)]">{g.family}</p>
              </div>
              <div className="flex flex-col gap-2 text-sm leading-relaxed text-[var(--muted)]">
                <p>
                  <span className="text-[var(--cream)]">Why GPU. </span>
                  {g.why_gpu}
                </p>
                <p>
                  <span className="text-[var(--cream)]">Why it was skipped. </span>
                  {g.why_skipped_or_done}
                </p>
                <p>
                  <span className="text-[var(--cream)]">Growth. </span>
                  {g.growth}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="font-serif text-2xl text-[var(--cream)]">
          What Run001 did instead
        </h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {catalog.run001_done.map((item) => (
            <li
              key={item}
              className="flex gap-2 rounded-md border border-[var(--line)] px-3 py-2 text-sm text-[var(--muted)]"
            >
              <MinusCircle className="mt-0.5 size-4 shrink-0 text-[var(--gold)]/70" />
              {item}
            </li>
          ))}
        </ul>
      </section>

      <Tabs defaultValue="growth" className="gap-4">
        <TabsList variant="line" className="flex h-auto flex-wrap justify-start gap-1 bg-transparent p-0">
          <TabsTrigger value="growth">Growth</TabsTrigger>
          <TabsTrigger value="heatmaps">Adjacency</TabsTrigger>
          <TabsTrigger value="graphs">Graphs</TabsTrigger>
          <TabsTrigger value="oeis">OEIS A000791</TabsTrigger>
        </TabsList>

        <TabsContent value="growth" className="flex flex-col gap-4">
          <Card className="border-[var(--line)] bg-[var(--card)]">
            <CardHeader>
              <CardTitle className="font-serif text-[var(--cream)]">
                Log-scale growth trajectories
              </CardTitle>
              <CardDescription>
                Discovered GPU families versus the probabilistic Erdős bound
                (blue), Frankl–Wilson (green), and the C=1.01 exponential
                target (dashed). Paley remains the strongest small-k explicit
                seed; none of these algebraic families reach exponential C≥1.01
                — that gap is the point of Erdős 78.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GrowthChart catalog={catalog} />
            </CardContent>
          </Card>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {bestMissed.map((b) => (
              <Card
                key={b.graph_id}
                className="border-[var(--line)] bg-[var(--card)]"
              >
                <CardHeader className="pb-2">
                  <CardTitle className="font-mono text-sm text-[var(--cream)]">
                    {b.graph_id}
                  </CardTitle>
                  <CardDescription className="font-mono text-[11px]">
                    {b.gpu_kernel}
                  </CardDescription>
                </CardHeader>
                <CardContent className="font-mono text-sm text-[var(--muted)]">
                  N={b.N} · certified k&gt;{b.k_target} · N^{"{1/k}"}=
                  {fmt(b.n_1_over_k, 4)}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="heatmaps">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(catalog.heatmaps).map(([id, matrix]) => (
              <Heatmap key={id} id={id} matrix={matrix} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="graphs" className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setTypeFilter("all")}
              className={chip(typeFilter === "all")}
            >
              all ({catalog.graphs.length})
            </button>
            {types.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTypeFilter(t)}
                className={chip(typeFilter === t)}
              >
                {t} ({catalog.graphs.filter((g) => g.construction_type === t).length})
              </button>
            ))}
          </div>
          <div className="overflow-x-auto rounded-lg border border-[var(--line)]">
            <Table>
              <TableHeader>
                <TableRow className="border-[var(--line)] hover:bg-transparent">
                  <TableHead>graph</TableHead>
                  <TableHead>N</TableHead>
                  <TableHead>k&gt;</TableHead>
                  <TableHead>N^{"{1/k}"}</TableHead>
                  <TableHead>ω / α</TableHead>
                  <TableHead>Run001</TableHead>
                  <TableHead>kernel</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shown.map((g) => (
                  <TableRow
                    key={g.graph_id}
                    className="border-[var(--line)] hover:bg-white/3"
                  >
                    <TableCell className="font-mono text-[11px] text-[var(--cream)]">
                      {g.graph_id}
                    </TableCell>
                    <TableCell className="font-mono">{g.N}</TableCell>
                    <TableCell className="font-mono">{g.k_target}</TableCell>
                    <TableCell className="font-mono">
                      {fmt(g.n_1_over_k, 4)}
                    </TableCell>
                    <TableCell className="font-mono text-[11px]">
                      {g.exact
                        ? `${g.omega_exact}/${g.alpha_exact}`
                        : `≤${g.omega_upper}/≤${g.alpha_upper}`}
                    </TableCell>
                    <TableCell>
                      {g.run001 === "done" ? (
                        <span className="text-[var(--gold)]">done</span>
                      ) : (
                        <span className="text-[var(--red)]">missed</span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[220px] truncate font-mono text-[10px] text-[var(--muted)]">
                      {g.gpu_kernel}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        <TabsContent value="oeis">
          <Card className="border-[var(--line)] bg-[var(--card)]">
            <CardHeader>
              <CardTitle className="font-serif text-[var(--cream)]">
                Diagonal Ramsey numbers · OEIS A000791
              </CardTitle>
              <CardDescription>
                A construction on N vertices with ω,α &lt; k proves R(k,k) &gt;
                N. Known exact values stop at k=4. Paley(17) is the unique
                (4,4)-free graph on 17 vertices, matching R(4,4)=18.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-[var(--line)]">
                    <TableHead>k</TableHead>
                    <TableHead>R(k,k)</TableHead>
                    <TableHead>status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {catalog.oeis_a000791.map((r) => (
                    <TableRow key={r.k} className="border-[var(--line)]">
                      <TableCell className="font-mono">{r.k}</TableCell>
                      <TableCell className="font-mono">
                        {r.R ?? `${r.R_lower}–${r.R_upper}`}
                      </TableCell>
                      <TableCell className="text-[var(--muted)]">
                        {r.status}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <section className="flex flex-col gap-3 border-t border-[var(--line)] pt-8">
        <h2 className="font-serif text-2xl text-[var(--cream)]">
          Honest bound on C
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-[var(--muted)]">
          Fitting log N against certified k on this catalogue does{" "}
          <strong className="font-medium text-[var(--cream)]">not</strong>{" "}
          produce C ≥ 1.01 as an infinite-family exponential. Spectral upper
          bounds on ω inflate k for large N, which shrinks{" "}
          <span className="font-mono">N^{"{1/k}"}</span> toward 1.
          Exact certificates (Paley 5, 13, 17; Nagy t=6,7; polarity PG(2,3))
          sit in the Paley polynomial regime. The GPU work Run001 skipped is
          real and useful for search and certification. It does not, by itself,
          resolve Erdős&apos;s constructive exponential-Ramsey problem.
        </p>
        <p className="flex items-start gap-2 text-sm text-[var(--muted)]">
          <PlusCircle className="mt-0.5 size-4 shrink-0 text-[var(--gold)]" />
          Re-run the kernels with{" "}
          <code className="mx-1 font-mono text-[var(--cream)]">
            python3 engine/run.py
          </code>
          . On a CUDA box the same code path uses GPU GEMM and{" "}
          <code className="mx-1 font-mono text-[var(--cream)]">
            torch.linalg.eigvalsh
          </code>
          .
        </p>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--line)] bg-[var(--card)] px-3 py-3">
      <dt className="text-[11px] tracking-wide text-[var(--muted)] uppercase">
        {label}
      </dt>
      <dd className="font-serif text-2xl text-[var(--cream)]">{value}</dd>
    </div>
  );
}

function chip(active: boolean) {
  return [
    "rounded-full border px-3 py-1 font-mono text-[11px] transition-colors",
    active
      ? "border-[var(--gold)] bg-[var(--gold)]/15 text-[var(--cream)]"
      : "border-[var(--line)] text-[var(--muted)] hover:border-[var(--gold)]/50",
  ].join(" ");
}
