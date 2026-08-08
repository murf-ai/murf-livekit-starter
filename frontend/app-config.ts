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
  companyName: 'Jan Sahay • Digital Financial Assistant',
  pageTitle: 'Jan Sahay (जन सहाय) — Voice Financial Literacy Guide',
  pageDescription:
    'Your trusted AI assistant for Indian government financial schemes (PMJDY, PMSBY, APY) and safe digital banking in Hindi & English.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/finance_avatar/finance.jpeg',
  accent: '#10B981',
  logoDark: '/finance_avatar/finance.jpeg',
  accentDark: '#34D399',
  startButtonText: 'Start conversation',

  audioVisualizerType: 'aura',
  audioVisualizerColor: '#10B981',
  audioVisualizerColorDark: '#34D399',
  audioVisualizerColorShift: 0.3,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
