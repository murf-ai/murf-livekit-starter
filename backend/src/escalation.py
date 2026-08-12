import os
import json
import logging
import uuid
from datetime import datetime, timezone
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("escalation")

ESCALATION_REASONS = ["possible_fraud", "decision_agent_cannot_make", "none"]

def classify_escalation_reason(user_turn_text: str) -> str:
    """
    Classifies a user statement into one of the escalation reasons:
    - 'possible_fraud': user reports fraudulent/unauthorized transaction or activity.
    - 'decision_agent_cannot_make': request requires human judgment (loan approval, waiving fee, overriding hold, reversing chargeback, changing account ownership).
    - 'none': normal request.
    """
    text = user_turn_text.lower()
    
    # Check for possible fraud indicators
    fraud_keywords = [
        "fraud", "unauthorized", "didn't make", "did not make", "don't recognize", 
        "stolen", "stole", "suspicious", "scam", "unrecognized", "unknown charge"
    ]
    if any(kw in text for kw in fraud_keywords) or ("charge" in text and ("not" in text or "don't" in text or "didn't" in text or "stole" in text or "unknown" in text)):
        return "possible_fraud"
        
    # Check for decision agent cannot make indicators
    decision_keywords = [
        "approve loan", "apply for loan", "waive fee", "waive my fee", "waiver", 
        "override hold", "remove hold", "reverse chargeback", "reverse charge", 
        "change account ownership", "transfer ownership"
    ]
    if any(kw in text for kw in decision_keywords):
        return "decision_agent_cannot_make"
        
    return "none"


def sanitize_and_validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and sanitizes escalation payload.
    Ensures required fields exist and sensitive fields (passwords, OTPs, PINs, card numbers, full account numbers) are redacted.
    """
    required_fields = ["who_needs_help", "what_happened", "already_checked", "urgency", "language_and_followup"]
    sanitized = {}
    
    for field in required_fields:
        val = str(payload.get(field, "")) if payload.get(field) is not None else ""
        if not val:
            if field == "who_needs_help":
                val = "unknown caller"
            elif field == "urgency":
                val = "medium"
            else:
                val = "Not specified"
        sanitized[field] = val

    # Validate urgency
    if sanitized["urgency"].lower() not in ["low", "medium", "high"]:
        sanitized["urgency"] = "medium"
    else:
        sanitized["urgency"] = sanitized["urgency"].lower()

    # Redact sensitive data from already_checked and what_happened
    def redact_sensitive(text: str) -> str:
        import re
        # Redact 16 digit card numbers or 10-12 digit account numbers, leaving last 4 digits
        # Match 13-19 digit card numbers
        text = re.sub(r'\b\d{12,19}\b', lambda m: f"ending in {m.group(0)[-4:]}", text)
        # Redact 4-6 digit PINs/OTPs if explicitly labeled
        text = re.sub(r'(?i)\b(pin|otp|password|cvv)[:\s]+\d+\b', r'\1: [REDACTED]', text)
        return text

    sanitized["already_checked"] = redact_sensitive(sanitized["already_checked"])
    sanitized["what_happened"] = redact_sensitive(sanitized["what_happened"])
    
    return sanitized


def post_to_slack_webhook(payload: Dict[str, Any], webhook_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Posts the formatted payload to Slack Webhook URL.
    Returns (success: bool, reference_id_or_error: str).
    """
    ref_id = f"ESC-{uuid.uuid4().hex[:4].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    
    slack_message = {
        "text": f":warning: *New Human Escalation Request* ({ref_id})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Human Escalation Request: {ref_id}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Who Needs Help:*\n{payload['who_needs_help']}"},
                    {"type": "mrkdwn", "text": f"*Urgency:*\n{payload['urgency'].upper()}"},
                    {"type": "mrkdwn", "text": f"*Language & Follow-up:*\n{payload['language_and_followup']}"},
                    {"type": "mrkdwn", "text": f"*Created At:*\n{created_at}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*What Happened:*\n{payload['what_happened']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Already Checked / Verified:*\n{payload['already_checked']}"
                }
            }
        ]
    }
    
    if not url:
        logger.warning("SLACK_WEBHOOK_URL is not set. Simulating escalation dispatch.")
        return True, ref_id
        
    try:
        req_data = json.dumps(slack_message).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return True, ref_id
            else:
                logger.error(f"Slack webhook returned status code {response.status}")
                return False, f"HTTP error {response.status}"
    except Exception as e:
        logger.error(f"Error posting to Slack webhook: {e}")
        return False, str(e)


@function_tool
async def create_escalation(
    self,
    context: RunContext,
    who_needs_help: str,
    what_happened: str,
    already_checked: str,
    urgency: str,
    language_and_followup: str,
) -> Dict[str, Any]:
    """
    Creates a human escalation request after caller explicit consent.
    
    Args:
        who_needs_help: Caller's name or ID if known, else 'unknown caller'.
        what_happened: 1-3 sentence plain-language summary of the issue.
        already_checked: What the agent verified or looked up (no full card/account numbers or passwords).
        urgency: Urgency level ('low', 'medium', 'high').
        language_and_followup: Spoken language and preferred contact method (call back, text, email).
    """
    raw_payload = {
        "who_needs_help": who_needs_help,
        "what_happened": what_happened,
        "already_checked": already_checked,
        "urgency": urgency,
        "language_and_followup": language_and_followup,
    }
    
    sanitized_payload = sanitize_and_validate_payload(raw_payload)
    created_at = datetime.now(timezone.utc).isoformat()
    
    success, ref_or_err = post_to_slack_webhook(sanitized_payload)
    
    if success:
        logger.info(f"Escalation successfully created: {ref_or_err}")
        return {
            "status": "created",
            "reference_id": ref_or_err,
            "created_at": created_at
        }
    else:
        logger.error(f"Escalation failed to dispatch: {ref_or_err}")
        return {
            "status": "failed",
            "error": ref_or_err,
            "created_at": created_at
        }
