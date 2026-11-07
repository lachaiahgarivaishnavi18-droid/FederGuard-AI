"""Configuration, persistence and opaque session authentication."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, String, JSON, ForeignKey, UniqueConstraint, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///runtime/coordinator.db'
    demo: bool = True
    cookie_secure: bool = False
    frontend_origin: str = 'http://localhost:5173'
    llm_provider: str = 'demo'
    llm_model: str = ''
    llm_api_key: str = ''
    llm_base_url: str = 'https://api.openai.com/v1'
    semantic_model: str = ''
    reranker_model: str = ''
    serverless: bool = False
    cloud_schema_ready: bool = False

settings = Settings()
Path(os.getenv('RUNTIME_DIR','runtime')).mkdir(parents=True,exist_ok=True)
engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if settings.database_url.startswith('sqlite') else {}, pool_pre_ping=True)
if settings.database_url.startswith('sqlite'):
    @event.listens_for(engine,'connect')
    def enable_foreign_keys(connection,record):
        connection.execute('PRAGMA foreign_keys=ON')
Session = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return secrets.token_hex(12)

class Bank(Base):
    __tablename__ = 'banks'
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    consent: Mapped[bool] = mapped_column(default=True)
    client_hash: Mapped[str] = mapped_column(default='')
    endpoint: Mapped[str] = mapped_column(default='')

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    role: Mapped[str] = mapped_column(default='analyst')
    bank_id: Mapped[str] = mapped_column(ForeignKey('banks.id'), index=True)

class LoginSession(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires: Mapped[float]

class Record(Base):
    """Typed resources; payload schemas are enforced at the API boundary."""
    __tablename__ = 'records'
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(index=True)
    bank_id: Mapped[str | None] = mapped_column(ForeignKey('banks.id'), nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(default=now)
    payload: Mapped[dict] = mapped_column(JSON)

class Participation(Base):
    __tablename__ = 'client_participation'
    __table_args__ = (UniqueConstraint('round_id', 'bank_id'),)
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    round_id: Mapped[str] = mapped_column(ForeignKey('records.id'))
    bank_id: Mapped[str] = mapped_column(ForeignKey('banks.id'))
    status: Mapped[str]
    metadata_json: Mapped[dict] = mapped_column(JSON)

def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def password_hash(value):
    salt = secrets.token_hex(16)
    return salt + ':' + hashlib.scrypt(value.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
def password_valid(value, stored):
    salt, expected = stored.split(':')
    return hmac.compare_digest(expected, hashlib.scrypt(value.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex())
def serialize(r): return {'id': r.id, 'bank_id': r.bank_id, 'created_at': r.created_at, **r.payload}
def add(db, kind, payload, bank_id=None):
    r = Record(kind=kind, bank_id=bank_id, payload=payload)
    db.add(r); db.flush(); return r
def audit(db, user, action, target=''):
    add(db, 'audit', {'actor': user.id, 'action': action, 'target': target}, user.bank_id)
