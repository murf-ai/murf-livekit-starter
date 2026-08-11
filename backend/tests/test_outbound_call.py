import pytest

from outbound_call import CallLifecycle, CallState, OutboundCallRequest, TwilioConfig

TWILIO_ENV = {
    "TWILIO_ACCOUNT_SID": "AC00000000000000000000000000000000",
    "TWILIO_AUTH_TOKEN": "secret",
    "TWILIO_PHONE_NUMBER": "+14155550100",
    "TWILIO_TO_NUMBER": "+919999999999",
    "PUBLIC_BASE_URL": "https://example.test",
    "LIVEKIT_SIP_URI": "sip:project@sip.livekit.cloud",
}


def test_twilio_configuration_validation(monkeypatch):
    for name, value in TWILIO_ENV.items():
        monkeypatch.setenv(name, value)
    config = TwilioConfig.from_env()
    assert config.to_number == "+919999999999"


def test_missing_twilio_credentials_have_clear_error(monkeypatch):
    for name in TWILIO_ENV:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match=r"TWILIO_ACCOUNT_SID.*TWILIO_AUTH_TOKEN"):
        TwilioConfig.from_env()


def test_invalid_twilio_phone_number(monkeypatch):
    for name, value in TWILIO_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("TWILIO_TO_NUMBER", "8423896052")
    with pytest.raises(ValueError, match=r"E\.164"):
        TwilioConfig.from_env()


def test_outbound_call_request_validation():
    OutboundCallRequest(
        customer_name="Shivam",
        order_id="ORD-1001",
        order_items=("1 litre milk",),
        delivery_time="Today, 6 PM-8 PM",
    ).validate()


def test_outbound_call_request_rejects_missing_items():
    with pytest.raises(ValueError, match="order_items"):
        OutboundCallRequest("Shivam", "ORD-1", (), "Today").validate()


@pytest.mark.parametrize(
    "path",
    [
        [CallState.RINGING, CallState.NO_ANSWER],
        [CallState.RINGING, CallState.BUSY],
        [CallState.RINGING, CallState.VOICEMAIL],
        [CallState.RINGING, CallState.USER_HANGUP],
        [
            CallState.RINGING,
            CallState.ANSWERED,
            CallState.CONNECTING_TO_AGENT,
            CallState.CONNECTED,
            CallState.IN_PROGRESS,
            CallState.OPTED_OUT,
        ],
        [
            CallState.RINGING,
            CallState.ANSWERED,
            CallState.CONNECTING_TO_AGENT,
            CallState.CONNECTED,
            CallState.IN_PROGRESS,
            CallState.COMPLETED,
        ],
    ],
)
def test_call_outcomes(path):
    lifecycle = CallLifecycle()
    for state in path:
        lifecycle.transition(state)
    assert lifecycle.state is path[-1]


def test_terminal_state_cannot_retry_automatically():
    lifecycle = CallLifecycle()
    lifecycle.transition(CallState.RINGING)
    lifecycle.transition(CallState.NO_ANSWER)
    with pytest.raises(ValueError, match="already terminal"):
        lifecycle.transition(CallState.RINGING)
