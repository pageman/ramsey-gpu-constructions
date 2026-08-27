import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  // Dual-stack (::) so both 127.0.0.1 and [::1] work. Chrome's Happy
  // Eyeballs tries IPv6 first; IPv4-only 0.0.0.0 caused ERR_CONNECTION_REFUSED.
  allowedDevOrigins: ["127.0.0.1", "localhost", "[::1]", "::1"],
};

export default nextConfig;
