"""Scraper do PriceHawk - Extrai preços de lojas configuradas por YAML."""
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests
import yaml
from bs4 import BeautifulSoup

from pricehawk.database import Store, Product, PriceHistory, get_session, init_db
from pricehawk.config import settings
from pricehawk.alerts import PriceDropAlert

logger = logging.getLogger(__name__)


@dataclass
class StoreConfig:
    """Configuração de uma loja."""
    name: str
    base_url: str
    price_selector: str
    name_selector: str
    availability_selector: Optional[str]
    products: list[dict]


@dataclass
class ProductConfig:
    """Configuração de um produto."""
    external_id: str
    url: str


@dataclass
class ScrapedProduct:
    """Produto extraído do scraping."""
    external_id: str
    name: str
    price: float
    currency: str
    availability: Optional[str]


def load_stores_config(config_path: Path) -> list[StoreConfig]:
    """Carrega configuração de lojas do YAML."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    stores = []
    for store_data in data.get("stores", []):
        products = [ProductConfig(**p) for p in store_data.get("products", [])]
        stores.append(StoreConfig(
            name=store_data["name"],
            base_url=store_data["base_url"],
            price_selector=store_data["price_selector"],
            name_selector=store_data["name_selector"],
            availability_selector=store_data.get("availability_selector"),
            products=products,
        ))
    return stores


def parse_price(price_text: str) -> tuple[float, str]:
    """Extrai valor numérico e moeda do texto do preço."""
    # Procura por símbolos de moeda comuns (incluindo R$)
    if "R$" in price_text:
        currency = "R$"
    elif "$" in price_text:
        currency = "$"
    elif "€" in price_text:
        currency = "€"
    elif "£" in price_text:
        currency = "£"
    elif "¥" in price_text:
        currency = "¥"
    else:
        currency = "BRL"

    # Limpa o texto mantendo apenas números, pontos e vírgulas
    clean_text = re.sub(r"[^\d.,]", "", price_text)

    # Trata formatos com vírgula de milhar vs decimal
    # Se houver vírgula e ponto, determina qual é o decimal
    if "," in clean_text and "." in clean_text:
        if clean_text.rfind(",") > clean_text.rfind("."):
            # Vírgula é decimal (ex: 1.234,56 -> 1234.56)
            clean_text = clean_text.replace(".", "").replace(",", ".")
        else:
            # Ponto é decimal (ex: 1,234.56 -> 1234.56)
            clean_text = clean_text.replace(",", "")
    elif "," in clean_text:
        # Apenas vírgula: se tiver 2 dígitos após a vírgula, é decimal
        parts = clean_text.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            clean_text = clean_text.replace(",", ".")
        else:
            clean_text = clean_text.replace(",", "")

    try:
        price = float(clean_text)
        return price, currency
    except ValueError:
        return 0.0, currency


def scrape_product(store: StoreConfig, product: ProductConfig) -> Optional[ScrapedProduct]:
    """Faz scraping de um produto individual."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(product.url, headers=headers, timeout=30)
        response.raise_for_status()

        # Verifica se é JSON (FakeStore API) ou HTML
        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return scrape_json_product(store, product, response.json())
        else:
            return scrape_html_product(store, product, response.text)

    except Exception as e:
        logger.error(f"Erro ao fazer scraping de {product.url}: {e}")
        return None


def scrape_json_product(store: StoreConfig, product: ProductConfig, data: dict) -> Optional[ScrapedProduct]:
    """Extrai dados de produto de resposta JSON."""
    try:
        # Para FakeStore API, os campos são diretos
        price = float(data.get(store.price_selector, 0))
        name = data.get(store.name_selector, "Produto sem nome")

        return ScrapedProduct(
            external_id=product.external_id,
            name=name,
            price=price,
            currency="USD",  # FakeStore usa USD
            availability="In Stock" if price > 0 else "Out of Stock",
        )
    except Exception as e:
        logger.error(f"Erro ao parsear JSON de {product.url}: {e}")
        return None


def scrape_html_product(store: StoreConfig, product: ProductConfig, html: str) -> Optional[ScrapedProduct]:
    """Extrai dados de produto de HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Preço
        price_elem = soup.select_one(store.price_selector)
        if not price_elem:
            logger.warning(f"Seletor de preço não encontrou elemento: {store.price_selector}")
            return None
        price_text = price_elem.get_text(strip=True)
        price, currency = parse_price(price_text)

        # Nome
        name_elem = soup.select_one(store.name_selector)
        name = name_elem.get_text(strip=True) if name_elem else "Produto sem nome"

        # Disponibilidade
        availability = None
        if store.availability_selector:
            avail_elem = soup.select_one(store.availability_selector)
            if avail_elem:
                availability = avail_elem.get_text(strip=True)

        return ScrapedProduct(
            external_id=product.external_id,
            name=name,
            price=price,
            currency=currency,
            availability=availability,
        )
    except Exception as e:
        logger.error(f"Erro ao parsear HTML de {product.url}: {e}")
        return None


def upsert_store(session, store_config: StoreConfig) -> Store:
    """Cria ou atualiza loja no banco."""
    store = session.query(Store).filter(Store.name == store_config.name).first()
    if not store:
        store = Store(
            name=store_config.name,
            base_url=store_config.base_url,
            price_selector=store_config.price_selector,
            name_selector=store_config.name_selector,
            availability_selector=store_config.availability_selector,
        )
        session.add(store)
        session.flush()
    else:
        store.price_selector = store_config.price_selector
        store.name_selector = store_config.name_selector
        store.availability_selector = store_config.availability_selector
    return store


def upsert_product(session, store: Store, product_config: ProductConfig, scraped: ScrapedProduct) -> Product:
    """Cria ou atualiza produto no banco."""
    product = session.query(Product).filter(
        Product.store_id == store.id,
        Product.external_id == product_config.external_id,
    ).first()

    if not product:
        product = Product(
            store_id=store.id,
            external_id=product_config.external_id,
            name=scraped.name,
            url=product_config.url,
        )
        session.add(product)
        session.flush()
    else:
        product.name = scraped.name
        product.url = product_config.url
    return product


def save_price_history(session, product: Product, scraped: ScrapedProduct) -> PriceHistory:
    """Salva histórico de preço."""
    history = PriceHistory(
        product_id=product.id,
        price=scraped.price,
        currency=scraped.currency,
        availability=scraped.availability,
    )
    session.add(history)
    return history


def check_price_drop(session, product: Product, new_price: float, threshold: float) -> bool:
    """Verifica se houve queda de preço acima do threshold."""
    # Busca o preço anterior mais recente
    last_history = session.query(PriceHistory).filter(
        PriceHistory.product_id == product.id
    ).order_by(PriceHistory.checked_at.desc()).first()

    if not last_history:
        return False

    old_price = last_history.price
    if old_price <= 0:
        return False

    drop_percentage = ((old_price - new_price) / old_price) * 100
    return drop_percentage >= threshold


def create_alert(session, product: Product, old_price: float, new_price: float, threshold: float) -> None:
    """Cria alerta de queda de preço."""
    from pricehawk.database import Alert
    drop_percentage = ((old_price - new_price) / old_price) * 100

    alert = Alert(
        product_id=product.id,
        old_price=old_price,
        new_price=new_price,
        drop_percentage=drop_percentage,
        threshold_percentage=threshold,
    )
    session.add(alert)
    logger.info(f"Alerta criado: {product.name} caiu {drop_percentage:.1f}% ({old_price} -> {new_price})")


def run_check(config_path: Path, dry_run: bool = False) -> None:
    """Executa verificação de preços para todas as lojas configuradas."""
    import asyncio
    init_db()

    stores_config = load_stores_config(config_path)
    threshold = 10.0  # Default threshold

    # Carrega threshold do YAML se existir
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if "alerts" in data:
            threshold = data["alerts"].get("drop_threshold_percentage", 10.0)

    logger.info(f"Iniciando verificação de {len(stores_config)} lojas (threshold: {threshold}%)")

    price_alert = PriceDropAlert()

    with get_session() as session:
        for store_config in stores_config:
            logger.info(f"Verificando loja: {store_config.name}")

            # Upsert store
            store = upsert_store(session, store_config)

            for product_config in store_config.products:
                logger.info(f"  Produto: {product_config.external_id}")

                scraped = scrape_product(store_config, product_config)
                if not scraped:
                    logger.warning(f"  Falha ao extrair dados de {product_config.url}")
                    continue

                # Upsert product
                product = upsert_product(session, store, product_config, scraped)

                # Verifica queda de preço
                old_price = None
                if not dry_run:
                    last_history = session.query(PriceHistory).filter(
                        PriceHistory.product_id == product.id
                    ).order_by(PriceHistory.checked_at.desc()).first()

                    if last_history:
                        old_price = last_history.price
                        if old_price > 0:
                            drop_percentage = ((old_price - scraped.price) / old_price) * 100
                            if drop_percentage >= threshold:
                                # Cria alerta no banco
                                create_alert(session, product, old_price, scraped.price, threshold)

                                # Envia notificação async
                                asyncio.run(price_alert.send_price_drop_alert(
                                    store_name=store.name,
                                    product_name=product.name,
                                    product_url=product.url,
                                    old_price=old_price,
                                    new_price=scraped.price,
                                    drop_percentage=drop_percentage,
                                    currency=scraped.currency
                                ))

                # Salva histórico
                if not dry_run:
                    save_price_history(session, product, scraped)

                logger.info(f"  Preço: {scraped.currency} {scraped.price:.2f}")

    logger.info("Verificação concluída")