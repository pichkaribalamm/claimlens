from app.models.schemas import (
    ClaimElement,
    SearchResult,
    Evidence,
    EvidenceExtractionResult,
)
from app.services.gemini_service import GeminiService


class EvidenceExtractor:

    def __init__(self):
        self.llm = GeminiService()

    def extract(
        self,
        claim_element: ClaimElement,
        search_result: SearchResult,
        reduced_content: str,
    ) -> list[Evidence]:

        if not reduced_content:
            return []

        prompt = f"""
You are a patent evidence extraction assistant.

Your task is to examine a patent claim element and
relevant content extracted from a publicly available
source page.

Determine whether the provided content contains
evidence that is relevant to the claim element.

IMPORTANT:

1. Only identify evidence that is actually supported by
   the provided content.
2. Do not rely on outside knowledge.
3. Do not infer facts that are not present in the content.
4. Extract the exact wording from the content that supports
   the finding.
5. Do not paraphrase the excerpt.
6. The excerpt must come directly from the provided content.
7. Evidence should be specific to the claim element.
8. If the content does not contain relevant evidence,
   return an empty list.
9. Return only the requested structured output.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

SOURCE:

Title:
{search_result.title}

URL:
{search_result.url}

RELEVANT PAGE CONTENT:

{reduced_content}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionResult,
        )

        parsed = EvidenceExtractionResult.model_validate_json(
            result
        )

        return parsed.evidence
