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

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=DefaultAzureCredential(),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
)


async def get_user_information(query: str) -> str:
    """Search the knowledge base user credit card due date and amount."""
    # Generate random due date (between today and 90 days from now)
    today = datetime.now()
    random_days = random.randint(0, 90)
    due_date = today + timedelta(days=random_days)
    data_vencimento = due_date.strftime("%d/%m/%Y")

    # Generate random invoice amount (between 100.00 and 5000.00)
    valor_da_fatura = round(random.uniform(100.00, 5000.00), 2)

    return f"Data de vencimento: {data_vencimento}, Valor da fatura: R$ {valor_da_fatura:.2f}"


async def get_product_information(query: Any) -> str:

    if isinstance(query, str):
        try:
            query = json.loads(query)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse arguments: {query}")
            return "Erro ao processar a consulta."

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
