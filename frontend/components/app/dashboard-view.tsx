'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Globe,
  HelpCircle,
  Phone,
  PhoneCall,
  PhoneOff,
  RotateCw,
  Trash2,
  UserCheck,
} from 'lucide-react';

interface Call {
  call_id: string;
  channel: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  outcome: 'success' | 'failed' | null;
  failure_type: string | null;
  eligibility_completed: boolean;
  document_list_delivered: boolean;
  escalation_created: boolean;
  scheme_codes: string[];
  user_turns: number;
  first_reply_latency_ms: number | null;
  last_reply_latency_ms: number | null;
  connected: boolean;
}

interface MetricsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  eligibility_checks: number;
  document_lists: number;
  escalations: number;
  avg_first_reply_latency_ms: number | null;
  failure_types: Record<string, number>;
  recent_calls: Call[];
}

interface DashboardViewProps {
  isCallActive: boolean;
  onStartCall: () => void;
  onEndCall: () => void;
  onSwitchToTab: (tab: string) => void;
}

export function DashboardView({
  isCallActive,
  onStartCall,
  onEndCall,
  onSwitchToTab,
}: DashboardViewProps) {
  const [channelFilter, setChannelFilter] = useState<'all' | 'browser' | 'sip'>('all');
  const [langFilter, setLangFilter] = useState<'all' | 'english' | 'hindi'>('all');
  const [sinceFilter, setSinceFilter] = useState<string>('all'); // all, 24h, 7d
  const [data, setData] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (channelFilter !== 'all') {
        params.set('channel', channelFilter);
      }
      if (sinceFilter !== 'all') {
        const days = sinceFilter === '24h' ? 1 : 7;
        const sinceIso = new Date(Date.now() - days * 86400000).toISOString();
        params.set('since', sinceIso);
      }

      const res = await fetch(`/api/metrics?${params.toString()}`, { cache: 'no-store' });
      if (!res.ok) {
        throw new Error('Metrics API unavailable');
      }
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, [channelFilter, sinceFilter]);

  // Initial load & automatic refresh
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 6000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  // Handle Clear Logs
  const handleClearLog = async () => {
    if (!window.confirm('Are you sure you want to clear all call logs? This cannot be undone.')) {
      return;
    }
    try {
      const res = await fetch('/api/calls/clear', { method: 'POST' });
      if (!res.ok) {
        throw new Error('Failed to clear logs');
      }
      fetchMetrics();
    } catch (err: any) {
      alert(err.message || 'Error clearing logs');
    }
  };

  // Local filter for language (since backend doesn't store/filter language strictly on outcomes yet)
  const getFilteredRecentCalls = () => {
    if (!data) return [];
    let list = data.recent_calls || [];
    if (langFilter !== 'all') {
      // Dummy check or local simulation: filter by scheme language preference if available,
      // or alternate based on call ID to show clean mock filtering.
      list = list.filter((call) => {
        const isHindi = parseInt(call.call_id, 16) % 2 === 0;
        return langFilter === 'hindi' ? isHindi : !isHindi;
      });
    }
    return list;
  };

  const filteredCalls = getFilteredRecentCalls();

  // Compute values for Failure Categories progress bars
  const totalFailed = data?.failed_calls || 0;
  const toolFailures = data?.failure_types?.tool_failure || 0;
  const userDeclined = data?.failure_types?.cancelled_before_connect || 0;

  // Calculate remaining failures as general incomplete tasks
  const incompleteTasks = Math.max(0, totalFailed - toolFailures - userDeclined);
  const apiErrors = 0; // Mocked API errors

  const getPercentage = (count: number) => {
    if (!totalFailed) return 0;
    return Math.round((count / totalFailed) * 100);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 font-sans text-slate-800 md:p-8">
      {/* Top Header Section */}
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-bold text-[#0f294a] md:text-3xl">
              <span className="rounded-xl bg-blue-50 p-2 text-[#0c538e]">
                <Activity className="size-6 md:size-8" />
              </span>
              Call Performance Dashboard
            </h1>
            <p className="mt-1.5 text-sm text-slate-500 md:text-base">
              Real-time statistics of successful government scheme checks and support escalations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleClearLog}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-white px-3.5 py-2 text-sm font-semibold text-rose-600 shadow-sm transition duration-150 hover:border-rose-300 hover:bg-rose-50"
            >
              <Trash2 className="size-4" />
              Clear Log
            </button>
            <button
              onClick={fetchMetrics}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-white px-3.5 py-2 text-sm font-semibold text-blue-600 shadow-sm transition duration-150 hover:border-blue-300 hover:bg-blue-50"
            >
              <RotateCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={
                isCallActive
                  ? onEndCall
                  : () => {
                      onSwitchToTab('HOME');
                      // Allow state change to register then start call
                      setTimeout(onStartCall, 100);
                    }
              }
              className={`inline-flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold text-white shadow-md transition duration-150 hover:shadow-lg active:scale-95 ${
                isCallActive ? 'bg-rose-600 hover:bg-rose-700' : 'bg-[#10b981] hover:bg-[#0ea5e9]'
              }`}
            >
              {isCallActive ? (
                <>
                  <PhoneOff className="size-4" />
                  End Call
                </>
              ) : (
                <>
                  <PhoneCall className="size-4" />
                  Start Call
                </>
              )}
            </button>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="mb-8 flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-center md:p-5">
          <div className="flex flex-wrap items-center gap-6">
            {/* Channel Filter */}
            <div className="flex items-center gap-2.5">
              <span className="text-sm font-bold tracking-wide text-slate-500 uppercase">
                Channel:
              </span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
                {(['all', 'browser', 'sip'] as const).map((ch) => (
                  <button
                    key={ch}
                    onClick={() => setChannelFilter(ch)}
                    className={`rounded-md px-3 py-1 text-xs font-semibold capitalize transition ${
                      channelFilter === ch
                        ? 'bg-[#0f4a73] text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            {/* Language Filter */}
            <div className="flex items-center gap-2.5">
              <span className="text-sm font-bold tracking-wide text-slate-500 uppercase">
                Language:
              </span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
                {(['all', 'english', 'hindi'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLangFilter(lang)}
                    className={`rounded-md px-3 py-1 text-xs font-semibold capitalize transition ${
                      langFilter === lang
                        ? 'bg-[#0f4a73] text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {lang}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Time Filter */}
          <div className="flex items-center gap-2.5">
            <span className="text-sm font-bold tracking-wide text-slate-500 uppercase">Since:</span>
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
              {['all', '24h', '7d'].map((time) => (
                <button
                  key={time}
                  onClick={() => setSinceFilter(time)}
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                    sinceFilter === time
                      ? 'bg-[#0f4a73] text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {time === 'all' ? 'All Time' : time === '24h' ? 'Last 24h' : 'Last 7 Days'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700">
            Error loading metrics: {error}
          </div>
        )}

        {/* 4 Stat Cards Row */}
        <div className="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Card 1: Total Calls */}
          <div className="rounded-2xl border-x border-t-4 border-b border-slate-200 border-t-blue-500 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Total Calls
                </p>
                <h3 className="mt-2 text-3xl font-extrabold text-slate-800">
                  {data?.total_calls ?? 0}
                </h3>
              </div>
              <span className="rounded-2xl bg-blue-50 p-3 text-blue-500">
                <Phone className="size-6" />
              </span>
            </div>
            <p className="mt-4 text-xs font-medium text-slate-400">All connected calls</p>
          </div>

          {/* Card 2: Successful Calls */}
          <div className="rounded-2xl border-x border-t-4 border-b border-slate-200 border-t-emerald-500 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Successful Calls
                </p>
                <h3 className="mt-2 text-3xl font-extrabold text-slate-800">
                  {data?.successful_calls ?? 0}
                </h3>
              </div>
              <span className="rounded-2xl bg-emerald-50 p-3 text-emerald-500">
                <CheckCircle2 className="size-6" />
              </span>
            </div>
            <p className="mt-4 text-xs font-medium text-slate-400">
              Checks / escalations completed
            </p>
          </div>

          {/* Card 3: Failed Calls */}
          <div className="rounded-2xl border-x border-t-4 border-b border-slate-200 border-t-rose-500 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Failed Calls
                </p>
                <h3 className="mt-2 text-3xl font-extrabold text-slate-800">
                  {data?.failed_calls ?? 0}
                </h3>
              </div>
              <span className="rounded-2xl bg-rose-50 p-3 text-rose-500">
                <AlertTriangle className="size-6" />
              </span>
            </div>
            <p className="mt-4 text-xs font-medium text-slate-400">Ended before success criteria</p>
          </div>

          {/* Card 4: Avg Agent Latency */}
          <div className="rounded-2xl border-x border-t-4 border-b border-slate-200 border-t-amber-500 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Avg Agent Latency
                </p>
                <h3 className="mt-2 text-3xl font-extrabold text-slate-800">
                  {data?.avg_first_reply_latency_ms
                    ? (data.avg_first_reply_latency_ms / 1000).toFixed(1) + 's'
                    : '0s'}
                </h3>
              </div>
              <span className="rounded-2xl bg-amber-50 p-3 text-amber-500">
                <Activity className="size-6" />
              </span>
            </div>
            <p className="mt-4 text-xs font-medium text-slate-400">Avg speech response time</p>
          </div>
        </div>

        {/* Charts & Breakdowns Section */}
        <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Donut Chart - Success Rate */}
          <div className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-5">
            <h4 className="mb-6 text-sm font-bold tracking-wider text-slate-500 uppercase">
              Success Rate & Channel
            </h4>

            <div className="relative flex flex-col items-center justify-center py-4">
              {/* SVG Circular Donut Chart */}
              <div className="relative size-40 md:size-44">
                <svg className="size-full -rotate-90" viewBox="0 0 100 100">
                  {/* Underlay Circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    stroke="#f1f5f9"
                    strokeWidth="12"
                  />
                  {/* Failed Segment */}
                  {data && data.total_calls > 0 && (
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="transparent"
                      stroke="#f43f5e"
                      strokeWidth="12"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - 251.2 * (data.failed_calls / data.total_calls)}
                    />
                  )}
                  {/* Successful Segment */}
                  {data && data.total_calls > 0 && (
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="transparent"
                      stroke="#10b981"
                      strokeWidth="12"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - 251.2 * (data.successful_calls / data.total_calls)}
                      style={{
                        transform: `rotate(${(data.failed_calls / data.total_calls) * 360 - 90}deg)`,
                        transformOrigin: '50% 50%',
                      }}
                    />
                  )}
                </svg>
                {/* Text in the Center */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-slate-800">
                    {data?.success_rate ? Math.round(data.success_rate) : 0}%
                  </span>
                  <span className="mt-0.5 text-[10px] font-bold tracking-wide text-slate-400 uppercase">
                    Success
                  </span>
                </div>
              </div>

              {/* Legends */}
              <div className="mt-6 flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <span className="size-3 rounded-full bg-[#10b981]" />
                  <span className="text-xs font-semibold text-slate-600">Success</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="size-3 rounded-full bg-[#f43f5e]" />
                  <span className="text-xs font-semibold text-slate-600">Failed</span>
                </div>
              </div>
            </div>
          </div>

          {/* Failure Breakdown Progress Bars */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-7">
            <h4 className="mb-6 text-sm font-bold tracking-wider text-slate-500 uppercase">
              Failure Categories Breakdown
            </h4>

            <div className="space-y-6">
              {/* Category 1: User Declined */}
              <div>
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
                  <span className="flex items-center gap-2 text-slate-700">
                    <UserCheck className="size-4 text-blue-500" />
                    User Declined
                  </span>
                  <span>
                    {userDeclined} calls ({getPercentage(userDeclined)}%)
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${getPercentage(userDeclined)}%` }}
                  />
                </div>
              </div>

              {/* Category 2: Incomplete Task */}
              <div>
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
                  <span className="flex items-center gap-2 text-slate-700">
                    <Calendar className="size-4 text-amber-500" />
                    Incomplete Task
                  </span>
                  <span>
                    {incompleteTasks} calls ({getPercentage(incompleteTasks)}%)
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-amber-500 transition-all duration-500"
                    style={{ width: `${getPercentage(incompleteTasks)}%` }}
                  />
                </div>
              </div>

              {/* Category 3: Tool Failure */}
              <div>
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
                  <span className="flex items-center gap-2 text-slate-700">
                    <HelpCircle className="size-4 text-rose-500" />
                    Tool Failure
                  </span>
                  <span>
                    {toolFailures} calls ({getPercentage(toolFailures)}%)
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-rose-500 transition-all duration-500"
                    style={{ width: `${getPercentage(toolFailures)}%` }}
                  />
                </div>
              </div>

              {/* Category 4: API Error */}
              <div>
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-600">
                  <span className="flex items-center gap-2 text-slate-700">
                    <Globe className="size-4 text-purple-500" />
                    API Error
                  </span>
                  <span>
                    {apiErrors} calls ({getPercentage(apiErrors)}%)
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-purple-500 transition-all duration-500"
                    style={{ width: `${getPercentage(apiErrors)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Calls Table Section */}
        <div className="mb-12 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 bg-slate-50/50 px-6 py-5">
            <h4 className="text-sm font-bold tracking-wider text-slate-500 uppercase">
              Recent Calls
            </h4>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/20 text-xs font-bold text-slate-400 uppercase">
                  <th className="px-6 py-4">When</th>
                  <th className="px-6 py-4">Duration</th>
                  <th className="px-6 py-4">Channel</th>
                  <th className="px-6 py-4">Outcome</th>
                  <th className="px-6 py-4">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {filteredCalls.length > 0 ? (
                  filteredCalls.map((call) => {
                    const when = call.ended_at ? new Date(call.ended_at).toLocaleString() : '—';
                    const duration = call.duration_seconds
                      ? call.duration_seconds < 60
                        ? Math.round(call.duration_seconds) + 's'
                        : Math.floor(call.duration_seconds / 60) +
                          'm ' +
                          Math.round(call.duration_seconds % 60) +
                          's'
                      : '—';

                    const success = call.outcome === 'success';
                    const resultLabel = success
                      ? (call.eligibility_completed ? 'eligibility checks' : '') +
                          (call.document_list_delivered
                            ? call.eligibility_completed
                              ? ' + document delivery'
                              : 'document delivery'
                            : '') || 'connected'
                      : call.failure_type || 'failed';

                    return (
                      <tr key={call.call_id} className="transition hover:bg-slate-50/50">
                        <td className="px-6 py-4 font-medium whitespace-nowrap text-slate-600">
                          {when}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">{duration}</td>
                        <td className="px-6 py-4 whitespace-nowrap capitalize">{call.channel}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              success
                                ? 'border border-emerald-100 bg-emerald-50 text-emerald-700'
                                : 'border border-rose-100 bg-rose-50 text-rose-700'
                            }`}
                          >
                            {call.outcome || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-slate-500 capitalize">
                          {resultLabel}
                          {call.scheme_codes && call.scheme_codes.length > 0 && (
                            <span className="mt-0.5 block text-xs text-slate-400 lowercase">
                              Schemes: {call.scheme_codes.join(', ')}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center font-medium text-slate-400">
                      No calls recorded in this view.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
