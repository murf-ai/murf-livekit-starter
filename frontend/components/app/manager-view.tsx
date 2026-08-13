'use client';

import { useEffect, useState } from 'react';
import {
  ArrowRightLeft,
  CheckCircle2,
  Clock,
  Key,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  UserPlus,
  XCircle,
} from 'lucide-react';

interface ManagerRequest {
  request_id: string;
  request_type: 'ACCOUNT_ACTIVATION' | 'TRANSACTION_TRANSFER';
  requester_name: string;
  user_id: string;
  safe_key?: string;
  details: Record<string, any>;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED';
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export function ManagerView() {
  const [requests, setRequests] = useState<ManagerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('PENDING');

  const fetchRequests = async () => {
    try {
      const res = await fetch('/api/manager/requests', { cache: 'no-store' });
      if (!res.ok) throw new Error('Failed to load manager queue');
      const json = await res.json();
      setRequests(json);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch manager requests';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
    const interval = setInterval(fetchRequests, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (requestId: string) => {
    setActionLoading(requestId);
    try {
      const res = await fetch('/api/manager/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, notes: 'Approved by Senior Manager X' }),
      });
      if (res.ok) {
        await fetchRequests();
      }
    } catch (err) {
      console.error('Approve failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (requestId: string) => {
    setActionLoading(requestId);
    try {
      const res = await fetch('/api/manager/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, notes: 'Rejected by Manager' }),
      });
      if (res.ok) {
        await fetchRequests();
      }
    } catch (err) {
      console.error('Reject failed:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (filterType !== 'ALL' && r.request_type !== filterType) return false;
    if (filterStatus === 'PENDING' && r.status !== 'PENDING_APPROVAL') return false;
    if (filterStatus === 'APPROVED' && r.status !== 'APPROVED') return false;
    if (filterStatus === 'REJECTED' && r.status !== 'REJECTED') return false;
    return true;
  });

  const pendingCount = requests.filter((r) => r.status === 'PENDING_APPROVAL').length;
  const accountCount = requests.filter((r) => r.request_type === 'ACCOUNT_ACTIVATION').length;
  const transferCount = requests.filter((r) => r.request_type === 'TRANSACTION_TRANSFER').length;
  const approvedCount = requests.filter((r) => r.status === 'APPROVED').length;

  return (
    <div className="min-h-full space-y-8 bg-slate-950 p-6 font-sans text-slate-100 md:p-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-2.5 text-blue-400">
            <UserCheck className="size-6" />
          </div>
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-black tracking-tight text-white">
              Senior Manager Approval Portal
              <span className="rounded-full border border-amber-500/30 bg-amber-500/20 px-2.5 py-0.5 text-xs font-bold tracking-wider text-amber-300 uppercase">
                FAKE BANK MANAGER
              </span>
            </h1>
            <p className="text-sm font-medium text-slate-400">
              Review and manually approve account activations, Safe Keys, and high-value transaction
              transfers
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setLoading(true);
            fetchRequests();
          }}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-slate-700"
        >
          <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Queue
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm font-medium text-rose-300">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Pending Approvals</span>
            <Clock className="size-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-amber-400">{pendingCount}</div>
          <div className="mt-1 text-xs text-slate-500">Awaiting Manager decision</div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">
              Account Creation Requests
            </span>
            <UserPlus className="size-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black text-blue-400">{accountCount}</div>
          <div className="mt-1 text-xs text-slate-500">Safe Key account setups</div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">
              Transfers & Transactions
            </span>
            <ArrowRightLeft className="size-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-emerald-400">{transferCount}</div>
          <div className="mt-1 text-xs text-slate-500">Safe Key verified transfers</div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold tracking-wider uppercase">Approved Requests</span>
            <CheckCircle2 className="size-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-white">{approvedCount}</div>
          <div className="mt-1 text-xs text-slate-500">Activated & executed</div>
        </div>
      </div>

      {/* Filter Tabs & Content */}
      <div className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/80 p-6">
        <div className="flex flex-col items-start justify-between gap-4 border-b border-slate-800 pb-4 sm:flex-row sm:items-center">
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setFilterStatus('PENDING')}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                filterStatus === 'PENDING'
                  ? 'border border-amber-500/40 bg-amber-500/20 text-amber-300'
                  : 'border border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
              }`}
            >
              Pending ({pendingCount})
            </button>
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                filterStatus === 'ALL'
                  ? 'border border-blue-500/40 bg-blue-500/20 text-blue-300'
                  : 'border border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
              }`}
            >
              All History ({requests.length})
            </button>
            <button
              onClick={() => setFilterStatus('APPROVED')}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
                filterStatus === 'APPROVED'
                  ? 'border border-emerald-500/40 bg-emerald-500/20 text-emerald-300'
                  : 'border border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
              }`}
            >
              Approved ({approvedCount})
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-400">Type:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs font-bold text-slate-200"
            >
              <option value="ALL">All Types</option>
              <option value="ACCOUNT_ACTIVATION">Account Activations</option>
              <option value="TRANSACTION_TRANSFER">Transfers & Transactions</option>
            </select>
          </div>
        </div>

        {/* Requests List */}
        {!filteredRequests.length ? (
          <div className="rounded-xl border border-dashed border-slate-800 py-12 text-center text-slate-500">
            <ShieldCheck className="mx-auto mb-2 size-8 text-slate-600" />
            <p className="text-sm font-medium">No requests matching filter criteria</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRequests.map((req) => (
              <div
                key={req.request_id}
                className="flex flex-col justify-between gap-6 rounded-xl border border-slate-800 bg-slate-950 p-5 transition hover:border-slate-700 md:flex-row md:items-center"
              >
                <div className="flex-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-slate-400">
                      {req.request_id}
                    </span>
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-[10px] font-extrabold uppercase ${
                        req.request_type === 'ACCOUNT_ACTIVATION'
                          ? 'border-blue-500/40 bg-blue-500/20 text-blue-300'
                          : 'border-emerald-500/40 bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      {req.request_type === 'ACCOUNT_ACTIVATION'
                        ? 'Account Creation'
                        : 'Transaction Transfer'}
                    </span>
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-[10px] font-extrabold uppercase ${
                        req.status === 'PENDING_APPROVAL'
                          ? 'border-amber-500/40 bg-amber-500/20 text-amber-400'
                          : req.status === 'APPROVED'
                            ? 'border-emerald-500/40 bg-emerald-500/20 text-emerald-400'
                            : 'border-rose-500/40 bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {req.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(req.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-sm font-bold text-white">
                    <span>
                      Applicant: <span className="text-blue-400">{req.requester_name}</span>
                    </span>
                    {req.safe_key && (
                      <span className="inline-flex items-center gap-1.5 rounded border border-amber-500/30 bg-slate-900 px-2.5 py-1 font-mono text-xs text-amber-300">
                        <Key className="size-3 text-amber-400" />
                        Safe Key: <strong className="text-white">{req.safe_key}</strong>
                      </span>
                    )}
                  </div>

                  <p className="text-xs leading-relaxed font-medium text-slate-400">
                    {req.details?.intent || req.details?.account_type
                      ? `Details: ${req.details.intent || req.details.account_type}`
                      : 'Request submitted via Jan Sahay AI voice assistant'}
                  </p>
                </div>

                {/* Manager Actions */}
                {req.status === 'PENDING_APPROVAL' && (
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      disabled={actionLoading === req.request_id}
                      onClick={() => handleApprove(req.request_id)}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-black text-slate-950 shadow-md transition hover:bg-emerald-600"
                    >
                      <CheckCircle2 className="size-4" />
                      Approve & Activate
                    </button>
                    <button
                      disabled={actionLoading === req.request_id}
                      onClick={() => handleReject(req.request_id)}
                      className="flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3.5 py-2 text-xs font-bold text-rose-400 transition hover:bg-rose-500/20"
                    >
                      <XCircle className="size-4" />
                      Reject
                    </button>
                  </div>
                )}

                {req.status !== 'PENDING_APPROVAL' && (
                  <div className="shrink-0 text-xs font-semibold text-slate-500 italic">
                    {req.resolution_notes || req.status}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
