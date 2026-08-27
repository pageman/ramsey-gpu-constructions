import { Dashboard } from "@/components/dashboard";
import type { Catalog } from "@/lib/types";
import catalogJson from "@/data/catalog.json";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ type?: string }>;
}) {
  const params = await searchParams;
  return (
    <Dashboard
      catalog={catalogJson as Catalog}
      typeFilter={params.type ?? "all"}
    />
  );
}
