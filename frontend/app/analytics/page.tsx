'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity,
  ArrowLeft,
  Calendar,
  Clock,
  FileText,
  Globe,
  Monitor,
  Phone,
  RefreshCw,
  Shield,
  UserCheck,
} from 'lucide-react';

interface CallRecord {
  id: number;
  room_name: string;
  participant_identity: string;
  status: string;
  created_at: string;
  ended_at: string | null;
  error_message: string | null;
  duration: number;
  avg_latency: number;
  channel: string;
  language: string;
  failure_type: string;
  outcome_type: string;
}

export default function AnalyticsPage() {
  const [history, setHistory] = useState<CallRecord[]>([]);

  // Filters State
  const [filterLanguage, setFilterLanguage] = useState<string>('All');
  const [filterChannel, setFilterChannel] = useState<string>('All');
  const [filterStatus, setFilterStatus] = useState<string>('All');
  const [filterDate, setFilterDate] = useState<string>('All'); // All, Today, Last7Days

  const fetchData = async () => {
    try {
      const historyRes = await fetch('/api/stats/history');
      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData);
      }
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    }
  };

  // Live Auto-Refresh (every 3 seconds)
  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchData();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const formatDuration = (seconds: number) => {
    if (!seconds || seconds <= 0) return '0s';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
  };

  const formatDate = (isoString: string) => {
    if (!isoString) return '—';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  // Apply filters to calls list
  const filteredHistory = history.filter((call) => {
    // Language filter
    if (filterLanguage !== 'All' && call.language !== filterLanguage) return false;

    // Channel filter
    if (filterChannel !== 'All' && call.channel !== filterChannel) return false;

    // Status filter
    if (filterStatus !== 'All' && call.status !== filterStatus) return false;

    // Date filter
    if (filterDate !== 'All') {
      const callDate = new Date(call.created_at);
      const now = new Date();
      if (filterDate === 'Today') {
        if (callDate.toDateString() !== now.toDateString()) return false;
      } else if (filterDate === 'Last7Days') {
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(now.getDate() - 7);
        if (callDate < sevenDaysAgo) return false;
      }
    }

    return true;
  });

  // Re-calculate statistics for filtered list
  const filteredStats = React.useMemo(() => {
    const total = filteredHistory.length;
    const successful = filteredHistory.filter((c) => c.status === 'success').length;
    const failed = filteredHistory.filter((c) => c.status === 'failed').length;
    const successRate = total > 0 ? (successful / total) * 100 : 0;

    const accepted = filteredHistory.filter((c) => c.failure_type !== 'user_declined').length;
    const rejected = filteredHistory.filter((c) => c.failure_type === 'user_declined').length;
    const acceptanceRate = total > 0 ? (accepted / total) * 100 : 0;

    const latencySum = filteredHistory
      .filter((c) => c.status === 'success' && c.avg_latency > 0)
      .reduce((sum, c) => sum + c.avg_latency, 0);
    const latencyCount = filteredHistory.filter(
      (c) => c.status === 'success' && c.avg_latency > 0
    ).length;
    const avgLatency = latencyCount > 0 ? latencySum / latencyCount : 0;

    // Failures grouping for filtered list
    const failures: Record<string, number> = {
      user_declined: 0,
      incomplete_task: 0,
      tool_failure: 0,
      api_error: 0,
      no_response: 0,
      user_hangup: 0,
    };
    filteredHistory.forEach((c) => {
      if (c.status === 'failed' && c.failure_type in failures) {
        failures[c.failure_type]++;
      }
    });

    // Outcomes grouping for filtered list
    const outcomes: Record<string, number> = {
      eligibility_check: 0,
      escalation: 0,
      saved_facts: 0,
    };
    filteredHistory.forEach((c) => {
      if (c.outcome_type in outcomes) {
        outcomes[c.outcome_type]++;
      }
    });

    return {
      total,
      successful,
      failed,
      successRate,
      accepted,
      rejected,
      acceptanceRate,
      avgLatency,
      failures,
      outcomes,
    };
  }, [filteredHistory]);

  const failureTypesLabels: Record<string, { label: string; color: string }> = {
    user_declined: { label: 'User Declined', color: 'bg-amber-500' },
    incomplete_task: { label: 'Incomplete Conversation', color: 'bg-yellow-500' },
    tool_failure: { label: 'Database/Tool Exception', color: 'bg-red-500' },
    api_error: { label: 'LLM/STT API Error', color: 'bg-rose-500' },
    no_response: { label: 'User Silent (No Response)', color: 'bg-slate-500' },
    user_hangup: { label: 'User Hang-up', color: 'bg-purple-500' },
  };

  const outcomeLabels: Record<string, string> = {
    eligibility_check: 'Scheme Eligibility Checked',
    escalation: 'Human Support Escalation',
    saved_facts: 'User Registered / Facts Saved',
    none: 'Normal Chat / Inquiry Only',
  };

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden bg-slate-950 font-sans text-slate-100">
      {/* Background Subtle Ambient Glow Circles */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(16,185,129,0.06),transparent)]" />

      {/* Top Banner Ribbon */}
      <div className="h-1.5 w-full shrink-0 bg-gradient-to-r from-[#FF9933] via-amber-300 via-white to-[#10B981] shadow-md" />

      <main className="relative z-10 mx-auto w-full max-w-7xl px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <Link
              href="/"
              className="mb-3 inline-flex items-center gap-2 text-xs font-bold text-slate-400 transition-colors hover:text-amber-400"
            >
              <ArrowLeft className="h-4.5 w-4.5" /> Back to Citizen Portal
            </Link>
            <h1 className="text-2xl leading-tight font-extrabold tracking-tight text-white sm:text-3xl">
              Sita AI Call Performance & Metrics
            </h1>
            <p className="mt-1 text-xs text-slate-400">
              Stand-alone monitoring dashboard containing response latency analytics, failure
              classification, and outcomes tracking.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-[10px] font-extrabold tracking-widest text-emerald-400 uppercase">
              <span className="h-1.5 w-1.5 animate-ping rounded-full bg-emerald-400" />
              Live Monitoring Active
            </span>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/90 px-4 py-2 text-xs font-bold text-slate-200 transition-all hover:bg-slate-800"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Sync Stats
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        <section className="mb-8 rounded-2xl border border-slate-800 bg-slate-900/30 p-5 backdrop-blur-md">
          <div className="mb-4 flex items-center gap-2 border-b border-slate-800 pb-3">
            <Globe className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-extrabold tracking-wider text-white uppercase">
              Filter Metrics
            </h3>
          </div>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <label className="mb-2 block text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
                Date Range
              </label>
              <select
                value={filterDate}
                onChange={(e) => setFilterDate(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs font-bold text-white focus:border-amber-400 focus:outline-none"
              >
                <option value="All">All Time</option>
                <option value="Today">Today Only</option>
                <option value="Last7Days">Past 7 Days</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
                Language
              </label>
              <select
                value={filterLanguage}
                onChange={(e) => setFilterLanguage(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs font-bold text-white focus:border-amber-400 focus:outline-none"
              >
                <option value="All">All Languages</option>
                <option value="English">English</option>
                <option value="Kannada (ಕನ್ನಡ)">Kannada (ಕನ್ನಡ)</option>
                <option value="Hindi (ಹಿन्दी)">Hindi (ಹಿन्दी)</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
                Call Channel
              </label>
              <select
                value={filterChannel}
                onChange={(e) => setFilterChannel(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs font-bold text-white focus:border-amber-400 focus:outline-none"
              >
                <option value="All">All Channels</option>
                <option value="Browser">Browser Portal</option>
                <option value="SIP">SIP / Outbound trunk</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
                Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-xs font-bold text-white focus:border-amber-400 focus:outline-none"
              >
                <option value="All">All Statuses</option>
                <option value="success">Success Only</option>
                <option value="failed">Failed Only</option>
                <option value="started">Started / Active Only</option>
              </select>
            </div>
          </div>
        </section>

        {/* Primary Metrics and Success Dial Grid */}
        <section className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Success Rate Dial */}
          <div className="relative flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
            <h3 className="absolute top-5 left-5 text-sm font-bold text-slate-200">
              Call Acceptance Rate
            </h3>
            <div className="relative mt-8 flex h-40 w-40 items-center justify-center">
              <svg className="h-full w-full -rotate-90">
                <circle
                  cx="80"
                  cy="80"
                  r="64"
                  className="fill-none stroke-slate-800"
                  strokeWidth="10"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="64"
                  className="fill-none stroke-emerald-500 transition-all duration-550"
                  strokeWidth="10"
                  strokeDasharray={2 * Math.PI * 64}
                  strokeDashoffset={2 * Math.PI * 64 * (1 - filteredStats.acceptanceRate / 100)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center">
                <span className="text-3xl font-extrabold text-white">
                  {filteredStats.acceptanceRate.toFixed(1)}%
                </span>
                <span className="mt-1 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
                  Accepted
                </span>
              </div>
            </div>
            <p className="mt-4 text-center text-xs font-medium text-slate-400">
              {filteredStats.accepted} Accepted &nbsp;/&nbsp; {filteredStats.rejected} Rejected
            </p>
          </div>

          {/* Performance stats Grid */}
          <div className="grid grid-cols-2 gap-4 lg:col-span-2">
            <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold tracking-wider text-slate-400 uppercase">
                  Total Calls
                </span>
                <Phone className="h-5 w-5 text-amber-400" />
              </div>
              <div className="mt-4">
                <h4 className="text-4xl font-extrabold text-white">{filteredStats.total}</h4>
                <p className="mt-1 text-[10px] text-slate-400">
                  {filteredStats.successful} Success / {filteredStats.failed} Failures
                </p>
              </div>
            </div>

            <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold tracking-wider text-slate-400 uppercase">
                  Avg Voice Latency
                </span>
                <Clock className="h-5 w-5 text-emerald-400" />
              </div>
              <div className="mt-4">
                <h4 className="text-4xl font-extrabold text-white">
                  {filteredStats.avgLatency.toFixed(2)}s
                </h4>
                <p className="mt-1 text-[10px] text-slate-400">
                  STT processing to agent playout start.
                </p>
              </div>
            </div>

            <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold tracking-wider text-slate-400 uppercase">
                  Outbound Ratio
                </span>
                <Activity className="h-5 w-5 text-purple-400" />
              </div>
              <div className="mt-4">
                <h4 className="text-4xl font-extrabold text-white">
                  {filteredStats.total > 0
                    ? (
                        (filteredHistory.filter((c) => c.channel === 'SIP').length /
                          filteredStats.total) *
                        100
                      ).toFixed(0)
                    : 0}
                  %
                </h4>
                <p className="mt-1 text-[10px] text-slate-400">
                  Percentage of calls arriving via SIP.
                </p>
              </div>
            </div>

            <div className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold tracking-wider text-slate-400 uppercase">
                  Average Duration
                </span>
                <Calendar className="h-5 w-5 text-rose-400" />
              </div>
              <div className="mt-4">
                <h4 className="text-4xl font-extrabold text-white">
                  {filteredHistory.length > 0
                    ? (
                        filteredHistory.reduce((sum, c) => sum + c.duration, 0) /
                        filteredHistory.length
                      ).toFixed(0)
                    : 0}
                  s
                </h4>
                <p className="mt-1 text-[10px] text-slate-400">Average call talk duration.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Failures and Outcomes Breakdown Panels */}
        <section className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Failure groups (Custom Bar Chart Layout) */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
            <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Failure Classifications</h3>
              <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-[10px] font-bold text-rose-400">
                Failed: {filteredStats.failed}
              </span>
            </div>

            <div className="space-y-4 text-left">
              {Object.entries(failureTypesLabels).map(([type, meta]) => {
                const count = filteredStats.failures[type] ?? 0;
                const pct = filteredStats.failed > 0 ? (count / filteredStats.failed) * 100 : 0;
                return (
                  <div key={type} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-300">{meta.label}</span>
                      <span className="font-bold text-slate-100">
                        {count} ({pct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                      <div
                        className={`h-full rounded-full transition-all duration-550 ${meta.color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Outcomes counters */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-xl backdrop-blur-md">
            <div className="mb-6 border-b border-slate-800 pb-3 text-left">
              <h3 className="text-base font-bold text-white">Citizen Portal Outcomes</h3>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div className="border-slate-850 flex items-center justify-between rounded-xl border bg-slate-950/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-indigo-500/20 bg-indigo-500/10 text-indigo-400">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="text-left">
                    <h4 className="text-sm font-bold text-white">Eligibility Checks</h4>
                    <p className="text-[10px] text-slate-500">Calculated eligibility checklists</p>
                  </div>
                </div>
                <span className="text-xl font-extrabold text-indigo-400">
                  {filteredStats.outcomes.eligibility_check ?? 0}
                </span>
              </div>

              <div className="border-slate-850 flex items-center justify-between rounded-xl border bg-slate-950/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/10 text-rose-400">
                    <Shield className="h-5 w-5" />
                  </div>
                  <div className="text-left">
                    <h4 className="text-sm font-bold text-white">Human Escalations</h4>
                    <p className="text-[10px] text-slate-500">Escalation tickets created</p>
                  </div>
                </div>
                <span className="text-xl font-extrabold text-rose-400">
                  {filteredStats.outcomes.escalation ?? 0}
                </span>
              </div>

              <div className="border-slate-850 flex items-center justify-between rounded-xl border bg-slate-950/60 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/10 text-emerald-400">
                    <UserCheck className="h-5 w-5" />
                  </div>
                  <div className="text-left">
                    <h4 className="text-sm font-bold text-white">User Facts Saved</h4>
                    <p className="text-[10px] text-slate-500">Returning profiles updated</p>
                  </div>
                </div>
                <span className="text-xl font-extrabold text-emerald-400">
                  {filteredStats.outcomes.saved_facts ?? 0}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* History Log Table */}
        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/50 p-5 text-left">
            <div>
              <h3 className="text-base font-bold text-white">Audit Log History</h3>
              <p className="mt-1 text-xs text-slate-400">
                Detailed list of conversations captured by the voice agent.
              </p>
            </div>
            <span className="rounded-full bg-slate-800 px-3 py-1 text-[10px] font-bold text-slate-300">
              Showing {filteredHistory.length} calls
            </span>
          </div>

          <div className="overflow-x-auto">
            {filteredHistory.length === 0 ? (
              <div className="py-20 text-center text-xs text-slate-500">
                No calls match your active filters.
              </div>
            ) : (
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/40 font-bold tracking-wider text-slate-400 uppercase">
                    <th className="px-5 py-4">ID</th>
                    <th className="px-5 py-4">Channel / Room</th>
                    <th className="px-5 py-4">Language</th>
                    <th className="px-5 py-4">Outcome</th>
                    <th className="px-5 py-4">Status & Details</th>
                    <th className="px-5 py-4">Latency</th>
                    <th className="px-5 py-4">Talk Time</th>
                    <th className="px-5 py-4">Start Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/85">
                  {filteredHistory.map((call) => (
                    <tr key={call.id} className="transition-colors hover:bg-slate-900/40">
                      <td className="px-5 py-4 font-bold text-slate-400">#{call.id}</td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1.5 font-bold">
                          <span
                            className={`rounded p-1 ${call.channel === 'SIP' ? 'border border-purple-500/20 bg-purple-500/10 text-purple-400' : 'border border-blue-500/20 bg-blue-500/10 text-blue-400'}`}
                            title={call.channel}
                          >
                            {call.channel === 'SIP' ? (
                              <Phone className="h-3 w-3" />
                            ) : (
                              <Monitor className="h-3 w-3" />
                            )}
                          </span>
                          <span className="max-w-[150px] truncate font-mono text-slate-300">
                            {call.room_name}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="rounded border border-slate-700 bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-300">
                          {call.language}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-bold text-slate-200">
                          {outcomeLabels[call.outcome_type] || call.outcome_type}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-extrabold tracking-wide uppercase ${
                            call.status === 'success'
                              ? 'border border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
                              : call.status === 'failed'
                                ? 'border border-rose-500/20 bg-rose-500/10 text-rose-400'
                                : 'border border-amber-500/20 bg-amber-500/10 text-amber-400'
                          }`}
                        >
                          {call.status === 'success' && (
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                          )}
                          {call.status === 'failed' && (
                            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          )}
                          {call.status === 'started' && (
                            <span className="bg-amber-450 h-1.5 w-1.5 animate-pulse rounded-full" />
                          )}
                          {call.status}
                        </span>
                        {call.status === 'failed' && (
                          <div className="mt-1 text-[10px] font-semibold text-rose-300">
                            Class:{' '}
                            {failureTypesLabels[call.failure_type]?.label || call.failure_type}
                          </div>
                        )}
                        {call.error_message && (
                          <div
                            className="mt-0.5 max-w-[200px] truncate font-mono text-[10px] text-rose-400/80"
                            title={call.error_message}
                          >
                            {call.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4 font-bold text-slate-200">
                        {call.status === 'success' && call.avg_latency > 0 ? (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-slate-500" />
                            {call.avg_latency.toFixed(2)}s
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="px-5 py-4 font-bold text-slate-200">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-slate-500" />
                          {formatDuration(call.duration)}
                        </div>
                      </td>
                      <td className="text-slate-350 px-5 py-4">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-3 w-3 text-slate-500" />
                          {formatDate(call.created_at)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
