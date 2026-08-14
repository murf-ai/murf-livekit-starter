import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  eslint: {
    // These warnings come from upstream LiveKit/AI UI components, not our code.
    ignoreDuringBuilds: true,
  },
  turbopack: {
    root: path.resolve(__dirname, '..'),
  },
  async rewrites() {
    const metrics = process.env.METRICS_ORIGIN ?? 'http://127.0.0.1:8082';
    return [
      { source: '/dashboard', destination: `${metrics}/dashboard` },
      { source: '/api/metrics', destination: `${metrics}/api/metrics` },
      { source: '/api/calls/clear', destination: `${metrics}/api/calls/clear` },
      { source: '/api/calls', destination: `${metrics}/api/calls` },
      { source: '/api/escalations', destination: `${metrics}/api/escalations` },
      { source: '/api/security', destination: `${metrics}/api/security` },
      { source: '/api/threats', destination: `${metrics}/api/threats` },
      { source: '/api/threats/ban', destination: `${metrics}/api/threats/ban` },
      { source: '/api/manager/requests', destination: `${metrics}/api/manager/requests` },
      { source: '/api/manager/approve', destination: `${metrics}/api/manager/approve` },
      { source: '/api/manager/reject', destination: `${metrics}/api/manager/reject` },
    ];
  },
};

export default nextConfig;
