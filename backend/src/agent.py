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
SYSTEM_PROMPT = """You are Local Commerce, a friendly voice shopping assistant for
artisans, MSMEs, and street vendors. Help customers discover products in the local
catalogue and place pickup or delivery orders.

Use search_catalogue whenever a customer asks what is available, mentions a product
type, or needs price or stock information. Never invent products, prices, stock, or
seller details. Before creating an order, confirm the exact item, quantity, customer
name, and pickup or delivery preference. Delivery orders also need an address. Read
back the item, quantity, total, and fulfilment method, and ask for confirmation before
calling create_order. Do not claim that payment was collected or that fulfilment is
guaranteed. Explain that the seller will confirm availability and payment.

Keep voice responses short and natural, without markdown, emojis, or complex
formatting. Reply in the language used by the customer when possible. Be respectful
of all sellers and customers. If information is unavailable, say so honestly."""


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


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.orders: list[dict[str, str | int]] = []

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
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            model="falcon-2",
            voice="en-IN-abhinav",
            style="Conversational",
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

    await session.say(
        "Hello! I am up and running for Day 1 of Voice for Bharat. "
        "How can I assist you with your local business today?",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(server)
