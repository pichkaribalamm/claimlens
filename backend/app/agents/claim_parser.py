from app.models.schemas import (
    Claim,
    ClaimParseResult,
)
from app.services.gemini_service import GeminiService


class ClaimParser:

    def __init__(self):
        self.llm = GeminiService()

    def parse(self, claim: Claim) -> ClaimParseResult:

        prompt = f"""
You are a patent claim analysis assistant.

Your task is to decompose the following patent claim
into its distinct technical claim elements.

IMPORTANT RULES:

1. Preserve the technical meaning of the claim.
2. Do not summarize the claim.
3. Do not add technical features that are not present.
4. Break the claim into meaningful limitations that can
   later be independently investigated for technical evidence.
5. Preserve relationships between elements where necessary.
6. Keep each element sufficiently specific to support
   a later web search.
7. Do not perform infringement analysis.
8. Do not determine whether any target product practices
   the claim.
9. Return only the requested structured output.

Claim number:
{claim.claim_number}

Claim text:
{claim.text}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=ClaimParseResult,
        )

        return ClaimParseResult.model_validate_json(result)
