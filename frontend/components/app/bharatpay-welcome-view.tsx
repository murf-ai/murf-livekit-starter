'use client';

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Shield, Mic, Zap, CreditCard, TrendingUp, PhoneCall, Lock } from 'lucide-react';
import { MicPermissionError } from './mic-permission-error';

interface BharatPayWelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

const features = [
  { icon: CreditCard, label: 'UPI & Payments', color: '#4f46e5' },
  { icon: TrendingUp, label: 'Loans & Lending', color: '#0891b2' },
  { icon: Shield, label: 'Account & KYC', color: '#059669' },
  { icon: Zap, label: 'Instant Support', color: '#d97706' },
];

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
    <div className="bp-welcome-root">
      {/* Animated background blobs */}
      <div className="bp-bg-blob bp-blob-1" />
      <div className="bp-bg-blob bp-blob-2" />
      <div className="bp-bg-blob bp-blob-3" />

      <div className="bp-welcome-content">
        {/* Top badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bp-top-badge"
        >
          <span className="bp-badge-dot" />
          <span>Powered by Murf Falcon TTS · 24/7 Support</span>
        </motion.div>

        {/* Logo & Brand */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="bp-logo-area"
        >
          {/* Logo mark — B icon in brand colors */}
          <div className="bp-logo-mark">
            <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="52" height="52" rx="16" fill="url(#bpGradient)" />
              <path d="M14 12h14c4.418 0 8 3.582 8 8 0 2.21-.895 4.21-2.344 5.656A7.972 7.972 0 0 1 36 32c0 4.418-3.582 8-8 8H14V12zm6 6v6h8a3 3 0 0 0 0-6H20zm0 12v6h8a3 3 0 0 0 0-6H20z" fill="white" />
              <defs>
                <linearGradient id="bpGradient" x1="0" y1="0" x2="52" y2="52" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#1a237e" />
                  <stop offset="1" stopColor="#283593" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="bp-brand-text">
            <h1 className="bp-brand-name">BharatPay</h1>
            <span className="bp-brand-tagline">Voice Support</span>
          </div>
        </motion.div>

        {/* Agent card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bp-agent-card"
        >
          <div className="bp-agent-avatar-ring">
            <div className="bp-agent-avatar">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="24" cy="18" r="9" fill="#fbbf24" />
                <path d="M6 42c0-9.941 8.059-18 18-18s18 8.059 18 18" fill="#f59e0b" />
              </svg>
            </div>
            <div className="bp-agent-status-dot" />
          </div>
          <div className="bp-agent-info">
            <h2 className="bp-agent-name">Pooja</h2>
            <p className="bp-agent-role">AI Support Agent · BharatPay</p>
          </div>
          <div className="bp-agent-langs">
            <span className="bp-lang-pill">Hindi</span>
            <span className="bp-lang-pill">English</span>
            <span className="bp-lang-pill">Hinglish</span>
          </div>
        </motion.div>

        {/* Hero text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="bp-hero-text"
        >
          <p className="bp-hero-headline">
            Get instant help with your payments, loans &amp; account — in <span className="bp-highlight">your language</span>
          </p>
        </motion.div>

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="bp-features-grid"
        >
          {features.map(({ icon: Icon, label, color }) => (
            <div key={label} className="bp-feature-chip">
              <Icon size={14} style={{ color }} />
              <span>{label}</span>
            </div>
          ))}
        </motion.div>

        {/* CTA Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="bp-cta-wrapper"
        >
          <button
            id="start-call-btn"
            onClick={handleStartCall}
            className="bp-cta-button"
          >
            <div className="bp-cta-icon-wrap">
              <PhoneCall size={20} />
            </div>
            <span>{startButtonText}</span>
          </button>
          <p className="bp-cta-hint">
            <Lock size={11} />
            <span>Mic required · No OTP or PIN ever asked on this call</span>
          </p>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="bp-footer"
        >
          <span>RBI Compliant</span>
          <span className="bp-footer-dot">·</span>
          <span>256-bit Encrypted</span>
          <span className="bp-footer-dot">·</span>
          <span>#VoiceForBharat</span>
        </motion.div>
      </div>
    </div>
  );
}
