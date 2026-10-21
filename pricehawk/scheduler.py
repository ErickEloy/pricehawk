"""Scheduler do PriceHawk usando APScheduler."""
import logging
import signal
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from pricehawk.scraper import run_check
from pricehawk.config import settings

logger = logging.getLogger(__name__)


def run_scheduler(config_path: Path, interval_minutes: int = None) -> None:
    """Executa o scheduler de verificação periódica."""
    if interval_minutes is None:
        interval_minutes = settings.check_interval_minutes

    scheduler = BlockingScheduler()

    def job():
        logger.info("Executando verificação agendada...")
        try:
            run_check(config_path)
        except Exception as e:
            logger.error(f"Erro na verificação agendada: {e}")

    # Adiciona job
    scheduler.add_job(
        job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="price_check",
        name="Verificação de preços",
        replace_existing=True,
    )

    # Handler para shutdown gracioso
    def shutdown(signum, frame):
        logger.info("Recebido sinal de shutdown, parando scheduler...")
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info(f"Scheduler iniciado - verificação a cada {interval_minutes} minutos")
    logger.info("Pressione Ctrl+C para parar")

    try:
        # Executa uma vez imediatamente
        job()
        # Inicia o scheduler
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no scheduler: {e}")
        raise