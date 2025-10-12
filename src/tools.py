import random
from datetime import datetime, timedelta
from typing import Any
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
import os
from azure.identity import DefaultAzureCredential

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    credential=DefaultAzureCredential(),
    index_name=os.getenv("AZURE_SEARCH_INDEX")
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


async def get_product_information(
    args: Any) -> str:
    print(f"Searching for '{args['query']}' in the knowledge base.")
    # Hybrid query using Azure AI Search with Semantic Ranker
    vector_queries = [VectorizableTextQuery(text=args['query'], k_nearest_neighbors=50, fields=embedding_field)]
   
    search_results = await search_client.search(
        search_text=args["query"], 
        query_type="semantic",
        semantic_configuration_name='default',
        top=5,
        vector_queries=vector_queries,
        select=", ".join(['chunk_id', 'chunk'])
    )
    result = ""
    async for r in search_results:
        result += f"[{r['chunk_id']}]: {r['chunk']}\n-----\n"
    return result