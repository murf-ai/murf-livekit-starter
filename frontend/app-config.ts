// Configured for Murf LiveKit Starter
export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  // BharatPay — Pooja Voice Support Agent (#VoiceForBharat)
  companyName: 'BharatPay',
  pageTitle: 'Pooja — BharatPay Voice Support',
  pageDescription: 'Talk to Pooja, your BharatPay AI support agent — UPI, payments, loans, and more, powered by Murf Falcon TTS.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/murf-logo.svg',
  accent: '#15803d',         // Deep trust green — finance and payments
  logoDark: '/murf-logo-dark.svg',
  accentDark: '#4ade80',     // Lighter green for dark mode
  startButtonText: 'Talk to Pooja',

  // Aura visualizer — alive and conversational
  audioVisualizerType: 'aura',
  audioVisualizerColor: '#15803d',
  audioVisualizerColorDark: '#4ade80',

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
