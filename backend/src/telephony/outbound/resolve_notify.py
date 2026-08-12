"""Day 7 — Resolve an escalation ticket and notify the caller via Linphone/SIP.

Flow:
  1. Mark the case resolved (status tracking).
  2. Build a PII-scrubbed callback payload.
  3. Dispatch the outbound worker with purpose=escalation_resolution
     so Jan Sahay places a mobile SIP call (Linphone or Twilio).

Prerequisites:
  - Outbound worker running:
        uv run python src/telephony/outbound/agent.py dev
  - LIVEKIT_SIP_OUTBOUND_TRUNK_ID set (Linphone trunk recommended for mobile)

Examples:
  uv run python src/telephony/outbound/resolve_notify.py \\
      --ref JS-A1B2C3D4 --to pratay \\
      --notes "Specialist verified no further unauthorized activity."

  uv run python src/telephony/outbound/resolve_notify.py \\
      --ref JS-A1B2C3D4 --to sip:pratay@sip.linphone.org --lang hi
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

# Make backend/src importable when run as a script.
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import escalation  # noqa: E402

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_BACKEND_ROOT / ".env.local", override=True)
load_dotenv(_SRC / "test" / ".env.local", override=True)
load_dotenv(".env.local", override=True)

AGENT_NAME = "outbound-agent"
E164 = re.compile(r"^\+[1-9]\d{6,14}$")
DEFAULT_TO = os.getenv("LINPHONE_SIP_URI", "sip:pratay@sip.linphone.org")


def _normalize_sip_target(raw: str) -> str:
    """Accept E.164, bare Linphone username, or sip:user@host → dial target."""
    target = (raw or "").strip()
    if target.startswith("sip:"):
        target = target[4:]
    if "@" in target:
        target = target.split("@", 1)[0]
    return target


async def dispatch_resolution_call(
    *,
    phone_number: str,
    room_name: str,
    callback: dict,
) -> None:
    """Create a LiveKit room and dispatch outbound-agent for resolution notify."""
    metadata = {
        "phone_number": phone_number,
        "caller_name": callback.get("caller_name") or "Caller",
        "language": callback.get("language") or "hi",
        "purpose": "escalation_resolution",
        "reference_id": callback.get("reference_id"),
        "resolution_notes": callback.get("resolution_notes") or "",
        "issue_description": callback.get("issue_description") or "",
        "follow_up_method": callback.get("follow_up_method") or "voice_callback",
        "user_id": callback.get("user_id"),
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
        description=(
            "Resolve a Jan Sahay escalation and notify the caller via "
            "Linphone / SIP outbound."
        )
    )
    parser.add_argument(
        "--ref",
        "--reference-id",
        dest="reference_id",
        required=True,
        help="Escalation reference ID (e.g. JS-A1B2C3D4)",
    )
    parser.add_argument(
        "--to",
        default=DEFAULT_TO,
        help=(
            "E.164, Linphone username, or sip:user@host "
            f"(default LINPHONE_SIP_URI: {DEFAULT_TO})"
        ),
    )
    parser.add_argument(
        "--notes",
        default="Your case has been reviewed by a specialist.",
        help="Resolution notes (PII-scrubbed before storage / speech)",
    )
    parser.add_argument(
        "--lang",
        default=None,
        choices=["hi", "en"],
        help="Override call language (default: ticket preferred_language)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the ticket but do not place the SIP call",
    )
    parser.add_argument("--room", default=None, help="Optional LiveKit room name")
    args = parser.parse_args()

    result = escalation.resolve_and_prepare_callback(
        args.reference_id,
        resolution_notes=args.notes,
    )
    if not result.get("ok"):
        sys.exit(result.get("message") or "Failed to resolve escalation.")

    callback = dict(result["callback"])
    if args.lang:
        callback["language"] = args.lang

    ref = callback["reference_id"]
    print(f"Resolved {ref} → status=resolved")
    print(f"  caller={callback.get('caller_name')} lang={callback.get('language')}")
    print(f"  notes={callback.get('resolution_notes')}")

    if args.dry_run:
        print("Dry-run: skipping Linphone / SIP dispatch.")
        print(json.dumps({"callback": callback}, indent=2, ensure_ascii=False))
        return

    target = _normalize_sip_target(args.to)
    if not E164.match(target) and not re.match(r"^[\w.-]+$", target):
        sys.exit(f"'{args.to}' is not E.164 (+…) or a simple Linphone username.")

    room_name = args.room or f"escalation-resolve-{uuid.uuid4().hex[:8]}"
    asyncio.run(
        dispatch_resolution_call(
            phone_number=target,
            room_name=room_name,
            callback=callback,
        )
    )
    escalation.mark_callback_dispatched(ref)
    print(f"Dispatched {AGENT_NAME} → room '{room_name}' calling {target}")
    print("  purpose=escalation_resolution (Day 7 Linphone mobile notify)")
    print("Watch the outbound worker terminal for call progress.")


if __name__ == "__main__":
    main()
