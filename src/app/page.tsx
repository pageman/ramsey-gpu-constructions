import { Dashboard } from "@/components/dashboard";
import type { Catalog } from "@/lib/types";
import catalogJson from "@/data/catalog.json";

export default function Home() {
  return <Dashboard catalog={catalogJson as Catalog} />;
}
