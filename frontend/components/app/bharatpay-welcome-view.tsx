'use client';

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Shield, Mic, CreditCard, TrendingUp, PhoneCall, Lock, Landmark } from 'lucide-react';
import { MicPermissionError } from './mic-permission-error';
import { CardSpotlight } from '@/components/ui/card-spotlight';
import { Button } from '@/components/ui/button';

interface BharatPayWelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export function BharatPayWelcomeView({ startButtonText, onStartCall }: BharatPayWelcomeViewProps) {
  const [micError, setMicError] = useState(false);

  const handleStartCall = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicError(false);
      onStartCall();
    } catch {
      setMicError(true);
    }
  };

  if (micError) {
    return <MicPermissionError onRetry={() => setMicError(false)} />;
  }

  return (
    <div className="relative flex h-full w-full flex-col items-center justify-between overflow-x-hidden overflow-y-auto bg-[#030303] px-6 py-8 md:py-12">
      {/* Background Depth - Glow and Vignettes */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {/* Radial Purple Glow behind Hero */}
        <div className="absolute top-0 left-1/2 h-[350px] w-[700px] -translate-x-1/2 rounded-full bg-purple-600/[0.025] blur-[90px]" />
        {/* Faint Indigo Glow */}
        <div className="absolute top-[25%] left-[20%] h-[250px] w-[450px] rounded-full bg-indigo-500/[0.012] blur-[90px]" />
      </div>

      {/* Content Center Wrapper */}
      <div className="relative z-10 my-auto flex w-full max-w-2xl flex-col items-center py-6 text-center">
        {/* Top badge */}
        <motion.div
          initial={{ opacity: 0, y: -15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 flex items-center gap-2 rounded-full border border-white/[0.04] bg-white/[0.02] px-4 py-1 text-[10px] font-medium tracking-wider text-[#92929a] uppercase shadow-sm select-none"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-[#8b5cf6] animate-pulse" />
          <span>Powered by Murf Falcon TTS · 24/7 Support</span>
        </motion.div>

        {/* Logo & Brand */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="flex flex-col items-center gap-3 mb-6"
        >
          <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7c3aed] to-[#4f46e5] shadow-lg shadow-purple-500/10">
            <svg width="34" height="34" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 12h14c4.418 0 8 3.582 8 8 0 2.21-.895 4.21-2.344 5.656A7.972 7.972 0 0 1 36 32c0 4.418-3.582 8-8 8H14V12zm6 6v6h8a3 3 0 0 0 0-6H20zm0 12v6h8a3 3 0 0 0 0-6H20z" fill="white" />
            </svg>
          </div>
          <div>
            <h1 className="font-sans text-2xl font-bold tracking-tight text-[#f5f5f5] md:text-3xl uppercase">
              BHARATPAY SUPPORT
            </h1>
            <p className="mt-1 bg-gradient-to-r from-[#c4a7ff] via-[#f0c8ff] to-[#8b5cf6] bg-clip-text text-[10px] font-semibold tracking-[0.2em] text-transparent uppercase">
              Pooja: AI Financial Voice Assistant
            </p>
          </div>
        </motion.div>

        {/* Hero Supporting Description */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-lg px-2 text-xs leading-relaxed text-[#92929a] md:text-sm"
        >
          Get instant, secure voice guidance with bank accounts, UPI payments, credit cards, or fraud safety in Hindi, English, and Hinglish.
        </motion.p>

        {/* Subtle premium divider */}
        <div className="relative my-6 flex w-full max-w-xs items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-white/5 to-transparent" />
          </div>
          <div className="relative size-1 rounded-full bg-[#8b5cf6] shadow-[0_0_6px_#8b5cf6]" />
        </div>

        {/* Capability Header */}
        <div className="mb-4 flex flex-col items-center select-none">
          <span className="text-[9px] font-semibold tracking-[0.25em] text-[#8b5cf6] uppercase">
            Financial Intelligence
          </span>
          <h2 className="mt-1 text-base font-medium tracking-wide text-[#f5f5f5]">
            What can Pooja help with?
          </h2>
        </div>

        {/* Cards Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="grid w-full gap-3 text-left sm:grid-cols-2"
        >
          {/* Card 1 */}
          <CardSpotlight className="relative flex h-28 flex-col justify-center overflow-hidden rounded-2xl border border-white/[0.04] bg-[#0b0b0b]/60 p-5 transition-all duration-300 hover:border-purple-500/20">
            {/* Micro details: Line graph motif */}
            <svg
              className="pointer-events-none absolute right-2 bottom-2 size-12 text-[#8b5cf6]/[0.02]"
              viewBox="0 0 40 40"
              fill="none"
            >
              <path
                d="M5 32 L12 22 L20 27 L28 12 L35 17"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            <div>
              <div className="flex items-center gap-2 text-[#c4a7ff] transition-colors group-hover:text-[#f0c8ff]">
                <CreditCard className="size-4 shrink-0" />
                <h3 className="font-sans text-[10px] font-semibold tracking-wider uppercase">
                  UPI & Payments
                </h3>
              </div>
              <p className="mt-2 pr-4 text-[11px] leading-relaxed text-[#92929a]">
                Get guidance on bank transfers, UPI PIN setup, failed payments, and transaction history.
              </p>
            </div>
          </CardSpotlight>

          {/* Card 2 */}
          <CardSpotlight className="relative flex h-28 flex-col justify-center overflow-hidden rounded-2xl border border-white/[0.04] bg-[#0b0b0b]/60 p-5 transition-all duration-300 hover:border-purple-500/20">
            {/* Micro details: Dot grid */}
            <div className="pointer-events-none absolute top-2 right-2 grid grid-cols-4 gap-0.5 opacity-[0.04]">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="size-0.5 rounded-full bg-[#c4a7ff]" />
              ))}
            </div>

            <div>
              <div className="flex items-center gap-2 text-[#c4a7ff] transition-colors group-hover:text-[#f0c8ff]">
                <TrendingUp className="size-4 shrink-0" />
                <h3 className="font-sans text-[10px] font-semibold tracking-wider uppercase">
                  Loans & Credit
                </h3>
              </div>
              <p className="mt-2 pr-4 text-[11px] leading-relaxed text-[#92929a]">
                Understand merchant loans, credit eligibility, interest rates, and EMI repayment plans.
              </p>
            </div>
          </CardSpotlight>

          {/* Card 3 */}
          <CardSpotlight className="relative flex h-28 flex-col justify-center overflow-hidden rounded-2xl border border-white/[0.04] bg-[#0b0b0b]/60 p-5 transition-all duration-300 hover:border-purple-500/20">
            {/* Micro details: Faint ₹ symbol */}
            <span className="pointer-events-none absolute right-3 bottom-1 font-serif text-3xl font-semibold text-[#f0c8ff]/[0.02] select-none">
              ₹
            </span>

            <div>
              <div className="flex items-center gap-2 text-[#c4a7ff] transition-colors group-hover:text-[#f0c8ff]">
                <Landmark className="size-4 shrink-0" />
                <h3 className="font-sans text-[10px] font-semibold tracking-wider uppercase">
                  Accounts & KYC
                </h3>
              </div>
              <p className="mt-2 pr-4 text-[11px] leading-relaxed text-[#92929a]">
                Complete your KYC, verify business documents, or manage bank accounts linked to BharatPay.
              </p>
            </div>
          </CardSpotlight>

          {/* Card 4 */}
          <CardSpotlight className="relative flex h-28 flex-col justify-center overflow-hidden rounded-2xl border border-white/[0.04] bg-[#0b0b0b]/60 p-5 transition-all duration-300 hover:border-purple-500/20">
            {/* Micro details: Faint compass/shield signal */}
            <svg
              className="pointer-events-none absolute right-2 bottom-2 size-10 text-[#8b5cf6]/[0.02]"
              viewBox="0 0 40 40"
              fill="none"
            >
              <circle cx="20" cy="20" r="11" stroke="currentColor" strokeWidth="1.5" />
              <path d="M20 14 V26 M14 20 H26" stroke="currentColor" strokeWidth="1.5" />
            </svg>

            <div>
              <div className="flex items-center gap-2 text-[#c4a7ff] transition-colors group-hover:text-[#f0c8ff]">
                <Shield className="size-4 shrink-0" />
                <h3 className="font-sans text-[10px] font-semibold tracking-wider uppercase">
                  Safety & Security
                </h3>
              </div>
              <p className="mt-2 pr-4 text-[11px] leading-relaxed text-[#92929a]">
                Learn to identify digital scams, report unrecognized transactions, and secure your wallet.
              </p>
            </div>
          </CardSpotlight>
        </motion.div>

        {/* Language selector indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-6 flex flex-col items-center gap-2 select-none"
        >
          <span className="text-[9px] font-semibold tracking-[0.2em] text-[#92929a] uppercase">
            Supported Languages
          </span>
          <div className="flex items-center gap-4 rounded-full border border-white/[0.04] bg-white/[0.01] px-5 py-1.5 shadow-[0_2px_8px_rgba(0,0,0,0.25)]">
            <span className="text-[11px] font-medium tracking-wide text-[#f5f5f5]">English</span>
            <span className="h-1 w-1 rounded-full bg-[#8b5cf6]" />
            <span className="text-[11px] font-medium tracking-wide text-[#f5f5f5]">Hindi</span>
            <span className="h-1 w-1 rounded-full bg-[#8b5cf6]" />
            <span className="text-[11px] font-medium tracking-wide text-[#f5f5f5]">Hinglish</span>
          </div>
        </motion.div>

        {/* CTA (Start Call Button) */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-8 flex flex-col items-center gap-2.5"
        >
          <Button
            id="start-call-btn"
            size="lg"
            onClick={handleStartCall}
            className="group relative cursor-pointer overflow-hidden rounded-full border border-purple-400/20 bg-gradient-to-b from-[#8b5cf6] to-[#6d3fd9] px-8 py-6 font-sans text-xs font-semibold tracking-wider text-white shadow-[0_4px_12px_rgba(109,63,217,0.15)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_0_20px_rgba(139,92,246,0.3)]"
          >
            {/* Hover highlight overlay */}
            <span className="pointer-events-none absolute inset-0 bg-white/[0.04] opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            <span className="relative z-10 flex items-center gap-2">
              <PhoneCall className="size-3.5 text-[#f0c8ff] transition-transform duration-300 group-hover:scale-110" />
              {startButtonText.toUpperCase()}
            </span>
          </Button>
          <span className="flex items-center gap-1.5 text-[10px] tracking-wide text-[#92929a] select-none">
            <Lock size={11} className="text-[#8b5cf6]" />
            <span>Mic required · No OTP or PIN ever asked on this call</span>
          </span>
        </motion.div>

        {/* Product Statement / Subtle Footer */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-10 flex w-full flex-col items-center gap-1 text-center select-none"
        >
          <div className="flex items-center gap-2 text-[10px] font-medium tracking-wide text-[#92929a]">
            <span>RBI Compliant</span>
            <span className="h-0.5 w-0.5 bg-[#92929a]/40 rounded-full" />
            <span>256-bit Encrypted</span>
            <span className="h-0.5 w-0.5 bg-[#92929a]/40 rounded-full" />
            <span>#VoiceForBharat</span>
          </div>
          <p className="max-w-sm px-4 text-[9px] text-[#92929a]/40 mt-1">
            Always verify important financial actions through the official BharatPay app.
          </p>
        </motion.footer>
      </div>
    </div>
  );
}
