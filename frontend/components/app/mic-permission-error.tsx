'use client';

import React from 'react';
import { motion } from 'motion/react';
import { MicOff, RefreshCcw, Chrome, Globe } from 'lucide-react';

interface MicPermissionErrorProps {
  onRetry: () => void;
}

export function MicPermissionError({ onRetry }: MicPermissionErrorProps) {
  return (
    <div className="bp-welcome-root">
      <div className="bp-bg-blob bp-blob-1" />
      <div className="bp-bg-blob bp-blob-2" />

      <div className="bp-welcome-content">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="bp-mic-error-card"
        >
          {/* Error icon */}
          <div className="bp-mic-error-icon">
            <MicOff size={32} strokeWidth={1.5} />
          </div>

          <h2 className="bp-mic-error-title">Microphone Access Blocked</h2>
          <p className="bp-mic-error-subtitle">
            Pooja needs your microphone to hear you. Please allow microphone access to start the call.
          </p>

          {/* Step-by-step fix */}
          <div className="bp-mic-steps">
            <p className="bp-mic-steps-heading">How to enable your microphone:</p>

            <div className="bp-mic-step">
              <div className="bp-mic-step-num">1</div>
              <div className="bp-mic-step-content">
                <div className="bp-mic-step-icon"><Globe size={14} /></div>
                <span>Click the <strong>🔒 lock icon</strong> or <strong>ⓘ info icon</strong> in your browser's address bar</span>
              </div>
            </div>

            <div className="bp-mic-step">
              <div className="bp-mic-step-num">2</div>
              <div className="bp-mic-step-content">
                <div className="bp-mic-step-icon"><Chrome size={14} /></div>
                <span>Find <strong>Microphone</strong> in the permissions list and set it to <strong>Allow</strong></span>
              </div>
            </div>

            <div className="bp-mic-step">
              <div className="bp-mic-step-num">3</div>
              <div className="bp-mic-step-content">
                <div className="bp-mic-step-icon"><RefreshCcw size={14} /></div>
                <span>Reload the page or click <strong>Try Again</strong> below</span>
              </div>
            </div>
          </div>

          {/* Retry button */}
          <button
            id="retry-mic-btn"
            onClick={onRetry}
            className="bp-mic-retry-btn"
          >
            <RefreshCcw size={16} />
            <span>Try Again</span>
          </button>

          <p className="bp-mic-privacy-note">
            🔒 Your voice data is processed securely and never stored permanently.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
