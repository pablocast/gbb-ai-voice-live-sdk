import random
from datetime import datetime, timedelta

def search_knowledge(query: str) -> str:
    """Search the knowledge base for relevant information."""
    # Generate random due date (between today and 90 days from now)
    today = datetime.now()
    random_days = random.randint(0, 90)
    due_date = today + timedelta(days=random_days)
    data_vencimento = due_date.strftime("%d/%m/%Y")
    
    # Generate random invoice amount (between 100.00 and 5000.00)
    valor_da_fatura = round(random.uniform(100.00, 5000.00), 2)
    
    return f"Data de vencimento: {data_vencimento}, Valor da fatura: R$ {valor_da_fatura:.2f}"


