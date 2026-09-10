"""Database models and async session management for PetroNexa."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON
from config import settings

DATABASE_URL = settings.database_url

connect_args = {}
if DATABASE_URL.startswith("sqlite+aiosqlite"):
    connect_args["timeout"] = 30

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="drilling_engineer")
    company_name: Mapped[str] = mapped_column(String(150), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    well_name: Mapped[str] = mapped_column(String(120), default="")
    field_name: Mapped[str] = mapped_column(String(120), default="")
    rig_name: Mapped[str] = mapped_column(String(120), default="")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    trajectory_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    owner = relationship("UserModel", back_populates="projects")


async def init_db() -> None:
    """Initializes schema and catches database engine connection exceptions explicitly."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        raise RuntimeError(f"Database initialization failed: {exc}") from exc


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
