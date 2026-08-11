from typing import Optional, Literal

from pydantic import BaseModel, Field, HttpUrl


# ============================================================
# CLAIM MODELS
# ============================================================


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


# ============================================================
# SEARCH MODELS
# ============================================================


class SearchQuery(BaseModel):

    query: str
    rationale: str
    priority: int = Field(
        default=1,
        ge=1,
        le=5,
    )


class SearchResult(BaseModel):

    title: str
    url: HttpUrl
    snippet: Optional[str] = None
    source: Optional[str] = None

    # Source qualification metadata.
    source_type: Optional[str] = None
    source_quality: Optional[str] = None


# ============================================================
# EVIDENCE MODELS
# ============================================================


EvidenceType = Literal[
    "direct",
    "supportive",
    "inferential",
    "contextual",
    "unsupported",
]


class Evidence(BaseModel):

    claim_element_id: str

    source_title: str
    url: HttpUrl

    # Exact passage extracted from the source.
    excerpt: str

    # What kind of technical evidence this represents.
    #
    # direct:
    #     The source explicitly describes the claimed
    #     technical functionality.
    #
    # supportive:
    #     The source describes a technically equivalent or
    #     strongly corresponding implementation.
    #
    # inferential:
    #     The source provides facts from which the claimed
    #     functionality can reasonably be inferred.
    #
    # contextual:
    #     The source is technically relevant but does not
    #     meaningfully establish the limitation by itself.
    #
    # unsupported:
    #     The excerpt does not actually support the element.
    evidence_type: EvidenceType = "contextual"

    # Human-readable explanation of why the passage is
    # relevant to the claim element.
    relevance: str = ""


# ============================================================
# CLAIM PARSING
# ============================================================


class ClaimParseResult(BaseModel):

    elements: list[ClaimElement]


# ============================================================
# TECHNOLOGY PROFILING
# ============================================================


class TechnologyProfile(BaseModel):

    claim_element_id: str
    target: TargetScope

    core_concept: str

    technical_concepts: list[str]

    alternative_terminology: list[str]

    likely_components: list[str]

    implementation_hypotheses: list[str]


class TechnologyProfileBatchResult(BaseModel):

    results: list[TechnologyProfile]


# ============================================================
# SEARCH PLANNING
# ============================================================


class SearchPlan(BaseModel):

    claim_element_id: str

    queries: list[SearchQuery]

    preferred_sources: list[str]

    search_strategy: str


class SearchPlanBatchResult(BaseModel):

    results: list[SearchPlan]


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================


class EvidenceExtractionResult(BaseModel):

    evidence: list[Evidence]


class EvidenceExtractionItem(BaseModel):

    source_index: int

    evidence: list[Evidence]


class EvidenceExtractionBatchResult(BaseModel):

    results: list[EvidenceExtractionItem]


# ============================================================
# EVIDENCE VERIFICATION
# ============================================================


class EvidenceVerificationResult(BaseModel):

    claim_element_id: str

    # Retained for compatibility with the existing pipeline.
    #
    # True means the evidence is sufficiently supportive
    # to contribute to element-level mapping.
    #
    # False means the evidence should not contribute to
    # element-level support.
    evidence_supported: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str

    # More granular assessment than the old boolean.
    #
    # direct:
    #     Explicit disclosure.
    #
    # supportive:
    #     Strong technical correspondence / equivalent
    #     implementation.
    #
    # inferential:
    #     Reasonable technical inference from disclosed facts.
    #
    # contextual:
    #     Relevant background but insufficient to establish
    #     the limitation.
    #
    # unsupported:
    #     Does not support the limitation.
    support_level: EvidenceType = "contextual"


class EvidenceVerificationItem(BaseModel):

    evidence_index: int

    evidence_supported: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str

    support_level: EvidenceType = "contextual"


class EvidenceVerificationBatchResult(BaseModel):

    results: list[EvidenceVerificationItem]


# ============================================================
# VERIFIED EVIDENCE
# ============================================================


class VerifiedEvidence(BaseModel):

    evidence: Evidence

    verification: EvidenceVerificationResult


# ============================================================
# CLAIM-ELEMENT EVIDENCE AGGREGATION
# ============================================================


class EvidenceCombination(BaseModel):

    """
    Represents a group of evidence items considered together
    when assessing a claim element.

    This is important because a claim element may be supported
    by multiple sources that establish different parts of the
    same technical relationship.
    """

    evidence_indexes: list[int] = Field(
        default_factory=list
    )

    support_level: EvidenceType = "contextual"

    supported: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    reasoning: str = ""


class ClaimElementEvidenceAssessment(BaseModel):

    """
    Element-level assessment after considering individual
    evidence items and, where appropriate, combinations of
    evidence.

    This is deliberately separate from individual evidence
    verification.

    Individual evidence asks:
        "What does this source establish?"

    Element assessment asks:
        "Do the available pieces collectively support
         this claim element?"
    """

    claim_element_id: str

    supported: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    support_level: EvidenceType = "contextual"

    evidence_indexes: list[int] = Field(
        default_factory=list
    )

    reasoning: str = ""


# ============================================================
# CLAIM ELEMENT MAPPING
# ============================================================


class ClaimElementMapping(BaseModel):

    claim_element_id: str

    supported: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence: list[Evidence]

    reasoning: str

    # More informative than the old binary supported flag.
    support_level: EvidenceType = "contextual"

    # Evidence can be combined across multiple sources.
    evidence_combinations: list[EvidenceCombination] = Field(
        default_factory=list
    )


# ============================================================
# CLAIM ANALYSIS
# ============================================================


class ClaimAnalysisResult(BaseModel):

    claim_number: str

    coverage_status: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    element_mappings: list[ClaimElementMapping]

    reasoning: str
