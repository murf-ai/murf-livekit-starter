# Murf Voice AI — Content & Community Growth Strategy

## The Two Pieces to Ship This Week

Based on the murf-livekit-starter repo, here's the plan: **one blog post** (thought-leadership + announcement style) and **one hands-on tutorial** (written + video). They serve different purposes and reach different audiences.

---

## Piece 1: The Blog Post

**Title options (pick one):**
- "Build a Voice AI Agent in 5 Minutes with Murf Falcon + LiveKit"
- "Why We Built the Fastest Voice AI Starter Kit (and How You Can Use It)"
- "From Zero to Voice AI Agent: Murf Falcon's 55ms Latency in Action"

**Angle:** This is not a tutorial — it's a "why this matters" post that shows what Murf Falcon enables and gets developers excited enough to click through to the repo or tutorial.

### Structure

**Hook (2-3 paragraphs)**
- Open with a pain point: building real-time voice AI is hard — high latency kills the experience, TTS APIs are expensive, and stitching together STT + LLM + TTS + WebRTC is a weekend-long rabbit hole
- Introduce the starter kit: we built a production-ready voice AI agent that runs in 5 minutes, powered by Murf Falcon (55ms TTS latency) + LiveKit
- Quick "what you'll have by the end" — a working voice agent you can talk to in your browser

**The Stack — What's Under the Hood (with architecture diagram)**
- Visual: simple flow diagram → User Speech → Deepgram STT → Gemini LLM → Murf Falcon TTS → LiveKit → User hears response
- Brief explanation of each piece and why it was chosen
- Emphasize Murf Falcon's differentiators: 55ms latency, 150+ voices, 35+ languages, $0.01/min (10x cheaper than ElevenLabs)

**Show, Don't Tell (embedded demo or GIF)**
- Embed a short screen recording or GIF of the agent in action
- Show the different audio visualizers (bar, wave, radial — the UI is gorgeous, use it)
- If possible, embed a live demo link

**Three Use Cases You Can Build Today**
- Customer support agent (the default prompt)
- Language tutor (the Spanish conversation prompt from the repo)
- AI receptionist (the medical clinic scheduling prompt)
- For each: 3-4 sentences on the use case + the system prompt swap (literally one variable change)

**Performance That Actually Matters**
- Quick comparison table: Murf Falcon vs. competitors on latency, cost, voice count
- Emphasize: 55ms model latency, 130ms time-to-first-audio, $0.01/min
- This section should feel like "here are the numbers, decide for yourself" — not salesy

**Get Started**
- Link to the repo
- Link to the tutorial (Piece 2)
- Link to Murf API docs and voice library
- CTA: "Star the repo, join the Discord, build something cool"

### Blog Post Specs
- **Length:** 1,200-1,500 words (5-7 min read)
- **Tone:** Technical but approachable — like you're explaining it to a smart friend at a hackathon
- **Visuals:** Architecture diagram, demo GIF/video, comparison table, code snippets (keep them short — 5-10 lines max)

---

## Piece 2: The Tutorial

**Title:** "Build a Real-Time Voice AI Agent with Murf + LiveKit (Full Guide)"

**Angle:** Step-by-step walkthrough from zero to a working voice agent. Written version is the "canonical" reference; video is the companion that shows it live.

### Written Tutorial Structure

**Introduction (what we're building)**
- Screenshot of the finished product
- List of what the user will learn
- Prerequisites: Python 3.10+, Node.js, API keys (Murf, LiveKit, Deepgram, Google/OpenAI)
- Estimated time: ~15 minutes

**Step 1: Get Your API Keys**
- Walk through signing up for each service (with direct links)
- Murf: murf.ai/api/dashboard
- LiveKit: cloud.livekit.io
- Deepgram: deepgram.com
- Google AI Studio (for Gemini): aistudio.google.com
- Show what the .env file should look like

**Step 2: Clone and Set Up the Backend**
- Clone the repo
- Create `.env.local` with credentials
- Install with `uv sync` (explain why uv, link to install)
- Quick tour of `agent.py` — explain the pipeline in ~10 lines of commentary

**Step 3: Set Up the Frontend**
- Create frontend `.env.local`
- Install with `pnpm install`
- Quick tour of the key components

**Step 4: Run It**
- `./start_app.sh` or the 3-terminal approach
- Show what it looks like when it's working
- Talk to the agent, show the transcript

**Step 5: Customize It**
- Change the voice (show 2-3 options with audio samples if possible)
- Change the system prompt (show the language tutor example)
- Change the visualizer style
- Add a function tool (walk through the weather example in the code)

**Step 6: Deploy It**
- Backend → Railway (one-click button)
- Frontend → Vercel (one-click button)
- Show the deployed version working

**What's Next**
- Link to Murf voice library
- Link to LiveKit docs
- Invite to Discord
- Ideas for what to build next (phone bot via SIP, avatar integration, multi-agent)

### Video Tutorial Specs
- **Length:** 10-15 minutes (people drop off after 15)
- **Format:** Screen recording with face cam in corner (optional but helps with engagement)
- **Flow:** Follow the written tutorial exactly — the video IS the written tutorial, just live
- **Record in segments:** Introduction, setup, running, customizing, deploying — edit together
- **Show your terminal and browser side by side**

### Recording Tips
- Use OBS Studio (free) or Loom (easier, built-in editing)
- 1080p minimum, 1440p preferred
- Bump your terminal font size to 16-18pt so it's readable
- Have all API keys ready before recording (no one wants to watch you sign up)
- Do one dry run before recording

---

## Where to Publish (Priority Order)

### Primary Platforms (publish first, this week)

| Platform | What to Post | Why |
|----------|-------------|-----|
| **Dev.to** | Blog post (full) | Huge dev audience, great SEO, built-in community, tags like #ai #voiceai #python #webdev. Free, no approval needed. Cross-posts to Forem network. |
| **Hashnode** | Blog post (cross-post) | Strong dev community, personal blog with custom domain support, good SEO. Cross-post the same blog. |
| **YouTube** | Video tutorial | The #1 destination for dev tutorials. Optimize title/description with keywords. |
| **GitHub README** | Already exists | Make sure the repo README links to the blog and tutorial. Add badges (stars, license, etc.) |

### Secondary Platforms (within a few days)

| Platform | What to Post | Why |
|----------|-------------|-----|
| **Hacker News** | Blog post link (Show HN) | "Show HN: Voice AI agent in 5 min with 55ms TTS latency" — the latency angle is catnip for HN. Post Tuesday-Thursday, 8-10am ET. |
| **Reddit** | Blog or tutorial link | r/MachineLearning, r/artificial, r/Python, r/webdev, r/SideProject. Follow each sub's self-promo rules. |
| **Twitter/X** | Thread summarizing the blog | Dev Twitter is still active. Thread format: pain point → solution → demo GIF → link. Tag @laboriously relevant accounts. |
| **LinkedIn** | Blog post (native or link) | Good for professional dev audience. Native posts get more reach than links. |
| **Discord (Murf's)** | Announcement + links | Your existing community. Pin it in an announcements channel. |

### Stretch Platforms (if you have bandwidth)

| Platform | What to Post | Why |
|----------|-------------|-----|
| **Medium / freeCodeCamp** | Tutorial (cross-post) | freeCodeCamp's publication has massive reach if they accept it. Medium's paywall is a downside but SEO is good. |
| **Indie Hackers** | Blog post | Good community for builder-types, especially if you frame it as "we built X" |
| **Product Hunt** | Launch the starter kit | Great for visibility spikes. Needs preparation — do this as a separate effort. |

---

## Distribution Strategy (Make It Spread)

### Day 1: Publish
- Post blog to Dev.to and Hashnode simultaneously
- Upload video to YouTube
- Update repo README with links to blog + tutorial
- Post in Murf Discord

### Day 2: Amplify
- Twitter/X thread (with demo GIF)
- LinkedIn post (native, not just a link)
- Submit to Hacker News (Show HN)
- Post to relevant Reddit subs

### Day 3-5: Engage
- Respond to every comment on Dev.to, HN, Reddit
- Answer questions in Discord
- Retweet/share any community members who try the project
- DM dev influencers who cover voice AI / AI agents (don't spam — genuine outreach only)

### Ongoing
- Track GitHub stars, blog views, video views
- Note which platform drives the most traffic (add UTM params to links)
- Use feedback to shape the next piece of content

---

## Content Calendar — What Comes After This Week

Once the first blog + tutorial are out, here's a cadence to build momentum:

| Week | Content | Type |
|------|---------|------|
| Week 1 (this week) | "Build a Voice AI Agent in 5 Min" blog + tutorial | Blog + Video |
| Week 2 | "Building a Multilingual Voice Tutor with Murf" | Tutorial (written) |
| Week 3 | "Murf Falcon vs. ElevenLabs vs. Play.ht: TTS Benchmark" | Blog (comparison) |
| Week 4 | "Deploy a Voice AI Phone Bot with Murf + LiveKit SIP" | Tutorial (advanced) |
| Week 5 | "How We Got 55ms TTS Latency" (technical deep-dive) | Blog (engineering) |
| Week 6 | Community showcase — "What Devs Are Building with Murf" | Blog (social proof) |

---

## Community Building Tactics

### Discord (your existing asset)
- Create channels: #showcase (people share what they built), #help (support), #announcements
- Post every new piece of content there first
- Run a monthly "build with Murf" challenge (even informal)
- Be genuinely helpful — answer questions fast

### GitHub
- Add "Good First Issues" to the repo for contributor onboarding
- Use GitHub Discussions for Q&A
- Respond to issues and PRs quickly (even if it's just "thanks, looking into this")
- Add a CONTRIBUTING.md (you already have one — keep it updated)

### Developer Relations Basics
- Track these metrics: GitHub stars, forks, clones, Discord members, blog views, video views, API signups
- Set up a simple dashboard (even a spreadsheet) to track week-over-week growth
- Every piece of content should have one clear CTA: star the repo, join Discord, or try the API
- Don't sell — teach. The product sells itself when devs see 55ms latency and $0.01/min pricing.

---

## Quick-Reference: SEO Keywords to Target

Use these in titles, descriptions, and tags across all platforms:

- voice AI agent
- text to speech API
- real-time voice AI
- LiveKit voice agent
- TTS low latency
- build voice assistant
- Python voice AI
- conversational AI agent
- Murf TTS API
- voice AI tutorial

---

## Tools You'll Need

| Tool | Purpose | Cost |
|------|---------|------|
| OBS Studio or Loom | Screen recording for video tutorial | Free / Free tier |
| Canva or Excalidraw | Architecture diagram for blog | Free |
| Gifski or LICEcap | Demo GIFs for social media | Free |
| Grammarly | Proofread blog posts | Free tier |
| UTM.io or manual UTMs | Track which platform drives traffic | Free |

---

*This strategy is designed to ship fast (this week) while setting up a repeatable system for ongoing content. The first blog + tutorial establish credibility; everything after builds on that foundation.*
