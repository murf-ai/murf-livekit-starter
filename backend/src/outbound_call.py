"""Configuration, validation, and state tracking for Twilio outbound calls."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class CallState(str, Enum):
    REQUESTED = "REQUESTED"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    CONNECTING_TO_AGENT = "CONNECTING_TO_AGENT"
    CONNECTED = "CONNECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    VOICEMAIL = "VOICEMAIL"
    FAILED = "FAILED"
    USER_HANGUP = "USER_HANGUP"
    OPTED_OUT = "OPTED_OUT"


TERMINAL_STATES = {
    CallState.COMPLETED,
    CallState.BUSY,
    CallState.NO_ANSWER,
    CallState.VOICEMAIL,
    CallState.FAILED,
    CallState.USER_HANGUP,
    CallState.OPTED_OUT,
}

ALLOWED_TRANSITIONS = {
    CallState.REQUESTED: {CallState.RINGING, CallState.FAILED},
    CallState.RINGING: {
        CallState.ANSWERED,
        CallState.BUSY,
        CallState.NO_ANSWER,
        CallState.VOICEMAIL,
        CallState.FAILED,
        CallState.USER_HANGUP,
    },
    CallState.ANSWERED: {
        CallState.CONNECTING_TO_AGENT,
        CallState.USER_HANGUP,
        CallState.FAILED,
    },
    CallState.CONNECTING_TO_AGENT: {
        CallState.CONNECTED,
        CallState.USER_HANGUP,
        CallState.FAILED,
    },
    CallState.CONNECTED: {
        CallState.IN_PROGRESS,
        CallState.USER_HANGUP,
        CallState.FAILED,
    },
    CallState.IN_PROGRESS: {
        CallState.COMPLETED,
        CallState.USER_HANGUP,
        CallState.OPTED_OUT,
        CallState.FAILED,
    },
}


@dataclass(frozen=True)
class TwilioConfig:
    account_sid: str
    auth_token: str
    phone_number: str
    to_number: str
    public_base_url: str
    livekit_sip_uri: str

    @classmethod
    def from_env(cls) -> TwilioConfig:
        names = (
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_PHONE_NUMBER",
            "TWILIO_TO_NUMBER",
            "PUBLIC_BASE_URL",
            "LIVEKIT_SIP_URI",
        )
        values = {name: os.getenv(name, "").strip() for name in names}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"Missing Twilio configuration: {', '.join(missing)}")
        for name in ("TWILIO_PHONE_NUMBER", "TWILIO_TO_NUMBER"):
            number = values[name]
            if not number.startswith("+") or not number[1:].isdigit():
                raise ValueError(f"{name} must be an international E.164 number")
        return cls(
            account_sid=values["TWILIO_ACCOUNT_SID"],
            auth_token=values["TWILIO_AUTH_TOKEN"],
            phone_number=values["TWILIO_PHONE_NUMBER"],
            to_number=values["TWILIO_TO_NUMBER"],
            public_base_url=values["PUBLIC_BASE_URL"],
            livekit_sip_uri=values["LIVEKIT_SIP_URI"],
        )


@dataclass(frozen=True)
class OutboundCallRequest:
    customer_name: str
    order_id: str
    order_items: tuple[str, ...]
    delivery_time: str

    def validate(self) -> None:
        required = {
            "customer_name": self.customer_name,
            "order_id": self.order_id,
            "delivery_time": self.delivery_time,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if not self.order_items:
            missing.append("order_items")
        if missing:
            raise ValueError(f"Missing outbound call fields: {', '.join(missing)}")


@dataclass
class CallLifecycle:
    state: CallState = CallState.REQUESTED

    def transition(self, next_state: CallState) -> None:
        if self.state in TERMINAL_STATES:
            raise ValueError(f"Call is already terminal: {self.state}")
        if next_state not in ALLOWED_TRANSITIONS.get(self.state, set()):
            raise ValueError(f"Invalid call transition: {self.state} -> {next_state}")
        self.state = next_state
