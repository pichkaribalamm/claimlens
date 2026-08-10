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

1. Preserve the exact technical meaning of the claim.
2. Do not summarize the claim.
3. Do not add technical features that are not present.
4. Break the claim into meaningful technical limitations
   that can later be independently investigated for
   technical evidence.
5. Preserve grammatical and functional relationships
   between claim elements.
6. Treat a component and a functional limitation that
   modifies that component as one claim element when the
   function is part of the component's claimed configuration.

   Example:
   "a processor configured to receive image data"

   should normally remain one element:

   "a processor configured to receive image data"

   and should NOT be split into:

   "a processor"

   and:

   "configured to receive image data"

7. Do not split a claim element merely because it contains
   a structural feature followed by a "configured to",
   "adapted to", "operative to", "for", or similar functional
   limitation.
8. Split elements when they represent genuinely distinct
   limitations or components that can reasonably be searched
   independently.
9. Preserve relationships introduced by terms such as:
   "coupled to", "connected to", "responsive to", "based on",
   "configured to", "in communication with", and "for".
10. Keep each element sufficiently specific to support
    later technical evidence discovery.
11. Do not perform infringement analysis.
12. Do not determine whether any target product practices
    the claim.
13. Return only the requested structured output.

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
