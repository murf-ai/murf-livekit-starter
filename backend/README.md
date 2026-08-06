# Backend - Suraksha Saathi

Python LiveKit voice agent for the Day 1 Telugu UPI fraud awareness build.

## Pipeline

```text
User speech -> Deepgram STT -> OpenAI GPT LLM -> Murf Falcon TTS -> LiveKit audio
```

## Main Files

- `src/agent.py` wires LiveKit, Deepgram, OpenAI, Murf, VAD, and turn detection.
- `src/agent_config.py` holds the agent name, Telugu Murf voice settings, GPT
  model, and system prompt.
- `tests/test_day1_config.py` verifies the Day 1 challenge contract without
  requiring live API calls.

## Environment

Copy `.env.example` to `.env.local` and fill in:

```text
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
MURF_API_KEY=
DEEPGRAM_API_KEY=
OPENAI_API_KEY=
```

`OPENAI_API_KEY` is required because the backend uses:

```python
openai.responses.LLM(model="gpt-4.1-mini")
```

## Commands

```powershell
uv sync
uv run python src/agent.py download-files
uv run python src/agent.py dev
```

No-credential checks:

```powershell
.venv\Scripts\ruff.exe check src tests
$env:PYTHONPATH='src'; .venv\Scripts\pytest.exe tests\test_day1_config.py -q
```
