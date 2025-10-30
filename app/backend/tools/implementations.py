"""
Function implementations for the Voice Assistant
Contains the actual function implementations that can be called by the AI
"""

import random
from datetime import datetime, timedelta
from typing import Any
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
import os
from azure.identity import DefaultAzureCredential
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize search client only if environment variables are available
search_client = None
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX")

if azure_search_endpoint and azure_search_index:
    search_client = SearchClient(
        endpoint=azure_search_endpoint,
        credential=DefaultAzureCredential(),
        index_name=azure_search_index,
    )


async def get_user_information(args: dict) -> str:
    """Search the knowledge base user credit card due date and amount."""
    # Extract query from args
    query = args.get("query", "") if isinstance(args, dict) else str(args)
    
    # Generate random due date (between today and 90 days from now)
    today = datetime.now()
    random_days = random.randint(0, 90)
    due_date = today + timedelta(days=random_days)
    data_vencimento = due_date.strftime("%d/%m/%Y")

    # Generate random invoice amount (between 100.00 and 5000.00)
    valor_da_fatura = round(random.uniform(100.00, 5000.00), 2)

    return f"Data de vencimento: {data_vencimento}, Valor da fatura: R$ {valor_da_fatura:.2f}"


async def get_product_information(args: dict) -> str:
    """Search the knowledge base for relevant product information."""
    # Extract query from args
    if isinstance(args, dict):
        query = args.get("query", "")
    else:
        # Handle case where args might be a string
        if isinstance(args, str):
            try:
                parsed_args = json.loads(args)
                query = parsed_args.get("query", args)
            except json.JSONDecodeError:
                query = args
        else:
            query = str(args)

    # Check if search client is initialized
    if not search_client:
        logger.warning("Azure Search client not initialized. Environment variables missing.")
        return f"Unable to search for '{query}' - Azure Search service not configured."

    # Hybrid query using Azure AI Search with Semantic Ranker
    vector_queries = [
        VectorizableTextQuery(text=query, k_nearest_neighbors=50, fields="text_vector")
    ]

    search_results = await search_client.search(
        search_text=query,
        query_type="semantic",
        semantic_configuration_name="default",
        top=5,
        vector_queries=vector_queries,
        select=", ".join(["chunk_id", "chunk"]),
    )
    result = ""
    async for r in search_results:
        result += f"[{r['chunk_id']}]: {r['chunk']}\n-----\n"
    return result