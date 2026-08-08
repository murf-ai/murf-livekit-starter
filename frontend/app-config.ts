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

  agentName?: string;
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Raksha System',
  pageTitle: 'Raksha: Disaster Response Triage',
  pageDescription: 'State your emergency, location, and immediate needs. Raksha will guide you in real-time.',

  supportsChatInput: true,
  supportsVideoInput: false, 
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/murf-logo.svg',
  accent: '#ef4444', 
  logoDark: '/murf-logo-dark.svg',
  accentDark: '#f87171', 
  startButtonText: 'TAP TO REPORT EMERGENCY',

  audioVisualizerType: 'bar',
  audioVisualizerColor: '#ef4444',
  audioVisualizerColorDark: '#f87171',
  audioVisualizerColorShift: 0.1,
  audioVisualizerBarCount: 5,

  agentName: process.env.AGENT_NAME ?? undefined,
  sandboxId: undefined,
};