"""
Testes para o módulo de alertas.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_alert_sender_init():
    """Testa inicialização do AlertSender."""
    from pricehawk.alerts import AlertSender
    from pricehawk.config import settings

    sender = AlertSender()
    assert sender.telegram_bot_token == settings.telegram_bot_token
    assert sender.telegram_chat_id == settings.telegram_chat_id
    assert sender.discord_webhook_url == settings.discord_webhook_url


def test_price_drop_alert_format_message():
    """Testa formatação da mensagem de alerta."""
    from pricehawk.alerts import PriceDropAlert

    alert = PriceDropAlert()
    message = alert.format_message(
        store_name="Test Store",
        product_name="Test Product",
        product_url="https://test.com/product/1",
        old_price=100.0,
        new_price=80.0,
        drop_percentage=20.0,
        currency="R$"
    )

    assert "Test Store" in message
    assert "Test Product" in message
    assert "R$ 100.00" in message
    assert "R$ 80.00" in message
    assert "20.0%" in message
    assert "https://test.com/product/1" in message


@pytest.mark.asyncio
async def test_send_price_drop_alert_no_config():
    """Testa envio de alerta sem configuração."""
    from pricehawk.alerts import PriceDropAlert
    from pricehawk.config import settings

    # Mock settings sem configuração
    mock_settings = MagicMock()
    mock_settings.telegram_bot_token = ''
    mock_settings.telegram_chat_id = ''
    mock_settings.discord_webhook_url = ''

    with patch('pricehawk.alerts.settings', mock_settings):
        alert = PriceDropAlert()
        results = await alert.send_price_drop_alert(
            store_name="Test Store",
            product_name="Test Product",
            product_url="https://test.com/product/1",
            old_price=100.0,
            new_price=80.0,
            drop_percentage=20.0,
            currency="R$"
        )

        assert results["telegram"] is False
        assert results["discord"] is False
