// Configured for Murf LiveKit Starter
export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  welcomeTitle?: string;
  welcomeSubtitle?: string;
  welcomeDescription?: string;

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
  companyName: 'BharatPay Support',
  pageTitle: 'Pooja — BharatPay Voice Support',
  pageDescription: 'Talk to Pooja, your BharatPay AI support agent — UPI, payments, loans, and more. #VoiceForBharat',

  welcomeTitle: 'BharatPay Support',
  welcomeSubtitle: 'POOJA: AI FINANCIAL VOICE ASSISTANT',
  welcomeDescription: 'Get instant voice help with bank accounts, UPI payments, credit cards, or fraud safety in Hindi, English, and Hinglish.',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/bharatpay-logo.png',
  accent: '#7C3AED',         // Premium purple
  logoDark: '/bharatpay-logo.png',
  accentDark: '#8B5CF6',     // Violet glow
  startButtonText: 'Talk to Pooja',

  // Radial audio visualizer with violet glow
  audioVisualizerType: 'radial',
  audioVisualizerColor: '#7C3AED',
  audioVisualizerColorDark: '#8B5CF6',
  audioVisualizerColorShift: 0.3,
  audioVisualizerBarCount: 5,
  audioVisualizerRadialBarCount: 36,
  audioVisualizerRadialRadius: 110,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
