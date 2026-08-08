'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Loader2, Mic, Volume2, PhoneOff, RotateCcw } from 'lucide-react';
import type { AgentState } from '@livekit/components-react';

// Map LiveKit agent state → friendly label + visual hint
type UIAgentState = 'connecting' | 'idle' | 'listening' | 'thinking' | 'speaking' | 'disconnected';

function mapAgentState(agentState: AgentState | undefined, isConnected: boolean): UIAgentState {
  if (!isConnected) return 'connecting';
  switch (agentState) {
    case 'listening':
      return 'listening';
    case 'thinking':
      return 'thinking';
    case 'speaking':
      return 'speaking';
    case 'disconnected':
      return 'disconnected';
    default:
      return 'idle';
  }
}

const STATE_CONFIG: Record<UIAgentState, { label: string; sublabel: string; color: string; bgColor: string }> = {
  connecting: {
    label: 'Connecting…',
    sublabel: 'Please wait while we connect you to Pooja',
    color: '#d97706',
    bgColor: 'rgba(217,119,6,0.12)',
  },
  idle: {
    label: 'Ready',
    sublabel: 'Speak to begin the conversation',
    color: '#6366f1',
    bgColor: 'rgba(99,102,241,0.12)',
  },
  listening: {
    label: 'Listening…',
    sublabel: 'Pooja is hearing you',
    color: '#059669',
    bgColor: 'rgba(5,150,105,0.12)',
  },
  thinking: {
    label: 'Thinking…',
    sublabel: 'Pooja is processing your question',
    color: '#0891b2',
    bgColor: 'rgba(8,145,178,0.12)',
  },
  speaking: {
    label: 'Pooja is speaking',
    sublabel: 'Agent is responding to you',
    color: '#7c3aed',
    bgColor: 'rgba(124,58,237,0.12)',
  },
  disconnected: {
    label: 'Call Ended',
    sublabel: 'Your session with Pooja has ended',
    color: '#dc2626',
    bgColor: 'rgba(220,38,38,0.12)',
  },
};

interface BharatPayStateIndicatorProps {
  agentState: AgentState | undefined;
  isConnected: boolean;
}

export function BharatPayStateIndicator({ agentState, isConnected }: BharatPayStateIndicatorProps) {
  const uiState = mapAgentState(agentState, isConnected);
  const config = STATE_CONFIG[uiState];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={uiState}
        initial={{ opacity: 0, y: 6, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -6, scale: 0.96 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="bp-state-indicator"
        style={{ backgroundColor: config.bgColor }}
      >
        {/* Status icon */}
        <div className="bp-state-icon" style={{ color: config.color }}>
          {uiState === 'connecting' && <Loader2 size={16} className="bp-spin" />}
          {uiState === 'idle' && <div className="bp-state-dot" style={{ background: config.color }} />}
          {uiState === 'listening' && <Mic size={16} />}
          {uiState === 'thinking' && <Loader2 size={16} className="bp-spin" />}
          {uiState === 'speaking' && <Volume2 size={16} />}
          {uiState === 'disconnected' && <PhoneOff size={16} />}
        </div>

        {/* Text */}
        <div className="bp-state-text">
          <span className="bp-state-label" style={{ color: config.color }}>{config.label}</span>
          <span className="bp-state-sublabel">{config.sublabel}</span>
        </div>

        {/* Listening pulse ring */}
        {uiState === 'listening' && (
          <div className="bp-listening-pulse" style={{ borderColor: config.color }} />
        )}

        {/* Speaking waveform bars */}
        {uiState === 'speaking' && (
          <div className="bp-speaking-bars">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bp-speaking-bar"
                style={{
                  background: config.color,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

interface BharatPayCallEndedViewProps {
  onRestart: () => void;
}

export function BharatPayCallEndedView({ onRestart }: BharatPayCallEndedViewProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0 }}
      className="bp-call-ended-overlay"
    >
      <div className="bp-call-ended-card">
        <div className="bp-call-ended-icon">
          <PhoneOff size={28} />
        </div>
        <h3 className="bp-call-ended-title">Call Ended</h3>
        <p className="bp-call-ended-subtitle">
          Thank you for calling BharatPay Support. We hope Pooja was helpful!
        </p>
        <p className="bp-call-ended-tagline">
          <em>Koi aur sawaal ho toh please call karein. BharatPay mein aapka swagat hai.</em>
        </p>
        <button
          id="restart-call-btn"
          onClick={onRestart}
          className="bp-restart-btn"
        >
          <RotateCcw size={16} />
          <span>Start New Call</span>
        </button>
      </div>
    </motion.div>
  );
}
