# Suraksha Saathi - Telugu UPI Fraud Awareness Agent

Day 1 build for Murf AI's **10 Days of Voice Agents - #VoiceForBharat
Edition**.

Suraksha Saathi is a Telugu-first voice agent for the **Financial Services**
track. It helps first-time digital payment users understand UPI fraud risk,
avoid unsafe requests for OTP or UPI PIN, and report suspected fraud quickly.

## Why This Matters

UPI has made payments simple, but scam calls, fake collect requests, and OTP
traps move faster than many text-heavy safety campaigns. A spoken Telugu helper
can reach people who are more comfortable explaining a stressful payment issue
by voice than reading an English warning screen.

## Day 1 Build

- Track: Financial Services.
- Agent name: `suraksha-saathi`.
- Main language: Telugu.
- Murf Falcon voice: `Samar`.
- Murf locale: `te-IN`.
- Transport/runtime: LiveKit Agents starter with Deepgram STT, OpenAI GPT LLM, and
  Murf Falcon TTS.
- Frontend: Next.js voice session UI branded for Suraksha Saathi.

See [CHALLENGE_DAY1.md](./CHALLENGE_DAY1.md) for the demo script, voice choice,
setup notes, and known limits.

## Architecture

```mermaid
flowchart LR
    A[User speaks Telugu or code mix] --> B[Deepgram STT]
    B --> C[OpenAI GPT LLM with Suraksha Saathi prompt]
    C --> D[Murf Falcon TTS: Samar, te-IN]
    D --> E[LiveKit audio session]
    E --> F[User hears spoken guidance]
```

## Local Setup

Prerequisites:

- Python 3.10+
- `uv`
- Node.js 18+
- Corepack or `pnpm`
- LiveKit project
- Murf API key
- Deepgram API key
- OpenAI API key

Create local environment files:

```powershell
Copy-Item backend\.env.example backend\.env.local
Copy-Item frontend\.env.example frontend\.env.local
```

Fill in real values in both `.env.local` files. Do not commit them.

Set explicit agent dispatch in `frontend\.env.local`:

```text
AGENT_NAME=suraksha-saathi
```

Install and run:

```powershell
cd backend
uv sync
uv run python src/agent.py download-files

cd ..\frontend
corepack pnpm install

cd ..
.\start_app.ps1
```

Open `http://localhost:3000`, click `Start Telugu call`, allow microphone
access, and record the Day 1 conversation.

## Verification

No-credential checks:

```powershell
cd backend
.venv\Scripts\ruff.exe check src tests
$env:PYTHONPATH='src'; .venv\Scripts\pytest.exe tests\test_day1_config.py -q
```

Live verification still requires real LiveKit, Murf, Deepgram, and LLM keys.

## Known Limits

- This is a Day 1 voice pipeline and persona build, not a full banking product.
- The agent gives safety information, not legal, banking, or police advice.
- It must never ask for OTP, UPI PIN, CVV, password, or screen-sharing access.
- Refunds, account recovery, and case outcomes are never promised.

## Credits

Based on the Murf LiveKit starter and powered by Murf Falcon.
