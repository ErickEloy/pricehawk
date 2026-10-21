"""CLI do PriceHawk."""
import sys
from pathlib import Path

import typer
from colorlog import ColoredFormatter
import logging

app = typer.Typer(
    name="pricehawk",
    help="PriceHawk - Monitor de preços white-label com alertas",
    add_completion=False,
)


def setup_logging(level: str = "INFO") -> None:
    """Configura logging colorido."""
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(cyan)s%(name)s%(reset)s: %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


@app.callback()
def callback(
    ctx: typer.Context,
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Nível de log"),
) -> None:
    """PriceHawk - Monitor de preços white-label."""
    setup_logging(log_level)


@app.command()
def version() -> None:
    """Mostra a versão do PriceHawk."""
    from pricehawk import __version__

    typer.echo(f"PriceHawk v{__version__}")


@app.command()
def check(
    config: Path = typer.Option("config/stores.yaml", "--config", "-c", help="Arquivo de configuração de lojas"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Executa sem salvar no banco"),
) -> None:
    """Verifica preços das lojas configuradas."""
    from pricehawk.scraper import run_check

    run_check(config, dry_run)


@app.command()
def daemon(
    config: Path = typer.Option("config/stores.yaml", "--config", "-c", help="Arquivo de configuração de lojas"),
    interval: int = typer.Option(60, "--interval", "-i", help="Intervalo em minutos"),
) -> None:
    """Executa o daemon de verificação periódica."""
    from pricehawk.scheduler import run_scheduler

    run_scheduler(config, interval)


@app.command()
def init_db() -> None:
    """Inicializa o banco de dados."""
    from pricehawk.database import init_db

    init_db()
    typer.echo("Banco de dados inicializado com sucesso!")


def main() -> None:
    """Entry point para o CLI."""
    app()


if __name__ == "__main__":
    main()