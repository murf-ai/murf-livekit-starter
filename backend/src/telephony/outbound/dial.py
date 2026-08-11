"""Dispatch the outbound agent to call a number (Day 6).

Worker must already be running:

    uv run python src/telephony/outbound/agent.py dev

Then dial (Twilio E.164 or Linphone username):

    uv run python src/telephony/outbound/dial.py --to +9198XXXXXXXX \\
      --name Ramesh --scheme pmsby --lang hi

    uv run python src/telephony/outbound/dial.py --to your_linphone_user \\
      --name Ramesh --scheme pmsby --lang hi
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from livekit import api

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_ROOT / ".env.local")
load_dotenv(_SRC_ROOT / "test" / ".env.local", override=True)
load_dotenv(".env.local")

AGENT_NAME = "outbound-agent"
E164 = re.compile(r"^\+[1-9]\d{6,14}$")
DEFAULT_TO = os.getenv("LINPHONE_SIP_URI", "sip:pratay@sip.linphone.org")


async def dial(
    phone_number: str,
    room_name: str,
    *,
    name: str,
    scheme: str,
    lang: str,
    eligible: bool,
) -> None:
    metadata = {
        "phone_number": phone_number,
        "caller_name": name,
        "scheme": scheme,
        "language": lang,
        "previously_eligible": eligible,
        "purpose": "scheme_deadline_reminder",
    }
    lk = api.LiveKitAPI()
    try:
        await lk.room.create_room(api.CreateRoomRequest(name=room_name))
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
    finally:
        await lk.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Place an outbound scheme-deadline reminder call."
    )
    parser.add_argument(
        "--to",
        default=DEFAULT_TO,
        help="E.164 (+91…), Linphone username, or sip:user@host "
        f"(default from LINPHONE_SIP_URI: {DEFAULT_TO})",
    )
    parser.add_argument("--room", default=None, help="Optional room name")
    parser.add_argument("--name", default="Caller", help="Callee display name")
    parser.add_argument(
        "--scheme",
        default="pmsby",
        help="Scheme code: pmsby | pmjjby | apy | pmjdy",
    )
    parser.add_argument(
        "--lang", default="hi", choices=["hi", "en"], help="Call language"
    )
    parser.add_argument(
        "--not-eligible",
        action="store_true",
        help="Do not treat as previously eligible",
    )
    args = parser.parse_args()

    target = args.to.strip()
    if target.startswith("sip:"):
        target = target[4:]
    if "@" in target:
        target = target.split("@", 1)[0]
    if not E164.match(target) and not re.match(r"^[\w.-]+$", target):
        sys.exit(f"'{args.to}' is not E.164 (+…) or a simple Linphone username.")

    eligible = not args.not_eligible
    room_name = args.room or f"outbound-{uuid.uuid4().hex[:8]}"

    asyncio.run(
        dial(
            target,
            room_name,
            name=args.name,
            scheme=args.scheme,
            lang=args.lang,
            eligible=eligible,
        )
    )
    print(f"Dispatched {AGENT_NAME} → room '{room_name}' calling {target}")
    print(
        f"  name={args.name} scheme={args.scheme} lang={args.lang} "
        f"previously_eligible={eligible}"
    )
    print("Watch the worker terminal for call progress.")


if __name__ == "__main__":
    main()
