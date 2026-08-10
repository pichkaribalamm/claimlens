from app.agents.evidence_verifier import EvidenceVerifier
from app.models.schemas import ClaimElement, Evidence


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
        "highlights and shadows where they should be — true to "
        "your natural skin tone and other details such as hair "
        "and eyebrows, just as your eyes see them."
    ),
    evidence_type="direct",
    relevance=(
        "The source explicitly confirms that the front camera "
        "features an AI image signal processor (ISP)."
    )
)

verifier = EvidenceVerifier()

result = verifier.verify(
    claim_element,
    evidence
)

print("\n=== VERIFICATION RESULT ===")
print(f"Claim Element: {result.claim_element_id}")
print(f"Supported: {result.evidence_supported}")
print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning}")
