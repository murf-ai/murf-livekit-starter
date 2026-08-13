'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { ConnectingView } from '@/components/app/connecting-view';
import { CallEndedView, type CallSummary } from '@/components/app/call-ended-view';
import { ParticleSwarmCanvas, type AgentUIState } from '@/components/app/particle-swarm-canvas';
import { MicPermissionModal } from '@/components/app/mic-permission-modal';
import { useMicPermissions } from '@/hooks/useMicPermissions';

import { DashboardView } from './dashboard-view';
import { SchemesView } from './schemes-view';
import { FraudView } from './fraud-view';
import { ComplaintView } from './complaint-view';
import { EscalationsView } from './escalations-view';

function sanitizeQuery(text: string): string {
  return text
    .replace(/\b(?:otp|pin|password|cvv)\b[:\s=]*\S+/gi, '[redacted]')
    .replace(/\b\d{4,18}\b/g, '[redacted]')
    .trim()
    .slice(0, 160);
}

const MotionWelcomeView = motion.create(WelcomeView);
const MotionConnectingView = motion.create(ConnectingView);
const MotionSessionView = motion.create(AgentSessionView_01);
const MotionCallEndedView = motion.create(CallEndedView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.4, ease: 'easeInOut' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const { isConnected, start, end } = session;
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { resolvedTheme } = useTheme();

  const [activeTab, setActiveTab] = useState<string>('CALL_DASHBOARD');
  const [isConnectingManual, setIsConnectingManual] = useState(false);
  const [hasStartedOnce, setHasStartedOnce] = useState(false);
  const [isCallEnded, setIsCallEnded] = useState(false);
  const [showMicModal, setShowMicModal] = useState(false);
  const [callSummary, setCallSummary] = useState<CallSummary | undefined>();

  const { permissionState, requestMic } = useMicPermissions();

  const snapshotQueries = () =>
    messages
      .filter((message) => message.from?.isLocal === true)
      .map((message) => sanitizeQuery(message.message ?? ''))
      .filter(Boolean)
      .slice(-8);

  useEffect(() => {
    if (isConnected) {
      setHasStartedOnce(true);
      setIsCallEnded(false);
      setIsConnectingManual(false);
    }
  }, [isConnected]);

  const handleDisconnect = async () => {
    setCallSummary({
      connected: true,
      outcome: 'success',
      reason: 'Thanks for talking with Jan Sahay. Start again anytime.',
      queries: snapshotQueries(),
    });
    setHasStartedOnce(true);
    setIsConnectingManual(false);
    setIsCallEnded(true);
    try {
      await end();
    } catch (err) {
      console.warn('Error ending session:', err);
    }
  };

  const handleCancelConnecting = async () => {
    setCallSummary({
      connected: false,
      outcome: 'failed',
      reason: 'The call was cancelled before connecting.',
      queries: snapshotQueries(),
    });
    setHasStartedOnce(true);
    setIsConnectingManual(false);
    setIsCallEnded(true);
    try {
      await fetch('/api/calls', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'cancelled_before_connect',
          channel: 'browser',
        }),
      });
    } catch (err) {
      console.warn('Could not record cancelled call:', err);
    }
    try {
      await end();
    } catch (err) {
      console.warn('Error ending session:', err);
    }
  };

  const handleStartCall = async () => {
    setIsCallEnded(false);
    if (permissionState === 'denied') {
      setShowMicModal(true);
      return;
    }
    const granted = await requestMic();
    if (!granted) {
      setShowMicModal(true);
      return;
    }
    setIsConnectingManual(true);
    try {
      if (isConnected) {
        await end();
      }
      await start();
    } catch (err) {
      console.error('Failed to start session:', err);
      await handleCancelConnecting();
    }
  };

  const isConnecting = isConnectingManual || agentState === 'connecting' || agentState === 'initializing';

  let uiState: AgentUIState = 'ready';
  if (isCallEnded && hasStartedOnce) {
    uiState = 'ended';
  } else if (isConnecting && !isConnected) {
    uiState = 'connecting';
  } else if (isConnected) {
    switch (agentState) {
      case 'speaking':
        uiState = 'speaking';
        break;
      case 'thinking':
        uiState = 'thinking';
        break;
      case 'listening':
        uiState = 'listening';
        break;
      case 'connecting':
      case 'initializing':
        uiState = 'connecting';
        break;
      default:
        uiState = 'listening';
    }
  } else {
    uiState = 'ready';
  }

  const isHome = activeTab === 'HOME';

  return (
    <div className={`relative min-h-screen w-full flex flex-col font-sans select-none ${
      isHome ? 'bg-slate-950 text-slate-100 overflow-hidden' : 'bg-[#f8fafc] text-slate-800'
    }`}>
      {/* Navigation Header */}
      <header className="h-16 bg-[#0b4d7e] text-white flex items-center justify-between px-6 shadow-md z-40 shrink-0 select-none">
        {/* Left: Logo & Branding */}
        <div className="flex items-center gap-3">
          <img 
            src="/finance_avatar/finance.jpeg" 
            alt="Jan Sahay Logo" 
            className="size-8 rounded-full border border-blue-200/40 object-cover"
          />
          <span className="font-extrabold text-base md:text-lg tracking-wide">
            Jan Sahay <span className="text-xs text-blue-200 font-bold hidden sm:inline ml-1.5">| जन सहाय</span>
          </span>
        </div>

        {/* Center: Tabs */}
        <nav className="hidden lg:flex items-stretch h-full">
          {([
            { id: 'HOME', label: 'Home' },
            { id: 'SCHEMES_SEARCH', label: 'Schemes Search' },
            { id: 'FRAUD_PREVENTION', label: 'Fraud Prevention' },
            { id: 'COMPLAINT_HELPLINE', label: 'Complaint Helpline' },
            { id: 'OPEN_ESCALATIONS', label: 'Open Escalations' },
            { id: 'CALL_DASHBOARD', label: 'Call Dashboard' }
          ] as const).map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 flex items-center text-xs md:text-sm font-bold uppercase tracking-wider transition ${
                  isActive 
                    ? 'bg-[#052e4b] border-b-4 border-b-amber-400 text-white' 
                    : 'text-blue-100 hover:bg-white/5 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Right: Call Status Badge */}
        <div className="flex items-center gap-3">
          {/* Mobile Menu Trigger */}
          <div className="lg:hidden">
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value)}
              className="bg-[#052e4b] text-white border border-blue-300/25 rounded-lg px-2.5 py-1.5 text-xs font-bold font-sans uppercase focus:outline-none"
            >
              <option value="HOME">Home</option>
              <option value="SCHEMES_SEARCH">Schemes Search</option>
              <option value="FRAUD_PREVENTION">Fraud Prevention</option>
              <option value="COMPLAINT_HELPLINE">Complaint Helpline</option>
              <option value="OPEN_ESCALATIONS">Open Escalations</option>
              <option value="CALL_DASHBOARD">Call Dashboard</option>
            </select>
          </div>

          {(isConnected || isConnecting) && (
            <button
              onClick={() => setActiveTab('HOME')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500 hover:bg-rose-600 text-white text-[10px] md:text-xs font-bold shadow-sm animate-pulse transition"
            >
              <span className="size-2 rounded-full bg-white block" />
              <span>LIVE CALL</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 relative flex flex-col min-h-0">
        {isHome ? (
          <>
            {/* 3D Three.js Particle Swarm Background Canvas */}
            <ParticleSwarmCanvas agentState={uiState} />

            <div className="flex-1 flex flex-col justify-center items-center relative z-10 w-full">
              <AnimatePresence mode="wait">
                {/* State 1: Ready */}
                {uiState === 'ready' && (
                  <MotionWelcomeView
                    key="welcome"
                    {...VIEW_MOTION_PROPS}
                    startButtonText={appConfig.startButtonText}
                    onStartCall={handleStartCall}
                  />
                )}

                {/* State 2: Connecting */}
                {uiState === 'connecting' && (
                  <MotionConnectingView
                    key="connecting"
                    {...VIEW_MOTION_PROPS}
                    onCancel={handleCancelConnecting}
                  />
                )}

                {/* Active call: listening / thinking / speaking */}
                {(uiState === 'listening' ||
                  uiState === 'thinking' ||
                  uiState === 'speaking') && (
                  <MotionSessionView
                    key="session-view"
                    {...VIEW_MOTION_PROPS}
                    supportsChatInput={appConfig.supportsChatInput}
                    supportsVideoInput={appConfig.supportsVideoInput}
                    supportsScreenShare={appConfig.supportsScreenShare}
                    isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
                    audioVisualizerType={appConfig.audioVisualizerType}
                    audioVisualizerColor={
                      resolvedTheme === 'dark'
                        ? appConfig.audioVisualizerColorDark
                        : appConfig.audioVisualizerColor
                    }
                    audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
                    audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
                    audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
                    audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
                    audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
                    audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
                    audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
                    onDisconnect={handleDisconnect}
                    className="fixed inset-x-0 bottom-0 top-16"
                  />
                )}

                {/* State 5: Call Ended */}
                {uiState === 'ended' && (
                  <MotionCallEndedView
                    key="call-ended"
                    {...VIEW_MOTION_PROPS}
                    onStartAgain={handleStartCall}
                    summary={callSummary}
                  />
                )}
              </AnimatePresence>
            </div>
          </>
        ) : (
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'CALL_DASHBOARD' && (
              <DashboardView 
                isCallActive={isConnected} 
                onStartCall={handleStartCall} 
                onEndCall={handleDisconnect}
                onSwitchToTab={setActiveTab}
              />
            )}
            {activeTab === 'SCHEMES_SEARCH' && <SchemesView />}
            {activeTab === 'FRAUD_PREVENTION' && <FraudView />}
            {activeTab === 'COMPLAINT_HELPLINE' && <ComplaintView />}
            {activeTab === 'OPEN_ESCALATIONS' && <EscalationsView />}
          </div>
        )}
      </div>

      {/* Step 4: Microphone Permission Error Handling Modal */}
      <MicPermissionModal
        isOpen={showMicModal}
        onRetry={async () => {
          const granted = await requestMic();
          if (granted) {
            setShowMicModal(false);
            start();
          }
        }}
        onClose={() => setShowMicModal(false)}
      />
    </div>
  );
}
