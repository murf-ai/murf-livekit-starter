"""Trigger an outbound call via Dhan Rakshak's outbound agent.

The outbound agent does NOT call anyone on its own — it waits to be dispatched
into a room with a phone number attached. This script does the dispatching.

Make sure the worker is running first:
    uv run python src/telephony/outbound/agent.py dev

Then place a call (Linphone SIP username, e.g. 'abhiram05'):
    uv run python src/telephony/outbound/dial.py --to abhiram05

For a real phone number (E.164 format):
    uv run python src/telephony/outbound/dial.py --to +15551234567
"""

import argparse
import asyncio
import json
import re
import sys
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

# Must match the agent_name in agent.py
AGENT_NAME = "dhan-rakshak-outbound"

# E.164 format: e.g. +15551234567
E164 = re.compile(r"^\+[1-9]\d{6,14}$")

# Linphone SIP format: e.g. abhiram05 (will be formatted as sip:username@sip.linphone.org)
LINPHONE_DOMAIN = "sip.linphone.org"


def format_sip_target(to: str) -> str:
    """
    Accepts either:
      - A raw Linphone username: e.g. 'abhiram05'  → 'sip:abhiram05@sip.linphone.org'
      - A full SIP URI:          e.g. 'sip:user@domain'  → passed through unchanged
      - An E.164 phone number:   e.g. '+15551234567'     → passed through unchanged
    """
    if to.startswith("sip:"):
        return to
    if E164.match(to):
        return to
    # Assume it's a Linphone username
    return f"sip:{to}@{LINPHONE_DOMAIN}"


async def dial(sip_target: str, room_name: str) -> None:
    """Create the room and dispatch the outbound agent into it."""
    lk = api.LiveKitAPI()
    try:
        # Create the room
        await lk.room.create_room(api.CreateRoomRequest(name=room_name))
        print(f"Room '{room_name}' created.")

        # Dispatch the agent with the SIP target in metadata
        dispatch = await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps({"phone_number": sip_target}),
            )
        )
        print(f"Agent dispatched: {dispatch.agent_name} → room '{room_name}'")
        print(f"Calling:          {sip_target}")
        print("Waiting for the call to be answered...")
    finally:
        await lk.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place an outbound call with the Dhan Rakshak agent.",
        epilog=(
            "Examples:\n"
            "  uv run python src/telephony/outbound/dial.py --to abhiram05\n"
            "  uv run python src/telephony/outbound/dial.py --to +91XXXXXXXXXX\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--to",
        required=True,
        metavar="LINPHONE_USER_OR_NUMBER",
        help="Linphone username (e.g. abhiram05) or E.164 phone number (e.g. +91XXXXXXXXXX)",
    )
    parser.add_argument(
        "--room",
        default=None,
        metavar="ROOM_NAME",
        help="LiveKit room name (auto-generated if not specified)",
    )

    args = parser.parse_args()
    sip_target = format_sip_target(args.to)
    room_name = args.room or f"outbound_call_room_{uuid.uuid4().hex[:8]}"

    print(f"SIP target : {sip_target}")
    print(f"Room name  : {room_name}")
    print()

    asyncio.run(dial(sip_target, room_name))


if __name__ == "__main__":
    main()
