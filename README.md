# 🛡️ Sita — Citizen AI Voice Assistant Portal

Jana Sahaya is an AI-powered citizen assistance web platform designed to empower individuals with instant guidance on:
- 💰 **Financial Literacy & Guidance**: Understand savings, budgeting, banking, loans, investments, and financial planning.
- 🛡️ **Fraud Prevention & Cyber Safety**: Learn how to avoid UPI fraud, OTP scams, phishing links, and fake loan apps.
- 🏛️ **Government Schemes Directory**: Discover central and state welfare schemes (like PM-KISAN, PMJDY, PMSBY, PMJJBY, APY, SSY, Mudra loans), check eligibility, and understand documentation.
- 📞 **Complaint Assistance**: Step-by-step guidance on reporting cybercrime, banking fraud, and consumer disputes.
- 🗣️ **Multilingual Voice Assistance**: Immersive, real-time voice consultations using secure AI voice pipelines.

Built with a clean, light, and professional government-tech design theme.

---

## Architecture

Jan Sahay utilizes a low-latency, real-time voice pipeline to communicate with citizens:

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[Gemini LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## Features & Implementation

### 1. Caller Memory Database (SQLite)
* **Location**: `backend/caller_data.db` (initialized automatically via [db.py](file:///c:/H-ASSASSIN/Codeing/Voice%20Agents/murf-livekit-starter/backend/src/db.py))
* **Usage**: Stores returning caller information such as `user_id`, `name`, `language_preference`, and `facts` (welfare schemes discussed, eligibility checks, etc.) extracted dynamically by the LLM during the voice call. This enables a personalized greeting and contextual continuity when a user reconnects.

### 2. Scheme Eligibility & Document Checklist Dataset (Local Hand-Built Dataset)
* **Location**: Implemented within the rules engine and tools in [agent.py](file:///c:/H-ASSASSIN/Codeing/Voice%20Agents/murf-livekit-starter/backend/src/agent.py) and [schemes_data.py](file:///c:/H-ASSASSIN/Codeing/Voice%20Agents/murf-livekit-starter/backend/src/schemes_data.py).
* **Usage**: Provides instant, rule-based eligibility verification, premium schedules, interest rates, and required document checklists for major national financial inclusion schemes:
  * **PMJDY** (Pradhan Mantri Jan Dhan Yojana)
  * **PMSBY** (Pradhan Mantri Suraksha Bima Yojana)
  * **PMJJBY** (Pradhan Mantri Jeevan Jyoti Bima Yojana)
  * **APY** (Atal Pension Yojana)
  * **SSY** (Sukanya Samriddhi Yojana)
  * **PM-KISAN** (PM Kisan Samman Nidhi)
  * **PMMY** (Pradhan Mantri MUDRA Yojana)

> [!IMPORTANT]
> **Data Access Note**: Since no public, stable, or free government API exists to programmatically check eligibility rules for these welfare schemes, this project utilizes a **hand-built local dataset** compiled directly from official Indian government scheme portals. All guidelines, age limits, tax exclusion policies (such as the APY tax-payer restrictions), premiums, and Sukanya Samriddhi interest rates (8.2% p.a.) are verified and updated as of **August 10, 2026**.

---

## Quickstart

### Prerequisites

- **Python** 3.10+
- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager
- **Node.js** 18+
- **pnpm** — fast Node package manager
- A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable | Where to get it | Required |
|----------|-----------------|----------|
| `LIVEKIT_URL` | LiveKit Cloud dashboard | Yes |
| `LIVEKIT_API_KEY` | LiveKit Cloud dashboard | Yes |
| `LIVEKIT_API_SECRET` | LiveKit Cloud dashboard | Yes |
| `MURF_API_KEY` | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes |
| `DEEPGRAM_API_KEY` | [deepgram.com](https://deepgram.com) | Yes |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Yes |

### Step 2: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 3: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 4: Run the Application

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser. Click **Start talking**, allow microphone access, and speak to interact with Jan Sahay.

---

## Project Structure

```
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   ├── agent.py         # Jan Sahay agent pipeline, rules engine, and tools
│   │   ├── db.py            # SQLite caller database setup and operations
│   │   ├── schemes_data.py  # Scheme dataset & eligibility evaluation engine
│   │   └── prompt.py        # Citizen support system prompt
│   ├── tests/               # LLM-judged evaluation suite
│   ├── pyproject.toml       # Python dependencies (uv)
│   └── caller_data.db       # Local SQLite user profile store
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main UI page
│   │   └── api/token/       # LiveKit token endpoint
│   ├── components/          # UI layout and interactive components
│   ├── app-config.ts        # Branding, title, theme configuration
│   └── package.json         # Node dependencies (pnpm)
├── start_app.ps1            # Start script for Windows
├── start_app.sh             # Start script for macOS/Linux
└── README.md                # This file
```

---

## License

MIT
