"""Alertas do PriceHawk - Telegram e Discord."""
import logging
from datetime import datetime
from typing import Optional

import httpx
from telegram import Bot

from pricehawk.config import settings

logger = logging.getLogger(__name__)


class AlertSender:
    """Envia alertas por diferentes canais."""

    def __init__(self):
        self.telegram_bot_token = settings.telegram_bot_token
        self.telegram_chat_id = settings.telegram_chat_id
        self.discord_webhook_url = settings.discord_webhook_url

    async def send_telegram_alert(self, message: str) -> bool:
        """Envia alerta via Telegram."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Token ou chat_id do Telegram não configurado")
            return False

        try:
            bot = Bot(token=self.telegram_bot_token)
            await bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info("Alerta Telegram enviado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Telegram: {e}")
            return False

    async def send_discord_alert(self, message: str) -> bool:
        """Envia alerta via Discord webhook."""
        if not self.discord_webhook_url:
            logger.warning("Webhook do Discord não configurado")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook_url,
                    json={
                        "content": message,
                        "embeds": [{
                            "title": "PriceHawk - Queda de Preço",
                            "description": message,
                            "color": 0x00FF00,
                            "timestamp": datetime.utcnow().isoformat(),
                        }]
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info("Alerta Discord enviado com sucesso")
                return True
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Discord: {e}")
            return False


class PriceDropAlert:
    """Gerencia alertas de queda de preço."""

    def __init__(self):
        self.sender = AlertSender()

    def format_message(
        self,
        store_name: str,
        product_name: str,
        product_url: str,
        old_price: float,
        new_price: float,
        drop_percentage: float,
        currency: str = "BRL"
    ) -> str:
        """Formata mensagem de alerta."""
        emoji = "📉"
        message = f"""{emoji} *Queda de Preço Detectada!*

*Loja:* {store_name}
*Produto:* {product_name}
*Preço anterior:* {currency} {old_price:.2f}
*Preço atual:* {currency} {new_price:.2f}
*Economia:* {drop_percentage:.1f}%

🔗 [Ver produto]({product_url})
"""
        return message

    async def send_price_drop_alert(
        self,
        store_name: str,
        product_name: str,
        product_url: str,
        old_price: float,
        new_price: float,
        drop_percentage: float,
        currency: str = "BRL"
    ) -> dict:
        """Envia alerta de queda de preço para todos os canais configurados."""
        message = self.format_message(
            store_name, product_name, product_url,
            old_price, new_price, drop_percentage, currency
        )

        results = {
            "telegram": False,
            "discord": False,
        }

        # Envia Telegram
        if settings.telegram_bot_token and settings.telegram_chat_id:
            results["telegram"] = await self.sender.send_telegram_alert(message)

        # Envia Discord
        if settings.discord_webhook_url:
            results["discord"] = await self.sender.send_discord_alert(message)

        return results


async def test_alerts() -> dict:
    """Testa conectividade dos canais de alerta."""
    sender = AlertSender()
    results = {}

    if settings.telegram_bot_token and settings.telegram_chat_id:
        try:
            results["telegram"] = await sender.send_telegram_alert(
                "PriceHawk - Teste de conectividade do Telegram ✅"
            )
        except Exception as e:
            logger.error(f"Erro no teste Telegram: {e}")
            results["telegram"] = False
    else:
        results["telegram"] = None  # Não configurado

    if settings.discord_webhook_url:
        try:
            results["discord"] = await sender.send_discord_alert(
                "PriceHawk - Teste de conectividade do Discord ✅"
            )
        except Exception as e:
            logger.error(f"Erro no teste Discord: {e}")
            results["discord"] = False
    else:
        results["discord"] = None  # Não configurado

    return results