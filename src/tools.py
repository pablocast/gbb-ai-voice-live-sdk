import random
from datetime import datetime, timedelta

def get_user_information(query: str) -> str:
    """Search the knowledge base user credit card due date and amount."""
    # Generate random due date (between today and 90 days from now)
    today = datetime.now()
    random_days = random.randint(0, 90)
    due_date = today + timedelta(days=random_days)
    data_vencimento = due_date.strftime("%d/%m/%Y")
    
    # Generate random invoice amount (between 100.00 and 5000.00)
    valor_da_fatura = round(random.uniform(100.00, 5000.00), 2)
    
    return f"Data de vencimento: {data_vencimento}, Valor da fatura: R$ {valor_da_fatura:.2f}"


def get_product_information(query: str) -> str:
    """Search the knowledge base for relevant product information."""
    # Simulate product information retrieval
    product_info = {
        "limite": "O limite do seu cartão de crédito pode variar conforme o uso e o perfil financeiro. Para mais detalhes, acesse o app PagBank.",
        "benefícios": "Os benefícios do cartão incluem cashback, descontos em parceiros e programa de pontos. Consulte o app PagBank para mais informações.",
        "taxas": "As taxas do cartão incluem anuidade, juros por atraso e tarifas de serviços. Detalhes completos estão disponíveis no app PagBank."
    }
    
    for key in product_info:
        if key in query.lower():
            return product_info[key]
    
    return "Desculpe, não consegui encontrar informações específicas sobre isso. Por favor, consulte o app PagBank para mais detalhes."