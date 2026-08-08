# Day 3 - Personalised Frontend

## Frontend Direction

Suraksha Saathi now looks and behaves like a Telugu financial-safety voice line
instead of a generic voice agent starter. The first screen focuses on UPI fraud
help, unknown collect requests, OTP/PIN safety, and quick reporting steps.

## Required States

The frontend makes these five states visible:

1. Ready - shown before the call starts with one clear `Start Telugu call`
   button.
2. Connecting - shown after the user taps the start button while LiveKit joins
   the session.
3. Listening - shown in the in-call status strip when the agent is listening to
   the caller.
4. Speaking - shown in the in-call status strip when the agent is replying.
5. Call ended - shown after disconnect, with a `Start again` action.

The in-call status strip also includes `data-day3-state` and
`data-day3-speaker` attributes so the state contract is easy to verify.

## Who Is Speaking

The session screen displays one clear speaker line:

- `Listening to you`
- `Agent is speaking`
- `Connecting to Suraksha Saathi`
- `Call ended`

The existing audio visualizer is configured as a teal bar visualizer to make
voice activity visible and match the Financial Services safety theme.

## Microphone Permission Error

If microphone access fails from the call controls, the frontend shows:

```text
Microphone permission blocked
Open your browser site settings, allow microphone access, then start again.
```

This is intentionally plain language for first-time users.

## Demo Script

Record this Day 3 flow:

1. Open the page and show the Ready screen.
2. Click `Start Telugu call` and show Connecting.
3. Speak a short Telugu-English question:
   `Naaku unknown UPI collect request vachindi. Accept cheyyala?`
4. Show the Listening and Speaking state strip during the exchange.
5. End the call.
6. Show the Call ended screen and `Start again`.
7. Optional: reload with microphone blocked in the browser and show the
   microphone permission message.

## Verification

Frontend contract:

```powershell
cd frontend
corepack pnpm day3:check
corepack pnpm build
```

Backend regression:

```powershell
cd backend
.venv\Scripts\ruff.exe check src tests
$env:PYTHONPATH='src'; .venv\Scripts\pytest.exe tests -q
```

## Submission Checklist

- Record a short video showing page load, connection, conversation, call ending,
  and how the frontend matches the Financial Services product.
- Mention Murf Falcon, 10 Days of Voice Agents, Murf AI, and `#VoiceForBharat`
  in the LinkedIn post.
- Submit the LinkedIn post link in the Discord form.
