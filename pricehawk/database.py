"""Banco de dados do PriceHawk usando SQLAlchemy."""
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, sessionmaker

from pricehawk.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy."""
    pass


class Store(Base):
    """Modelo de loja."""
    __tablename__ = "stores"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(255), unique=True, nullable=False)
    base_url: Mapped[str] = Column(String(500), nullable=False)
    price_selector: Mapped[str] = Column(String(500), nullable=False)
    name_selector: Mapped[str] = Column(String(500), nullable=False)
    availability_selector: Mapped[str] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")


class Product(Base):
    """Modelo de produto."""
    __tablename__ = "products"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = Column(Integer, ForeignKey("stores.id"), nullable=False)
    external_id: Mapped[str] = Column(String(255), nullable=False)
    name: Mapped[str] = Column(String(500), nullable=False)
    url: Mapped[str] = Column(String(1000), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("store_id", "external_id", name="uq_store_external"),)

    store = relationship("Store", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    """Histórico de preços."""
    __tablename__ = "price_history"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = Column(Integer, ForeignKey("products.id"), nullable=False)
    price: Mapped[float] = Column(Float, nullable=False)
    currency: Mapped[str] = Column(String(10), default="BRL")
    availability: Mapped[str] = Column(String(50), nullable=True)
    checked_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")


class Alert(Base):
    """Alerta de queda de preço."""
    __tablename__ = "alerts"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price: Mapped[float] = Column(Float, nullable=False)
    new_price: Mapped[float] = Column(Float, nullable=False)
    drop_percentage: Mapped[float] = Column(Float, nullable=False)
    threshold_percentage: Mapped[float] = Column(Float, nullable=False)
    notified: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    notified_at: Mapped[datetime] = Column(DateTime, nullable=True)


# Engine e Session
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Inicializa o banco de dados criando todas as tabelas."""
    # Garante que o diretório existe para SQLite
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados inicializado")


@contextmanager
def get_session():
    """Context manager para sessões do banco."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()