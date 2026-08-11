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


SupportLevel = Literal[
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

    # Preserve this as a free-form field.
    #
    # This describes the TYPE/NATURE of the evidence,
    # not its strength of support.
    #
    # Examples:
    # - "official product documentation"
    # - "technical documentation"
    # - "product specification"
    # - "technical article"
    # - "architecture description"
    # - "implementation description"
    evidence_type: str

    # Explanation of why the excerpt is relevant.
    relevance: str


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

    # Compatibility field retained for the existing pipeline.
    #
    # True means the evidence contributes meaningful support
    # to the claim element.
    #
    # False means the evidence should not contribute support.
    evidence_supported: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str

    # Strength/type of support established by this evidence.
    #
    # direct:
    #     The source explicitly discloses the claimed
    #     technical limitation.
    #
    # supportive:
    #     The source provides strong technical correspondence
    #     or an equivalent implementation.
    #
    # inferential:
    #     The source does not state the limitation verbatim,
    #     but the limitation can reasonably be inferred from
    #     the disclosed technical facts.
    #
    # contextual:
    #     The source is technically relevant but does not
    #     materially establish the limitation.
    #
    # unsupported:
    #     The evidence does not support the limitation.
    support_level: SupportLevel = "contextual"


class EvidenceVerificationItem(BaseModel):

    evidence_index: int

    evidence_supported: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str

    support_level: SupportLevel = "contextual"


class EvidenceVerificationBatchResult(BaseModel):

    results: list[EvidenceVerificationItem]


# ============================================================
# VERIFIED EVIDENCE
# ============================================================


class VerifiedEvidence(BaseModel):

    evidence: Evidence

    verification: EvidenceVerificationResult


# ============================================================
# EVIDENCE COMBINATION
# ============================================================


class EvidenceCombination(BaseModel):

    """
    Represents multiple evidence items considered together.

    A claim element does not necessarily need to be established
    by one source or one excerpt.

    Different evidence items may establish different parts of
    the same technical relationship.
    """

    evidence_indexes: list[int] = Field(
        default_factory=list
    )

    support_level: SupportLevel = "contextual"

    supported: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    reasoning: str = ""


# ============================================================
# CLAIM-ELEMENT EVIDENCE ASSESSMENT
# ============================================================


class ClaimElementEvidenceAssessment(BaseModel):

    """
    Element-level assessment after considering individual
    evidence items and combinations of evidence.

    Individual evidence verification asks:

        "What does this individual source establish?"

    Element-level assessment asks:

        "Do the available pieces of evidence collectively
         support this claim element?"
    """

    claim_element_id: str

    supported: bool = False

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    support_level: SupportLevel = "contextual"

    evidence_indexes: list[int] = Field(
        default_factory=list
    )

    reasoning: str = ""


# ============================================================
# CLAIM-ELEMENT MAPPING
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

    # Overall strength of support for this claim element.
    support_level: SupportLevel = "contextual"

    # Groups of evidence that collectively establish
    # the claim element.
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
