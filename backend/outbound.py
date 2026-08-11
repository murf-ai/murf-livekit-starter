import asyncio
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from livekit.api import LiveKitAPI
from livekit.protocol.sip import CreateSIPParticipantRequest
from livekit.api import CreateAgentDispatchRequest

# Force load .env.local from backend folder
env_path = Path(__file__).resolve().parent / ".env.local"
load_dotenv(dotenv_path=env_path)

async def main():
    api = LiveKitAPI()
    
    SIP_TRUNK_ID = "ST_M24ZLQNDcmVe" 
    YOUR_PHONE_NUMBER = "raksha_aii" 
    AGENT_NAME = "my-agent"
    
    unique_room_name = f"emergency-room-{uuid.uuid4().hex[:6]}"
    unique_identity = f"victim-{uuid.uuid4().hex[:4]}"

    print(f"Creating fresh room: {unique_room_name}")

    # 1. Dispatch Raksha (my-agent) into the room
    print(f"Dispatching agent '{AGENT_NAME}' into room...")
    try:
        await api.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=unique_room_name
            )
        )
        print("Agent dispatch request sent!")
    except Exception as e:
        print(f"Failed to dispatch agent: {e}")

    # 2. Dial your phone into the same room
    print(f"Initiating emergency broadcast to {YOUR_PHONE_NUMBER}...")
    request = CreateSIPParticipantRequest(
        sip_trunk_id=SIP_TRUNK_ID,
        sip_call_to=YOUR_PHONE_NUMBER,
        room_name=unique_room_name,
        participant_identity=unique_identity,
    )
    
    try:
        await api.sip.create_sip_participant(request)
        print("Call dispatched successfully! Raksha will join and speak once connected.")
    except Exception as e:
        print(f"Failed to dispatch call: {e}")
    finally:
        await api.aclose()

if __name__ == "__main__":
    asyncio.run(main())