# Telephony — Outbound SIP / Linphone (Day 6 + Day 7)

Outbound agent places a real phone or **Linphone mobile SIP** call for:

| Day | Purpose | Entry point |
|-----|---------|-------------|
| **6** | Scheme deadline reminder for a previously eligible caller | `outbound/dial.py` |
| **7** | Human-escalation **resolution callback** (notify caller case is resolved) | `outbound/resolve_notify.py` |

Both paths share the same worker (`outbound/agent.py`), trunk, and low-latency
audio pipeline tuned for mobile networks.

## Files

| Path | Role |
|------|------|
| `outbound/agent.py` | Worker: dials SIP, opens call, runs Nemotron + Murf |
| `outbound/dial.py` | Dispatch script (scheme reminder **or** resolution notify) |
| `outbound/resolve_notify.py` | Day 7: mark ticket resolved + Linphone notify |
| `outbound/outbound-trunk.json` | Twilio Elastic SIP trunk template |
| `outbound/linphone-trunk.json` | Linphone free-trial alternative trunk (mobile-native) |

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

# Day 7 escalation + Linphone mobile
# ESCALATION_WEBHOOK_URL=https://example.com/hooks/jan-sahay-escalation
LINPHONE_SIP_URI=sip:your_username@sip.linphone.org
SIP_OUTBOUND_HOST=sip.linphone.org
```

## Linphone mobile integration (Jan Sahay)

Recommended path for curriculum demos without a paid Twilio trial.

### 1. Mobile client setup

1. Install **Linphone** on Android / iOS.
2. Create a free account at [sip.linphone.org](https://www.linphone.org).
3. Sign in on the phone; confirm registration shows **green / registered**.
4. **Turn OFF** “Media encryption mandatory” (Settings → Network / Call) so
   LiveKit SIP media negotiates cleanly.
5. Leave the app in the foreground or allow background SIP for the demo ring.

### 2. LiveKit outbound trunk

```bash
# edit numbers to sip:<your-linphone-username>
lk sip outbound create src/telephony/outbound/linphone-trunk.json
# save printed ST_… as LIVEKIT_SIP_OUTBOUND_TRUNK_ID in .env.local
```

`linphone-trunk.json` template:

```json
{
  "trunk": {
    "name": "linphone-trunk",
    "address": "sip.linphone.org",
    "transport": "SIP_TRANSPORT_TLS",
    "numbers": ["sip:REPLACE_WITH_LINPHONE_USERNAME"]
  }
}
```

### 3. Audio pipeline (low latency on mobile)

The outbound worker is pre-tuned for SIP:

- **STT:** Deepgram Nova-3 multilingual (handles Hindi/English on cellular noise)
- **VAD:** Silero with higher activation threshold + padding (fewer false barge-ins)
- **TTS:** Murf Falcon `hi-IN-anisha` / `en-IN-anisha`, 24 kHz, short buffer delay
- **Noise cancellation:** LiveKit `BVCTelephony` on SIP participants, `BVC` otherwise
- **Turn detection:** Multilingual model with tighter endpointing for mobile RTT

### 4. Event / call flow

```
resolve_notify.py / dial.py
        │  CreateRoom + CreateAgentDispatch (metadata JSON)
        ▼
outbound-agent worker
        │  create_sip_participant (trunk → Linphone URI)
        ▼
Linphone mobile rings  →  callee answers
        │
        ▼
session.start + session.say(greeting)
        │  purpose=scheme_deadline_reminder  OR  escalation_resolution
        ▼
Nemotron tools / conversation  →  end_call / hangup
```

Metadata keys the worker understands:

| Key | Day 6 | Day 7 resolution |
|-----|-------|------------------|
| `phone_number` | required | required |
| `caller_name` | yes | yes |
| `language` | `hi` / `en` | `hi` / `en` |
| `purpose` | `scheme_deadline_reminder` | `escalation_resolution` |
| `scheme` | yes | — |
| `reference_id` | — | yes |
| `resolution_notes` | — | scrubbed outcome text |

### 5. Persona on mobile

Jan Sahay stays **authoritative, empathetic, and professional** — bank-grade
customer service over cellular:

- Short turns (~35 words) for packet-loss resilience
- Always states **who / why / how to stop** in the first audio
- Never asks for OTP, PIN, password, CVV, or full account numbers
- Never promises instant live-agent pickup on resolution calls

## Twilio outbound trunk (optional)

1. Twilio → Elastic SIP Trunk → **Termination** URI + credential list.
2. Edit `outbound/outbound-trunk.json` (address, numbers, auth).
3. `lk sip outbound create src/telephony/outbound/outbound-trunk.json`
4. Put printed `ST_…` id into `LIVEKIT_SIP_OUTBOUND_TRUNK_ID`.

## Run worker

```bash
cd backend
uv run python src/telephony/outbound/agent.py dev
```

## Day 6 — scheme deadline dial

```bash
cd backend
uv run python src/telephony/outbound/dial.py --to $LINPHONE_SIP_URI \
  --name Ramesh \
  --scheme pmsby \
  --lang hi
```

## Day 7 — escalation resolve + Linphone notify

1. Create a ticket in-session (voice agent consent gate) **or** via unit demo.
2. Resolve and ring the caller’s Linphone:

```bash
cd backend
# dry-run: mark resolved, print callback metadata only
uv run python src/telephony/outbound/resolve_notify.py \
  --ref JS-A1B2C3D4 \
  --to $LINPHONE_SIP_URI \
  --notes "Specialist verified no further unauthorized activity." \
  --dry-run

# live SIP notify (worker must be running)
uv run python src/telephony/outbound/resolve_notify.py \
  --ref JS-A1B2C3D4 \
  --to $LINPHONE_SIP_URI \
  --notes "Specialist verified no further unauthorized activity."
```

Equivalent via `dial.py`:

```bash
uv run python src/telephony/outbound/dial.py --to $LINPHONE_SIP_URI \
  --purpose escalation_resolution \
  --ref JS-A1B2C3D4 \
  --name Ramesh --lang en \
  --notes "Case closed by specialist."
```

## Day 7 offline mock scenarios (no SIP)

```bash
cd backend
uv run python scripts/demo_escalation_scenarios.py
uv run pytest tests/test_escalation.py -q
```

## Opening scripts

**Day 6:** who (Jan Sahay), why (eligible + deadline), how to stop  
(“कॉल बंद” / “stop calling”).

**Day 7:** who, resolved case + **reference ID**, scrubbed outcome, how to stop,
explicit “we will not ask for OTP/PIN”.

## Demo video tips

Record Linphone ringing on the phone + full conversation. For Day 7, show:

1. In-app fraud report → consent → reference ID  
2. Specialist resolve + outbound ring on the same Linphone account  
3. Agent reading the reference and next steps without promising instant pickup
