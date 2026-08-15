# FinSafe AI — My 10-Day Voice Agent Journey

## About the Project

FinSafe AI is a voice-first financial services assistant built during the Murf AI 10 Days of Voice Agents — VoiceForBharat Edition.

The goal of FinSafe AI is to make financial information easier to access through natural voice conversations.

Instead of typing questions, users can speak naturally with the assistant and receive voice responses.

The project uses Murf Falcon for text-to-speech and LiveKit for real-time voice communication.

---

## What I Built

During the 10-day challenge, I gradually improved FinSafe AI from a basic voice assistant into a more complete conversational AI system.

The major features I worked on include:

- Voice conversations
- Clear agent personality and role
- Safety guardrails
- Multilingual voice support
- Personalized frontend
- Agent state indicators
- Persistent caller memory
- SQLite database
- Financial scheme eligibility tool
- Outbound voice calls
- Human escalation
- Call tracking and analytics
- Specialist agent handoff

---

## 1. Voice Agent

FinSafe AI is designed specifically for the Financial Services track.

The agent has a defined role, objectives, personality, and safety boundaries.

This helps the assistant stay focused on financial-service-related conversations instead of behaving like a general-purpose chatbot.

---

## 2. Multilingual Voice Support

FinSafe AI supports multilingual conversations.

The agent can communicate in languages such as:

- English
- Hindi
- Gujarati
- Other supported languages

I also worked on making the agent respond in the language used by the user.

This makes the voice experience more natural and accessible for users who prefer Indian languages.

---

## 3. Personalized Frontend

I customized the frontend to make the voice-agent experience easier to understand.

The interface shows different agent states:

- Ready
- Connecting
- Listening
- Speaking
- Call Ended

This helps users understand what the agent is doing during a conversation.

---

## 4. Persistent Memory

One of the major improvements was adding persistent memory.

The agent can store approved caller information using SQLite so that information can be retrieved in future conversations.

The stored information can include:

- User ID
- Name
- Language preference
- Relevant financial facts
- Last interaction

The agent also asks the user for permission before saving information.

For financial services, sensitive information such as account numbers and government ID numbers should not be stored.

---

## 5. Financial Tools

I added a financial scheme eligibility lookup tool.

This allows the agent to use a tool when the user asks a question that requires external or structured information.

The basic flow is:

User asks a question

↓

Agent decides whether a tool is required

↓

Financial eligibility tool is called

↓

The result is processed

↓

Agent explains the result to the user

The agent should not invent an answer when the data source or tool is unavailable.

---

## 6. Outbound Voice Calls

I also worked on outbound voice calls.

This allows the voice agent to proactively communicate with users instead of only waiting for a user to start a browser conversation.

This helped me understand how voice agents can be used in real-world communication scenarios.

---

## 7. Human Escalation

The agent can also involve a human when the situation requires additional assistance.

Instead of trying to answer every question itself, the system can provide a path toward human support.

This is especially useful for financial services where some situations may require human assistance.

---

## 8. Call Tracking and Analytics

I worked on tracking voice interactions and call outcomes.

Call analytics can help understand:

- Number of conversations
- Call outcomes
- User interactions
- Situations requiring additional assistance

This can help improve the agent over time.

---

## 9. Specialist Agent Handoff

One of the final improvements was adding a specialist agent.

For FinSafe AI, the specialist focuses on government scheme-related questions.

The architecture is:

Main FinSafe Agent

↓

Does the request require specialist help?

↓

No → Main Agent answers

Yes → Conversation is handed to the specialist

↓

Government Scheme Specialist

The main agent informs the user before the handoff and the specialist continues the conversation using the existing context.

This taught me that an AI agent does not need to be an expert at everything.

It needs to know when to involve the right specialist.

---

## Architecture

The overall voice-agent architecture can be represented as:

User

↓

Speech-to-Text

↓

Large Language Model

↓

Memory / Tools / Specialist Agents

↓

Text-to-Speech

↓

User

LiveKit provides the real-time communication layer and Murf Falcon is used for voice generation.

---

## Technologies Used

- Python
- LiveKit
- Murf Falcon
- SQLite
- Large Language Model
- Speech-to-Text
- Text-to-Speech
- Frontend web technologies
- Git and GitHub

---

## Challenges I Faced

Building the project was not always straightforward.

Some of the challenges I faced included:

### Multilingual Response

Initially, the agent could understand multiple languages but sometimes responded in a different language.

I improved the language instructions so that the agent follows the user's language more consistently.

### LiveKit Connectivity

During testing, I encountered connection problems such as network connection errors and connection resets.

This helped me understand that real-time voice applications depend on both application code and stable network connectivity.

### Persistent Memory

Another challenge was making sure returning callers could be recognized correctly.

The system uses caller identity and stored information to retrieve previous conversation-related data.

---

## Privacy and Security

Security was an important part of the project.

API keys and secrets should never be committed to GitHub.

Sensitive user information should also be handled carefully.

The project should not store:

- API keys
- Passwords
- OTPs
- Bank account numbers
- Government ID numbers
- Private caller information

Memory should only be saved when the user gives permission.

---

## What I Learned

The biggest lesson from this challenge is that a useful voice agent is much more than an LLM connected to a microphone.

A strong voice agent needs:

- Conversation
- Context
- Memory
- Tools
- Safety
- Reliability
- Human escalation
- Specialization

I learned how different components work together to create a more complete conversational AI experience.

Memory makes conversations more personal.

Tools allow the agent to access useful information.

Guardrails help keep the agent within its intended role.

Human escalation provides a safety path.

Specialist agents allow the system to handle more focused requests.

---

## My 10-Day Journey

The project evolved step by step:

Day 1 → Voice Agent

Day 2 → Role and Guardrails

Day 3 → Personalized Frontend

Day 4 → Persistent Memory

Day 5 → Tools

Day 6 → Outbound Calls

Day 7 → Human Escalation / Call Handling

Day 8 → Call Tracking and Analytics

Day 9 → Specialist Agent Handoff

Day 10 → Sharing the Complete Journey

---

## Final Thoughts

The 10 Days of Voice Agents challenge was a great hands-on learning experience.

I started with a basic voice agent and gradually added memory, tools, multilingual support, outbound calls, human escalation, analytics, and specialist handoffs.

The journey taught me that building voice AI is not only about making an AI speak.

It is about making the system:

Listen → Understand → Remember → Act → Escalate → Respond

I am excited to continue improving FinSafe AI and keep exploring conversational AI and voice technology.

---

## Project Repository

GitHub:

https://github.com/Dodiyayash/murf-livekit-starter

Built as part of the Murf AI 10 Days of Voice Agents — VoiceForBharat Edition.