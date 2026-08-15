# Telephony — Phone Calls with Murf Falcon

Connect the voice agent to real phone numbers. Two starters:

- **[`inbound/`](inbound/)** — someone calls your number, the agent answers
- **[`outbound/`](outbound/)** — the agent calls someone

Both use the same voice pipeline as [`src/agent.py`](../agent.py) (Deepgram STT → Gemini → Murf Falcon TTS), so anything you learn there applies here.

## How it works

```
Caller ──PSTN──► Your SIP provider ──SIP──► LiveKit ──► Your agent
                    (Twilio, etc.)          (trunk +
                                          dispatch rule)
```

LiveKit sits between your phone provider and your agent. You need two things configured on the LiveKit side:

- A **SIP trunk** — tells LiveKit which numbers to accept calls for (inbound) or how to authenticate when placing calls (outbound)
- A **dispatch rule** — tells LiveKit which agent to hand inbound calls to (inbound only)

## Prerequisites

> **Run every command on this page from the `backend/` directory** — all paths below are relative to it.

Beyond the [backend setup](../../README.md), you need:

1. **The `lk` CLI** — used to create trunks and dispatch rules:

   ```bash
   # macOS
   brew install livekit-cli
   # Linux
   curl -sSL https://get.livekit.io/cli | bash
   # Windows
   winget install LiveKit.LiveKitCLI
   ```

   Then authenticate: `lk cloud auth`

2. **A SIP provider account with a phone number.** These examples use [Twilio](https://twilio.com), but any SIP provider works. Numbers cost money, and some countries require identity or business verification before they'll issue one — budget time for this.

No new Python dependencies — `livekit-api` already ships with `livekit-agents`.

---

## Inbound: answering calls

### 1. Point your provider at LiveKit

In Twilio, create an **Elastic SIP Trunk** (Voice → Manage → Elastic SIP Trunking):

- Under **Origination**, add an Origination URI: `sip:<your-project>.sip.livekit.cloud`
- Under **Numbers**, attach the phone number you want the agent to answer

Your LiveKit SIP URI is in the LiveKit Cloud dashboard under **Settings → SIP**.

### 2. Create the LiveKit inbound trunk

Edit [`inbound/inbound-trunk.json`](inbound/inbound-trunk.json) and replace the number with yours, then:

```bash
lk sip inbound create src/telephony/inbound/inbound-trunk.json
```

Note the trunk ID it prints (`ST_...`).

### 3. Create the dispatch rule

Edit [`inbound/dispatch-rule.json`](inbound/dispatch-rule.json) and paste your trunk ID into `trunkIds`, then:

```bash
lk sip dispatch create src/telephony/inbound/dispatch-rule.json
```

This routes every call on that trunk into its own room and dispatches the agent named `inbound-agent`. The `agentName` in this file **must** match the `agent_name` in [`inbound/agent.py`](inbound/agent.py).

### 4. Run it

```bash
uv run python src/telephony/inbound/agent.py dev
```

Call your number. The agent picks up and greets you.

---

## Outbound: placing calls

### 1. Set up termination in Twilio

On the same Elastic SIP Trunk, under **Termination**:

- Set a Termination SIP URI (e.g. `your-trunk.pstn.twilio.com`)
- Under **Credential Lists**, create a username and password — LiveKit uses these to authenticate

### 2. Create the LiveKit outbound trunk

Edit [`outbound/outbound-trunk.json`](outbound/outbound-trunk.json) with your termination URI, credentials, and caller ID number, then:

```bash
lk sip outbound create src/telephony/outbound/outbound-trunk.json
```

Add the trunk ID it prints to `.env.local`:

```bash
LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_your_trunk_id
```

### 3. Run it

Start the worker:

```bash
uv run python src/telephony/outbound/agent.py dev
```

Then, in another terminal, place a call:

```bash
uv run python src/telephony/outbound/dial.py --to +15551234567
```

The agent joins a room, dials the number, and starts talking when someone picks up. There is no dispatch rule for outbound — `dial.py` dispatches the agent directly.

---

## Environment variables

Added on top of the [backend's existing variables](../../.env.example):

| Variable | Required for | Purpose |
|----------|--------------|---------|
| `LIVEKIT_SIP_OUTBOUND_TRUNK_ID` | Outbound | The trunk LiveKit dials through |
| `TRANSFER_TO_NUMBER` | Optional | Where `transfer_to_human` sends the call |

Trunks and dispatch rules live on LiveKit's servers, not in your env — that's why inbound needs no new variables.

## What each agent can do

Both agents ship with a small set of tools you can extend:

| Tool | Inbound | Outbound | What it does |
|------|:---:|:---:|--------------|
| `transfer_to_human` | ✅ | ✅ | Warm handoff to `TRANSFER_TO_NUMBER` via SIP transfer |
| `end_call` | ✅ | ✅ | Says goodbye, then deletes the room to hang up |
| `detected_answering_machine` | — | ✅ | Hangs up on voicemail instead of talking to it |

Add your own with the `@function_tool` decorator, same as in [`src/agent.py`](../agent.py).

## Customizing

Each agent file is self-contained — everything is in one file so you can copy a folder and hack on it.

- **What it says** — the `SYSTEM_PROMPT` and `GREETING` constants at the top
- **The voice** — the `voice` argument in `murf.TTS(...)`. Browse the [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
- **Caller ID** — the inbound agent reads it via `caller_phone_number()`, which pulls the `sip.phoneNumber` participant attribute. Use it to look up a customer record before greeting them
- **Noise cancellation** — both agents switch to `BVCTelephony` for SIP participants, which is tuned for the narrow frequency range of phone audio. Leave this on

## Deploying

The [Dockerfile](../../Dockerfile) builds the whole `backend/` directory, so the telephony agents are already in the image. Override the command to run one:

```bash
docker run --env-file .env.local murf-voice-agent \
  uv run src/telephony/inbound/agent.py start
```

Each agent is a separate worker process — run the ones you need. They can share a LiveKit project with the web agent in `src/agent.py`, since dispatch is by agent name.

## Troubleshooting

**The call connects but nobody speaks.** The worker isn't running, or the `agentName` in your dispatch rule doesn't match the `agent_name` in the agent file. Check `lk sip dispatch list`.

**Calls go straight to a busy signal.** Your provider isn't forwarding to LiveKit. Recheck the Origination URI in Twilio and that the number is attached to the trunk.

**Outbound calls fail immediately.** Usually the trunk credentials or a caller ID mismatch — the number in `outbound-trunk.json` must be one your provider has verified you can call from. The agent logs the SIP status code on failure.

**Audio is choppy or the agent talks over people.** Confirm `BVCTelephony` is being applied — it only kicks in for `PARTICIPANT_KIND_SIP` participants.

For anything deeper, see [LiveKit's SIP troubleshooting guide](https://docs.livekit.io/reference/telephony/troubleshooting/).

## Links

- [LiveKit SIP docs](https://docs.livekit.io/sip/)
- [LiveKit agent dispatch](https://docs.livekit.io/agents/server/agent-dispatch/)
- [Twilio Elastic SIP Trunking](https://www.twilio.com/docs/sip-trunking)
- [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
