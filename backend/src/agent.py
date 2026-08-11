import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable

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

from catalogue import (
    Catalogue,
    CatalogueItem,
    CatalogueUnavailableError,
    calculate_total,
    fetch_catalogue,
    search_products,
)
from knowledge import KnowledgeBase
from memory import CallerMemory, CallerMemoryStore

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """IDENTITY
You are Mitra, a warm male local-commerce voice assistant. Only while replying in
Hindi, use masculine forms such as "मैं सुन रहा हूँ" and "मैं मदद कर सकता हूँ".
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
Always use search_catalogue for product availability, price, stock, category, or
budget questions; never answer them from memory. Use calculate_order_total for every
order calculation instead of doing arithmetic yourself. Treat the returned catalogue
timestamp as data freshness and mention it when relevant. The catalogue is a local
prototype dataset, not live data. If either tool fails, clearly say that current
product information cannot be confirmed and never invent a fallback answer.
For schemes, crop guidance, training, or other knowledge questions, always call
search_knowledge_base. Answer only from its returned passages, mention the document
title naturally, and say when the knowledge base has no relevant answer. Never treat
a retrieved document as proof that the caller is eligible or that an outcome is
approved. Suggest checking the cited official source for current details.

LANGUAGE
LANGUAGE ROUTING IS A HIGH-PRIORITY RULE. Determine the response language only from
the user's current message, never from earlier turns, the greeting, caller memory, or
your Indian identity.
1. If the current message is English, reply only in English. Do not answer an
   English-only message in Hindi. The only permitted Devanagari word in an English
   response is the greeting "नमस्ते". Example: "Do you have milk?" must receive an
   English answer.
2. If the current message is Hindi, reply only in Hindi written in Devanagari.
   Romanized Hindi counts as Hindi: convert its Hindi meaning to Devanagari instead of
   copying Romanized Hindi. Example: "Mujhe doodh chahiye" must receive a Devanagari
   Hindi answer.
3. If the message mixes Hindi and English, use Hindi in Devanagari while keeping only
   product names, brands, IDs, and unavoidable technical terms in English.
If the user switches languages, switch with their current message. Keep product names
and numbers clear. If you cannot confidently identify the language, ask in English:
"Would you prefer English or Hindi?" Never mock grammar, accents, or word choice.
Understand common Hindi shopping words and Romanized variants. Examples: achar or
achaar means pickle, sajawati chiz or sajawati cheez means decorative handicrafts,
and sarso or sarson ka tel means mustard oil. Reply using the customer's wording.
Always write each language in its native script. Write every Hindi word in Devanagari,
never Romanized Hindi, even when the caller speaks Romanized Hindi. English product
names, identifiers, and source titles may stay in English. Apply the same native-script
rule to every other non-English language.
Whenever you say Namaste in any response, always write the greeting as "नमस्ते" in
Devanagari, even when the rest of the response is English. Never write "Namaste" in
Latin letters.

CALLER MEMORY
At the beginning of a conversation, use lookup_caller to check whether this caller is
known. Never guess an identity or reveal one caller's memory to another caller. If a
record is found, greet the caller by name and continue from the saved last conversation
or another relevant fact. Do not repeat the generic first-call introduction or replay
the same canned greeting. If no record is found, continue normally and ask their name
only when useful. Unless the caller explicitly asks you to remember or save the exact
details they are providing, state exactly what you propose to remember and ask for
permission in a separate turn. Call save_caller_memory after an explicit yes to that
proposal or an explicit request to save the supplied details. Pass
consent_given=true only for that explicit yes; silence, ambiguity, or consent to an
order is not memory consent. If the caller says no, do not call the save tool. Useful
local-commerce facts are the caller's district, a short last-conversation summary,
recent order, usual quantity, and preferred delivery slot. Never save call details
automatically. If the caller asks to be forgotten, call forget_caller immediately;
deletion needs no extra confirmation. Clearly report whether a saved record was
removed.

Do not postpone memory consent until the call ends. When the caller shares a useful
name, district, language preference, usual quantity, delivery slot, recent order, or
detail for next time, finish the current answer and immediately state the exact short
facts you could remember, then ask permission. If the caller's next message explicitly
agrees, call save_caller_memory before discussing anything else. Do not merely say
that you will remember it. If the caller explicitly says "remember this", "save my
details", or equivalent while stating the exact facts, that request itself is explicit
consent: call save_caller_memory immediately with consent_given=true and report the
tool result.

When the caller indicates they are finished, says goodbye, or asks to end the call,
do not say goodbye immediately if there is a useful name or conversation detail that
has not yet been saved with consent. First state the exact short detail you propose to
remember. Then ask: "Would you like me to remember that for your next call?" In Hindi
ask: "क्या आप चाहेंगे कि मैं यह बात आपकी अगली कॉल के लिए याद रखूँ?" Wait for their
answer. If they explicitly agree, call save_caller_memory before saying goodbye. If
they refuse, say that you will not save it before saying goodbye. If they do not answer
clearly, do not save anything; ask once for yes or no. Do not ask again when nothing
useful was learned or when the caller already answered this consent question.

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
tool succeeds. When both the customer name and amount are supplied, call the tool
immediately using the caller's exact words; do not ask them to repeat, spell, or
reconfirm those details before the tool call.

STYLE
Sound calm, patient, and practical. Prefer one or two short sentences at a time, with
no markdown, bullets, brackets, emojis, or sentences longer than about 20 words. Ask
one question at a time. Let the user finish and handle pauses without rushing. If no
meaningful speech is detected, say once: "I'm here. Take your time, or tell me how I
can help with local products or orders." After a second failed attempt, say: "No
problem. We can try again whenever you're ready. Goodbye."""

FIRST_TURN_GREETING = (
    "नमस्ते! I'm Mitra, your local shopping assistant. I can help you find local "
    "products, check listed prices, or prepare order requests. How may I help?"
)

OUTBOUND_CALL_PROMPT = """IDENTITY
You are Mitra, an AI calling assistant for a local-commerce marketplace. You are on
an outbound call solely to confirm the order details supplied in the call context.

RULES
- Clearly identify yourself as an AI assistant, explain the order-confirmation reason,
  and explain that the customer can say "stop" to prevent future calls.
- Never invent or change the customer, order, items, or delivery window.
- Confirmation has two mandatory, separate steps. First read every item and ask whether
  the item list is correct. Only after an explicit yes, call confirm_order_items.
- Then state the delivery window and ask whether that delivery window is acceptable.
  Only after a second explicit yes, call confirm_delivery_window.
- Never combine the two questions or treat one yes as approval for both steps.
- Only after confirm_delivery_window succeeds, say the order is confirmed and end politely.
- If the customer says stop, do not continue the order conversation. Acknowledge the
  opt-out, say there will be no automatic retry, and end politely.
- If the customer declines or sounds uncertain, acknowledge it without persuasion.
- Never ask for payment details, an OTP, PIN, password, or bank information.
- Use one or two short spoken sentences at a time with no markdown or bullet points.
"""

HINDI_SCRIPT_RANGE = range(0x0900, 0x0980)
ROMANIZED_HINDI_WORDS = {
    "aap",
    "aapke",
    "acha",
    "achha",
    "chahiye",
    "doodh",
    "ghar",
    "hai",
    "hain",
    "ka",
    "ke",
    "ki",
    "kya",
    "liye",
    "main",
    "mein",
    "mujhe",
    "nahi",
    "namaste",
    "paas",
    "rupaye",
}


def _response_language(message: str) -> str:
    """Classify the current utterance for strict English/Hindi response routing."""
    if any(ord(character) in HINDI_SCRIPT_RANGE for character in message):
        return "Hindi"
    words = {word.strip(".,!?;:'\"()[]{}").casefold() for word in message.split()}
    if len(words & ROMANIZED_HINDI_WORDS) >= 2:
        return "Hindi"
    return "English"


def _returning_caller_greeting(memory: CallerMemory) -> str:
    last_conversation = memory.facts.get("last_conversation")
    recent_order = memory.facts.get("recent_order")
    context = last_conversation or recent_order
    if memory.language_preference.casefold() == "hindi":
        if context:
            return (
                f"नमस्ते, {memory.name}। पिछली बार हम {context} पर बात कर रहे थे। "
                "क्या हम वहीं से आगे बढ़ें?"
            )
        return f"नमस्ते, {memory.name}। आपका फिर से स्वागत है। आज मैं कैसे मदद करूँ?"
    if context:
        return (
            f"नमस्ते, {memory.name}. Last time we were discussing {context}. "
            "Would you like to continue from there?"
        )
    return (
        f"नमस्ते, {memory.name}. Welcome back. How can I help with local shopping today?"
    )


BUSINESS_INVENTORY = {
    "mustard oil": {"quantity": 15, "unit": "liters"},
}

INVENTORY_ALIASES = {
    "sarson ka tel": "mustard oil",
    "sarso ka tel": "mustard oil",
    "सरसों का तेल": "mustard oil",
    "सरसो का तेल": "mustard oil",
    "sarson": "mustard oil",
    "sarso": "mustard oil",
    "सरसों": "mustard oil",
    "सरसो": "mustard oil",
}

CATALOGUE_ALIASES = {
    "bluetooth speaker": "bluetooth speaker",
    "aam ka achaar": "mango pickle",
    "aam ka achar": "mango pickle",
    "आम का अचार": "mango pickle",
    "sajawati cheez": "handicrafts",
    "sajawati chiz": "handicrafts",
    "sajawti cheez": "handicrafts",
    "sajawti chiz": "handicrafts",
    "सजावटी चीज़": "handicrafts",
    "सजावटी चीज": "handicrafts",
    "achaar": "pickle",
    "achar": "pickle",
    "अचार": "pickle",
    "ब्लूटूथ स्पीकर": "bluetooth speaker",
    "ब्लूटूथ speaker": "bluetooth speaker",
}


def _matching_alias(value: str, aliases: dict[str, str]) -> str | None:
    normalized = " ".join(value.casefold().strip().split())
    for alias in sorted(aliases, key=len, reverse=True):
        if alias in normalized:
            return aliases[alias]
    return None


def _normalize_inventory_name(product_name: str) -> str:
    return (
        _matching_alias(product_name, INVENTORY_ALIASES)
        or product_name.casefold().strip()
    )


def _normalize_catalogue_query(query: str) -> str:
    return _matching_alias(query, CATALOGUE_ALIASES) or query.casefold().strip()


class Assistant(Agent):
    def __init__(
        self,
        caller_id: str = "test-caller",
        memory_store: CallerMemoryStore | None = None,
        knowledge_base: KnowledgeBase | None = None,
        catalogue_provider: Callable[[], Catalogue] | None = None,
        instructions: str = SYSTEM_PROMPT,
        outbound_context: dict | None = None,
    ) -> None:
        super().__init__(instructions=instructions)
        self.caller_id = caller_id
        database_path = os.getenv("CALLER_MEMORY_DB")
        self.memory_store = memory_store or (
            CallerMemoryStore(database_path) if database_path else CallerMemoryStore()
        )
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.catalogue_provider = catalogue_provider
        self.outbound_context = outbound_context
        self.outbound_items_confirmed = False
        self.orders: list[dict[str, str | int]] = []
        self.credit_entries: list[dict[str, str | int]] = []

    @function_tool
    async def confirm_order_items(self, context: RunContext) -> str:
        """Record the first explicit yes confirming the complete outbound item list."""
        del context
        if not self.outbound_context:
            return "Item confirmation is only available during an outbound order call."
        self.outbound_items_confirmed = True
        return (
            "The item list is confirmed. Now state the delivery window and ask the "
            "customer to confirm that window in a separate question."
        )

    @function_tool
    async def confirm_delivery_window(self, context: RunContext) -> str:
        """Confirm delivery after items and delivery each received a separate yes."""
        del context
        if not self.outbound_context:
            return (
                "Delivery confirmation is only available during an outbound order call."
            )
        if not self.outbound_items_confirmed:
            return "Do not confirm the order: the item list has not been confirmed yet."
        order_id = str(self.outbound_context.get("orderId", "")).strip()
        callback_url = os.getenv(
            "OUTBOUND_CALLBACK_URL",
            "http://127.0.0.1:3000/api/outbound-call/outcome",
        )
        api_secret = os.getenv("LIVEKIT_API_SECRET", "")

        def notify_frontend() -> None:
            request = urllib.request.Request(
                callback_url,
                data=json.dumps({"orderId": order_id}).encode(),
                headers={
                    "Authorization": f"Bearer {api_secret}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"Outcome callback returned {response.status}")

        try:
            await asyncio.to_thread(notify_frontend)
        except (OSError, RuntimeError, urllib.error.URLError) as error:
            logger.error(
                "Failed to publish confirmation for order %s: %s", order_id, error
            )
            return (
                "The delivery was accepted, but the confirmation could not be recorded. "
                "Apologize and do not claim the order is confirmed."
            )
        logger.info("Outbound order %s confirmed after both approvals", order_id)
        return (
            f"Order {order_id} is confirmed. Tell the customer it is confirmed, repeat "
            "the delivery window, thank them, and end politely."
        )

    async def _catalogue(self):
        if self.catalogue_provider is not None:
            return await asyncio.to_thread(self.catalogue_provider)
        url = os.getenv("CATALOGUE_API_URL", "http://127.0.0.1:8001/catalogue")
        return await asyncio.to_thread(fetch_catalogue, url)

    def llm_node(self, chat_ctx, tools, model_settings):
        """Route every generated response using the latest user's language."""
        routed_ctx = chat_ctx.copy()
        user_message = next(
            (
                message
                for message in reversed(routed_ctx.messages())
                if message.role == "user"
            ),
            None,
        )
        if user_message is None:
            return super().llm_node(routed_ctx, tools, model_settings)

        language = _response_language(user_message.text_content)
        if language == "Hindi":
            directive = (
                "For this response, reply only in natural Hindi written in "
                "Devanagari. Keep only product names, brands, IDs, and unavoidable "
                "technical terms in English. Do not use Romanized Hindi."
            )
        else:
            directive = (
                "For this response, reply only in English. Do not include Hindi "
                "words, Romanized Hindi, or Devanagari text, except that the greeting "
                "Namaste must always be written as नमस्ते."
            )
        user_message.content.append(f"[LANGUAGE INSTRUCTION: {directive}]")
        normalized_message = user_message.text_content.casefold()
        if any(
            phrase in normalized_message
            for phrase in (
                "remember my",
                "remember this",
                "save my details",
                "save this",
            )
        ):
            user_message.content.append(
                "[MEMORY INSTRUCTION: The user explicitly requested that the supplied "
                "details be remembered. This is explicit consent. Call "
                "save_caller_memory now with consent_given=true. Do not ask for "
                "confirmation again and do not merely promise to remember.]"
            )
        return super().llm_node(routed_ctx, tools, model_settings)

    @function_tool
    async def lookup_caller(self, context: RunContext) -> str:
        """Look up the current caller's saved profile and shopping preferences."""
        del context
        memory = self.memory_store.lookup(self.caller_id)
        if memory is None:
            return "No saved memory was found for this caller."
        facts = ", ".join(
            f"{key.replace('_', ' ')}: {value}" for key, value in memory.facts.items()
        )
        return (
            f"Returning caller: {memory.name}. Language preference: "
            f"{memory.language_preference}. Saved facts: {facts or 'none'}."
        )

    @function_tool
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        consent_given: bool,
        district: str = "",
        recent_order: str = "",
        last_conversation: str = "",
        usual_quantity: str = "",
        preferred_delivery_slot: str = "",
    ) -> str:
        """Persist caller details after explicit consent so future calls can use them.

        Call this tool immediately when the caller accepts a stated memory proposal,
        or when they explicitly ask to remember/save the exact details they supplied.
        Do not claim details were remembered unless this tool returns success.

        Args:
            name: The caller's name.
            language_preference: Language the caller prefers.
            consent_given: True only after an explicit yes to saving these facts.
            district: Caller district useful for local product discovery and delivery.
            recent_order: A recent product or order useful on the next call.
            last_conversation: Short summary the caller agreed to resume next time.
            usual_quantity: The caller's usual product quantity.
            preferred_delivery_slot: The caller's preferred delivery time.
        """
        del context
        facts = {
            "district": district.strip(),
            "recent_order": recent_order.strip(),
            "last_conversation": last_conversation.strip(),
            "usual_quantity": usual_quantity.strip(),
            "preferred_delivery_slot": preferred_delivery_slot.strip(),
        }
        saved = self.memory_store.save(
            user_id=self.caller_id,
            name=name,
            language_preference=language_preference,
            facts=facts,
            consent_given=consent_given,
        )
        if not consent_given:
            return "Memory not saved: the caller did not explicitly consent."
        if not saved:
            return "Memory not saved: a caller name is required."
        logger.info("Saved caller memory for participant %s", self.caller_id)
        return "Caller memory saved. It will be available on their next call."

    @function_tool
    async def forget_caller(self, context: RunContext) -> str:
        """Delete all saved memory for the current caller when they ask to forget it."""
        del context
        forgotten = self.memory_store.forget(self.caller_id)
        if forgotten:
            return "Your saved caller record was deleted. I no longer remember you."
        return "No saved caller record existed, so there was nothing to delete."

    @function_tool
    async def search_knowledge_base(self, context: RunContext, query: str) -> str:
        """Retrieve source-labelled passages for knowledge and guidance questions.

        Args:
            query: The caller's question about schemes, farming, or learning material.
        """
        del context
        return self.knowledge_base.grounded_context(query)

    @function_tool
    async def check_inventory(self, context: RunContext, product_name: str) -> str:
        """Check the shop's current stock for a product.

        Args:
            product_name: Product to look up, such as mustard oil.
        """
        del context
        normalized_name = _normalize_inventory_name(product_name)
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
    async def search_catalogue(
        self,
        context: RunContext,
        query: str = "",
        category: str = "",
        max_price: int | None = None,
    ) -> str:
        """Fetch authoritative product information from the local catalogue.

        Call this tool whenever a customer asks about product availability, price,
        stock, products in a category, or products within a budget. Do not answer
        product, price, or stock questions from memory. Use the returned catalogue
        data as the source of truth. Results include price, unit, stock,
        availability, seller, and the catalogue's last-updated timestamp.

        Args:
            query: Product name, seller, item ID, or general search text. May be empty
                when category is supplied.
            category: Optional category such as dairy, bakery, food, or textiles.
            max_price: Optional maximum listed unit price in Indian rupees.
        """
        del context
        if max_price is not None and max_price < 0:
            return "The maximum price must be zero or greater."
        try:
            catalogue = await self._catalogue()
        except CatalogueUnavailableError as exc:
            logger.exception("Catalogue lookup failed")
            return str(exc)
        normalized_query = _normalize_catalogue_query(query)
        matches = search_products(
            catalogue,
            query=normalized_query,
            category=category,
            max_price=max_price,
        )
        if not matches:
            return (
                "No matching products were found in the local catalogue. "
                f"Catalogue last updated: {catalogue.updated_at}."
            )

        results = "\n".join(
            f"{item.product_id}: {item.name} by {item.seller}; "
            f"INR {item.price_inr} per {item.unit}; stock {item.stock_quantity}; "
            f"available: {'yes' if item.available else 'no'}; "
            f"catalogue last updated: {catalogue.updated_at}"
            for item in matches
        )
        return (
            f"{results}\nThis is a catalogue snapshot; the seller must confirm "
            "the final price and availability."
        )

    @function_tool
    async def calculate_order_total(
        self,
        context: RunContext,
        product_ids: list[str],
        quantities: list[int],
    ) -> str:
        """Calculate an order total using authoritative local catalogue prices.

        Call this tool whenever a customer asks how much one or more requested
        products will cost. Do not calculate catalogue order totals manually. The
        tool validates product IDs, positive quantities, and available stock, then
        returns line subtotals, the final INR total, and catalogue timestamp.

        Args:
            product_ids: Catalogue product IDs in order, such as DAI-101 and BAK-201.
            quantities: Requested quantity corresponding to each product ID.
        """
        del context
        try:
            result = calculate_total(await self._catalogue(), product_ids, quantities)
        except CatalogueUnavailableError as exc:
            logger.exception("Order total catalogue lookup failed")
            return str(exc)
        except ValueError as exc:
            return f"The order total could not be calculated: {exc}"

        line_results = [
            f"{line.quantity} x {line.name} at INR {line.unit_price_inr} "
            f"= INR {line.subtotal_inr}"
            for line in result.lines
        ]
        line_results.append(f"Order total = INR {result.total_inr}")
        line_results.append(f"Catalogue last updated: {result.updated_at}")
        return "\n".join(line_results)

    @staticmethod
    def _catalogue_search_text(item: CatalogueItem) -> str:
        return f"{item.product_id} {item.name} {item.seller} {item.category}".casefold()

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
        try:
            catalogue = await self._catalogue()
        except CatalogueUnavailableError as exc:
            logger.exception("Order creation catalogue lookup failed")
            return str(exc)
        item = next(
            (
                product
                for product in catalogue.products
                if product.product_id == item_id.upper()
            ),
            None,
        )
        if item is None:
            return "Order not created: item ID is not in the catalogue."
        if quantity < 1 or quantity > item.stock_quantity:
            return (
                f"Order not created: choose between 1 and {item.stock_quantity} units."
            )

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
                "item_id": item.product_id,
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


@server.rtc_session(agent_name="mitra")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Connect first so the participant identity can key persistent caller memory.
    await ctx.connect()
    participant = await ctx.wait_for_participant()
    outbound_context = None
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        try:
            metadata = json.loads(participant.metadata or "{}")
            if metadata.get("type") == "outbound_order_confirmation":
                outbound_context = metadata
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Invalid outbound SIP participant metadata")
        if outbound_context is None and os.getenv("ORDER_ID"):
            outbound_context = {
                "type": "outbound_order_confirmation",
                "customerName": os.getenv("ORDER_CUSTOMER_NAME", "Customer"),
                "orderId": os.getenv("ORDER_ID", ""),
                "orderItems": [
                    item.strip()
                    for item in os.getenv("ORDER_ITEMS", "").split("|")
                    if item.strip()
                ],
                "orderTotal": os.getenv("ORDER_TOTAL_INR", ""),
                "deliveryTime": os.getenv("ORDER_DELIVERY_TIME", ""),
            }
    assistant = Assistant(
        caller_id=participant.identity,
        outbound_context=outbound_context,
        instructions=(
            f"{OUTBOUND_CALL_PROMPT}\n\nCALL CONTEXT\n"
            f"Customer: {outbound_context.get('customerName')}\n"
            f"Order ID: {outbound_context.get('orderId')}\n"
            f"Items: {', '.join(outbound_context.get('orderItems', []))}\n"
            f"Total: INR {outbound_context.get('orderTotal')}\n"
            f"Delivery: {outbound_context.get('deliveryTime')}"
            if outbound_context
            else SYSTEM_PROMPT
        ),
    )
    caller_memory = assistant.memory_store.lookup(participant.identity)

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
        agent=assistant,
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

    if outbound_context:
        greeting = (
            "Hi, this is Mitra, an AI calling assistant from FreshMart. "
            "I'm calling to confirm your grocery order scheduled for delivery today. "
            "If you don't want to receive calls like this, just say stop at any time. "
            f"The order contains {', '.join(outbound_context['orderItems'])}. "
            f"The complete order total is INR {outbound_context['orderTotal']}. "
            "Are all of these items correct?"
        )
        logger.info(
            "Outbound conversation started for order %s", outbound_context["orderId"]
        )
    else:
        greeting = (
            _returning_caller_greeting(caller_memory)
            if caller_memory is not None
            else FIRST_TURN_GREETING
        )
    await session.say(greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
