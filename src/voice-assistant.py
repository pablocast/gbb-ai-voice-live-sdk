from azure.core.credentials import AzureKeyCredential, TokenCredential
import os
from dotenv import load_dotenv
import sys
import signal
import logging 
import asyncio

# Own modules
from handler import AsyncFunctionCallingClient, AudioProcessor
import utilities as utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(override=True)

api_key = os.getenv("AZURE_VOICELIVE_API_KEY")
endpoint = os.getenv("AZURE_VOICELIVE_ENDPOINT")
model = 'gpt-4o-realtime' #os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
voice = "pt-BR-FranciscaNeural"
credential = AzureKeyCredential(api_key) 

instructions = utils.load_instructions("instructions.txt")

tools = [{
    "type": "function",
    "name": "search_knowledge",
    "description": "Search for information in the knowledge base",
    "parameters": {
        "type": "object",
        "properties": {
        "query": {
            "type": "string",
            "description": "The search query string"
            }
        },
        "required": [
        "query"
        ]
    }
}
]

async def main():
    """Main async function."""
    # Create and run the client
    client = AsyncFunctionCallingClient(
        endpoint=endpoint,
        credential=credential,
        model=model,
        voice=voice,
        instructions=instructions,
        tools=tools
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        client.audio_processor.cleanup()
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Voice Live function calling client shut down.")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

