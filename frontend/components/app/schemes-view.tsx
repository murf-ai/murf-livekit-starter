'use client';

import React, { useState } from 'react';
import {
  ArrowRight,
  Award,
  Check,
  FileText,
  HelpCircle,
  Search,
  ShieldAlert,
  X,
} from 'lucide-react';

interface Scheme {
  id: string;
  code: string;
  name: string;
  nameHindi: string;
  category: 'savings' | 'insurance' | 'pension' | 'credit';
  tagline: string;
  description: string;
  benefits: string[];
  eligibility: string[];
  documents: string[];
}

const SCHEMES: Scheme[] = [
  {
    id: 'pmjdy',
    code: 'pmjdy',
    name: 'Pradhan Mantri Jan Dhan Yojana (PMJDY)',
    nameHindi: 'प्रधानमंत्री जन धन योजना',
    category: 'savings',
    tagline: 'National Mission for Financial Inclusion',
    description:
      'A national mission for financial inclusion to ensure access to financial services, namely, basic savings & deposit accounts, remittance, credit, insurance, pension in an affordable manner.',
    benefits: [
      'Interest on deposit accounts.',
      'Accidental insurance cover of Rs. 2 Lakh (for accounts opened after 28.08.2018).',
      'No minimum balance required.',
      'Overdraft (OD) facility up to Rs. 10,000 to eligible account holders.',
      'Direct Benefit Transfer (DBT) eligible for government schemes.',
    ],
    eligibility: [
      'Must be a citizen of India.',
      'Any individual above 10 years of age can open an account.',
      'Should not possess another savings account.',
    ],
    documents: [
      'Aadhaar Card (if address has changed, present address proof is required).',
      'PAN Card (optional, but recommended).',
      'Voter ID, Passport, or Driving License (if Aadhaar is not available).',
    ],
  },
  {
    id: 'pmsby',
    code: 'pmsby',
    name: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
    nameHindi: 'प्रधानमंत्री सुरक्षा बीमा योजना',
    category: 'insurance',
    tagline: 'Affordable Accidental Insurance Cover',
    description:
      'An accident insurance scheme offering one-year accidental death and disability cover, renewable from year to year.',
    benefits: [
      'Accidental Death Cover of Rs. 2 Lakh.',
      'Total and Irrecoverable Loss of both eyes or loss of use of both hands or feet: Rs. 2 Lakh.',
      'Partial Disability Cover (loss of one eye, hand, or foot): Rs. 1 Lakh.',
      'Extremely low premium of only Rs. 20 per annum (auto-debited from bank account).',
    ],
    eligibility: [
      'Age limit: 18 to 70 years.',
      'Must have an active savings bank account linked to auto-debit consent.',
    ],
    documents: [
      'Aadhaar Card.',
      'Active savings bank account details.',
      'Duly filled application / consent form.',
    ],
  },
  {
    id: 'pmjjby',
    code: 'pmjjby',
    name: 'Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)',
    nameHindi: 'प्रधानमंत्री जीवन ज्योति बीमा योजना',
    category: 'insurance',
    tagline: 'Low-cost Term Life Insurance Scheme',
    description:
      'A government-backed life insurance scheme in India providing term life cover, renewable yearly, in case of death of the insured.',
    benefits: [
      'Life cover of Rs. 2 Lakh in case of death due to any reason.',
      "Premium of Rs. 436 per annum, auto-debited from the account holder's bank account.",
      'Simplified enrolment and claim process.',
    ],
    eligibility: [
      'Age limit: 18 to 50 years (life cover up to 55 years subject to annual renewals).',
      'Must have an active bank account with consent for auto-debit.',
    ],
    documents: ['Aadhaar Card.', 'Bank Account passbook.', 'Consent form for premium auto-debit.'],
  },
  {
    id: 'apy',
    code: 'apy',
    name: 'Atal Pension Yojana (APY)',
    nameHindi: 'अटल पेंशन योजना',
    category: 'pension',
    tagline: 'Guaranteed Pension for Unorganized Sector',
    description:
      'A pension scheme focused on the unorganized sector workers, offering a guaranteed minimum pension after the age of 60 based on the contribution amount and entry age.',
    benefits: [
      'Guaranteed monthly pension of Rs. 1,000, Rs. 2,000, Rs. 3,000, Rs. 4,000, or Rs. 5,000 starting at age 60.',
      'On death of the pensioner, the same pension amount is guaranteed to the spouse for life.',
      'On death of both pensioner and spouse, the accumulated pension corpus is returned to the nominee.',
    ],
    eligibility: [
      'Age limit: 18 to 40 years.',
      'Must have a savings bank account.',
      'Should not be an income tax payer (as per recent rules).',
    ],
    documents: [
      'Aadhaar Card.',
      'Active bank account with auto-debit mandate.',
      'Mobile number linked to the account.',
    ],
  },
  {
    id: 'pmmy',
    code: 'pmmy',
    name: 'Pradhan Mantri Mudra Yojana (PMMY)',
    nameHindi: 'प्रधानमंत्री मुद्रा योजना',
    category: 'credit',
    tagline: 'Micro Unit Funding for Small Businesses',
    description:
      'A scheme to provide loans up to Rs. 10 Lakh to non-corporate, non-farm small/micro enterprises to help fund business establishment, expansions, and working capital.',
    benefits: [
      'Shishu Loans: Cover loans up to Rs. 50,000.',
      'Kishor Loans: Cover loans above Rs. 50,000 and up to Rs. 5 Lakh.',
      'Tarun Loans: Cover loans above Rs. 5 Lakh and up to Rs. 10 Lakh.',
      'No collateral requirement for Mudra loans.',
    ],
    eligibility: [
      'Any Indian citizen who has a business plan for a non-farm income-generating activity.',
      'Micro-enterprises, proprietary firms, partnerships, or small business units.',
    ],
    documents: [
      'Mudra Application Form.',
      'Identity Proof & Address Proof (Aadhaar, Voter ID, PAN).',
      'Business address proof and business registration/license.',
      'Quotes or invoices for machinery/materials to be purchased.',
    ],
  },
];

export function SchemesView() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<
    'all' | 'savings' | 'insurance' | 'pension' | 'credit'
  >('all');
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);

  const filteredSchemes = SCHEMES.filter((scheme) => {
    const matchesSearch =
      scheme.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scheme.nameHindi.includes(searchQuery) ||
      scheme.tagline.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scheme.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = activeCategory === 'all' || scheme.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 font-sans text-slate-800 md:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header Title */}
        <div className="mb-8 border-b border-slate-200 pb-6">
          <h1 className="flex items-center gap-3 text-2xl font-bold text-[#0f294a] md:text-3xl">
            <span className="rounded-xl bg-blue-50 p-2 text-[#0c538e]">
              <FileText className="size-6 md:size-8" />
            </span>
            Government Financial Schemes Search
          </h1>
          <p className="mt-1.5 text-sm text-slate-500 md:text-base">
            Explore and search official Indian government financial literacy and safety schemes
            (PMJDY, PMSBY, APY, PMJJBY, Mudra).
          </p>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div className="relative max-w-lg flex-1">
            <Search className="absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, benefits, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pr-4 pl-11 shadow-sm transition focus:border-transparent focus:ring-2 focus:ring-[#0f4a73] focus:outline-none"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {(['all', 'savings', 'insurance', 'pension', 'credit'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`rounded-xl border px-4 py-2 text-xs font-semibold capitalize transition md:text-sm ${
                  activeCategory === cat
                    ? 'border-transparent bg-[#0f4a73] text-white shadow-sm'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {cat === 'all' ? 'All Schemes' : cat}
              </button>
            ))}
          </div>
        </div>

        {/* Schemes Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredSchemes.length > 0 ? (
            filteredSchemes.map((scheme) => (
              <div
                key={scheme.id}
                onClick={() => setSelectedScheme(scheme)}
                className="flex cursor-pointer flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-md"
              >
                <div>
                  <div className="mb-3.5 flex items-center justify-between gap-2">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-bold uppercase ${
                        scheme.category === 'savings'
                          ? 'border border-blue-100 bg-blue-50 text-blue-700'
                          : scheme.category === 'insurance'
                            ? 'border border-emerald-100 bg-emerald-50 text-emerald-700'
                            : scheme.category === 'pension'
                              ? 'border border-amber-100 bg-amber-50 text-amber-700'
                              : 'border border-purple-100 bg-purple-50 text-purple-700'
                      }`}
                    >
                      {scheme.category}
                    </span>
                    <span className="text-xs font-semibold text-slate-400">
                      {scheme.code.toUpperCase()}
                    </span>
                  </div>

                  <h3 className="line-clamp-2 text-lg font-bold text-slate-800">{scheme.name}</h3>
                  <p className="mt-1 text-xs font-semibold text-slate-400">{scheme.nameHindi}</p>
                  <p className="mt-3 line-clamp-1 text-sm font-medium text-slate-500 italic">
                    "{scheme.tagline}"
                  </p>
                  <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-slate-500">
                    {scheme.description}
                  </p>
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 text-sm font-bold text-[#0c538e] hover:text-[#0f4a73]">
                  <span>View Details & Eligibility</span>
                  <ArrowRight className="size-4" />
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full rounded-2xl border border-slate-200 bg-white p-12 text-center font-medium text-slate-400 shadow-sm">
              No government schemes matched your search criteria.
            </div>
          )}
        </div>

        {/* Scheme Details Modal */}
        {selectedScheme && (
          <div className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
            <div className="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl">
              {/* Modal Header */}
              <div className="sticky top-0 flex items-center justify-between gap-4 border-b border-slate-200 bg-[#0f4a73] px-6 py-5 text-white">
                <div>
                  <h3 className="text-lg font-bold md:text-xl">{selectedScheme.name}</h3>
                  <p className="mt-0.5 text-xs font-semibold text-blue-200">
                    {selectedScheme.nameHindi} · {selectedScheme.code.toUpperCase()}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedScheme(null)}
                  className="rounded-lg bg-white/10 p-1.5 text-white transition hover:bg-white/20 focus:outline-none"
                >
                  <X className="size-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="space-y-6 p-6">
                <div>
                  <h4 className="mb-2 text-xs font-bold tracking-wider text-slate-400 uppercase">
                    Description
                  </h4>
                  <p className="text-sm leading-relaxed text-slate-600">
                    {selectedScheme.description}
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  {/* Eligibility */}
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-5">
                    <h4 className="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-slate-500 uppercase">
                      <Award className="size-4 text-amber-500" />
                      Eligibility Criteria
                    </h4>
                    <ul className="space-y-2">
                      {selectedScheme.eligibility.map((item, idx) => (
                        <li key={idx} className="flex gap-2 text-xs leading-relaxed text-slate-600">
                          <Check className="mt-0.5 size-4 shrink-0 text-emerald-500" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Documents Required */}
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-5">
                    <h4 className="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-slate-500 uppercase">
                      <ShieldAlert className="size-4 text-blue-500" />
                      Documents Required
                    </h4>
                    <ul className="space-y-2">
                      {selectedScheme.documents.map((item, idx) => (
                        <li key={idx} className="flex gap-2 text-xs leading-relaxed text-slate-600">
                          <Check className="mt-0.5 size-4 shrink-0 text-[#0c538e]" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Benefits */}
                <div>
                  <h4 className="mb-3 flex items-center gap-2 text-xs font-bold tracking-wider text-slate-400 uppercase">
                    <Check className="size-4 text-emerald-500" />
                    Key Benefits & Provisions
                  </h4>
                  <ul className="space-y-2.5">
                    {selectedScheme.benefits.map((item, idx) => (
                      <li key={idx} className="flex gap-2.5 text-sm leading-relaxed text-slate-600">
                        <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-xs font-bold text-emerald-600">
                          {idx + 1}
                        </span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 flex justify-end border-t border-slate-200 bg-slate-50 px-6 py-4">
                <button
                  onClick={() => setSelectedScheme(null)}
                  className="rounded-lg border border-slate-300 bg-white px-5 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
