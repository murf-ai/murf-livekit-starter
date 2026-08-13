'use client';

import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Ban,
  Eye,
  Lock,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Unlock,
} from 'lucide-react';

interface ThreatEvent {
  event_id: string;
  room_id: string;
  timestamp: string;
  threat_score: number;
  threat_level: 'safe' | 'monitor' | 'warn' | 'restrict' | 'ban';
  signals: string[];
  action_taken: string;
  details: Record<string, unknown>;
}

interface ActiveBan {
  fingerprint: string;
  room_id?: string;
  banned_at: string;
  expires_at?: string;
  reason: string;
  total_threat_score: number;
  is_permanent: boolean;
}

interface SecurityStats {
  total_threat_events: number;
  affected_sessions: number;
  avg_threat_score: number;
  max_threat_score: number;
  ban_events: number;
  restrict_events: number;
  warn_events: number;
  monitor_events: number;
  active_bans: number;
  signal_distribution: Record<string, number>;
}

interface SecurityData {
  stats: SecurityStats;
  recent_threats: ThreatEvent[];
  active_bans: ActiveBan[];
}

export function SecurityView() {
  const [data, setData] = useState<SecurityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchSecurityData = async () => {
    try {
      const res = await fetch('/api/security', { cache: 'no-store' });
      if (!res.ok) throw new Error('Security data endpoint unavailable');
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load security metrics';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleUnban = async (fingerprint: string) => {
    setActionLoading(fingerprint);
    try {
      const res = await fetch('/api/threats/ban', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'unban', fingerprint }),
      });
      if (res.ok) {
        await fetchSecurityData();
      }
    } catch (err) {
      console.error('Failed to unban session:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const getLevelBadgeClass = (level: string) => {
    switch (level) {
      case 'ban':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      case 'restrict':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'warn':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';
      case 'monitor':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  const formatSignalName = (signal: string) => {
    return signal.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="min-h-full space-y-8 bg-slate-950 p-6 font-sans text-slate-100 md:p-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-2.5 text-rose-400">
              <ShieldAlert className="size-6 animate-pulse" />
            </div>
            <div>
              <h1 className="flex items-center gap-2 text-2xl font-black tracking-tight text-white">
                Security Command Center
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold tracking-wide text-emerald-400">
                  REAL-TIME ACTIVE
                </span>
              </h1>
              <p className="text-sm font-medium text-slate-400">
                Live threat intelligence, automated ban enforcement, and attack mitigation
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => {
            setLoading(true);
            fetchSecurityData();
          }}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-700"
        >
          <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Feed
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm font-medium text-rose-300">
          <AlertTriangle className="size-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Threat Events</span>
            <Activity className="size-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black text-white">
            {data?.stats?.total_threat_events ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Across {data?.stats?.affected_sessions ?? 0} session(s)
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Active Bans</span>
            <Ban className="size-4 text-rose-400" />
          </div>
          <div className="text-3xl font-black text-rose-400">{data?.stats?.active_bans ?? 0}</div>
          <div className="mt-1 text-xs text-slate-500">Strict rate limit / threat blocks</div>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Avg Threat Score</span>
            <Lock className="size-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-amber-400">
            {data?.stats?.avg_threat_score ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Max score observed: {data?.stats?.max_threat_score ?? 0}
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Restricted Sessions</span>
            <ShieldCheck className="size-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-emerald-400">
            {(data?.stats?.restrict_events ?? 0) + (data?.stats?.ban_events ?? 0)}
          </div>
          <div className="mt-1 text-xs text-slate-500">Automated protection triggered</div>
        </div>
      </div>

      {/* Main Content Grid: Active Bans + Signal Distribution */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Active Bans Section */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Ban className="size-5 text-rose-400" />
              <h2 className="text-lg font-bold text-white">Active Session Bans</h2>
            </div>
            <span className="text-xs font-semibold text-slate-400">
              {data?.active_bans?.length ?? 0} Banned Fingerprint(s)
            </span>
          </div>

          {!data?.active_bans?.length ? (
            <div className="rounded-xl border border-dashed border-slate-800 py-12 text-center text-slate-500">
              <ShieldCheck className="mx-auto mb-2 size-8 text-slate-600" />
              <p className="text-sm font-medium">No active bans in effect</p>
              <p className="mt-0.5 text-xs text-slate-600">
                System monitoring all active incoming calls
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 font-bold tracking-wider text-slate-400 uppercase">
                    <th className="pb-3">Fingerprint</th>
                    <th className="pb-3">Reason</th>
                    <th className="pb-3">Threat Score</th>
                    <th className="pb-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {data.active_bans.map((ban) => (
                    <tr key={ban.fingerprint} className="hover:bg-slate-800/20">
                      <td className="py-3.5 font-mono font-semibold text-slate-300">
                        {ban.fingerprint}
                      </td>
                      <td className="max-w-xs truncate py-3.5 text-slate-400">{ban.reason}</td>
                      <td className="py-3.5 font-bold text-rose-400">
                        {ban.total_threat_score} pts
                      </td>
                      <td className="py-3.5">
                        <button
                          disabled={actionLoading === ban.fingerprint}
                          onClick={() => handleUnban(ban.fingerprint)}
                          className="inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-400 transition hover:bg-emerald-500/20"
                        >
                          <Unlock className="size-3" />
                          Unban
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Signal Distribution */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
          <div className="flex items-center gap-2">
            <Eye className="size-5 text-amber-400" />
            <h2 className="text-lg font-bold text-white">Threat Signals</h2>
          </div>

          {data?.stats?.signal_distribution &&
          Object.keys(data.stats.signal_distribution).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(data.stats.signal_distribution).map(([signal, count]) => (
                <div key={signal} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-300">{formatSignalName(signal)}</span>
                    <span className="font-bold text-amber-400">{count}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-1.5 rounded-full bg-amber-400"
                      style={{
                        width: `${Math.min(100, (count / (data?.stats?.total_threat_events || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 py-12 text-center text-slate-500">
              <p className="text-sm font-medium">No signals recorded yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Threat Feed */}
      <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="size-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white">Recent Security Intercept Feed</h2>
          </div>
          <span className="text-xs text-slate-500">Auto-refreshing every 3s</span>
        </div>

        {!data?.recent_threats?.length ? (
          <div className="rounded-xl border border-dashed border-slate-800 py-12 text-center text-slate-500">
            <ShieldCheck className="mx-auto mb-2 size-8 text-emerald-500/40" />
            <p className="text-sm font-medium">Clean audit log — no security threats detected</p>
          </div>
        ) : (
          <div className="space-y-3">
            {data.recent_threats.map((event) => (
              <div
                key={event.event_id}
                className="flex flex-col justify-between gap-4 rounded-xl border border-slate-800/80 bg-slate-950 p-4 transition hover:border-slate-700 md:flex-row md:items-center"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-slate-300">
                      {event.event_id}
                    </span>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-extrabold uppercase ${getLevelBadgeClass(
                        event.threat_level
                      )}`}
                    >
                      {event.threat_level}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {event.signals.map((sig) => (
                      <span
                        key={sig}
                        className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-semibold text-slate-300"
                      >
                        {formatSignalName(sig)}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm font-black text-rose-400">
                      +{event.threat_score} pts
                    </div>
                    <div className="text-[11px] font-semibold text-slate-500 uppercase">
                      Action: {event.action_taken}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
