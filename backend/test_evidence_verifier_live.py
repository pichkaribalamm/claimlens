from app.agents.evidence_verifier import EvidenceVerifier
from app.models.schemas import ClaimElement, Evidence


claim_element = ClaimElement(
    id="1.2",
    claim_number="1",
    text="a processor configured to receive image data"
)

evidence = Evidence(
    claim_element_id="1.2",
    source_title="Samsung Galaxy S26 Ultra",
    url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
    excerpt=(
        "High-resolution image data is analyzed in real time "
        "to maintain crisp textures and clarity across the whole "
        "scene for rich, true-to-life photos."
    ),
    evidence_type="direct",
    relevance=(
        "The source discusses image data processing in the target device."
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
