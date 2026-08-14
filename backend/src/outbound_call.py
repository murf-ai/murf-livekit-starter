import os
import asyncio
import logging
import sys
from dotenv import load_dotenv
from livekit import api

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("outbound_call")

async def main():
    # Load environment variables
    load_dotenv(".env.local")
    
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not url or not api_key or not api_secret:
        logger.error("LiveKit credentials not found in environment variables. Please check backend/.env.local")
        sys.exit(1)
        
    # Check for CLI arguments to override target SIP URI
    if len(sys.argv) > 1:
        sip_uri = sys.argv[1]
    else:
        sip_uri = os.getenv("LINPHONE_SIP_URI", "sip:yourusername@sip.linphone.org")
        
    sip_host = os.getenv("SIP_OUTBOUND_HOST", "sip.linphone.org")
    
    import time
    room_name = f"outbound_call_room_{int(time.time())}"
    logger.info(f"Connecting to LiveKit Server: {url}")
    lk_api = api.LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)

    # Clean the target SIP URI: LiveKit expects only the username/number when using a stored trunk
    target_number = sip_uri
    if target_number.startswith("sip:"):
        target_number = target_number[4:]
    if "@" in target_number:
        target_number = target_number.split("@")[0]

    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID", "ST_LVJkmP9NQ2gJ")

    # 1. Dispatch agent to ensure it is waiting in the room
    logger.info(f"Creating agent dispatch for room '{room_name}'...")
    try:
        dispatch = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="my-agent",
                room=room_name
            )
        )
        logger.info(f"Agent dispatch created: {dispatch.id}")
    except Exception as e:
        logger.warning(f"Could not create agent dispatch (it may already be running or configured automatically): {e}")

    # 2. Initiate SIP Outbound participant call
    logger.info(f"Dialing SIP target: {target_number} via trunk ID {sip_trunk_id}...")
    try:
        request = api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_call_to=target_number,
            sip_trunk_id=sip_trunk_id,
            participant_identity="sip_user_linphone",
            wait_until_answered=True
        )
        
        participant = await lk_api.sip.create_sip_participant(request)
        logger.info(f"Outbound call successful! Participant details: {participant}")
        
    except Exception as e:
        logger.error(f"Error making outbound SIP call: {e}")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(main())
