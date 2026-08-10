from app.models.schemas import (
    ClaimElement,
    VerifiedEvidence,
    ClaimElementMapping,
)
from app.services.gemini_service import GeminiService


class ClaimMapper:

    def __init__(self):
        self.llm = GeminiService()

    def map(
        self,
        claim_element: ClaimElement,
        verified_evidence: list[VerifiedEvidence],
    ) -> ClaimElementMapping:

        supported_evidence = [
            item
            for item in verified_evidence
            if item.verification.evidence_supported
        ]

        evidence_text = "\n\n".join(
            (
                f"Source: {item.evidence.source_title}\n"
                f"Excerpt: {item.evidence.excerpt}\n"
                f"Verification Confidence: "
                f"{item.verification.confidence}\n"
                f"Verification Reasoning: "
                f"{item.verification.reasoning}"
            )
            for item in supported_evidence
        )

        if not evidence_text:
            return ClaimElementMapping(
                claim_element_id=claim_element.id,
                supported=False,
                confidence=0.0,
                evidence=[],
                reasoning=(
                    "No verified evidence supports this claim element."
                ),
            )

        prompt = f"""
You are a patent claim mapping assistant.

Your task is to determine whether the verified evidence
provided below supports the complete technical substance
of a specific patent claim element.

IMPORTANT:

1. Evaluate only the claim element and the verified evidence.
2. Do not use outside knowledge.
3. Do not introduce facts that are not present in the evidence.
4. The evidence must support the technical substance of the
   claim element, not merely share terminology.
5. Consider every limitation expressed in the claim element.
6. If any material part of the claim element is unsupported,
   mark the claim element as unsupported.
7. Only evidence that has already passed verification is
   provided here.
8. Preserve the provided evidence objects in the output.
9. Be conservative when the evidence is ambiguous.
10. Return only the requested structured output.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

VERIFIED EVIDENCE:

{evidence_text}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=ClaimElementMapping,
        )

        return ClaimElementMapping.model_validate_json(result)
