"""
FastAPI WebSocket server for Voice Assistant
Clean implementation using webhandler.py for cloud/container deployments
"""

import asyncio
import json
import logging
import base64
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from web_handler import WebSocketVoiceClient, VoiceAssistantBridge
from azure.core.credentials import AzureKeyCredential

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global bridge instance
bridge = VoiceAssistantBridge()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting WebSocket server...")
    yield
    logger.info("Shutting down WebSocket server...")


# Create FastAPI app
app = FastAPI(
    title="Voice Assistant WebSocket API",
    description="WebSocket bridge for Azure VoiceLive API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define API endpoints BEFORE static file mounting
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "voice-assistant-websocket"}


# Define WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for voice assistant communication"""
    await bridge.connect(websocket, client_id)

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message = json.loads(data)

            await handle_frontend_message(client_id, message, websocket)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        await bridge.disconnect(client_id)


async def handle_frontend_message(client_id: str, message: dict, websocket: WebSocket):
    """Handle messages from frontend"""
    message_type = message.get("type")

    if message_type == "start_session":
        await start_voice_session(client_id, message.get("config", {}))

    elif message_type == "stop_session":
        await stop_voice_session(client_id)

    elif message_type == "send_audio":
        await handle_audio_input(client_id, message.get("audio"))

    elif message_type == "interrupt":
        await interrupt_assistant(client_id)

    elif message_type == "audio_chunk":
        # Handle real-time audio streaming from frontend
        await handle_audio_chunk(client_id, message.get("data"))

    else:
        logger.warning(f"Unknown message type: {message_type}")


async def start_voice_session(client_id: str, config: dict):
    """Start a voice session for the client"""
    try:
        # Get environment variables
        endpoint = os.getenv("AZURE_VOICELIVE_ENDPOINT")
        api_key = os.getenv("AZURE_VOICELIVE_API_KEY")

        if not endpoint or not api_key:
            raise ValueError("Missing Azure VoiceLive configuration")

        # Create credential
        credential = AzureKeyCredential(api_key)

        # Load instructions
        instructions_path = os.path.join(
            os.path.dirname(__file__), "shared", "instructions.txt"
        )
        with open(instructions_path, "r", encoding="utf-8") as f:
            instructions = f.read()

        # Load tools from YAML configuration
        from tool_loader import get_tool_loader

        tool_loader = get_tool_loader()
        tools = tool_loader.get_tool_definitions()

        # Log tool environment info
        env_info = tool_loader.get_environment_info()
        logger.info(f"Tool environment: {env_info}")

        # Create audio streaming callback
        async def stream_audio_to_client(audio_data: bytes):
            """Stream audio data to frontend via WebSocket."""
            try:
                # Encode audio data as base64 for WebSocket transmission
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")

                message = {
                    "type": "audio_data",
                    "data": audio_base64,
                    "format": "pcm16",
                    "sample_rate": 24000,
                    "channels": 1,
                    "timestamp": asyncio.get_event_loop().time(),
                }

                await bridge.send_message(client_id, message)
                logger.debug(
                    f"🔊 Audio data streamed to client {client_id} ({len(audio_data)} bytes)"
                )

            except Exception as e:
                logger.error(f"Failed to stream audio to client {client_id}: {e}")

        # Create voice client with audio streaming support
        voice_client = WebSocketVoiceClient(
            client_id=client_id,
            endpoint=endpoint,
            credential=credential,
            bridge=bridge,
            model=config.get("model", "gpt-4o-realtime"),
            voice=config.get(
                "voice", "pt-BR-FranciscaNeural"
            ),  # Valid VoiceLive API voice
            instructions=instructions,
            tools=tools,
            websocket_callback=stream_audio_to_client,
        )

        # Store client
        bridge.voice_clients[client_id] = voice_client

        # Send session started event
        await bridge.send_message(
            client_id,
            {
                "type": "session_started",
                "status": "success",
                "message": "Voice session initialized with audio streaming",
                "config": {
                    "model": voice_client.model,
                    "voice": voice_client.voice,
                    "tools_count": len(tools),
                    "audio_streaming": True,
                    "sample_rate": 24000,
                    "format": "pcm16",
                    "channels": 1,
                },
            },
        )

        # Start the voice client (this will run in background)
        asyncio.create_task(voice_client.run())

        logger.info(
            f"✅ Voice session with audio streaming started for client {client_id}"
        )

    except Exception as e:
        logger.error(f"Failed to start voice session for {client_id}: {e}")
        await bridge.send_message(client_id, {"type": "session_error", "error": str(e)})


async def stop_voice_session(client_id: str):
    """Stop voice session for the client"""
    if client_id in bridge.voice_clients:
        voice_client = bridge.voice_clients[client_id]
        await voice_client.cleanup()
        del bridge.voice_clients[client_id]

        await bridge.send_message(
            client_id, {"type": "session_stopped", "status": "success"}
        )
        logger.info(f"Voice session stopped for client {client_id}")


async def handle_audio_input(client_id: str, audio_data: str):
    """Handle audio input from frontend (legacy method)"""
    if client_id not in bridge.voice_clients:
        return

    voice_client = bridge.voice_clients[client_id]
    try:
        # Audio data should be base64 encoded
        await voice_client.process_audio_input(audio_data)
        logger.debug(f"Audio input processed for client {client_id}")
    except Exception as e:
        logger.error(f"Error handling audio input for {client_id}: {e}")


async def handle_audio_chunk(client_id: str, audio_base64: str):
    """Handle real-time audio chunks from frontend"""
    if client_id not in bridge.voice_clients:
        logger.warning(f"No voice client found for {client_id}")
        return

    voice_client = bridge.voice_clients[client_id]
    try:
        # Process audio chunk
        await voice_client.process_audio_input(audio_base64)
        logger.debug(f"Audio chunk processed for client {client_id}")
    except Exception as e:
        logger.error(f"Error handling audio chunk for {client_id}: {e}")


async def interrupt_assistant(client_id: str):
    """Interrupt the assistant's current response"""
    if client_id not in bridge.voice_clients:
        return

    voice_client = bridge.voice_clients[client_id]
    try:
        await voice_client.interrupt_response()
        await bridge.send_message(
            client_id,
            {
                "type": "assistant_interrupted",
                "status": "success",
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
        logger.info(f"Assistant interrupted for client {client_id}")
    except Exception as e:
        logger.error(f"Error interrupting assistant for {client_id}: {e}")


# Mount static files for frontend
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    # Mount ALL static files at root level - this is the key fix
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    # Development fallback
    @app.get("/")
    async def root():
        return {
            "message": "Voice Assistant WebSocket Server with Audio Streaming",
            "version": "1.0.0",
        }


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
