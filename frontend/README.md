# Frontend — Voice Agent UI

The React/Next.js frontend for the Voice Agent Starter. Built with [LiveKit Agents UI](https://livekit.io/ui) components, it provides a polished interface for real-time voice conversations with your agent.

### Features

- Real-time voice interaction with LiveKit Agents
- Camera video streaming support
- Screen sharing capabilities
- Multiple audio visualizer styles (`bar`, `grid`, `radial`, `wave`, `aura`)
- Light/dark theme switching with system preference detection
- Customizable branding, colors, and UI text via configuration

## Setup

### 1. Install dependencies

```bash
cd frontend
pnpm install
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in your LiveKit credentials (same project as the backend):

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
AGENT_NAME=my-agent
```

### 3. Run

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). Make sure your backend agent is running too.

## Customization

### Branding & UI (`app-config.ts`)

Edit [`app-config.ts`](app-config.ts) to change branding, features, and button text:

```ts
export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Murf AI',
  pageTitle: 'Voice Agent Starter',
  pageDescription: 'A voice agent powered by Murf Falcon — the fastest TTS API',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,

  logo: '/murf-logo.svg',
  accent: '#6366F1',
  logoDark: '/murf-logo-dark.svg',
  accentDark: '#818cf8',
  startButtonText: 'Start talking',

  agentName: process.env.AGENT_NAME ?? undefined,
};
```

### Audio visualizers

Set `audioVisualizerType` in [`app-config.ts`](app-config.ts):

| Type | Description | Key options |
|------|-------------|-------------|
| `bar` (default) | Vertical bars | `audioVisualizerBarCount` |
| `grid` | Dot grid | `audioVisualizerGridRowCount`, `audioVisualizerGridColumnCount` |
| `radial` | Circular bars | `audioVisualizerRadialBarCount`, `audioVisualizerRadialRadius` |
| `wave` | Oscilloscope wave | `audioVisualizerWaveLineWidth` |
| `aura` | Shader-based glow | `audioVisualizerAuraColorShift` |

Use `audioVisualizerColor` / `audioVisualizerColorDark` to set accent colors across all modes.

### Editing components

All UI components are local and fully editable:

- **`components/agents-ui/`** — Core UI: media controls, audio visualizers, chat transcript, session provider
- **`components/app/`** — App-level logic: view transitions, welcome screen, theming
- **`components/ui/`** — Primitive shadcn/ui components (button, select, tooltip, etc.)

To update Agents UI components to the latest version:

```bash
pnpm shadcn:install
```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx                # Main page
│   ├── layout.tsx              # Root layout
│   └── api/token/route.ts      # LiveKit token endpoint
├── components/
│   ├── agents-ui/              # Agents UI components (visualizers, controls, chat)
│   ├── app/                    # App components (welcome view, theme, controller)
│   ├── ai-elements/            # AI conversation elements
│   └── ui/                     # Primitive shadcn/ui components
├── hooks/                      # React hooks (audio visualizers, controls)
├── lib/                        # Utilities
├── public/                     # Static assets (logos, fonts)
├── styles/                     # Global CSS
├── app-config.ts               # Branding & feature configuration
└── package.json                # Dependencies (pnpm)
```

## Deployment

### Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend and backend don't call each other directly — they both connect to LiveKit, which handles real-time audio transport. Use the same LiveKit project credentials on both.

## Links

- [LiveKit Agents UI](https://livekit.io/ui)
- [LiveKit JavaScript SDK](https://github.com/livekit/client-sdk-js)
- [LiveKit Docs](https://docs.livekit.io)

## License

MIT — see [LICENSE](LICENSE).
