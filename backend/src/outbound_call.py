import asyncio
import os
import uuid

from dotenv import load_dotenv
from livekit import api

# Load variables from .env.local
load_dotenv(".env.local")

# LiveKit agent name
AGENT_NAME = "my-agent"

# LiveKit outbound SIP trunk ID
OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_TRUNK_ID")

# Linphone SIP destination
SIP_DESTINATION = os.getenv(
    "OUTBOUND_SIP_URI",
    "sip:yashdodiya@sip.linphone.org",
)


async def make_outbound_call():

    # --------------------------------------------------
    # Check configuration
    # --------------------------------------------------

    if not OUTBOUND_TRUNK_ID:
        raise ValueError(
            "LIVEKIT_SIP_TRUNK_ID is missing in .env.local"
        )

    if not SIP_DESTINATION:
        raise ValueError(
            "OUTBOUND_SIP_URI is missing in .env.local"
        )

    # --------------------------------------------------
    # Create a unique LiveKit room
    # --------------------------------------------------

    room_name = f"finance-outbound-{uuid.uuid4().hex[:8]}"

    lkapi = api.LiveKitAPI()

    try:

        print("Starting Finance outbound call...")
        print(f"Room: {room_name}")
        print(f"Calling SIP: {SIP_DESTINATION}")
        print(f"Trunk: {OUTBOUND_TRUNK_ID}")

        # --------------------------------------------------
        # Dispatch your existing AI agent
        # --------------------------------------------------

        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
            )
        )

        print("Agent dispatched successfully.")
        print(f"Dispatch: {dispatch}")

        # --------------------------------------------------
        # Create outbound SIP call
        # --------------------------------------------------

        participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=SIP_DESTINATION,
                room_name=room_name,
                participant_identity="finance-customer",
                participant_name="Finance Customer",
                wait_until_answered=True,
            )
        )

        print("")
        print("========================================")
        print("CALL CONNECTED SUCCESSFULLY")
        print("========================================")
        print(f"SIP destination: {SIP_DESTINATION}")
        print(f"Room: {room_name}")
        print(f"SIP participant: {participant}")
        print("========================================")

    except Exception as e:

        print("")
        print("========================================")
        print("OUTBOUND CALL FAILED")
        print("========================================")
        print(f"Error: {e}")
        print("========================================")

    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(make_outbound_call())