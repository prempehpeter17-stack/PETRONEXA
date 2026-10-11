"""Database models and async session management for PetroNexa."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, Boolean, text
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
    company_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    phone_number: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), default="professional", nullable=False)
    study_level: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    programme: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    job_title: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    sms_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
    """Create tables and add new profile columns to existing installations safely."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # create_all does not alter existing tables. Keep older PetroNexa databases
            # usable when the registration profile is upgraded.
            def migrate_user_columns(sync_conn):
                from sqlalchemy import inspect

                inspector = inspect(sync_conn)
                if "users" not in inspector.get_table_names():
                    return
                existing = {column["name"] for column in inspector.get_columns("users")}
                migrations = {
                    "full_name": "VARCHAR(150) NOT NULL DEFAULT ''",
                    "phone_number": "VARCHAR(40) NOT NULL DEFAULT ''",
                    "country": "VARCHAR(80) NOT NULL DEFAULT ''",
                    "account_type": "VARCHAR(30) NOT NULL DEFAULT 'professional'",
                    "study_level": "VARCHAR(80) NOT NULL DEFAULT ''",
                    "programme": "VARCHAR(120) NOT NULL DEFAULT ''",
                    "job_title": "VARCHAR(120) NOT NULL DEFAULT ''",
                    "sms_opt_in": "BOOLEAN NOT NULL DEFAULT FALSE",
                }
                for column_name, column_definition in migrations.items():
                    if column_name not in existing:
                        sync_conn.execute(
                            text(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}")
                        )

            await conn.run_sync(migrate_user_columns)
    except Exception as exc:
        raise RuntimeError(f"Database initialization failed: {exc}") from exc


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
