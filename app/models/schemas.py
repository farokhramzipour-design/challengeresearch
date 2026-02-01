from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


ChallengeType = Literal[
    "Regulatory",
    "Logistics",
    "Geopolitics",
    "Tariffs",
    "Sanctions",
    "Customs",
    "FX/Payments",
    "Energy",
    "SupplyChain",
    "ESG/CBAM",
    "Tech/ExportControls",
    "Labor",
    "Maritime",
    "Insurance",
    "Other",
]

ImpactArea = Literal["imports", "exports", "transit", "services_trade", "manufacturing"]
Severity = Literal["low", "medium", "high"]
TimeHorizon = Literal["now", "0-3m", "3-12m", "12m+"]
Relevance = Literal["direct", "indirect"]
Sector = Literal[
    "automotive",
    "agri-food",
    "steel",
    "chemicals",
    "pharma",
    "electronics",
    "energy",
    "shipping",
    "retail",
    "other",
]
Credibility = Literal["high", "medium", "low"]


class Evidence(BaseModel):
    source_name: str
    url: HttpUrl
    published_at: Optional[str] = None
    quote: str
    credibility: Credibility


class ChallengeItem(BaseModel):
    title: str
    summary: str
    challenge_type: ChallengeType
    impact_area: List[ImpactArea]
    severity: Severity
    time_horizon: TimeHorizon
    uk_relevance: Relevance
    eu_relevance: Relevance
    affected_sectors: List[Sector]
    evidence: List[Evidence]
    confidence: float
    dedupe_key: str


class OutputSchema(BaseModel):
    run_id: str
    scope: dict
    items: List[ChallengeItem]
    stats: dict


class RunConfig(BaseModel):
    max_items: int = 20
    recency_days: int = 60
    top_n_per_query: int = 5
    categories: Optional[List[str]] = None
    dry_run: bool = False


class RunStatus(BaseModel):
    run_id: str
    status: str
    created_at: datetime
    stats: dict
    error: Optional[str] = None


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
