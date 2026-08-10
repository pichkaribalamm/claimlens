from app.agents.claim_mapper import ClaimMapper
from app.models.schemas import (
    ClaimElement,
    Evidence,
    EvidenceVerificationResult,
    VerifiedEvidence,
)


claim_element = ClaimElement(
    id="1.2",
    claim_number="1",
    text="an AI image signal processor (ISP) associated with the front camera"
)

evidence = Evidence(
    claim_element_id="1.2",
    source_title="Samsung Galaxy S26 Ultra",
    url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
    excerpt=(
        "Galaxy S26 Ultra's front camera now features an AI image "
        "signal processor (ISP) for more natural selfies with "
        "highlights and shadows where they should be."
    ),
    evidence_type="direct",
    relevance=(
        "The source explicitly confirms that the front camera "
        "features an AI image signal processor (ISP)."
    )
)

verification = EvidenceVerificationResult(
    claim_element_id="1.2",
    evidence_supported=True,
    confidence=0.98,
    reasoning=(
        "The evidence excerpt explicitly states that the front "
        "camera features an AI image signal processor (ISP)."
    )
)

verified_evidence = VerifiedEvidence(
    evidence=evidence,
    verification=verification,
)

mapper = ClaimMapper()

result = mapper.map(
    claim_element,
    [verified_evidence],
)

print("\n=== CLAIM MAPPING RESULT ===")
print(f"Claim Element: {result.claim_element_id}")
print(f"Supported: {result.supported}")
print(f"Confidence: {result.confidence}")
print(f"Evidence Count: {len(result.evidence)}")
print(f"Reasoning: {result.reasoning}")
