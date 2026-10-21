"""Testes unitários para o PriceHawk."""
import pytest
from pathlib import Path
import tempfile
import os

from pricehawk.config import Settings


def test_settings_defaults():
    """Testa configurações padrão."""
    # Cria um arquivo .env temporário
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text("")

        settings = Settings(_env_file=env_file)

        assert settings.database_url == "sqlite:///pricehawk.db"
        assert settings.log_level == "INFO"
        assert settings.app_name == "PriceHawk"
        assert settings.brand_color == "#2563eb"
        assert settings.currency_symbol == "R$"
        assert settings.check_interval_minutes == 60


def test_settings_from_env():
    """Testa configurações vindas do .env."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text("DATABASE_URL=sqlite:///test.db\nLOG_LEVEL=DEBUG\nAPP_NAME=TestApp\n")

        settings = Settings(_env_file=env_file)

        assert settings.database_url == "sqlite:///test.db"
        assert settings.log_level == "DEBUG"
        assert settings.app_name == "TestApp"


def test_load_stores_config():
    """Testa carregamento da configuração de lojas."""
    from pricehawk.scraper import load_stores_config

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "stores.yaml"
        config_file.write_text("""
stores:
  - name: "Test Store"
    base_url: "https://test.com"
    price_selector: ".price"
    name_selector: "h1"
    availability_selector: ".stock"
    products:
      - external_id: "1"
        url: "https://test.com/product/1"
""")

        stores = load_stores_config(config_file)

        assert len(stores) == 1
        assert stores[0].name == "Test Store"
        assert stores[0].base_url == "https://test.com"
        assert stores[0].price_selector == ".price"
        assert stores[0].name_selector == "h1"
        assert stores[0].availability_selector == ".stock"
        assert len(stores[0].products) == 1
        assert stores[0].products[0].external_id == "1"
        assert stores[0].products[0].url == "https://test.com/product/1"


def test_parse_price():
    """Testa parsing de preços."""
    from pricehawk.scraper import parse_price

    # Preço em reais
    price, currency = parse_price("R$ 51,77")
    assert price == 51.77
    assert currency == "R$"

    # Preço em dólares
    price, currency = parse_price("$ 22.30")
    assert price == 22.30
    assert currency == "$"

    # Preço em euros
    price, currency = parse_price("€ 49,99")
    assert price == 49.99
    assert currency == "€"

    # Preço simples
    price, currency = parse_price("109.95")
    assert price == 109.95
    assert currency == "BRL"


@pytest.mark.asyncio
async def test_database_init():
    """Testa inicialização do banco."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from pricehawk.database import Base, Store, Product

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)

    session = SessionLocal()
    try:
        # Testa inserção de loja
        store = Store(
            name="Test Store",
            base_url="https://test.com",
            price_selector=".price",
            name_selector="h1",
        )
        session.add(store)
        session.flush()

        assert store.id is not None
        assert store.name == "Test Store"

        # Testa inserção de produto
        product = Product(
            store_id=store.id,
            external_id="1",
            name="Test Product",
            url="https://test.com/product/1",
        )
        session.add(product)
        session.flush()

        assert product.id is not None
        assert product.name == "Test Product"
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])