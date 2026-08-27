export type GapEntry = {
  id: string;
  name: string;
  run001: "done" | "not_done";
  gpu: boolean;
  kernel: string;
  why_gpu: string;
  why_skipped_or_done: string;
  family: string;
  growth: string;
  implemented_here?: boolean;
};

export type GraphRow = {
  graph_id: string;
  construction_type: string;
  N: number;
  k_target: number;
  provenance_seed: number;
  degree_mean: number;
  degree_std: number;
  omega_exact: number | null;
  alpha_exact: number | null;
  omega_lower: number;
  omega_upper: number;
  alpha_lower: number;
  alpha_upper: number;
  theta_approx: number;
  spectral_gap: number;
  is_k_free: boolean;
  triangles: number;
  n_1_over_k: number;
  exact: boolean;
  gpu_kernel: string;
  run001: string;
  field: string;
  device: string;
};

export type Catalog = {
  device: string;
  n_graphs: number;
  generated_at: string;
  run001_done: string[];
  gap: GapEntry[];
  graphs: GraphRow[];
  best_by_type: {
    construction_type: string;
    graph_id: string;
    N: number;
    k_target: number;
    n_1_over_k: number;
    run001: string;
    gpu_kernel: string;
  }[];
  fits: {
    C: number | null;
    slope: number | null;
    points: number;
    construction: string | null;
    mean_n_1_over_k?: number;
  }[];
  oeis_a000791: {
    k: number;
    R?: number;
    R_lower?: number;
    R_upper?: number;
    status: string;
    oeis: string;
  }[];
  reference_curves: { name: string; points: { k: number; N: number }[] }[];
  heatmaps: Record<string, number[][]>;
  jobs?: Record<
    string,
    {
      n_graphs: number;
      scale: string;
      seconds: number;
      owners?: { cells: string[]; families: string[] };
    }
  >;
  algorithms?: string[];
};
