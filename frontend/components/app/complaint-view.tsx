'use client';

import React, { useState, useEffect } from 'react';
import { Send, FileCheck, PhoneCall, ChevronRight, CheckCircle2, ShieldAlert } from 'lucide-react';

interface RecentCall {
  call_id: string;
  started_at: string;
  scheme_codes: string[];
}

export function ComplaintView() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [category, setCategory] = useState('scheme_eligibility');
  const [selectedCallId, setSelectedCallId] = useState('');
  const [description, setDescription] = useState('');
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([]);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [ticketId, setTicketId] = useState('');

  // Load recent calls to populate dropdown
  useEffect(() => {
    async function loadCalls() {
      try {
        const res = await fetch('/api/metrics');
        if (res.ok) {
          const data = await res.json();
          if (data && data.recent_calls) {
            setRecentCalls(
              data.recent_calls.map((c: any) => ({
                call_id: c.call_id,
                started_at: c.started_at,
                scheme_codes: c.scheme_codes || [],
              }))
            );
          }
        }
      } catch (err) {
        console.warn('Error loading recent calls for grievance form:', err);
      }
    }
    loadCalls();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !phone.trim() || !description.trim()) {
      alert('Please fill in all required fields.');
      return;
    }
    
    setIsSubmitting(true);

    // Simulate network submission
    setTimeout(() => {
      const generatedTicket = `JS-2026-${Math.floor(100000 + Math.random() * 900000)}`;
      setTicketId(generatedTicket);
      setIsSubmitting(false);
      setSubmitSuccess(true);
      
      // Store ticket in local storage so it can be picked up by the escalations tab!
      try {
        const stored = localStorage.getItem('jan_sahay_escalations');
        const tickets = stored ? JSON.parse(stored) : [];
        tickets.push({
          ticket_id: generatedTicket,
          name: name.trim(),
          phone: phone.trim().slice(0, -4) + 'XXXX', // Mask phone
          category: category === 'scheme_eligibility' ? 'Scheme Eligibility' : category === 'banking_fraud' ? 'Fraud Report' : 'Service Grievance',
          call_id: selectedCallId || 'Direct Submission',
          description: description.trim(),
          status: 'Assigned to Nodal Officer',
          date: new Date().toISOString(),
        });
        localStorage.setItem('jan_sahay_escalations', JSON.stringify(tickets));
      } catch (err) {
        console.error('Failed to save escalation ticket:', err);
      }
    }, 1200);
  };

  const handleResetForm = () => {
    setName('');
    setPhone('');
    setCategory('scheme_eligibility');
    setSelectedCallId('');
    setDescription('');
    setSubmitSuccess(false);
    setTicketId('');
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans p-6 md:p-8">
      <div className="mx-auto max-w-4xl">
        {/* Title */}
        <div className="border-b border-slate-200 pb-6 mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-[#0f294a] flex items-center gap-3">
            <span className="p-2 rounded-xl bg-blue-50 text-[#0c538e]">
              <FileCheck className="size-6 md:size-8" />
            </span>
            Citizen Grievance Helpline
          </h1>
          <p className="mt-1.5 text-sm md:text-base text-slate-500">
            Submit complaints, report digital banking frauds, or dispute government scheme eligibility decisions.
          </p>
        </div>

        {!submitSuccess ? (
          <div className="bg-white border border-slate-200 rounded-3xl p-6 md:p-8 shadow-sm">
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-6 pb-2 border-b border-slate-100 flex items-center gap-2">
              <ShieldAlert className="size-4 text-slate-400" />
              Official Grievance Registration Form
            </h3>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Full Name */}
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="fullname" className="text-xs font-bold text-slate-500 uppercase">
                    Citizen Full Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="fullname"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your legal full name"
                    className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0f4a73] focus:bg-white transition text-sm font-semibold"
                  />
                </div>

                {/* Mobile Number */}
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="phone" className="text-xs font-bold text-slate-500 uppercase">
                    Contact Mobile Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="phone"
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Enter your 10-digit mobile number"
                    className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0f4a73] focus:bg-white transition text-sm font-semibold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Grievance Category */}
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="category" className="text-xs font-bold text-slate-500 uppercase">
                    Grievance Category <span className="text-rose-500">*</span>
                  </label>
                  <select
                    id="category"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0f4a73] focus:bg-white transition text-sm font-semibold"
                  >
                    <option value="scheme_eligibility">Scheme Eligibility Issue</option>
                    <option value="banking_fraud">Digital Banking Fraud / Scam</option>
                    <option value="service_complaint">General Banking Service Complaint</option>
                  </select>
                </div>

                {/* Call Reference */}
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="call_ref" className="text-xs font-bold text-slate-500 uppercase">
                    Select Call Reference (Optional)
                  </label>
                  <select
                    id="call_ref"
                    value={selectedCallId}
                    onChange={(e) => setSelectedCallId(e.target.value)}
                    className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0f4a73] focus:bg-white transition text-sm font-semibold"
                  >
                    <option value="">-- No call reference associated --</option>
                    {recentCalls.map((c) => {
                      const dateStr = new Date(c.started_at).toLocaleDateString();
                      const schemeStr = c.scheme_codes.length > 0 
                        ? `(${c.scheme_codes.join(', ').toUpperCase()})` 
                        : '';
                      return (
                        <option key={c.call_id} value={c.call_id}>
                          Call ID: {c.call_id} on {dateStr} {schemeStr}
                        </option>
                      );
                    })}
                  </select>
                </div>
              </div>

              {/* Grievance Description */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="description" className="text-xs font-bold text-slate-500 uppercase">
                  Detailed Description of Grievance <span className="text-rose-500">*</span>
                </label>
                <textarea
                  id="description"
                  required
                  rows={5}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide complete details including scheme name, bank branch, and what went wrong during transaction/eligibility check..."
                  className="px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-[#0f4a73] focus:bg-white transition text-sm font-medium leading-relaxed"
                />
              </div>

              {/* Submit Button */}
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-[#0f4a73] hover:bg-[#0c538e] rounded-xl shadow-md transition active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                >
                  {isSubmitting ? (
                    <>
                      <div className="size-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Registering...
                    </>
                  ) : (
                    <>
                      <Send className="size-4" />
                      Register Grievance
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm text-center">
            <div className="inline-flex p-4 rounded-3xl bg-emerald-50 text-emerald-600 mb-6 border border-emerald-100">
              <CheckCircle2 className="size-12" />
            </div>

            <h2 className="text-2xl font-extrabold text-slate-800">Grievance Registered Successfully!</h2>
            <p className="mt-2 text-slate-500 text-sm font-semibold max-w-lg mx-auto leading-relaxed">
              Your ticket has been officially logged in the system. The Nodal Officer has been notified and will review your request.
            </p>

            {/* Ticket details box */}
            <div className="max-w-md mx-auto bg-slate-50 border border-slate-200 rounded-2xl p-5 my-8 text-left space-y-3">
              <div className="flex justify-between items-center text-xs font-bold text-slate-400 uppercase tracking-wide">
                <span>Grievance Ticket ID</span>
                <span className="text-[#0c538e] select-all font-mono font-bold bg-blue-50 px-2 py-0.5 rounded">
                  {ticketId}
                </span>
              </div>
              <div className="border-t border-slate-200/60 pt-3 flex justify-between text-sm text-slate-600">
                <span className="font-semibold">Citizen Name:</span>
                <span className="font-bold text-slate-800">{name}</span>
              </div>
              <div className="flex justify-between text-sm text-slate-600">
                <span className="font-semibold">Category:</span>
                <span className="font-bold text-slate-800 capitalize">
                  {category === 'scheme_eligibility' ? 'Scheme Eligibility' : category === 'banking_fraud' ? 'Fraud Report' : 'Service Complaint'}
                </span>
              </div>
              <div className="flex justify-between text-sm text-slate-600">
                <span className="font-semibold">Estimated Resolution:</span>
                <span className="font-bold text-amber-600">Within 3-5 Working Days</span>
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <button
                onClick={handleResetForm}
                className="px-5 py-2.5 text-sm font-bold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition shadow-sm"
              >
                File Another Complaint
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
