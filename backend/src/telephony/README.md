# Telephony (Day 6) — Outbound scheme-deadline calls

Outbound agent places a real phone/SIP call and reminds a **previously eligible**
caller that a scheme renewal / enrolment window is approaching.

## Files

| Path | Role |
|------|------|
| `outbound/agent.py` | Worker: dials SIP, opens call, runs Nemotron + Murf |
| `outbound/dial.py` | Dispatch script with name / scheme / lang metadata |
| `outbound/outbound-trunk.json` | Twilio Elastic SIP trunk template |
| `outbound/linphone-trunk.json` | Linphone free-trial alternative trunk |

## Env (backend/.env.local)

```bash
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_...   # from `lk sip outbound create`
OPENAI_API_KEY=nvapi-...              # NVIDIA Nemotron
MURF_API_KEY=...
DEEPGRAM_API_KEY=...
# optional
TRANSFER_TO_NUMBER=+91...
NVIDIA_MODEL=nvidia/nemotron-3-nano-30b-a3b
```

## Twilio outbound trunk

1. Twilio → Elastic SIP Trunk → **Termination** URI + credential list.
2. Edit `outbound/outbound-trunk.json` (address, numbers, auth).
3. `lk sip outbound create src/telephony/outbound/outbound-trunk.json`
4. Put printed `ST_…` id into `LIVEKIT_SIP_OUTBOUND_TRUNK_ID`.

## Linphone alternative (no Twilio trial)

See challenge doc:
https://github.com/murf-ai/voice-for-bharat-challenge-2026/blob/main/supplementary/outbound-over-linphone.md

```bash
# edit linphone-trunk.json numbers to sip:<your-username>
lk sip outbound create src/telephony/outbound/linphone-trunk.json
# save ST_… as LIVEKIT_SIP_OUTBOUND_TRUNK_ID
# Linphone app: turn OFF "Media encryption mandatory"
```

## Run (with test .env.local)

```bash
cd backend
uv run python src/telephony/outbound/agent.py dev
```

Other terminal:

```bash
cd backend
uv run python src/telephony/outbound/dial.py --to $LINPHONE_SIP_URI \
  --name Ramesh \
  --scheme pmsby \
  --lang hi
```

Or just use your phone number for Twilio test.
```

## Opening script (Step 4)

First audio includes: **who** (Jan Sahay), **why** (eligible + deadline),
**how to stop** (“कॉल बंद” / “stop calling”).

## Demo video (Step 5)

Record phone/Linphone ringing + full conversation for submission.
