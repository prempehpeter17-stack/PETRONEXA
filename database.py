"""
Database session management and ORM models for PetroNexa.
"""
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(40), default="drilling_engineer")
    company_name = Column(String(150), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    simulations = relationship("SimulationModel", back_populates="owner", cascade="all, delete-orphan")


class SimulationModel(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    simulation_type = Column(String(50), nullable=False)  # 'hydraulics', 'cementing', 'well_control'
    input_parameters = Column(Text, nullable=False)  # JSON payload
    output_results = Column(Text, nullable=False)  # JSON payload
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("UserModel", back_populates="simulations")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
