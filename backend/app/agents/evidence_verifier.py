from app.models.schemas import (
    ClaimElement,
    Evidence,
    EvidenceVerificationResult,
)
from app.services.gemini_service import GeminiService


class EvidenceVerifier:

    def __init__(self):
        self.llm = GeminiService()

    def verify(
        self,
        claim_element: ClaimElement,
        evidence: Evidence,
    ) -> EvidenceVerificationResult:

        prompt = f"""
You are a patent evidence verification assistant.

Your task is to determine whether a specific evidence excerpt
actually supports a specific patent claim element.

IMPORTANT:

1. Evaluate ONLY the provided claim element and evidence excerpt.
2. Do not use outside knowledge.
3. Do not infer facts that are not explicitly supported by
   the evidence excerpt.
4. Do not rely on the source title or URL as proof.
5. The evidence must support the technical substance of the
   claim element, not merely contain similar terminology.
6. If the excerpt only discusses a related concept but does
   not establish the claimed functionality, mark the evidence
   as unsupported.
7. Be conservative. When the evidence is ambiguous, mark it
   as unsupported.
8. Confidence must reflect how strongly the excerpt supports
   the claim element.
9. Return only the requested structured output.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

EVIDENCE:

Source:
{evidence.source_title}

Excerpt:
{evidence.excerpt}

Evidence Type:
{evidence.evidence_type}

Relevance:
{evidence.relevance}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationResult,
        )

        return EvidenceVerificationResult.model_validate_json(
            result
        )
