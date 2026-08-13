import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  eslint: {
    // These warnings come from upstream LiveKit/AI UI components, not our code.
    ignoreDuringBuilds: true,
  },
  experimental: {
    turbopack: {
      root: path.resolve(__dirname, '..'),
    },
  },
  async rewrites() {
    const metrics = process.env.METRICS_ORIGIN ?? 'http://127.0.0.1:8082';
    return [
      { source: '/dashboard', destination: `${metrics}/dashboard` },
      { source: '/api/metrics', destination: `${metrics}/api/metrics` },
      { source: '/api/calls/clear', destination: `${metrics}/api/calls/clear` },
      { source: '/api/calls', destination: `${metrics}/api/calls` },
      { source: '/api/escalations', destination: `${metrics}/api/escalations` },
    ];
  },
};

export default nextConfig;
