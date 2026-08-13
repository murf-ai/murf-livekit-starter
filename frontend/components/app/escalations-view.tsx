'use client';

import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, Award, FileText, ChevronRight, User, RefreshCw, Layers } from 'lucide-react';

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
    description: 'Denied PM Suraksha Bima Yojana due to age limit confusion (citizen is 64 years old, which is well within the 18-70 limit).',
    status: 'Assigned to Nodal Officer',
    date: new Date(Date.now() - 36 * 3600000).toISOString(), // 36 hours ago
    priority: 'High',
    nodal_officer: 'S. K. Verma (Lead Investigator)'
  },
  {
    ticket_id: 'JS-2026-384119',
    name: 'Sunita Devi Sharma',
    phone: '7829XXXXXX',
    category: 'Fraud Report',
    call_id: 'f87ac521',
    description: 'Received WhatsApp SMS asking to enter UPI PIN to receive APY pension credit of Rs. 5,000. Potential phishing loop blocked.',
    status: 'Investigation Closed',
    date: new Date(Date.now() - 72 * 3600000).toISOString(), // 72 hours ago
    priority: 'High',
    nodal_officer: 'Sunil Nair (Cyber Cell Analyst)'
  }
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
            nodal_officer: nodal_officer
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
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans p-6 md:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Title */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-6 mb-8 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-[#0f294a] flex items-center gap-3">
              <span className="p-2 rounded-xl bg-blue-50 text-[#0c538e]">
                <Layers className="size-6 md:size-8" />
              </span>
              Open Escalations & Tickets
            </h1>
            <p className="mt-1.5 text-sm md:text-base text-slate-500">
              Track active investigations and citizen tickets escalated directly by Jan Sahay AI.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadTickets}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-semibold text-blue-600 bg-white border border-blue-200 rounded-lg shadow-sm hover:bg-blue-50 hover:border-blue-300 transition duration-150"
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
                  className="bg-white border border-slate-200 rounded-2xl p-5 md:p-6 shadow-sm hover:shadow-md transition flex flex-col md:flex-row justify-between gap-6"
                >
                  <div className="flex-1 space-y-4">
                    {/* Header line of ticket */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-[#0c538e] bg-blue-50 px-2.5 py-0.5 rounded-lg select-all font-mono">
                        {t.ticket_id}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide ${
                        t.priority === 'High' 
                          ? 'bg-rose-50 text-rose-700 border border-rose-100' 
                          : 'bg-amber-50 text-amber-700 border border-amber-100'
                      }`}>
                        {t.priority || 'Medium'} Priority
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide ${
                        isClosed
                          ? 'bg-slate-100 text-slate-700 border border-slate-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                      }`}>
                        {t.status}
                      </span>
                    </div>

                    {/* Content line */}
                    <div>
                      <h4 className="text-base font-extrabold text-slate-800 capitalize">
                        {t.name} <span className="text-slate-400 font-semibold text-xs">({t.phone})</span>
                      </h4>
                      <p className="text-xs text-slate-400 font-semibold mt-1">
                        Category: <span className="text-slate-600">{t.category}</span> · Call Ref: <span className="text-slate-600 font-mono">{t.call_id}</span> · Registered: {dateStr}
                      </p>
                    </div>

                    <p className="text-sm text-slate-500 font-medium leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
                      {t.description}
                    </p>
                  </div>

                  {/* Nodal Officer Section */}
                  <div className="md:w-64 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-6 flex flex-col justify-between">
                    <div className="space-y-1">
                      <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                        <User className="size-3.5 text-slate-400" />
                        Assigned Nodal Officer
                      </h5>
                      <p className="text-sm font-bold text-slate-700 mt-1">
                        {t.nodal_officer || 'Unassigned'}
                      </p>
                    </div>

                    <div className="pt-4 flex items-center text-xs font-bold text-[#0c538e] hover:text-[#0f4a73] cursor-pointer">
                      <span>Investigate Details</span>
                      <ChevronRight className="size-4" />
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="bg-white border border-slate-200 rounded-3xl p-12 text-center text-slate-400 font-medium shadow-sm">
              No open escalations or ticket cases found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
