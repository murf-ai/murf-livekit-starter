import logging
from dataclasses import dataclass

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY
You are Mitra, a warm male local-commerce voice assistant. Use masculine Hindi forms
such as "मैं सुन रहा हूँ" and "मैं मदद कर सकता हूँ" when referring to yourself.
You work for a marketplace of
Indian artisans, MSMEs, neighbourhood shops, and street vendors. You are not the
seller, a bank, a delivery company, or a government authority.

OBJECTIVES
A successful call does one or more of these things:
1. Helps a customer discover a suitable local product using the catalogue.
2. Collects complete details for a pickup or delivery order request and records it
   only after the customer confirms the spoken summary.
3. Helps a shopkeeper check recorded stock or add a customer credit entry safely.

KNOWLEDGE
The catalogue and inventory tools are your only source for products, listed prices,
sellers, and stock. Tool results are snapshots, not guarantees. Say "listed price"
and explain that the seller must confirm the final price, availability, payment, and
delivery date. If a tool has no answer, say you do not have that information. Never
invent personal data, policies, discounts, order status, or seller decisions.

LANGUAGE
Detect the user's language and reply in the same language when possible. Mirror a
Hindi-English mix with natural conversational Hinglish, including the user's level of
formality. If the user switches languages, switch with them. Keep product names and
numbers clear. If you cannot confidently understand the language, apologise and ask
the user to repeat in Hindi or English. Never mock grammar, accents, or word choice.

GUARDRAILS
Refuse requests to fabricate seller confirmation, manipulate records, deceive or harm
someone, reveal private data, or do work unrelated to local commerce. Never claim an
order, price, discount, payment, refund, stock level, or delivery date is confirmed
unless the relevant tool has recorded it; even then, call an order an "order request"
until the seller confirms it. Never claim to have contacted a seller or human unless a
real handoff mechanism confirms that. Never ask for an OTP, PIN, password, full bank
account number, or full card details. Do not provide legal, medical, or financial
advice. Acknowledge the request briefly, state the limit, and offer a safe next step.

For seller decisions, disputes, refunds, payment issues, safety concerns, repeated
misunderstanding, or anything outside your authority, use this escalation script in
the user's language: "I can't verify or decide that. I can help you contact the seller
or a human support person. Would you like me to note your order ID and a brief message?"
Only request the order ID and a short non-sensitive message. For immediate danger,
tell the user to contact local emergency services or a trusted person now.

ORDER RULES
Use search_catalogue for catalogue, product, price, seller, or stock questions. Before
calling create_order, collect the exact item, quantity, customer name, and pickup or
delivery choice. For delivery, also collect the address. Read back the item, quantity,
listed total, and fulfilment method, then obtain an explicit yes. Never treat silence
or an unclear answer as confirmation. Use check_inventory for shop stock. Use
check_inventory immediately when a shopkeeper names a product; do not ask for a shop
name or seller ID. Use add_credit_entry for khata credit and confirm it only after the
tool succeeds.

STYLE
Sound calm, patient, and practical. Prefer one or two short sentences at a time, with
no markdown, bullets, brackets, emojis, or sentences longer than about 20 words. Ask
one question at a time. Let the user finish and handle pauses without rushing. If no
meaningful speech is detected, say once: "I'm here. Take your time, or tell me how I
can help with local products or orders." After a second failed attempt, say: "No
problem. We can try again whenever you're ready. Goodbye."""

FIRST_TURN_GREETING = (
    "Namaste! I'm Mitra, your local shopping assistant. I can help you find local "
    "products, check listed prices, or prepare order requests. How may I help?"
)


@dataclass(frozen=True)
class CatalogueItem:
    item_id: str
    name: str
    seller: str
    category: str
    price_inr: int
    stock: int


CATALOGUE = (
    CatalogueItem(
        "ART-101",
        "Hand-painted terracotta diya set",
        "Maya Crafts",
        "handicrafts",
        320,
        12,
    ),
    CatalogueItem(
        "TXT-204", "Handloom cotton stole", "Sakhi Weaves", "textiles", 850, 7
    ),
    CatalogueItem(
        "FOD-310",
        "Homemade mango pickle, 500 grams",
        "Asha Foods",
        "food",
        240,
        18,
    ),
    CatalogueItem(
        "FOD-315",
        "Fresh millet rotis, pack of 6",
        "Shanti Tiffins",
        "food",
        120,
        10,
    ),
    CatalogueItem("HOM-408", "Natural coir doormat", "Coastal Works", "home", 450, 5),
)

BUSINESS_INVENTORY = {
    "mustard oil": {"quantity": 15, "unit": "liters"},
}


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.orders: list[dict[str, str | int]] = []
        self.credit_entries: list[dict[str, str | int]] = []

    @function_tool
    async def check_inventory(self, context: RunContext, product_name: str) -> str:
        """Check the shop's current stock for a product.

        Args:
            product_name: Product to look up, such as mustard oil.
        """
        del context
        normalized_name = product_name.casefold().strip()
        stock = BUSINESS_INVENTORY.get(normalized_name)
        if stock is None:
            return f"No inventory record was found for {product_name.strip()}."

        return (
            f"{product_name.strip().title()}: {stock['quantity']} "
            f"{stock['unit']} currently in stock."
        )

    @function_tool
    async def add_credit_entry(
        self,
        context: RunContext,
        customer_name: str,
        amount_inr: int,
    ) -> str:
        """Record money owed by a customer in the shop's khata register.

        Args:
            customer_name: Customer whose credit should be recorded.
            amount_inr: Credit amount in Indian rupees.
        """
        del context
        customer_name = customer_name.strip()
        if not customer_name:
            return "Credit entry not recorded: the customer name is required."
        if amount_inr <= 0:
            return "Credit entry not recorded: the amount must be greater than zero."

        entry_id = f"KH-{len(self.credit_entries) + 1:04d}"
        self.credit_entries.append(
            {
                "entry_id": entry_id,
                "customer_name": customer_name,
                "amount_inr": amount_inr,
            }
        )
        logger.info("Created khata credit entry %s", entry_id)
        return (
            f"Credit entry {entry_id} recorded: INR {amount_inr} for {customer_name}."
        )

    @function_tool
    async def search_catalogue(self, context: RunContext, query: str) -> str:
        """Search products by name, category, seller, or item ID.

        Args:
            query: What the customer wants, such as pickles, textiles, or ART-101.
        """
        del context
        terms = query.casefold().split()
        matches = [
            item
            for item in CATALOGUE
            if all(term in self._catalogue_search_text(item) for term in terms)
        ]
        if not matches:
            return "No matching products are currently listed."

        return "\n".join(
            f"{item.item_id}: {item.name} by {item.seller}; "
            f"INR {item.price_inr}; {item.stock} available"
            for item in matches
        )

    @staticmethod
    def _catalogue_search_text(item: CatalogueItem) -> str:
        return f"{item.item_id} {item.name} {item.seller} {item.category}".casefold()

    @function_tool
    async def create_order(
        self,
        context: RunContext,
        item_id: str,
        quantity: int,
        customer_name: str,
        fulfilment: str,
        delivery_address: str = "",
    ) -> str:
        """Create an order only after the customer confirms the read-back summary.

        Args:
            item_id: Exact catalogue item ID.
            quantity: Number of units requested.
            customer_name: Name supplied by the customer.
            fulfilment: Either pickup or delivery.
            delivery_address: Required when fulfilment is delivery.
        """
        del context
        item = next(
            (product for product in CATALOGUE if product.item_id == item_id.upper()),
            None,
        )
        if item is None:
            return "Order not created: item ID is not in the catalogue."
        if quantity < 1 or quantity > item.stock:
            return f"Order not created: choose between 1 and {item.stock} units."

        fulfilment = fulfilment.casefold().strip()
        if fulfilment not in {"pickup", "delivery"}:
            return "Order not created: fulfilment must be pickup or delivery."
        if fulfilment == "delivery" and not delivery_address.strip():
            return "Order not created: a delivery address is required."
        if not customer_name.strip():
            return "Order not created: the customer name is required."

        order_id = f"LC-{len(self.orders) + 1:04d}"
        total = item.price_inr * quantity
        self.orders.append(
            {
                "order_id": order_id,
                "item_id": item.item_id,
                "quantity": quantity,
                "customer_name": customer_name.strip(),
                "fulfilment": fulfilment,
                "delivery_address": delivery_address.strip(),
                "total_inr": total,
            }
        )
        logger.info("Created local commerce order %s", order_id)
        return (
            f"Order {order_id} recorded for {quantity} x {item.name}. "
            f"Total INR {total}, {fulfilment}. Payment is not collected; "
            "the seller must confirm the order."
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            model="falcon-2",
            voice="Abhinav",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    await session.say(FIRST_TURN_GREETING, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
