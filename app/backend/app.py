import asyncio
import json
import logging
import base64
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

from handler import AsyncFunctionCallingClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.voicelive.models import AzureStandardVoice, ServerEventType, ItemType

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VoiceAssistantBridge:
    """Bridge between frontend WebSocket and Azure VoiceLive API"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.voice_clients: Dict[str, AsyncFunctionCallingClient] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
        
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.voice_clients:
            # Cleanup voice client
            voice_client = self.voice_clients[client_id]
            if voice_client.audio_processor:
                await voice_client.audio_processor.cleanup()
            del self.voice_clients[client_id]
        logger.info(f"Client {client_id} disconnected")
        
    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self.disconnect(client_id)
                
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, message)


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
    lifespan=lifespan
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


class WebSocketVoiceClient(AsyncFunctionCallingClient):
    """Extended voice client that sends events via WebSocket"""
    
    def __init__(self, client_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.bridge = bridge
        
    async def _handle_event(self, event, connection):
        """Override to send events to frontend via WebSocket"""
        # Send event to frontend first (before processing)
        event_data = {
            "type": "voice_event",
            "event_type": event.type,
            "data": self._serialize_event(event)
        }
        await self.bridge.send_message(self.client_id, event_data)
        
        # Call parent handler
        await super()._handle_event(event, connection)
        
    async def _handle_function_call_with_improved_pattern(self, conversation_created_event, connection):
        """Enhanced function call handler with WebSocket events"""
        # Validate the event structure
        if not isinstance(conversation_created_event, type(conversation_created_event)):
            logger.error("Expected ServerEventConversationItemCreated")
            return

        if not hasattr(conversation_created_event.item, 'call_id'):
            logger.error("Expected ResponseFunctionCallItem")
            return

        function_call_item = conversation_created_event.item
        function_name = function_call_item.name
        call_id = function_call_item.call_id
        previous_item_id = function_call_item.id

        logger.info(f"Function call detected: {function_name} with call_id: {call_id}")

        # Send function call started event
        await self.bridge.send_message(self.client_id, {
            "type": "tool_call_started",
            "function_name": function_name,
            "call_id": call_id,
            "timestamp": asyncio.get_event_loop().time()
        })

        try:
            # Set tracking variables
            self.function_call_in_progress = True
            self.active_call_id = call_id

            # Wait for the function arguments to be complete
            from handler import _wait_for_event, ServerEventType
            function_done = await _wait_for_event(
                connection, {ServerEventType.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE}
            )

            if function_done.call_id != call_id:
                logger.warning(f"Call ID mismatch: expected {call_id}, got {function_done.call_id}")
                return

            arguments = function_done.arguments
            logger.info(f"Function arguments received: {arguments}")

            # Send function arguments received event
            await self.bridge.send_message(self.client_id, {
                "type": "tool_call_arguments",
                "function_name": function_name,
                "call_id": call_id,
                "arguments": arguments,
                "timestamp": asyncio.get_event_loop().time()
            })

            # Wait for response to be done before proceeding
            await _wait_for_event(connection, {ServerEventType.RESPONSE_DONE})

            # Execute the function if we have it
            if function_name in self.available_functions:
                logger.info(f"Executing function: {function_name}")
                
                # Send function executing event
                await self.bridge.send_message(self.client_id, {
                    "type": "tool_call_executing",
                    "function_name": function_name,
                    "call_id": call_id,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                # Execute the function
                start_time = asyncio.get_event_loop().time()
                result = await self.available_functions[function_name](arguments)
                end_time = asyncio.get_event_loop().time()

                # Send function completed event
                await self.bridge.send_message(self.client_id, {
                    "type": "tool_call_completed",
                    "function_name": function_name,
                    "call_id": call_id,
                    "result": result,
                    "execution_time": end_time - start_time,
                    "timestamp": end_time
                })

                # Create function call output item
                from azure.ai.voicelive.models import FunctionCallOutputItem
                function_output = FunctionCallOutputItem(
                    call_id=call_id, output=json.dumps(result)
                )

                # Send the result back to the conversation with proper previous_item_id
                await connection.conversation.item.create(
                    previous_item_id=previous_item_id, item=function_output
                )

                logger.info(f"Function result sent: {result}")

                # Create a new response to process the function result
                await connection.response.create()

            else:
                logger.error(f"Unknown function: {function_name}")
                
                # Send function error event
                await self.bridge.send_message(self.client_id, {
                    "type": "tool_call_error",
                    "function_name": function_name,
                    "call_id": call_id,
                    "error": f"Unknown function: {function_name}",
                    "timestamp": asyncio.get_event_loop().time()
                })

        except asyncio.TimeoutError:
            error_msg = f"Timeout waiting for function call completion for {function_name}"
            logger.error(error_msg)
            
            # Send timeout event
            await self.bridge.send_message(self.client_id, {
                "type": "tool_call_error",
                "function_name": function_name,
                "call_id": call_id,
                "error": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            error_msg = f"Error executing function {function_name}: {e}"
            logger.error(error_msg)
            
            # Send error event
            await self.bridge.send_message(self.client_id, {
                "type": "tool_call_error",
                "function_name": function_name,
                "call_id": call_id,
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            })
            
        finally:
            self.function_call_in_progress = False
            self.active_call_id = None
        
    def _serialize_event(self, event):
        """Serialize VoiceLive event for frontend"""
        event_dict = {
            "type": event.type,
            "timestamp": getattr(event, 'timestamp', asyncio.get_event_loop().time())
        }
        
        # Add specific event data based on type
        if hasattr(event, 'session'):
            event_dict["session_id"] = event.session.id
            
        if hasattr(event, 'delta'):
            if event.type == "response.text.delta":
                event_dict["text"] = event.delta
            # Don't send audio data to reduce payload size
            elif event.type == "response.audio.delta":
                event_dict["has_audio"] = True
                event_dict["audio_length"] = len(event.delta) if event.delta else 0
                
        if hasattr(event, 'item'):
            event_dict["item"] = {
                "id": event.item.id,
                "type": event.item.type
            }
            if hasattr(event.item, 'name'):
                event_dict["item"]["name"] = event.item.name
            if hasattr(event.item, 'call_id'):
                event_dict["item"]["call_id"] = event.item.call_id
                
        if hasattr(event, 'error'):
            event_dict["error"] = {
                "message": event.error.message,
                "code": getattr(event.error, 'code', None)
            }
            
        # Add transcription data
        if hasattr(event, 'transcript'):
            event_dict["transcript"] = event.transcript
            
        return event_dict


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
        instructions_path = os.path.join(os.path.dirname(__file__), "shared", "instructions.txt")
        with open(instructions_path, "r", encoding="utf-8") as f:
            instructions = f.read()
            
        # Define tools
        tools = [
            {
                "type": "function",
                "name": "get_user_information",
                "description": "Search the knowledge base user credit card due date and amount",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query string"}
                    },
                    "required": ["query"],
                },
            },
            {
                "type": "function",
                "name": "get_product_information",
                "description": "Search the knowledge base for relevant product information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query string"}
                    },
                    "required": ["query"],
                },
            },
        ]
      
        # Create voice client
        voice_client = WebSocketVoiceClient(
            client_id=client_id,
            endpoint=endpoint,
            credential=credential,
            model=config.get("model", "gpt-4o-realtime"),
            voice=config.get("voice", "pt-BR-FranciscaNeural"),
            instructions=instructions,
            tools=tools
        )
        
        # Store client
        bridge.voice_clients[client_id] = voice_client
        
        # Send session started event
        await bridge.send_message(client_id, {
            "type": "session_started",
            "status": "success",
            "message": "Voice session initialized",
            "config": {
                "model": voice_client.model,
                "voice": voice_client.voice,
                "tools_count": len(tools)
            }
        })
        
        # Start the voice client (this will run in background)
        asyncio.create_task(voice_client.run())
        
        logger.info(f"Voice session started for client {client_id}")
        
    except Exception as e:
        logger.error(f"Failed to start voice session for {client_id}: {e}")
        await bridge.send_message(client_id, {
            "type": "session_error",
            "error": str(e)
        })


async def stop_voice_session(client_id: str):
    """Stop voice session for the client"""
    if client_id in bridge.voice_clients:
        voice_client = bridge.voice_clients[client_id]
        if voice_client.audio_processor:
            await voice_client.audio_processor.cleanup()
        del bridge.voice_clients[client_id]
        
        await bridge.send_message(client_id, {
            "type": "session_stopped",
            "status": "success"
        })
        logger.info(f"Voice session stopped for client {client_id}")


async def handle_audio_input(client_id: str, audio_data: str):
    """Handle audio input from frontend"""
    if client_id not in bridge.voice_clients:
        return
        
    voice_client = bridge.voice_clients[client_id]
    if voice_client.audio_processor and voice_client.audio_processor.connection:
        try:
            # Audio data should be base64 encoded
            await voice_client.audio_processor.connection.input_audio_buffer.append(audio=audio_data)
        except Exception as e:
            logger.error(f"Error handling audio input for {client_id}: {e}")


async def interrupt_assistant(client_id: str):
    """Interrupt the assistant's current response"""
    if client_id not in bridge.voice_clients:
        return
        
    voice_client = bridge.voice_clients[client_id]
    if voice_client.audio_processor and voice_client.audio_processor.connection:
        try:
            await voice_client.audio_processor.connection.response.cancel()
            await bridge.send_message(client_id, {
                "type": "assistant_interrupted",
                "status": "success"
            })
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
        return {"message": "Voice Assistant WebSocket Server", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )