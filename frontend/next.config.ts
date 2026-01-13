import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // CRITICAL for Docker
};

export default nextConfig;