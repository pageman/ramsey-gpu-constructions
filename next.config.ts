import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  // Dev server binds to 0.0.0.0; browsers hit 127.0.0.1. Without this,
  // Next 16 403s /_next chunk requests and client JS never loads.
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
