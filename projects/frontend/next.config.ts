/** @type {import('next').NextConfig} */
// Backend origin the Next server proxies to. Defaults to the local dev backend;
// in containers set BACKEND_ORIGIN=http://backend:8000 (read at server startup).
const backend = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig = {
  // Emit a self-contained server bundle for a lean production image.
  output: "standalone",
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
        destination: `${backend}/health`,
      },
      {
        source: "/ready",
        destination: `${backend}/ready`,
      },
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
