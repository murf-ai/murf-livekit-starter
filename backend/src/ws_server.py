import asyncio
import json
import logging
from datetime import datetime, timezone
import websockets

logger = logging.getLogger("ws_server")

CONNECTED_CLIENTS = set()

async def ws_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    logger.info(f"[WS SERVER] Client connected. Total clients: {len(CONNECTED_CLIENTS)}")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        logger.info(f"[WS SERVER] Client disconnected. Total clients: {len(CONNECTED_CLIENTS)}")

def broadcast_outcome(record: dict):
    t_broadcast = datetime.now(timezone.utc).isoformat()
    logger.info(f"[TIMESTAMP DEBUG 1d] WebSocket broadcast_outcome triggered at {t_broadcast} for clients={len(CONNECTED_CLIENTS)}")
    if not CONNECTED_CLIENTS:
        return
    
    payload = json.dumps({
        "type": "OUTCOME_RECORDED",
        "timestamp": t_broadcast,
        "record": record
    })
    
    websockets.broadcast(CONNECTED_CLIENTS, payload)

async def start_ws_server():
    server = await websockets.serve(ws_handler, "0.0.0.0", 8765)
    logger.info("[WS SERVER] WebSocket server running on ws://0.0.0.0:8765")
    return server

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_ws_server())
