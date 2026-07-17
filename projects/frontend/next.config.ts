/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    reactCompiler: {
      target: "18",
    },
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
