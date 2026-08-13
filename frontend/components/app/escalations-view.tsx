'use client';

import React, { useEffect, useState } from 'react';
import {
  Award,
  ChevronRight,
  FileText,
  Layers,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  User,
} from 'lucide-react';

interface EscalationTicket {
  ticket_id: string;
  name: string;
  phone: string;
  category: string;
  call_id: string;
  description: string;
  status: string;
  date: string;
  priority?: 'High' | 'Medium' | 'Low';
  nodal_officer?: string;
}

const DEFAULT_MOCK_TICKETS: EscalationTicket[] = [
  {
    ticket_id: 'JS-2026-894721',
    name: 'Ramesh Chandra Kumar',
    phone: '9845XXXXXX',
    category: 'Scheme Eligibility',
    call_id: 'd9b3ac1f',
    description:
      'Denied PM Suraksha Bima Yojana due to age limit confusion (citizen is 64 years old, which is well within the 18-70 limit).',
    status: 'Assigned to Nodal Officer',
    date: new Date(Date.now() - 36 * 3600000).toISOString(), // 36 hours ago
    priority: 'High',
    nodal_officer: 'S. K. Verma (Lead Investigator)',
  },
  {
    ticket_id: 'JS-2026-384119',
    name: 'Sunita Devi Sharma',
    phone: '7829XXXXXX',
    category: 'Fraud Report',
    call_id: 'f87ac521',
    description:
      'Received WhatsApp SMS asking to enter UPI PIN to receive APY pension credit of Rs. 5,000. Potential phishing loop blocked.',
    status: 'Investigation Closed',
    date: new Date(Date.now() - 72 * 3600000).toISOString(), // 72 hours ago
    priority: 'High',
    nodal_officer: 'Sunil Nair (Cyber Cell Analyst)',
  },
];

export function EscalationsView() {
  const [tickets, setTickets] = useState<EscalationTicket[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTickets = async () => {
    try {
      const response = await fetch('/api/escalations');
      if (response.ok) {
        const data = await response.json();

        // Map database escalations to EscalationTicket structure
        const mapped: EscalationTicket[] = data.map((t: any) => {
          let priority: 'High' | 'Medium' | 'Low' = 'Medium';
          if (t.urgency === 'high' || t.urgency === 'emergency') {
            priority = 'High';
          } else if (t.urgency === 'low') {
            priority = 'Low';
          }

          let nodal_officer = 'S. K. Verma (Lead Investigator)';
          if (t.trigger_type === 'fraud_suspected') {
            nodal_officer = 'Sunil Nair (Cyber Cell Analyst)';
          }

          let category = 'General Escalation';
          if (t.trigger_type === 'fraud_suspected') {
            category = 'Fraud Report';
          } else if (t.trigger_type === 'complex_decision') {
            category = 'Scheme Eligibility';
          } else if (t.trigger_type === 'user_requested') {
            category = 'User Request';
          }

          let status = 'Assigned to Nodal Officer';
          if (t.status === 'resolved') {
            status = 'Investigation Closed';
          } else if (t.status === 'in_progress') {
            status = 'In Progress';
          }

          return {
            ticket_id: t.reference_id,
            name: t.requester_name || 'Anonymous Caller',
            phone: t.contact_hint || t.user_id || 'Unknown',
            category: category,
            call_id: t.user_id || 'Unknown',
            description: t.issue_description,
            status: status,
            date: t.created_at || new Date().toISOString(),
            priority: priority,
            nodal_officer: nodal_officer,
          };
        });

        // Display live tickets. If none exist in database, display DEFAULT_MOCK_TICKETS as fallback.
        if (mapped.length > 0) {
          setTickets([...mapped, ...DEFAULT_MOCK_TICKETS]);
        } else {
          setTickets(DEFAULT_MOCK_TICKETS);
        }
      }
    } catch (err) {
      console.error('Error fetching escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
    const interval = setInterval(loadTickets, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 font-sans text-slate-800 md:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Title */}
        <div className="mb-8 flex flex-col gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-bold text-[#0f294a] md:text-3xl">
              <span className="rounded-xl bg-blue-50 p-2 text-[#0c538e]">
                <Layers className="size-6 md:size-8" />
              </span>
              Open Escalations & Tickets
            </h1>
            <p className="mt-1.5 text-sm text-slate-500 md:text-base">
              Track active investigations and citizen tickets escalated directly by Jan Sahay AI.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadTickets}
              className="inline-flex items-center gap-2 rounded-lg border border-blue-200 bg-white px-3.5 py-2 text-sm font-semibold text-blue-600 shadow-sm transition duration-150 hover:border-blue-300 hover:bg-blue-50"
            >
              <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh Tickets
            </button>
          </div>
        </div>

        {/* Tickets Grid list */}
        <div className="space-y-6">
          {tickets.length > 0 ? (
            tickets.map((t) => {
              const dateStr = new Date(t.date).toLocaleString();
              const isClosed = t.status.toLowerCase().includes('closed');

              return (
                <div
                  key={t.ticket_id}
                  className="flex flex-col justify-between gap-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md md:flex-row md:p-6"
                >
                  <div className="flex-1 space-y-4">
                    {/* Header line of ticket */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-lg bg-blue-50 px-2.5 py-0.5 font-mono text-sm font-bold text-[#0c538e] select-all">
                        {t.ticket_id}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold tracking-wide uppercase ${
                          t.priority === 'High'
                            ? 'border border-rose-100 bg-rose-50 text-rose-700'
                            : 'border border-amber-100 bg-amber-50 text-amber-700'
                        }`}
                      >
                        {t.priority || 'Medium'} Priority
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold tracking-wide uppercase ${
                          isClosed
                            ? 'border border-slate-200 bg-slate-100 text-slate-700'
                            : 'border border-emerald-100 bg-emerald-50 text-emerald-700'
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>

                    {/* Content line */}
                    <div>
                      <h4 className="text-base font-extrabold text-slate-800 capitalize">
                        {t.name}{' '}
                        <span className="text-xs font-semibold text-slate-400">({t.phone})</span>
                      </h4>
                      <p className="mt-1 text-xs font-semibold text-slate-400">
                        Category: <span className="text-slate-600">{t.category}</span> · Call Ref:{' '}
                        <span className="font-mono text-slate-600">{t.call_id}</span> · Registered:{' '}
                        {dateStr}
                      </p>
                    </div>

                    <p className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm leading-relaxed font-medium text-slate-500">
                      {t.description}
                    </p>
                  </div>

                  {/* Nodal Officer Section */}
                  <div className="flex flex-col justify-between border-t border-slate-100 pt-4 md:w-64 md:border-t-0 md:border-l md:pt-0 md:pl-6">
                    <div className="space-y-1">
                      <h5 className="flex items-center gap-1.5 text-xs font-bold tracking-wide text-slate-400 uppercase">
                        <User className="size-3.5 text-slate-400" />
                        Assigned Nodal Officer
                      </h5>
                      <p className="mt-1 text-sm font-bold text-slate-700">
                        {t.nodal_officer || 'Unassigned'}
                      </p>
                    </div>

                    <div className="flex cursor-pointer items-center pt-4 text-xs font-bold text-[#0c538e] hover:text-[#0f4a73]">
                      <span>Investigate Details</span>
                      <ChevronRight className="size-4" />
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center font-medium text-slate-400 shadow-sm">
              No open escalations or ticket cases found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
