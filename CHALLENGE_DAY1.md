# Day 1 - Voice for Bharat

## Track

Financial Services

## Agent

Suraksha Saathi is a Telugu-first voice agent for UPI fraud awareness and safe
digital payment guidance.

## Problem

Many new digital payment users in India receive scam calls, fake collect
requests, and OTP or UPI PIN traps. A voice-first helper is useful for people
who may not read English alerts quickly, especially when they are stressed after
a suspicious call or payment request.

Suraksha Saathi does not act like a bank or police officer. It gives simple,
spoken safety guidance, reminds callers not to share secrets, and points urgent
cases to the bank, the national cybercrime helpline 1930, or
cybercrime.gov.in.

## Day 1 Requirements

- Starter repo: Murf LiveKit starter.
- Track selected: Financial Services.
- Indian voice: Murf `Samar`.
- Main spoken locale: Telugu, `te-IN`.
- Speech: Murf Falcon through `livekit-murf`.
- Agent dispatch name: `suraksha-saathi`.

## Voice Choice

`Samar` was selected because Murf's Falcon 2 voice library lists it as an
Indian English voice with Telugu locale support. The voice is suitable for a
trustworthy fraud-awareness phone line because it sounds direct and calm.

## Demo Script

Say the track out loud in the recording:

> "My track is Financial Services. This is Suraksha Saathi, a Telugu-first UPI
> fraud awareness voice agent for Bharat."

Suggested short conversation:

1. User: "Namaste, naaku oka UPI collect request vachindi. Nenu accept
   cheyyala?"
2. Agent should greet as Suraksha Saathi and explain not to approve unknown
   collect requests.
3. User: "Bank ani call chesi OTP adugutunnaru."
4. Agent should say never share OTP, PIN, CVV, password, or screen access.
5. User: "Nenu already money lose ayyanu."
6. Agent should tell the caller to contact the bank immediately and report
   quickly to 1930 or cybercrime.gov.in.

## Setup

Create local environment files from the examples:

```powershell
Copy-Item backend\.env.example backend\.env.local
Copy-Item frontend\.env.example frontend\.env.local
```

Fill in real values for LiveKit, Murf, Deepgram, and Gemini or OpenAI. Do not
commit `.env.local`.

For explicit agent dispatch, set this in `frontend\.env.local`:

```text
AGENT_NAME=suraksha-saathi
```

Run the stack:

```powershell
.\start_app.ps1
```

Then open `http://localhost:3000`, click `Start Telugu call`, and record the
brief conversation.

## Known Limits

- This Day 1 build has the voice pipeline and first persona only; deeper
  guardrails and red-team evidence belong to Day 2.
- The agent gives safety information, not legal, banking, or police advice.
- A real call requires valid LiveKit, Murf, Deepgram, and LLM API keys.
