# Jan Sahay — Finance Voice Agent (Day 2)

**जन सहाय** is a bilingual voice AI companion for **financial literacy in India**. It explains government schemes (PMJDY, PMSBY, PMJJBY, APY), digital payments (UPI), and banking safety — with hard guardrails so it never asks for OTP/PIN/account numbers or promises scheme approval.

Built for **#10DaysOfAIVoiceAgents** / **#VoiceForBharat** on top of [Murf Falcon](https://murf.ai) + [LiveKit Agents](https://docs.livekit.io/agents).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming)
[![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io)
[![Branch](https://img.shields.io/badge/branch-day--2-0F6E56)](https://github.com/prataykarali/finance_voice_agent/tree/day-2)

---

## Day 2 goals

| Goal | What we shipped |
| --- | --- |
| **Personality + job** | Jan Sahay — warm financial literacy assistant (not a bank employee) |
| **Language** | Hindi ↔ English reply + Murf voice switch from STT + transcript |
| **Safety** | Never ask for OTP / PIN / account number; never promise scheme approval |
| **UX** | Live chat transcript + subtitle caption of what the agent says |
| **Smooth turns** | One greeting only; no stacked language locks; no instruction thrash |

---

## Architecture

```mermaid
flowchart LR
    A[User speaks] -->|audio| B[Deepgram Nova-3 multi]
    B -->|transcript + lang| C[Language detect]
    C -->|hi / en lock| D[Gemini LLM]
    D -->|reply text| E[Murf Falcon TTS]
    E -->|hi-IN-anisha or en-IN-anisha| F[LiveKit]
    F -->|audio + text| G[Browser UI + subtitles]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#185FA5,stroke:#85B7EB,color:#fff
    style G fill:#444441,stroke:#888780,color:#fff
```

**Pipeline:** Deepgram STT → Gemini LLM → Murf Falcon TTS, over LiveKit realtime audio.

---

## Repo layout

```
finance_voice_agent/
├── backend/
│   └── src/
│       ├── agent.py      # Voice pipeline, language switch, greeting
│       └── prompt.py     # Jan Sahay SYSTEM_PROMPT + guardrails
├── frontend/             # Next.js LiveKit Agents UI
├── start_app.sh          # Start agent + frontend (and LiveKit if installed)
└── README.md
```

---

## Quickstart

### Prerequisites

- Python **3.10+** and [**uv**](https://docs.astral.sh/uv/)
- Node.js **18+** and **pnpm**
- API keys (see below)
- Optional local [LiveKit server](https://docs.livekit.io/home/self-hosting/local/) **or** [LiveKit Cloud](https://cloud.livekit.io/)

### 1. Clone

```bash
git clone https://github.com/prataykarali/finance_voice_agent.git
cd finance_voice_agent
git checkout day-2
```

### 2. Environment

Copy examples and fill in keys:

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

| Variable | Service | Required |
| --- | --- | --- |
| `LIVEKIT_URL` | LiveKit Cloud or local `ws://127.0.0.1:7880` | Yes |
| `LIVEKIT_API_KEY` | LiveKit | Yes |
| `LIVEKIT_API_SECRET` | LiveKit | Yes |
| `MURF_API_KEY` | [murf.ai](https://murf.ai/api/dashboard) | Yes |
| `DEEPGRAM_API_KEY` | [deepgram.com](https://deepgram.com) | Yes |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | Yes |

> **Gemini free tier:** Quotas are **per model per day**. If you see `429 RESOURCE_EXHAUSTED` on one model, switch `model=` in `backend/src/agent.py` (this branch uses `gemini-flash-lite-latest`).

### 3. Install

```bash
cd backend
uv sync
uv run python src/agent.py download-files   # first time only

cd ../frontend
pnpm install
```

### 4. Run

**All-in-one** (from repo root):

```bash
chmod +x start_app.sh
./start_app.sh
```

**Or three terminals:**

```bash
# Terminal 1 — local LiveKit (optional if using Cloud)
livekit-server --dev
# or: ./livekit-server --dev

# Terminal 2 — agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — UI
cd frontend && pnpm dev
```

Open **http://localhost:3000** → **Start talking** → allow mic.

---

## Day 2 behavior (what to demo)

1. **Greeting (once):** Hindi intro as Jan Sahay  
2. **Speak English** → English reply + `en-IN-anisha` voice  
3. **Speak Hindi / Hinglish** → Hindi reply + `hi-IN-anisha` voice  
4. **Ask for OTP/PIN** → polite refusal + safety warning  
5. **Ask “guarantee scheme approval?”** → no guarantee; bank/gov decides  
6. **Subtitles:** transcript open by default; caption if chat is closed  

---

## Key files

### `backend/src/prompt.py`

System prompt: identity, objectives (schemes + digital safety), language rules, **guardrails**, first-turn-only greeting policy.

### `backend/src/agent.py`

- Loads `SYSTEM_PROMPT` from `prompt.py`
- Detects language each user turn (`on_user_turn_completed`)
- Updates instructions + Murf voice only when language **changes**
- Single ephemeral `[[LANG_LOCK]]` system message (no stacking)
- One `session.say(...)` greeting after connect

### Frontend subtitles

`frontend/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block.tsx`

- Chat/transcript **open by default**
- Always-on caption of latest agent line when chat is collapsed

---

## Configuration cheatsheet

| What | Where |
| --- | --- |
| Persona / guardrails | `backend/src/prompt.py` |
| LLM model | `google.LLM(model=...)` in `agent.py` |
| Default / Hindi voice | `VOICE_HI = "hi-IN-anisha"` |
| English voice | `VOICE_EN = "en-IN-anisha"` |
| STT | `deepgram.STT(model="nova-3", language="multi")` |
| Branding | `frontend/app-config.ts` |

Browse Murf voices: https://murf.ai/api/docs/voices-styles/voice-library  

---

## Responsible AI (non‑negotiable)

- **Never** ask for OTP, PIN, UPI PIN, password, card, Aadhaar, or account number  
- **Never** invent or share secrets  
- **Never** promise scheme / loan / claim approval  
- Escalate account-specific tracking to bank branch / official portal / helpline  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Stuck on “thinking…” | Gemini **429** free-tier quota | Switch model in `agent.py` or wait for reset / enable billing |
| Always replies in Hindi | Language lock / history | New session after latest `day-2`; speak clear English |
| Echo / fake “hello” user lines | Mic picking up agent TTS | Use headphones; keep noise cancellation on |
| No agent joins room | Agent not running or LiveKit env mismatch | Check `uv run python src/agent.py dev` logs; same LiveKit creds on FE + BE |
| Fork “1 commit behind” murf starter | Upstream `multi locale` on `agent.py` | This branch keeps Day 2 logic and already includes `language="multi"` STT |

---

## Branch

```bash
git checkout day-2
git pull origin day-2
```

- Repo: https://github.com/prataykarali/finance_voice_agent  
- Branch: https://github.com/prataykarali/finance_voice_agent/tree/day-2  

Forked from [murf-ai/murf-livekit-starter](https://github.com/murf-ai/murf-livekit-starter).

---

## License

MIT — see [LICENSE](LICENSE).

---

**Day 2 complete.** Looking forward to Day 3.

`#10DaysOfAIVoiceAgents` `#MurfFalcon` `#VoiceForBharat`
