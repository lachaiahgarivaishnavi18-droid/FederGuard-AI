from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import math

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Credentials(Strict):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=128)
class Register(Credentials):
    password: str = Field(min_length=12, max_length=128)
    bank_id: str | None = None
class BankInput(Strict):
    id: str = Field(pattern=r'^[a-z][a-z0-9_-]{1,30}$')
    name: str = Field(min_length=2, max_length=100)
class BankEdit(Strict):
    active: bool = True
    consent: bool = True
class MemberInput(Credentials):
    password: str = Field(min_length=12, max_length=128)
    role: Literal['analyst','reviewer'] = 'analyst'
class Privacy(Strict):
    enabled: bool = True
    clipping_norm: float = Field(default=1, gt=0, le=10)
    noise_multiplier: float = Field(default=1.2, ge=0.5, le=10)
    delta: float = Field(default=1e-5, ge=1e-9, le=1e-3)
    max_epsilon: float = Field(default=30, gt=0, le=100)
class RoundInput(Strict):
    strategy: Literal['FedAvg', 'FedProx'] = 'FedAvg'
    bank_ids: list[str] = Field(default_factory=lambda: ['bank_a', 'bank_b', 'bank_c'], min_length=2, max_length=30)
    steps: int = Field(default=3, ge=1, le=20)
    proximal_mu: float = Field(default=0.01, ge=0, le=1)
    dropout_bank: str | None = None
    @field_validator('bank_ids')
    @classmethod
    def unique(cls, value):
        if len(set(value)) != len(value): raise ValueError('Duplicate bank')
        return value
class Features(Strict):
    amount: float = Field(ge=0, le=1000000)
    velocity: float = Field(ge=0, le=100)
    device_risk: float = Field(ge=0, le=1)
    geo_deviation: float = Field(ge=0, le=1)
    account_age: float = Field(ge=0, le=36500)
    hour: float = Field(ge=0, le=23)
class Query(Strict):
    question: str = Field(min_length=3, max_length=2000)
class Contribution(Strict):
    title: str = Field(min_length=3, max_length=200)
    category: Literal['Velocity', 'Account takeover', 'Card-not-present', 'Merchant anomaly']
    summary: str = Field(min_length=10, max_length=3000)
    evidence_refs: list[str] = Field(min_length=1, max_length=20)
    confidence: float = Field(ge=0, le=1)
    sharing: Literal['private', 'consortium'] = 'private'
    privacy_classification: Literal['aggregate', 'synthetic']
    expires_at: str
class Review(Strict):
    status: Literal['approved', 'rejected']
class CaseInput(Strict):
    title: str = Field(min_length=3, max_length=200)
    alert_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
class Note(Strict):
    text: str = Field(min_length=1, max_length=3000)
class CaseStatus(Strict):
    status: Literal['NEW', 'UNDER_REVIEW', 'ADDITIONAL_INFORMATION_REQUIRED', 'ESCALATED', 'CLOSED', 'FALSE_POSITIVE', 'INCONCLUSIVE']
class TrainRequest(Strict):
    round_id: str
    version: int = Field(ge=0)
    parameters: list[float] = Field(min_length=7, max_length=7)
    steps: int = Field(ge=1, le=20)
    strategy: Literal['FedAvg', 'FedProx']
    proximal_mu: float = Field(ge=0, le=1)
    privacy: Privacy
    @field_validator('parameters')
    @classmethod
    def finite(cls, values):
        if not all(math.isfinite(v) for v in values): raise ValueError('Nonfinite parameters')
        return values
