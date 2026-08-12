"""Dispatch the outbound agent to call a number (Day 6 + Day 7).

Worker must already be running:

    uv run python src/telephony/outbound/agent.py dev

Day 6 — scheme deadline reminder (Twilio E.164 or Linphone username):

    uv run python src/telephony/outbound/dial.py --to +9198XXXXXXXX \\
      --name Ramesh --scheme pmsby --lang hi

    uv run python src/telephony/outbound/dial.py --to your_linphone_user \\
      --name Ramesh --scheme pmsby --lang hi

Day 7 — escalation resolution callback (prefer resolve_notify.py):

    uv run python src/telephony/outbound/dial.py --to your_linphone_user \\
      --purpose escalation_resolution --ref JS-A1B2C3D4 \\
      --name Ramesh --lang hi --notes "Specialist closed your fraud review."
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
VALID_PURPOSES = frozenset({"scheme_deadline_reminder", "escalation_resolution"})


def _normalize_sip_target(raw: str) -> str:
    target = (raw or "").strip()
    if target.startswith("sip:"):
        target = target[4:]
    if "@" in target:
        target = target.split("@", 1)[0]
    return target


async def dial(
    phone_number: str,
    room_name: str,
    *,
    name: str,
    scheme: str,
    lang: str,
    eligible: bool,
    purpose: str = "scheme_deadline_reminder",
    reference_id: str | None = None,
    resolution_notes: str | None = None,
    issue_description: str | None = None,
) -> None:
    metadata: dict = {
        "phone_number": phone_number,
        "caller_name": name,
        "language": lang,
        "purpose": purpose,
    }
    if purpose == "scheme_deadline_reminder":
        metadata["scheme"] = scheme
        metadata["previously_eligible"] = eligible
    else:
        metadata["reference_id"] = reference_id
        metadata["resolution_notes"] = resolution_notes or ""
        metadata["issue_description"] = issue_description or ""
        metadata["follow_up_method"] = "voice_callback"

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
        description=(
            "Place an outbound call: scheme deadline (Day 6) or "
            "escalation resolution notify (Day 7 / Linphone)."
        )
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
        help="Scheme code: pmsby | pmjjby | apy | pmjdy (Day 6)",
    )
    parser.add_argument(
        "--lang", default="hi", choices=["hi", "en"], help="Call language"
    )
    parser.add_argument(
        "--not-eligible",
        action="store_true",
        help="Do not treat as previously eligible (Day 6)",
    )
    parser.add_argument(
        "--purpose",
        default="scheme_deadline_reminder",
        choices=sorted(VALID_PURPOSES),
        help="Call purpose (default: scheme_deadline_reminder)",
    )
    parser.add_argument(
        "--ref",
        "--reference-id",
        dest="reference_id",
        default=None,
        help="Escalation reference ID (required for escalation_resolution)",
    )
    parser.add_argument(
        "--notes",
        default="Your case has been reviewed by a specialist.",
        help="Resolution notes for escalation_resolution calls",
    )
    parser.add_argument(
        "--issue",
        default="",
        help="Optional scrubbed issue description for resolution calls",
    )
    args = parser.parse_args()

    if args.purpose == "escalation_resolution" and not args.reference_id:
        sys.exit("--ref / --reference-id is required for escalation_resolution.")

    target = _normalize_sip_target(args.to)
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
            purpose=args.purpose,
            reference_id=args.reference_id,
            resolution_notes=args.notes,
            issue_description=args.issue,
        )
    )
    print(f"Dispatched {AGENT_NAME} → room '{room_name}' calling {target}")
    print(
        f"  purpose={args.purpose} name={args.name} lang={args.lang}"
        + (
            f" ref={args.reference_id}"
            if args.purpose == "escalation_resolution"
            else f" scheme={args.scheme} previously_eligible={eligible}"
        )
    )
    print("Watch the worker terminal for call progress.")


if __name__ == "__main__":
    main()
