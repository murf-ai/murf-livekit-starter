# The Anatomy of a Sub-200ms Voice AI Agent

<!--
PUBLISHING NOTES (delete before posting):
- Dev.to tags: voiceai, ai, python, opensource
- Cover image: architecture diagram or screenshot of agent UI
- INSERT DEMO GIF after the intro (15sec screen recording of a live conversation)
- HN title: "The anatomy of a sub-200ms voice AI agent"
- This post is education-first: teaches voice pipeline architecture.
  The starter kit is a resource, not the point.
-->

Most voice AI demos cheat. They show a pre-recorded conversation with perfect timing, skip the part where the agent takes 800ms to start responding, and gloss over the pipeline complexity that makes real-time voice feel impossible.

I know because I've sat through dozens of them while working on developer tools at Murf. And when I actually tried to build a real-time voice agent myself — one where the latency was low enough to feel like a conversation — I learned that the hard part isn't any single component. It's the space *between* them.

This post breaks down the architecture of a voice AI agent that responds end-to-end in under 200ms. Everything I'm describing is running in an [open-source starter kit](https://github.com/sanchitasunil/murf-livekit-starter) you can clone and try, but the architecture applies regardless of which providers you choose.

<!-- INSERT DEMO GIF HERE -->

## Where the time actually goes

A voice agent is a pipeline with four stages, and each one costs time:

```
You speak → [STT ~150ms] → text → [LLM ~100ms] → response → [TTS ~55-300ms] → audio → [transport ~20ms] → you hear it
```

If you add those numbers naively, you're looking at 325-570ms before the user hears the first syllable of a response. That doesn't sound terrible on paper, but in a live conversation, anything over ~250ms feels like the other person is hesitating. Over ~500ms and it feels broken.

So the question becomes: where do you cut time, and how?

**STT is mostly solved.** Deepgram's Nova-3, Whisper variants, and AssemblyAI's real-time models all return transcriptions fast enough that STT isn't your bottleneck. Differences exist, but they're in the 20-50ms range — not make-or-break.

**LLM latency depends on the model, but streaming helps.** If you use a fast model (Gemini 2.5 Flash, GPT-4o-mini) with streaming enabled, the LLM starts emitting tokens before it's finished thinking. Your TTS doesn't need to wait for the full response — it can start converting the first sentence while the second is still being generated.

**TTS is where most agents stall.** This is the insight that surprised me. I assumed the LLM would be the bottleneck. In practice, STT and LLM latency are both manageable. But TTS time-to-first-byte varies wildly across providers — from 55ms to 300ms+ — and unlike STT or LLM, you can't pipeline around it. The user is waiting for audio. Every millisecond of TTS latency is a millisecond of silence.

**Transport is nearly free.** LiveKit (WebRTC-based) adds ~20ms of transport latency. This is not the layer to optimize.

## The three tricks that get you under 200ms

The starter kit uses three techniques that, combined, make the pipeline feel instant. None of them are novel — LiveKit's agents framework and various TTS providers support them — but using all three together is what crosses the threshold from "noticeable delay" to "feels like a conversation."

### 1. Preemptive generation

The LLM doesn't wait for you to finish speaking. It starts forming a response based on what you've said *so far*. If you say "Can you help me reschedule my—" the LLM is already working on a response about rescheduling before you say "appointment."

If the LLM guessed wrong based on the partial input, it discards and regenerates. But most of the time, the first few words of your sentence contain enough intent that the response is ready by the time you finish talking.

In the starter kit, this is one flag:

```python
session = AgentSession(
    ...
    preemptive_generation=True,
)
```

### 2. Sentence-level TTS streaming

Instead of waiting for the full LLM response and then converting it to speech, the TTS starts working the moment it has one complete sentence. The LLM streams tokens, a sentence tokenizer collects them, and as soon as a sentence boundary is detected, that chunk goes to TTS immediately.

```python
tts=murf.TTS(
    voice="en-US-matthew",
    style="Conversation",
    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
    text_pacing=True  # adds natural pauses between sentences
)
```

The `min_sentence_len=2` prevents the tokenizer from firing on fragments like "Sure." before the rest of the response arrives. The `text_pacing=True` inserts natural pauses so the output doesn't sound like a single breathless run-on.

### 3. Fast TTS (this is the one you can't fake)

The first two tricks reduce *perceived* latency by overlapping work. But you still need the TTS itself to be fast, because that's the last synchronous step before the user hears audio.

I tested several providers. Here's what I measured:

| Provider | Time to First Byte (p50) | Cost/min |
|----------|--------------------------|----------|
| Murf Falcon | ~55ms | $0.01 |
| Cartesia | ~135ms | $0.04 |
| AWS Polly | ~150ms | $0.02 |
| ElevenLabs | ~200ms | $0.10 |
| OpenAI TTS | ~300ms | $0.06 |

*(These are approximate. Latency varies by region. If you want to run your own benchmarks: [open-source TTS latency benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker).)*

I work at Murf, so take the framing with appropriate salt — but the numbers are independently reproducible. We built the starter kit with Falcon because the latency difference is the thing that takes the experience from "pretty good" to "wait, that was AI?"

The cost difference matters for a different reason: at $0.01/min, you can prototype without thinking about it. When you're iterating on prompts and testing conversations, running 100 test calls at $0.10/min adds up fast.

## The turn detection problem nobody talks about

Here's something I didn't appreciate until I built a voice agent: knowing when someone has finished talking is *hard*.

Silence detection (VAD — voice activity detection) is not enough. People pause mid-sentence. They say "um." They trail off and then continue. If your agent jumps in every time it detects 300ms of silence, it will constantly talk over the user. If it waits too long, the conversation drags.

The starter kit uses two layers:

**Silero VAD** handles the acoustic side — is there human speech happening right now, or is it silence/noise? This is fast and reliable, but it only tells you about *sound*, not *meaning*.

**A multilingual turn detector** handles the semantic side — based on the words transcribed so far, is this person done with their thought? This model understands conversational patterns across languages, so it knows that "I was wondering if..." is probably not a complete turn, even if the speaker pauses after it.

```python
session = AgentSession(
    ...
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
)
```

Getting turn detection wrong is the #1 reason voice agents feel awkward, and it's the thing most tutorials skip entirely. If you're building in this space, spend time here.

## Swapping the agent's brain in 30 seconds

The agent's entire behavior is a system prompt — a single string at the top of `agent.py`. The pipeline doesn't change. The frontend doesn't change. You just rewrite the instructions.

The starter kit ships as a customer support agent, but I tested it as a Spanish language tutor (speaks in Spanish, corrects your grammar, switches to English for explanations) and a medical clinic receptionist (schedules appointments, answers office hours questions, takes messages). Same deploy, different prompt.

This is where voice AI gets interesting for developers: the infrastructure is a solved problem once, and then every new use case is just a prompt. Language tutoring, interview prep, accessibility tools, therapy practice bots, game NPCs — the pipeline is identical. The prompt is the product.

## Run it yourself

The [starter kit](https://github.com/sanchitasunil/murf-livekit-starter) takes about 5 minutes to set up. Clone the repo, grab API keys from [Murf](https://murf.ai/api/dashboard), [LiveKit](https://cloud.livekit.io), [Deepgram](https://deepgram.com), and [Google AI Studio](https://aistudio.google.com), drop them in `.env.local`, and run the start script. One-click deploy buttons for Railway and Vercel are in the README if you want to put it in production.

I'm also putting together a **video tutorial** walking through the full setup — narrated by Murf, because that seemed like the right move.

## Where to go deeper

If you want to extend the starter kit: the agent supports function calling (there's a commented-out weather tool example), LiveKit supports SIP for phone integration, and the codebase has hooks for Hedra avatar integration if you want to give your agent a face.

If you want to understand voice AI architecture more broadly, a few resources I found useful while building this: the [LiveKit Agents docs](https://docs.livekit.io/agents/) are the best technical reference for the pipeline model, and the [Murf API docs](https://murf.ai/api/docs) cover the TTS streaming integration in detail.

If you build something with this — or if you have questions, feedback, or want to tell me what I got wrong — I'm in the [Murf Discord](https://discord.gg/FbKAy96Sz7). Come say hi.

---

*I'm Sally, dev advocate at [Murf](https://murf.ai). I work on tools and content that help developers build with voice AI.*

---

*Tags: #voiceai #ai #python #opensource*
