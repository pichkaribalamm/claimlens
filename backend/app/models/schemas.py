from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class Claim(BaseModel):
    claim_number: str
    text: str


class ClaimElement(BaseModel):
    id: str
    claim_number: str
    text: str
    element_type: Optional[str] = None


class TargetScope(BaseModel):
    company: Optional[str] = None
    product: Optional[str] = None
    technology: Optional[str] = None


class SearchQuery(BaseModel):
    query: str
    rationale: str
    priority: int = Field(default=1, ge=1, le=5)


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: Optional[str] = None
    source: Optional[str] = None


class Evidence(BaseModel):
    claim_element_id: str
    source_title: str
    url: HttpUrl
    excerpt: str
    evidence_type: str
    relevance: str


class TechnologyProfile(BaseModel):
    claim_element_id: str
    target: TargetScope
    core_concept: str
    technical_concepts: list[str]
    alternative_terminology: list[str]
    likely_components: list[str]
    implementation_hypotheses: list[str]


class SearchPlan(BaseModel):
    claim_element_id: str
    queries: list[SearchQuery]
    preferred_sources: list[str]
    search_strategy: str


class EvidenceFinding(BaseModel):
    claim_element_id: str
    source_title: str
    url: HttpUrl
    excerpt: str
    evidence_type: str
    relevance: str
