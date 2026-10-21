"""Utilitários de API para o dashboard."""
import requests
from typing import Dict, List, Optional
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def get_products() -> List[Dict]:
    """Busca lista de produtos."""
    try:
        response = requests.get(f"{BASE_URL}/products", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar produtos: {e}")
        return []


def get_price_history(product_id: int) -> List[Dict]:
    """Busca histórico de preços de um produto."""
    try:
        response = requests.get(
            f"{BASE_URL}/products/{product_id}/history",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return []


def get_alerts() -> List[Dict]:
    """Busca alertas ativos."""
    try:
        response = requests.get(f"{BASE_URL}/alerts", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao buscar alertas: {e}")
        return []
