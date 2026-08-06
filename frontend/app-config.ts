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
  companyName: 'Vyapar AI',
  pageTitle: 'Vyapar AI — Local Commerce Voice Assistant',
  pageDescription: 'Your friendly local voice AI assistant to discover products, check prices, and shop from nearby merchants instantly.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: false,

  logo: '/vyapar-logo.svg',
  accent: '#8B5CF6',
  logoDark: '/vyapar-logo-dark.svg',
  accentDark: '#A78BFA',
  startButtonText: 'Talk to Vyapar AI',

  // optional: audio visualization configuration
  audioVisualizerType: 'wave',
  audioVisualizerColor: '#8B5CF6',
  audioVisualizerColorDark: '#A78BFA',
  audioVisualizerColorShift: 0.4,
  audioVisualizerBarCount: 5,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
