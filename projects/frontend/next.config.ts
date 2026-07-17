/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    reactCompiler: {
      target: "18",
    },
    // /api/compare holds the connection for one local-LLM generation
    // (~20s, ~40s on fabrication retry); default 30s proxy timeout resets it.
    proxyTimeout: 120_000,
  },
  async rewrites() {
    return [
      {
        source: "/health",
        destination: "http://localhost:8000/health",
      },
      {
        source: "/ready",
        destination: "http://localhost:8000/ready",
      },
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
