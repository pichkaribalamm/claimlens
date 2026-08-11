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

Determine whether the evidence excerpt directly supports
the technical limitations of the claim element.

RULES:

1. Evaluate only the claim element and evidence excerpt.
2. Use no outside knowledge.
3. Do not infer facts not explicitly supported by the excerpt.
4. Similar terminology is not sufficient.
5. The excerpt must support the technical substance of the
   claim element.
6. When ambiguous or incomplete, mark unsupported.
7. Return only the requested structured output.

CLAIM ELEMENT:
ID: {claim_element.id}
TEXT: {claim_element.text}

EVIDENCE EXCERPT:
{evidence.excerpt}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationResult,
        )

        return EvidenceVerificationResult.model_validate_json(
            result
        )
